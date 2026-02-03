"""
GUARDIAN Webhook Server - Real-time event processing from Helius
"""
import asyncio
import json
import hashlib
import hmac
from datetime import datetime
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass, field

import structlog
from aiohttp import web

from ..core.config import config
from ..core.database import get_db

logger = structlog.get_logger()


@dataclass
class WebhookEvent:
    """Parsed webhook event"""
    event_type: str
    signature: str
    timestamp: int
    data: Dict[str, Any]
    raw: Dict[str, Any]
    received_at: datetime = field(default_factory=datetime.now)


class HeliusWebhookServer:
    """
    Webhook server for receiving real-time events from Helius.
    Distributes events to registered handlers (agents).
    """
    
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8080,
        webhook_secret: str = None
    ):
        self.host = host
        self.port = port
        self.webhook_secret = webhook_secret or config.helius_webhook_secret
        
        self.app = web.Application()
        self.runner: Optional[web.AppRunner] = None
        
        # Event handlers by type
        self.handlers: Dict[str, List[Callable]] = {
            "TRANSFER": [],
            "SWAP": [],
            "NFT_SALE": [],
            "NFT_MINT": [],
            "TOKEN_MINT": [],
            "UNKNOWN": [],
            "*": [],  # Catch-all
        }
        
        # Event queue for async processing
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.processing = False
        
        # Stats
        self.events_received = 0
        self.events_processed = 0
        self.errors = 0
        
        self._setup_routes()
        logger.info("Webhook server initialized", port=port)
    
    def _setup_routes(self):
        """Setup HTTP routes"""
        self.app.router.add_post("/webhook/helius", self._handle_helius_webhook)
        self.app.router.add_get("/health", self._health_check)
        self.app.router.add_get("/stats", self._get_stats)
    
    async def start(self):
        """Start the webhook server"""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        
        site = web.TCPSite(self.runner, self.host, self.port)
        await site.start()
        
        # Start event processor
        self.processing = True
        asyncio.create_task(self._process_events())
        
        logger.info(f"Webhook server started", url=f"http://{self.host}:{self.port}")
    
    async def stop(self):
        """Stop the webhook server"""
        self.processing = False
        if self.runner:
            await self.runner.cleanup()
        logger.info("Webhook server stopped")
    
    def register_handler(self, event_type: str, handler: Callable):
        """Register a handler for an event type"""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
        logger.info(f"Registered handler for {event_type}")
    
    def unregister_handler(self, event_type: str, handler: Callable):
        """Unregister a handler"""
        if event_type in self.handlers:
            self.handlers[event_type] = [h for h in self.handlers[event_type] if h != handler]
    
    async def _handle_helius_webhook(self, request: web.Request) -> web.Response:
        """Handle incoming Helius webhook"""
        try:
            # Verify signature if secret is set
            if self.webhook_secret:
                signature = request.headers.get("X-Helius-Signature", "")
                body = await request.read()
                
                expected = hmac.new(
                    self.webhook_secret.encode(),
                    body,
                    hashlib.sha256
                ).hexdigest()
                
                if not hmac.compare_digest(signature, expected):
                    logger.warning("Invalid webhook signature")
                    return web.Response(status=401, text="Invalid signature")
                
                data = json.loads(body)
            else:
                data = await request.json()
            
            self.events_received += 1
            
            # Parse events (Helius sends array)
            events = data if isinstance(data, list) else [data]
            
            for event_data in events:
                event = self._parse_event(event_data)
                await self.event_queue.put(event)
            
            return web.Response(status=200, text="OK")
            
        except Exception as e:
            self.errors += 1
            logger.error("Error handling webhook", error=str(e))
            return web.Response(status=500, text=str(e))
    
    def _parse_event(self, data: Dict) -> WebhookEvent:
        """Parse raw webhook data into event"""
        # Helius enhanced transaction format
        event_type = data.get("type", "UNKNOWN")
        signature = data.get("signature", "")
        timestamp = data.get("timestamp", 0)
        
        # Extract relevant fields
        parsed_data = {
            "description": data.get("description", ""),
            "fee": data.get("fee", 0),
            "fee_payer": data.get("feePayer", ""),
            "slot": data.get("slot", 0),
            "source": data.get("source", ""),
        }
        
        # Token transfers
        if "tokenTransfers" in data:
            parsed_data["token_transfers"] = data["tokenTransfers"]
        
        # Native transfers
        if "nativeTransfers" in data:
            parsed_data["native_transfers"] = data["nativeTransfers"]
        
        # Account data
        if "accountData" in data:
            parsed_data["account_data"] = data["accountData"]
        
        # Instructions
        if "instructions" in data:
            parsed_data["instructions"] = data["instructions"]
        
        return WebhookEvent(
            event_type=event_type,
            signature=signature,
            timestamp=timestamp,
            data=parsed_data,
            raw=data
        )
    
    async def _process_events(self):
        """Process events from queue"""
        while self.processing:
            try:
                # Wait for event with timeout
                try:
                    event = await asyncio.wait_for(
                        self.event_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Get handlers for this event type
                handlers = self.handlers.get(event.event_type, [])
                handlers.extend(self.handlers.get("*", []))
                
                if not handlers:
                    logger.debug(f"No handlers for event type: {event.event_type}")
                    continue
                
                # Call all handlers concurrently
                tasks = [h(event) for h in handlers]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Log errors
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.error(
                            "Handler error",
                            handler=handlers[i].__name__,
                            error=str(result)
                        )
                        self.errors += 1
                
                self.events_processed += 1
                
            except Exception as e:
                logger.error("Event processing error", error=str(e))
                self.errors += 1
    
    async def _health_check(self, request: web.Request) -> web.Response:
        """Health check endpoint"""
        return web.json_response({
            "status": "healthy",
            "events_received": self.events_received,
            "events_processed": self.events_processed,
            "queue_size": self.event_queue.qsize(),
            "errors": self.errors
        })
    
    async def _get_stats(self, request: web.Request) -> web.Response:
        """Get server statistics"""
        return web.json_response({
            "uptime": "N/A",  # Would track start time
            "events_received": self.events_received,
            "events_processed": self.events_processed,
            "events_pending": self.event_queue.qsize(),
            "errors": self.errors,
            "handlers": {k: len(v) for k, v in self.handlers.items()}
        })


class AlertDispatcher:
    """
    Dispatches alerts to multiple channels (Discord, Telegram, Twitter, etc.)
    """
    
    def __init__(self):
        self.channels: Dict[str, Dict] = {}
        self.db = get_db()
    
    def add_channel(self, name: str, channel_type: str, config: Dict):
        """Add an alert channel"""
        self.channels[name] = {
            "type": channel_type,
            "config": config,
            "enabled": True
        }
    
    async def send_alert(
        self,
        threat_id: int,
        message: str,
        severity: int = 50,
        channels: List[str] = None
    ):
        """Send alert to specified channels (or all if None)"""
        targets = channels or list(self.channels.keys())
        
        for channel_name in targets:
            if channel_name not in self.channels:
                continue
            
            channel = self.channels[channel_name]
            if not channel["enabled"]:
                continue
            
            try:
                if channel["type"] == "discord":
                    await self._send_discord(channel["config"], message, severity)
                elif channel["type"] == "telegram":
                    await self._send_telegram(channel["config"], message)
                elif channel["type"] == "twitter":
                    await self._send_twitter(channel["config"], message)
                elif channel["type"] == "webhook":
                    await self._send_webhook(channel["config"], message, severity)
                
                # Record in database
                self.db.record_alert(threat_id, channel_name, message)
                
            except Exception as e:
                logger.error(f"Failed to send alert to {channel_name}", error=str(e))
    
    async def _send_discord(self, config: Dict, message: str, severity: int):
        """Send Discord webhook"""
        import aiohttp
        
        webhook_url = config.get("webhook_url")
        if not webhook_url:
            return
        
        # Color based on severity
        if severity >= 80:
            color = 0xFF0000  # Red
        elif severity >= 60:
            color = 0xFFA500  # Orange
        elif severity >= 40:
            color = 0xFFFF00  # Yellow
        else:
            color = 0x00FF00  # Green
        
        embed = {
            "title": "🛡️ GUARDIAN Alert",
            "description": message,
            "color": color,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "Solana Immune System"}
        }
        
        async with aiohttp.ClientSession() as session:
            await session.post(
                webhook_url,
                json={"embeds": [embed]}
            )
    
    async def _send_telegram(self, config: Dict, message: str):
        """Send Telegram message"""
        import aiohttp
        
        bot_token = config.get("bot_token")
        chat_id = config.get("chat_id")
        if not bot_token or not chat_id:
            return
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        async with aiohttp.ClientSession() as session:
            await session.post(url, json={
                "chat_id": chat_id,
                "text": f"🛡️ *GUARDIAN Alert*\n\n{message}",
                "parse_mode": "Markdown"
            })
    
    async def _send_twitter(self, config: Dict, message: str):
        """Send tweet (placeholder - needs Twitter API)"""
        logger.info("Twitter alert (not implemented)", message=message[:50])
    
    async def _send_webhook(self, config: Dict, message: str, severity: int):
        """Send to generic webhook"""
        import aiohttp
        
        url = config.get("url")
        if not url:
            return
        
        async with aiohttp.ClientSession() as session:
            await session.post(url, json={
                "source": "guardian",
                "message": message,
                "severity": severity,
                "timestamp": datetime.utcnow().isoformat()
            })


# Singleton instances
_webhook_server: Optional[HeliusWebhookServer] = None
_alert_dispatcher: Optional[AlertDispatcher] = None


def get_webhook_server(port: int = 8080) -> HeliusWebhookServer:
    global _webhook_server
    if _webhook_server is None:
        _webhook_server = HeliusWebhookServer(port=port)
    return _webhook_server


def get_alert_dispatcher() -> AlertDispatcher:
    global _alert_dispatcher
    if _alert_dispatcher is None:
        _alert_dispatcher = AlertDispatcher()
    return _alert_dispatcher
