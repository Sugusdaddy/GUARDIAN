"""
ORACLE Agent - ML-Based Risk Prediction
ENHANCED: Real ML integration with embeddings, clustering, and prediction models
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import hashlib

from ..core.base_agent import AutonomousAgent, Threat, Decision
from ..core.config import AgentConfig, config
from ..core.database import get_db
from ..core.embeddings import get_embedder, get_classifier, get_scorer, ThreatClassifier


class OracleAgent(AutonomousAgent):
    """
    ORACLE - The Predictor
    
    ENHANCED ML-powered threat prediction:
    - Real embeddings for threat similarity
    - Clustering to detect attack campaigns
    - Risk scoring with multiple signals
    - Pattern learning from historical data
    - Behavioral anomaly detection
    """
    
    def __init__(self, config: AgentConfig = config):
        super().__init__(
            role="ORACLE",
            agent_type="Oracle",
            capabilities=[
                "risk_prediction",
                "pattern_analysis",
                "threat_scoring",
                "behavioral_modeling",
                "anomaly_detection",
                "campaign_detection"
            ],
            config=config
        )
        
        # ML components
        self.embedder = get_embedder()
        self.classifier = get_classifier()
        
        # Prediction cache (address -> prediction)
        self.prediction_cache: Dict[str, Dict] = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Clustering for campaign detection
        self.recent_threats: List[Dict] = []
        self.detected_campaigns: List[Dict] = []
        
        # Calibration tracking
        self.predictions_made = 0
        self.predictions_correct = 0
        
        self.log.info("🔮 Oracle ready with ML predictions...")
    
    async def scan_environment(self) -> List[Threat]:
        """
        Oracle analyzes existing threats and generates meta-insights.
        Also monitors for patterns that other agents might miss.
        """
        threats = []
        
        try:
            # 1. Analyze recent threats for campaigns
            campaign_threats = await self._detect_campaigns()
            threats.extend(campaign_threats)
            
            # 2. Re-score existing active threats with updated intelligence
            rescore_threats = await self._rescore_active_threats()
            threats.extend(rescore_threats)
            
            # 3. Check for anomalies in transaction patterns
            anomaly_threats = await self._detect_anomalies()
            threats.extend(anomaly_threats)
            
            # 4. Predict emerging threats from patterns
            predicted_threats = await self._predict_emerging_threats()
            threats.extend(predicted_threats)
            
        except Exception as e:
            self.log.error("Oracle scan error", error=str(e))
        
        return threats
    
    async def _detect_campaigns(self) -> List[Threat]:
        """
        Use clustering to detect coordinated attack campaigns.
        Multiple related threats = organized campaign.
        """
        threats = []
        
        # Get recent threats from database
        recent = self.db.get_active_threats(limit=100)
        
        if len(recent) < 5:
            return threats
        
        # Cluster threats
        cluster_result = self.classifier.cluster_threats(recent, eps=0.4, min_samples=3)
        
        # Each cluster with 3+ members could be a campaign
        for cluster in cluster_result.get("clusters", []):
            if len(cluster["members"]) >= 3:
                # Check if we've already detected this campaign
                campaign_hash = hashlib.md5(
                    json.dumps(sorted(cluster["members"])).encode()
                ).hexdigest()[:16]
                
                if any(c.get("hash") == campaign_hash for c in self.detected_campaigns):
                    continue
                
                # Get the threats in this cluster
                cluster_threats = [recent[i] for i in cluster["members"] if i < len(recent)]
                
                # Analyze campaign characteristics
                threat_types = [t.get("threat_type") for t in cluster_threats]
                most_common_type = max(set(threat_types), key=threat_types.count)
                avg_severity = sum(t.get("severity", 0) for t in cluster_threats) / len(cluster_threats)
                
                # Create campaign threat
                campaign_threat = Threat(
                    id=self.get_next_threat_id(),
                    threat_type="CoordinatedCampaign",
                    severity=min(95, avg_severity + 20),  # Campaigns are more serious
                    target_address=None,
                    description=f"Coordinated attack campaign detected: {len(cluster_threats)} related {most_common_type} threats",
                    evidence={
                        "campaign_hash": campaign_hash,
                        "threat_count": len(cluster_threats),
                        "primary_type": most_common_type,
                        "member_ids": [t.get("id") for t in cluster_threats],
                        "addresses": [t.get("target_address") for t in cluster_threats if t.get("target_address")]
                    },
                    detected_by="Oracle"
                )
                
                threats.append(campaign_threat)
                self.detected_campaigns.append({"hash": campaign_hash, "detected_at": datetime.now()})
                
                self.log.info(
                    "🎯 Campaign detected",
                    type=most_common_type,
                    count=len(cluster_threats),
                    severity=campaign_threat.severity
                )
        
        return threats
    
    async def _rescore_active_threats(self) -> List[Threat]:
        """
        Re-evaluate active threats with updated intelligence.
        May upgrade severity if new evidence emerges.
        """
        threats = []
        
        active = self.db.get_active_threats(limit=50)
        blacklist = set(b["address"] for b in self.db.get_blacklist())
        patterns = self.db.get_patterns(min_confidence=0.6)
        
        for threat_data in active:
            # Skip if recently scored
            cache_key = f"rescore_{threat_data['id']}"
            if cache_key in self.prediction_cache:
                cached = self.prediction_cache[cache_key]
                if (datetime.now() - cached["time"]).seconds < self.cache_ttl:
                    continue
            
            # Re-score
            score_result = self.scorer.score_threat(threat_data, blacklist, patterns)
            new_score = score_result["final_score"]
            old_score = threat_data.get("severity", 50)
            
            # Cache result
            self.prediction_cache[cache_key] = {
                "score": new_score,
                "time": datetime.now()
            }
            
            # If score increased significantly, create upgrade alert
            if new_score > old_score + 15:
                upgrade_threat = Threat(
                    id=self.get_next_threat_id(),
                    threat_type="ThreatUpgrade",
                    severity=new_score,
                    target_address=threat_data.get("target_address"),
                    description=f"Threat severity upgraded: {old_score:.0f} → {new_score:.0f}",
                    evidence={
                        "original_threat_id": threat_data["id"],
                        "old_severity": old_score,
                        "new_severity": new_score,
                        "reason": score_result.get("recommendation"),
                        "ml_details": score_result.get("ml_details", {})
                    },
                    detected_by="Oracle"
                )
                threats.append(upgrade_threat)
                
                self.log.info(
                    "⬆️ Threat upgraded",
                    threat_id=threat_data["id"],
                    old=old_score,
                    new=new_score
                )
        
        return threats
    
    async def _detect_anomalies(self) -> List[Threat]:
        """
        Use anomaly detection to find unusual patterns.
        """
        threats = []
        
        # Get recent transaction patterns from cache
        high_risk_txs = self.db.get_high_risk_txs(min_risk=30, limit=50)
        
        if len(high_risk_txs) < 10:
            return threats
        
        # Check each for anomaly
        for tx in high_risk_txs:
            tx_dict = dict(tx) if hasattr(tx, "keys") else tx
            
            # Create threat-like object for embedding
            threat_like = {
                "threat_type": "Transaction",
                "severity": tx_dict.get("risk_score", 50),
                "target_address": tx_dict.get("to_address"),
                "description": f"Transaction {tx_dict.get('signature', '')[:16]}",
                "evidence": tx_dict
            }
            
            # Check if anomalous
            ml_result = self.classifier.predict_risk(threat_like)
            
            if ml_result.get("is_anomaly") and ml_result.get("risk_score", 0) > 60:
                anomaly_threat = Threat(
                    id=self.get_next_threat_id(),
                    threat_type="AnomalousTransaction",
                    severity=ml_result["risk_score"],
                    target_address=tx_dict.get("to_address"),
                    description=f"Anomalous transaction pattern detected",
                    evidence={
                        "signature": tx_dict.get("signature"),
                        "anomaly_score": ml_result.get("anomaly_score"),
                        "risk_score": ml_result["risk_score"],
                        "similar_threats": ml_result.get("similar_threats", [])
                    },
                    detected_by="Oracle"
                )
                threats.append(anomaly_threat)
        
        return threats
    
    async def _predict_emerging_threats(self) -> List[Threat]:
        """
        Analyze patterns to predict threats before they fully materialize.
        """
        threats = []
        
        # Get learned patterns
        patterns = self.db.get_patterns(min_confidence=0.7)
        
        # Look for patterns with increasing occurrence
        for pattern in patterns:
            if pattern.get("occurrences", 0) < 5:
                continue
            
            pattern_data = pattern.get("pattern_data", {})
            if isinstance(pattern_data, str):
                try:
                    pattern_data = json.loads(pattern_data)
                except:
                    continue
            
            # Check if this pattern typically escalates
            avg_severity = pattern_data.get("severity", 50)
            if avg_severity > 60 and pattern.get("confidence", 0) > 0.75:
                # This is a high-confidence severe pattern
                prediction_threat = Threat(
                    id=self.get_next_threat_id(),
                    threat_type="PredictedThreat",
                    severity=min(80, avg_severity),
                    target_address=None,
                    description=f"High probability of {pattern['pattern_type']} attack based on pattern analysis",
                    evidence={
                        "pattern_type": pattern["pattern_type"],
                        "confidence": pattern["confidence"],
                        "occurrences": pattern["occurrences"],
                        "historical_severity": avg_severity
                    },
                    detected_by="Oracle"
                )
                # Only add if not recently predicted
                cache_key = f"predict_{pattern['pattern_type']}"
                if cache_key not in self.prediction_cache:
                    threats.append(prediction_threat)
                    self.prediction_cache[cache_key] = {"time": datetime.now()}
        
        return threats
    
    async def execute_action(self, decision: Decision, threat: Threat) -> Dict[str, Any]:
        """Execute Oracle-specific actions"""
        result = {"status": "success", "action": decision.action}
        
        if decision.action in ["WARN", "COORDINATE"]:
            # Share intelligence with other agents
            for agent in self.other_agents:
                if hasattr(agent, "receive_intelligence"):
                    await agent.receive_intelligence({
                        "from": "Oracle",
                        "threat_id": threat.id,
                        "prediction": {
                            "severity": threat.severity,
                            "confidence": decision.confidence,
                            "recommendation": decision.action
                        }
                    })
            result["intelligence_shared"] = True
        
        if decision.action == "BLOCK" and threat.threat_type == "CoordinatedCampaign":
            # Add all campaign addresses to watchlist
            evidence = threat.evidence if isinstance(threat.evidence, dict) else {}
            addresses = evidence.get("addresses", [])
            
            for addr in addresses:
                if addr:
                    self.db.add_to_watchlist(
                        addr,
                        f"Campaign_{evidence.get('campaign_hash', 'unknown')[:8]}",
                        "Oracle",
                        f"Part of coordinated campaign"
                    )
            
            result["addresses_watched"] = len(addresses)
        
        # Track prediction for calibration
        self.predictions_made += 1
        
        return result
    
    async def receive_intelligence(self, intel: Dict):
        """Receive intelligence from other agents"""
        self.log.debug("Received intelligence", from_agent=intel.get("from"))
        # Store for analysis
        self.recent_threats.append({
            **intel,
            "received_at": datetime.now()
        })
        
        # Trim old data
        cutoff = datetime.now() - timedelta(hours=1)
        self.recent_threats = [
            t for t in self.recent_threats 
            if t.get("received_at", datetime.now()) > cutoff
        ]
    
    async def get_risk_prediction(self, address: str) -> Dict[str, Any]:
        """
        Get ML risk prediction for an address.
        Called by other agents for consultation.
        """
        # Check cache
        cache_key = f"addr_{address}"
        if cache_key in self.prediction_cache:
            cached = self.prediction_cache[cache_key]
            if (datetime.now() - cached["time"]).seconds < self.cache_ttl:
                return cached["result"]
        
        # Build threat-like object
        threat = {
            "threat_type": "Unknown",
            "severity": 50,
            "target_address": address,
            "description": f"Risk assessment for {address}",
            "evidence": {}
        }
        
        # Get scoring inputs
        blacklist = set(b["address"] for b in self.db.get_blacklist())
        patterns = self.db.get_patterns(min_confidence=0.5)
        
        # Score
        result = self.scorer.score_threat(threat, blacklist, patterns)
        
        # Cache
        self.prediction_cache[cache_key] = {
            "result": result,
            "time": datetime.now()
        }
        
        return result
    
    async def get_current_intelligence(self) -> Dict:
        """Return current intelligence for other agents"""
        return {
            "recent_threats": len(self.recent_threats),
            "campaigns_detected": len(self.detected_campaigns),
            "predictions_made": self.predictions_made,
            "cache_size": len(self.prediction_cache),
            "active": self.running,
            "capabilities": self.capabilities
        }
    
    def get_scan_interval(self) -> int:
        """Oracle scans less frequently but does deeper analysis"""
        return 120  # Every 2 minutes
