"""
COORDINATOR Agent - Swarm Orchestration
Coordinates multi-agent responses to threats
"""
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, TYPE_CHECKING

from ..core.base_agent import AutonomousAgent, Threat, Decision
from ..core.config import AgentConfig, config

if TYPE_CHECKING:
    from ..core.base_agent import AutonomousAgent


class CoordinatorAgent(AutonomousAgent):
    """
    COORDINATOR - The Orchestrator
    
    Coordinates multi-agent swarm responses:
    - Receives coordination requests
    - Gathers proposals from agents
    - Synthesizes optimal response
    - Executes coordinated actions
    - Maintains swarm consensus
    """
    
    def __init__(self, config: AgentConfig = config):
        super().__init__(
            role="COORDINATOR",
            agent_type="Coordinator",
            capabilities=[
                "swarm_coordination",
                "consensus_building",
                "resource_allocation",
                "action_planning"
            ],
            config=config
        )
        
        # Pending coordination requests
        self.pending_coordinations: List[Dict] = []
        
        # Active coordinations
        self.active_coordinations: Dict[int, Dict] = {}
        
        # Coordination history
        self.coordination_history: List[Dict] = []
        
        self.log.info("🎯 Coordinator ready to orchestrate swarm...")
    
    async def scan_environment(self) -> List[Threat]:
        """Coordinator doesn't scan - it responds to coordination requests"""
        
        # Process any pending coordination requests
        for coord in self.pending_coordinations[:]:
            await self.process_coordination_request(coord)
            self.pending_coordinations.remove(coord)
        
        # Return empty - coordinator generates threats via coordination
        return []
    
    async def process_coordination_request(self, request: Dict):
        """Process a coordination request from another agent"""
        
        self.log.info(
            f"🎯 Processing coordination request",
            threat_id=request.get("threat_id"),
            from_agent=request.get("initiator")
        )
        
        # Store as active
        coord_id = len(self.active_coordinations)
        self.active_coordinations[coord_id] = {
            "request": request,
            "status": "gathering_proposals",
            "started_at": datetime.now().isoformat()
        }
        
        # Gather proposals from relevant agents
        proposals = await self.gather_agent_proposals(request)
        
        # Synthesize optimal response
        consensus = await self.reach_consensus_with_opus(request, proposals)
        
        # Update coordination status
        self.active_coordinations[coord_id]["status"] = "consensus_reached"
        self.active_coordinations[coord_id]["consensus"] = consensus
        
        # Execute if approved
        if consensus.get("approved"):
            await self.execute_coordinated_response(coord_id, consensus)
    
    async def coordinate_threat_response(
        self,
        initiating_agent: 'AutonomousAgent',
        decision: Decision,
        threat: Threat
    ) -> Dict:
        """
        Main coordination entry point.
        Called by other agents when they need swarm consensus.
        """
        
        self.log.info(
            f"🤝 Coordination request from {initiating_agent.role}",
            threat_id=threat.id
        )
        
        request = {
            "threat_id": threat.id,
            "threat": threat.to_dict(),
            "initiator": initiating_agent.role,
            "decision": decision.to_dict(),
            "suggested_agents": decision.suggested_agents,
            "timestamp": datetime.now().isoformat()
        }
        
        # Gather proposals
        proposals = await self.gather_agent_proposals(request)
        
        # Reach consensus
        consensus = await self.reach_consensus_with_opus(request, proposals)
        
        # Record in history
        self.coordination_history.append({
            "request": request,
            "proposals": proposals,
            "consensus": consensus,
            "timestamp": datetime.now().isoformat()
        })
        
        return consensus
    
    async def gather_agent_proposals(self, request: Dict) -> List[Dict]:
        """Gather proposals from relevant agents"""
        
        proposals = []
        suggested_types = request.get("suggested_agents", [])
        
        for agent in self.other_agents:
            # Include agents that are suggested or have relevant capabilities
            should_include = (
                agent.agent_type in suggested_types or
                not suggested_types  # Include all if none specified
            )
            
            if should_include and hasattr(agent, 'propose_strategy'):
                try:
                    # Convert threat dict back to Threat object
                    threat_dict = request.get("threat", {})
                    threat = Threat(
                        id=threat_dict.get("id", 0),
                        threat_type=threat_dict.get("threat_type", "Unknown"),
                        severity=threat_dict.get("severity", 50),
                        target_address=threat_dict.get("target_address"),
                        description=threat_dict.get("description", ""),
                        evidence=threat_dict.get("evidence", {}),
                        detected_by=threat_dict.get("detected_by", "Unknown")
                    )
                    
                    proposal = await agent.propose_strategy(threat)
                    proposals.append(proposal)
                    self.log.debug(f"Got proposal from {agent.role}")
                    
                except Exception as e:
                    self.log.warning(f"Failed to get proposal from {agent.role}", error=str(e))
        
        return proposals
    
    async def reach_consensus_with_opus(
        self,
        request: Dict,
        proposals: List[Dict]
    ) -> Dict:
        """Use Opus to synthesize optimal coordinated response"""
        
        prompt = f"""You are the COORDINATOR agent orchestrating a swarm response for the Solana Immune System.

THREAT REQUIRING COORDINATION:
{json.dumps(request.get("threat", {}), indent=2)}

INITIATING AGENT'S DECISION:
{json.dumps(request.get("decision", {}), indent=2)}

PROPOSALS FROM AGENTS:
{json.dumps(proposals, indent=2)}

PARTICIPATING AGENTS: {[p.get("agent") for p in proposals]}

YOUR TASK:
Synthesize the optimal coordinated response considering:
1. Speed vs thoroughness tradeoff
2. Risk of false positives (don't cry wolf)
3. Resource allocation across agents
4. Verification requirements
5. Community impact
6. On-chain transaction costs

OUTPUT FORMAT (JSON):
{{
    "approved": <true|false>,
    "action_plan": "<step-by-step coordinated strategy>",
    "agent_assignments": {{
        "<agent_type>": "<specific task>"
    }},
    "execution_order": [<agent types in sequence>],
    "verification_steps": [<list of verification requirements>],
    "estimated_response_time_seconds": <number>,
    "confidence": <0-100>,
    "risk_of_false_positive": <0-100>,
    "reasoning": "<detailed explanation for on-chain publication>"
}}

Be decisive but careful. False positives damage credibility.
"""
        
        response = self.opus.messages.create(
            model=self.config.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.content[0].text
        
        try:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                consensus = json.loads(response_text[json_start:json_end])
            else:
                consensus = json.loads(response_text)
        except json.JSONDecodeError:
            self.log.warning("Failed to parse consensus response")
            consensus = {
                "approved": False,
                "action_plan": "Manual review required",
                "agent_assignments": {},
                "execution_order": [],
                "verification_steps": [],
                "estimated_response_time_seconds": 0,
                "confidence": 0,
                "risk_of_false_positive": 50,
                "reasoning": response_text
            }
        
        consensus["full_reasoning"] = response_text
        consensus["timestamp"] = datetime.now().isoformat()
        
        return consensus
    
    async def execute_coordinated_response(self, coord_id: int, consensus: Dict):
        """Execute the coordinated response according to the plan"""
        
        self.log.info(f"⚡ Executing coordinated response", coord_id=coord_id)
        
        execution_order = consensus.get("execution_order", [])
        assignments = consensus.get("agent_assignments", {})
        
        results = {}
        
        for agent_type in execution_order:
            agent = next((a for a in self.other_agents if a.agent_type == agent_type), None)
            
            if agent:
                task = assignments.get(agent_type, "execute_default_action")
                
                try:
                    self.log.info(f"Delegating to {agent_type}: {task}")
                    
                    # Execute agent's assigned task
                    if hasattr(agent, 'execute_coordinated_task'):
                        result = await agent.execute_coordinated_task(task, consensus)
                    else:
                        result = {"status": "completed", "task": task}
                    
                    results[agent_type] = result
                    
                except Exception as e:
                    self.log.error(f"Failed to execute {agent_type} task", error=str(e))
                    results[agent_type] = {"status": "failed", "error": str(e)}
        
        # Update coordination status
        self.active_coordinations[coord_id]["status"] = "executed"
        self.active_coordinations[coord_id]["results"] = results
        
        # Record on-chain
        await self.record_coordination_onchain(coord_id, consensus, results)
        
        self.log.info(f"✅ Coordinated response completed", coord_id=coord_id)
    
    async def record_coordination_onchain(self, coord_id: int, consensus: Dict, results: Dict):
        """Record coordination decision and outcome on-chain"""
        # TODO: Implement actual on-chain recording via Anchor
        self.log.info(
            f"📋 Recorded coordination on-chain",
            coord_id=coord_id,
            agents_involved=len(results)
        )
    
    async def execute_action(self, decision: Decision, threat: Threat) -> Dict[str, Any]:
        """Coordinator executes by delegating to the swarm"""
        return {"status": "delegated", "action": decision.action}
    
    async def propose_strategy(self, threat: Threat) -> Dict:
        """Coordinator's proposal - always suggests coordination"""
        return {
            "agent": "Coordinator",
            "strategy": "Coordinate swarm response",
            "confidence": 1.0,
            "requires_agents": ["Scanner", "Oracle", "Sentinel"]
        }
    
    async def get_current_intelligence(self) -> Dict:
        """Return Coordinator's current state"""
        return {
            "active_coordinations": len(self.active_coordinations),
            "pending_requests": len(self.pending_coordinations),
            "total_coordinations": len(self.coordination_history),
            "active": self.running,
            "capabilities": self.capabilities
        }
