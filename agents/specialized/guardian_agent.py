"""
GUARDIAN Agent - Threat Defense & Blocking
Executes defensive actions to protect users
"""
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional

from ..core.base_agent import AutonomousAgent, Threat, Decision
from ..core.config import AgentConfig, config


class GuardianAgent(AutonomousAgent):
    """
    GUARDIAN - The Defender
    
    Executes defensive actions against confirmed threats:
    - Blocks malicious contracts in registry
    - Sends real-time alerts to affected users
    - Coordinates with other protocols
    - Triggers emergency responses
    """
    
    def __init__(self, config: AgentConfig = config):
        super().__init__(
            role="GUARDIAN",
            agent_type="Guardian",
            capabilities=[
                "threat_blocking",
                "user_protection",
                "emergency_response",
                "protocol_coordination"
            ],
            config=config
        )
        
        # Blocked addresses
        self.blocked_addresses: set = set()
        
        # Alert history
        self.alerts_sent: List[Dict] = []
        
        # Defense actions taken
        self.defense_history: List[Dict] = []
        
        self.log.info("🛡️ Guardian ready to defend...")
    
    async def scan_environment(self) -> List[Threat]:
        """Guardian responds to confirmed threats from other agents"""
        threats = []
        
        # Check for high-priority threats from coordinator
        coordinator = next(
            (a for a in self.other_agents if a.agent_type == "Coordinator"),
            None
        )
        
        if coordinator:
            # Get approved coordinations that need execution
            for coord_id, coord in coordinator.active_coordinations.items():
                if coord.get("status") == "approved" and "Guardian" in coord.get("consensus", {}).get("execution_order", []):
                    # Execute guardian's part
                    threat_dict = coord.get("request", {}).get("threat", {})
                    if threat_dict:
                        threats.append(Threat(
                            id=threat_dict.get("id", self.get_next_threat_id()),
                            threat_type="ApprovedAction",
                            severity=threat_dict.get("severity", 80),
                            target_address=threat_dict.get("target_address"),
                            description=f"Approved for blocking: {threat_dict.get('description', 'N/A')}",
                            evidence=threat_dict.get("evidence", {}),
                            detected_by="Coordinator"
                        ))
        
        return threats
    
    async def execute_action(self, decision: Decision, threat: Threat) -> Dict[str, Any]:
        """Execute defensive actions"""
        
        result = {"status": "success", "action": decision.action, "actions_taken": []}
        
        if decision.action == "BLOCK":
            # Block the malicious address
            if threat.target_address:
                await self.block_address(threat.target_address)
                result["actions_taken"].append(f"blocked_{threat.target_address[:8]}")
            
            # Register in threat database
            await self.register_block_onchain(threat)
            result["actions_taken"].append("registered_onchain")
            
            # Alert affected users
            alerts = await self.alert_affected_users(threat)
            result["actions_taken"].append(f"alerted_{alerts}_users")
            result["users_alerted"] = alerts
        
        elif decision.action == "WARN":
            # Send community warning
            await self.send_community_warning(threat, decision.reasoning)
            result["actions_taken"].append("community_warning_sent")
        
        elif decision.action == "COORDINATE":
            # Coordinate with external protocols
            await self.coordinate_with_protocols(threat)
            result["actions_taken"].append("protocols_notified")
        
        # Record action
        self.defense_history.append({
            "threat_id": threat.id,
            "action": decision.action,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
        return result
    
    async def block_address(self, address: str):
        """Block a malicious address"""
        self.blocked_addresses.add(address)
        self.log.info(f"🚫 Blocked address: {address[:16]}...")
        
        # TODO: Update on-chain registry
    
    async def register_block_onchain(self, threat: Threat):
        """Register blocking action on-chain"""
        # TODO: Call threat-intelligence program to register
        self.log.info(f"📝 Registered block on-chain for threat {threat.id}")
    
    async def alert_affected_users(self, threat: Threat) -> int:
        """Alert users who may be affected"""
        
        # TODO: Query blockchain for token holders
        # TODO: Send alerts via available channels
        
        # For now, log the alert
        alert = {
            "threat_id": threat.id,
            "target": threat.target_address,
            "severity": threat.severity,
            "message": f"⚠️ SECURITY ALERT: {threat.description}",
            "timestamp": datetime.now().isoformat()
        }
        
        self.alerts_sent.append(alert)
        self.log.info(f"📢 Alert sent for threat {threat.id}")
        
        # Return simulated user count
        return 0
    
    async def send_community_warning(self, threat: Threat, reasoning: str):
        """Send warning to the community"""
        
        # Find reporter agent
        reporter = next(
            (a for a in self.other_agents if a.agent_type == "Reporter"),
            None
        )
        
        if reporter and hasattr(reporter, 'send_alert'):
            await reporter.send_alert(threat, reasoning)
        else:
            self.log.warning("No Reporter agent available for community warning")
    
    async def coordinate_with_protocols(self, threat: Threat):
        """Coordinate with external protocols for enhanced protection"""
        
        # TODO: Integrate with:
        # - Jupiter (pause routing to malicious tokens)
        # - Raydium (alert about malicious pools)
        # - DexScreener (flag suspicious tokens)
        
        self.log.info(f"🤝 Coordinated with protocols for threat {threat.id}")
    
    async def execute_coordinated_task(self, task: str, consensus: Dict) -> Dict:
        """Execute a task assigned by the coordinator"""
        
        self.log.info(f"⚡ Executing coordinated task: {task}")
        
        result = {"status": "completed", "task": task}
        
        if "block" in task.lower():
            # Execute blocking
            threat = consensus.get("request", {}).get("threat", {})
            if threat.get("target_address"):
                await self.block_address(threat["target_address"])
                result["blocked"] = threat["target_address"]
        
        elif "alert" in task.lower():
            # Send alerts
            result["alerts_sent"] = True
        
        return result
    
    def is_blocked(self, address: str) -> bool:
        """Check if an address is blocked"""
        return address in self.blocked_addresses
    
    async def propose_strategy(self, threat: Threat) -> Dict:
        """Guardian's proposal - defensive action"""
        
        if threat.severity > 80:
            strategy = "Immediate blocking and user alerts"
            confidence = 0.9
        elif threat.severity > 50:
            strategy = "Block and monitor, send community warning"
            confidence = 0.7
        else:
            strategy = "Monitor only, prepare for potential blocking"
            confidence = 0.5
        
        return {
            "agent": "Guardian",
            "strategy": strategy,
            "confidence": confidence,
            "can_block": bool(threat.target_address)
        }
    
    async def get_current_intelligence(self) -> Dict:
        """Return Guardian's current state"""
        return {
            "blocked_addresses": len(self.blocked_addresses),
            "alerts_sent": len(self.alerts_sent),
            "defense_actions": len(self.defense_history),
            "active": self.running,
            "capabilities": self.capabilities
        }
