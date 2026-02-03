"""
GUARDIAN Telegram Bot - Real-time alerts and commands
"""
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
import structlog

from core.database import get_db
from core.config import config
from core.embeddings import get_scorer

logger = structlog.get_logger()


class GuardianTelegramBot:
    """
    Telegram bot for GUARDIAN alerts and commands.
    
    Commands:
    /start - Welcome message
    /status - System status
    /threats - Recent threats
    /blacklist - View blacklist
    /score <address> - Score an address
    /alert on|off - Toggle alerts
    """
    
    def __init__(self, token: str, chat_id: str = None):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.client = httpx.AsyncClient(timeout=30.0)
        self.db = get_db()
        self.scorer = get_scorer()
        self.running = False
        self.last_update_id = 0
        self.alerts_enabled = True
        
        logger.info("Telegram bot initialized")
    
    async def send_message(self, text: str, chat_id: str = None, parse_mode: str = "Markdown"):
        """Send a message"""
        target = chat_id or self.chat_id
        if not target:
            logger.warning("No chat_id specified")
            return
        
        try:
            await self.client.post(
                f"{self.base_url}/sendMessage",
                json={
                    "chat_id": target,
                    "text": text,
                    "parse_mode": parse_mode
                }
            )
        except Exception as e:
            logger.error("Failed to send message", error=str(e))
    
    async def send_alert(self, threat: dict):
        """Send threat alert"""
        if not self.alerts_enabled or not self.chat_id:
            return
        
        severity = threat.get("severity", 0)
        emoji = "🔴" if severity >= 80 else "🟠" if severity >= 60 else "🟡" if severity >= 40 else "🟢"
        
        message = f"""
{emoji} *GUARDIAN ALERT*

*Type:* `{threat.get('threat_type', 'Unknown')}`
*Severity:* {severity:.1f}/100
*Target:* `{(threat.get('target_address') or 'N/A')[:20]}...`

{threat.get('description', '')}

*Detected by:* {threat.get('detected_by', 'Unknown')}
*Time:* {datetime.now().strftime('%H:%M:%S')}
"""
        await self.send_message(message)
    
    async def handle_command(self, message: dict):
        """Handle incoming command"""
        text = message.get("text", "")
        chat_id = str(message["chat"]["id"])
        
        if not text.startswith("/"):
            return
        
        parts = text.split()
        command = parts[0].lower().replace("@", " ").split()[0]
        args = parts[1:] if len(parts) > 1 else []
        
        if command == "/start":
            await self.cmd_start(chat_id)
        elif command == "/status":
            await self.cmd_status(chat_id)
        elif command == "/threats":
            await self.cmd_threats(chat_id)
        elif command == "/blacklist":
            await self.cmd_blacklist(chat_id)
        elif command == "/score":
            await self.cmd_score(chat_id, args)
        elif command == "/alert":
            await self.cmd_alert(chat_id, args)
        elif command == "/help":
            await self.cmd_help(chat_id)
    
    async def cmd_start(self, chat_id: str):
        """Welcome message"""
        message = """
🛡️ *GUARDIAN Bot*
_Solana Immune System_

I'll keep you updated on threats detected in the Solana ecosystem.

*Commands:*
/status - System status
/threats - Recent threats
/blacklist - Known bad actors
/score <address> - Risk assessment
/alert on|off - Toggle alerts
/help - Show help

Stay safe! 🔒
"""
        await self.send_message(message, chat_id)
        self.chat_id = chat_id  # Save chat ID for alerts
    
    async def cmd_status(self, chat_id: str):
        """System status"""
        stats = self.db.get_threat_stats()
        agents = self.db.get_all_agent_stats()
        
        message = f"""
📊 *GUARDIAN Status*

*Threats:*
├ Active: {stats.get('by_status', {}).get('active', 0)}
├ Resolved: {stats.get('by_status', {}).get('resolved', 0)}
├ Last 24h: {stats.get('last_24h', 0)}
└ Avg Severity: {stats.get('avg_severity', 0):.1f}

*Agents:* {len(agents)} active
*Blacklisted:* {len(self.db.get_blacklist())} addresses
*Network:* {config.network}
*Alerts:* {'✅ ON' if self.alerts_enabled else '❌ OFF'}

_Updated: {datetime.now().strftime('%H:%M:%S')}_
"""
        await self.send_message(message, chat_id)
    
    async def cmd_threats(self, chat_id: str):
        """Recent threats"""
        threats = self.db.get_active_threats(limit=5)
        
        if not threats:
            await self.send_message("✅ No active threats!", chat_id)
            return
        
        message = "🚨 *Recent Threats*\n\n"
        
        for t in threats:
            sev = t.get('severity', 0)
            emoji = "🔴" if sev >= 80 else "🟠" if sev >= 60 else "🟡"
            message += f"{emoji} *{t['threat_type']}* - {sev:.0f}\n"
            message += f"└ `{(t.get('target_address') or 'N/A')[:16]}...`\n\n"
        
        await self.send_message(message, chat_id)
    
    async def cmd_blacklist(self, chat_id: str):
        """Show blacklist"""
        blacklist = self.db.get_blacklist(min_severity=70)[:10]
        
        if not blacklist:
            await self.send_message("📋 Blacklist is empty", chat_id)
            return
        
        message = "🚫 *High-Risk Blacklist*\n\n"
        
        for b in blacklist:
            message += f"• `{b['address'][:16]}...` ({b['severity']})\n"
            message += f"  _{b.get('reason', 'No reason')[:30]}_\n\n"
        
        await self.send_message(message, chat_id)
    
    async def cmd_score(self, chat_id: str, args: list):
        """Score an address"""
        if not args:
            await self.send_message("Usage: `/score <address>`", chat_id)
            return
        
        address = args[0]
        
        # Build threat for scoring
        threat = {
            "threat_type": "Unknown",
            "severity": 50,
            "target_address": address,
            "description": f"Risk check for {address}",
            "evidence": {}
        }
        
        blacklist = set(b["address"] for b in self.db.get_blacklist())
        patterns = self.db.get_patterns(min_confidence=0.5)
        
        result = self.scorer.score_threat(threat, blacklist, patterns)
        score = result["final_score"]
        
        emoji = "🔴" if score >= 80 else "🟠" if score >= 60 else "🟡" if score >= 40 else "🟢"
        
        message = f"""
{emoji} *Risk Assessment*

*Address:* `{address[:20]}...`
*Score:* {score:.1f}/100
*Recommendation:* {result['recommendation']}

*Components:*
├ ML Score: {result['component_scores'].get('ml_score', 0):.1f}
├ Blacklist: {'⚠️ MATCH' if result['component_scores'].get('blacklist_match', 0) > 0 else '✅ Clean'}
└ Anomaly: {result['component_scores'].get('anomaly', 0):.1f}
"""
        await self.send_message(message, chat_id)
    
    async def cmd_alert(self, chat_id: str, args: list):
        """Toggle alerts"""
        if not args:
            status = "✅ ON" if self.alerts_enabled else "❌ OFF"
            await self.send_message(f"Alerts are currently {status}\n\nUse `/alert on` or `/alert off`", chat_id)
            return
        
        if args[0].lower() == "on":
            self.alerts_enabled = True
            self.chat_id = chat_id
            await self.send_message("✅ Alerts enabled! You'll receive threat notifications.", chat_id)
        elif args[0].lower() == "off":
            self.alerts_enabled = False
            await self.send_message("❌ Alerts disabled.", chat_id)
    
    async def cmd_help(self, chat_id: str):
        """Show help"""
        await self.cmd_start(chat_id)
    
    async def poll_updates(self):
        """Poll for new messages"""
        try:
            response = await self.client.get(
                f"{self.base_url}/getUpdates",
                params={
                    "offset": self.last_update_id + 1,
                    "timeout": 30
                }
            )
            
            data = response.json()
            
            if data.get("ok") and data.get("result"):
                for update in data["result"]:
                    self.last_update_id = update["update_id"]
                    
                    if "message" in update:
                        await self.handle_command(update["message"])
                        
        except Exception as e:
            logger.error("Poll error", error=str(e))
    
    async def start(self):
        """Start the bot"""
        self.running = True
        logger.info("Telegram bot starting...")
        
        while self.running:
            await self.poll_updates()
            await asyncio.sleep(1)
    
    async def stop(self):
        """Stop the bot"""
        self.running = False
        await self.client.aclose()
        logger.info("Telegram bot stopped")


async def main():
    """Run the bot"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN not set in .env")
        print("\nTo create a bot:")
        print("1. Message @BotFather on Telegram")
        print("2. Send /newbot and follow instructions")
        print("3. Copy the token to your .env file")
        return
    
    bot = GuardianTelegramBot(token, chat_id)
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())
