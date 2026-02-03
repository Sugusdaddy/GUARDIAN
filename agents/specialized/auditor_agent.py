"""
AUDITOR Agent - Reasoning Verification & Integrity
Ensures all agent decisions are transparent and verifiable
"""
import asyncio
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional

from ..core.base_agent import AutonomousAgent, Threat, Decision
from ..core.config import AgentConfig, config


class AuditorAgent(AutonomousAgent):
    """
    AUDITOR - The Verifier
    
    Ensures integrity of the agent swarm:
    - Verifies reasoning commits match reveals
    - Audits agent decisions
    - Detects compromised agents
    - Maintains transparency standards
    """
    
    def __init__(self, config: AgentConfig = config):
        super().__init__(
            role="AUDITOR",
            agent_type="Auditor",
            capabilities=[
                "reasoning_verification",
                "decision_auditing",
                "integrity_checking",
                "transparency_enforcement"
            ],
            config=config
        )
        
        # Audit records
        self.pending_audits: List[Dict] = []
        self.completed_audits: List[Dict] = []
        self.failed_audits: List[Dict] = []
        
        # Verification cache
        self.verified_hashes: Dict[str, bool] = {}
        
        # Agent reputation tracking
        self.agent_integrity_scores: Dict[str, float] = {}
        
        # Statistics
        self.total_verifications = 0
        self.verification_failures = 0
        
        self.log.info("✅ Auditor agent ready for verification")
    
    async def scan_environment(self) -> List[Threat]:
        """Auditor scans for verification needs"""
        threats = []
        
        # Check pending audits
        for audit in self.pending_audits[:10]:  # Process 10 at a time
            result = await self.verify_audit(audit)
            
            if not result["verified"]:
                # Create threat for failed verification
                threats.append(Threat(
                    id=self.get_next_threat_id(),
                    threat_type="IntegrityViolation",
                    severity=95,
                    target_address=None,
                    description=f"Agent {audit.get('agent')} failed verification: {result.get('reason')}",
                    evidence={
                        "audit": audit,
                        "result": result
                    },
                    detected_by="Auditor"
                ))
            
            self.pending_audits.remove(audit)
        
        # Periodically audit random past decisions
        if self.total_verifications % 50 == 0:
            random_audits = await self.random_audit()
            threats.extend(random_audits)
        
        return threats
    
    async def execute_action(self, decision: Decision, threat: Threat) -> Dict[str, Any]:
        """Execute auditing actions"""
        
        result = {"status": "success", "action": decision.action}
        
        if threat.threat_type == "IntegrityViolation":
            # Handle integrity violation
            await self.handle_integrity_violation(threat)
            result["violation_handled"] = True
        
        return result
    
    async def queue_for_audit(self, agent: str, reasoning_hash: str, 
                              threat_id: int, action: str):
        """Queue a decision for auditing"""
        
        self.pending_audits.append({
            "agent": agent,
            "reasoning_hash": reasoning_hash,
            "threat_id": threat_id,
            "action": action,
            "queued_at": datetime.now().isoformat(),
            "status": "pending"
        })
        
        self.log.debug(f"📋 Queued audit for {agent} on threat #{threat_id}")
    
    async def verify_audit(self, audit: Dict) -> Dict:
        """Verify a queued audit"""
        
        self.total_verifications += 1
        
        # Find the corresponding reveal
        reasoning_text = audit.get("reasoning_text")
        
        if not reasoning_text:
            # Reasoning not yet revealed - keep in queue
            return {"verified": True, "reason": "awaiting_reveal"}
        
        # Verify hash
        computed_hash = hashlib.sha256(reasoning_text.encode()).hexdigest()
        expected_hash = audit.get("reasoning_hash")
        
        if computed_hash == expected_hash:
            # Verification passed
            self.completed_audits.append({
                **audit,
                "verified": True,
                "verified_at": datetime.now().isoformat()
            })
            
            # Update agent integrity score
            self._update_integrity_score(audit["agent"], True)
            
            self.verified_hashes[expected_hash] = True
            
            return {"verified": True, "computed_hash": computed_hash}
        else:
            # Verification FAILED
            self.verification_failures += 1
            
            self.failed_audits.append({
                **audit,
                "verified": False,
                "expected_hash": expected_hash,
                "computed_hash": computed_hash,
                "failed_at": datetime.now().isoformat()
            })
            
            # Update agent integrity score
            self._update_integrity_score(audit["agent"], False)
            
            self.log.error(
                f"❌ VERIFICATION FAILED for {audit['agent']} on threat #{audit['threat_id']}"
            )
            
            return {
                "verified": False,
                "reason": "hash_mismatch",
                "expected": expected_hash[:16],
                "computed": computed_hash[:16]
            }
    
    def _update_integrity_score(self, agent: str, success: bool):
        """Update an agent's integrity score"""
        
        current = self.agent_integrity_scores.get(agent, 100.0)
        
        if success:
            # Small increase for success
            new_score = min(100.0, current + 0.1)
        else:
            # Large decrease for failure
            new_score = max(0.0, current - 10.0)
        
        self.agent_integrity_scores[agent] = new_score
        
        if new_score < 50:
            self.log.warning(f"⚠️ Agent {agent} integrity score critical: {new_score}")
    
    async def random_audit(self) -> List[Threat]:
        """Perform random audits on past decisions"""
        threats = []
        
        # Select random completed audits to re-verify
        import random
        if self.completed_audits:
            samples = random.sample(
                self.completed_audits, 
                min(5, len(self.completed_audits))
            )
            
            for audit in samples:
                # Re-verify
                if audit.get("reasoning_text"):
                    result = await self.verify_audit(audit)
                    if not result["verified"]:
                        threats.append(Threat(
                            id=self.get_next_threat_id(),
                            threat_type="RetrospectiveViolation",
                            severity=99,
                            target_address=None,
                            description=f"Retrospective audit failure for {audit['agent']}",
                            evidence={"audit": audit, "result": result},
                            detected_by="Auditor"
                        ))
        
        return threats
    
    async def handle_integrity_violation(self, threat: Threat):
        """Handle a detected integrity violation"""
        
        audit = threat.evidence.get("audit", {})
        agent_name = audit.get("agent")
        
        # Alert all agents about compromised agent
        for agent in self.other_agents:
            if hasattr(agent, 'receive_integrity_alert'):
                await agent.receive_integrity_alert(agent_name, threat)
        
        self.log.error(f"🚨 INTEGRITY VIOLATION: Agent {agent_name} may be compromised!")
    
    def get_agent_integrity(self, agent: str) -> float:
        """Get integrity score for an agent"""
        return self.agent_integrity_scores.get(agent, 100.0)
    
    async def get_current_intelligence(self) -> Dict:
        """Return Auditor's current state"""
        return {
            "pending_audits": len(self.pending_audits),
            "completed_audits": len(self.completed_audits),
            "failed_audits": len(self.failed_audits),
            "verification_rate": (
                (self.total_verifications - self.verification_failures) / 
                max(1, self.total_verifications) * 100
            ),
            "agent_scores": self.agent_integrity_scores,
            "active": self.running,
            "capabilities": self.capabilities
        }
    
    async def propose_strategy(self, threat: Threat) -> Dict:
        """Auditor's proposal - verification requirements"""
        
        return {
            "agent": "Auditor",
            "strategy": "Verify all reasoning before and after action",
            "confidence": 0.99,
            "requirements": [
                "reasoning_commit_before_action",
                "reasoning_reveal_after_action",
                "hash_verification"
            ]
        }
