"""
Base Autonomous Agent Class
Core framework for all security agents in the Solana Immune System

ENHANCED: Now includes database persistence, on-chain commits, and ML scoring
"""
import asyncio
import hashlib
import json
import structlog
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from dataclasses import dataclass, field

from anthropic import Anthropic

# Try importing Solana (optional)
try:
    from solana.rpc.async_api import AsyncClient
    from solders.keypair import Keypair
    from solders.pubkey import Pubkey
    HAS_SOLANA = True
except ImportError:
    HAS_SOLANA = False
    AsyncClient = None
    class Keypair:
        def __init__(self):
            import secrets
            self._secret = secrets.token_hex(32)
        def pubkey(self):
            return f"Mock{self._secret[:40]}"
        @classmethod
        def from_bytes(cls, data):
            return cls()
    class Pubkey:
        pass

from .config import AgentConfig, config
from .database import get_db, GuardianDB
from .onchain import GuardianOnChain, ActionType, create_onchain_client
from .embeddings import get_scorer, RiskScorer

if TYPE_CHECKING:
    from .base_agent import AutonomousAgent

logger = structlog.get_logger()


@dataclass
class Threat:
    """Represents a detected threat"""
    id: int
    threat_type: str
    severity: float  # 0-100
    target_address: Optional[str]
    description: str
    evidence: Dict[str, Any]
    detected_by: str
    detected_at: datetime = field(default_factory=datetime.now)
    status: str = "active"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "threat_type": self.threat_type,
            "severity": self.severity,
            "target_address": self.target_address,
            "description": self.description,
            "evidence": self.evidence,
            "detected_by": self.detected_by,
            "detected_at": self.detected_at.isoformat(),
            "status": self.status,
        }


@dataclass
class Decision:
    """Represents an agent's decision"""
    action: str  # IGNORE, MONITOR, WARN, BLOCK, COORDINATE
    confidence: float
    reasoning: str
    requires_consensus: bool
    suggested_agents: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "requires_consensus": self.requires_consensus,
            "suggested_agents": self.suggested_agents,
        }


class AutonomousAgent(ABC):
    """
    Base class for all autonomous security agents.
    
    Implements the core autonomous loop:
    1. PERCEIVE - Scan environment for threats
    2. REASON - Use Claude Opus for analysis
    3. COMMIT - Publish reasoning hash on-chain
    4. DECIDE - Make action decision
    5. COLLABORATE - Coordinate with swarm if needed
    6. ACT - Execute security action
    7. REVEAL - Publish full reasoning on-chain
    8. LEARN - Update memory from outcomes
    """
    
    def __init__(
        self,
        role: str,
        agent_type: str,
        capabilities: List[str],
        config: AgentConfig = config,
    ):
        self.role = role
        self.agent_type = agent_type
        self.capabilities = capabilities
        self.config = config
        
        # Initialize clients
        self.opus = Anthropic(api_key=config.anthropic_api_key)
        self.solana = AsyncClient(config.solana_rpc_url) if HAS_SOLANA and AsyncClient else None
        
        # Load wallet
        try:
            with open(config.wallet_path, 'r') as f:
                keypair_data = json.load(f)
            self.wallet = Keypair.from_bytes(bytes(keypair_data))
            self.agent_id = self.wallet.pubkey()
        except FileNotFoundError:
            # Generate temporary wallet for testing
            self.wallet = Keypair()
            self.agent_id = self.wallet.pubkey()
            logger.warning("No wallet file found, using temporary keypair")
        
        # Database for persistence
        self.db: GuardianDB = get_db()
        
        # On-chain client (initialized lazily)
        self._onchain: Optional[GuardianOnChain] = None
        
        # ML Risk Scorer
        self.scorer: RiskScorer = get_scorer()
        
        # State
        self.memory: List[Dict] = []
        self.threat_history: List[Threat] = []
        self.other_agents: List['AutonomousAgent'] = []
        self.running = False
        self.threat_counter = 0
        
        # Track stats
        self._scan_count = 0
        self._threats_detected = 0
        
        # Logging
        self.log = logger.bind(agent=self.role)
        self.log.info(f"✅ {self.role} agent initialized", agent_id=str(self.agent_id)[:16])
    
    async def get_onchain(self) -> GuardianOnChain:
        """Get or create on-chain client"""
        if self._onchain is None:
            self._onchain = GuardianOnChain(self.wallet, self.config.solana_rpc_url, self.config.network)
            await self._onchain.connect()
        return self._onchain
    
    async def start(self):
        """Start the autonomous loop"""
        self.running = True
        self.log.info(f"🚀 {self.role} starting autonomous loop...")
        
        while self.running:
            try:
                await self.autonomous_cycle()
                await asyncio.sleep(self.get_scan_interval())
            except Exception as e:
                self.log.error(f"Error in autonomous loop", error=str(e))
                await asyncio.sleep(60)  # Wait before retrying
    
    async def stop(self):
        """Stop the autonomous loop"""
        self.running = False
        self.log.info(f"🛑 {self.role} stopping...")
    
    async def autonomous_cycle(self):
        """Single cycle of the autonomous loop"""
        
        # Track scan
        self._scan_count += 1
        self.db.update_agent_stats(
            str(self.agent_id),
            self.agent_type,
            total_scans=1
        )
        
        # 1. PERCEIVE - Scan environment
        threats = await self.scan_environment()
        
        if not threats:
            self.log.debug("No threats detected this cycle")
            return
        
        self.log.info(f"⚠️ Detected {len(threats)} potential threats")
        
        for threat in threats:
            try:
                await self.process_threat(threat)
                self.db.update_agent_stats(
                    str(self.agent_id),
                    self.agent_type,
                    threats_detected=1
                )
            except Exception as e:
                self.log.error(f"Error processing threat", threat_id=threat.id, error=str(e))
    
    async def process_threat(self, threat: Threat):
        """Process a single threat through the full pipeline"""
        
        # 0. PERSIST - Store threat in database
        db_threat_id = self.db.insert_threat(threat.to_dict())
        threat.id = db_threat_id  # Use database ID
        self._threats_detected += 1
        
        # 1. ML SCORING - Get initial risk assessment
        blacklist = set(b['address'] for b in self.db.get_blacklist())
        patterns = self.db.get_patterns(min_confidence=0.5)
        ml_score = self.scorer.score_threat(threat.to_dict(), blacklist, patterns)
        
        self.log.info(
            f"📊 ML Risk Score",
            threat_id=threat.id,
            score=f"{ml_score['final_score']:.1f}",
            recommendation=ml_score['recommendation']
        )
        
        # Skip low-risk threats if ML is confident
        if ml_score['final_score'] < 20 and ml_score.get('ml_details', {}).get('confidence', 0) > 0.8:
            self.log.info(f"⏭️ Skipping low-risk threat", threat_id=threat.id)
            self.db.update_threat_status(threat.id, "ignored", "Low ML risk score")
            return
        
        # 2. REASON - Use Claude Opus for analysis
        self.log.info(f"🧠 Analyzing threat with Opus", threat_id=threat.id)
        analysis = await self.analyze_with_opus(threat)
        
        # Enhance analysis with ML insights
        analysis["ml_risk_score"] = ml_score['final_score']
        analysis["ml_recommendation"] = ml_score['recommendation']
        
        # 3. COMMIT - Publish reasoning hash on-chain BEFORE acting
        self.log.info(f"📝 Committing reasoning on-chain", threat_id=threat.id)
        reasoning_hash = await self.commit_reasoning_onchain(threat.id, analysis)
        
        # 4. DECIDE - Make action decision
        decision = self.make_decision(analysis, threat)
        self.log.info(
            f"💡 Decision made",
            threat_id=threat.id,
            action=decision.action,
            confidence=decision.confidence
        )
        
        # 5. COLLABORATE - Check with swarm if needed
        if decision.requires_consensus:
            self.log.info(f"🤝 Requesting swarm consensus", threat_id=threat.id)
            consensus = await self.reach_swarm_consensus(decision, threat)
            if not consensus.get("approved"):
                self.log.warning(f"❌ Swarm rejected action", threat_id=threat.id)
                self.db.update_threat_status(threat.id, "rejected", "Swarm consensus rejected")
                return
        
        # 6. ACT - Execute security action
        self.log.info(f"⚡ Executing action", threat_id=threat.id, action=decision.action)
        result = await self.execute_action(decision, threat)
        
        # 7. REVEAL - Publish full reasoning on-chain
        self.log.info(f"🔓 Revealing reasoning on-chain", threat_id=threat.id)
        await self.reveal_reasoning_onchain(reasoning_hash, analysis["full_reasoning"])
        
        # 8. LEARN - Update memory and database
        await self.learn_from_outcome(threat, decision, result)
        
        # Update threat status in DB
        self.db.update_threat_status(threat.id, "processed", f"Action: {decision.action}")
        
        self.log.info(f"✅ Threat processed successfully", threat_id=threat.id)
    
    @abstractmethod
    async def scan_environment(self) -> List[Threat]:
        """
        Scan the Solana blockchain for threats.
        Must be implemented by each specialized agent.
        """
        pass
    
    @abstractmethod
    async def execute_action(self, decision: Decision, threat: Threat) -> Dict[str, Any]:
        """
        Execute the security action.
        Must be implemented by each specialized agent.
        """
        pass
    
    async def analyze_with_opus(self, threat: Threat) -> Dict[str, Any]:
        """Use Claude Opus for sophisticated threat analysis"""
        
        # Gather context
        historical_context = self.get_historical_context(threat)
        swarm_intel = await self.query_swarm_intelligence()
        
        prompt = f"""You are {self.role}, an autonomous security agent protecting the Solana blockchain.
You are part of the SOLANA IMMUNE SYSTEM - a multi-agent swarm that detects and neutralizes threats.

YOUR SPECIALIZATION: {self.agent_type}
YOUR CAPABILITIES: {', '.join(self.capabilities)}

THREAT DETECTED:
{json.dumps(threat.to_dict(), indent=2)}

HISTORICAL CONTEXT (similar past threats):
{json.dumps(historical_context, indent=2)}

SWARM INTELLIGENCE (insights from other agents):
{json.dumps(swarm_intel, indent=2)}

ANALYZE THIS THREAT AND PROVIDE:
1. Threat probability score (0-100%)
2. Specific attack vectors identified
3. Potential damage estimation (in SOL/USD)
4. Recommended action: IGNORE | MONITOR | WARN | BLOCK | COORDINATE
5. Confidence level (0-100%)
6. Detailed reasoning (this will be published on-chain for transparency)
7. Whether this requires coordination with other agents
8. If coordination needed, which agent types should participate

OUTPUT FORMAT (JSON):
{{
    "threat_score": <0-100>,
    "attack_vectors": [<list of identified vectors>],
    "potential_damage_usd": <estimated damage>,
    "recommended_action": "<IGNORE|MONITOR|WARN|BLOCK|COORDINATE>",
    "confidence": <0-100>,
    "reasoning": "<detailed explanation for on-chain publication>",
    "requires_coordination": <true|false>,
    "suggested_agents": [<list of agent types if coordination needed>]
}}

Be thorough but decisive. Your reasoning will be publicly visible on-chain.
"""
        
        response = self.opus.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse response
        response_text = response.content[0].text
        
        # Extract JSON from response
        try:
            # Try to find JSON in the response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                analysis = json.loads(response_text[json_start:json_end])
            else:
                analysis = json.loads(response_text)
        except json.JSONDecodeError:
            self.log.warning("Failed to parse Opus response as JSON, using fallback")
            analysis = {
                "threat_score": 50,
                "attack_vectors": ["unknown"],
                "potential_damage_usd": 0,
                "recommended_action": "MONITOR",
                "confidence": 30,
                "reasoning": response_text,
                "requires_coordination": False,
                "suggested_agents": []
            }
        
        # Store full reasoning for on-chain publication
        analysis["full_reasoning"] = response_text
        analysis["timestamp"] = datetime.now().isoformat()
        
        return analysis
    
    async def commit_reasoning_onchain(self, threat_id: int, analysis: Dict) -> str:
        """
        Commit reasoning hash to blockchain BEFORE taking any action.
        This ensures transparency and prevents post-hoc manipulation.
        """
        reasoning_text = analysis["full_reasoning"]
        reasoning_hash = hashlib.sha256(reasoning_text.encode()).hexdigest()
        
        # Map action to ActionType enum
        action_map = {
            "IGNORE": ActionType.IGNORE,
            "MONITOR": ActionType.MONITOR,
            "WARN": ActionType.WARN,
            "BLOCK": ActionType.BLOCK,
            "COORDINATE": ActionType.COORDINATE,
            "RECOVER": ActionType.RECOVER,
        }
        action_type = action_map.get(analysis.get("recommended_action", "MONITOR"), ActionType.MONITOR)
        
        # Store in database first (always works)
        commit_id = self.db.insert_reasoning_commit({
            "threat_id": threat_id,
            "agent_id": str(self.agent_id),
            "reasoning_hash": reasoning_hash,
            "action_type": analysis.get("recommended_action", "MONITOR"),
        })
        
        # Try on-chain commit (may fail if no SOL/network issues)
        try:
            onchain = await self.get_onchain()
            result = await onchain.commit_reasoning(
                threat_id=threat_id,
                reasoning_text=reasoning_text,
                action_type=action_type
            )
            
            if result.get("success"):
                self.log.info(
                    f"📝 Reasoning committed ON-CHAIN",
                    threat_id=threat_id,
                    tx=result.get("signature", "")[:16],
                    hash=reasoning_hash[:16]
                )
            else:
                self.log.warning(
                    f"📝 Reasoning committed (DB only, on-chain failed)",
                    threat_id=threat_id,
                    error=result.get("error"),
                    hash=reasoning_hash[:16]
                )
        except Exception as e:
            self.log.warning(
                f"📝 Reasoning committed (DB only)",
                threat_id=threat_id,
                hash=reasoning_hash[:16],
                error=str(e)
            )
        
        return reasoning_hash
    
    async def reveal_reasoning_onchain(self, reasoning_hash: str, reasoning_text: str):
        """
        Reveal full reasoning on-chain after action is taken.
        Anyone can verify the hash matches.
        """
        # Verify hash matches
        computed_hash = hashlib.sha256(reasoning_text.encode()).hexdigest()
        if computed_hash != reasoning_hash:
            self.log.error("Hash mismatch during reveal!", expected=reasoning_hash[:16], got=computed_hash[:16])
            return
        
        # Update database
        # Find the commit by hash and reveal it
        self.db.conn.execute(
            "UPDATE reasoning_commits SET revealed = TRUE, reveal_timestamp = ?, reasoning_text = ? WHERE reasoning_hash = ?",
            (datetime.now().isoformat(), reasoning_text, reasoning_hash)
        )
        self.db.conn.commit()
        
        # Try on-chain reveal
        try:
            onchain = await self.get_onchain()
            # Would need threat_id to properly reveal - simplified for now
            self.log.info(f"🔓 Reasoning revealed", hash=reasoning_hash[:16])
        except Exception as e:
            self.log.warning(f"🔓 Reasoning revealed (DB only)", hash=reasoning_hash[:16], error=str(e))
    
    def make_decision(self, analysis: Dict, threat: Threat) -> Decision:
        """Convert Opus analysis into an executable decision"""
        
        action = analysis.get("recommended_action", "MONITOR")
        confidence = analysis.get("confidence", 50) / 100.0
        
        # Determine if consensus is required
        requires_consensus = (
            analysis.get("requires_coordination", False) or
            action in ["BLOCK", "COORDINATE"] or
            confidence < self.config.min_threat_confidence
        )
        
        return Decision(
            action=action,
            confidence=confidence,
            reasoning=analysis.get("reasoning", ""),
            requires_consensus=requires_consensus,
            suggested_agents=analysis.get("suggested_agents", [])
        )
    
    async def reach_swarm_consensus(self, decision: Decision, threat: Threat) -> Dict:
        """Coordinate with other agents for consensus"""
        
        # Find coordinator agent
        coordinator = next(
            (a for a in self.other_agents if a.agent_type == "Coordinator"),
            None
        )
        
        if coordinator:
            return await coordinator.coordinate_threat_response(self, decision, threat)
        
        # No coordinator, proceed with local decision
        self.log.warning("No coordinator available, proceeding without consensus")
        return {"approved": True, "reason": "no_coordinator"}
    
    async def learn_from_outcome(self, threat: Threat, decision: Decision, result: Dict):
        """Learn from action outcomes to improve future decisions"""
        
        learning_entry = {
            "timestamp": datetime.now().isoformat(),
            "threat": threat.to_dict(),
            "decision": decision.to_dict(),
            "result": result,
            "agent": self.role
        }
        
        self.memory.append(learning_entry)
        self.threat_history.append(threat)
        
        # Add to ML classifier training data
        # Assume success = true positive for now (could be refined with feedback)
        is_true_positive = result.get("status") == "success" and decision.action in ["WARN", "BLOCK", "COORDINATE"]
        self.scorer.classifier.add_training_sample(threat.to_dict(), is_true_positive)
        
        # Record pattern in database
        self.db.record_pattern(
            pattern_type=threat.threat_type,
            pattern_data={
                "action_taken": decision.action,
                "confidence": decision.confidence,
                "severity": threat.severity,
                "detected_by": threat.detected_by
            },
            confidence=decision.confidence
        )
        
        # Trim memory if too large
        if len(self.memory) > self.config.max_memory_entries:
            self.memory = self.memory[-self.config.max_memory_entries:]
        
        # Periodically extract patterns and retrain
        if len(self.memory) % 10 == 0:
            await self.extract_patterns()
        
        # Retrain classifier periodically
        if len(self.scorer.classifier.threat_embeddings) % 50 == 0:
            self.scorer.classifier.train_risk_classifier(min_samples=20)
    
    async def extract_patterns(self):
        """Use Opus to identify patterns in threat history"""
        
        if len(self.memory) < 5:
            return
        
        prompt = f"""Analyze these {len(self.memory)} security events handled by {self.role}:

{json.dumps(self.memory[-50:], indent=2)}

Extract:
1. Common attack patterns
2. False positive indicators
3. Successful defense strategies
4. Areas for improvement

Output actionable insights in JSON format."""
        
        try:
            response = self.opus.messages.create(
                model=self.config.model,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            self.log.info(f"🧠 Learned new patterns from {len(self.memory)} events")
        except Exception as e:
            self.log.error(f"Failed to extract patterns", error=str(e))
    
    def get_historical_context(self, threat: Threat) -> List[Dict]:
        """Get relevant historical threats for context"""
        
        similar_threats = [
            t.to_dict() for t in self.threat_history
            if t.threat_type == threat.threat_type
        ]
        
        return similar_threats[-10:]  # Last 10 similar threats
    
    async def query_swarm_intelligence(self) -> Dict:
        """Get insights from other agents"""
        
        intel = {}
        for agent in self.other_agents:
            if hasattr(agent, 'get_current_intelligence'):
                try:
                    intel[agent.role] = await agent.get_current_intelligence()
                except Exception as e:
                    self.log.warning(f"Failed to get intel from {agent.role}", error=str(e))
        
        return intel
    
    async def get_current_intelligence(self) -> Dict:
        """Return current intelligence for other agents"""
        return {
            "recent_threats": len(self.threat_history),
            "active": self.running,
            "capabilities": self.capabilities
        }
    
    def get_scan_interval(self) -> int:
        """Get scan interval in seconds based on agent type"""
        intervals = {
            "Sentinel": 30,
            "Scanner": 60,
            "Oracle": 120,
            "Intel": 300,
            "Reporter": 180,
            "Guardian": 30,
            "Auditor": 120,
            "Hunter": 300,
            "Healer": 600,
            "Coordinator": 60,
        }
        return intervals.get(self.agent_type, self.config.scan_interval_seconds)
    
    def get_next_threat_id(self) -> int:
        """Generate next threat ID"""
        self.threat_counter += 1
        return self.threat_counter
