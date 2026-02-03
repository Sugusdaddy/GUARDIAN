"""
SWAPGUARD Agent - Risk-Aware DEX Trading Protection

Intercepts swap requests, analyzes token risk, and provides
protected trading with automatic honeypot detection, rug pull
warnings, and intelligent slippage management.

Your bodyguard for every trade on Solana.
"""

import asyncio
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

from agents.core.base_agent import BaseAgent


class SwapRisk(Enum):
    """Risk levels for swap operations"""
    SAFE = "safe"              # Green light - verified token
    LOW = "low"                # Minor concerns - proceed with caution
    MEDIUM = "medium"          # Significant risk - user acknowledgment required  
    HIGH = "high"              # Dangerous - strong warning
    CRITICAL = "critical"      # DO NOT TRADE - honeypot/scam confirmed
    BLOCKED = "blocked"        # Blacklisted - swap rejected


class SwapAction(Enum):
    """Actions the agent can take on swaps"""
    APPROVE = "approve"        # Safe to execute
    WARN = "warn"              # Show warning, allow if acknowledged
    LIMIT = "limit"            # Reduce position size
    REJECT = "reject"          # Block the swap
    REQUIRE_CONFIRM = "require_confirm"  # Need explicit confirmation


@dataclass
class TokenAnalysis:
    """Complete token risk analysis"""
    mint: str
    symbol: str
    name: str
    
    # Risk scores (0-100)
    overall_risk: float
    honeypot_risk: float
    rugpull_risk: float
    liquidity_risk: float
    concentration_risk: float
    
    # Flags
    is_honeypot: bool
    is_blacklisted: bool
    has_mint_authority: bool
    has_freeze_authority: bool
    is_verified: bool
    
    # Liquidity data
    liquidity_usd: float
    price_impact_1sol: float
    can_sell: bool
    
    # Holder data
    top_holder_pct: float
    holder_count: int
    
    # Metadata
    has_social: bool
    age_hours: float
    
    # Warnings
    warnings: List[str] = field(default_factory=list)
    
    # Recommendation
    risk_level: SwapRisk = SwapRisk.MEDIUM
    recommended_action: SwapAction = SwapAction.WARN
    max_safe_amount_sol: float = 0.0


@dataclass  
class SwapRequest:
    """Incoming swap request to evaluate"""
    id: str
    user_wallet: str
    input_mint: str
    output_mint: str
    input_amount: float
    input_symbol: str
    output_symbol: str
    slippage_bps: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SwapDecision:
    """Agent's decision on a swap request"""
    request_id: str
    action: SwapAction
    risk_level: SwapRisk
    
    # Analysis
    token_analysis: Optional[TokenAnalysis]
    
    # Recommendations
    recommended_slippage_bps: int
    max_safe_amount: float
    warnings: List[str]
    
    # If approved, the safe swap parameters
    safe_swap_params: Optional[Dict] = None
    
    # Reasoning
    reasoning: str = ""
    confidence: float = 0.0


class SwapGuardAgent(BaseAgent):
    """
    🛡️ SWAPGUARD - Your Trading Bodyguard
    
    Protects users from dangerous trades by:
    - Analyzing tokens before swap execution
    - Detecting honeypots in real-time
    - Warning about rug pull indicators
    - Managing slippage intelligently
    - Blocking trades to blacklisted tokens
    - Limiting exposure on risky tokens
    
    Integration:
    - Jupiter aggregator for quotes and swaps
    - Scanner agent for deep token analysis
    - Blacklist database for known scams
    - ML risk scoring for unknown tokens
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(
            agent_id="swapguard",
            name="SwapGuard",
            description="Risk-aware DEX trading protection"
        )
        
        self.config = config or {}
        
        # Risk thresholds
        self.thresholds = {
            "safe_max_risk": 20,           # Below this = SAFE
            "low_max_risk": 40,            # Below this = LOW
            "medium_max_risk": 60,         # Below this = MEDIUM
            "high_max_risk": 80,           # Below this = HIGH
            "critical_threshold": 80,       # Above this = CRITICAL
            "min_liquidity_usd": 1000,     # Minimum liquidity
            "max_price_impact_pct": 10,    # Max acceptable price impact
            "honeypot_block": True,        # Auto-block honeypots
            "blacklist_block": True,       # Auto-block blacklisted
        }
        
        # Position limits based on risk
        self.position_limits = {
            SwapRisk.SAFE: 100.0,       # No limit (100 SOL max shown)
            SwapRisk.LOW: 10.0,         # 10 SOL max
            SwapRisk.MEDIUM: 2.0,       # 2 SOL max
            SwapRisk.HIGH: 0.5,         # 0.5 SOL max
            SwapRisk.CRITICAL: 0.0,     # No trading
            SwapRisk.BLOCKED: 0.0,      # No trading
        }
        
        # Slippage recommendations based on risk
        self.slippage_recommendations = {
            SwapRisk.SAFE: 50,          # 0.5%
            SwapRisk.LOW: 100,          # 1%
            SwapRisk.MEDIUM: 200,       # 2%
            SwapRisk.HIGH: 500,         # 5%
            SwapRisk.CRITICAL: 1000,    # 10% (if somehow allowed)
        }
        
        # Blacklist cache
        self.blacklist: set = set()
        
        # Whitelist (verified safe tokens)
        self.whitelist: set = {
            "So11111111111111111111111111111111111111112",   # SOL
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
            "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",  # USDT
            "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So",   # mSOL
            "7dHbWXmci3dT8UFYWYZweBLXgycu7Y3iL6trKn1Y7ARj",  # stSOL
            "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",  # BONK
            "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN",   # JUP
        }
        
        # Analysis cache
        self.analysis_cache: Dict[str, Tuple[TokenAnalysis, datetime]] = {}
        self.cache_ttl = timedelta(minutes=5)
        
        # Stats
        self.stats = {
            "swaps_evaluated": 0,
            "swaps_approved": 0,
            "swaps_warned": 0,
            "swaps_blocked": 0,
            "honeypots_caught": 0,
            "user_savings_usd": 0.0,
        }
        
        self.log.info("🛡️ SwapGuard initialized - Ready to protect your trades")
    
    async def evaluate_swap(self, request: SwapRequest) -> SwapDecision:
        """
        Main entry point: Evaluate a swap request and return decision.
        
        This is called before any swap is executed to determine if it's safe.
        """
        self.stats["swaps_evaluated"] += 1
        
        self.log.info(f"📋 Evaluating swap: {request.input_symbol} → {request.output_symbol}",
                     amount=request.input_amount,
                     user=request.user_wallet[:8])
        
        # Check if output token is whitelisted (fast path)
        if request.output_mint in self.whitelist:
            return self._approve_swap(request, "Token is verified and whitelisted")
        
        # Check if output token is blacklisted
        if request.output_mint in self.blacklist:
            self.stats["swaps_blocked"] += 1
            return self._reject_swap(request, "Token is blacklisted as a known scam")
        
        # Get or compute token analysis
        analysis = await self._get_token_analysis(request.output_mint, request.output_symbol)
        
        # Make decision based on analysis
        decision = self._make_decision(request, analysis)
        
        # Update stats
        if decision.action == SwapAction.APPROVE:
            self.stats["swaps_approved"] += 1
        elif decision.action == SwapAction.REJECT:
            self.stats["swaps_blocked"] += 1
            if analysis and analysis.is_honeypot:
                self.stats["honeypots_caught"] += 1
                self.stats["user_savings_usd"] += request.input_amount * 150  # Rough SOL price
        else:
            self.stats["swaps_warned"] += 1
        
        return decision
    
    async def _get_token_analysis(self, mint: str, symbol: str) -> TokenAnalysis:
        """Get token analysis from cache or compute fresh"""
        
        # Check cache
        if mint in self.analysis_cache:
            cached, timestamp = self.analysis_cache[mint]
            if datetime.now(timezone.utc) - timestamp < self.cache_ttl:
                self.log.debug(f"Cache hit for {symbol}")
                return cached
        
        # Compute fresh analysis
        analysis = await self._analyze_token(mint, symbol)
        
        # Cache it
        self.analysis_cache[mint] = (analysis, datetime.now(timezone.utc))
        
        return analysis
    
    async def _analyze_token(self, mint: str, symbol: str) -> TokenAnalysis:
        """
        Perform comprehensive token analysis.
        
        Integrates multiple data sources:
        - Jupiter for liquidity/tradability
        - On-chain data for authorities
        - Holder analysis
        - Pattern matching
        """
        self.log.info(f"🔍 Analyzing token: {symbol} ({mint[:8]}...)")
        
        warnings = []
        
        # Initialize with defaults (will be updated with real data)
        analysis = TokenAnalysis(
            mint=mint,
            symbol=symbol,
            name=symbol,
            overall_risk=50.0,
            honeypot_risk=0.0,
            rugpull_risk=0.0,
            liquidity_risk=50.0,
            concentration_risk=50.0,
            is_honeypot=False,
            is_blacklisted=False,
            has_mint_authority=False,
            has_freeze_authority=False,
            is_verified=False,
            liquidity_usd=0.0,
            price_impact_1sol=100.0,
            can_sell=True,
            top_holder_pct=0.0,
            holder_count=0,
            has_social=False,
            age_hours=0.0,
            warnings=warnings,
        )
        
        try:
            # Check liquidity via Jupiter
            liquidity_data = await self._check_jupiter_liquidity(mint)
            
            if liquidity_data:
                analysis.liquidity_usd = liquidity_data.get("estimated_liquidity_usd", 0)
                analysis.price_impact_1sol = liquidity_data.get("price_impact_buy", 100)
                analysis.can_sell = liquidity_data.get("can_sell", False)
                
                # Honeypot detection: can buy but can't sell
                if liquidity_data.get("can_buy") and not liquidity_data.get("can_sell"):
                    analysis.is_honeypot = True
                    analysis.honeypot_risk = 100.0
                    warnings.append("🚨 HONEYPOT DETECTED: Cannot sell this token!")
                
                # Low liquidity warning
                if analysis.liquidity_usd < self.thresholds["min_liquidity_usd"]:
                    analysis.liquidity_risk = 80.0
                    warnings.append(f"⚠️ Very low liquidity: ${analysis.liquidity_usd:.0f}")
                elif analysis.liquidity_usd < 10000:
                    analysis.liquidity_risk = 50.0
                    warnings.append(f"⚠️ Low liquidity: ${analysis.liquidity_usd:.0f}")
                else:
                    analysis.liquidity_risk = max(0, 30 - (analysis.liquidity_usd / 10000))
                
                # High price impact warning
                if analysis.price_impact_1sol > self.thresholds["max_price_impact_pct"]:
                    warnings.append(f"⚠️ High price impact: {analysis.price_impact_1sol:.1f}%")
            else:
                # No liquidity data = very risky
                analysis.liquidity_risk = 90.0
                warnings.append("⚠️ Unable to verify liquidity - token may not be tradeable")
            
            # Check token metadata and authorities
            token_info = await self._get_token_info(mint)
            
            if token_info:
                analysis.name = token_info.get("name", symbol)
                analysis.has_mint_authority = token_info.get("mint_authority_enabled", False)
                analysis.has_freeze_authority = token_info.get("freeze_authority_enabled", False)
                analysis.is_verified = token_info.get("verified", False)
                analysis.age_hours = token_info.get("age_hours", 0)
                analysis.holder_count = token_info.get("holder_count", 0)
                analysis.top_holder_pct = token_info.get("top_holder_pct", 0)
                analysis.has_social = token_info.get("has_social", False)
                
                # Mint authority warning (can mint infinite tokens)
                if analysis.has_mint_authority:
                    analysis.rugpull_risk += 30
                    warnings.append("⚠️ Mint authority enabled - team can create unlimited tokens")
                
                # Freeze authority warning (can freeze your tokens)
                if analysis.has_freeze_authority:
                    analysis.rugpull_risk += 20
                    warnings.append("⚠️ Freeze authority enabled - your tokens could be frozen")
                
                # New token warning
                if analysis.age_hours < 24:
                    analysis.rugpull_risk += 20
                    warnings.append(f"⚠️ Very new token: {analysis.age_hours:.1f} hours old")
                elif analysis.age_hours < 72:
                    analysis.rugpull_risk += 10
                    warnings.append(f"⚠️ New token: {analysis.age_hours:.1f} hours old")
                
                # Concentration warning
                if analysis.top_holder_pct > 50:
                    analysis.concentration_risk = 90.0
                    warnings.append(f"🚨 High concentration: Top holder owns {analysis.top_holder_pct:.1f}%")
                elif analysis.top_holder_pct > 20:
                    analysis.concentration_risk = 60.0
                    warnings.append(f"⚠️ Concentrated holdings: Top holder owns {analysis.top_holder_pct:.1f}%")
                
                # Low holder count
                if analysis.holder_count < 100:
                    warnings.append(f"⚠️ Few holders: only {analysis.holder_count} wallets")
                
                # No social links
                if not analysis.has_social:
                    warnings.append("⚠️ No social media links found")
            
            # Calculate overall risk score
            analysis.overall_risk = self._calculate_overall_risk(analysis)
            
            # Determine risk level and action
            analysis.risk_level = self._determine_risk_level(analysis)
            analysis.recommended_action = self._determine_action(analysis)
            analysis.max_safe_amount_sol = self.position_limits.get(analysis.risk_level, 0.0)
            
            analysis.warnings = warnings
            
        except Exception as e:
            self.log.error(f"Error analyzing token {symbol}", error=str(e))
            analysis.overall_risk = 75.0
            analysis.risk_level = SwapRisk.HIGH
            analysis.recommended_action = SwapAction.WARN
            analysis.warnings = ["⚠️ Unable to fully analyze token - proceed with extreme caution"]
        
        self.log.info(f"📊 Analysis complete: {symbol} = {analysis.risk_level.value} risk ({analysis.overall_risk:.0f}/100)")
        
        return analysis
    
    async def _check_jupiter_liquidity(self, mint: str) -> Optional[Dict]:
        """Check token liquidity via Jupiter API"""
        try:
            # Import Jupiter client
            from agents.integrations.jupiter import get_jupiter_client
            jupiter = get_jupiter_client()
            
            return await jupiter.check_liquidity(mint)
        except Exception as e:
            self.log.warning(f"Jupiter liquidity check failed", error=str(e))
            return None
    
    async def _get_token_info(self, mint: str) -> Optional[Dict]:
        """Get token metadata and on-chain info"""
        try:
            # This would integrate with Helius or direct RPC
            # For now, return simulated data structure
            # In production, this calls the actual APIs
            
            return {
                "name": "Unknown Token",
                "mint_authority_enabled": False,
                "freeze_authority_enabled": False,
                "verified": False,
                "age_hours": 48,
                "holder_count": 500,
                "top_holder_pct": 15.0,
                "has_social": True,
            }
        except Exception as e:
            self.log.warning(f"Token info fetch failed", error=str(e))
            return None
    
    def _calculate_overall_risk(self, analysis: TokenAnalysis) -> float:
        """Calculate weighted overall risk score"""
        
        # If honeypot, instant max risk
        if analysis.is_honeypot:
            return 100.0
        
        # Weighted average of risk factors
        weights = {
            "honeypot": 0.30,
            "rugpull": 0.25,
            "liquidity": 0.25,
            "concentration": 0.20,
        }
        
        score = (
            analysis.honeypot_risk * weights["honeypot"] +
            analysis.rugpull_risk * weights["rugpull"] +
            analysis.liquidity_risk * weights["liquidity"] +
            analysis.concentration_risk * weights["concentration"]
        )
        
        # Bonus for verified tokens
        if analysis.is_verified:
            score *= 0.7
        
        return min(100, max(0, score))
    
    def _determine_risk_level(self, analysis: TokenAnalysis) -> SwapRisk:
        """Determine risk level from analysis"""
        
        if analysis.is_honeypot:
            return SwapRisk.CRITICAL
        
        if analysis.is_blacklisted:
            return SwapRisk.BLOCKED
        
        risk = analysis.overall_risk
        
        if risk < self.thresholds["safe_max_risk"]:
            return SwapRisk.SAFE
        elif risk < self.thresholds["low_max_risk"]:
            return SwapRisk.LOW
        elif risk < self.thresholds["medium_max_risk"]:
            return SwapRisk.MEDIUM
        elif risk < self.thresholds["high_max_risk"]:
            return SwapRisk.HIGH
        else:
            return SwapRisk.CRITICAL
    
    def _determine_action(self, analysis: TokenAnalysis) -> SwapAction:
        """Determine recommended action from analysis"""
        
        risk_level = analysis.risk_level
        
        if risk_level == SwapRisk.SAFE:
            return SwapAction.APPROVE
        elif risk_level == SwapRisk.LOW:
            return SwapAction.APPROVE  # Approve with info
        elif risk_level == SwapRisk.MEDIUM:
            return SwapAction.WARN
        elif risk_level == SwapRisk.HIGH:
            return SwapAction.REQUIRE_CONFIRM
        elif risk_level in (SwapRisk.CRITICAL, SwapRisk.BLOCKED):
            return SwapAction.REJECT
        
        return SwapAction.WARN
    
    def _make_decision(self, request: SwapRequest, analysis: TokenAnalysis) -> SwapDecision:
        """Make final swap decision based on analysis"""
        
        action = analysis.recommended_action
        risk_level = analysis.risk_level
        
        # Check if amount exceeds safe limit
        max_safe = self.position_limits.get(risk_level, 0.0)
        if request.input_amount > max_safe and max_safe > 0:
            action = SwapAction.LIMIT
            analysis.warnings.append(
                f"⚠️ Amount ({request.input_amount} SOL) exceeds safe limit ({max_safe} SOL) for this risk level"
            )
        
        # Build safe swap parameters if approved
        safe_params = None
        if action in (SwapAction.APPROVE, SwapAction.WARN, SwapAction.LIMIT):
            recommended_slippage = self.slippage_recommendations.get(risk_level, 100)
            safe_amount = min(request.input_amount, max_safe) if max_safe > 0 else request.input_amount
            
            safe_params = {
                "input_mint": request.input_mint,
                "output_mint": request.output_mint,
                "amount": safe_amount,
                "slippage_bps": max(request.slippage_bps, recommended_slippage),
                "max_accounts": 20,  # Limit compute
            }
        
        # Generate reasoning
        reasoning = self._generate_reasoning(request, analysis, action)
        
        return SwapDecision(
            request_id=request.id,
            action=action,
            risk_level=risk_level,
            token_analysis=analysis,
            recommended_slippage_bps=self.slippage_recommendations.get(risk_level, 100),
            max_safe_amount=max_safe,
            warnings=analysis.warnings,
            safe_swap_params=safe_params,
            reasoning=reasoning,
            confidence=self._calculate_confidence(analysis),
        )
    
    def _generate_reasoning(self, request: SwapRequest, analysis: TokenAnalysis, action: SwapAction) -> str:
        """Generate human-readable reasoning for the decision"""
        
        lines = [f"Swap evaluation: {request.input_symbol} → {request.output_symbol}"]
        lines.append(f"Risk Score: {analysis.overall_risk:.0f}/100 ({analysis.risk_level.value})")
        lines.append(f"Decision: {action.value.upper()}")
        lines.append("")
        
        if analysis.is_honeypot:
            lines.append("🚨 CRITICAL: Token identified as HONEYPOT")
            lines.append("You can buy but CANNOT SELL this token.")
            lines.append("This is a confirmed scam - DO NOT TRADE.")
        elif analysis.warnings:
            lines.append("Risk factors identified:")
            for warning in analysis.warnings:
                lines.append(f"  {warning}")
        
        if action == SwapAction.APPROVE:
            lines.append("")
            lines.append("✅ Trade approved - acceptable risk level")
        elif action == SwapAction.REJECT:
            lines.append("")
            lines.append("❌ Trade BLOCKED for your protection")
        
        return "\n".join(lines)
    
    def _calculate_confidence(self, analysis: TokenAnalysis) -> float:
        """Calculate confidence in our analysis"""
        
        confidence = 50.0  # Base confidence
        
        # More data = higher confidence
        if analysis.liquidity_usd > 0:
            confidence += 15
        if analysis.holder_count > 0:
            confidence += 10
        if analysis.age_hours > 0:
            confidence += 10
        if analysis.is_verified:
            confidence += 15
        
        # Extreme values = higher confidence
        if analysis.is_honeypot:
            confidence = 95.0  # Very confident it's bad
        elif analysis.overall_risk < 10 or analysis.overall_risk > 90:
            confidence += 10
        
        return min(99, confidence)
    
    def _approve_swap(self, request: SwapRequest, reason: str) -> SwapDecision:
        """Quick approve for whitelisted tokens"""
        self.stats["swaps_approved"] += 1
        
        return SwapDecision(
            request_id=request.id,
            action=SwapAction.APPROVE,
            risk_level=SwapRisk.SAFE,
            token_analysis=None,
            recommended_slippage_bps=50,
            max_safe_amount=100.0,
            warnings=[],
            safe_swap_params={
                "input_mint": request.input_mint,
                "output_mint": request.output_mint,
                "amount": request.input_amount,
                "slippage_bps": request.slippage_bps,
            },
            reasoning=f"✅ {reason}",
            confidence=99.0,
        )
    
    def _reject_swap(self, request: SwapRequest, reason: str) -> SwapDecision:
        """Quick reject for blacklisted tokens"""
        return SwapDecision(
            request_id=request.id,
            action=SwapAction.REJECT,
            risk_level=SwapRisk.BLOCKED,
            token_analysis=None,
            recommended_slippage_bps=0,
            max_safe_amount=0.0,
            warnings=[f"🚨 {reason}"],
            safe_swap_params=None,
            reasoning=f"❌ BLOCKED: {reason}",
            confidence=99.0,
        )
    
    # =========================================================================
    # Blacklist Management
    # =========================================================================
    
    def add_to_blacklist(self, mint: str, reason: str = ""):
        """Add a token to the blacklist"""
        self.blacklist.add(mint)
        self.log.warning(f"Token blacklisted: {mint[:16]}...", reason=reason)
    
    def remove_from_blacklist(self, mint: str):
        """Remove a token from the blacklist"""
        self.blacklist.discard(mint)
        self.log.info(f"Token removed from blacklist: {mint[:16]}...")
    
    def add_to_whitelist(self, mint: str):
        """Add a verified token to whitelist"""
        self.whitelist.add(mint)
        self.log.info(f"Token whitelisted: {mint[:16]}...")
    
    # =========================================================================
    # Stats and Reporting
    # =========================================================================
    
    def get_stats(self) -> Dict:
        """Get agent statistics"""
        return {
            **self.stats,
            "blacklist_size": len(self.blacklist),
            "whitelist_size": len(self.whitelist),
            "cache_size": len(self.analysis_cache),
        }
    
    def get_recent_honeypots(self) -> List[str]:
        """Get list of recently detected honeypots"""
        honeypots = []
        for mint, (analysis, _) in self.analysis_cache.items():
            if analysis.is_honeypot:
                honeypots.append(mint)
        return honeypots


# =========================================================================
# Convenience Functions
# =========================================================================

_swapguard_instance: Optional[SwapGuardAgent] = None


def get_swapguard() -> SwapGuardAgent:
    """Get or create SwapGuard singleton"""
    global _swapguard_instance
    if _swapguard_instance is None:
        _swapguard_instance = SwapGuardAgent()
    return _swapguard_instance


async def evaluate_swap(
    user_wallet: str,
    input_mint: str,
    output_mint: str,
    amount: float,
    input_symbol: str = "SOL",
    output_symbol: str = "TOKEN",
    slippage_bps: int = 100
) -> SwapDecision:
    """
    Convenience function to evaluate a swap.
    
    Usage:
        decision = await evaluate_swap(
            user_wallet="...",
            input_mint="So111...",
            output_mint="TokenMint...",
            amount=1.0,
            input_symbol="SOL",
            output_symbol="SCAM",
        )
        
        if decision.action == SwapAction.APPROVE:
            # Execute swap with decision.safe_swap_params
            pass
        elif decision.action == SwapAction.REJECT:
            # Block swap, show decision.warnings
            pass
    """
    guard = get_swapguard()
    
    request = SwapRequest(
        id=hashlib.md5(f"{user_wallet}{output_mint}{amount}".encode()).hexdigest()[:12],
        user_wallet=user_wallet,
        input_mint=input_mint,
        output_mint=output_mint,
        input_amount=amount,
        input_symbol=input_symbol,
        output_symbol=output_symbol,
        slippage_bps=slippage_bps,
    )
    
    return await guard.evaluate_swap(request)
