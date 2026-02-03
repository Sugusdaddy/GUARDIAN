use anchor_lang::prelude::*;
use anchor_lang::solana_program::hash::hash;

declare_id!("87CGxPABDUwvSRzByXeMcmZ5Qo8B6225z2q8D8VkxUjt"); // Will be updated after first build

#[program]
pub mod reasoning_registry {
    use super::*;

    /// Commit reasoning hash on-chain BEFORE taking any action
    /// This ensures transparency and prevents post-hoc reasoning manipulation
    pub fn commit_reasoning(
        ctx: Context<CommitReasoning>,
        agent_id: Pubkey,
        reasoning_hash: [u8; 32],
        threat_id: u64,
        action_type: ActionType,
    ) -> Result<()> {
        let reasoning_commit = &mut ctx.accounts.reasoning_commit;
        let clock = Clock::get()?;
        
        reasoning_commit.agent_id = agent_id;
        reasoning_commit.reasoning_hash = reasoning_hash;
        reasoning_commit.threat_id = threat_id;
        reasoning_commit.action_type = action_type;
        reasoning_commit.commit_timestamp = clock.unix_timestamp;
        reasoning_commit.revealed = false;
        reasoning_commit.reveal_timestamp = None;
        reasoning_commit.reasoning_text = String::new();
        reasoning_commit.bump = ctx.bumps.reasoning_commit;

        emit!(ReasoningCommitted {
            agent_id,
            threat_id,
            reasoning_hash,
            action_type,
            timestamp: clock.unix_timestamp,
        });

        msg!(
            "Agent {} committed reasoning for threat {} with action {:?}",
            agent_id,
            threat_id,
            action_type
        );
        Ok(())
    }

    /// Reveal the full reasoning text after action is taken
    /// Verifies the hash matches what was committed
    pub fn reveal_reasoning(
        ctx: Context<RevealReasoning>,
        reasoning_text: String,
    ) -> Result<()> {
        let reasoning_commit = &mut ctx.accounts.reasoning_commit;
        let clock = Clock::get()?;

        // Cannot reveal twice
        require!(!reasoning_commit.revealed, ErrorCode::AlreadyRevealed);

        // Verify hash matches
        let computed_hash = hash(reasoning_text.as_bytes());
        require!(
            computed_hash.to_bytes() == reasoning_commit.reasoning_hash,
            ErrorCode::HashMismatch
        );

        reasoning_commit.reasoning_text = reasoning_text.clone();
        reasoning_commit.revealed = true;
        reasoning_commit.reveal_timestamp = Some(clock.unix_timestamp);

        emit!(ReasoningRevealed {
            agent_id: reasoning_commit.agent_id,
            threat_id: reasoning_commit.threat_id,
            reasoning_text,
            timestamp: clock.unix_timestamp,
        });

        msg!(
            "Reasoning revealed and verified for threat {}",
            reasoning_commit.threat_id
        );
        Ok(())
    }

    /// Verify that a reasoning commit is valid (hash matches revealed text)
    pub fn verify_reasoning(ctx: Context<VerifyReasoning>) -> Result<bool> {
        let reasoning_commit = &ctx.accounts.reasoning_commit;

        // Must be revealed first
        require!(reasoning_commit.revealed, ErrorCode::NotRevealed);

        let computed_hash = hash(reasoning_commit.reasoning_text.as_bytes());
        let is_valid = computed_hash.to_bytes() == reasoning_commit.reasoning_hash;

        emit!(ReasoningVerified {
            agent_id: reasoning_commit.agent_id,
            threat_id: reasoning_commit.threat_id,
            is_valid,
            timestamp: Clock::get()?.unix_timestamp,
        });

        Ok(is_valid)
    }

    /// Query reasoning commits by agent (returns count, client fetches details)
    pub fn get_agent_stats(ctx: Context<GetAgentStats>) -> Result<AgentStats> {
        let agent_registry = &ctx.accounts.agent_registry;
        Ok(AgentStats {
            total_commits: agent_registry.total_commits,
            total_reveals: agent_registry.total_reveals,
            accuracy_score: agent_registry.accuracy_score,
        })
    }

    /// Initialize agent registry for tracking stats
    pub fn initialize_agent_registry(
        ctx: Context<InitializeAgentRegistry>,
        agent_id: Pubkey,
    ) -> Result<()> {
        let registry = &mut ctx.accounts.agent_registry;
        registry.agent_id = agent_id;
        registry.total_commits = 0;
        registry.total_reveals = 0;
        registry.accuracy_score = 100; // Start at 100%, decreases on false positives
        registry.bump = ctx.bumps.agent_registry;

        msg!("Initialized registry for agent {}", agent_id);
        Ok(())
    }
}

// ============== ACCOUNTS ==============

#[derive(Accounts)]
#[instruction(agent_id: Pubkey, reasoning_hash: [u8; 32], threat_id: u64)]
pub struct CommitReasoning<'info> {
    #[account(
        init,
        payer = authority,
        space = 8 + ReasoningCommit::INIT_SPACE,
        seeds = [b"reasoning", agent_id.as_ref(), &threat_id.to_le_bytes()],
        bump
    )]
    pub reasoning_commit: Account<'info, ReasoningCommit>,
    
    #[account(mut)]
    pub authority: Signer<'info>,
    
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct RevealReasoning<'info> {
    #[account(
        mut,
        has_one = agent_id @ ErrorCode::UnauthorizedAgent,
    )]
    pub reasoning_commit: Account<'info, ReasoningCommit>,
    
    /// CHECK: Verified via has_one constraint
    pub agent_id: UncheckedAccount<'info>,
    
    pub authority: Signer<'info>,
}

#[derive(Accounts)]
pub struct VerifyReasoning<'info> {
    pub reasoning_commit: Account<'info, ReasoningCommit>,
}

#[derive(Accounts)]
#[instruction(agent_id: Pubkey)]
pub struct InitializeAgentRegistry<'info> {
    #[account(
        init,
        payer = authority,
        space = 8 + AgentRegistry::INIT_SPACE,
        seeds = [b"agent_registry", agent_id.as_ref()],
        bump
    )]
    pub agent_registry: Account<'info, AgentRegistry>,
    
    #[account(mut)]
    pub authority: Signer<'info>,
    
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct GetAgentStats<'info> {
    pub agent_registry: Account<'info, AgentRegistry>,
}

// ============== STATE ==============

#[account]
#[derive(InitSpace)]
pub struct ReasoningCommit {
    pub agent_id: Pubkey,
    pub reasoning_hash: [u8; 32],
    pub threat_id: u64,
    pub action_type: ActionType,
    pub commit_timestamp: i64,
    pub revealed: bool,
    pub reveal_timestamp: Option<i64>,
    #[max_len(2000)]
    pub reasoning_text: String,
    pub bump: u8,
}

#[account]
#[derive(InitSpace)]
pub struct AgentRegistry {
    pub agent_id: Pubkey,
    pub total_commits: u64,
    pub total_reveals: u64,
    pub accuracy_score: u8, // 0-100
    pub bump: u8,
}

// ============== TYPES ==============

#[derive(AnchorSerialize, AnchorDeserialize, Clone, Copy, PartialEq, Eq, InitSpace, Debug)]
pub enum ActionType {
    Ignore,
    Monitor,
    Warn,
    Block,
    Coordinate,
    Recover,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone)]
pub struct AgentStats {
    pub total_commits: u64,
    pub total_reveals: u64,
    pub accuracy_score: u8,
}

// ============== EVENTS ==============

#[event]
pub struct ReasoningCommitted {
    pub agent_id: Pubkey,
    pub threat_id: u64,
    pub reasoning_hash: [u8; 32],
    pub action_type: ActionType,
    pub timestamp: i64,
}

#[event]
pub struct ReasoningRevealed {
    pub agent_id: Pubkey,
    pub threat_id: u64,
    pub reasoning_text: String,
    pub timestamp: i64,
}

#[event]
pub struct ReasoningVerified {
    pub agent_id: Pubkey,
    pub threat_id: u64,
    pub is_valid: bool,
    pub timestamp: i64,
}

// ============== ERRORS ==============

#[error_code]
pub enum ErrorCode {
    #[msg("Reasoning has already been revealed")]
    AlreadyRevealed,
    #[msg("Hash does not match reasoning text")]
    HashMismatch,
    #[msg("Reasoning has not been revealed yet")]
    NotRevealed,
    #[msg("Unauthorized agent for this operation")]
    UnauthorizedAgent,
    #[msg("Invalid reasoning text length")]
    InvalidReasoningLength,
}
