"""
QUANTUM Agent - Post-Quantum Cryptography Defense

Assesses quantum computing threats to Solana wallets and provides
migration roadmap to quantum-resistant cryptography.

NIST 2035 deadline tracking for harvest-now-decrypt-later attacks.
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from agents.core.base_agent import BaseAgent


class QuantumThreatLevel(Enum):
    """Quantum threat levels"""
    NONE = "none"           # No quantum threat
    LOW = "low"             # 10+ years out
    MEDIUM = "medium"       # 5-10 years
    HIGH = "high"           # 2-5 years
    CRITICAL = "critical"   # Imminent threat


class MigrationPhase(Enum):
    """Quantum migration phases"""
    ASSESSMENT = "assessment"
    PLANNING = "planning"
    HYBRID = "hybrid"
    MIGRATION = "migration"
    COMPLETE = "complete"


@dataclass
class QuantumAssessment:
    """Quantum readiness assessment for a wallet"""
    address: str
    quantum_score: int  # 0-100 (higher = more prepared)
    threat_level: QuantumThreatLevel
    vulnerabilities: List[str]
    recommendations: List[str]
    migration_phase: MigrationPhase
    estimated_safe_until: str  # Year estimate
    harvest_risk: bool  # Harvest-now-decrypt-later risk
    timestamp: datetime


class QuantumAgent(BaseAgent):
    """
    ⚛️ QUANTUM DEFENSE - Future-Proofing Agent
    
    Monitors quantum computing developments and assesses
    Solana wallet readiness for post-quantum cryptography.
    
    Features:
    - Quantum readiness scoring (0-100)
    - Harvest-now-decrypt-later risk assessment
    - NIST 2035 timeline tracking
    - Migration roadmap generation
    - Quantum-safe algorithm recommendations
    - Wallet quantum score calculation
    
    Based on NIST Post-Quantum Cryptography standards:
    - CRYSTALS-Kyber (key encapsulation)
    - CRYSTALS-Dilithium (signatures)
    - SPHINCS+ (hash-based signatures)
    """
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(
            name="QUANTUM",
            role="Future Defense",
            description="Post-quantum cryptography readiness",
            config=config
        )
        
        # Quantum timeline estimates (conservative)
        self.quantum_timeline = {
            "cryptographically_relevant": 2035,  # NIST estimate
            "early_warning": 2030,
            "planning_deadline": 2028,
            "current_year": datetime.now().year
        }
        
        # Vulnerability factors
        self.vulnerability_weights = {
            "ed25519_keys": 30,          # Current Solana signature scheme
            "high_value_wallet": 25,      # High-value targets
            "long_term_storage": 20,      # Keys stored for future use
            "institutional_wallet": 15,   # Institutional targets
            "public_key_exposed": 10      # Public key on-chain
        }
        
        # NIST approved post-quantum algorithms
        self.pq_algorithms = {
            "key_encapsulation": ["CRYSTALS-Kyber", "BIKE", "HQC"],
            "signatures": ["CRYSTALS-Dilithium", "FALCON", "SPHINCS+"],
            "hash_based": ["XMSS", "LMS"]
        }
        
        # Assessment history
        self.assessments: List[QuantumAssessment] = []
        
        # Statistics
        self.stats = {
            "wallets_assessed": 0,
            "high_risk_wallets": 0,
            "migration_plans_generated": 0
        }
    
    async def assess_wallet(
        self, 
        address: str,
        balance_usd: float = 0,
        is_institutional: bool = False,
        key_age_years: float = 0
    ) -> QuantumAssessment:
        """
        Assess a wallet's quantum readiness.
        
        Args:
            address: Wallet address
            balance_usd: Wallet balance in USD
            is_institutional: Whether it's an institutional wallet
            key_age_years: How long the key has been in use
        
        Returns:
            QuantumAssessment with score and recommendations
        """
        self.stats["wallets_assessed"] += 1
        
        vulnerabilities = []
        recommendations = []
        risk_score = 0
        
        # Check 1: Ed25519 vulnerability (all Solana wallets)
        vulnerabilities.append("Uses Ed25519 signatures (quantum-vulnerable)")
        risk_score += self.vulnerability_weights["ed25519_keys"]
        recommendations.append("Monitor Solana's transition to quantum-resistant signatures")
        
        # Check 2: High-value target
        if balance_usd >= 100_000:
            vulnerabilities.append(f"High-value wallet (${balance_usd:,.0f})")
            risk_score += self.vulnerability_weights["high_value_wallet"]
            recommendations.append("Consider distributing funds across multiple wallets")
        
        # Check 3: Long-term storage risk
        if key_age_years >= 2:
            vulnerabilities.append(f"Keys in use for {key_age_years:.1f} years")
            risk_score += self.vulnerability_weights["long_term_storage"]
            recommendations.append("Plan periodic key rotation")
        
        # Check 4: Institutional target
        if is_institutional:
            vulnerabilities.append("Institutional wallet (high-value target)")
            risk_score += self.vulnerability_weights["institutional_wallet"]
            recommendations.append("Implement quantum-readiness planning now")
        
        # Check 5: Public key exposure (all used wallets)
        vulnerabilities.append("Public key exposed on-chain")
        risk_score += self.vulnerability_weights["public_key_exposed"]
        
        # Calculate quantum score (inverse of risk)
        quantum_score = max(0, 100 - risk_score)
        
        # Determine threat level
        years_until_quantum = self.quantum_timeline["cryptographically_relevant"] - datetime.now().year
        if years_until_quantum <= 5:
            threat_level = QuantumThreatLevel.HIGH
        elif years_until_quantum <= 10:
            threat_level = QuantumThreatLevel.MEDIUM
        else:
            threat_level = QuantumThreatLevel.LOW
        
        # Harvest-now-decrypt-later risk
        harvest_risk = balance_usd >= 10_000 or is_institutional
        if harvest_risk:
            recommendations.append(
                "⚠️ HARVEST RISK: Adversaries may store encrypted data now "
                "to decrypt when quantum computers are available"
            )
        
        # Determine migration phase
        if quantum_score >= 80:
            migration_phase = MigrationPhase.ASSESSMENT
        elif quantum_score >= 60:
            migration_phase = MigrationPhase.PLANNING
        elif quantum_score >= 40:
            migration_phase = MigrationPhase.HYBRID
        else:
            migration_phase = MigrationPhase.MIGRATION
            self.stats["high_risk_wallets"] += 1
        
        # Add general recommendations
        recommendations.extend([
            "Follow NIST post-quantum cryptography standards",
            "Monitor Solana Foundation quantum-readiness announcements",
            f"Target migration completion before {self.quantum_timeline['planning_deadline']}"
        ])
        
        assessment = QuantumAssessment(
            address=address,
            quantum_score=quantum_score,
            threat_level=threat_level,
            vulnerabilities=vulnerabilities,
            recommendations=recommendations,
            migration_phase=migration_phase,
            estimated_safe_until=str(self.quantum_timeline["cryptographically_relevant"]),
            harvest_risk=harvest_risk,
            timestamp=datetime.now(timezone.utc)
        )
        
        self.assessments.append(assessment)
        return assessment
    
    async def get_quantum_timeline(self) -> Dict:
        """Get current quantum threat timeline."""
        current_year = datetime.now().year
        return {
            "current_year": current_year,
            "cryptographically_relevant_quantum": self.quantum_timeline["cryptographically_relevant"],
            "years_remaining": self.quantum_timeline["cryptographically_relevant"] - current_year,
            "planning_deadline": self.quantum_timeline["planning_deadline"],
            "early_warning": self.quantum_timeline["early_warning"],
            "threat_level": self._get_global_threat_level().value,
            "nist_approved_algorithms": self.pq_algorithms
        }
    
    def _get_global_threat_level(self) -> QuantumThreatLevel:
        """Calculate global quantum threat level."""
        years_remaining = self.quantum_timeline["cryptographically_relevant"] - datetime.now().year
        if years_remaining <= 2:
            return QuantumThreatLevel.CRITICAL
        elif years_remaining <= 5:
            return QuantumThreatLevel.HIGH
        elif years_remaining <= 10:
            return QuantumThreatLevel.MEDIUM
        else:
            return QuantumThreatLevel.LOW
    
    async def generate_migration_roadmap(self, address: str) -> Dict:
        """
        Generate a 5-step migration roadmap to quantum-resistant crypto.
        """
        self.stats["migration_plans_generated"] += 1
        
        return {
            "address": address,
            "roadmap": [
                {
                    "phase": 1,
                    "name": "Assessment",
                    "description": "Inventory all cryptographic assets and dependencies",
                    "timeline": "Immediate",
                    "actions": [
                        "Catalog all wallets and key pairs",
                        "Identify high-value targets",
                        "Document key management procedures"
                    ]
                },
                {
                    "phase": 2,
                    "name": "Planning",
                    "description": "Develop quantum migration strategy",
                    "timeline": f"Before {self.quantum_timeline['planning_deadline']}",
                    "actions": [
                        "Select target post-quantum algorithms",
                        "Plan hybrid cryptography transition",
                        "Budget for migration"
                    ]
                },
                {
                    "phase": 3,
                    "name": "Hybrid Implementation",
                    "description": "Implement hybrid classical/PQ cryptography",
                    "timeline": f"{self.quantum_timeline['planning_deadline']}-{self.quantum_timeline['early_warning']}",
                    "actions": [
                        "Deploy hybrid signature schemes",
                        "Test with small-value transactions",
                        "Monitor Solana protocol updates"
                    ]
                },
                {
                    "phase": 4,
                    "name": "Full Migration",
                    "description": "Complete transition to PQ cryptography",
                    "timeline": f"Before {self.quantum_timeline['cryptographically_relevant']}",
                    "actions": [
                        "Migrate all assets to PQ-secure wallets",
                        "Deprecate classical-only keys",
                        "Verify migration completeness"
                    ]
                },
                {
                    "phase": 5,
                    "name": "Maintenance",
                    "description": "Ongoing quantum security monitoring",
                    "timeline": "Continuous",
                    "actions": [
                        "Monitor quantum computing advances",
                        "Update algorithms as standards evolve",
                        "Regular security audits"
                    ]
                }
            ],
            "recommended_algorithms": self.pq_algorithms,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def process_task(self, task: Dict) -> Dict:
        """Process incoming tasks."""
        task_type = task.get("type")
        
        if task_type == "assess_wallet":
            assessment = await self.assess_wallet(
                address=task["address"],
                balance_usd=task.get("balance_usd", 0),
                is_institutional=task.get("is_institutional", False),
                key_age_years=task.get("key_age_years", 0)
            )
            return {
                "success": True,
                "assessment": {
                    "address": assessment.address,
                    "quantum_score": assessment.quantum_score,
                    "threat_level": assessment.threat_level.value,
                    "vulnerabilities": assessment.vulnerabilities,
                    "recommendations": assessment.recommendations,
                    "migration_phase": assessment.migration_phase.value,
                    "harvest_risk": assessment.harvest_risk
                }
            }
        
        elif task_type == "get_timeline":
            return {
                "success": True,
                "timeline": await self.get_quantum_timeline()
            }
        
        elif task_type == "generate_roadmap":
            roadmap = await self.generate_migration_roadmap(task["address"])
            return {"success": True, "roadmap": roadmap}
        
        return {"success": False, "error": f"Unknown task type: {task_type}"}
