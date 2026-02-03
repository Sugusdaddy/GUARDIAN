"""
GUARDIAN Solana Scanner - Real token and contract analysis
Fetches live data from Solana for threat detection
"""
import asyncio
import httpx
from datetime import datetime
from typing import Dict, List, Optional, Any
import structlog

logger = structlog.get_logger()

# Known scam patterns and signatures
SCAM_SIGNATURES = {
    "honeypot_functions": [
        "setMaxTxPercent",
        "setSwapEnabled", 
        "blacklistAddress",
        "setTradingEnabled",
        "excludeFromFee"
    ],
    "drainer_functions": [
        "setApprovalForAll",
        "transferFrom",
        "safeTransferFrom"
    ],
    "rugpull_indicators": [
        "removeLiquidity",
        "withdrawAll",
        "emergencyWithdraw"
    ]
}

# Known scammer addresses (would be populated from intelligence feeds)
KNOWN_SCAMMERS = set()


class SolanaScanner:
    """
    Real-time Solana token and contract scanner.
    Uses multiple RPC endpoints and APIs for comprehensive analysis.
    """
    
    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com"):
        self.rpc_url = rpc_url
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Jupiter API for token info
        self.jupiter_url = "https://token.jup.ag"
        
        # Birdeye API for market data (if available)
        self.birdeye_url = "https://public-api.birdeye.so"
        
        logger.info("Solana scanner initialized")
    
    async def close(self):
        await self.client.aclose()
    
    async def get_token_info(self, mint: str) -> Optional[Dict]:
        """Get token metadata and info"""
        try:
            # Try Jupiter first
            response = await self.client.get(f"{self.jupiter_url}/all")
            if response.status_code == 200:
                tokens = response.json()
                for token in tokens:
                    if token.get("address") == mint:
                        return {
                            "name": token.get("name"),
                            "symbol": token.get("symbol"),
                            "decimals": token.get("decimals"),
                            "logo": token.get("logoURI"),
                            "tags": token.get("tags", []),
                            "verified": "verified" in token.get("tags", [])
                        }
        except Exception as e:
            logger.warning(f"Token info fetch failed", error=str(e))
        
        return None
    
    async def analyze_token(self, mint: str) -> Dict[str, Any]:
        """
        Comprehensive token analysis for risk assessment.
        Returns risk factors and score.
        """
        result = {
            "mint": mint,
            "risk_score": 0,
            "risk_factors": [],
            "warnings": [],
            "info": {},
            "analyzed_at": datetime.now().isoformat()
        }
        
        # 1. Check if known scammer
        if mint in KNOWN_SCAMMERS:
            result["risk_score"] = 100
            result["risk_factors"].append("KNOWN_SCAMMER")
            return result
        
        # 2. Get token info
        token_info = await self.get_token_info(mint)
        if token_info:
            result["info"] = token_info
            
            # Unverified tokens are riskier
            if not token_info.get("verified"):
                result["risk_score"] += 20
                result["warnings"].append("Token not verified on Jupiter")
        else:
            result["risk_score"] += 30
            result["warnings"].append("Token not found in registry")
        
        # 3. Check holder concentration (would need DAS API)
        # Placeholder for holder analysis
        
        # 4. Check liquidity (would need DEX API)
        # Placeholder for liquidity analysis
        
        # 5. Check age
        # Newer tokens are riskier
        
        return result
    
    async def analyze_transaction(self, signature: str) -> Dict[str, Any]:
        """Analyze a transaction for suspicious activity"""
        result = {
            "signature": signature,
            "risk_score": 0,
            "risk_factors": [],
            "details": {}
        }
        
        try:
            # Get transaction
            response = await self.client.post(
                self.rpc_url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getTransaction",
                    "params": [signature, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                tx = data.get("result")
                
                if tx:
                    result["details"]["slot"] = tx.get("slot")
                    result["details"]["fee"] = tx.get("meta", {}).get("fee")
                    
                    # Check for suspicious instructions
                    instructions = tx.get("transaction", {}).get("message", {}).get("instructions", [])
                    
                    for ix in instructions:
                        program = ix.get("program")
                        parsed = ix.get("parsed", {})
                        
                        # Check for token approvals
                        if parsed.get("type") == "approve":
                            result["risk_factors"].append("TOKEN_APPROVAL")
                            result["risk_score"] += 30
                        
                        # Check for large transfers
                        if parsed.get("type") == "transfer":
                            amount = parsed.get("info", {}).get("lamports", 0)
                            if amount > 1_000_000_000_000:  # > 1000 SOL
                                result["risk_factors"].append("LARGE_TRANSFER")
                                result["risk_score"] += 20
        
        except Exception as e:
            logger.error(f"Transaction analysis failed", error=str(e))
        
        return result
    
    async def check_address(self, address: str) -> Dict[str, Any]:
        """Check an address for suspicious activity patterns"""
        result = {
            "address": address,
            "risk_score": 0,
            "risk_factors": [],
            "activity": {},
            "recommendation": "UNKNOWN"
        }
        
        # Check blacklist
        if address in KNOWN_SCAMMERS:
            result["risk_score"] = 100
            result["risk_factors"].append("KNOWN_SCAMMER")
            result["recommendation"] = "BLOCK"
            return result
        
        try:
            # Get recent transactions
            response = await self.client.post(
                self.rpc_url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getSignaturesForAddress",
                    "params": [address, {"limit": 20}]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                signatures = data.get("result", [])
                
                result["activity"]["recent_txs"] = len(signatures)
                
                # Check patterns
                if len(signatures) > 15:
                    result["risk_factors"].append("HIGH_ACTIVITY")
                    result["risk_score"] += 10
                
                # Check for recent creation (all txs in last hour)
                if signatures:
                    first_tx_time = signatures[-1].get("blockTime", 0)
                    if first_tx_time > 0:
                        age_hours = (datetime.now().timestamp() - first_tx_time) / 3600
                        if age_hours < 24:
                            result["risk_factors"].append("NEW_ADDRESS")
                            result["risk_score"] += 20
        
        except Exception as e:
            logger.error(f"Address check failed", error=str(e))
        
        # Set recommendation
        if result["risk_score"] >= 70:
            result["recommendation"] = "BLOCK"
        elif result["risk_score"] >= 40:
            result["recommendation"] = "WARN"
        elif result["risk_score"] >= 20:
            result["recommendation"] = "MONITOR"
        else:
            result["recommendation"] = "SAFE"
        
        return result
    
    async def get_new_tokens(self, limit: int = 20) -> List[Dict]:
        """Get recently created tokens (potential scams)"""
        # Would integrate with pump.fun API, Raydium, etc.
        # Placeholder
        return []
    
    async def monitor_whale_wallets(self, wallets: List[str]) -> List[Dict]:
        """Monitor whale wallets for large movements"""
        alerts = []
        
        for wallet in wallets:
            try:
                response = await self.client.post(
                    self.rpc_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "getBalance",
                        "params": [wallet]
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    balance = data.get("result", {}).get("value", 0) / 1e9
                    
                    # Would compare to historical balance
                    # Alert on significant changes
                    
            except Exception as e:
                logger.warning(f"Whale monitor failed for {wallet[:16]}", error=str(e))
        
        return alerts


# Singleton
_scanner: Optional[SolanaScanner] = None

def get_scanner(rpc_url: str = None) -> SolanaScanner:
    global _scanner
    if _scanner is None:
        _scanner = SolanaScanner(rpc_url or "https://api.mainnet-beta.solana.com")
    return _scanner
