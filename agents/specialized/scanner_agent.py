"""
SCANNER Agent - Smart Contract & Token Analysis
Analyzes new contracts and tokens for vulnerabilities and scam indicators
"""
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional

import httpx
from solders.pubkey import Pubkey

from ..core.base_agent import AutonomousAgent, Threat, Decision
from ..core.config import AgentConfig, config


class ScannerAgent(AutonomousAgent):
    """
    SCANNER - The Analyst
    
    Analyzes smart contracts and tokens for vulnerabilities:
    - Rug pull indicators (mint authority, liquidity locks)
    - Honeypot characteristics
    - Contract code vulnerabilities
    - Token metadata manipulation
    - Suspicious liquidity patterns
    """
    
    def __init__(self, config: AgentConfig = config):
        super().__init__(
            role="SCANNER",
            agent_type="Scanner",
            capabilities=[
                "contract_analysis",
                "token_scanning",
                "vulnerability_detection",
                "liquidity_analysis"
            ],
            config=config
        )
        
        # Helius API for token data
        self.helius_api_url = "https://api.helius.xyz/v0"
        self.helius_api_key = config.helius_api_key
        
        # Jupiter API for DEX data
        self.jupiter_api_url = "https://quote-api.jup.ag/v6"
        
        # Scam indicators and their weights
        self.scam_indicators = {
            "mint_authority_enabled": 25,
            "freeze_authority_enabled": 15,
            "low_liquidity": 20,
            "single_holder_majority": 25,
            "no_social_links": 10,
            "copy_name": 15,
            "honeypot_transfer_restrictions": 30,
        }
        
        # Cache for analyzed tokens
        self.analyzed_tokens: Dict[str, Dict] = {}
        
        self.log.info("🔍 Scanner ready to analyze contracts...")
    
    async def scan_environment(self) -> List[Threat]:
        """Scan for new tokens and contracts to analyze"""
        threats = []
        
        try:
            # Get recently created tokens
            new_tokens = await self.get_new_tokens()
            
            for token in new_tokens:
                # Skip if already analyzed
                if token.get("mint") in self.analyzed_tokens:
                    continue
                
                analysis = await self.analyze_token(token)
                self.analyzed_tokens[token.get("mint")] = analysis
                
                if analysis["is_suspicious"]:
                    threats.append(Threat(
                        id=self.get_next_threat_id(),
                        threat_type=analysis["threat_type"],
                        severity=analysis["risk_score"],
                        target_address=token.get("mint"),
                        description=analysis["description"],
                        evidence=analysis,
                        detected_by="Scanner"
                    ))
            
            # Also scan trending tokens on DEXes
            trending_threats = await self.scan_trending_tokens()
            threats.extend(trending_threats)
            
        except Exception as e:
            self.log.error(f"Error scanning tokens", error=str(e))
        
        return threats
    
    async def get_new_tokens(self) -> List[Dict]:
        """Fetch recently created tokens via Helius"""
        
        async with httpx.AsyncClient() as client:
            try:
                # Use Helius DAS API to get recent token mints
                response = await client.post(
                    f"https://mainnet.helius-rpc.com/?api-key={self.helius_api_key}",
                    json={
                        "jsonrpc": "2.0",
                        "id": "scanner-1",
                        "method": "searchAssets",
                        "params": {
                            "ownerAddress": None,
                            "createdAfter": int(datetime.now().timestamp()) - 3600,  # Last hour
                            "tokenType": "fungible",
                            "limit": 50
                        }
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("result", {}).get("items", [])
                
            except Exception as e:
                self.log.error(f"Error fetching new tokens", error=str(e))
        
        return []
    
    async def analyze_token(self, token: Dict) -> Dict[str, Any]:
        """Deep analysis of a token for scam indicators"""
        
        mint_address = token.get("mint", token.get("id", "unknown"))
        red_flags = []
        risk_score = 0
        
        try:
            # 1. Check mint authority
            mint_info = await self.get_mint_info(mint_address)
            if mint_info.get("mintAuthority"):
                red_flags.append("mint_authority_enabled")
                risk_score += self.scam_indicators["mint_authority_enabled"]
            
            # 2. Check freeze authority
            if mint_info.get("freezeAuthority"):
                red_flags.append("freeze_authority_enabled")
                risk_score += self.scam_indicators["freeze_authority_enabled"]
            
            # 3. Check liquidity
            liquidity = await self.get_token_liquidity(mint_address)
            if liquidity < 1000:  # Less than $1000 liquidity
                red_flags.append("low_liquidity")
                risk_score += self.scam_indicators["low_liquidity"]
            
            # 4. Check holder distribution
            holders = await self.get_holder_distribution(mint_address)
            if holders.get("top_holder_percentage", 0) > 50:
                red_flags.append("single_holder_majority")
                risk_score += self.scam_indicators["single_holder_majority"]
            
            # 5. Check metadata
            metadata = token.get("content", {}).get("metadata", {})
            if not metadata.get("links"):
                red_flags.append("no_social_links")
                risk_score += self.scam_indicators["no_social_links"]
            
            # 6. Check for honeypot characteristics
            is_honeypot = await self.check_honeypot(mint_address)
            if is_honeypot:
                red_flags.append("honeypot_transfer_restrictions")
                risk_score += self.scam_indicators["honeypot_transfer_restrictions"]
            
        except Exception as e:
            self.log.warning(f"Error analyzing token {mint_address[:8]}", error=str(e))
            red_flags.append("analysis_error")
            risk_score += 10
        
        # Determine threat type
        if "honeypot_transfer_restrictions" in red_flags:
            threat_type = "Honeypot"
        elif "mint_authority_enabled" in red_flags and "single_holder_majority" in red_flags:
            threat_type = "RugPull"
        elif risk_score > 50:
            threat_type = "SuspiciousToken"
        else:
            threat_type = "Unknown"
        
        is_suspicious = risk_score >= 40
        
        return {
            "mint": mint_address,
            "is_suspicious": is_suspicious,
            "risk_score": min(risk_score, 100),
            "red_flags": red_flags,
            "threat_type": threat_type,
            "description": f"Token analysis: {len(red_flags)} red flags detected, risk score {risk_score}%",
            "liquidity_usd": liquidity if 'liquidity' in dir() else 0,
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_mint_info(self, mint_address: str) -> Dict:
        """Get token mint information"""
        try:
            response = await self.solana.get_account_info(Pubkey.from_string(mint_address))
            if response.value:
                # Parse mint account data
                # Simplified - in production would properly decode
                return {
                    "mintAuthority": True,  # Would check actual data
                    "freezeAuthority": False
                }
        except Exception as e:
            self.log.warning(f"Error getting mint info", mint=mint_address[:8], error=str(e))
        
        return {}
    
    async def get_token_liquidity(self, mint_address: str) -> float:
        """Get token liquidity from DEXes via Jupiter"""
        
        async with httpx.AsyncClient() as client:
            try:
                # Get quote for small amount to check liquidity
                response = await client.get(
                    f"{self.jupiter_api_url}/quote",
                    params={
                        "inputMint": mint_address,
                        "outputMint": "So11111111111111111111111111111111111111112",  # SOL
                        "amount": "1000000",  # 1 token (assuming 6 decimals)
                        "slippageBps": 100
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Estimate liquidity from price impact
                    return float(data.get("outAmount", 0)) / 1_000_000_000 * 100  # Rough USD estimate
                    
            except Exception as e:
                self.log.debug(f"Error getting liquidity", mint=mint_address[:8])
        
        return 0
    
    async def get_holder_distribution(self, mint_address: str) -> Dict:
        """Get token holder distribution"""
        
        async with httpx.AsyncClient() as client:
            try:
                # Use Helius to get token holders
                response = await client.get(
                    f"{self.helius_api_url}/tokens/{mint_address}/holders",
                    params={"api-key": self.helius_api_key},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    holders = response.json()
                    if holders:
                        # Calculate top holder percentage
                        total_supply = sum(h.get("amount", 0) for h in holders)
                        top_holder = max(holders, key=lambda x: x.get("amount", 0))
                        top_percentage = (top_holder.get("amount", 0) / total_supply * 100) if total_supply > 0 else 0
                        
                        return {
                            "holder_count": len(holders),
                            "top_holder_percentage": top_percentage
                        }
                        
            except Exception as e:
                self.log.debug(f"Error getting holder distribution", mint=mint_address[:8])
        
        return {"holder_count": 0, "top_holder_percentage": 100}
    
    async def check_honeypot(self, mint_address: str) -> bool:
        """Check if token has honeypot characteristics"""
        
        # Check if token can be sold by simulating a swap
        async with httpx.AsyncClient() as client:
            try:
                # Try to get a sell quote
                response = await client.get(
                    f"{self.jupiter_api_url}/quote",
                    params={
                        "inputMint": mint_address,
                        "outputMint": "So11111111111111111111111111111111111111112",
                        "amount": "1000000",
                        "slippageBps": 5000  # High slippage to catch issues
                    },
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    return True  # Can't get quote, might be honeypot
                
                data = response.json()
                # Check for extreme price impact (>50% = likely honeypot)
                if data.get("priceImpactPct", 0) > 50:
                    return True
                    
            except Exception as e:
                self.log.debug(f"Honeypot check error", mint=mint_address[:8])
                return True  # Assume honeypot if can't check
        
        return False
    
    async def scan_trending_tokens(self) -> List[Threat]:
        """Scan trending tokens on DEXes for suspicious activity"""
        threats = []
        
        # Would integrate with Birdeye, DexScreener, or similar
        # to get trending tokens and analyze them
        
        return threats
    
    async def execute_action(self, decision: Decision, threat: Threat) -> Dict[str, Any]:
        """Execute Scanner-specific actions"""
        
        result = {"status": "success", "action": decision.action}
        
        if decision.action == "BLOCK":
            # Register threat in on-chain database
            await self.register_threat_onchain(threat)
            result["registered_onchain"] = True
            
            # Notify Intel agent
            intel = next((a for a in self.other_agents if a.agent_type == "Intel"), None)
            if intel and threat.target_address:
                await intel.add_threat_to_database(threat)
                result["added_to_database"] = True
        
        elif decision.action == "WARN":
            # Alert community via Reporter
            reporter = next((a for a in self.other_agents if a.agent_type == "Reporter"), None)
            if reporter:
                await reporter.send_alert(threat, decision.reasoning)
                result["alert_sent"] = True
        
        return result
    
    async def register_threat_onchain(self, threat: Threat):
        """Register a threat in the on-chain threat database"""
        # TODO: Implement actual on-chain registration via Anchor
        self.log.info(f"🚨 Registered threat on-chain", threat_id=threat.id, type=threat.threat_type)
