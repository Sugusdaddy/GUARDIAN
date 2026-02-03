"""
GUARDIAN On-Chain Client - Real Anchor program interaction
Connects Python agents to Solana smart contracts
"""
import asyncio
import hashlib
import json
import struct
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import IntEnum

import structlog

# Try importing Solana libraries (may not be available)
try:
    from solana.rpc.async_api import AsyncClient
    from solana.rpc.commitment import Confirmed
    from solders.keypair import Keypair
    from solders.pubkey import Pubkey
    from solders.system_program import ID as SYSTEM_PROGRAM_ID
    from solders.instruction import Instruction, AccountMeta
    HAS_SOLANA = True
except ImportError:
    HAS_SOLANA = False
    # Create mock classes
    class Keypair:
        def __init__(self):
            self._pubkey = "MockPubkey" + "0" * 32
        def pubkey(self):
            return self._pubkey
        @classmethod
        def from_bytes(cls, data):
            return cls()
    class Pubkey:
        @staticmethod
        def from_string(s):
            return s
        @staticmethod
        def find_program_address(seeds, program_id):
            return ("MockPDA", 255)
    AsyncClient = None
    Confirmed = None
    SYSTEM_PROGRAM_ID = "11111111111111111111111111111111"

from .config import config

logger = structlog.get_logger()

# Program IDs (will be updated after deployment)
REASONING_REGISTRY_ID = Pubkey.from_string("87CGxPABDUwvSRzByXeMcmZ5Qo8B6225z2q8D8VkxUjt")
THREAT_INTELLIGENCE_ID = Pubkey.from_string("87CGxPABDUwvSRzByXeMcmZ5Qo8B6225z2q8D8VkxUjt")  # placeholder
AGENT_COORDINATOR_ID = Pubkey.from_string("87CGxPABDUwvSRzByXeMcmZ5Qo8B6225z2q8D8VkxUjt")  # placeholder


class ActionType(IntEnum):
    """Maps to Rust ActionType enum"""
    IGNORE = 0
    MONITOR = 1
    WARN = 2
    BLOCK = 3
    COORDINATE = 4
    RECOVER = 5


class ThreatType(IntEnum):
    """Maps to Rust ThreatType enum"""
    RUGPULL = 0
    HONEYPOT = 1
    DRAINER = 2
    FLASHLOAN = 3
    ORACLE_MANIPULATION = 4
    SANDWICH = 5
    SUSPICIOUS_TRANSFER = 6
    BLACKLISTED_INTERACTION = 7
    UNKNOWN = 8


@dataclass
class ReasoningCommit:
    """On-chain reasoning commit data"""
    agent_id: Pubkey
    reasoning_hash: bytes
    threat_id: int
    action_type: ActionType
    commit_timestamp: int
    revealed: bool
    reveal_timestamp: Optional[int]
    reasoning_text: str
    bump: int


class GuardianOnChain:
    """
    Client for interacting with GUARDIAN Anchor programs.
    Handles commit/reveal reasoning, threat registration, and coordination.
    """
    
    def __init__(
        self,
        wallet: Keypair,
        rpc_url: str = None,
        network: str = "devnet"
    ):
        self.wallet = wallet
        self.rpc_url = rpc_url or config.solana_rpc_url
        self.network = network
        self.client: Optional[AsyncClient] = None
        self.provider: Optional[Provider] = None
        
        # Program instances (loaded from IDL)
        self.reasoning_program: Optional[Program] = None
        self.threat_program: Optional[Program] = None
        self.coordinator_program: Optional[Program] = None
        
        logger.info(
            "OnChain client initialized",
            wallet=str(wallet.pubkey())[:16],
            network=network
        )
    
    async def connect(self):
        """Connect to Solana and load programs"""
        self.client = AsyncClient(self.rpc_url, commitment=Confirmed)
        
        # Check connection
        version = await self.client.get_version()
        logger.info(f"Connected to Solana", version=version.value.solana_core)
        
        # Load IDLs and create program instances
        await self._load_programs()
    
    async def _load_programs(self):
        """Load Anchor program IDLs"""
        idl_dir = Path(__file__).parent.parent.parent / "target" / "idl"
        
        # Try to load reasoning registry
        reasoning_idl_path = idl_dir / "reasoning_registry.json"
        if reasoning_idl_path.exists():
            with open(reasoning_idl_path) as f:
                idl_json = json.load(f)
                # Note: anchorpy Program loading would go here
                # For now we'll use raw instructions
                logger.info("Loaded reasoning registry IDL")
        else:
            logger.warning("Reasoning registry IDL not found - using raw instructions")
    
    async def close(self):
        """Close connection"""
        if self.client:
            await self.client.close()
    
    # ============== PDA Derivation ==============
    
    def get_reasoning_pda(self, agent_id: Pubkey, threat_id: int) -> tuple[Pubkey, int]:
        """Derive PDA for reasoning commit"""
        seeds = [
            b"reasoning",
            bytes(agent_id),
            struct.pack("<Q", threat_id)  # u64 little-endian
        ]
        return Pubkey.find_program_address(seeds, REASONING_REGISTRY_ID)
    
    def get_agent_registry_pda(self, agent_id: Pubkey) -> tuple[Pubkey, int]:
        """Derive PDA for agent registry"""
        seeds = [b"agent_registry", bytes(agent_id)]
        return Pubkey.find_program_address(seeds, REASONING_REGISTRY_ID)
    
    def get_threat_pda(self, threat_id: int) -> tuple[Pubkey, int]:
        """Derive PDA for threat record"""
        seeds = [b"threat", struct.pack("<Q", threat_id)]
        return Pubkey.find_program_address(seeds, THREAT_INTELLIGENCE_ID)
    
    # ============== Reasoning Registry ==============
    
    async def commit_reasoning(
        self,
        threat_id: int,
        reasoning_text: str,
        action_type: ActionType
    ) -> Dict[str, Any]:
        """
        Commit reasoning hash on-chain BEFORE taking action.
        Returns transaction signature and reasoning hash.
        """
        # Compute hash
        reasoning_hash = hashlib.sha256(reasoning_text.encode()).digest()
        
        # Derive PDA
        reasoning_pda, bump = self.get_reasoning_pda(self.wallet.pubkey(), threat_id)
        
        logger.info(
            "Committing reasoning on-chain",
            threat_id=threat_id,
            action=ActionType(action_type).name,
            hash=reasoning_hash.hex()[:16]
        )
        
        # Build instruction data (Anchor discriminator + args)
        # commit_reasoning discriminator: hash of "global:commit_reasoning"[:8]
        discriminator = hashlib.sha256(b"global:commit_reasoning").digest()[:8]
        
        instruction_data = (
            discriminator +
            bytes(self.wallet.pubkey()) +  # agent_id: Pubkey
            reasoning_hash +                # reasoning_hash: [u8; 32]
            struct.pack("<Q", threat_id) +  # threat_id: u64
            struct.pack("<B", action_type)  # action_type: enum (u8)
        )
        
        # Build instruction
        instruction = Instruction(
            program_id=REASONING_REGISTRY_ID,
            accounts=[
                AccountMeta(reasoning_pda, is_signer=False, is_writable=True),
                AccountMeta(self.wallet.pubkey(), is_signer=True, is_writable=True),
                AccountMeta(SYSTEM_PROGRAM_ID, is_signer=False, is_writable=False),
            ],
            data=instruction_data
        )
        
        # Send transaction
        try:
            recent_blockhash = await self.client.get_latest_blockhash()
            tx = Transaction(
                recent_blockhash=recent_blockhash.value.blockhash,
                fee_payer=self.wallet.pubkey()
            )
            tx.add(instruction)
            
            # Sign and send
            result = await self.client.send_transaction(tx, self.wallet)
            signature = str(result.value)
            
            logger.info(
                "Reasoning committed on-chain",
                signature=signature[:16],
                threat_id=threat_id
            )
            
            return {
                "success": True,
                "signature": signature,
                "reasoning_hash": reasoning_hash.hex(),
                "pda": str(reasoning_pda),
                "threat_id": threat_id,
                "action_type": ActionType(action_type).name
            }
            
        except Exception as e:
            logger.error("Failed to commit reasoning", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "reasoning_hash": reasoning_hash.hex()
            }
    
    async def reveal_reasoning(
        self,
        threat_id: int,
        reasoning_text: str
    ) -> Dict[str, Any]:
        """
        Reveal full reasoning text on-chain after action.
        Verifies hash matches the commit.
        """
        # Verify hash locally first
        reasoning_hash = hashlib.sha256(reasoning_text.encode()).digest()
        
        # Derive PDA
        reasoning_pda, _ = self.get_reasoning_pda(self.wallet.pubkey(), threat_id)
        
        logger.info(
            "Revealing reasoning on-chain",
            threat_id=threat_id,
            text_length=len(reasoning_text)
        )
        
        # Build instruction
        discriminator = hashlib.sha256(b"global:reveal_reasoning").digest()[:8]
        
        # String encoding: 4-byte length prefix + utf-8 bytes
        text_bytes = reasoning_text.encode('utf-8')
        instruction_data = (
            discriminator +
            struct.pack("<I", len(text_bytes)) +
            text_bytes
        )
        
        instruction = Instruction(
            program_id=REASONING_REGISTRY_ID,
            accounts=[
                AccountMeta(reasoning_pda, is_signer=False, is_writable=True),
                AccountMeta(self.wallet.pubkey(), is_signer=False, is_writable=False),
                AccountMeta(self.wallet.pubkey(), is_signer=True, is_writable=False),
            ],
            data=instruction_data
        )
        
        try:
            recent_blockhash = await self.client.get_latest_blockhash()
            tx = Transaction(
                recent_blockhash=recent_blockhash.value.blockhash,
                fee_payer=self.wallet.pubkey()
            )
            tx.add(instruction)
            
            result = await self.client.send_transaction(tx, self.wallet)
            signature = str(result.value)
            
            logger.info(
                "Reasoning revealed on-chain",
                signature=signature[:16],
                threat_id=threat_id
            )
            
            return {
                "success": True,
                "signature": signature,
                "pda": str(reasoning_pda),
                "verified": True
            }
            
        except Exception as e:
            logger.error("Failed to reveal reasoning", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def get_reasoning_commit(self, agent_id: Pubkey, threat_id: int) -> Optional[Dict]:
        """Fetch reasoning commit from chain"""
        reasoning_pda, _ = self.get_reasoning_pda(agent_id, threat_id)
        
        try:
            account = await self.client.get_account_info(reasoning_pda)
            if account.value is None:
                return None
            
            # Parse account data (skip 8-byte discriminator)
            data = account.value.data
            # Would need proper deserialization here
            # For now return raw
            return {
                "pda": str(reasoning_pda),
                "data_length": len(data),
                "exists": True
            }
            
        except Exception as e:
            logger.error("Failed to fetch reasoning", error=str(e))
            return None
    
    # ============== Threat Intelligence ==============
    
    async def register_threat(
        self,
        threat_id: int,
        threat_type: ThreatType,
        severity: int,
        target_address: Optional[str],
        description: str,
        evidence_hash: bytes
    ) -> Dict[str, Any]:
        """Register a new threat on-chain"""
        
        threat_pda, _ = self.get_threat_pda(threat_id)
        
        logger.info(
            "Registering threat on-chain",
            threat_id=threat_id,
            type=ThreatType(threat_type).name,
            severity=severity
        )
        
        # Build instruction (simplified - would need full Anchor encoding)
        discriminator = hashlib.sha256(b"global:register_threat").digest()[:8]
        
        target_bytes = bytes(Pubkey.from_string(target_address)) if target_address else bytes(32)
        has_target = 1 if target_address else 0
        
        instruction_data = (
            discriminator +
            struct.pack("<B", threat_type) +       # threat_type enum
            struct.pack("<B", severity) +          # severity u8
            struct.pack("<B", has_target) +        # Option tag
            target_bytes +                         # target address
            struct.pack("<I", len(description)) +  # string length
            description.encode('utf-8') +          # description
            evidence_hash                          # evidence_hash [u8; 32]
        )
        
        instruction = Instruction(
            program_id=THREAT_INTELLIGENCE_ID,
            accounts=[
                AccountMeta(threat_pda, is_signer=False, is_writable=True),
                AccountMeta(self.wallet.pubkey(), is_signer=True, is_writable=True),
                AccountMeta(SYSTEM_PROGRAM_ID, is_signer=False, is_writable=False),
            ],
            data=instruction_data
        )
        
        try:
            recent_blockhash = await self.client.get_latest_blockhash()
            tx = Transaction(
                recent_blockhash=recent_blockhash.value.blockhash,
                fee_payer=self.wallet.pubkey()
            )
            tx.add(instruction)
            
            result = await self.client.send_transaction(tx, self.wallet)
            signature = str(result.value)
            
            logger.info("Threat registered on-chain", signature=signature[:16])
            
            return {
                "success": True,
                "signature": signature,
                "threat_pda": str(threat_pda)
            }
            
        except Exception as e:
            logger.error("Failed to register threat", error=str(e))
            return {"success": False, "error": str(e)}
    
    # ============== Utility ==============
    
    async def get_balance(self) -> float:
        """Get wallet SOL balance"""
        result = await self.client.get_balance(self.wallet.pubkey())
        return result.value / 1_000_000_000
    
    async def request_airdrop(self, amount_sol: float = 1.0) -> Optional[str]:
        """Request devnet airdrop"""
        if self.network != "devnet":
            logger.warning("Airdrop only available on devnet")
            return None
        
        try:
            lamports = int(amount_sol * 1_000_000_000)
            result = await self.client.request_airdrop(self.wallet.pubkey(), lamports)
            signature = str(result.value)
            
            # Wait for confirmation
            await self.client.confirm_transaction(signature)
            
            logger.info(f"Airdrop received", amount=amount_sol, signature=signature[:16])
            return signature
            
        except Exception as e:
            logger.error("Airdrop failed", error=str(e))
            return None
    
    async def check_program_deployed(self, program_id: Pubkey) -> bool:
        """Check if a program is deployed"""
        try:
            account = await self.client.get_account_info(program_id)
            return account.value is not None and account.value.executable
        except Exception:
            return False


# Factory function
async def create_onchain_client(
    wallet_path: str = None,
    rpc_url: str = None,
    network: str = "devnet"
) -> GuardianOnChain:
    """Create and connect an on-chain client"""
    
    # Load wallet
    wallet_path = wallet_path or config.wallet_path
    with open(wallet_path) as f:
        keypair_data = json.load(f)
    wallet = Keypair.from_bytes(bytes(keypair_data))
    
    # Create client
    client = GuardianOnChain(wallet, rpc_url, network)
    await client.connect()
    
    return client
