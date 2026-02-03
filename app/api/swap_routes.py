"""
Swap API Routes - Risk-Aware DEX Trading

Endpoints for protected swap operations with automatic
risk analysis and honeypot detection.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import hashlib

# Import SwapGuard
import sys
sys.path.insert(0, ".")
from GUARDIAN.agents.specialized.swapguard_agent import (
    SwapGuardAgent,
    SwapRequest,
    SwapDecision,
    SwapAction,
    SwapRisk,
    TokenAnalysis,
    get_swapguard,
    evaluate_swap,
)
from agents.integrations.jupiter import get_jupiter_client, safe_swap


router = APIRouter(prefix="/api/swap", tags=["swap"])


# =========================================================================
# Request/Response Models
# =========================================================================

class SwapEvaluateRequest(BaseModel):
    """Request to evaluate a swap before execution"""
    user_wallet: str = Field(..., description="User's wallet public key")
    input_mint: str = Field(..., description="Token mint to sell")
    output_mint: str = Field(..., description="Token mint to buy")
    amount: float = Field(..., gt=0, description="Amount to swap (in token units, not lamports)")
    input_symbol: str = Field(default="SOL", description="Input token symbol")
    output_symbol: str = Field(default="TOKEN", description="Output token symbol")
    slippage_bps: int = Field(default=100, ge=1, le=5000, description="Slippage in basis points")


class SwapEvaluateResponse(BaseModel):
    """Response from swap evaluation"""
    request_id: str
    action: str  # approve, warn, reject, etc.
    risk_level: str  # safe, low, medium, high, critical, blocked
    
    # Risk scores
    overall_risk: Optional[float] = None
    honeypot_risk: Optional[float] = None
    rugpull_risk: Optional[float] = None
    liquidity_risk: Optional[float] = None
    
    # Recommendations
    recommended_slippage_bps: int
    max_safe_amount_sol: float
    
    # Warnings
    warnings: List[str]
    
    # If approved, safe parameters
    safe_swap_params: Optional[dict] = None
    
    # Reasoning
    reasoning: str
    confidence: float
    
    # Flags
    is_honeypot: bool = False
    is_blacklisted: bool = False
    can_proceed: bool = False


class QuickCheckRequest(BaseModel):
    """Quick token safety check"""
    mint: str = Field(..., description="Token mint address to check")


class QuickCheckResponse(BaseModel):
    """Quick check result"""
    mint: str
    is_safe: bool
    risk_level: str
    can_buy: bool
    can_sell: bool
    is_honeypot: bool
    liquidity_usd: float
    price_impact_pct: float
    warnings: List[str]


class SwapExecuteRequest(BaseModel):
    """Request to execute a safe swap"""
    user_wallet: str
    input_mint: str
    output_mint: str  
    amount_lamports: int = Field(..., gt=0)
    max_slippage_bps: int = Field(default=100, ge=1, le=5000)
    skip_risk_check: bool = Field(default=False, description="Skip risk analysis (not recommended)")


class SwapExecuteResponse(BaseModel):
    """Response with swap transaction"""
    success: bool
    risk_level: str
    warnings: List[str]
    
    # Transaction to sign (base64)
    transaction: Optional[str] = None
    
    # Quote details
    expected_output: Optional[int] = None
    minimum_output: Optional[int] = None
    price_impact_pct: Optional[float] = None
    
    # Recommendation
    recommended_slippage: int
    
    error: Optional[str] = None


class TokenAnalysisResponse(BaseModel):
    """Detailed token analysis"""
    mint: str
    symbol: str
    name: str
    
    overall_risk: float
    risk_level: str
    
    honeypot_risk: float
    rugpull_risk: float
    liquidity_risk: float
    concentration_risk: float
    
    is_honeypot: bool
    is_blacklisted: bool
    has_mint_authority: bool
    has_freeze_authority: bool
    is_verified: bool
    
    liquidity_usd: float
    can_sell: bool
    
    holder_count: int
    top_holder_pct: float
    age_hours: float
    
    warnings: List[str]
    recommended_action: str
    max_safe_amount_sol: float


class SwapGuardStats(BaseModel):
    """SwapGuard statistics"""
    swaps_evaluated: int
    swaps_approved: int
    swaps_warned: int
    swaps_blocked: int
    honeypots_caught: int
    user_savings_usd: float
    blacklist_size: int
    whitelist_size: int


# =========================================================================
# Endpoints
# =========================================================================

@router.post("/evaluate", response_model=SwapEvaluateResponse)
async def evaluate_swap_endpoint(request: SwapEvaluateRequest):
    """
    🛡️ Evaluate a swap before execution.
    
    This endpoint analyzes the target token and returns:
    - Risk assessment (honeypot, rug pull, liquidity risks)
    - Recommended action (approve, warn, reject)
    - Safe swap parameters if approved
    - Warnings and reasoning
    
    Always call this before executing a swap!
    """
    try:
        decision = await evaluate_swap(
            user_wallet=request.user_wallet,
            input_mint=request.input_mint,
            output_mint=request.output_mint,
            amount=request.amount,
            input_symbol=request.input_symbol,
            output_symbol=request.output_symbol,
            slippage_bps=request.slippage_bps,
        )
        
        # Build response
        analysis = decision.token_analysis
        
        return SwapEvaluateResponse(
            request_id=decision.request_id,
            action=decision.action.value,
            risk_level=decision.risk_level.value,
            overall_risk=analysis.overall_risk if analysis else None,
            honeypot_risk=analysis.honeypot_risk if analysis else None,
            rugpull_risk=analysis.rugpull_risk if analysis else None,
            liquidity_risk=analysis.liquidity_risk if analysis else None,
            recommended_slippage_bps=decision.recommended_slippage_bps,
            max_safe_amount_sol=decision.max_safe_amount,
            warnings=decision.warnings,
            safe_swap_params=decision.safe_swap_params,
            reasoning=decision.reasoning,
            confidence=decision.confidence,
            is_honeypot=analysis.is_honeypot if analysis else False,
            is_blacklisted=analysis.is_blacklisted if analysis else False,
            can_proceed=decision.action in (SwapAction.APPROVE, SwapAction.WARN),
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quick-check", response_model=QuickCheckResponse)
async def quick_check_token(request: QuickCheckRequest):
    """
    ⚡ Quick safety check for a token.
    
    Faster than full evaluation - checks:
    - Can buy/sell (honeypot detection)
    - Basic liquidity
    - Price impact
    
    Use for quick screening before showing tokens to users.
    """
    try:
        jupiter = get_jupiter_client()
        liquidity = await jupiter.check_liquidity(request.mint)
        
        warnings = []
        risk_level = "safe"
        
        if liquidity.get("is_honeypot"):
            risk_level = "critical"
            warnings.append("🚨 HONEYPOT: Cannot sell!")
        elif not liquidity.get("has_liquidity"):
            risk_level = "critical"
            warnings.append("❌ No liquidity")
        elif liquidity.get("estimated_liquidity_usd", 0) < 1000:
            risk_level = "high"
            warnings.append("⚠️ Very low liquidity")
        elif liquidity.get("estimated_liquidity_usd", 0) < 10000:
            risk_level = "medium"
            warnings.append("⚠️ Low liquidity")
        elif liquidity.get("price_impact_buy", 0) > 5:
            risk_level = "medium"
            warnings.append(f"⚠️ High price impact: {liquidity.get('price_impact_buy', 0):.1f}%")
        
        return QuickCheckResponse(
            mint=request.mint,
            is_safe=risk_level in ("safe", "low"),
            risk_level=risk_level,
            can_buy=liquidity.get("can_buy", False),
            can_sell=liquidity.get("can_sell", False),
            is_honeypot=liquidity.get("is_honeypot", False),
            liquidity_usd=liquidity.get("estimated_liquidity_usd", 0),
            price_impact_pct=liquidity.get("price_impact_buy", 0) or 0,
            warnings=warnings,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute", response_model=SwapExecuteResponse)
async def execute_safe_swap(request: SwapExecuteRequest):
    """
    🔄 Execute a risk-aware swap.
    
    Returns a transaction for the user to sign - does NOT auto-execute.
    
    Flow:
    1. Analyzes token risk
    2. Adjusts slippage if needed
    3. Gets quote from Jupiter
    4. Returns unsigned transaction
    
    User must sign and submit the transaction themselves.
    """
    try:
        result = await safe_swap(
            input_mint=request.input_mint,
            output_mint=request.output_mint,
            amount_lamports=request.amount_lamports,
            user_wallet=request.user_wallet,
            max_slippage_bps=request.max_slippage_bps,
        )
        
        return SwapExecuteResponse(
            success=result.get("safe", False),
            risk_level=result.get("risk_level", "unknown"),
            warnings=result.get("warnings", []),
            transaction=result.get("transaction"),
            expected_output=result.get("quote", {}).get("outAmount") if result.get("quote") else None,
            minimum_output=result.get("quote", {}).get("otherAmountThreshold") if result.get("quote") else None,
            price_impact_pct=result.get("quote", {}).get("priceImpactPct", 0) * 100 if result.get("quote") else None,
            recommended_slippage=result.get("recommended_slippage", request.max_slippage_bps),
            error=result.get("error"),
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyze/{mint}", response_model=TokenAnalysisResponse)
async def analyze_token(mint: str, symbol: str = Query(default="TOKEN")):
    """
    🔍 Get detailed token analysis.
    
    Comprehensive risk analysis including:
    - Honeypot detection
    - Rug pull indicators
    - Liquidity assessment
    - Holder concentration
    - Authority checks
    """
    try:
        guard = get_swapguard()
        analysis = await guard._get_token_analysis(mint, symbol)
        
        return TokenAnalysisResponse(
            mint=analysis.mint,
            symbol=analysis.symbol,
            name=analysis.name,
            overall_risk=analysis.overall_risk,
            risk_level=analysis.risk_level.value,
            honeypot_risk=analysis.honeypot_risk,
            rugpull_risk=analysis.rugpull_risk,
            liquidity_risk=analysis.liquidity_risk,
            concentration_risk=analysis.concentration_risk,
            is_honeypot=analysis.is_honeypot,
            is_blacklisted=analysis.is_blacklisted,
            has_mint_authority=analysis.has_mint_authority,
            has_freeze_authority=analysis.has_freeze_authority,
            is_verified=analysis.is_verified,
            liquidity_usd=analysis.liquidity_usd,
            can_sell=analysis.can_sell,
            holder_count=analysis.holder_count,
            top_holder_pct=analysis.top_holder_pct,
            age_hours=analysis.age_hours,
            warnings=analysis.warnings,
            recommended_action=analysis.recommended_action.value,
            max_safe_amount_sol=analysis.max_safe_amount_sol,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=SwapGuardStats)
async def get_swapguard_stats():
    """
    📊 Get SwapGuard statistics.
    
    Shows how many swaps evaluated, blocked honeypots,
    and estimated user savings.
    """
    guard = get_swapguard()
    stats = guard.get_stats()
    
    return SwapGuardStats(**stats)


@router.get("/honeypots")
async def get_detected_honeypots():
    """
    🍯 Get list of recently detected honeypots.
    """
    guard = get_swapguard()
    honeypots = guard.get_recent_honeypots()
    
    return {
        "count": len(honeypots),
        "honeypots": honeypots,
    }


@router.post("/blacklist/add")
async def add_to_blacklist(mint: str, reason: str = "Manual addition"):
    """
    🚫 Add a token to the blacklist.
    """
    guard = get_swapguard()
    guard.add_to_blacklist(mint, reason)
    
    return {"success": True, "message": f"Token {mint[:16]}... added to blacklist"}


@router.post("/whitelist/add")
async def add_to_whitelist(mint: str):
    """
    ✅ Add a verified token to the whitelist.
    """
    guard = get_swapguard()
    guard.add_to_whitelist(mint)
    
    return {"success": True, "message": f"Token {mint[:16]}... added to whitelist"}


# =========================================================================
# Jupiter Direct Endpoints
# =========================================================================

@router.get("/quote")
async def get_swap_quote(
    input_mint: str,
    output_mint: str,
    amount: int,
    slippage_bps: int = 100,
):
    """
    💱 Get a raw swap quote from Jupiter.
    
    No risk analysis - use /evaluate for protected swaps.
    """
    try:
        jupiter = get_jupiter_client()
        quote = await jupiter.get_quote(
            input_mint,
            output_mint,
            amount,
            slippage_bps
        )
        
        if not quote:
            raise HTTPException(status_code=404, detail="No route found")
        
        return quote
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/price/{mint}")
async def get_token_price(mint: str):
    """
    💰 Get token price in USD.
    """
    try:
        jupiter = get_jupiter_client()
        price = await jupiter.get_price(mint)
        
        return {
            "mint": mint,
            "price_usd": price,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tokens/search")
async def search_tokens(query: str):
    """
    🔎 Search for tokens by name or symbol.
    """
    try:
        jupiter = get_jupiter_client()
        results = await jupiter.search_token(query)
        
        return {
            "query": query,
            "count": len(results),
            "tokens": results,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
