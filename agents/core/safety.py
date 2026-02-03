"""
Safety Module - Human Oversight & Fallback Systems

Implements critical safety mechanisms:
1. Human approval for high-risk actions
2. Deterministic fallbacks when AI unavailable
3. Rate limiting and cooldowns
4. Emergency stop functionality
"""
import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import structlog

logger = structlog.get_logger()


class ActionSeverity(Enum):
    """Severity levels for actions"""
    LOW = 1      # Monitor only
    MEDIUM = 2   # Warn users
    HIGH = 3     # Block/coordinate
    CRITICAL = 4 # Requires human approval


@dataclass
class SafetyConfig:
    """Safety configuration"""
    # Human approval thresholds
    require_human_approval_above_severity: ActionSeverity = ActionSeverity.HIGH
    require_human_approval_above_value_usd: float = 10000
    require_human_approval_for_new_patterns: bool = True
    
    # Consensus requirements
    min_agents_for_block: int = 3
    min_confidence_for_action: float = 0.70
    
    # Rate limiting
    max_blocks_per_hour: int = 10
    cooldown_seconds: int = 300  # 5 minutes
    
    # Fallback behavior
    use_deterministic_fallback: bool = True
    fallback_confidence_threshold: float = 0.90
    
    # Emergency stop
    emergency_stop_enabled: bool = False


class SafetyGuard:
    """
    Central safety guard for the agent swarm.
    Ensures human oversight and prevents runaway autonomous actions.
    """
    
    def __init__(self, config: SafetyConfig = None):
        self.config = config or SafetyConfig()
        
        # Action tracking
        self.recent_actions: List[Dict] = []
        self.blocked_addresses: Dict[str, datetime] = {}
        self.pending_human_approval: List[Dict] = []
        
        # Emergency state
        self._emergency_stop = os.getenv("EMERGENCY_STOP", "").lower() == "true"
        
        # Callbacks for human approval
        self._human_approval_callback: Optional[Callable] = None
        
        logger.info("SafetyGuard initialized", config=str(config))
    
    @property
    def emergency_stop(self) -> bool:
        """Check if emergency stop is active"""
        return self._emergency_stop or self.config.emergency_stop_enabled
    
    def activate_emergency_stop(self, reason: str):
        """Activate emergency stop"""
        self._emergency_stop = True
        logger.critical("EMERGENCY STOP ACTIVATED", reason=reason)
    
    def deactivate_emergency_stop(self):
        """Deactivate emergency stop (requires confirmation)"""
        self._emergency_stop = False
        logger.warning("Emergency stop deactivated")
    
    async def check_action_allowed(
        self,
        action: str,
        severity: ActionSeverity,
        target_address: Optional[str],
        confidence: float,
        estimated_value_usd: float = 0,
        is_new_pattern: bool = False,
        agent_votes: int = 1
    ) -> Dict:
        """
        Check if an action is allowed by safety rules.
        
        Returns:
            {
                "allowed": bool,
                "reason": str,
                "requires_human_approval": bool,
                "fallback_action": Optional[str]
            }
        """
        result = {
            "allowed": True,
            "reason": "passed_all_checks",
            "requires_human_approval": False,
            "fallback_action": None
        }
        
        # Check 1: Emergency stop
        if self.emergency_stop:
            return {
                "allowed": False,
                "reason": "emergency_stop_active",
                "requires_human_approval": False,
                "fallback_action": "monitor_only"
            }
        
        # Check 2: Confidence threshold
        if confidence < self.config.min_confidence_for_action:
            return {
                "allowed": False,
                "reason": f"confidence_too_low ({confidence:.0%} < {self.config.min_confidence_for_action:.0%})",
                "requires_human_approval": False,
                "fallback_action": "monitor_only"
            }
        
        # Check 3: Consensus for blocking actions
        if action in ["BLOCK", "COORDINATE"] and agent_votes < self.config.min_agents_for_block:
            return {
                "allowed": False,
                "reason": f"insufficient_consensus ({agent_votes} < {self.config.min_agents_for_block})",
                "requires_human_approval": False,
                "fallback_action": "warn_only"
            }
        
        # Check 4: Rate limiting
        if action == "BLOCK":
            recent_blocks = sum(
                1 for a in self.recent_actions
                if a["action"] == "BLOCK" and 
                datetime.fromisoformat(a["timestamp"]) > datetime.now() - timedelta(hours=1)
            )
            if recent_blocks >= self.config.max_blocks_per_hour:
                return {
                    "allowed": False,
                    "reason": f"rate_limit_exceeded ({recent_blocks} blocks in last hour)",
                    "requires_human_approval": True,
                    "fallback_action": "warn_only"
                }
        
        # Check 5: Cooldown for same address
        if target_address and target_address in self.blocked_addresses:
            last_block = self.blocked_addresses[target_address]
            if datetime.now() - last_block < timedelta(seconds=self.config.cooldown_seconds):
                return {
                    "allowed": False,
                    "reason": "address_in_cooldown",
                    "requires_human_approval": False,
                    "fallback_action": None
                }
        
        # Check 6: Human approval requirements
        needs_human = False
        if severity.value >= self.config.require_human_approval_above_severity.value:
            needs_human = True
            result["reason"] = "severity_requires_approval"
        elif estimated_value_usd > self.config.require_human_approval_above_value_usd:
            needs_human = True
            result["reason"] = "value_requires_approval"
        elif is_new_pattern and self.config.require_human_approval_for_new_patterns:
            needs_human = True
            result["reason"] = "new_pattern_requires_approval"
        
        if needs_human:
            result["requires_human_approval"] = True
            # Queue for human approval
            self.pending_human_approval.append({
                "action": action,
                "severity": severity.name,
                "target": target_address,
                "confidence": confidence,
                "value_usd": estimated_value_usd,
                "queued_at": datetime.now().isoformat()
            })
            logger.warning(
                "Action requires human approval",
                action=action,
                reason=result["reason"]
            )
        
        return result
    
    def record_action(self, action: str, target_address: Optional[str], result: str):
        """Record an action for rate limiting and audit"""
        self.recent_actions.append({
            "action": action,
            "target": target_address,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
        if action == "BLOCK" and target_address:
            self.blocked_addresses[target_address] = datetime.now()
        
        # Keep only last 1000 actions
        if len(self.recent_actions) > 1000:
            self.recent_actions = self.recent_actions[-1000:]
    
    def get_pending_approvals(self) -> List[Dict]:
        """Get actions pending human approval"""
        return self.pending_human_approval.copy()
    
    def approve_action(self, index: int) -> bool:
        """Approve a pending action"""
        if 0 <= index < len(self.pending_human_approval):
            action = self.pending_human_approval.pop(index)
            logger.info("Action approved by human", action=action)
            return True
        return False
    
    def reject_action(self, index: int) -> bool:
        """Reject a pending action"""
        if 0 <= index < len(self.pending_human_approval):
            action = self.pending_human_approval.pop(index)
            logger.info("Action rejected by human", action=action)
            return True
        return False


class DeterministicFallback:
    """
    Rule-based fallback system when AI is unavailable.
    Uses deterministic rules instead of AI for threat detection.
    """
    
    # Known scam indicators and their risk scores
    RULES = {
        "mint_authority_enabled": 25,
        "freeze_authority_enabled": 15,
        "top_holder_above_90_percent": 25,
        "liquidity_below_1000_usd": 20,
        "token_age_below_24h": 10,
        "name_copies_known_token": 20,
        "no_social_links": 10,
        "suspicious_transfer_pattern": 15,
        "known_scammer_interaction": 30,
    }
    
    # Known legitimate tokens (whitelist)
    WHITELIST = {
        "So11111111111111111111111111111111111111112",  # SOL
        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
        "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",  # USDT
    }
    
    @classmethod
    def analyze_token(cls, token_data: Dict) -> Dict:
        """
        Analyze a token using deterministic rules.
        
        Returns:
            {
                "risk_score": 0-100,
                "flags": List[str],
                "recommendation": str,
                "confidence": float
            }
        """
        mint = token_data.get("mint", "")
        
        # Check whitelist
        if mint in cls.WHITELIST:
            return {
                "risk_score": 0,
                "flags": [],
                "recommendation": "IGNORE",
                "confidence": 1.0
            }
        
        flags = []
        score = 0
        
        # Check each rule
        if token_data.get("mint_authority"):
            flags.append("mint_authority_enabled")
            score += cls.RULES["mint_authority_enabled"]
        
        if token_data.get("freeze_authority"):
            flags.append("freeze_authority_enabled")
            score += cls.RULES["freeze_authority_enabled"]
        
        top_holder = token_data.get("top_holder_percentage", 0)
        if top_holder > 90:
            flags.append("top_holder_above_90_percent")
            score += cls.RULES["top_holder_above_90_percent"]
        
        liquidity = token_data.get("liquidity_usd", 0)
        if liquidity < 1000:
            flags.append("liquidity_below_1000_usd")
            score += cls.RULES["liquidity_below_1000_usd"]
        
        age_hours = token_data.get("age_hours", 0)
        if age_hours < 24:
            flags.append("token_age_below_24h")
            score += cls.RULES["token_age_below_24h"]
        
        # Cap at 100
        score = min(score, 100)
        
        # Determine recommendation
        if score >= 70:
            recommendation = "BLOCK"
        elif score >= 50:
            recommendation = "WARN"
        elif score >= 30:
            recommendation = "MONITOR"
        else:
            recommendation = "IGNORE"
        
        # Confidence based on number of flags
        confidence = min(0.5 + (len(flags) * 0.1), 0.95)
        
        return {
            "risk_score": score,
            "flags": flags,
            "recommendation": recommendation,
            "confidence": confidence
        }
    
    @classmethod
    def analyze_transaction(cls, tx_data: Dict) -> Dict:
        """Analyze a transaction using deterministic rules"""
        flags = []
        score = 0
        
        amount_sol = tx_data.get("amount_sol", 0)
        
        # Large transfer
        if amount_sol > 1000:
            flags.append("large_transfer")
            score += 30
        
        # Known bad address
        if tx_data.get("involves_known_scammer"):
            flags.append("known_scammer_interaction")
            score += cls.RULES["known_scammer_interaction"]
        
        score = min(score, 100)
        
        if score >= 50:
            recommendation = "WARN"
        else:
            recommendation = "MONITOR"
        
        return {
            "risk_score": score,
            "flags": flags,
            "recommendation": recommendation,
            "confidence": 0.7 if flags else 0.5
        }


# Global safety guard instance
_safety_guard: Optional[SafetyGuard] = None


def get_safety_guard() -> SafetyGuard:
    """Get or create the global safety guard"""
    global _safety_guard
    if _safety_guard is None:
        _safety_guard = SafetyGuard()
    return _safety_guard
