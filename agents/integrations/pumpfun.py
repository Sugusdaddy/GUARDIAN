"""
GUARDIAN Pump.fun Integration - Real-time new token monitoring
Detects rugs, honeypots, and scams as they launch
"""
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import structlog

logger = structlog.get_logger()


class PumpFunMonitor:
    """
    Monitor pump.fun for new token launches and detect scams.
    
    Scam indicators:
    - Dev holds >10% supply
    - No social links
    - Copy of existing token name
    - Instant large buys (insider)
    - Liquidity < $1000
    """
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.base_url = "https://frontend-api.pump.fun"
        self.known_scam_names = set()
        self.monitored_tokens: Dict[str, Dict] = {}
        
        # Thresholds
        self.MIN_LIQUIDITY_USD = 1000
        self.MAX_DEV_HOLDING_PCT = 10
        self.MIN_HOLDERS = 10
        self.SUSPICIOUS_EARLY_BUY_SOL = 5
        
        logger.info("Pump.fun monitor initialized")
    
    async def get_new_tokens(self, limit: int = 50) -> List[Dict]:
        """Get recently launched tokens"""
        try:
            response = await self.client.get(
                f"{self.base_url}/coins",
                params={"offset": 0, "limit": limit, "sort": "created_timestamp", "order": "DESC"}
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error("Failed to fetch new tokens", error=str(e))
        return []
    
    async def get_token_details(self, mint: str) -> Optional[Dict]:
        """Get detailed token info"""
        try:
            response = await self.client.get(f"{self.base_url}/coins/{mint}")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch token {mint[:16]}", error=str(e))
        return None
    
    async def analyze_token(self, token: Dict) -> Dict[str, Any]:
        """
        Comprehensive scam analysis for a pump.fun token.
        Returns risk assessment.
        """
        result = {
            "mint": token.get("mint"),
            "name": token.get("name"),
            "symbol": token.get("symbol"),
            "risk_score": 0,
            "risk_factors": [],
            "warnings": [],
            "recommendation": "UNKNOWN",
            "details": {}
        }
        
        # 1. Check market cap / liquidity
        market_cap = token.get("usd_market_cap", 0)
        if market_cap < self.MIN_LIQUIDITY_USD:
            result["risk_score"] += 25
            result["risk_factors"].append("LOW_LIQUIDITY")
            result["warnings"].append(f"Market cap only ${market_cap:.0f}")
        
        # 2. Check if dev wallet holds too much
        # Would need to analyze holder distribution
        
        # 3. Check social links
        has_twitter = bool(token.get("twitter"))
        has_telegram = bool(token.get("telegram"))
        has_website = bool(token.get("website"))
        
        if not any([has_twitter, has_telegram, has_website]):
            result["risk_score"] += 30
            result["risk_factors"].append("NO_SOCIALS")
            result["warnings"].append("No social media links")
        
        # 4. Check name for common scam patterns
        name = (token.get("name") or "").lower()
        symbol = (token.get("symbol") or "").lower()
        
        scam_keywords = ["elon", "trump", "pepe", "wojak", "doge", "shib", "safe", "moon", "inu", "baby"]
        if any(kw in name or kw in symbol for kw in scam_keywords):
            result["risk_score"] += 15
            result["warnings"].append("Name contains common scam keywords")
        
        # 5. Check age
        created = token.get("created_timestamp")
        if created:
            try:
                created_time = datetime.fromtimestamp(created / 1000)
                age_hours = (datetime.now() - created_time).total_seconds() / 3600
                result["details"]["age_hours"] = age_hours
                
                if age_hours < 1:
                    result["risk_score"] += 20
                    result["risk_factors"].append("VERY_NEW")
                    result["warnings"].append("Token created less than 1 hour ago")
            except:
                pass
        
        # 6. Check reply count (engagement)
        reply_count = token.get("reply_count", 0)
        if reply_count < 5:
            result["risk_score"] += 10
            result["warnings"].append("Low community engagement")
        
        # 7. Check if king of the hill
        is_koth = token.get("king_of_the_hill_timestamp") is not None
        if is_koth:
            result["risk_score"] -= 10  # Slightly less risky if popular
        
        # Calculate final recommendation
        if result["risk_score"] >= 70:
            result["recommendation"] = "AVOID"
        elif result["risk_score"] >= 50:
            result["recommendation"] = "HIGH_RISK"
        elif result["risk_score"] >= 30:
            result["recommendation"] = "CAUTION"
        else:
            result["recommendation"] = "MODERATE"
        
        result["details"]["market_cap"] = market_cap
        result["details"]["has_socials"] = any([has_twitter, has_telegram, has_website])
        result["details"]["reply_count"] = reply_count
        
        return result
    
    async def scan_new_launches(self) -> List[Dict]:
        """Scan recent launches and return high-risk tokens"""
        high_risk = []
        
        tokens = await self.get_new_tokens(limit=30)
        
        for token in tokens:
            analysis = await self.analyze_token(token)
            
            if analysis["risk_score"] >= 50:
                high_risk.append({
                    **analysis,
                    "image": token.get("image_uri"),
                    "created": token.get("created_timestamp")
                })
        
        return sorted(high_risk, key=lambda x: x["risk_score"], reverse=True)
    
    async def monitor_loop(self, callback=None, interval: int = 30):
        """Continuous monitoring loop"""
        logger.info("Starting pump.fun monitoring loop")
        
        while True:
            try:
                high_risk = await self.scan_new_launches()
                
                for token in high_risk:
                    mint = token["mint"]
                    
                    # Check if we've already alerted
                    if mint not in self.monitored_tokens:
                        self.monitored_tokens[mint] = {
                            "first_seen": datetime.now(),
                            "alerted": False
                        }
                        
                        if callback:
                            await callback(token)
                        
                        logger.warning(
                            "High-risk token detected",
                            name=token["name"],
                            symbol=token["symbol"],
                            risk=token["risk_score"]
                        )
                
                # Cleanup old entries
                cutoff = datetime.now() - timedelta(hours=24)
                self.monitored_tokens = {
                    k: v for k, v in self.monitored_tokens.items()
                    if v["first_seen"] > cutoff
                }
                
            except Exception as e:
                logger.error("Monitor loop error", error=str(e))
            
            await asyncio.sleep(interval)


class DexScreenerClient:
    """
    DexScreener integration for market data and pair analysis.
    """
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.base_url = "https://api.dexscreener.com/latest"
    
    async def get_token_pairs(self, token_address: str) -> List[Dict]:
        """Get trading pairs for a token"""
        try:
            response = await self.client.get(
                f"{self.base_url}/dex/tokens/{token_address}"
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("pairs", [])
        except Exception as e:
            logger.error(f"DexScreener fetch failed", error=str(e))
        return []
    
    async def analyze_liquidity(self, token_address: str) -> Dict:
        """Analyze token liquidity across DEXes"""
        pairs = await self.get_token_pairs(token_address)
        
        result = {
            "token": token_address,
            "total_liquidity_usd": 0,
            "total_volume_24h": 0,
            "pairs_count": len(pairs),
            "dexes": [],
            "risk_factors": []
        }
        
        for pair in pairs:
            liquidity = pair.get("liquidity", {}).get("usd", 0)
            volume = pair.get("volume", {}).get("h24", 0)
            
            result["total_liquidity_usd"] += liquidity or 0
            result["total_volume_24h"] += volume or 0
            result["dexes"].append(pair.get("dexId"))
        
        # Risk analysis
        if result["total_liquidity_usd"] < 5000:
            result["risk_factors"].append("VERY_LOW_LIQUIDITY")
        elif result["total_liquidity_usd"] < 50000:
            result["risk_factors"].append("LOW_LIQUIDITY")
        
        if result["pairs_count"] == 1:
            result["risk_factors"].append("SINGLE_PAIR")
        
        return result


# Singletons
_pumpfun: Optional[PumpFunMonitor] = None
_dexscreener: Optional[DexScreenerClient] = None

def get_pumpfun() -> PumpFunMonitor:
    global _pumpfun
    if _pumpfun is None:
        _pumpfun = PumpFunMonitor()
    return _pumpfun

def get_dexscreener() -> DexScreenerClient:
    global _dexscreener
    if _dexscreener is None:
        _dexscreener = DexScreenerClient()
    return _dexscreener
