"""
Helius Integration - Real-time Solana monitoring
"""
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
import httpx
import structlog

logger = structlog.get_logger()


class HeliusClient:
    """
    Client for Helius API integration.
    Provides real-time transaction monitoring and blockchain data.
    """
    
    def __init__(self, api_key: str, network: str = "devnet"):
        self.api_key = api_key
        self.network = network
        
        if network == "mainnet":
            self.rpc_url = f"https://mainnet.helius-rpc.com/?api-key={api_key}"
            self.api_url = "https://api.helius.xyz/v0"
        else:
            self.rpc_url = f"https://devnet.helius-rpc.com/?api-key={api_key}"
            self.api_url = "https://api-devnet.helius.xyz/v0"
        
        self.client = httpx.AsyncClient(timeout=30.0)
        logger.info(f"Helius client initialized for {network}")
    
    async def close(self):
        await self.client.aclose()
    
    # ============== RPC Methods ==============
    
    async def get_balance(self, address: str) -> float:
        """Get SOL balance for an address"""
        response = await self.client.post(
            self.rpc_url,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBalance",
                "params": [address]
            }
        )
        data = response.json()
        if "result" in data:
            return data["result"]["value"] / 1_000_000_000
        return 0
    
    async def get_signatures(self, address: str, limit: int = 100) -> List[Dict]:
        """Get recent transaction signatures for an address"""
        response = await self.client.post(
            self.rpc_url,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getSignaturesForAddress",
                "params": [address, {"limit": limit}]
            }
        )
        data = response.json()
        return data.get("result", [])
    
    async def get_transaction(self, signature: str) -> Optional[Dict]:
        """Get parsed transaction details"""
        response = await self.client.post(
            self.rpc_url,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTransaction",
                "params": [signature, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}]
            }
        )
        data = response.json()
        return data.get("result")
    
    # ============== Enhanced API Methods ==============
    
    async def get_parsed_transactions(self, address: str, limit: int = 50) -> List[Dict]:
        """Get parsed transaction history using Helius Enhanced API"""
        try:
            response = await self.client.get(
                f"{self.api_url}/addresses/{address}/transactions",
                params={"api-key": self.api_key, "limit": limit}
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching transactions", error=str(e))
        return []
    
    async def get_token_metadata(self, mint: str) -> Optional[Dict]:
        """Get token metadata using DAS API"""
        try:
            response = await self.client.post(
                self.rpc_url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getAsset",
                    "params": {"id": mint}
                }
            )
            data = response.json()
            return data.get("result")
        except Exception as e:
            logger.error(f"Error fetching token metadata", error=str(e))
        return None
    
    async def search_assets(self, owner: Optional[str] = None, 
                           token_type: str = "fungible",
                           limit: int = 50) -> List[Dict]:
        """Search for assets using DAS API"""
        try:
            params = {
                "tokenType": token_type,
                "limit": limit
            }
            if owner:
                params["ownerAddress"] = owner
            
            response = await self.client.post(
                self.rpc_url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "searchAssets",
                    "params": params
                }
            )
            data = response.json()
            return data.get("result", {}).get("items", [])
        except Exception as e:
            logger.error(f"Error searching assets", error=str(e))
        return []
    
    async def get_token_holders(self, mint: str, limit: int = 100) -> List[Dict]:
        """Get token holders"""
        try:
            response = await self.client.get(
                f"{self.api_url}/tokens/{mint}/holders",
                params={"api-key": self.api_key, "limit": limit}
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching token holders", error=str(e))
        return []
    
    # ============== Webhook Management ==============
    
    async def create_webhook(self, webhook_url: str, 
                            transaction_types: List[str] = None,
                            account_addresses: List[str] = None) -> Optional[str]:
        """Create a webhook for real-time monitoring"""
        try:
            payload = {
                "webhookURL": webhook_url,
                "transactionTypes": transaction_types or ["Any"],
                "accountAddresses": account_addresses or [],
                "webhookType": "enhanced"
            }
            
            response = await self.client.post(
                f"{self.api_url}/webhooks",
                params={"api-key": self.api_key},
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Webhook created: {data.get('webhookID')}")
                return data.get("webhookID")
        except Exception as e:
            logger.error(f"Error creating webhook", error=str(e))
        return None
    
    async def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a webhook"""
        try:
            response = await self.client.delete(
                f"{self.api_url}/webhooks/{webhook_id}",
                params={"api-key": self.api_key}
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error deleting webhook", error=str(e))
        return False
    
    async def list_webhooks(self) -> List[Dict]:
        """List all webhooks"""
        try:
            response = await self.client.get(
                f"{self.api_url}/webhooks",
                params={"api-key": self.api_key}
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Error listing webhooks", error=str(e))
        return []


class HeliusMonitor:
    """
    Real-time transaction monitor using Helius.
    Polls for new transactions and triggers callbacks.
    """
    
    def __init__(self, client: HeliusClient):
        self.client = client
        self.monitored_addresses: Dict[str, Dict] = {}
        self.callbacks: List[Callable] = []
        self.running = False
        self.poll_interval = 10  # seconds
        self.last_signatures: Dict[str, str] = {}
    
    def add_address(self, address: str, label: str = None):
        """Add an address to monitor"""
        self.monitored_addresses[address] = {
            "label": label or address[:8],
            "added_at": datetime.now().isoformat()
        }
        logger.info(f"Monitoring address: {address[:16]}...")
    
    def remove_address(self, address: str):
        """Remove an address from monitoring"""
        if address in self.monitored_addresses:
            del self.monitored_addresses[address]
            logger.info(f"Stopped monitoring: {address[:16]}...")
    
    def on_transaction(self, callback: Callable):
        """Register a callback for new transactions"""
        self.callbacks.append(callback)
    
    async def start(self):
        """Start monitoring"""
        self.running = True
        logger.info("Helius monitor started")
        
        while self.running:
            try:
                await self._poll_transactions()
                await asyncio.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"Monitor error", error=str(e))
                await asyncio.sleep(self.poll_interval)
    
    async def stop(self):
        """Stop monitoring"""
        self.running = False
        logger.info("Helius monitor stopped")
    
    async def _poll_transactions(self):
        """Poll for new transactions"""
        for address in list(self.monitored_addresses.keys()):
            try:
                signatures = await self.client.get_signatures(address, limit=10)
                
                if not signatures:
                    continue
                
                last_sig = self.last_signatures.get(address)
                new_txs = []
                
                for sig_info in signatures:
                    sig = sig_info.get("signature")
                    if sig == last_sig:
                        break
                    new_txs.append(sig_info)
                
                if signatures:
                    self.last_signatures[address] = signatures[0].get("signature")
                
                # Trigger callbacks for new transactions
                for tx in new_txs:
                    for callback in self.callbacks:
                        try:
                            await callback(address, tx)
                        except Exception as e:
                            logger.error(f"Callback error", error=str(e))
                            
            except Exception as e:
                logger.error(f"Error polling {address[:8]}", error=str(e))


# Singleton instances
_helius_client: Optional[HeliusClient] = None
_helius_monitor: Optional[HeliusMonitor] = None


def get_helius_client(api_key: str = None, network: str = "devnet") -> HeliusClient:
    """Get or create Helius client singleton"""
    global _helius_client
    if _helius_client is None:
        if not api_key:
            import os
            api_key = os.getenv("HELIUS_API_KEY")
        _helius_client = HeliusClient(api_key, network)
    return _helius_client


def get_helius_monitor(api_key: str = None, network: str = "devnet") -> HeliusMonitor:
    """Get or create Helius monitor singleton"""
    global _helius_monitor
    if _helius_monitor is None:
        client = get_helius_client(api_key, network)
        _helius_monitor = HeliusMonitor(client)
    return _helius_monitor
