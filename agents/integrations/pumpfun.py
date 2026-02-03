"""
GUARDIAN Pump.fun Integration - Real-time token monitoring
Production-ready implementation with proper error handling
"""
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import structlog

logger = structlog.get_logger()


class PumpFunClient:
    """Production pump.fun API client"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.base_url = "https://frontend-api.pump.fun"
        self.cache: Dict[str, Any] = {}
        self.cache_ttl = 60  # seconds
    
    async def close(self):
        await self.client.aclose()
    
    async def get_coins(self, limit: int = 50, offset: int = 0, sort: str = "created_timestamp", order: str = "DESC") -> List[Dict]:
        """Fetch coins from pump.fun API"""
        cache_key = f"coins_{limit}_{offset}_{sort}_{order}"
        
        # Check cache
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if (datetime.now() - cached["time"]).seconds < self.cache_ttl:
                return cached["data"]
        
        try:
            response = await self.client.get(
                f"{self.base_url}/coins",
                params={
                    "offset": offset,
                    "limit": limit,
                    "sort": sort,
                    "order": order,
                    "includeNsfw": "false"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.cache[cache_key] = {"data": data, "time": datetime.now()}
                return data
            else:
                logger.warning(f"Pump.fun API returned {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Pump.fun API error: {e}")
            return []
    
    async def get_coin(self, mint: str) -> Optional[Dict]:
        """Get single coin details"""
        try:
            response = await self.client.get(f"{self.base_url}/coins/{mint}")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch coin {mint}: {e}")
        return None
    
    async def get_trades(self, mint: str, limit: int = 50) -> List[Dict]:
        """Get recent trades for a coin"""
        try:
            response = await self.client.get(
                f"{self.base_url}/trades/{mint}",
                params={"limit": limit}
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch trades: {e}")
        return []


class TokenAnalyzer:
    """Analyzes pump.fun tokens for risk factors"""
    
    # Risk weights
    WEIGHTS = {
        "no_socials": 25,
        "very_new": 20,
        "low_mcap": 15,
        "low_engagement": 10,
        "suspicious_name": 10,
        "high_concentration": 20,
    }
    
    # Suspicious keywords in token names
    SUSPICIOUS_KEYWORDS = [
        "elon", "trump", "musk", "safe", "moon", "100x", "1000x",
        "gem", "next", "baby", "mini", "inu", "shib", "doge"
    ]
    
    def analyze(self, token: Dict) -> Dict[str, Any]:
        """Comprehensive token risk analysis"""
        result = {
            "mint": token.get("mint"),
            "name": token.get("name", "Unknown"),
            "symbol": token.get("symbol", "???"),
            "image": token.get("image_uri"),
            "risk_score": 0,
            "risk_factors": [],
            "warnings": [],
            "recommendation": "UNKNOWN",
            "metrics": {}
        }
        
        # 1. Market cap analysis
        mcap = token.get("usd_market_cap", 0) or 0
        result["metrics"]["market_cap"] = mcap
        
        if mcap < 1000:
            result["risk_score"] += self.WEIGHTS["low_mcap"]
            result["risk_factors"].append("MICRO_CAP")
            result["warnings"].append("Market cap under $1,000")
        elif mcap < 10000:
            result["risk_score"] += self.WEIGHTS["low_mcap"] // 2
            result["warnings"].append("Low market cap")
        
        # 2. Social presence
        has_twitter = bool(token.get("twitter"))
        has_telegram = bool(token.get("telegram"))
        has_website = bool(token.get("website"))
        
        result["metrics"]["has_twitter"] = has_twitter
        result["metrics"]["has_telegram"] = has_telegram
        result["metrics"]["has_website"] = has_website
        
        if not any([has_twitter, has_telegram, has_website]):
            result["risk_score"] += self.WEIGHTS["no_socials"]
            result["risk_factors"].append("NO_SOCIALS")
            result["warnings"].append("No social media presence")
        
        # 3. Token age
        created = token.get("created_timestamp")
        if created:
            try:
                if isinstance(created, (int, float)):
                    created_time = datetime.fromtimestamp(created / 1000 if created > 1e12 else created)
                else:
                    created_time = datetime.now()
                
                age_hours = (datetime.now() - created_time).total_seconds() / 3600
                result["metrics"]["age_hours"] = round(age_hours, 2)
                
                if age_hours < 1:
                    result["risk_score"] += self.WEIGHTS["very_new"]
                    result["risk_factors"].append("VERY_NEW")
                    result["warnings"].append("Created less than 1 hour ago")
                elif age_hours < 6:
                    result["risk_score"] += self.WEIGHTS["very_new"] // 2
                    result["warnings"].append("Token is less than 6 hours old")
            except:
                result["metrics"]["age_hours"] = None
        
        # 4. Community engagement
        reply_count = token.get("reply_count", 0) or 0
        result["metrics"]["reply_count"] = reply_count
        
        if reply_count < 5:
            result["risk_score"] += self.WEIGHTS["low_engagement"]
            result["risk_factors"].append("LOW_ENGAGEMENT")
        
        # 5. Name analysis
        name_lower = (token.get("name") or "").lower()
        symbol_lower = (token.get("symbol") or "").lower()
        
        for keyword in self.SUSPICIOUS_KEYWORDS:
            if keyword in name_lower or keyword in symbol_lower:
                result["risk_score"] += self.WEIGHTS["suspicious_name"]
                result["risk_factors"].append("SUSPICIOUS_NAME")
                result["warnings"].append(f"Name contains '{keyword}'")
                break
        
        # 6. King of the hill status (positive signal)
        if token.get("king_of_the_hill_timestamp"):
            result["risk_score"] = max(0, result["risk_score"] - 10)
            result["metrics"]["is_trending"] = True
        else:
            result["metrics"]["is_trending"] = False
        
        # Calculate recommendation
        score = result["risk_score"]
        if score >= 70:
            result["recommendation"] = "AVOID"
        elif score >= 50:
            result["recommendation"] = "HIGH_RISK"
        elif score >= 30:
            result["recommendation"] = "CAUTION"
        else:
            result["recommendation"] = "LOW_RISK"
        
        return result


class PumpFunMonitor:
    """Main pump.fun monitoring service"""
    
    def __init__(self):
        self.client = PumpFunClient()
        self.analyzer = TokenAnalyzer()
        self.last_scan: Optional[datetime] = None
        self.scan_results: List[Dict] = []
    
    async def scan_new_tokens(self, limit: int = 30) -> List[Dict]:
        """Scan and analyze new tokens"""
        tokens = await self.client.get_coins(limit=limit, sort="created_timestamp", order="DESC")
        
        results = []
        for token in tokens:
            analysis = self.analyzer.analyze(token)
            results.append(analysis)
        
        # Sort by risk score descending
        results.sort(key=lambda x: x["risk_score"], reverse=True)
        
        self.last_scan = datetime.now()
        self.scan_results = results
        
        return results
    
    async def scan_trending(self, limit: int = 20) -> List[Dict]:
        """Get trending/popular tokens"""
        tokens = await self.client.get_coins(limit=limit, sort="market_cap", order="DESC")
        
        results = []
        for token in tokens:
            analysis = self.analyzer.analyze(token)
            results.append(analysis)
        
        return results
    
    async def analyze_token(self, mint: str) -> Optional[Dict]:
        """Deep analysis of a specific token"""
        token = await self.client.get_coin(mint)
        if not token:
            return None
        
        analysis = self.analyzer.analyze(token)
        
        # Get trade history for additional analysis
        trades = await self.client.get_trades(mint, limit=100)
        if trades:
            # Analyze trading patterns
            buy_count = sum(1 for t in trades if t.get("is_buy"))
            sell_count = len(trades) - buy_count
            
            analysis["metrics"]["recent_buys"] = buy_count
            analysis["metrics"]["recent_sells"] = sell_count
            analysis["metrics"]["buy_ratio"] = round(buy_count / len(trades) * 100, 1) if trades else 0
            
            # Heavy selling is a warning sign
            if sell_count > buy_count * 2:
                analysis["risk_score"] += 15
                analysis["risk_factors"].append("HEAVY_SELLING")
                analysis["warnings"].append("High sell pressure detected")
        
        return analysis
    
    async def close(self):
        await self.client.close()


# Singleton
_monitor: Optional[PumpFunMonitor] = None

def get_pumpfun_monitor() -> PumpFunMonitor:
    global _monitor
    if _monitor is None:
        _monitor = PumpFunMonitor()
    return _monitor
