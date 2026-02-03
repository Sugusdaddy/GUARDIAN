"""
REPORTER Agent - Community Communication & Alerts
Communicates threats and warnings to the community
"""
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional

from ..core.base_agent import AutonomousAgent, Threat, Decision
from ..core.config import AgentConfig, config


class ReporterAgent(AutonomousAgent):
    """
    REPORTER - The Herald
    
    Communicates with the community:
    - Sends threat alerts
    - Publishes security reports
    - Maintains public dashboard
    - Social media integration (Twitter, Discord)
    """
    
    def __init__(self, config: AgentConfig = config):
        super().__init__(
            role="REPORTER",
            agent_type="Reporter",
            capabilities=[
                "community_alerts",
                "report_generation",
                "social_media",
                "dashboard_updates"
            ],
            config=config
        )
        
        # Alert history
        self.alerts_sent: List[Dict] = []
        self.reports_generated: List[Dict] = []
        
        # Rate limiting
        self.last_alert_time: Dict[str, datetime] = {}
        self.alert_cooldown_seconds = 300  # 5 min between alerts for same threat
        
        # Channels (placeholders - would integrate with real APIs)
        self.channels = {
            "twitter": {"enabled": False, "handle": "@SolanaImmune"},
            "discord": {"enabled": False, "webhook": None},
            "telegram": {"enabled": False, "bot_token": None},
            "dashboard": {"enabled": True, "url": "https://immune.solana.com"}
        }
        
        self.log.info("📢 Reporter agent ready to communicate")
    
    async def scan_environment(self) -> List[Threat]:
        """Reporter doesn't scan - it responds to alert requests"""
        return []
    
    async def execute_action(self, decision: Decision, threat: Threat) -> Dict[str, Any]:
        """Execute reporting actions"""
        
        result = {"status": "success", "actions_taken": []}
        
        if decision.action in ["WARN", "BLOCK"]:
            # Send alert
            alert_result = await self.send_alert(threat, decision.reasoning)
            result["alert_sent"] = alert_result
            result["actions_taken"].append("alert_sent")
        
        return result
    
    async def send_alert(self, threat: Threat, reasoning: str) -> Dict:
        """Send alert to all enabled channels"""
        
        # Check rate limiting
        if not self._should_send_alert(threat):
            self.log.info(f"⏳ Alert rate-limited for threat #{threat.id}")
            return {"sent": False, "reason": "rate_limited"}
        
        # Create alert message
        alert = self._create_alert_message(threat, reasoning)
        
        results = {}
        
        # Send to each enabled channel
        if self.channels["dashboard"]["enabled"]:
            results["dashboard"] = await self._update_dashboard(alert)
        
        if self.channels["twitter"]["enabled"]:
            results["twitter"] = await self._post_twitter(alert)
        
        if self.channels["discord"]["enabled"]:
            results["discord"] = await self._post_discord(alert)
        
        if self.channels["telegram"]["enabled"]:
            results["telegram"] = await self._post_telegram(alert)
        
        # Record alert
        self.alerts_sent.append({
            "threat_id": threat.id,
            "alert": alert,
            "results": results,
            "timestamp": datetime.now().isoformat()
        })
        
        # Update rate limit tracking
        self.last_alert_time[str(threat.id)] = datetime.now()
        
        self.log.info(f"📢 Alert sent for threat #{threat.id}")
        
        return {"sent": True, "channels": results}
    
    def _should_send_alert(self, threat: Threat) -> bool:
        """Check if we should send an alert (rate limiting)"""
        
        last_time = self.last_alert_time.get(str(threat.id))
        if not last_time:
            return True
        
        elapsed = (datetime.now() - last_time).total_seconds()
        return elapsed > self.alert_cooldown_seconds
    
    def _create_alert_message(self, threat: Threat, reasoning: str) -> Dict:
        """Create formatted alert message"""
        
        severity_emoji = "🔴" if threat.severity > 80 else "🟠" if threat.severity > 50 else "🟡"
        
        # Short version for Twitter
        short_msg = f"{severity_emoji} SECURITY ALERT: {threat.threat_type} detected! "
        if threat.target_address:
            short_msg += f"Address: {threat.target_address[:8]}... "
        short_msg += f"Severity: {threat.severity}% #Solana #Security"
        
        # Long version for Discord/Telegram
        long_msg = f"""
{severity_emoji} **SOLANA IMMUNE SYSTEM ALERT** {severity_emoji}

**Threat Type:** {threat.threat_type}
**Severity:** {threat.severity}%
**Target:** {threat.target_address or 'N/A'}
**Detected By:** {threat.detected_by}

**Description:**
{threat.description}

**Analysis:**
{reasoning[:500]}{'...' if len(reasoning) > 500 else ''}

**Status:** Under investigation

🔗 View on Dashboard: {self.channels['dashboard']['url']}/threat/{threat.id}
"""
        
        return {
            "short": short_msg,
            "long": long_msg,
            "threat_id": threat.id,
            "severity": threat.severity,
            "threat_type": threat.threat_type,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _update_dashboard(self, alert: Dict) -> bool:
        """Update the public dashboard"""
        # Placeholder - would integrate with actual dashboard API
        self.log.debug(f"Dashboard updated with threat #{alert['threat_id']}")
        return True
    
    async def _post_twitter(self, alert: Dict) -> bool:
        """Post alert to Twitter"""
        # Placeholder - would integrate with Twitter API
        self.log.debug(f"Would post to Twitter: {alert['short'][:50]}...")
        return False  # Not actually posting
    
    async def _post_discord(self, alert: Dict) -> bool:
        """Post alert to Discord"""
        # Placeholder - would integrate with Discord webhook
        self.log.debug(f"Would post to Discord: threat #{alert['threat_id']}")
        return False
    
    async def _post_telegram(self, alert: Dict) -> bool:
        """Post alert to Telegram"""
        # Placeholder - would integrate with Telegram Bot API
        self.log.debug(f"Would post to Telegram: threat #{alert['threat_id']}")
        return False
    
    async def generate_daily_report(self) -> Dict:
        """Generate daily security report"""
        
        # Collect stats from all agents
        total_threats = 0
        blocked_threats = 0
        
        for agent in self.other_agents:
            if hasattr(agent, 'threat_history'):
                total_threats += len(agent.threat_history)
            if hasattr(agent, 'blocked_addresses'):
                blocked_threats += len(agent.blocked_addresses)
        
        report = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "threats_detected": total_threats,
            "threats_blocked": blocked_threats,
            "alerts_sent": len(self.alerts_sent),
            "agents_active": sum(1 for a in self.other_agents if a.running) + 1,
            "generated_at": datetime.now().isoformat()
        }
        
        self.reports_generated.append(report)
        self.log.info(f"📊 Daily report generated: {total_threats} threats, {blocked_threats} blocked")
        
        return report
    
    async def get_current_intelligence(self) -> Dict:
        """Return Reporter's current state"""
        return {
            "alerts_sent_today": sum(
                1 for a in self.alerts_sent 
                if a.get("timestamp", "").startswith(datetime.now().strftime("%Y-%m-%d"))
            ),
            "total_alerts": len(self.alerts_sent),
            "reports_generated": len(self.reports_generated),
            "channels_enabled": sum(1 for c in self.channels.values() if c.get("enabled")),
            "active": self.running,
            "capabilities": self.capabilities
        }
    
    async def propose_strategy(self, threat: Threat) -> Dict:
        """Reporter's proposal - communication strategy"""
        
        if threat.severity > 80:
            strategy = "Immediate multi-channel alert"
            confidence = 0.95
        elif threat.severity > 50:
            strategy = "Dashboard update + Discord alert"
            confidence = 0.8
        else:
            strategy = "Dashboard update only"
            confidence = 0.7
        
        return {
            "agent": "Reporter",
            "strategy": strategy,
            "confidence": confidence,
            "channels": [c for c, v in self.channels.items() if v.get("enabled")]
        }
