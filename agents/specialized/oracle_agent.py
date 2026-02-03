"""
ORACLE Agent - ML-Based Risk Prediction
Uses Claude Opus for sophisticated risk prediction and pattern analysis
"""
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from ..core.base_agent import AutonomousAgent, Threat, Decision
from ..core.config import AgentConfig, config


class OracleAgent(AutonomousAgent):
    """
    ORACLE - The Predictor
    
    ML-powered threat prediction and risk scoring:
    - Calculates threat probability scores
    - Predicts rug pull likelihood
    - Identifies emerging attack patterns
    - Provides risk assessments for the swarm
    """
    
    def __init__(self, config: AgentConfig = config):
        super().__init__(
            role="ORACLE",
            agent_type="Oracle",
            capabilities=[
                "risk_prediction",
                "pattern_analysis",
                "threat_scoring",
                "behavioral_modeling"
            ],
            config=config
        )
        
        # Prediction cache
        self.prediction_cache: Dict[str, Dict] = {}
        
        # Historical patterns learned
        self.learned_patterns: List[Dict] = []
        
        # Risk score history for calibration
        self.score_history: List[Dict] = []
        
        self.log.info("🔮 Oracle ready for predictions...")
    
    async def scan_environment(self) -> List[Threat]:
        """Oracle analyzes existing threats from other agents"""
        threats = []
        
        try:
            # Get unscored threats from other agents
            unscored_threats = await self.get_unscored_threats()
            
            for threat in unscored_threats:
                # Generate sophisticated risk prediction
                prediction = await self.predict_risk(threat)
                
                # If high risk, escalate as a new threat
                if prediction["threat_probability"] > 70:
                    threats.append(Threat(
                        id=self.get_next_threat_id(),
                        threat_type="HighRiskPrediction",
                        severity=prediction["threat_probability"],
                        target_address=threat.target_address,
                        description=f"Oracle prediction: {prediction['threat_probability']}% threat probability",
                        evidence={
                            "original_threat": threat.to_dict(),
                            "prediction": prediction
                        },
                        detected_by="Oracle"
                    ))
                
                # Cache the prediction
                if threat.target_address:
                    self.prediction_cache[threat.target_address] = prediction
            
            # Also identify emerging patterns
            pattern_threats = await self.identify_emerging_patterns()
            threats.extend(pattern_threats)
            
        except Exception as e:
            self.log.error(f"Error in Oracle scan", error=str(e))
        
        return threats
    
    async def get_unscored_threats(self) -> List[Threat]:
        """Get threats from other agents that haven't been scored"""
        unscored = []
        
        for agent in self.other_agents:
            if hasattr(agent, 'threat_history'):
                for threat in agent.threat_history[-20:]:  # Last 20 threats
                    if threat.target_address and threat.target_address not in self.prediction_cache:
                        unscored.append(threat)
        
        return unscored[:10]  # Limit to 10 per cycle
    
    async def predict_risk(self, threat: Threat) -> Dict[str, Any]:
        """Use Opus for sophisticated risk prediction"""
        
        # Gather context
        similar_historical = self.get_similar_historical_threats(threat)
        learned_context = self.get_relevant_patterns(threat)
        
        prompt = f"""You are the ORACLE, an ML-powered prediction agent for the Solana Immune System.

CURRENT THREAT TO ANALYZE:
{json.dumps(threat.to_dict(), indent=2)}

SIMILAR HISTORICAL THREATS AND OUTCOMES:
{json.dumps(similar_historical, indent=2)}

LEARNED PATTERNS:
{json.dumps(learned_context, indent=2)}

PREDICT THE FOLLOWING:
1. Probability this is a genuine threat (0-100%)
2. If it's a rug pull, likelihood of execution in next 24h (0-100%)
3. Estimated financial damage if not stopped (in USD)
4. Time sensitivity: IMMEDIATE | HOURS | DAYS | WEEKS
5. Attack sophistication level: BASIC | MODERATE | ADVANCED | EXPERT
6. Likelihood of false positive (0-100%)

Consider these factors:
- Token/contract characteristics
- Historical patterns of similar threats
- Current market conditions
- Behavioral indicators
- Technical indicators

OUTPUT FORMAT (JSON):
{{
    "threat_probability": <0-100>,
    "rug_pull_likelihood_24h": <0-100>,
    "estimated_damage_usd": <number>,
    "time_sensitivity": "<IMMEDIATE|HOURS|DAYS|WEEKS>",
    "sophistication": "<BASIC|MODERATE|ADVANCED|EXPERT>",
    "false_positive_likelihood": <0-100>,
    "confidence": <0-100>,
    "key_indicators": [<list of factors that led to this prediction>],
    "recommended_priority": "<CRITICAL|HIGH|MEDIUM|LOW>",
    "reasoning": "<detailed explanation>"
}}

Be calibrated - avoid both over-alerting and under-alerting.
"""
        
        response = self.opus.messages.create(
            model=self.config.model,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.content[0].text
        
        try:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                prediction = json.loads(response_text[json_start:json_end])
            else:
                prediction = json.loads(response_text)
        except json.JSONDecodeError:
            self.log.warning("Failed to parse Oracle prediction")
            prediction = {
                "threat_probability": 50,
                "rug_pull_likelihood_24h": 50,
                "estimated_damage_usd": 0,
                "time_sensitivity": "HOURS",
                "sophistication": "MODERATE",
                "false_positive_likelihood": 50,
                "confidence": 30,
                "key_indicators": ["analysis_incomplete"],
                "recommended_priority": "MEDIUM",
                "reasoning": response_text
            }
        
        # Store for calibration
        self.score_history.append({
            "threat_id": threat.id,
            "prediction": prediction,
            "timestamp": datetime.now().isoformat()
        })
        
        return prediction
    
    def get_similar_historical_threats(self, threat: Threat) -> List[Dict]:
        """Find similar threats from history"""
        
        similar = []
        for hist_threat in self.threat_history:
            if hist_threat.threat_type == threat.threat_type:
                similar.append({
                    "threat": hist_threat.to_dict(),
                    "outcome": "TODO"  # Would track actual outcomes
                })
        
        return similar[-5:]  # Last 5 similar
    
    def get_relevant_patterns(self, threat: Threat) -> List[Dict]:
        """Get learned patterns relevant to this threat"""
        
        relevant = []
        for pattern in self.learned_patterns:
            if pattern.get("threat_types") and threat.threat_type in pattern["threat_types"]:
                relevant.append(pattern)
        
        return relevant[-3:]  # Last 3 relevant patterns
    
    async def identify_emerging_patterns(self) -> List[Threat]:
        """Identify new attack patterns emerging across threats"""
        threats = []
        
        if len(self.threat_history) < 10:
            return threats  # Need enough data
        
        # Use Opus to identify patterns
        recent_threats = [t.to_dict() for t in self.threat_history[-50:]]
        
        prompt = f"""Analyze these recent threats for emerging patterns:

{json.dumps(recent_threats, indent=2)}

Identify:
1. New attack vectors not seen before
2. Coordinated attacks (multiple related threats)
3. Evolution of existing attack types
4. Geographic or temporal clustering

OUTPUT JSON:
{{
    "emerging_patterns": [
        {{
            "pattern_name": "<name>",
            "description": "<description>",
            "threat_count": <number>,
            "severity": <0-100>,
            "recommendation": "<action>"
        }}
    ],
    "coordinated_attacks_detected": <true|false>,
    "new_attack_vectors": [<list>]
}}
"""
        
        try:
            response = self.opus.messages.create(
                model=self.config.model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1:
                analysis = json.loads(response_text[json_start:json_end])
                
                # Store learned patterns
                for pattern in analysis.get("emerging_patterns", []):
                    self.learned_patterns.append(pattern)
                
                # Create threats for high-severity emerging patterns
                for pattern in analysis.get("emerging_patterns", []):
                    if pattern.get("severity", 0) > 70:
                        threats.append(Threat(
                            id=self.get_next_threat_id(),
                            threat_type="EmergingPattern",
                            severity=pattern["severity"],
                            target_address=None,
                            description=f"Emerging pattern detected: {pattern['pattern_name']}",
                            evidence=pattern,
                            detected_by="Oracle"
                        ))
                        
        except Exception as e:
            self.log.warning(f"Pattern analysis failed", error=str(e))
        
        return threats
    
    async def execute_action(self, decision: Decision, threat: Threat) -> Dict[str, Any]:
        """Oracle shares predictions with the swarm"""
        
        result = {"status": "success", "action": decision.action}
        
        # Oracle primarily shares intelligence rather than taking direct action
        if decision.action in ["WARN", "BLOCK", "COORDINATE"]:
            # Share prediction with all agents
            for agent in self.other_agents:
                if hasattr(agent, 'receive_oracle_prediction'):
                    await agent.receive_oracle_prediction(threat, self.prediction_cache.get(threat.target_address, {}))
            
            result["predictions_shared"] = True
        
        return result
    
    async def get_current_intelligence(self) -> Dict:
        """Return Oracle's current intelligence for other agents"""
        return {
            "recent_predictions": len(self.score_history),
            "learned_patterns": len(self.learned_patterns),
            "active": self.running,
            "capabilities": self.capabilities,
            "high_risk_count": sum(1 for s in self.score_history[-100:] 
                                   if s["prediction"].get("threat_probability", 0) > 70)
        }
    
    async def propose_strategy(self, threat: Threat) -> Dict:
        """Oracle's data-driven proposal for threat handling"""
        
        prediction = await self.predict_risk(threat)
        
        action = "BLOCK" if prediction["threat_probability"] > 80 else \
                 "WARN" if prediction["threat_probability"] > 60 else \
                 "MONITOR" if prediction["threat_probability"] > 40 else "IGNORE"
        
        return {
            "agent": "Oracle",
            "strategy": f"Risk {prediction['threat_probability']}% - {action}",
            "confidence": prediction["confidence"] / 100,
            "risk_score": prediction["threat_probability"],
            "time_sensitivity": prediction["time_sensitivity"]
        }
