"""
HEALER Agent - Fund Recovery & Remediation
Attempts to recover funds and help affected users
"""
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional

from ..core.base_agent import AutonomousAgent, Threat, Decision
from ..core.config import AgentConfig, config


class HealerAgent(AutonomousAgent):
    """
    HEALER - The Restorer
    
    Attempts fund recovery and user remediation:
    - Monitors for recovery opportunities
    - Coordinates with affected users
    - Executes recovery transactions
    - Provides post-incident support
    """
    
    def __init__(self, config: AgentConfig = config):
        super().__init__(
            role="HEALER",
            agent_type="Healer",
            capabilities=[
                "fund_recovery",
                "user_support",
                "remediation",
                "post_incident_analysis"
            ],
            config=config
        )
        
        # Recovery tracking
        self.active_recoveries: Dict[str, Dict] = {}
        self.completed_recoveries: List[Dict] = []
        self.failed_recoveries: List[Dict] = []
        
        # Affected users registry
        self.affected_users: Dict[str, List[Dict]] = {}  # threat_id -> list of affected users
        
        # Statistics
        self.total_recovered_sol = 0.0
        self.total_recovered_usd = 0.0
        self.users_helped = 0
        
        self.log.info("💚 Healer agent ready for recovery operations")
    
    async def scan_environment(self) -> List[Threat]:
        """Healer scans for recovery opportunities"""
        threats = []
        
        # Monitor active recoveries
        for recovery_id, recovery in list(self.active_recoveries.items()):
            result = await self.check_recovery_opportunity(recovery)
            
            if result.get("opportunity_found"):
                threats.append(Threat(
                    id=self.get_next_threat_id(),
                    threat_type="RecoveryOpportunity",
                    severity=30,  # Lower severity - it's a positive action
                    target_address=result.get("target_address"),
                    description=f"Recovery opportunity found for {recovery['threat_id']}",
                    evidence={
                        "recovery_id": recovery_id,
                        "opportunity": result
                    },
                    detected_by="Healer"
                ))
            
            if result.get("complete"):
                recovery["status"] = "complete"
                recovery["result"] = result
                self.completed_recoveries.append(recovery)
                del self.active_recoveries[recovery_id]
        
        return threats
    
    async def execute_action(self, decision: Decision, threat: Threat) -> Dict[str, Any]:
        """Execute healing actions"""
        
        result = {"status": "success", "action": decision.action}
        
        if threat.threat_type == "RecoveryOpportunity":
            # Attempt recovery
            recovery_result = await self.attempt_recovery(threat)
            result["recovery_attempted"] = True
            result["recovery_result"] = recovery_result
        
        elif decision.action in ["BLOCK", "COORDINATE"]:
            # Register threat for recovery monitoring
            await self.register_for_recovery(threat)
            result["registered_for_recovery"] = True
        
        return result
    
    async def register_for_recovery(self, threat: Threat):
        """Register a threat for recovery monitoring"""
        
        recovery_id = f"REC-{threat.id}"
        
        self.active_recoveries[recovery_id] = {
            "recovery_id": recovery_id,
            "threat_id": threat.id,
            "threat_type": threat.threat_type,
            "target_address": threat.target_address,
            "registered_at": datetime.now().isoformat(),
            "status": "monitoring",
            "checks": 0,
            "max_checks": 100  # Stop after 100 checks
        }
        
        self.log.info(f"💚 Registered threat #{threat.id} for recovery monitoring")
    
    async def check_recovery_opportunity(self, recovery: Dict) -> Dict:
        """Check for recovery opportunities"""
        
        recovery["checks"] += 1
        
        result = {
            "opportunity_found": False,
            "complete": False
        }
        
        # Check if max checks reached
        if recovery["checks"] >= recovery["max_checks"]:
            result["complete"] = True
            result["reason"] = "max_checks_reached"
            return result
        
        # Check for stuck funds in contracts
        # This is a placeholder - real implementation would:
        # 1. Monitor for liquidity being added back
        # 2. Check for governance/admin functions
        # 3. Look for time-locked funds becoming available
        
        target = recovery.get("target_address")
        if target:
            # Check account balance
            try:
                response = await self.solana.get_balance(
                    Pubkey.from_string(target) if isinstance(target, str) else target
                )
                
                balance_sol = response.value / 1_000_000_000 if response.value else 0
                
                if balance_sol > 0.1:  # Some funds available
                    result["opportunity_found"] = True
                    result["available_sol"] = balance_sol
                    result["target_address"] = target
                    
            except Exception as e:
                self.log.debug(f"Error checking balance", error=str(e))
        
        return result
    
    async def attempt_recovery(self, threat: Threat) -> Dict:
        """Attempt to recover funds"""
        
        self.log.info(f"💚 Attempting recovery for threat #{threat.id}")
        
        # This is a placeholder - real implementation would:
        # 1. Identify recovery mechanism (admin function, timelock, etc.)
        # 2. Prepare recovery transaction
        # 3. Execute with proper authorization
        # 4. Distribute recovered funds to affected users
        
        recovery_result = {
            "success": False,
            "amount_sol": 0,
            "reason": "manual_intervention_required",
            "timestamp": datetime.now().isoformat()
        }
        
        # For now, just log the attempt
        self.log.info(
            f"⚠️ Recovery for threat #{threat.id} requires manual intervention"
        )
        
        return recovery_result
    
    async def register_affected_user(self, threat_id: int, user_address: str, 
                                     estimated_loss: float):
        """Register a user affected by a threat"""
        
        if str(threat_id) not in self.affected_users:
            self.affected_users[str(threat_id)] = []
        
        self.affected_users[str(threat_id)].append({
            "user_address": user_address,
            "estimated_loss_sol": estimated_loss,
            "registered_at": datetime.now().isoformat(),
            "recovery_status": "pending"
        })
        
        self.users_helped += 1
        self.log.info(f"📝 Registered affected user for threat #{threat_id}")
    
    async def distribute_recovered_funds(self, threat_id: int, amount_sol: float):
        """Distribute recovered funds to affected users"""
        
        affected = self.affected_users.get(str(threat_id), [])
        
        if not affected:
            self.log.warning(f"No affected users registered for threat #{threat_id}")
            return
        
        # Calculate pro-rata distribution
        total_losses = sum(u["estimated_loss_sol"] for u in affected)
        
        for user in affected:
            share = (user["estimated_loss_sol"] / total_losses) * amount_sol
            user["recovery_amount"] = share
            user["recovery_status"] = "distributed"
            
            # Would execute actual distribution transaction here
            self.log.info(
                f"💚 Distributed {share:.4f} SOL to {user['user_address'][:16]}..."
            )
        
        self.total_recovered_sol += amount_sol
    
    async def get_current_intelligence(self) -> Dict:
        """Return Healer's current state"""
        return {
            "active_recoveries": len(self.active_recoveries),
            "completed_recoveries": len(self.completed_recoveries),
            "failed_recoveries": len(self.failed_recoveries),
            "total_recovered_sol": self.total_recovered_sol,
            "users_helped": self.users_helped,
            "active": self.running,
            "capabilities": self.capabilities
        }
    
    async def propose_strategy(self, threat: Threat) -> Dict:
        """Healer's proposal - recovery strategy"""
        
        # Check if this threat type typically allows recovery
        recoverable_types = ["RugPull", "DrainAttack", "FlashLoanAttack"]
        
        if threat.threat_type in recoverable_types:
            return {
                "agent": "Healer",
                "strategy": "Monitor for recovery opportunities",
                "confidence": 0.6,
                "recovery_likelihood": "medium"
            }
        else:
            return {
                "agent": "Healer",
                "strategy": "Limited recovery potential - focus on prevention",
                "confidence": 0.4,
                "recovery_likelihood": "low"
            }


# Import for type hints
from solders.pubkey import Pubkey
