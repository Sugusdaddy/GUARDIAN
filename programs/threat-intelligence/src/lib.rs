use anchor_lang::prelude::*;

declare_id!("Fo9Nm41pvuUCT2sPPsuo1XyWCQCTKf6GNwASQ1ZMEfpv"); // Will be updated after first build

#[program]
pub mod threat_intelligence {
    use super::*;

    /// Initialize the global threat counter
    pub fn initialize_threat_counter(ctx: Context<InitializeThreatCounter>) -> Result<()> {
        let counter = &mut ctx.accounts.threat_counter;
        counter.count = 0;
        counter.authority = ctx.accounts.authority.key();
        counter.bump = ctx.bumps.threat_counter;
        
        msg!("Threat counter initialized");
        Ok(())
    }

    /// Register a new threat detected by an agent
    pub fn register_threat(
        ctx: Context<RegisterThreat>,
        threat_type: ThreatType,
        severity: u8,
        target_address: Option<Pubkey>,
        description: String,
        evidence_hash: [u8; 32],
    ) -> Result<()> {
        require!(severity <= 100, ErrorCode::InvalidSeverity);
        require!(description.len() <= 500, ErrorCode::DescriptionTooLong);

        let counter = &mut ctx.accounts.threat_counter;
        let threat = &mut ctx.accounts.threat;
        let clock = Clock::get()?;

        threat.threat_id = counter.count;
        threat.threat_type = threat_type;
        threat.severity = severity;
        threat.target_address = target_address;
        threat.description = description.clone();
        threat.evidence_hash = evidence_hash;
        threat.detected_at = clock.unix_timestamp;
        threat.detected_by = ctx.accounts.authority.key();
        threat.status = ThreatStatus::Active;
        threat.confirmed_by = vec![];
        threat.false_positive_votes = 0;
        threat.bump = ctx.bumps.threat;

        counter.count += 1;

        emit!(ThreatRegistered {
            threat_id: threat.threat_id,
            threat_type,
            severity,
            target_address,
            detected_by: ctx.accounts.authority.key(),
            timestamp: clock.unix_timestamp,
        });

        msg!(
            "Registered threat #{} - {:?} with severity {}",
            threat.threat_id,
            threat_type,
            severity
        );
        Ok(())
    }

    /// Confirm a threat (another agent validates it)
    pub fn confirm_threat(ctx: Context<ConfirmThreat>) -> Result<()> {
        let threat = &mut ctx.accounts.threat;
        let confirmer = ctx.accounts.authority.key();

        // Can't confirm your own threat
        require!(threat.detected_by != confirmer, ErrorCode::CannotConfirmOwn);
        
        // Can't confirm twice
        require!(
            !threat.confirmed_by.contains(&confirmer),
            ErrorCode::AlreadyConfirmed
        );

        threat.confirmed_by.push(confirmer);

        // Auto-escalate if 3+ confirmations
        if threat.confirmed_by.len() >= 3 && threat.status == ThreatStatus::Active {
            threat.status = ThreatStatus::Confirmed;
            emit!(ThreatEscalated {
                threat_id: threat.threat_id,
                new_status: ThreatStatus::Confirmed,
                confirmations: threat.confirmed_by.len() as u8,
                timestamp: Clock::get()?.unix_timestamp,
            });
        }

        emit!(ThreatConfirmed {
            threat_id: threat.threat_id,
            confirmed_by: confirmer,
            total_confirmations: threat.confirmed_by.len() as u8,
            timestamp: Clock::get()?.unix_timestamp,
        });

        Ok(())
    }

    /// Mark threat as false positive
    pub fn mark_false_positive(ctx: Context<MarkFalsePositive>) -> Result<()> {
        let threat = &mut ctx.accounts.threat;
        
        threat.false_positive_votes += 1;

        // If 3+ false positive votes, mark as false positive
        if threat.false_positive_votes >= 3 {
            threat.status = ThreatStatus::FalsePositive;
            emit!(ThreatStatusChanged {
                threat_id: threat.threat_id,
                old_status: ThreatStatus::Active,
                new_status: ThreatStatus::FalsePositive,
                timestamp: Clock::get()?.unix_timestamp,
            });
        }

        Ok(())
    }

    /// Update threat status
    pub fn update_threat_status(
        ctx: Context<UpdateThreatStatus>,
        new_status: ThreatStatus,
    ) -> Result<()> {
        let threat = &mut ctx.accounts.threat;
        let old_status = threat.status.clone();

        threat.status = new_status.clone();

        emit!(ThreatStatusChanged {
            threat_id: threat.threat_id,
            old_status,
            new_status,
            timestamp: Clock::get()?.unix_timestamp,
        });

        msg!(
            "Updated threat #{} status to {:?}",
            threat.threat_id,
            new_status
        );
        Ok(())
    }

    /// Add known malicious address to watchlist
    pub fn add_to_watchlist(
        ctx: Context<AddToWatchlist>,
        address: Pubkey,
        reason: String,
        linked_threat_id: Option<u64>,
    ) -> Result<()> {
        let watchlist_entry = &mut ctx.accounts.watchlist_entry;
        let clock = Clock::get()?;

        watchlist_entry.address = address;
        watchlist_entry.reason = reason;
        watchlist_entry.linked_threat_id = linked_threat_id;
        watchlist_entry.added_at = clock.unix_timestamp;
        watchlist_entry.added_by = ctx.accounts.authority.key();
        watchlist_entry.active = true;
        watchlist_entry.bump = ctx.bumps.watchlist_entry;

        emit!(AddressWatchlisted {
            address,
            linked_threat_id,
            added_by: ctx.accounts.authority.key(),
            timestamp: clock.unix_timestamp,
        });

        msg!("Added {} to watchlist", address);
        Ok(())
    }

    /// Check if an address is on the watchlist
    pub fn check_watchlist(ctx: Context<CheckWatchlist>) -> Result<bool> {
        Ok(ctx.accounts.watchlist_entry.active)
    }
}

// ============== ACCOUNTS ==============

#[derive(Accounts)]
pub struct InitializeThreatCounter<'info> {
    #[account(
        init,
        payer = authority,
        space = 8 + ThreatCounter::INIT_SPACE,
        seeds = [b"threat_counter"],
        bump
    )]
    pub threat_counter: Account<'info, ThreatCounter>,
    
    #[account(mut)]
    pub authority: Signer<'info>,
    
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct RegisterThreat<'info> {
    #[account(
        init,
        payer = authority,
        space = 8 + Threat::INIT_SPACE,
        seeds = [b"threat", threat_counter.count.to_le_bytes().as_ref()],
        bump
    )]
    pub threat: Account<'info, Threat>,
    
    #[account(mut, seeds = [b"threat_counter"], bump = threat_counter.bump)]
    pub threat_counter: Account<'info, ThreatCounter>,
    
    #[account(mut)]
    pub authority: Signer<'info>,
    
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct ConfirmThreat<'info> {
    #[account(mut)]
    pub threat: Account<'info, Threat>,
    
    pub authority: Signer<'info>,
}

#[derive(Accounts)]
pub struct MarkFalsePositive<'info> {
    #[account(mut)]
    pub threat: Account<'info, Threat>,
    
    pub authority: Signer<'info>,
}

#[derive(Accounts)]
pub struct UpdateThreatStatus<'info> {
    #[account(mut)]
    pub threat: Account<'info, Threat>,
    
    pub authority: Signer<'info>,
}

#[derive(Accounts)]
#[instruction(address: Pubkey)]
pub struct AddToWatchlist<'info> {
    #[account(
        init,
        payer = authority,
        space = 8 + WatchlistEntry::INIT_SPACE,
        seeds = [b"watchlist", address.as_ref()],
        bump
    )]
    pub watchlist_entry: Account<'info, WatchlistEntry>,
    
    #[account(mut)]
    pub authority: Signer<'info>,
    
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct CheckWatchlist<'info> {
    pub watchlist_entry: Account<'info, WatchlistEntry>,
}

// ============== STATE ==============

#[account]
#[derive(InitSpace)]
pub struct ThreatCounter {
    pub count: u64,
    pub authority: Pubkey,
    pub bump: u8,
}

#[account]
#[derive(InitSpace)]
pub struct Threat {
    pub threat_id: u64,
    pub threat_type: ThreatType,
    pub severity: u8, // 0-100
    pub target_address: Option<Pubkey>,
    #[max_len(500)]
    pub description: String,
    pub evidence_hash: [u8; 32],
    pub detected_at: i64,
    pub detected_by: Pubkey,
    pub status: ThreatStatus,
    #[max_len(10)]
    pub confirmed_by: Vec<Pubkey>,
    pub false_positive_votes: u8,
    pub bump: u8,
}

#[account]
#[derive(InitSpace)]
pub struct WatchlistEntry {
    pub address: Pubkey,
    #[max_len(200)]
    pub reason: String,
    pub linked_threat_id: Option<u64>,
    pub added_at: i64,
    pub added_by: Pubkey,
    pub active: bool,
    pub bump: u8,
}

// ============== TYPES ==============

#[derive(AnchorSerialize, AnchorDeserialize, Clone, Copy, PartialEq, Eq, InitSpace, Debug)]
pub enum ThreatType {
    RugPull,
    Honeypot,
    PhishingContract,
    SuspiciousTransfer,
    PriceManipulation,
    UnauthorizedMint,
    FlashLoanAttack,
    SandwichAttack,
    DrainAttack,
    Unknown,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone, Copy, PartialEq, Eq, InitSpace, Debug)]
pub enum ThreatStatus {
    Active,
    Confirmed,
    Neutralized,
    FalsePositive,
    UnderInvestigation,
    Escalated,
}

// ============== EVENTS ==============

#[event]
pub struct ThreatRegistered {
    pub threat_id: u64,
    pub threat_type: ThreatType,
    pub severity: u8,
    pub target_address: Option<Pubkey>,
    pub detected_by: Pubkey,
    pub timestamp: i64,
}

#[event]
pub struct ThreatConfirmed {
    pub threat_id: u64,
    pub confirmed_by: Pubkey,
    pub total_confirmations: u8,
    pub timestamp: i64,
}

#[event]
pub struct ThreatEscalated {
    pub threat_id: u64,
    pub new_status: ThreatStatus,
    pub confirmations: u8,
    pub timestamp: i64,
}

#[event]
pub struct ThreatStatusChanged {
    pub threat_id: u64,
    pub old_status: ThreatStatus,
    pub new_status: ThreatStatus,
    pub timestamp: i64,
}

#[event]
pub struct AddressWatchlisted {
    pub address: Pubkey,
    pub linked_threat_id: Option<u64>,
    pub added_by: Pubkey,
    pub timestamp: i64,
}

// ============== ERRORS ==============

#[error_code]
pub enum ErrorCode {
    #[msg("Severity must be between 0 and 100")]
    InvalidSeverity,
    #[msg("Description exceeds maximum length")]
    DescriptionTooLong,
    #[msg("Cannot confirm your own threat")]
    CannotConfirmOwn,
    #[msg("Already confirmed this threat")]
    AlreadyConfirmed,
    #[msg("Unauthorized for this operation")]
    Unauthorized,
}
