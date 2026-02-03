"""
GUARDIAN Configuration - Production Settings
"""
import os
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

@dataclass
class AgentConfig:
    """Agent configuration with mainnet defaults"""
    
    # Network - MAINNET by default
    network: str = field(default_factory=lambda: os.getenv("NETWORK", "mainnet-beta"))
    
    # Solana RPC
    solana_rpc_url: str = field(default_factory=lambda: os.getenv(
        "SOLANA_RPC_URL",
        "https://api.mainnet-beta.solana.com"
    ))
    
    # Wallet
    wallet_path: str = field(default_factory=lambda: os.getenv(
        "WALLET_PATH",
        str(Path(__file__).parent.parent.parent / "wallet.json")
    ))
    
    # Anthropic
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    model: str = field(default_factory=lambda: os.getenv("MODEL", "claude-sonnet-4-20250514"))
    max_tokens: int = field(default_factory=lambda: int(os.getenv("MAX_TOKENS", "4096")))
    
    # Helius (for enhanced RPC)
    helius_api_key: str = field(default_factory=lambda: os.getenv("HELIUS_API_KEY", ""))
    helius_webhook_secret: str = field(default_factory=lambda: os.getenv("HELIUS_WEBHOOK_SECRET", ""))
    
    # Agent settings
    scan_interval_seconds: int = field(default_factory=lambda: int(os.getenv("SCAN_INTERVAL_SECONDS", "30")))
    min_threat_confidence: float = field(default_factory=lambda: float(os.getenv("MIN_THREAT_CONFIDENCE", "0.6")))
    max_memory_entries: int = field(default_factory=lambda: int(os.getenv("MAX_MEMORY_ENTRIES", "1000")))
    
    def validate(self):
        """Validate configuration"""
        if not self.anthropic_api_key:
            print("Warning: ANTHROPIC_API_KEY not set")
        
        if self.network not in ["mainnet-beta", "devnet", "testnet"]:
            raise ValueError(f"Invalid network: {self.network}")
    
    @property
    def is_mainnet(self) -> bool:
        return self.network == "mainnet-beta"


# Global config instance
config = AgentConfig()
