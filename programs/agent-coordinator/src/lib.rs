use anchor_lang::prelude::*;

declare_id!("CafKDt5dyrYHFC2KUaJU2ux6AXEc2oFAjtdUoNaktwVX"); // Will be updated after first build

#[program]
pub mod agent_coordinator {
    use super::*;

    /// Initialize the swarm registry
    pub fn initialize_swarm(ctx: Context<InitializeSwarm>) -> Result<()> {
        let swarm = &mut ctx.accounts.swarm_registry;
        swarm.authority = ctx.accounts.authority.key();
        swarm.total_agents = 0;
        swarm.active_coordinations = 0;
        swarm.total_coordinations = 0;
        swarm.bump = ctx.bumps.swarm_registry;

        msg!("Swarm registry initialized");
        Ok(())
    }

    /// Register a new agent in the swarm
    pub fn register_agent(
        ctx: Context<RegisterAgent>,
        agent_type: AgentType,
        capabilities: Vec<Capability>,
    ) -> Result<()> {
        require!(capabilities.len() <= 10, ErrorCode::TooManyCapabilities);

        let agent = &mut ctx.accounts.agent_registration;
        let swarm = &mut ctx.accounts.swarm_registry;
        let clock = Clock::get()?;

        agent.agent_id = ctx.accounts.agent_authority.key();
        agent.agent_type = agent_type;
        agent.capabilities = capabilities.clone();
        agent.registered_at = clock.unix_timestamp;
        agent.last_active = clock.unix_timestamp;
        agent.active = true;
        agent.total_actions = 0;
        agent.successful_actions = 0;
        agent.reputation_score = 100; // Start at 100
        agent.bump = ctx.bumps.agent_registration;

        swarm.total_agents += 1;

        emit!(AgentRegistered {
            agent_id: agent.agent_id,
            agent_type,
            capabilities,
            timestamp: clock.unix_timestamp,
        });

        msg!("Registered {:?} agent: {}", agent_type, agent.agent_id);
        Ok(())
    }

    /// Initiate a coordinated response to a threat
    pub fn initiate_coordination(
        ctx: Context<InitiateCoordination>,
        threat_id: u64,
        required_capabilities: Vec<Capability>,
        action_plan: String,
        urgency: Urgency,
    ) -> Result<()> {
        let coordination = &mut ctx.accounts.coordination;
        let swarm = &mut ctx.accounts.swarm_registry;
        let clock = Clock::get()?;

        coordination.coordination_id = swarm.total_coordinations;
        coordination.threat_id = threat_id;
        coordination.initiator = ctx.accounts.authority.key();
        coordination.required_capabilities = required_capabilities;
        coordination.action_plan = action_plan;
        coordination.urgency = urgency;
        coordination.status = CoordinationStatus::Pending;
        coordination.participating_agents = vec![];
        coordination.votes_for = 0;
        coordination.votes_against = 0;
        coordination.initiated_at = clock.unix_timestamp;
        coordination.executed_at = None;
        coordination.result_hash = None;
        coordination.bump = ctx.bumps.coordination;

        swarm.total_coordinations += 1;
        swarm.active_coordinations += 1;

        emit!(CoordinationInitiated {
            coordination_id: coordination.coordination_id,
            threat_id,
            initiator: ctx.accounts.authority.key(),
            urgency,
            timestamp: clock.unix_timestamp,
        });

        msg!(
            "Coordination #{} initiated for threat {}",
            coordination.coordination_id,
            threat_id
        );
        Ok(())
    }

    /// Agent joins a coordination
    pub fn join_coordination(ctx: Context<JoinCoordination>) -> Result<()> {
        let coordination = &mut ctx.accounts.coordination;
        let agent = &ctx.accounts.agent_registration;

        // Check if agent has required capabilities
        let has_required = coordination
            .required_capabilities
            .iter()
            .any(|req| agent.capabilities.contains(req));

        require!(has_required, ErrorCode::MissingCapabilities);
        require!(
            !coordination.participating_agents.contains(&agent.agent_id),
            ErrorCode::AlreadyJoined
        );

        coordination.participating_agents.push(agent.agent_id);

        emit!(AgentJoinedCoordination {
            coordination_id: coordination.coordination_id,
            agent_id: agent.agent_id,
            timestamp: Clock::get()?.unix_timestamp,
        });

        msg!(
            "Agent {} joined coordination #{}",
            agent.agent_id,
            coordination.coordination_id
        );
        Ok(())
    }

    /// Vote on a coordination action
    pub fn vote_on_coordination(
        ctx: Context<VoteOnCoordination>,
        vote: bool, // true = approve, false = reject
    ) -> Result<()> {
        let coordination = &mut ctx.accounts.coordination;
        let agent = &ctx.accounts.agent_registration;

        // Must be a participant
        require!(
            coordination.participating_agents.contains(&agent.agent_id),
            ErrorCode::NotParticipant
        );

        if vote {
            coordination.votes_for += 1;
        } else {
            coordination.votes_against += 1;
        }

        // Check if consensus reached (>50% of participants)
        let total_votes = coordination.votes_for + coordination.votes_against;
        let participant_count = coordination.participating_agents.len() as u8;
        
        if total_votes >= participant_count {
            if coordination.votes_for > coordination.votes_against {
                coordination.status = CoordinationStatus::Approved;
                emit!(CoordinationApproved {
                    coordination_id: coordination.coordination_id,
                    votes_for: coordination.votes_for,
                    votes_against: coordination.votes_against,
                    timestamp: Clock::get()?.unix_timestamp,
                });
            } else {
                coordination.status = CoordinationStatus::Rejected;
                emit!(CoordinationRejected {
                    coordination_id: coordination.coordination_id,
                    votes_for: coordination.votes_for,
                    votes_against: coordination.votes_against,
                    timestamp: Clock::get()?.unix_timestamp,
                });
            }
        }

        Ok(())
    }

    /// Execute an approved coordination
    pub fn execute_coordination(
        ctx: Context<ExecuteCoordination>,
        result_hash: [u8; 32],
    ) -> Result<()> {
        let coordination = &mut ctx.accounts.coordination;
        let swarm = &mut ctx.accounts.swarm_registry;
        let clock = Clock::get()?;

        require!(
            coordination.status == CoordinationStatus::Approved,
            ErrorCode::NotApproved
        );

        coordination.status = CoordinationStatus::Executed;
        coordination.executed_at = Some(clock.unix_timestamp);
        coordination.result_hash = Some(result_hash);

        swarm.active_coordinations = swarm.active_coordinations.saturating_sub(1);

        emit!(CoordinationExecuted {
            coordination_id: coordination.coordination_id,
            threat_id: coordination.threat_id,
            result_hash,
            timestamp: clock.unix_timestamp,
        });

        msg!(
            "Coordination #{} executed successfully",
            coordination.coordination_id
        );
        Ok(())
    }

    /// Update agent's last active timestamp
    pub fn heartbeat(ctx: Context<Heartbeat>) -> Result<()> {
        let agent = &mut ctx.accounts.agent_registration;
        agent.last_active = Clock::get()?.unix_timestamp;
        Ok(())
    }

    /// Update agent reputation based on action outcome
    pub fn update_reputation(
        ctx: Context<UpdateReputation>,
        success: bool,
    ) -> Result<()> {
        let agent = &mut ctx.accounts.agent_registration;

        agent.total_actions += 1;
        if success {
            agent.successful_actions += 1;
            // Increase reputation (max 100)
            agent.reputation_score = std::cmp::min(100, agent.reputation_score + 1);
        } else {
            // Decrease reputation (min 0)
            agent.reputation_score = agent.reputation_score.saturating_sub(5);
        }

        emit!(ReputationUpdated {
            agent_id: agent.agent_id,
            new_score: agent.reputation_score,
            success,
            timestamp: Clock::get()?.unix_timestamp,
        });

        Ok(())
    }
}

// ============== ACCOUNTS ==============

#[derive(Accounts)]
pub struct InitializeSwarm<'info> {
    #[account(
        init,
        payer = authority,
        space = 8 + SwarmRegistry::INIT_SPACE,
        seeds = [b"swarm"],
        bump
    )]
    pub swarm_registry: Account<'info, SwarmRegistry>,
    
    #[account(mut)]
    pub authority: Signer<'info>,
    
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct RegisterAgent<'info> {
    #[account(
        init,
        payer = authority,
        space = 8 + AgentRegistration::INIT_SPACE,
        seeds = [b"agent", agent_authority.key().as_ref()],
        bump
    )]
    pub agent_registration: Account<'info, AgentRegistration>,
    
    #[account(mut, seeds = [b"swarm"], bump = swarm_registry.bump)]
    pub swarm_registry: Account<'info, SwarmRegistry>,
    
    /// CHECK: Agent's signing authority
    pub agent_authority: UncheckedAccount<'info>,
    
    #[account(mut)]
    pub authority: Signer<'info>,
    
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
#[instruction(threat_id: u64)]
pub struct InitiateCoordination<'info> {
    #[account(
        init,
        payer = authority,
        space = 8 + Coordination::INIT_SPACE,
        seeds = [b"coordination", swarm_registry.total_coordinations.to_le_bytes().as_ref()],
        bump
    )]
    pub coordination: Account<'info, Coordination>,
    
    #[account(mut, seeds = [b"swarm"], bump = swarm_registry.bump)]
    pub swarm_registry: Account<'info, SwarmRegistry>,
    
    #[account(mut)]
    pub authority: Signer<'info>,
    
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct JoinCoordination<'info> {
    #[account(mut)]
    pub coordination: Account<'info, Coordination>,
    
    pub agent_registration: Account<'info, AgentRegistration>,
    
    pub authority: Signer<'info>,
}

#[derive(Accounts)]
pub struct VoteOnCoordination<'info> {
    #[account(mut)]
    pub coordination: Account<'info, Coordination>,
    
    pub agent_registration: Account<'info, AgentRegistration>,
    
    pub authority: Signer<'info>,
}

#[derive(Accounts)]
pub struct ExecuteCoordination<'info> {
    #[account(mut)]
    pub coordination: Account<'info, Coordination>,
    
    #[account(mut, seeds = [b"swarm"], bump = swarm_registry.bump)]
    pub swarm_registry: Account<'info, SwarmRegistry>,
    
    pub authority: Signer<'info>,
}

#[derive(Accounts)]
pub struct Heartbeat<'info> {
    #[account(mut)]
    pub agent_registration: Account<'info, AgentRegistration>,
    
    pub authority: Signer<'info>,
}

#[derive(Accounts)]
pub struct UpdateReputation<'info> {
    #[account(mut)]
    pub agent_registration: Account<'info, AgentRegistration>,
    
    pub authority: Signer<'info>,
}

// ============== STATE ==============

#[account]
#[derive(InitSpace)]
pub struct SwarmRegistry {
    pub authority: Pubkey,
    pub total_agents: u64,
    pub active_coordinations: u64,
    pub total_coordinations: u64,
    pub bump: u8,
}

#[account]
#[derive(InitSpace)]
pub struct AgentRegistration {
    pub agent_id: Pubkey,
    pub agent_type: AgentType,
    #[max_len(10)]
    pub capabilities: Vec<Capability>,
    pub registered_at: i64,
    pub last_active: i64,
    pub active: bool,
    pub total_actions: u64,
    pub successful_actions: u64,
    pub reputation_score: u8, // 0-100
    pub bump: u8,
}

#[account]
#[derive(InitSpace)]
pub struct Coordination {
    pub coordination_id: u64,
    pub threat_id: u64,
    pub initiator: Pubkey,
    #[max_len(5)]
    pub required_capabilities: Vec<Capability>,
    #[max_len(1000)]
    pub action_plan: String,
    pub urgency: Urgency,
    pub status: CoordinationStatus,
    #[max_len(10)]
    pub participating_agents: Vec<Pubkey>,
    pub votes_for: u8,
    pub votes_against: u8,
    pub initiated_at: i64,
    pub executed_at: Option<i64>,
    pub result_hash: Option<[u8; 32]>,
    pub bump: u8,
}

// ============== TYPES ==============

#[derive(AnchorSerialize, AnchorDeserialize, Clone, Copy, PartialEq, Eq, InitSpace, Debug)]
pub enum AgentType {
    Sentinel,   // Transaction monitoring
    Scanner,    // Contract analysis
    Guardian,   // Threat defense
    Oracle,     // Risk prediction
    Intel,      // Knowledge base
    Reporter,   // Community alerts
    Auditor,    // Reasoning verification
    Hunter,     // Actor tracking
    Healer,     // Fund recovery
    Coordinator,// Swarm orchestration
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone, Copy, PartialEq, Eq, InitSpace, Debug)]
pub enum Capability {
    TransactionMonitoring,
    ContractAnalysis,
    ThreatDetection,
    RiskPrediction,
    KnowledgeManagement,
    CommunityAlerts,
    ReasoningVerification,
    ActorTracking,
    FundRecovery,
    SwarmCoordination,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone, Copy, PartialEq, Eq, InitSpace, Debug)]
pub enum Urgency {
    Low,
    Medium,
    High,
    Critical,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone, Copy, PartialEq, Eq, InitSpace, Debug)]
pub enum CoordinationStatus {
    Pending,
    Approved,
    Rejected,
    Executed,
    Failed,
    Cancelled,
}

// ============== EVENTS ==============

#[event]
pub struct AgentRegistered {
    pub agent_id: Pubkey,
    pub agent_type: AgentType,
    pub capabilities: Vec<Capability>,
    pub timestamp: i64,
}

#[event]
pub struct CoordinationInitiated {
    pub coordination_id: u64,
    pub threat_id: u64,
    pub initiator: Pubkey,
    pub urgency: Urgency,
    pub timestamp: i64,
}

#[event]
pub struct AgentJoinedCoordination {
    pub coordination_id: u64,
    pub agent_id: Pubkey,
    pub timestamp: i64,
}

#[event]
pub struct CoordinationApproved {
    pub coordination_id: u64,
    pub votes_for: u8,
    pub votes_against: u8,
    pub timestamp: i64,
}

#[event]
pub struct CoordinationRejected {
    pub coordination_id: u64,
    pub votes_for: u8,
    pub votes_against: u8,
    pub timestamp: i64,
}

#[event]
pub struct CoordinationExecuted {
    pub coordination_id: u64,
    pub threat_id: u64,
    pub result_hash: [u8; 32],
    pub timestamp: i64,
}

#[event]
pub struct ReputationUpdated {
    pub agent_id: Pubkey,
    pub new_score: u8,
    pub success: bool,
    pub timestamp: i64,
}

// ============== ERRORS ==============

#[error_code]
pub enum ErrorCode {
    #[msg("Agent has too many capabilities specified")]
    TooManyCapabilities,
    #[msg("Agent missing required capabilities for this coordination")]
    MissingCapabilities,
    #[msg("Agent has already joined this coordination")]
    AlreadyJoined,
    #[msg("Agent is not a participant in this coordination")]
    NotParticipant,
    #[msg("Coordination has not been approved")]
    NotApproved,
    #[msg("Unauthorized for this operation")]
    Unauthorized,
}
