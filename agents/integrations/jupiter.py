"""
Jupiter Integration - Risk-Aware DEX Aggregator

Complete integration with Jupiter for:
- Price and liquidity data
- Swap quotes with risk analysis
- Secure swap execution
- Transaction building
"""
import asyncio
import base64
from typing import Dict, List, Optional, Any
import httpx
import structlog

logger = structlog.get_logger()


class JupiterClient:
    """
    Client for Jupiter DEX aggregator.
    
    Features:
    - Swap quotes with price impact
    - Liquidity checking
    - Honeypot detection
    - Transaction building
    - Risk-aware execution
    """
    
    def __init__(self):
        self.api_url = "https://quote-api.jup.ag/v6"
        self.price_url = "https://price.jup.ag/v6"
        self.token_url = "https://token.jup.ag"
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Common token mints
        self.SOL_MINT = "So11111111111111111111111111111111111111112"
        self.USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        self.USDT_MINT = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
        
        # Cache
        self._price_cache: Dict[str, tuple] = {}  # mint -> (price, timestamp)
        self._token_list_cache: Optional[List[Dict]] = None
        
        logger.info("🪐 Jupiter client initialized")
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
    
    # =========================================================================
    # Price & Quote APIs
    # =========================================================================
    
    async def get_quote(
        self, 
        input_mint: str, 
        output_mint: str, 
        amount: int, 
        slippage_bps: int = 100,
        only_direct_routes: bool = False,
        as_legacy_transaction: bool = False,
        max_accounts: int = 64,
    ) -> Optional[Dict]:
        """
        Get a swap quote from Jupiter.
        
        Args:
            input_mint: Token to sell
            output_mint: Token to buy
            amount: Amount in smallest units (lamports for SOL)
            slippage_bps: Slippage tolerance in basis points (100 = 1%)
            only_direct_routes: Only use direct routes (faster, less optimal)
            as_legacy_transaction: Use legacy transaction format
            max_accounts: Maximum accounts in transaction
        
        Returns:
            Quote data including:
            - inputMint, outputMint
            - inAmount, outAmount
            - priceImpactPct
            - routePlan (swap route details)
            - otherAmountThreshold (minimum output with slippage)
        """
        try:
            params = {
                "inputMint": input_mint,
                "outputMint": output_mint,
                "amount": str(amount),
                "slippageBps": slippage_bps,
                "onlyDirectRoutes": str(only_direct_routes).lower(),
                "asLegacyTransaction": str(as_legacy_transaction).lower(),
                "maxAccounts": max_accounts,
            }
            
            response = await self.client.get(
                f"{self.api_url}/quote",
                params=params
            )
            
            if response.status_code == 200:
                quote = response.json()
                logger.debug(f"Quote received", 
                           input=input_mint[:8], 
                           output=output_mint[:8],
                           impact=quote.get("priceImpactPct"))
                return quote
            else:
                logger.warning(f"Jupiter quote failed: {response.status_code}", 
                             body=response.text[:200])
                return None
                
        except Exception as e:
            logger.error(f"Error getting Jupiter quote", error=str(e))
            return None
    
    async def get_price(self, token_mint: str, vs_currency: str = "usd") -> Optional[float]:
        """
        Get token price in USD (or other currency).
        
        Uses Jupiter's price API which aggregates from multiple sources.
        """
        try:
            # Check cache (valid for 30 seconds)
            import time
            now = time.time()
            if token_mint in self._price_cache:
                cached_price, cached_time = self._price_cache[token_mint]
                if now - cached_time < 30:
                    return cached_price
            
            response = await self.client.get(
                f"{self.price_url}/price",
                params={"ids": token_mint}
            )
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and token_mint in data["data"]:
                    price = data["data"][token_mint].get("price")
                    if price:
                        self._price_cache[token_mint] = (price, now)
                        return price
            return None
            
        except Exception as e:
            logger.error(f"Error getting price", error=str(e))
            return None
    
    async def get_prices(self, token_mints: List[str]) -> Dict[str, float]:
        """Get prices for multiple tokens at once"""
        try:
            response = await self.client.get(
                f"{self.price_url}/price",
                params={"ids": ",".join(token_mints)}
            )
            
            if response.status_code == 200:
                data = response.json()
                prices = {}
                if "data" in data:
                    for mint, info in data["data"].items():
                        if "price" in info:
                            prices[mint] = info["price"]
                return prices
            return {}
            
        except Exception as e:
            logger.error(f"Error getting prices", error=str(e))
            return {}
    
    # =========================================================================
    # Liquidity & Risk Analysis
    # =========================================================================
    
    async def check_liquidity(self, token_mint: str) -> Dict:
        """
        Comprehensive liquidity check for a token.
        
        Tests both buy and sell directions to detect honeypots.
        
        Returns:
            {
                "mint": str,
                "has_liquidity": bool,
                "can_buy": bool,
                "can_sell": bool,
                "estimated_liquidity_usd": float,
                "price_impact_buy": float,
                "price_impact_sell": float,
                "is_honeypot": bool,
                "buy_quote": dict | None,
                "sell_quote": dict | None,
            }
        """
        result = {
            "mint": token_mint,
            "has_liquidity": False,
            "can_buy": False,
            "can_sell": False,
            "estimated_liquidity_usd": 0,
            "price_impact_buy": None,
            "price_impact_sell": None,
            "is_honeypot": False,
            "buy_quote": None,
            "sell_quote": None,
        }
        
        # Test 1: Can we BUY this token? (SOL -> Token)
        buy_quote = await self.get_quote(
            self.SOL_MINT,
            token_mint,
            1_000_000_000,  # 1 SOL
            500  # 5% slippage (generous for testing)
        )
        
        if buy_quote:
            result["can_buy"] = True
            result["has_liquidity"] = True
            result["buy_quote"] = buy_quote
            
            # Parse price impact
            impact = buy_quote.get("priceImpactPct")
            if impact:
                try:
                    result["price_impact_buy"] = float(impact) * 100  # Convert to percentage
                except:
                    result["price_impact_buy"] = 0
        
        # Test 2: Can we SELL this token? (Token -> SOL)
        # First we need to know how much token we'd get from the buy
        if buy_quote and buy_quote.get("outAmount"):
            sell_amount = int(int(buy_quote["outAmount"]) * 0.9)  # 90% of what we'd buy
            
            sell_quote = await self.get_quote(
                token_mint,
                self.SOL_MINT,
                sell_amount,
                500  # 5% slippage
            )
            
            if sell_quote:
                result["can_sell"] = True
                result["sell_quote"] = sell_quote
                
                impact = sell_quote.get("priceImpactPct")
                if impact:
                    try:
                        result["price_impact_sell"] = float(impact) * 100
                    except:
                        result["price_impact_sell"] = 0
        
        # HONEYPOT DETECTION: Can buy but can't sell
        if result["can_buy"] and not result["can_sell"]:
            result["is_honeypot"] = True
            logger.warning(f"🚨 HONEYPOT DETECTED: {token_mint[:16]}...")
        
        # Estimate liquidity based on price impact
        if result["price_impact_buy"] is not None:
            impact = abs(result["price_impact_buy"])
            if impact < 1:
                result["estimated_liquidity_usd"] = 100000  # $100k+
            elif impact < 5:
                result["estimated_liquidity_usd"] = 10000   # $10k+
            elif impact < 20:
                result["estimated_liquidity_usd"] = 1000    # $1k+
            else:
                result["estimated_liquidity_usd"] = 100     # Very low
        
        return result
    
    async def is_token_tradeable(self, token_mint: str) -> bool:
        """Quick check if a token has any liquidity on Jupiter"""
        quote = await self.get_quote(
            self.SOL_MINT,
            token_mint,
            100_000_000,  # 0.1 SOL
            1000  # 10% slippage (very generous)
        )
        return quote is not None
    
    # =========================================================================
    # Swap Execution
    # =========================================================================
    
    async def get_swap_transaction(
        self,
        quote: Dict,
        user_public_key: str,
        wrap_unwrap_sol: bool = True,
        fee_account: Optional[str] = None,
        compute_unit_price_micro_lamports: Optional[int] = None,
        priority_level: str = "medium",
    ) -> Optional[Dict]:
        """
        Get a swap transaction from a quote.
        
        Args:
            quote: Quote object from get_quote()
            user_public_key: User's wallet public key
            wrap_unwrap_sol: Auto wrap/unwrap SOL
            fee_account: Optional fee account for referral
            compute_unit_price_micro_lamports: Priority fee
            priority_level: "min", "low", "medium", "high", "veryHigh"
        
        Returns:
            {
                "swapTransaction": str (base64 encoded),
                "lastValidBlockHeight": int,
                "prioritizationFeeLamports": int,
            }
        """
        try:
            body = {
                "quoteResponse": quote,
                "userPublicKey": user_public_key,
                "wrapAndUnwrapSol": wrap_unwrap_sol,
                "dynamicComputeUnitLimit": True,
                "prioritizationFeeLamports": {
                    "priorityLevelWithMaxLamports": {
                        "maxLamports": 10000000,  # Max 0.01 SOL priority fee
                        "priorityLevel": priority_level,
                    }
                }
            }
            
            if fee_account:
                body["feeAccount"] = fee_account
            
            if compute_unit_price_micro_lamports:
                body["computeUnitPriceMicroLamports"] = compute_unit_price_micro_lamports
            
            response = await self.client.post(
                f"{self.api_url}/swap",
                json=body
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Swap transaction failed: {response.status_code}",
                           body=response.text[:500])
                return None
                
        except Exception as e:
            logger.error(f"Error getting swap transaction", error=str(e))
            return None
    
    async def execute_swap(
        self,
        input_mint: str,
        output_mint: str,
        amount: int,
        user_public_key: str,
        slippage_bps: int = 100,
        priority_level: str = "medium",
    ) -> Dict[str, Any]:
        """
        Complete swap flow: quote -> transaction.
        
        Returns transaction ready for signing, NOT signed/submitted.
        User must sign and submit separately for security.
        
        Returns:
            {
                "success": bool,
                "quote": dict | None,
                "transaction": str | None (base64),
                "expected_output": int,
                "minimum_output": int,
                "price_impact_pct": float,
                "error": str | None,
            }
        """
        result = {
            "success": False,
            "quote": None,
            "transaction": None,
            "expected_output": 0,
            "minimum_output": 0,
            "price_impact_pct": 0,
            "error": None,
        }
        
        # Step 1: Get quote
        quote = await self.get_quote(
            input_mint,
            output_mint,
            amount,
            slippage_bps
        )
        
        if not quote:
            result["error"] = "Failed to get quote - token may not be tradeable"
            return result
        
        result["quote"] = quote
        result["expected_output"] = int(quote.get("outAmount", 0))
        result["minimum_output"] = int(quote.get("otherAmountThreshold", 0))
        
        try:
            result["price_impact_pct"] = float(quote.get("priceImpactPct", 0)) * 100
        except:
            pass
        
        # Step 2: Get swap transaction
        swap_result = await self.get_swap_transaction(
            quote,
            user_public_key,
            priority_level=priority_level
        )
        
        if not swap_result:
            result["error"] = "Failed to build swap transaction"
            return result
        
        result["transaction"] = swap_result.get("swapTransaction")
        result["success"] = True
        
        return result
    
    # =========================================================================
    # Token Information
    # =========================================================================
    
    async def get_token_list(self) -> List[Dict]:
        """Get list of all tokens known to Jupiter"""
        try:
            if self._token_list_cache:
                return self._token_list_cache
            
            response = await self.client.get(f"{self.token_url}/all")
            
            if response.status_code == 200:
                self._token_list_cache = response.json()
                return self._token_list_cache
                
        except Exception as e:
            logger.error(f"Error getting token list", error=str(e))
        
        return []
    
    async def get_token_info(self, mint: str) -> Optional[Dict]:
        """Get info for a specific token"""
        try:
            response = await self.client.get(f"{self.token_url}/strict")
            
            if response.status_code == 200:
                tokens = response.json()
                for token in tokens:
                    if token.get("address") == mint:
                        return token
        except Exception as e:
            logger.error(f"Error getting token info", error=str(e))
        
        return None
    
    async def search_token(self, query: str) -> List[Dict]:
        """Search for tokens by name or symbol"""
        tokens = await self.get_token_list()
        query_lower = query.lower()
        
        matches = []
        for token in tokens:
            name = token.get("name", "").lower()
            symbol = token.get("symbol", "").lower()
            
            if query_lower in name or query_lower in symbol:
                matches.append(token)
                if len(matches) >= 20:
                    break
        
        return matches


# =========================================================================
# Risk-Aware Swap Functions
# =========================================================================

async def safe_swap(
    input_mint: str,
    output_mint: str,
    amount_lamports: int,
    user_wallet: str,
    max_slippage_bps: int = 100,
) -> Dict[str, Any]:
    """
    Execute a risk-aware swap with automatic protection.
    
    This function:
    1. Checks token for honeypot/scam indicators
    2. Verifies liquidity is sufficient
    3. Adjusts slippage based on liquidity
    4. Returns transaction for user to sign
    
    Args:
        input_mint: Token to sell
        output_mint: Token to buy
        amount_lamports: Amount in lamports
        user_wallet: User's public key
        max_slippage_bps: Maximum slippage user will accept
    
    Returns:
        {
            "safe": bool,
            "risk_level": str,
            "warnings": list,
            "transaction": str | None,
            "quote": dict | None,
            "recommended_slippage": int,
            "error": str | None,
        }
    """
    jupiter = get_jupiter_client()
    
    result = {
        "safe": False,
        "risk_level": "unknown",
        "warnings": [],
        "transaction": None,
        "quote": None,
        "recommended_slippage": max_slippage_bps,
        "error": None,
    }
    
    # Step 1: Check liquidity and honeypot
    liquidity = await jupiter.check_liquidity(output_mint)
    
    if liquidity.get("is_honeypot"):
        result["risk_level"] = "critical"
        result["warnings"].append("🚨 HONEYPOT DETECTED - Cannot sell this token!")
        result["error"] = "Token is a honeypot - swap blocked"
        return result
    
    if not liquidity.get("has_liquidity"):
        result["risk_level"] = "critical"
        result["warnings"].append("❌ No liquidity found for this token")
        result["error"] = "Token has no liquidity"
        return result
    
    # Step 2: Assess risk level
    estimated_liq = liquidity.get("estimated_liquidity_usd", 0)
    price_impact = liquidity.get("price_impact_buy", 0) or 0
    
    if estimated_liq >= 100000 and price_impact < 1:
        result["risk_level"] = "safe"
    elif estimated_liq >= 10000 and price_impact < 5:
        result["risk_level"] = "low"
        result["warnings"].append(f"⚠️ Moderate liquidity: ${estimated_liq:,.0f}")
    elif estimated_liq >= 1000:
        result["risk_level"] = "medium"
        result["warnings"].append(f"⚠️ Low liquidity: ${estimated_liq:,.0f}")
        result["recommended_slippage"] = max(max_slippage_bps, 200)
    else:
        result["risk_level"] = "high"
        result["warnings"].append(f"⚠️ Very low liquidity: ${estimated_liq:,.0f}")
        result["warnings"].append(f"⚠️ High price impact: {price_impact:.1f}%")
        result["recommended_slippage"] = max(max_slippage_bps, 500)
    
    # Step 3: Execute swap with appropriate slippage
    swap_result = await jupiter.execute_swap(
        input_mint,
        output_mint,
        amount_lamports,
        user_wallet,
        result["recommended_slippage"]
    )
    
    if swap_result.get("success"):
        result["safe"] = True
        result["transaction"] = swap_result.get("transaction")
        result["quote"] = swap_result.get("quote")
    else:
        result["error"] = swap_result.get("error", "Swap failed")
    
    return result


# =========================================================================
# Singleton
# =========================================================================

_jupiter_client: Optional[JupiterClient] = None


def get_jupiter_client() -> JupiterClient:
    """Get or create Jupiter client singleton"""
    global _jupiter_client
    if _jupiter_client is None:
        _jupiter_client = JupiterClient()
    return _jupiter_client


async def close_jupiter_client():
    """Close the Jupiter client"""
    global _jupiter_client
    if _jupiter_client:
        await _jupiter_client.close()
        _jupiter_client = None
