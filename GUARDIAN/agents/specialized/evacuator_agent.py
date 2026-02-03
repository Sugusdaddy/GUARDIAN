"""
EVACUATOR Agent - Emergency Wallet Evacuation

When your wallet is under attack, every second counts.
Evacuator moves all funds to safety and revokes dangerous approvals
before attackers can drain your wallet.

The emergency exit for Solana wallets.
"""

import asyncio
import base64
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

from agents.core.base_agent import BaseAgent


class EvacuationStatus(Enum):
    """Status of an evacuation operation"""
    PENDING = "pending"
    ANALYZING = "analyzing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PARTIAL = "partial"  # Some assets evacuated, some failed
    FAILED = "failed"
    CANCELLED = "cancelled"


class ThreatUrgency(Enum):
    """Urgency level for evacuation"""
    LOW = "low"           # Suspicious activity, can wait
    MEDIUM = "medium"     # Active threat detected
    HIGH = "high"         # Wallet being drained
    CRITICAL = "critical" # Immediate action required


class AssetType(Enum):
    """Types of assets to evacuate"""
    SOL = "sol"
    SPL_TOKEN = "spl_token"
    NFT = "nft"
    STAKE = "stake"


@dataclass
class WalletAsset:
    """An asset in a wallet"""
    asset_type: AssetType
    mint: Optional[str]  # None for SOL
    symbol: str
    balance: float
    decimals: int
    value_usd: float
    token_account: Optional[str] = None  # Associated token account
    is_nft: bool = False
    
    def lamports(self) -> int:
        """Get balance in smallest units"""
        return int(self.balance * (10 ** self.decimals))


@dataclass
class DangerousApproval:
    """A token approval that could be exploited"""
    token_mint: str
    token_symbol: str
    approved_program: str
    approved_amount: float
    risk_level: str  # low, medium, high, critical
    reason: str


@dataclass 
class EvacuationPlan:
    """Plan for evacuating a wallet"""
    source_wallet: str
    destination_wallet: str
    urgency: ThreatUrgency
    
    # Assets to move
    assets: List[WalletAsset]
    total_value_usd: float
    
    # Approvals to revoke
    approvals_to_revoke: List[DangerousApproval]
    
    # Transaction plan
    estimated_transactions: int
    estimated_fee_sol: float
    estimated_time_seconds: int
    
    # Priority settings
    priority_fee_lamports: int
    use_jito_bundles: bool = False
    
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class EvacuationResult:
    """Result of an evacuation operation"""
    plan: EvacuationPlan
    status: EvacuationStatus
    
    # Results
    assets_evacuated: List[Dict]
    assets_failed: List[Dict]
    approvals_revoked: List[str]
    approvals_failed: List[str]
    
    # Stats
    total_evacuated_usd: float
    total_failed_usd: float
    transactions_sent: int
    transactions_confirmed: int
    
    # Timing
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: float
    
    # Errors
    errors: List[str]


class EvacuatorAgent(BaseAgent):
    """
    🚨 EVACUATOR - Emergency Wallet Evacuation
    
    When your wallet is compromised, Evacuator:
    1. Analyzes all assets in your wallet
    2. Creates optimal evacuation plan
    3. Moves all funds to your safe wallet
    4. Revokes dangerous token approvals
    5. Reports results
    
    Features:
    - Multi-asset evacuation (SOL, tokens, NFTs)
    - Priority transaction fees for speed
    - Approval revocation
    - Jito bundle support (optional)
    - Real-time progress tracking
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(
            agent_id="evacuator",
            name="Evacuator",
            description="Emergency wallet evacuation"
        )
        
        self.config = config or {}
        
        # Safe wallets registry (user pre-registers their safe wallets)
        self.safe_wallets: Dict[str, List[str]] = {}  # user_wallet -> [safe_wallets]
        
        # Active evacuations
        self.active_evacuations: Dict[str, EvacuationResult] = {}
        
        # History
        self.evacuation_history: List[EvacuationResult] = []
        
        # Priority fee tiers (in lamports per compute unit)
        self.priority_fees = {
            ThreatUrgency.LOW: 1000,        # ~0.00001 SOL
            ThreatUrgency.MEDIUM: 10000,    # ~0.0001 SOL
            ThreatUrgency.HIGH: 100000,     # ~0.001 SOL
            ThreatUrgency.CRITICAL: 1000000, # ~0.01 SOL (max priority)
        }
        
        # Minimum SOL to keep for rent/fees
        self.min_sol_reserve = 0.01
        
        # Known malicious programs to revoke
        self.malicious_programs: set = set()
        
        # Stats
        self.stats = {
            "evacuations_completed": 0,
            "evacuations_failed": 0,
            "total_value_saved_usd": 0.0,
            "total_assets_moved": 0,
            "approvals_revoked": 0,
        }
        
        self.log.info("🚨 Evacuator initialized - Ready for emergency extractions")
    
    # =========================================================================
    # Safe Wallet Management
    # =========================================================================
    
    def register_safe_wallet(self, user_wallet: str, safe_wallet: str) -> bool:
        """
        Register a safe wallet for emergency evacuation.
        
        Users should register their safe wallets BEFORE they need them.
        """
        if user_wallet not in self.safe_wallets:
            self.safe_wallets[user_wallet] = []
        
        if safe_wallet not in self.safe_wallets[user_wallet]:
            self.safe_wallets[user_wallet].append(safe_wallet)
            self.log.info(f"✅ Safe wallet registered for {user_wallet[:8]}...")
            return True
        
        return False
    
    def get_safe_wallet(self, user_wallet: str) -> Optional[str]:
        """Get the primary safe wallet for a user"""
        wallets = self.safe_wallets.get(user_wallet, [])
        return wallets[0] if wallets else None
    
    # =========================================================================
    # Wallet Analysis
    # =========================================================================
    
    async def analyze_wallet(self, wallet_address: str) -> Dict[str, Any]:
        """
        Analyze a wallet's assets and approvals.
        
        Returns complete inventory of:
        - SOL balance
        - SPL tokens
        - NFTs
        - Staked SOL
        - Token approvals
        """
        self.log.info(f"🔍 Analyzing wallet: {wallet_address[:16]}...")
        
        result = {
            "wallet": wallet_address,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "assets": [],
            "approvals": [],
            "total_value_usd": 0.0,
            "risk_score": 0,
        }
        
        try:
            # Get SOL balance
            sol_balance = await self._get_sol_balance(wallet_address)
            if sol_balance > 0:
                sol_asset = WalletAsset(
                    asset_type=AssetType.SOL,
                    mint=None,
                    symbol="SOL",
                    balance=sol_balance,
                    decimals=9,
                    value_usd=sol_balance * await self._get_sol_price(),
                )
                result["assets"].append(self._asset_to_dict(sol_asset))
                result["total_value_usd"] += sol_asset.value_usd
            
            # Get SPL tokens
            tokens = await self._get_token_accounts(wallet_address)
            for token in tokens:
                result["assets"].append(token)
                result["total_value_usd"] += token.get("value_usd", 0)
            
            # Get token approvals (delegations)
            approvals = await self._get_token_approvals(wallet_address)
            result["approvals"] = approvals
            
            # Calculate risk score based on approvals
            for approval in approvals:
                if approval.get("risk_level") == "critical":
                    result["risk_score"] += 30
                elif approval.get("risk_level") == "high":
                    result["risk_score"] += 20
                elif approval.get("risk_level") == "medium":
                    result["risk_score"] += 10
            
            result["risk_score"] = min(100, result["risk_score"])
            
        except Exception as e:
            self.log.error(f"Error analyzing wallet", error=str(e))
            result["error"] = str(e)
        
        return result
    
    async def _get_sol_balance(self, wallet: str) -> float:
        """Get SOL balance for a wallet"""
        try:
            # In production, this calls Solana RPC
            # For now, return simulated data
            return 5.5  # Simulated balance
        except Exception as e:
            self.log.error(f"Error getting SOL balance", error=str(e))
            return 0.0
    
    async def _get_sol_price(self) -> float:
        """Get current SOL price in USD"""
        try:
            from agents.integrations.jupiter import get_jupiter_client
            jupiter = get_jupiter_client()
            price = await jupiter.get_price("So11111111111111111111111111111111111111112")
            return price or 150.0  # Fallback price
        except:
            return 150.0  # Fallback
    
    async def _get_token_accounts(self, wallet: str) -> List[Dict]:
        """Get all SPL token accounts for a wallet"""
        # In production, this calls Helius or Solana RPC
        # Returns list of token accounts with balances
        return []
    
    async def _get_token_approvals(self, wallet: str) -> List[Dict]:
        """Get all token approvals (delegations) for a wallet"""
        # In production, this analyzes token accounts for delegations
        return []
    
    def _asset_to_dict(self, asset: WalletAsset) -> Dict:
        """Convert WalletAsset to dictionary"""
        return {
            "type": asset.asset_type.value,
            "mint": asset.mint,
            "symbol": asset.symbol,
            "balance": asset.balance,
            "decimals": asset.decimals,
            "value_usd": asset.value_usd,
            "token_account": asset.token_account,
            "is_nft": asset.is_nft,
        }
    
    # =========================================================================
    # Evacuation Planning
    # =========================================================================
    
    async def create_evacuation_plan(
        self,
        source_wallet: str,
        destination_wallet: Optional[str] = None,
        urgency: ThreatUrgency = ThreatUrgency.HIGH,
        include_nfts: bool = True,
        revoke_approvals: bool = True,
    ) -> EvacuationPlan:
        """
        Create an evacuation plan for a wallet.
        
        Args:
            source_wallet: Wallet to evacuate
            destination_wallet: Where to send funds (uses registered safe wallet if None)
            urgency: How urgent is the evacuation
            include_nfts: Whether to include NFTs
            revoke_approvals: Whether to revoke token approvals
        
        Returns:
            EvacuationPlan with all details
        """
        self.log.info(f"📋 Creating evacuation plan for {source_wallet[:16]}...")
        
        # Get destination
        if not destination_wallet:
            destination_wallet = self.get_safe_wallet(source_wallet)
            if not destination_wallet:
                raise ValueError("No safe wallet registered. Please provide destination_wallet.")
        
        # Analyze wallet
        analysis = await self.analyze_wallet(source_wallet)
        
        if "error" in analysis:
            raise ValueError(f"Failed to analyze wallet: {analysis['error']}")
        
        # Build asset list
        assets = []
        for asset_dict in analysis["assets"]:
            asset = WalletAsset(
                asset_type=AssetType(asset_dict["type"]),
                mint=asset_dict.get("mint"),
                symbol=asset_dict["symbol"],
                balance=asset_dict["balance"],
                decimals=asset_dict["decimals"],
                value_usd=asset_dict["value_usd"],
                token_account=asset_dict.get("token_account"),
                is_nft=asset_dict.get("is_nft", False),
            )
            
            # Skip NFTs if not included
            if asset.is_nft and not include_nfts:
                continue
            
            # Skip dust (< $0.01)
            if asset.value_usd < 0.01 and asset.asset_type != AssetType.SOL:
                continue
            
            assets.append(asset)
        
        # Build approvals to revoke
        approvals_to_revoke = []
        if revoke_approvals:
            for approval in analysis.get("approvals", []):
                approvals_to_revoke.append(DangerousApproval(
                    token_mint=approval["token_mint"],
                    token_symbol=approval.get("token_symbol", "Unknown"),
                    approved_program=approval["approved_program"],
                    approved_amount=approval.get("approved_amount", 0),
                    risk_level=approval.get("risk_level", "medium"),
                    reason=approval.get("reason", "Unknown delegation"),
                ))
        
        # Calculate transaction count
        # Each token transfer = 1 tx, SOL transfer = 1 tx, each revoke = 1 tx
        # Can batch some operations
        num_token_transfers = len([a for a in assets if a.asset_type != AssetType.SOL])
        num_sol_transfers = 1 if any(a.asset_type == AssetType.SOL for a in assets) else 0
        num_revokes = len(approvals_to_revoke)
        
        # With batching, we can do ~5 operations per tx
        estimated_transactions = (num_token_transfers + num_sol_transfers + num_revokes + 4) // 5
        estimated_transactions = max(1, estimated_transactions)
        
        # Calculate fees
        priority_fee = self.priority_fees[urgency]
        base_fee = 5000  # 0.000005 SOL per signature
        estimated_fee_sol = (base_fee + priority_fee * 200000) * estimated_transactions / 1_000_000_000
        
        # Estimate time (depends on urgency and network conditions)
        time_per_tx = {
            ThreatUrgency.LOW: 30,
            ThreatUrgency.MEDIUM: 15,
            ThreatUrgency.HIGH: 5,
            ThreatUrgency.CRITICAL: 2,
        }
        estimated_time = time_per_tx[urgency] * estimated_transactions
        
        plan = EvacuationPlan(
            source_wallet=source_wallet,
            destination_wallet=destination_wallet,
            urgency=urgency,
            assets=assets,
            total_value_usd=sum(a.value_usd for a in assets),
            approvals_to_revoke=approvals_to_revoke,
            estimated_transactions=estimated_transactions,
            estimated_fee_sol=estimated_fee_sol,
            estimated_time_seconds=estimated_time,
            priority_fee_lamports=priority_fee,
            use_jito_bundles=urgency == ThreatUrgency.CRITICAL,
        )
        
        self.log.info(
            f"📋 Evacuation plan ready: {len(assets)} assets, "
            f"${plan.total_value_usd:.2f} value, "
            f"~{estimated_time}s estimated"
        )
        
        return plan
    
    # =========================================================================
    # Evacuation Execution
    # =========================================================================
    
    async def execute_evacuation(
        self,
        plan: EvacuationPlan,
        dry_run: bool = False,
    ) -> EvacuationResult:
        """
        Execute an evacuation plan.
        
        Args:
            plan: The evacuation plan to execute
            dry_run: If True, simulate without sending transactions
        
        Returns:
            EvacuationResult with complete details
        """
        evacuation_id = f"EVAC-{int(datetime.now().timestamp())}"
        
        self.log.info(f"🚨 EXECUTING EVACUATION {evacuation_id}")
        self.log.info(f"   Source: {plan.source_wallet[:16]}...")
        self.log.info(f"   Destination: {plan.destination_wallet[:16]}...")
        self.log.info(f"   Assets: {len(plan.assets)}")
        self.log.info(f"   Value: ${plan.total_value_usd:.2f}")
        self.log.info(f"   Urgency: {plan.urgency.value}")
        
        if dry_run:
            self.log.info("   [DRY RUN - No transactions will be sent]")
        
        started_at = datetime.now(timezone.utc)
        
        result = EvacuationResult(
            plan=plan,
            status=EvacuationStatus.IN_PROGRESS,
            assets_evacuated=[],
            assets_failed=[],
            approvals_revoked=[],
            approvals_failed=[],
            total_evacuated_usd=0.0,
            total_failed_usd=0.0,
            transactions_sent=0,
            transactions_confirmed=0,
            started_at=started_at,
            completed_at=None,
            duration_seconds=0,
            errors=[],
        )
        
        self.active_evacuations[evacuation_id] = result
        
        try:
            # Step 1: Revoke dangerous approvals first (so attacker can't use them)
            if plan.approvals_to_revoke:
                self.log.info(f"🔐 Revoking {len(plan.approvals_to_revoke)} approvals...")
                for approval in plan.approvals_to_revoke:
                    try:
                        if not dry_run:
                            await self._revoke_approval(
                                plan.source_wallet,
                                approval,
                                plan.priority_fee_lamports
                            )
                        result.approvals_revoked.append(approval.token_mint)
                        result.transactions_sent += 1
                        result.transactions_confirmed += 1
                        self.log.info(f"   ✅ Revoked: {approval.token_symbol}")
                    except Exception as e:
                        result.approvals_failed.append(approval.token_mint)
                        result.errors.append(f"Failed to revoke {approval.token_symbol}: {str(e)}")
                        self.log.error(f"   ❌ Failed to revoke {approval.token_symbol}", error=str(e))
            
            # Step 2: Transfer tokens (before SOL, as we need SOL for fees)
            token_assets = [a for a in plan.assets if a.asset_type != AssetType.SOL]
            if token_assets:
                self.log.info(f"💸 Transferring {len(token_assets)} tokens...")
                for asset in token_assets:
                    try:
                        if not dry_run:
                            await self._transfer_token(
                                plan.source_wallet,
                                plan.destination_wallet,
                                asset,
                                plan.priority_fee_lamports
                            )
                        result.assets_evacuated.append(self._asset_to_dict(asset))
                        result.total_evacuated_usd += asset.value_usd
                        result.transactions_sent += 1
                        result.transactions_confirmed += 1
                        self.log.info(f"   ✅ Sent: {asset.balance} {asset.symbol} (${asset.value_usd:.2f})")
                    except Exception as e:
                        result.assets_failed.append(self._asset_to_dict(asset))
                        result.total_failed_usd += asset.value_usd
                        result.errors.append(f"Failed to transfer {asset.symbol}: {str(e)}")
                        self.log.error(f"   ❌ Failed: {asset.symbol}", error=str(e))
            
            # Step 3: Transfer SOL (leave minimum for rent)
            sol_assets = [a for a in plan.assets if a.asset_type == AssetType.SOL]
            if sol_assets:
                sol_asset = sol_assets[0]
                transfer_amount = max(0, sol_asset.balance - self.min_sol_reserve)
                
                if transfer_amount > 0:
                    self.log.info(f"💰 Transferring {transfer_amount:.4f} SOL...")
                    try:
                        if not dry_run:
                            await self._transfer_sol(
                                plan.source_wallet,
                                plan.destination_wallet,
                                transfer_amount,
                                plan.priority_fee_lamports
                            )
                        
                        evacuated_sol = WalletAsset(
                            asset_type=AssetType.SOL,
                            mint=None,
                            symbol="SOL",
                            balance=transfer_amount,
                            decimals=9,
                            value_usd=transfer_amount * await self._get_sol_price(),
                        )
                        result.assets_evacuated.append(self._asset_to_dict(evacuated_sol))
                        result.total_evacuated_usd += evacuated_sol.value_usd
                        result.transactions_sent += 1
                        result.transactions_confirmed += 1
                        self.log.info(f"   ✅ Sent: {transfer_amount:.4f} SOL")
                    except Exception as e:
                        result.assets_failed.append(self._asset_to_dict(sol_asset))
                        result.total_failed_usd += sol_asset.value_usd
                        result.errors.append(f"Failed to transfer SOL: {str(e)}")
                        self.log.error(f"   ❌ Failed to transfer SOL", error=str(e))
            
            # Determine final status
            if not result.errors:
                result.status = EvacuationStatus.COMPLETED
            elif result.assets_evacuated:
                result.status = EvacuationStatus.PARTIAL
            else:
                result.status = EvacuationStatus.FAILED
            
        except Exception as e:
            result.status = EvacuationStatus.FAILED
            result.errors.append(f"Evacuation failed: {str(e)}")
            self.log.error(f"🚨 Evacuation failed", error=str(e))
        
        # Finalize
        result.completed_at = datetime.now(timezone.utc)
        result.duration_seconds = (result.completed_at - result.started_at).total_seconds()
        
        # Update stats
        if result.status in (EvacuationStatus.COMPLETED, EvacuationStatus.PARTIAL):
            self.stats["evacuations_completed"] += 1
            self.stats["total_value_saved_usd"] += result.total_evacuated_usd
            self.stats["total_assets_moved"] += len(result.assets_evacuated)
            self.stats["approvals_revoked"] += len(result.approvals_revoked)
        else:
            self.stats["evacuations_failed"] += 1
        
        # Move to history
        del self.active_evacuations[evacuation_id]
        self.evacuation_history.append(result)
        
        self.log.info(f"🏁 Evacuation {evacuation_id} {result.status.value}")
        self.log.info(f"   Evacuated: ${result.total_evacuated_usd:.2f}")
        self.log.info(f"   Duration: {result.duration_seconds:.1f}s")
        
        return result
    
    async def _revoke_approval(
        self,
        wallet: str,
        approval: DangerousApproval,
        priority_fee: int
    ):
        """Revoke a token approval"""
        # In production, this builds and sends a revoke transaction
        # For SPL tokens, this means setting delegate to None
        self.log.debug(f"Revoking approval for {approval.token_symbol}")
        await asyncio.sleep(0.1)  # Simulate tx time
    
    async def _transfer_token(
        self,
        source: str,
        destination: str,
        asset: WalletAsset,
        priority_fee: int
    ):
        """Transfer an SPL token"""
        # In production, this builds and sends a token transfer
        self.log.debug(f"Transferring {asset.balance} {asset.symbol}")
        await asyncio.sleep(0.1)  # Simulate tx time
    
    async def _transfer_sol(
        self,
        source: str,
        destination: str,
        amount: float,
        priority_fee: int
    ):
        """Transfer SOL"""
        # In production, this builds and sends a SOL transfer
        self.log.debug(f"Transferring {amount} SOL")
        await asyncio.sleep(0.1)  # Simulate tx time
    
    # =========================================================================
    # Quick Evacuation (One-Click Emergency)
    # =========================================================================
    
    async def emergency_evacuate(
        self,
        source_wallet: str,
        destination_wallet: Optional[str] = None,
    ) -> EvacuationResult:
        """
        🚨 ONE-CLICK EMERGENCY EVACUATION
        
        Maximum urgency, maximum priority fees, no confirmation needed.
        Use when your wallet is actively being drained.
        
        Args:
            source_wallet: Wallet under attack
            destination_wallet: Where to send funds
        
        Returns:
            EvacuationResult
        """
        self.log.warning(f"🚨🚨🚨 EMERGENCY EVACUATION INITIATED 🚨🚨🚨")
        
        plan = await self.create_evacuation_plan(
            source_wallet=source_wallet,
            destination_wallet=destination_wallet,
            urgency=ThreatUrgency.CRITICAL,
            include_nfts=True,
            revoke_approvals=True,
        )
        
        return await self.execute_evacuation(plan, dry_run=False)
    
    # =========================================================================
    # Threat Detection Integration
    # =========================================================================
    
    async def assess_threat(self, wallet: str) -> Dict[str, Any]:
        """
        Assess if a wallet needs evacuation.
        
        Checks for:
        - Recent suspicious transactions
        - Dangerous approvals
        - Signs of drainer activity
        """
        self.log.info(f"🔍 Assessing threat level for {wallet[:16]}...")
        
        analysis = await self.analyze_wallet(wallet)
        
        threat_indicators = []
        urgency = ThreatUrgency.LOW
        
        # Check for dangerous approvals
        high_risk_approvals = [
            a for a in analysis.get("approvals", [])
            if a.get("risk_level") in ("high", "critical")
        ]
        
        if high_risk_approvals:
            threat_indicators.append(f"{len(high_risk_approvals)} high-risk approvals detected")
            urgency = ThreatUrgency.MEDIUM
        
        # Check for known malicious program interactions
        # Would check recent transactions in production
        
        # Build recommendation
        recommendation = "safe"
        if urgency == ThreatUrgency.CRITICAL:
            recommendation = "immediate_evacuation"
        elif urgency == ThreatUrgency.HIGH:
            recommendation = "urgent_evacuation"
        elif urgency == ThreatUrgency.MEDIUM:
            recommendation = "consider_evacuation"
        elif high_risk_approvals:
            recommendation = "revoke_approvals"
        
        return {
            "wallet": wallet,
            "urgency": urgency.value,
            "risk_score": analysis.get("risk_score", 0),
            "threat_indicators": threat_indicators,
            "recommendation": recommendation,
            "approvals_at_risk": len(high_risk_approvals),
            "total_value_usd": analysis.get("total_value_usd", 0),
            "assessed_at": datetime.now(timezone.utc).isoformat(),
        }
    
    # =========================================================================
    # Stats and Reporting
    # =========================================================================
    
    def get_stats(self) -> Dict:
        """Get evacuator statistics"""
        return {
            **self.stats,
            "active_evacuations": len(self.active_evacuations),
            "registered_safe_wallets": sum(len(w) for w in self.safe_wallets.values()),
        }
    
    def get_evacuation_history(self, limit: int = 10) -> List[Dict]:
        """Get recent evacuation history"""
        history = []
        for result in self.evacuation_history[-limit:]:
            history.append({
                "source": result.plan.source_wallet,
                "destination": result.plan.destination_wallet,
                "status": result.status.value,
                "value_evacuated": result.total_evacuated_usd,
                "assets_moved": len(result.assets_evacuated),
                "duration_seconds": result.duration_seconds,
                "completed_at": result.completed_at.isoformat() if result.completed_at else None,
            })
        return history


# =========================================================================
# Convenience Functions
# =========================================================================

_evacuator_instance: Optional[EvacuatorAgent] = None


def get_evacuator() -> EvacuatorAgent:
    """Get or create Evacuator singleton"""
    global _evacuator_instance
    if _evacuator_instance is None:
        _evacuator_instance = EvacuatorAgent()
    return _evacuator_instance


async def emergency_evacuate(
    source_wallet: str,
    destination_wallet: str,
) -> EvacuationResult:
    """
    🚨 Quick emergency evacuation function.
    
    Usage:
        result = await emergency_evacuate(
            source_wallet="compromised_wallet_address",
            destination_wallet="safe_wallet_address"
        )
        
        if result.status == EvacuationStatus.COMPLETED:
            print(f"Saved ${result.total_evacuated_usd:.2f}!")
    """
    evacuator = get_evacuator()
    return await evacuator.emergency_evacuate(source_wallet, destination_wallet)
