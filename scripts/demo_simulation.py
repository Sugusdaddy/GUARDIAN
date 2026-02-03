#!/usr/bin/env python3
"""
GUARDIAN Demo Simulation
Simulates various threat scenarios to demonstrate the system
"""
import asyncio
import random
import sys
import os
from datetime import datetime
from pathlib import Path

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))

# Import only what we need for simulation
from core.database import get_db

# Try to import scorer, fallback to simple scoring
try:
    from core.embeddings import get_scorer
    HAS_SCORER = True
except ImportError:
    HAS_SCORER = False
    def get_scorer():
        return None

# Simulated addresses
ADDRESSES = [
    "SimAddr1" + "x" * 36,
    "SimAddr2" + "y" * 36,
    "SimAddr3" + "z" * 36,
    "ScamWallet" + "a" * 35,
    "DrainerBot" + "b" * 35,
    "WhaleAccnt" + "c" * 35,
    "LegitUser1" + "d" * 35,
    "NewToken00" + "e" * 35,
]

# Threat templates
THREAT_TEMPLATES = [
    {
        "threat_type": "Rugpull",
        "severity_range": (70, 95),
        "description": "Potential rugpull detected: {address} - Liquidity removal pattern identified",
        "evidence_template": {
            "liquidity_removed_pct": None,
            "time_since_launch_hours": None,
            "holder_concentration": None
        }
    },
    {
        "threat_type": "Honeypot",
        "severity_range": (60, 90),
        "description": "Honeypot token detected: {address} - Sell function disabled or restricted",
        "evidence_template": {
            "buy_tax": None,
            "sell_tax": None,
            "sell_disabled": True,
            "contract_verified": False
        }
    },
    {
        "threat_type": "Drainer",
        "severity_range": (85, 100),
        "description": "Wallet drainer contract: {address} - SetApprovalForAll detected in transaction",
        "evidence_template": {
            "approval_type": "setApprovalForAll",
            "target_collection": None,
            "suspicious_functions": ["transferFrom", "safeTransferFrom"]
        }
    },
    {
        "threat_type": "SuspiciousTransfer",
        "severity_range": (40, 70),
        "description": "Large suspicious transfer: {amount:.2f} SOL from {address}",
        "evidence_template": {
            "amount_sol": None,
            "destination": None,
            "previous_activity": "minimal"
        }
    },
    {
        "threat_type": "Sandwich",
        "severity_range": (50, 80),
        "description": "Sandwich attack detected targeting {address}",
        "evidence_template": {
            "frontrun_tx": None,
            "victim_tx": None,
            "backrun_tx": None,
            "profit_usd": None
        }
    },
    {
        "threat_type": "FlashLoan",
        "severity_range": (65, 95),
        "description": "Flash loan attack in progress: {address} - Unusual borrow/repay pattern",
        "evidence_template": {
            "borrowed_amount_usd": None,
            "protocols_affected": [],
            "price_impact_pct": None
        }
    },
    {
        "threat_type": "OracleManipulation",
        "severity_range": (75, 95),
        "description": "Oracle price manipulation attempt: {address} targeting {protocol}",
        "evidence_template": {
            "oracle_address": None,
            "price_deviation_pct": None,
            "protocol_affected": None
        }
    },
    {
        "threat_type": "BlacklistedInteraction",
        "severity_range": (80, 100),
        "description": "Interaction with known malicious address: {address}",
        "evidence_template": {
            "blacklisted_address": None,
            "interaction_type": "transfer",
            "historical_victims": None
        }
    }
]

AGENTS = ["Sentinel", "Scanner", "Oracle", "Hunter", "Guardian", "Intel"]


def generate_threat():
    """Generate a random simulated threat"""
    template = random.choice(THREAT_TEMPLATES)
    address = random.choice(ADDRESSES)
    
    severity = random.uniform(*template["severity_range"])
    
    # Fill in evidence
    evidence = template["evidence_template"].copy()
    for key in evidence:
        if evidence[key] is None:
            if "amount" in key or "pct" in key:
                evidence[key] = random.uniform(10, 1000)
            elif "address" in key or "tx" in key:
                evidence[key] = "Sim" + "".join(random.choices("abcdef0123456789", k=40))
            elif isinstance(evidence[key], list):
                evidence[key] = ["simulated_data"]
            else:
                evidence[key] = random.randint(1, 100)
    
    # Format description
    description = template["description"].format(
        address=address[:16] + "...",
        amount=random.uniform(100, 10000),
        protocol="SimProtocol"
    )
    
    return {
        "threat_type": template["threat_type"],
        "severity": severity,
        "target_address": address,
        "description": description,
        "evidence": evidence,
        "detected_by": random.choice(AGENTS)
    }


def generate_blacklist_entry():
    """Generate a random blacklist entry"""
    reasons = [
        "Known scammer - multiple rugpulls",
        "Drainer contract deployer",
        "Phishing site operator",
        "Sandwich bot operator",
        "Flash loan attacker",
    ]
    
    return {
        "address": "Blacklisted" + "".join(random.choices("0123456789abcdef", k=36)),
        "reason": random.choice(reasons),
        "severity": random.randint(70, 100)
    }


async def run_simulation(
    num_threats: int = 20,
    num_blacklist: int = 5,
    interval: float = 0.5,
    live: bool = False
):
    """Run threat simulation"""
    db = get_db()
    scorer = get_scorer()
    
    print("\n" + "="*60)
    print("   GUARDIAN Demo Simulation")
    print("="*60 + "\n")
    
    # Add blacklist entries
    print(f"📝 Adding {num_blacklist} blacklist entries...")
    for _ in range(num_blacklist):
        entry = generate_blacklist_entry()
        db.add_to_blacklist(entry["address"], entry["reason"], "Simulation", entry["severity"])
    
    blacklist = set(b["address"] for b in db.get_blacklist())
    patterns = db.get_patterns(min_confidence=0.3)
    
    print(f"\n🚨 Generating {num_threats} simulated threats...\n")
    
    for i in range(num_threats):
        threat = generate_threat()
        
        # Score the threat
        if scorer:
            score_result = scorer.score_threat(threat, blacklist, patterns)
            threat["severity"] = score_result["final_score"]  # Use ML-enhanced score
        else:
            # Simple scoring without ML
            score_result = {
                "final_score": threat["severity"],
                "recommendation": "WARN" if threat["severity"] > 60 else "MONITOR"
            }
        
        # Insert into database
        threat_id = db.insert_threat(threat)
        
        # Display
        sev = threat["severity"]
        sev_color = "\033[91m" if sev >= 70 else "\033[93m" if sev >= 40 else "\033[92m"
        reset = "\033[0m"
        
        print(f"  [{i+1:3d}] {threat['threat_type']:20s} | "
              f"Severity: {sev_color}{sev:5.1f}{reset} | "
              f"Rec: {score_result['recommendation']:10s} | "
              f"By: {threat['detected_by']}")
        
        if live:
            await asyncio.sleep(interval)
    
    # Summary
    stats = db.get_threat_stats()
    
    print("\n" + "="*60)
    print("   Simulation Complete")
    print("="*60)
    print(f"""
    Total Threats: {sum(stats.get('by_status', {}).values())}
    By Type:
""")
    for threat_type, count in stats.get("by_type", {}).items():
        print(f"      {threat_type}: {count}")
    
    print(f"""
    Avg Severity: {stats.get('avg_severity', 0):.1f}
    Blacklisted Addresses: {len(blacklist)}
    
    Run 'python cli.py' to explore the data
    Run 'python app/api/main.py' to start the dashboard
    """)


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="GUARDIAN Demo Simulation")
    parser.add_argument("-n", "--num-threats", type=int, default=20, help="Number of threats to simulate")
    parser.add_argument("-b", "--num-blacklist", type=int, default=5, help="Number of blacklist entries")
    parser.add_argument("-i", "--interval", type=float, default=0.1, help="Interval between threats (seconds)")
    parser.add_argument("--live", action="store_true", help="Simulate in real-time with delays")
    
    args = parser.parse_args()
    
    await run_simulation(
        num_threats=args.num_threats,
        num_blacklist=args.num_blacklist,
        interval=args.interval,
        live=args.live
    )


if __name__ == "__main__":
    asyncio.run(main())
