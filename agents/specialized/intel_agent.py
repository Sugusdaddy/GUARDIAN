"""
INTEL Agent - Threat Intelligence & Knowledge Base
Maintains database of known threats, scam patterns, and malicious actors
"""
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Set

from ..core.base_agent import AutonomousAgent, Threat, Decision
from ..core.config import AgentConfig, config


class IntelAgent(AutonomousAgent):
    """
    INTEL - The Archivist
    
    Maintains the threat intelligence knowledge base:
    - Known scam addresses and patterns
    - Attack signatures and indicators
    - Historical threat data
    - Cross-references and connections
    """
    
    def __init__(self, config: AgentConfig = config):
        super().__init__(
            role="INTEL",
            agent_type="Intel",
            capabilities=[
                "knowledge_management",
                "pattern_storage",
                "threat_correlation",
                "historical_analysis"
            ],
            config=config
        )
        
        # Knowledge base
        self.known_scams: Dict[str, Dict] = {}  # address -> scam info
        self.attack_signatures: List[Dict] = []
        self.malicious_actors: Dict[str, Dict] = {}  # actor_id -> info
        self.threat_patterns: List[Dict] = []
        
        # Watchlists
        self.address_watchlist: Set[str] = set()
        self.token_watchlist: Set[str] = set()
        
        # Statistics
        self.total_threats_recorded = 0
        self.queries_served = 0
        
        self.log.info("📚 Intel agent ready - knowledge base initialized")
    
    async def scan_environment(self) -> List[Threat]:
        """Intel doesn't scan - it maintains knowledge and responds to queries"""
        
        # Periodically analyze patterns in the knowledge base
        if len(self.known_scams) > 10 and self.total_threats_recorded % 10 == 0:
            await self.analyze_patterns()
        
        return []
    
    async def execute_action(self, decision: Decision, threat: Threat) -> Dict[str, Any]:
        """Intel stores and correlates threat data"""
        
        result = {"status": "success", "action": "stored"}
        
        # Store threat in knowledge base
        await self.add_threat_to_database(threat)
        
        # Check for correlations
        correlations = await self.find_correlations(threat)
        if correlations:
            result["correlations"] = correlations
        
        return result
    
    async def add_threat_to_database(self, threat: Threat):
        """Add a threat to the knowledge base"""
        
        if threat.target_address:
            self.known_scams[threat.target_address] = {
                "threat_id": threat.id,
                "type": threat.threat_type,
                "severity": threat.severity,
                "description": threat.description,
                "evidence": threat.evidence,
                "detected_at": threat.detected_at.isoformat(),
                "detected_by": threat.detected_by,
                "status": threat.status
            }
            
            # Add to watchlist
            self.address_watchlist.add(threat.target_address)
        
        self.total_threats_recorded += 1
        self.log.info(f"📝 Recorded threat #{threat.id} in knowledge base")
    
    async def add_to_watchlist(self, address: str, reason: str):
        """Add an address to the watchlist"""
        self.address_watchlist.add(address)
        self.known_scams[address] = self.known_scams.get(address, {})
        self.known_scams[address]["watchlist_reason"] = reason
        self.known_scams[address]["added_to_watchlist"] = datetime.now().isoformat()
        
        self.log.info(f"👁️ Added {address[:16]}... to watchlist")
    
    async def check_address(self, address: str) -> Optional[Dict]:
        """Check if an address is in the knowledge base"""
        self.queries_served += 1
        return self.known_scams.get(address)
    
    async def is_watchlisted(self, address: str) -> bool:
        """Check if an address is on the watchlist"""
        self.queries_served += 1
        return address in self.address_watchlist
    
    async def find_correlations(self, threat: Threat) -> List[Dict]:
        """Find correlations with existing threats"""
        
        correlations = []
        
        # Check if threat address has connections to known scams
        if threat.target_address:
            for known_addr, info in self.known_scams.items():
                if known_addr == threat.target_address:
                    continue
                
                # Check for similar patterns
                if info.get("type") == threat.threat_type:
                    correlations.append({
                        "type": "same_attack_type",
                        "related_address": known_addr,
                        "threat_type": threat.threat_type
                    })
        
        # Check evidence for known signatures
        for signature in self.attack_signatures:
            if self._matches_signature(threat, signature):
                correlations.append({
                    "type": "signature_match",
                    "signature_name": signature.get("name"),
                    "confidence": signature.get("confidence", 0.8)
                })
        
        if correlations:
            self.log.info(f"🔗 Found {len(correlations)} correlations for threat #{threat.id}")
        
        return correlations
    
    def _matches_signature(self, threat: Threat, signature: Dict) -> bool:
        """Check if a threat matches a known attack signature"""
        
        required_indicators = signature.get("indicators", [])
        evidence = threat.evidence or {}
        
        matches = 0
        for indicator in required_indicators:
            if indicator in evidence:
                matches += 1
        
        # Match if 70%+ of indicators present
        return matches >= len(required_indicators) * 0.7 if required_indicators else False
    
    async def analyze_patterns(self):
        """Analyze patterns in the knowledge base"""
        
        if len(self.known_scams) < 5:
            return
        
        # Group by threat type
        type_counts = {}
        for info in self.known_scams.values():
            t_type = info.get("type", "Unknown")
            type_counts[t_type] = type_counts.get(t_type, 0) + 1
        
        # Find most common attack types
        sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
        
        self.log.info(f"📊 Pattern analysis: {sorted_types[:3]}")
        
        # Store patterns for other agents
        self.threat_patterns = [
            {"type": t, "count": c, "percentage": c/len(self.known_scams)*100}
            for t, c in sorted_types
        ]
    
    async def get_current_intelligence(self) -> Dict:
        """Return current intelligence for other agents"""
        return {
            "known_scams_count": len(self.known_scams),
            "watchlist_size": len(self.address_watchlist),
            "attack_signatures": len(self.attack_signatures),
            "queries_served": self.queries_served,
            "top_threat_types": self.threat_patterns[:3] if self.threat_patterns else [],
            "active": self.running,
            "capabilities": self.capabilities
        }
    
    async def propose_strategy(self, threat: Threat) -> Dict:
        """Intel's proposal based on historical data"""
        
        # Check if we've seen this before
        existing = await self.check_address(threat.target_address) if threat.target_address else None
        correlations = await self.find_correlations(threat)
        
        if existing:
            return {
                "agent": "Intel",
                "strategy": "KNOWN THREAT - Immediate action recommended",
                "confidence": 0.95,
                "existing_record": True,
                "correlations": len(correlations)
            }
        elif correlations:
            return {
                "agent": "Intel",
                "strategy": f"CORRELATED - Matches {len(correlations)} patterns",
                "confidence": 0.8,
                "existing_record": False,
                "correlations": len(correlations)
            }
        else:
            return {
                "agent": "Intel",
                "strategy": "NEW THREAT - No historical data",
                "confidence": 0.5,
                "existing_record": False,
                "correlations": 0
            }
    
    def export_knowledge_base(self) -> Dict:
        """Export the entire knowledge base"""
        return {
            "known_scams": self.known_scams,
            "attack_signatures": self.attack_signatures,
            "malicious_actors": self.malicious_actors,
            "threat_patterns": self.threat_patterns,
            "address_watchlist": list(self.address_watchlist),
            "exported_at": datetime.now().isoformat()
        }
