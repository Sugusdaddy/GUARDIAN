"""
NETWORK Agent - Solana Infrastructure Health Monitoring

Monitors Solana network health, TPS, block time, DDoS indicators,
MEV/sandwich attacks, validator stake concentration, and congestion.

The nervous system of the swarm - knows when the network is under stress.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from agents.core.base_agent import BaseAgent


class CongestionLevel(Enum):
    """Network congestion levels (1-5)"""
    CLEAR = 1          # Normal operations
    LIGHT = 2          # Slightly elevated
    MODERATE = 3       # Noticeable delays
    HEAVY = 4          # Significant congestion
    CRITICAL = 5       # Network degraded


class NetworkEvent(Enum):
    """Types of network events"""
    TPS_SPIKE = "tps_spike"
    TPS_DROP = "tps_drop"
    BLOCK_TIME_HIGH = "block_time_high"
    DDOS_SUSPECTED = "ddos_suspected"
    MEV_DETECTED = "mev_detected"
    SANDWICH_ATTACK = "sandwich_attack"
    VALIDATOR_CONCENTRATION = "validator_concentration"
    PROGRAM_UPGRADE = "program_upgrade"
    EPOCH_CHANGE = "epoch_change"


@dataclass
class NetworkStatus:
    """Current network status snapshot"""
    timestamp: datetime
    tps: float
    block_time_ms: float
    slot_height: int
    epoch: int
    congestion_level: CongestionLevel
    active_validators: int
    top_validator_stake_pct: float
    recent_events: List[Dict]
    health_score: int  # 0-100


@dataclass
class MEVAlert:
    """MEV/Sandwich attack detection"""
    timestamp: datetime
    attack_type: str  # "sandwich", "frontrun", "backrun"
    victim_signature: str
    attacker_address: str
    profit_estimate_sol: float
    affected_token: str


class NetworkAgent(BaseAgent):
    """
    🌐 NETWORK MONITOR - Nervous System Agent
    
    Real-time monitoring of Solana network health and threats.
    
    Features:
    - TPS tracking with anomaly detection
    - Block time monitoring
    - DDoS detection (10K+ TPS spikes)
    - MEV/Sandwich attack detection
    - Validator stake concentration analysis
    - 5-level congestion assessment
    - Program upgrade tracking
    - Epoch change notifications
    
    Thresholds:
    - Normal TPS: 2,000-4,000
    - DDoS indicator: >10,000 TPS
    - Normal block time: 400-600ms
    - High congestion: >800ms block time
    """
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(
            name="NETWORK",
            role="Infrastructure Monitor",
            description="Solana network health and threat detection",
            config=config
        )
        
        # Thresholds
        self.thresholds = {
            "tps_normal_low": 2000,
            "tps_normal_high": 4000,
            "tps_ddos_indicator": 10000,
            "tps_drop_critical": 500,
            "block_time_normal_ms": 500,
            "block_time_high_ms": 800,
            "block_time_critical_ms": 1200,
            "validator_concentration_warning": 33,  # Top validator % stake
            "sandwich_profit_threshold_sol": 0.01
        }
        
        # State
        self.current_status: Optional[NetworkStatus] = None
        self.status_history: List[NetworkStatus] = []
        self.mev_alerts: List[MEVAlert] = []
        self.events: List[Dict] = []
        
        # Monitoring state
        self.last_tps_values: List[float] = []
        self.watched_programs: Set[str] = set()
        
        # Statistics
        self.stats = {
            "status_checks": 0,
            "ddos_alerts": 0,
            "mev_detected": 0,
            "sandwich_attacks": 0,
            "high_congestion_periods": 0
        }
    
    async def check_network_status(self) -> NetworkStatus:
        """
        Check current Solana network status.
        
        In production, this would query:
        - Helius/RPC for TPS and block time
        - Solana validators API for stake distribution
        - Transaction simulation for congestion
        """
        self.stats["status_checks"] += 1
        
        # Simulated data (would be real RPC calls in production)
        tps = await self._get_current_tps()
        block_time = await self._get_block_time()
        slot_height = await self._get_slot_height()
        epoch = await self._get_epoch()
        validator_info = await self._get_validator_info()
        
        # Calculate congestion level
        congestion = self._calculate_congestion(tps, block_time)
        
        # Check for events
        events = await self._detect_events(tps, block_time, validator_info)
        
        # Calculate health score
        health_score = self._calculate_health_score(tps, block_time, congestion)
        
        status = NetworkStatus(
            timestamp=datetime.now(timezone.utc),
            tps=tps,
            block_time_ms=block_time,
            slot_height=slot_height,
            epoch=epoch,
            congestion_level=congestion,
            active_validators=validator_info.get("count", 0),
            top_validator_stake_pct=validator_info.get("top_stake_pct", 0),
            recent_events=[e for e in events],
            health_score=health_score
        )
        
        self.current_status = status
        self.status_history.append(status)
        
        # Keep last 1000 status checks
        if len(self.status_history) > 1000:
            self.status_history = self.status_history[-1000:]
        
        # Alert on critical events
        for event in events:
            if event.get("severity") == "critical":
                await self._emit_critical_alert(event)
        
        return status
    
    async def _get_current_tps(self) -> float:
        """Get current TPS from RPC."""
        # Would call getRecentPerformanceSamples in production
        # Placeholder returning simulated value
        import random
        return random.uniform(2500, 3500)
    
    async def _get_block_time(self) -> float:
        """Get current average block time."""
        # Would calculate from recent slots
        import random
        return random.uniform(400, 600)
    
    async def _get_slot_height(self) -> int:
        """Get current slot height."""
        # Would call getSlot
        return 300_000_000  # Placeholder
    
    async def _get_epoch(self) -> int:
        """Get current epoch."""
        # Would call getEpochInfo
        return 600  # Placeholder
    
    async def _get_validator_info(self) -> Dict:
        """Get validator stake distribution."""
        # Would call getVoteAccounts
        return {
            "count": 1800,
            "top_stake_pct": 8.5,  # Top validator's stake percentage
            "top_10_stake_pct": 35.0
        }
    
    def _calculate_congestion(self, tps: float, block_time: float) -> CongestionLevel:
        """Calculate network congestion level (1-5)."""
        score = 0
        
        # TPS factor
        if tps < self.thresholds["tps_drop_critical"]:
            score += 2
        elif tps > self.thresholds["tps_ddos_indicator"]:
            score += 2  # DDoS also causes congestion
        
        # Block time factor
        if block_time > self.thresholds["block_time_critical_ms"]:
            score += 2
        elif block_time > self.thresholds["block_time_high_ms"]:
            score += 1
        
        # Map score to congestion level
        if score >= 4:
            return CongestionLevel.CRITICAL
        elif score >= 3:
            return CongestionLevel.HEAVY
        elif score >= 2:
            return CongestionLevel.MODERATE
        elif score >= 1:
            return CongestionLevel.LIGHT
        return CongestionLevel.CLEAR
    
    async def _detect_events(
        self, 
        tps: float, 
        block_time: float,
        validator_info: Dict
    ) -> List[Dict]:
        """Detect network events based on metrics."""
        events = []
        
        # TPS anomalies
        if tps > self.thresholds["tps_ddos_indicator"]:
            events.append({
                "type": NetworkEvent.DDOS_SUSPECTED.value,
                "severity": "critical",
                "message": f"Possible DDoS: TPS at {tps:.0f}",
                "value": tps
            })
            self.stats["ddos_alerts"] += 1
        
        elif tps < self.thresholds["tps_drop_critical"]:
            events.append({
                "type": NetworkEvent.TPS_DROP.value,
                "severity": "warning",
                "message": f"TPS dropped to {tps:.0f}",
                "value": tps
            })
        
        # Block time issues
        if block_time > self.thresholds["block_time_critical_ms"]:
            events.append({
                "type": NetworkEvent.BLOCK_TIME_HIGH.value,
                "severity": "warning",
                "message": f"Block time elevated: {block_time:.0f}ms",
                "value": block_time
            })
            self.stats["high_congestion_periods"] += 1
        
        # Validator concentration
        if validator_info.get("top_stake_pct", 0) > self.thresholds["validator_concentration_warning"]:
            events.append({
                "type": NetworkEvent.VALIDATOR_CONCENTRATION.value,
                "severity": "info",
                "message": f"High validator concentration: top validator has {validator_info['top_stake_pct']:.1f}% stake",
                "value": validator_info["top_stake_pct"]
            })
        
        # Store events
        for event in events:
            event["timestamp"] = datetime.now(timezone.utc).isoformat()
            self.events.append(event)
        
        return events
    
    def _calculate_health_score(
        self, 
        tps: float, 
        block_time: float,
        congestion: CongestionLevel
    ) -> int:
        """Calculate overall network health score (0-100)."""
        score = 100
        
        # TPS penalty
        if tps < self.thresholds["tps_normal_low"]:
            score -= 20
        elif tps > self.thresholds["tps_ddos_indicator"]:
            score -= 30
        
        # Block time penalty
        if block_time > self.thresholds["block_time_high_ms"]:
            score -= 15
        if block_time > self.thresholds["block_time_critical_ms"]:
            score -= 25
        
        # Congestion penalty
        score -= (congestion.value - 1) * 10
        
        return max(0, score)
    
    async def detect_mev(self, transaction_signature: str) -> Optional[MEVAlert]:
        """
        Analyze a transaction for MEV/sandwich attack patterns.
        
        Would analyze surrounding transactions for:
        - Frontrunning (same token, higher priority fee)
        - Backrunning (same token, immediately after)
        - Sandwich (both front and back)
        """
        # Placeholder - would analyze transaction and surrounding slots
        return None
    
    async def _emit_critical_alert(self, event: Dict):
        """Emit critical network event to swarm."""
        self.log_warning(f"🚨 NETWORK ALERT: {event['message']}")
        await self.emit_event("network_critical", event)
    
    async def get_health_report(self) -> Dict:
        """Generate comprehensive network health report."""
        if not self.current_status:
            await self.check_network_status()
        
        status = self.current_status
        
        return {
            "timestamp": status.timestamp.isoformat(),
            "health_score": status.health_score,
            "tps": status.tps,
            "block_time_ms": status.block_time_ms,
            "congestion_level": status.congestion_level.name,
            "congestion_value": status.congestion_level.value,
            "slot_height": status.slot_height,
            "epoch": status.epoch,
            "validators": {
                "active": status.active_validators,
                "top_stake_pct": status.top_validator_stake_pct
            },
            "recent_events": status.recent_events[-10:],
            "statistics": self.stats,
            "thresholds": self.thresholds
        }
    
    async def process_task(self, task: Dict) -> Dict:
        """Process incoming tasks."""
        task_type = task.get("type")
        
        if task_type == "check_status":
            status = await self.check_network_status()
            return {
                "success": True,
                "status": {
                    "health_score": status.health_score,
                    "tps": status.tps,
                    "block_time_ms": status.block_time_ms,
                    "congestion": status.congestion_level.name,
                    "validators": status.active_validators
                }
            }
        
        elif task_type == "health_report":
            return {
                "success": True,
                "report": await self.get_health_report()
            }
        
        elif task_type == "detect_mev":
            alert = await self.detect_mev(task["signature"])
            return {
                "success": True,
                "mev_detected": alert is not None,
                "alert": alert.__dict__ if alert else None
            }
        
        elif task_type == "get_events":
            limit = task.get("limit", 50)
            return {
                "success": True,
                "events": self.events[-limit:]
            }
        
        elif task_type == "get_statistics":
            return {"success": True, "statistics": self.stats}
        
        return {"success": False, "error": f"Unknown task type: {task_type}"}


# Import Set for type hints
from typing import Set
