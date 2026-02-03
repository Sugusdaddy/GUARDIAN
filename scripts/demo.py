#!/usr/bin/env python3
"""
Solana Immune System - Demo Script
Demonstrates the autonomous multi-agent security system in action.
"""
import asyncio
import os
import sys
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agents'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


def print_banner():
    print("""
    ==============================================================
    |                                                            |
    |     SOLANA IMMUNE SYSTEM - DEMO                            |
    |                                                            |
    |     Autonomous Multi-Agent Security Infrastructure         |
    |                                                            |
    ==============================================================
    """)


async def demo_threat_detection():
    """Demonstrate threat detection flow"""
    
    print("\n" + "="*60)
    print("[DEMO 1] Simulated Threat Detection")
    print("="*60)
    
    # Simulate a suspicious token
    suspicious_token = {
        "mint": "ScamToken111111111111111111111111111111111",
        "name": "FAKE BONK",
        "symbol": "BONK",  # Copying real token name
        "indicators": {
            "mint_authority_enabled": True,
            "freeze_authority_enabled": True,
            "top_holder_percentage": 95,
            "liquidity_usd": 500,
            "age_hours": 2
        }
    }
    
    print(f"\n[!] SCANNER detected suspicious token:")
    print(f"    Mint: {suspicious_token['mint'][:20]}...")
    print(f"    Name: {suspicious_token['name']} (copying real token!)")
    print(f"    Red Flags:")
    for flag, value in suspicious_token['indicators'].items():
        print(f"      - {flag}: {value}")
    
    # Simulate Opus analysis
    print(f"\n[*] ORACLE analyzing with Claude Opus...")
    await asyncio.sleep(1)
    
    analysis = {
        "threat_score": 94,
        "threat_type": "RugPull",
        "confidence": 92,
        "reasoning": """Analysis complete:
        1. Mint authority ENABLED - can mint unlimited tokens
        2. Freeze authority ENABLED - can freeze user accounts
        3. 95% held by top wallet - extreme concentration
        4. Only $500 liquidity - easy to drain
        5. Copying 'BONK' name - social engineering
        
        VERDICT: HIGH PROBABILITY RUG PULL (94%)
        RECOMMENDATION: BLOCK immediately"""
    }
    
    print(f"\n[*] ORACLE Risk Assessment:")
    print(f"    Threat Score: {analysis['threat_score']}%")
    print(f"    Type: {analysis['threat_type']}")
    print(f"    Confidence: {analysis['confidence']}%")
    print(f"\n    Reasoning:")
    for line in analysis['reasoning'].split('\n'):
        print(f"    {line}")
    
    return analysis


async def demo_commit_reveal():
    """Demonstrate commit-reveal transparency"""
    
    print("\n" + "="*60)
    print("[DEMO 2] Verifiable On-Chain Reasoning")
    print("="*60)
    
    import hashlib
    
    reasoning = "Agent SCANNER detected rug pull indicators. Mint authority enabled, 95% concentration, $500 liquidity. Recommendation: BLOCK."
    
    # Commit phase
    reasoning_hash = hashlib.sha256(reasoning.encode()).hexdigest()
    
    print(f"\n[COMMIT PHASE] (before action):")
    print(f"    Reasoning Hash: {reasoning_hash[:32]}...")
    print(f"    Transaction: [simulated] Committed to Solana devnet")
    
    await asyncio.sleep(0.5)
    
    # Execute phase
    print(f"\n[EXECUTE PHASE]:")
    print(f"    Action: BLOCK token")
    print(f"    Token added to threat registry")
    print(f"    Community alert triggered")
    
    await asyncio.sleep(0.5)
    
    # Reveal phase
    print(f"\n[REVEAL PHASE] (after action):")
    print(f"    Full Reasoning: \"{reasoning}\"")
    
    # Verify
    verify_hash = hashlib.sha256(reasoning.encode()).hexdigest()
    match = verify_hash == reasoning_hash
    
    print(f"\n[VERIFY PHASE]:")
    print(f"    Computed Hash: {verify_hash[:32]}...")
    print(f"    Hash Match: {'VERIFIED' if match else 'FAILED'}")
    print(f"\n    Anyone can verify this decision on Solana Explorer!")


async def demo_swarm_coordination():
    """Demonstrate multi-agent coordination"""
    
    print("\n" + "="*60)
    print("[DEMO 3] Swarm Coordination")
    print("="*60)
    
    print(f"\n[*] COORDINATOR initiating swarm response...")
    
    agents = [
        ("SENTINEL", "Monitor related wallets"),
        ("SCANNER", "Deep contract analysis"),
        ("ORACLE", "Risk prediction: 94%"),
        ("GUARDIAN", "Execute blocking"),
    ]
    
    print(f"\n[*] Agent Assignments:")
    for agent, task in agents:
        print(f"    {agent}: {task}")
    
    print(f"\n[*] Swarm Voting:")
    for agent, _ in agents:
        await asyncio.sleep(0.3)
        print(f"    {agent}: [APPROVE]")
    
    print(f"\n[+] Consensus reached: 4/4 agents approve")
    print(f"    Executing coordinated response...")
    
    await asyncio.sleep(0.5)
    
    print(f"\n[*] GUARDIAN executing:")
    print(f"    - Token blocked in registry")
    print(f"    - Watchlist updated")
    print(f"    - Community alert sent")
    print(f"\n[+] Threat neutralized!")


async def demo_metrics():
    """Show simulated metrics"""
    
    print("\n" + "="*60)
    print("[DEMO 4] System Metrics")
    print("="*60)
    
    metrics = {
        "Agents Active": "4/4",
        "Threats Detected (24h)": 47,
        "Threats Blocked": 12,
        "False Positives": 2,
        "Accuracy": "94.7%",
        "Avg Response Time": "28 seconds",
        "SOL Protected": "~15,000",
    }
    
    print(f"\n[*] Real-time Statistics:")
    for metric, value in metrics.items():
        print(f"    {metric}: {value}")


async def main():
    print_banner()
    
    print(f"[*] Demo started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[*] Network: Solana Devnet")
    print(f"[*] Model: Claude Opus")
    
    # Run demos
    await demo_threat_detection()
    await demo_commit_reveal()
    await demo_swarm_coordination()
    await demo_metrics()
    
    print("\n" + "="*60)
    print("[+] DEMO COMPLETE")
    print("="*60)
    print("""
    The Solana Immune System demonstrates:
    
    [+] Autonomous threat detection
    [+] AI-powered analysis (Claude Opus)
    [+] Verifiable on-chain reasoning
    [+] Multi-agent swarm coordination
    [+] Real-time protection
    
    Protecting Solana, one block at a time.
    """)


if __name__ == "__main__":
    asyncio.run(main())
