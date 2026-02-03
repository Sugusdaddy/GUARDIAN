"""
HONEYPOT Agent - Active Defense via Bait Wallets

Deploys configurable bait wallets to lure attackers, captures their
tools, methods, and fund flow patterns. Builds attacker profiles
and auto-blacklists malicious actors.

Offense as defense - catch them before they catch you.
"""

import asyncio
import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum

from agents.core.base_agent import BaseAgent


class HoneypotType(Enum):
    """Types of honeypot deployments"""
    LOW_VALUE = "low_value"           # Small bait (0.1-1 SOL)
    MEDIUM_VALUE = "medium_value"     # Medium bait (1-10 SOL)
    HIGH_VALUE = "high_value"         # High-value target (10+ SOL)
    TOKEN_APPROVAL = "token_approval" # Fake token approvals
    NFT_BAIT = "nft_bait"            # Valuable-looking NFTs


class AttackType(Enum):
    """Detected attack types"""
    DRAINER = "drainer"              # Token drainer
    APPROVAL_EXPLOIT = "approval"    # Approval abuse
    PHISHING = "phishing"            # Phishing attempt
    SWEEPER = "sweeper"              # Wallet sweeper
    UNKNOWN = "unknown"


@dataclass
class HoneypotDeployment:
    """A deployed honeypot instance"""
    id: str
    address: str
    honeypot_type: HoneypotType
    bait_amount_sol: float
    deployed_at: datetime
    is_active: bool = True
    interactions: List[Dict] = field(default_factory=list)
    attackers_caught: List[str] = field(default_factory=list)


@dataclass
class AttackerProfile:
    """Profile of a caught attacker"""
    address: str
    first_seen: datetime
    last_seen: datetime
    attack_types: Set[AttackType]
    tool_signatures: List[str]
    fund_destinations: List[str]
    total_interactions: int
    honeypots_triggered: List[str]
    risk_score: int  # 0-100


class HoneypotAgent(BaseAgent):
    """
    🪤 HONEYPOT DEFENSE - Active Trap Agent
    
    Deploys bait wallets to catch attackers in the act.
    Captures tools, methods, and fund flow patterns.
    
    Features:
    - Deploy configurable bait wallets
    - Monitor honeypots in real-time (2-minute intervals)
    - Capture attacker tool signatures
    - Profile attacker TTPs (Tactics, Techniques, Procedures)
    - Auto-blacklist malicious actors
    - Track fund flow from stolen funds
    - Generate attacker intelligence reports
    
    "The best defense is understanding your enemy."
    """
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(
            name="HONEYPOT",
            role="Active Defense",
            description="Bait wallet traps for catching attackers",
            config=config
        )
        
        # Deployment configuration
        self.config = {
            "monitoring_interval_seconds": 120,  # 2 minutes
            "max_active_honeypots": 10,
            "default_bait_amounts": {
                HoneypotType.LOW_VALUE: 0.5,
                HoneypotType.MEDIUM_VALUE: 2.0,
                HoneypotType.HIGH_VALUE: 10.0,
                HoneypotType.TOKEN_APPROVAL: 0.1,
                HoneypotType.NFT_BAIT: 0.1
            }
        }
        
        # Active deployments
        self.deployments: Dict[str, HoneypotDeployment] = {}
        
        # Attacker database
        self.attackers: Dict[str, AttackerProfile] = {}
        
        # Known drainer signatures (program hashes, patterns)
        self.known_drainer_signatures: Set[str] = set()
        
        # Statistics
        self.stats = {
            "honeypots_deployed": 0,
            "attackers_caught": 0,
            "attacks_detected": 0,
            "total_bait_deployed_sol": 0.0
        }
    
    async def deploy_honeypot(
        self,
        honeypot_type: HoneypotType = HoneypotType.LOW_VALUE,
        custom_bait_amount: Optional[float] = None
    ) -> HoneypotDeployment:
        """
        Deploy a new honeypot bait wallet.
        
        Args:
            honeypot_type: Type of honeypot to deploy
            custom_bait_amount: Override default bait amount
        
        Returns:
            HoneypotDeployment with wallet details
        """
        # Check deployment limits
        active_count = sum(1 for d in self.deployments.values() if d.is_active)
        if active_count >= self.config["max_active_honeypots"]:
            self.log_warning("Maximum active honeypots reached")
            raise ValueError("Maximum honeypot limit reached")
        
        # Generate honeypot ID
        honeypot_id = f"HP-{secrets.token_hex(4).upper()}"
        
        # Generate bait wallet (in production, this would create a real keypair)
        # For safety, we use a deterministic but random-looking address
        fake_address = f"Honey{secrets.token_hex(20)}"[:44]
        
        # Determine bait amount
        bait_amount = custom_bait_amount or self.config["default_bait_amounts"][honeypot_type]
        
        deployment = HoneypotDeployment(
            id=honeypot_id,
            address=fake_address,
            honeypot_type=honeypot_type,
            bait_amount_sol=bait_amount,
            deployed_at=datetime.now(timezone.utc)
        )
        
        self.deployments[honeypot_id] = deployment
        self.stats["honeypots_deployed"] += 1
        self.stats["total_bait_deployed_sol"] += bait_amount
        
        self.log_info(
            f"🪤 Honeypot deployed: {honeypot_id}\n"
            f"   Type: {honeypot_type.value}\n"
            f"   Bait: {bait_amount} SOL\n"
            f"   Address: {fake_address[:16]}..."
        )
        
        # Start monitoring (in production, this would set up webhooks)
        asyncio.create_task(self._monitor_honeypot(honeypot_id))
        
        return deployment
    
    async def _monitor_honeypot(self, honeypot_id: str):
        """
        Monitor a honeypot for interactions.
        Runs every 2 minutes while honeypot is active.
        """
        while honeypot_id in self.deployments:
            deployment = self.deployments[honeypot_id]
            if not deployment.is_active:
                break
            
            # Check for interactions (would query RPC in production)
            interactions = await self._check_interactions(deployment.address)
            
            for interaction in interactions:
                await self._process_interaction(honeypot_id, interaction)
            
            await asyncio.sleep(self.config["monitoring_interval_seconds"])
    
    async def _check_interactions(self, address: str) -> List[Dict]:
        """
        Check for new interactions with a honeypot address.
        Would integrate with Helius webhooks in production.
        """
        # Placeholder - would fetch recent transactions
        return []
    
    async def _process_interaction(self, honeypot_id: str, interaction: Dict):
        """
        Process a honeypot interaction - potential attacker caught!
        """
        self.stats["attacks_detected"] += 1
        deployment = self.deployments[honeypot_id]
        
        attacker_address = interaction.get("from_address")
        attack_type = self._classify_attack(interaction)
        tool_signature = self._extract_tool_signature(interaction)
        
        # Record interaction
        deployment.interactions.append({
            "attacker": attacker_address,
            "attack_type": attack_type.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "transaction_signature": interaction.get("signature"),
            "tool_signature": tool_signature
        })
        
        # Update or create attacker profile
        if attacker_address not in self.attackers:
            self.attackers[attacker_address] = AttackerProfile(
                address=attacker_address,
                first_seen=datetime.now(timezone.utc),
                last_seen=datetime.now(timezone.utc),
                attack_types={attack_type},
                tool_signatures=[tool_signature] if tool_signature else [],
                fund_destinations=[],
                total_interactions=0,
                honeypots_triggered=[],
                risk_score=50
            )
            self.stats["attackers_caught"] += 1
            deployment.attackers_caught.append(attacker_address)
        
        profile = self.attackers[attacker_address]
        profile.last_seen = datetime.now(timezone.utc)
        profile.attack_types.add(attack_type)
        profile.total_interactions += 1
        profile.honeypots_triggered.append(honeypot_id)
        if tool_signature:
            profile.tool_signatures.append(tool_signature)
        
        # Increase risk score
        profile.risk_score = min(100, profile.risk_score + 10)
        
        # Auto-blacklist
        await self._blacklist_attacker(attacker_address, profile)
        
        self.log_warning(
            f"🎯 ATTACKER CAUGHT!\n"
            f"   Honeypot: {honeypot_id}\n"
            f"   Attacker: {attacker_address[:16]}...\n"
            f"   Attack Type: {attack_type.value}\n"
            f"   Risk Score: {profile.risk_score}"
        )
        
        # Emit event for swarm
        await self.emit_event("attacker_caught", {
            "honeypot_id": honeypot_id,
            "attacker": attacker_address,
            "attack_type": attack_type.value,
            "risk_score": profile.risk_score
        })
    
    def _classify_attack(self, interaction: Dict) -> AttackType:
        """Classify the type of attack based on interaction pattern."""
        # Would analyze transaction data to classify
        # Placeholder logic
        if interaction.get("involves_approval"):
            return AttackType.APPROVAL_EXPLOIT
        elif interaction.get("drains_all"):
            return AttackType.DRAINER
        elif interaction.get("sweeps_tokens"):
            return AttackType.SWEEPER
        return AttackType.UNKNOWN
    
    def _extract_tool_signature(self, interaction: Dict) -> Optional[str]:
        """Extract unique signature of attacker's tool/script."""
        # Would hash program invocations, patterns, etc.
        if "program_id" in interaction:
            return hashlib.sha256(
                interaction["program_id"].encode()
            ).hexdigest()[:16]
        return None
    
    async def _blacklist_attacker(self, address: str, profile: AttackerProfile):
        """Add attacker to global blacklist."""
        # Emit blacklist event for Intel agent
        await self.emit_event("blacklist_address", {
            "address": address,
            "reason": "honeypot_triggered",
            "risk_score": profile.risk_score,
            "attack_types": [t.value for t in profile.attack_types]
        })
    
    async def get_deployments(self, active_only: bool = True) -> List[Dict]:
        """Get all honeypot deployments."""
        deployments = []
        for d in self.deployments.values():
            if active_only and not d.is_active:
                continue
            deployments.append({
                "id": d.id,
                "address": d.address,
                "type": d.honeypot_type.value,
                "bait_amount": d.bait_amount_sol,
                "deployed_at": d.deployed_at.isoformat(),
                "is_active": d.is_active,
                "interactions_count": len(d.interactions),
                "attackers_caught": len(d.attackers_caught)
            })
        return deployments
    
    async def get_attacker_profile(self, address: str) -> Optional[Dict]:
        """Get detailed profile of a caught attacker."""
        if address not in self.attackers:
            return None
        
        profile = self.attackers[address]
        return {
            "address": profile.address,
            "first_seen": profile.first_seen.isoformat(),
            "last_seen": profile.last_seen.isoformat(),
            "attack_types": [t.value for t in profile.attack_types],
            "tool_signatures": profile.tool_signatures,
            "total_interactions": profile.total_interactions,
            "honeypots_triggered": profile.honeypots_triggered,
            "risk_score": profile.risk_score
        }
    
    async def deactivate_honeypot(self, honeypot_id: str) -> bool:
        """Deactivate a honeypot deployment."""
        if honeypot_id in self.deployments:
            self.deployments[honeypot_id].is_active = False
            self.log_info(f"Honeypot {honeypot_id} deactivated")
            return True
        return False
    
    async def process_task(self, task: Dict) -> Dict:
        """Process incoming tasks."""
        task_type = task.get("type")
        
        if task_type == "deploy":
            honeypot_type = HoneypotType(task.get("honeypot_type", "low_value"))
            deployment = await self.deploy_honeypot(
                honeypot_type=honeypot_type,
                custom_bait_amount=task.get("bait_amount")
            )
            return {
                "success": True,
                "deployment": {
                    "id": deployment.id,
                    "address": deployment.address,
                    "type": deployment.honeypot_type.value,
                    "bait_amount": deployment.bait_amount_sol
                }
            }
        
        elif task_type == "get_deployments":
            return {
                "success": True,
                "deployments": await self.get_deployments(
                    active_only=task.get("active_only", True)
                )
            }
        
        elif task_type == "get_attacker":
            profile = await self.get_attacker_profile(task["address"])
            return {
                "success": profile is not None,
                "profile": profile
            }
        
        elif task_type == "deactivate":
            success = await self.deactivate_honeypot(task["honeypot_id"])
            return {"success": success}
        
        elif task_type == "get_statistics":
            return {"success": True, "statistics": self.stats}
        
        return {"success": False, "error": f"Unknown task type: {task_type}"}
