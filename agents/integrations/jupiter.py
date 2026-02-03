"""
Jupiter Integration - DEX aggregator for price and liquidity data
"""
import asyncio
from typing import Dict, List, Optional
import httpx
import structlog

logger = structlog.get_logger()


class JupiterClient:
    """
    Client for Jupiter DEX aggregator.
    Used for checking token liquidity and price data.
    """
    
    def __init__(self):
        self.api_url = "https://quote-api.jup.ag/v6"
        self.price_url = "https://price.jup.ag/v6"
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Common token mints
        self.SOL_MINT = "So11111111111111111111111111111111111111112"
        self.USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        
        logger.info("Jupiter client initialized")
    
    async def close(self):
        await self.client.aclose()
    
    async def get_quote(self, input_mint: str, output_mint: str, 
                       amount: int, slippage_bps: int = 100) -> Optional[Dict]:
        """
        Get a swap quote.
        
        Args:
            input_mint: Token to sell
            output_mint: Token to buy
            amount: Amount in smallest units
            slippage_bps: Slippage in basis points (100 = 1%)
        
        Returns:
            Quote data including output amount and price impact
        """
        try:
            response = await self.client.get(
                f"{self.api_url}/quote",
                params={
                    "inputMint": input_mint,
                    "outputMint": output_mint,
                    "amount": str(amount),
                    "slippageBps": slippage_bps
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Jupiter quote failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting Jupiter quote", error=str(e))
            return None
    
    async def get_price(self, token_mint: str) -> Optional[float]:
        """Get token price in USD"""
        try:
            response = await self.client.get(
                f"{self.price_url}/price",
                params={"ids": token_mint}
            )
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and token_mint in data["data"]:
                    return data["data"][token_mint].get("price")
            return None
            
        except Exception as e:
            logger.error(f"Error getting price", error=str(e))
            return None
    
    async def check_liquidity(self, token_mint: str) -> Dict:
        """
        Check token liquidity by attempting quotes.
        Returns liquidity assessment.
        """
        result = {
            "mint": token_mint,
            "has_liquidity": False,
            "can_buy": False,
            "can_sell": False,
            "estimated_liquidity_usd": 0,
            "price_impact_buy": None,
            "price_impact_sell": None,
            "is_honeypot": False
        }
        
        # Try to get a buy quote (SOL -> Token)
        buy_quote = await self.get_quote(
            self.SOL_MINT,
            token_mint,
            1_000_000_000,  # 1 SOL
            500  # 5% slippage
        )
        
        if buy_quote:
            result["can_buy"] = True
            result["has_liquidity"] = True
            result["price_impact_buy"] = buy_quote.get("priceImpactPct", 0)
        
        # Try to get a sell quote (Token -> SOL)
        sell_quote = await self.get_quote(
            token_mint,
            self.SOL_MINT,
            1_000_000,  # Small amount
            500
        )
        
        if sell_quote:
            result["can_sell"] = True
            result["price_impact_sell"] = sell_quote.get("priceImpactPct", 0)
        else:
            # Can buy but can't sell = potential honeypot
            if result["can_buy"]:
                result["is_honeypot"] = True
        
        # Estimate liquidity based on price impact
        if result["price_impact_buy"] is not None:
            # Lower price impact = higher liquidity
            impact = abs(float(result["price_impact_buy"]))
            if impact < 1:
                result["estimated_liquidity_usd"] = 100000  # $100k+
            elif impact < 5:
                result["estimated_liquidity_usd"] = 10000   # $10k+
            elif impact < 20:
                result["estimated_liquidity_usd"] = 1000    # $1k+
            else:
                result["estimated_liquidity_usd"] = 100     # Very low
        
        return result
    
    async def get_token_list(self) -> List[Dict]:
        """Get list of all tokens known to Jupiter"""
        try:
            response = await self.client.get(
                "https://token.jup.ag/all"
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Error getting token list", error=str(e))
        return []
    
    async def is_token_tradeable(self, token_mint: str) -> bool:
        """Check if a token is tradeable on Jupiter"""
        quote = await self.get_quote(
            self.SOL_MINT,
            token_mint,
            100_000_000,  # 0.1 SOL
            1000  # 10% slippage (generous)
        )
        return quote is not None


# Singleton instance
_jupiter_client: Optional[JupiterClient] = None


def get_jupiter_client() -> JupiterClient:
    """Get or create Jupiter client singleton"""
    global _jupiter_client
    if _jupiter_client is None:
        _jupiter_client = JupiterClient()
    return _jupiter_client
