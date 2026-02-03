"""
HUNTER Agent - Malicious Actor Tracking & Attribution
Tracks and identifies malicious actors across the blockchain
"""
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, Set

import httpx
from solders.pubkey import Pubkey

from ..core.base_agent import AutonomousAgent, Threat, Decision
from ..core.config import AgentConfig, config


class HunterAgent(AutonomousAgent):
    """
    HUNTER - The Tracker
    
    Tracks malicious actors and their operations:
    - Follows money trails
    - Identifies repeat offenders
    - Connects related scam operations
    - Builds actor profiles
    """
    
    def __init__(self, config: AgentConfig = config):
        super().__init__(
            role="HUNTER",
            agent_type="Hunter",
            capabilities=[
                "actor_tracking",
                "money_trail_analysis",
                "identity_correlation",
                "network_mapping"
            ],
            config=config
        )
        
        # Actor database
        self.known_actors: Dict[str, Dict] = {}  # actor_id -> profile
        self.address_to_actor: Dict[str, str] = {}  # address -> actor_id
        
        # Tracking state
        self.active_investigations: Dict[str, Dict] = {}
        self.completed_investigations: List[Dict] = []
        
        # Network graph (simplified)
        self.connections: Dict[str, Set[str]] = {}  # address -> connected addresses
        
        # Helius API
        self.helius_api_key = config.helius_api_key
        
        self.log.info("🔍 Hunter agent ready for tracking")
    
    async def scan_environment(self) -> List[Threat]:
        """Hunter tracks active investigations"""
        threats = []
        
        # Process active investigations
        for inv_id, investigation in list(self.active_investigations.items()):
            results = await self.continue_investigation(investigation)
            
            if results.get("new_addresses"):
                # Found new connected addresses
                for addr in results["new_addresses"]:
                    threats.append(Threat(
                        id=self.get_next_threat_id(),
                        threat_type="ConnectedMaliciousAddress",
                        severity=70,
                        target_address=addr,
                        description=f"Address connected to known scam actor {inv_id}",
                        evidence={
                            "investigation_id": inv_id,
                            "connection_path": results.get("path", [])
                        },
                        detected_by="Hunter"
                    ))
            
            if results.get("complete"):
                self.completed_investigations.append(investigation)
                del self.active_investigations[inv_id]
        
        return threats
    
    async def execute_action(self, decision: Decision, threat: Threat) -> Dict[str, Any]:
        """Execute hunter-specific actions"""
        
        result = {"status": "success", "action": decision.action}
        
        if decision.action in ["BLOCK", "COORDINATE"]:
            # Start tracking the actor
            if threat.target_address:
                inv_id = await self.start_investigation(threat.target_address, threat)
                result["investigation_started"] = inv_id
        
        return result
    
    async def start_investigation(self, address: str, threat: Threat) -> str:
        """Start a new investigation"""
        
        inv_id = f"INV-{len(self.completed_investigations) + len(self.active_investigations) + 1}"
        
        self.active_investigations[inv_id] = {
            "id": inv_id,
            "initial_address": address,
            "trigger_threat": threat.to_dict(),
            "discovered_addresses": {address},
            "transaction_graph": {},
            "started_at": datetime.now().isoformat(),
            "depth": 0,
            "max_depth": 3
        }
        
        self.log.info(f"🔍 Started investigation {inv_id} for {address[:16]}...")
        
        return inv_id
    
    async def continue_investigation(self, investigation: Dict) -> Dict:
        """Continue an active investigation"""
        
        results = {
            "new_addresses": [],
            "complete": False
        }
        
        if investigation["depth"] >= investigation["max_depth"]:
            results["complete"] = True
            return results
        
        # Get addresses to investigate this round
        addresses_to_check = list(investigation["discovered_addresses"])[:5]
        
        for address in addresses_to_check:
            # Get transaction history
            connected = await self.get_connected_addresses(address)
            
            for conn_addr in connected:
                if conn_addr not in investigation["discovered_addresses"]:
                    investigation["discovered_addresses"].add(conn_addr)
                    results["new_addresses"].append(conn_addr)
                    
                    # Update connection graph
                    if address not in self.connections:
                        self.connections[address] = set()
                    self.connections[address].add(conn_addr)
        
        investigation["depth"] += 1
        
        if not results["new_addresses"]:
            results["complete"] = True
        
        return results
    
    async def get_connected_addresses(self, address: str) -> List[str]:
        """Get addresses connected via transactions"""
        
        connected = []
        
        try:
            async with httpx.AsyncClient() as client:
                # Use Helius to get transaction history
                response = await client.get(
                    f"https://api.helius.xyz/v0/addresses/{address}/transactions",
                    params={
                        "api-key": self.helius_api_key,
                        "limit": 50
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    transactions = response.json()
                    
                    for tx in transactions:
                        # Extract connected addresses from transaction
                        if tx.get("feePayer") and tx["feePayer"] != address:
                            connected.append(tx["feePayer"])
                        
                        for account in tx.get("accountData", []):
                            acc_addr = account.get("account")
                            if acc_addr and acc_addr != address:
                                connected.append(acc_addr)
                
        except Exception as e:
            self.log.warning(f"Error getting connected addresses", error=str(e))
        
        # Deduplicate
        return list(set(connected))[:20]  # Limit to 20
    
    async def identify_actor(self, addresses: List[str]) -> Optional[str]:
        """Try to identify if addresses belong to a known actor"""
        
        for addr in addresses:
            if addr in self.address_to_actor:
                return self.address_to_actor[addr]
        
        return None
    
    async def create_actor_profile(self, inv_id: str) -> Dict:
        """Create a profile for a tracked actor"""
        
        investigation = self.active_investigations.get(inv_id) or \
                       next((i for i in self.completed_investigations if i["id"] == inv_id), None)
        
        if not investigation:
            return {}
        
        actor_id = f"ACTOR-{len(self.known_actors) + 1}"
        
        profile = {
            "actor_id": actor_id,
            "known_addresses": list(investigation["discovered_addresses"]),
            "first_seen": investigation.get("started_at"),
            "trigger_threat": investigation.get("trigger_threat", {}).get("threat_type"),
            "address_count": len(investigation["discovered_addresses"]),
            "created_at": datetime.now().isoformat()
        }
        
        # Store profile
        self.known_actors[actor_id] = profile
        
        # Map addresses to actor
        for addr in profile["known_addresses"]:
            self.address_to_actor[addr] = actor_id
        
        self.log.info(f"👤 Created actor profile {actor_id} with {profile['address_count']} addresses")
        
        return profile
    
    async def get_current_intelligence(self) -> Dict:
        """Return Hunter's current state"""
        return {
            "active_investigations": len(self.active_investigations),
            "completed_investigations": len(self.completed_investigations),
            "known_actors": len(self.known_actors),
            "tracked_addresses": len(self.address_to_actor),
            "connection_graph_size": sum(len(v) for v in self.connections.values()),
            "active": self.running,
            "capabilities": self.capabilities
        }
    
    async def propose_strategy(self, threat: Threat) -> Dict:
        """Hunter's proposal - tracking strategy"""
        
        # Check if address is already known
        known_actor = await self.identify_actor([threat.target_address] if threat.target_address else [])
        
        if known_actor:
            return {
                "agent": "Hunter",
                "strategy": f"KNOWN ACTOR: {known_actor} - expand investigation",
                "confidence": 0.9,
                "known_actor": known_actor
            }
        else:
            return {
                "agent": "Hunter",
                "strategy": "Start new investigation - trace connections",
                "confidence": 0.7,
                "known_actor": None
            }
