"""
Fallback RPC System - Redundant Solana connections

Provides multiple RPC endpoints for reliability:
1. Primary: Helius (best performance)
2. Fallback 1: QuickNode
3. Fallback 2: Public RPC
4. Fallback 3: Alchemy
"""
import asyncio
import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import httpx
import structlog

logger = structlog.get_logger()


@dataclass
class RPCEndpoint:
    """Represents an RPC endpoint"""
    name: str
    url: str
    priority: int
    healthy: bool = True
    last_error: Optional[str] = None
    latency_ms: float = 0
    requests_made: int = 0
    errors: int = 0


class FallbackRPCClient:
    """
    RPC client with automatic fallback to backup endpoints.
    Ensures system availability even if primary RPC fails.
    """
    
    def __init__(self, helius_api_key: str = None):
        self.endpoints: List[RPCEndpoint] = []
        self.current_endpoint_index = 0
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Initialize endpoints
        self._setup_endpoints(helius_api_key)
        
        logger.info(f"FallbackRPC initialized with {len(self.endpoints)} endpoints")
    
    def _setup_endpoints(self, helius_api_key: str = None):
        """Setup RPC endpoints in priority order"""
        
        # Primary: Helius (if API key provided)
        if helius_api_key:
            self.endpoints.append(RPCEndpoint(
                name="Helius",
                url=f"https://devnet.helius-rpc.com/?api-key={helius_api_key}",
                priority=1
            ))
        
        # Fallback 1: Public devnet RPC
        self.endpoints.append(RPCEndpoint(
            name="Solana Public",
            url="https://api.devnet.solana.com",
            priority=2
        ))
        
        # Fallback 2: Another public endpoint
        self.endpoints.append(RPCEndpoint(
            name="Solana Public 2",
            url="https://devnet.solana.com",
            priority=3
        ))
        
        # Sort by priority
        self.endpoints.sort(key=lambda x: x.priority)
    
    @property
    def current_endpoint(self) -> RPCEndpoint:
        """Get current active endpoint"""
        return self.endpoints[self.current_endpoint_index]
    
    async def _make_request(self, endpoint: RPCEndpoint, payload: Dict) -> Optional[Dict]:
        """Make a request to a specific endpoint"""
        try:
            import time
            start = time.time()
            
            response = await self.client.post(
                endpoint.url,
                json=payload,
                timeout=10.0
            )
            
            latency = (time.time() - start) * 1000
            endpoint.latency_ms = latency
            endpoint.requests_made += 1
            
            if response.status_code == 200:
                endpoint.healthy = True
                endpoint.last_error = None
                return response.json()
            else:
                endpoint.errors += 1
                endpoint.last_error = f"HTTP {response.status_code}"
                return None
                
        except Exception as e:
            endpoint.errors += 1
            endpoint.last_error = str(e)
            endpoint.healthy = False
            logger.warning(f"RPC error on {endpoint.name}", error=str(e))
            return None
    
    async def request(self, method: str, params: List = None) -> Optional[Dict]:
        """
        Make an RPC request with automatic fallback.
        Tries each endpoint in priority order until one succeeds.
        """
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or []
        }
        
        # Try current endpoint first
        result = await self._make_request(self.current_endpoint, payload)
        if result and "result" in result:
            return result
        
        # Fallback to other endpoints
        for i, endpoint in enumerate(self.endpoints):
            if i == self.current_endpoint_index:
                continue
            
            logger.info(f"Falling back to {endpoint.name}")
            result = await self._make_request(endpoint, payload)
            
            if result and "result" in result:
                # Switch to this endpoint as primary
                self.current_endpoint_index = i
                logger.info(f"Switched primary RPC to {endpoint.name}")
                return result
        
        # All endpoints failed
        logger.error("All RPC endpoints failed")
        return None
    
    async def get_balance(self, address: str) -> float:
        """Get SOL balance for an address"""
        result = await self.request("getBalance", [address])
        if result and "result" in result:
            return result["result"]["value"] / 1_000_000_000
        return 0
    
    async def get_slot(self) -> int:
        """Get current slot"""
        result = await self.request("getSlot")
        if result and "result" in result:
            return result["result"]
        return 0
    
    async def get_recent_blockhash(self) -> Optional[str]:
        """Get recent blockhash"""
        result = await self.request("getLatestBlockhash")
        if result and "result" in result:
            return result["result"]["value"]["blockhash"]
        return None
    
    async def health_check(self) -> Dict:
        """Check health of all endpoints"""
        results = {}
        
        for endpoint in self.endpoints:
            try:
                result = await self._make_request(endpoint, {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getHealth"
                })
                
                results[endpoint.name] = {
                    "healthy": endpoint.healthy,
                    "latency_ms": endpoint.latency_ms,
                    "requests": endpoint.requests_made,
                    "errors": endpoint.errors
                }
            except:
                results[endpoint.name] = {"healthy": False}
        
        return results
    
    def get_status(self) -> Dict:
        """Get current RPC status"""
        return {
            "current_endpoint": self.current_endpoint.name,
            "endpoints": [
                {
                    "name": e.name,
                    "healthy": e.healthy,
                    "latency_ms": e.latency_ms,
                    "error_rate": e.errors / max(e.requests_made, 1)
                }
                for e in self.endpoints
            ]
        }
    
    async def close(self):
        """Close the client"""
        await self.client.aclose()


# Singleton instance
_fallback_client: Optional[FallbackRPCClient] = None


def get_fallback_rpc(helius_api_key: str = None) -> FallbackRPCClient:
    """Get or create fallback RPC client"""
    global _fallback_client
    if _fallback_client is None:
        if not helius_api_key:
            helius_api_key = os.getenv("HELIUS_API_KEY")
        _fallback_client = FallbackRPCClient(helius_api_key)
    return _fallback_client
