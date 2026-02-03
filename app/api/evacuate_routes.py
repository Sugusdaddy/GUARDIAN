"""
Evacuation API Routes - Emergency Wallet Protection

Endpoints for emergency wallet evacuation when under attack.
Move all funds to safety before attackers can drain them.
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Import Evacuator
import sys
sys.path.insert(0, ".")
from GUARDIAN.agents.specialized.evacuator_agent import (
    EvacuatorAgent,
    EvacuationPlan,
    EvacuationResult,
    EvacuationStatus,
    ThreatUrgency,
    get_evacuator,
    emergency_evacuate,
)


router = APIRouter(prefix="/api/evacuate", tags=["evacuate"])


# =========================================================================
# Request/Response Models
# =========================================================================

class RegisterSafeWalletRequest(BaseModel):
    """Register a safe wallet for emergencies"""
    user_wallet: str = Field(..., description="Your main wallet address")
    safe_wallet: str = Field(..., description="Safe wallet to evacuate to")


class AnalyzeWalletRequest(BaseModel):
    """Request to analyze a wallet"""
    wallet: str = Field(..., description="Wallet address to analyze")


class WalletAnalysisResponse(BaseModel):
    """Wallet analysis result"""
    wallet: str
    timestamp: str
    total_value_usd: float
    risk_score: int
    assets: List[dict]
    approvals: List[dict]
    error: Optional[str] = None


class CreatePlanRequest(BaseModel):
    """Request to create an evacuation plan"""
    source_wallet: str = Field(..., description="Wallet to evacuate")
    destination_wallet: Optional[str] = Field(None, description="Safe wallet (uses registered if None)")
    urgency: str = Field(default="high", description="low, medium, high, or critical")
    include_nfts: bool = Field(default=True, description="Include NFTs in evacuation")
    revoke_approvals: bool = Field(default=True, description="Revoke dangerous approvals")


class EvacuationPlanResponse(BaseModel):
    """Evacuation plan details"""
    source_wallet: str
    destination_wallet: str
    urgency: str
    total_value_usd: float
    asset_count: int
    approvals_to_revoke: int
    estimated_transactions: int
    estimated_fee_sol: float
    estimated_time_seconds: int
    assets: List[dict]
    ready_to_execute: bool


class ExecutePlanRequest(BaseModel):
    """Request to execute an evacuation"""
    source_wallet: str
    destination_wallet: str
    urgency: str = "high"
    dry_run: bool = Field(default=False, description="Simulate without sending transactions")


class EmergencyEvacuateRequest(BaseModel):
    """🚨 Emergency evacuation request"""
    source_wallet: str = Field(..., description="Wallet under attack")
    destination_wallet: str = Field(..., description="Safe wallet to evacuate to")


class EvacuationResultResponse(BaseModel):
    """Evacuation result"""
    status: str
    total_evacuated_usd: float
    total_failed_usd: float
    assets_evacuated: int
    assets_failed: int
    approvals_revoked: int
    transactions_sent: int
    transactions_confirmed: int
    duration_seconds: float
    errors: List[str]


class ThreatAssessmentResponse(BaseModel):
    """Threat assessment for a wallet"""
    wallet: str
    urgency: str
    risk_score: int
    threat_indicators: List[str]
    recommendation: str
    approvals_at_risk: int
    total_value_usd: float
    assessed_at: str


class EvacuatorStats(BaseModel):
    """Evacuator statistics"""
    evacuations_completed: int
    evacuations_failed: int
    total_value_saved_usd: float
    total_assets_moved: int
    approvals_revoked: int
    active_evacuations: int
    registered_safe_wallets: int


# =========================================================================
# Endpoints
# =========================================================================

@router.post("/register-safe-wallet")
async def register_safe_wallet(request: RegisterSafeWalletRequest):
    """
    📝 Register a safe wallet for emergency evacuation.
    
    **Do this BEFORE you need it!**
    
    When your wallet is under attack, you don't want to be
    typing addresses. Register your safe wallet now.
    """
    evacuator = get_evacuator()
    success = evacuator.register_safe_wallet(
        request.user_wallet,
        request.safe_wallet
    )
    
    return {
        "success": success,
        "message": "Safe wallet registered" if success else "Wallet already registered",
        "user_wallet": request.user_wallet[:16] + "...",
        "safe_wallet": request.safe_wallet[:16] + "...",
    }


@router.post("/analyze", response_model=WalletAnalysisResponse)
async def analyze_wallet(request: AnalyzeWalletRequest):
    """
    🔍 Analyze a wallet's assets and approvals.
    
    Returns:
    - All assets (SOL, tokens, NFTs)
    - All token approvals (potential attack vectors)
    - Risk score based on approvals
    - Total portfolio value
    """
    try:
        evacuator = get_evacuator()
        result = await evacuator.analyze_wallet(request.wallet)
        
        return WalletAnalysisResponse(
            wallet=result["wallet"],
            timestamp=result["timestamp"],
            total_value_usd=result["total_value_usd"],
            risk_score=result["risk_score"],
            assets=result["assets"],
            approvals=result["approvals"],
            error=result.get("error"),
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assess-threat", response_model=ThreatAssessmentResponse)
async def assess_threat(request: AnalyzeWalletRequest):
    """
    ⚠️ Assess if a wallet needs evacuation.
    
    Checks for:
    - Dangerous token approvals
    - Signs of drainer activity
    - Recent suspicious transactions
    
    Returns recommendation:
    - safe: No action needed
    - revoke_approvals: Should revoke some approvals
    - consider_evacuation: Some risk, consider moving funds
    - urgent_evacuation: High risk, evacuate soon
    - immediate_evacuation: Under attack, evacuate NOW
    """
    try:
        evacuator = get_evacuator()
        result = await evacuator.assess_threat(request.wallet)
        
        return ThreatAssessmentResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plan", response_model=EvacuationPlanResponse)
async def create_evacuation_plan(request: CreatePlanRequest):
    """
    📋 Create an evacuation plan.
    
    Analyzes the wallet and creates a detailed plan including:
    - All assets to evacuate
    - Approvals to revoke
    - Transaction count and fees
    - Estimated time
    
    Review the plan before executing.
    """
    try:
        evacuator = get_evacuator()
        
        # Map urgency string to enum
        urgency_map = {
            "low": ThreatUrgency.LOW,
            "medium": ThreatUrgency.MEDIUM,
            "high": ThreatUrgency.HIGH,
            "critical": ThreatUrgency.CRITICAL,
        }
        urgency = urgency_map.get(request.urgency.lower(), ThreatUrgency.HIGH)
        
        plan = await evacuator.create_evacuation_plan(
            source_wallet=request.source_wallet,
            destination_wallet=request.destination_wallet,
            urgency=urgency,
            include_nfts=request.include_nfts,
            revoke_approvals=request.revoke_approvals,
        )
        
        return EvacuationPlanResponse(
            source_wallet=plan.source_wallet,
            destination_wallet=plan.destination_wallet,
            urgency=plan.urgency.value,
            total_value_usd=plan.total_value_usd,
            asset_count=len(plan.assets),
            approvals_to_revoke=len(plan.approvals_to_revoke),
            estimated_transactions=plan.estimated_transactions,
            estimated_fee_sol=plan.estimated_fee_sol,
            estimated_time_seconds=plan.estimated_time_seconds,
            assets=[evacuator._asset_to_dict(a) for a in plan.assets],
            ready_to_execute=True,
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute", response_model=EvacuationResultResponse)
async def execute_evacuation(request: ExecutePlanRequest):
    """
    🚀 Execute an evacuation plan.
    
    This will:
    1. Revoke dangerous approvals
    2. Transfer all tokens to safe wallet
    3. Transfer SOL (keeping minimum for rent)
    
    Set dry_run=true to simulate without sending transactions.
    """
    try:
        evacuator = get_evacuator()
        
        urgency_map = {
            "low": ThreatUrgency.LOW,
            "medium": ThreatUrgency.MEDIUM,
            "high": ThreatUrgency.HIGH,
            "critical": ThreatUrgency.CRITICAL,
        }
        urgency = urgency_map.get(request.urgency.lower(), ThreatUrgency.HIGH)
        
        # Create plan
        plan = await evacuator.create_evacuation_plan(
            source_wallet=request.source_wallet,
            destination_wallet=request.destination_wallet,
            urgency=urgency,
        )
        
        # Execute
        result = await evacuator.execute_evacuation(plan, dry_run=request.dry_run)
        
        return EvacuationResultResponse(
            status=result.status.value,
            total_evacuated_usd=result.total_evacuated_usd,
            total_failed_usd=result.total_failed_usd,
            assets_evacuated=len(result.assets_evacuated),
            assets_failed=len(result.assets_failed),
            approvals_revoked=len(result.approvals_revoked),
            transactions_sent=result.transactions_sent,
            transactions_confirmed=result.transactions_confirmed,
            duration_seconds=result.duration_seconds,
            errors=result.errors,
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emergency", response_model=EvacuationResultResponse)
async def emergency_evacuation(request: EmergencyEvacuateRequest):
    """
    🚨🚨🚨 EMERGENCY EVACUATION 🚨🚨🚨
    
    **USE WHEN YOUR WALLET IS ACTIVELY BEING DRAINED**
    
    This is the panic button:
    - Maximum priority fees
    - No confirmation needed
    - Revokes all approvals
    - Moves everything immediately
    
    Every second counts when you're under attack.
    """
    try:
        result = await emergency_evacuate(
            source_wallet=request.source_wallet,
            destination_wallet=request.destination_wallet,
        )
        
        return EvacuationResultResponse(
            status=result.status.value,
            total_evacuated_usd=result.total_evacuated_usd,
            total_failed_usd=result.total_failed_usd,
            assets_evacuated=len(result.assets_evacuated),
            assets_failed=len(result.assets_failed),
            approvals_revoked=len(result.approvals_revoked),
            transactions_sent=result.transactions_sent,
            transactions_confirmed=result.transactions_confirmed,
            duration_seconds=result.duration_seconds,
            errors=result.errors,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=EvacuatorStats)
async def get_evacuator_stats():
    """
    📊 Get Evacuator statistics.
    
    Shows total value saved, evacuations completed, etc.
    """
    evacuator = get_evacuator()
    stats = evacuator.get_stats()
    
    return EvacuatorStats(**stats)


@router.get("/history")
async def get_evacuation_history(limit: int = Query(default=10, le=100)):
    """
    📜 Get recent evacuation history.
    """
    evacuator = get_evacuator()
    history = evacuator.get_evacuation_history(limit)
    
    return {
        "count": len(history),
        "evacuations": history,
    }


@router.get("/safe-wallets/{user_wallet}")
async def get_safe_wallets(user_wallet: str):
    """
    🏠 Get registered safe wallets for a user.
    """
    evacuator = get_evacuator()
    safe_wallets = evacuator.safe_wallets.get(user_wallet, [])
    
    return {
        "user_wallet": user_wallet[:16] + "...",
        "safe_wallets": [w[:16] + "..." for w in safe_wallets],
        "count": len(safe_wallets),
    }
