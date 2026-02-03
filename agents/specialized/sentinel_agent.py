"""
SENTINEL Agent - Transaction Monitoring
Watches for suspicious transaction patterns, whale movements, and unusual transfers
"""
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional

import httpx
from solana.rpc.types import MemcmpOpts
from solders.pubkey import Pubkey

from ..core.base_agent import AutonomousAgent, Threat, Decision
from ..core.config import AgentConfig, config


class SentinelAgent(AutonomousAgent):
    """
    SENTINEL - The Watchman
    
    Monitors Solana transactions and wallets for suspicious activity:
    - Large sudden transfers
    - Known scammer wallet activity
    - Unusual transaction patterns
    - Whale movements that could indicate dumps
    - Draining transactions
    """
    
    def __init__(self, config: AgentConfig = config):
        super().__init__(
            role="SENTINEL",
            agent_type="Sentinel",
            capabilities=[
                "transaction_monitoring",
                "wallet_tracking",
                "pattern_detection",
                "whale_alerts"
            ],
            config=config
        )
        
        # Monitored addresses (known high-value wallets, exchanges, etc.)
        self.monitored_addresses: List[str] = []
        
        # Suspicious patterns
        self.suspicious_patterns = {
            "large_transfer_threshold_sol": 1000,  # Alert on transfers > 1000 SOL
            "rapid_tx_count_threshold": 50,  # Alert on > 50 tx in 5 min
            "new_token_interaction_threshold": 10,  # Alert on wallet interacting with > 10 new tokens
        }
        
        # Known scammer addresses (populated from Intel agent)
        self.blacklisted_addresses: set = set()
        
        # Helius webhook URL for real-time monitoring
        self.helius_api_url = f"https://api.helius.xyz/v0"
        self.helius_api_key = config.helius_api_key
        
        self.log.info("🔭 Sentinel watching the chain...")
    
    async def scan_environment(self) -> List[Threat]:
        """Monitor transactions and wallets for suspicious activity"""
        threats = []
        
        try:
            # Get recent transactions via Helius
            recent_txs = await self.get_recent_transactions()
            
            for tx in recent_txs:
                threat = await self.analyze_transaction(tx)
                if threat:
                    threats.append(threat)
            
            # Check for whale movements
            whale_threats = await self.check_whale_movements()
            threats.extend(whale_threats)
            
            # Check blacklisted addresses
            blacklist_threats = await self.check_blacklisted_activity()
            threats.extend(blacklist_threats)
            
        except Exception as e:
            self.log.error(f"Error scanning environment", error=str(e))
        
        return threats
    
    async def get_recent_transactions(self) -> List[Dict]:
        """Fetch recent transactions via Helius Enhanced API"""
        
        async with httpx.AsyncClient() as client:
            try:
                # Get recent parsed transactions
                response = await client.get(
                    f"{self.helius_api_url}/addresses/signatures",
                    params={
                        "api-key": self.helius_api_key,
                        "limit": 100
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    self.log.warning(f"Helius API returned {response.status_code}")
                    return []
                    
            except Exception as e:
                self.log.error(f"Error fetching transactions", error=str(e))
                return []
    
    async def analyze_transaction(self, tx: Dict) -> Optional[Threat]:
        """Analyze a single transaction for suspicious patterns"""
        
        # Check for large transfers
        if tx.get("lamports", 0) > self.suspicious_patterns["large_transfer_threshold_sol"] * 1_000_000_000:
            return Threat(
                id=self.get_next_threat_id(),
                threat_type="SuspiciousTransfer",
                severity=60,
                target_address=tx.get("to"),
                description=f"Large transfer detected: {tx.get('lamports', 0) / 1_000_000_000:.2f} SOL",
                evidence={
                    "signature": tx.get("signature"),
                    "from": tx.get("from"),
                    "to": tx.get("to"),
                    "amount_sol": tx.get("lamports", 0) / 1_000_000_000
                },
                detected_by="Sentinel"
            )
        
        # Check for interaction with blacklisted addresses
        if tx.get("to") in self.blacklisted_addresses or tx.get("from") in self.blacklisted_addresses:
            return Threat(
                id=self.get_next_threat_id(),
                threat_type="BlacklistedInteraction",
                severity=90,
                target_address=tx.get("to") if tx.get("to") in self.blacklisted_addresses else tx.get("from"),
                description="Transaction with known malicious address detected",
                evidence={
                    "signature": tx.get("signature"),
                    "from": tx.get("from"),
                    "to": tx.get("to"),
                    "blacklisted_address": tx.get("to") if tx.get("to") in self.blacklisted_addresses else tx.get("from")
                },
                detected_by="Sentinel"
            )
        
        return None
    
    async def check_whale_movements(self) -> List[Threat]:
        """Monitor whale wallets for large movements"""
        threats = []
        
        # Get top token holders and monitor for dumps
        # This would integrate with Helius or DAS API
        # Placeholder for whale monitoring logic
        
        return threats
    
    async def check_blacklisted_activity(self) -> List[Threat]:
        """Check for activity from known malicious addresses"""
        threats = []
        
        for address in list(self.blacklisted_addresses)[:10]:  # Check first 10
            try:
                response = await self.solana.get_signatures_for_address(
                    Pubkey.from_string(address),
                    limit=5
                )
                
                if response.value:
                    recent_sig = response.value[0]
                    # Check if recent activity (within last hour)
                    # For now, just log
                    self.log.debug(f"Blacklisted address {address[:8]}... has recent activity")
                    
            except Exception as e:
                self.log.warning(f"Error checking blacklisted address", address=address[:8], error=str(e))
        
        return threats
    
    async def execute_action(self, decision: Decision, threat: Threat) -> Dict[str, Any]:
        """Execute Sentinel-specific actions"""
        
        result = {"status": "success", "action": decision.action}
        
        if decision.action == "WARN":
            # Alert the community via Reporter agent
            reporter = next((a for a in self.other_agents if a.agent_type == "Reporter"), None)
            if reporter:
                await reporter.send_alert(threat, decision.reasoning)
                result["alert_sent"] = True
            
        elif decision.action == "BLOCK":
            # Add to watchlist and notify Intel agent
            intel = next((a for a in self.other_agents if a.agent_type == "Intel"), None)
            if intel and threat.target_address:
                await intel.add_to_watchlist(threat.target_address, threat.description)
                result["added_to_watchlist"] = True
        
        elif decision.action == "MONITOR":
            # Add address to monitored list
            if threat.target_address:
                self.monitored_addresses.append(threat.target_address)
                result["monitoring_started"] = True
        
        return result
    
    def add_to_blacklist(self, address: str):
        """Add an address to the blacklist"""
        self.blacklisted_addresses.add(address)
        self.log.info(f"Added {address[:8]}... to blacklist")
    
    def remove_from_blacklist(self, address: str):
        """Remove an address from the blacklist"""
        self.blacklisted_addresses.discard(address)
        self.log.info(f"Removed {address[:8]}... from blacklist")
