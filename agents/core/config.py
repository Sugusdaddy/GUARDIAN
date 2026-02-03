"""
Agent Configuration
"""
import os
from dataclasses import dataclass, field
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv()


@dataclass
class AgentConfig:
    """Configuration for autonomous agents"""
    
    # API Keys
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    helius_api_key: str = field(default_factory=lambda: os.getenv("HELIUS_API_KEY", ""))
    
    # Solana
    solana_rpc_url: str = field(default_factory=lambda: os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com"))
    wallet_path: str = field(default_factory=lambda: os.getenv("WALLET_PATH", "./wallets/guardian-wallet.json"))
    network: str = field(default_factory=lambda: os.getenv("SOLANA_NETWORK", "devnet"))
    
    # Program IDs (will be updated after deployment)
    reasoning_registry_program_id: str = "11111111111111111111111111111111"
    threat_intelligence_program_id: str = "11111111111111111111111111111111"
    agent_coordinator_program_id: str = "11111111111111111111111111111111"
    
    # Agent behavior
    scan_interval_seconds: int = 30
    min_threat_confidence: float = 0.7
    require_consensus_threshold: int = 3
    max_memory_entries: int = 1000
    
    # Claude Opus settings
    model: str = "claude-opus-4-20250514"
    max_tokens: int = 2000
    
    # Logging
    log_level: str = "INFO"
    
    def validate(self) -> bool:
        """Validate configuration"""
        errors = []
        
        if not self.anthropic_api_key:
            errors.append("Missing ANTHROPIC_API_KEY")
        if not self.solana_rpc_url:
            errors.append("Missing SOLANA_RPC_URL")
        if not self.wallet_path:
            errors.append("Missing WALLET_PATH")
            
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        
        return True


# Global config instance
config = AgentConfig()
