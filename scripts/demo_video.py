#!/usr/bin/env python3
"""
GUARDIAN Demo Video Script
Cinematic demonstration of the 16-agent security swarm

Run: python scripts/demo_video.py
Record your screen while this runs for the hackathon video!
"""

import asyncio
import sys
import os

# Fix Windows encoding
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8')

import random
from datetime import datetime

# Colors for terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    
    # Background colors
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def type_text(text, delay=0.03, color=""):
    """Typewriter effect"""
    for char in text:
        sys.stdout.write(f"{color}{char}{Colors.END}")
        sys.stdout.flush()
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(delay))
    print()


def print_slow(text, delay=0.5, color=""):
    """Print with delay"""
    print(f"{color}{text}{Colors.END}")
    asyncio.get_event_loop().run_until_complete(asyncio.sleep(delay))


def print_instant(text, color=""):
    """Print instantly"""
    print(f"{color}{text}{Colors.END}")


def print_box(text, color=Colors.CYAN):
    """Print text in a box"""
    width = len(text) + 4
    print(f"{color}╔{'═' * width}╗")
    print(f"║  {text}  ║")
    print(f"╚{'═' * width}╝{Colors.END}")


def print_banner():
    """Print GUARDIAN banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║   ██████╗ ██╗   ██╗ █████╗ ██████╗ ██████╗ ██╗ █████╗ ███╗   ██╗  ║
    ║  ██╔════╝ ██║   ██║██╔══██╗██╔══██╗██╔══██╗██║██╔══██╗████╗  ██║  ║
    ║  ██║  ███╗██║   ██║███████║██████╔╝██║  ██║██║███████║██╔██╗ ██║  ║
    ║  ██║   ██║██║   ██║██╔══██║██╔══██╗██║  ██║██║██╔══██║██║╚██╗██║  ║
    ║  ╚██████╔╝╚██████╔╝██║  ██║██║  ██║██████╔╝██║██║  ██║██║ ╚████║  ║
    ║   ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝  ║
    ║                                                                   ║
    ║              🛡️  SOLANA IMMUNE SYSTEM  🛡️                         ║
    ║                                                                   ║
    ║          16 Autonomous Agents • 24/7 Protection • AI-Powered      ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """
    print(f"{Colors.CYAN}{Colors.BOLD}{banner}{Colors.END}")


async def scene_intro():
    """Scene 1: System startup"""
    clear_screen()
    print_banner()
    await asyncio.sleep(2)
    
    print_slow("\n" + "═" * 70, color=Colors.DIM)
    print_slow(f"  {Colors.WHITE}Initializing GUARDIAN Security Swarm...{Colors.END}", delay=1)
    print_slow("═" * 70 + "\n", color=Colors.DIM)
    
    await asyncio.sleep(0.5)
    
    # Core agents
    core_agents = [
        ("🔭", "SENTINEL", "Transaction Monitor"),
        ("🔍", "SCANNER", "Contract Analyzer"),
        ("🔮", "ORACLE", "ML Risk Predictor"),
        ("🎯", "COORDINATOR", "Swarm Orchestrator"),
        ("🛡️", "GUARDIAN", "Threat Defender"),
        ("📚", "INTEL", "Threat Database"),
        ("📢", "REPORTER", "Alert System"),
        ("✅", "AUDITOR", "Reasoning Verifier"),
        ("🔎", "HUNTER", "Actor Tracker"),
        ("💚", "HEALER", "Recovery Agent"),
    ]
    
    print_slow(f"  {Colors.BOLD}Loading Core Defense Squad (10 agents)...{Colors.END}\n", delay=0.3)
    
    for emoji, name, role in core_agents:
        print_slow(f"    {emoji}  {Colors.GREEN}[ONLINE]{Colors.END}  {Colors.BOLD}{name:12}{Colors.END} - {Colors.DIM}{role}{Colors.END}", delay=0.15)
    
    await asyncio.sleep(0.5)
    
    # Elite agents
    elite_agents = [
        ("🍯", "HONEYPOT", "Active Trap System"),
        ("🇰🇵", "LAZARUS", "State-Actor Tracker"),
        ("🌐", "NETWORK", "Infrastructure Monitor"),
        ("⚛️", "QUANTUM", "Post-Quantum Defense"),
        ("🛡️", "SWAPGUARD", "Trade Protection"),
        ("🚨", "EVACUATOR", "Emergency Extraction"),
    ]
    
    print_slow(f"\n  {Colors.BOLD}Loading Elite Threat Squad (6 agents)...{Colors.END}\n", delay=0.3)
    
    for emoji, name, role in elite_agents:
        print_slow(f"    {emoji}  {Colors.CYAN}[ONLINE]{Colors.END}  {Colors.BOLD}{name:12}{Colors.END} - {Colors.DIM}{role}{Colors.END}", delay=0.2)
    
    await asyncio.sleep(0.5)
    
    print_slow(f"\n{'═' * 70}", color=Colors.DIM)
    print_slow(f"  {Colors.GREEN}{Colors.BOLD}✓ ALL 16 AGENTS OPERATIONAL{Colors.END}", delay=0.5)
    print_slow(f"  {Colors.DIM}Monitoring Solana mainnet in real-time...{Colors.END}", delay=0.3)
    print_slow(f"{'═' * 70}\n", color=Colors.DIM)
    
    await asyncio.sleep(2)


async def scene_honeypot_detection():
    """Scene 2: Detect honeypot in real-time"""
    clear_screen()
    
    print_slow(f"\n{Colors.CYAN}{'═' * 70}{Colors.END}")
    print_slow(f"{Colors.CYAN}  SCENE 2: REAL-TIME HONEYPOT DETECTION{Colors.END}")
    print_slow(f"{Colors.CYAN}{'═' * 70}{Colors.END}\n")
    
    await asyncio.sleep(1)
    
    # Simulated token data
    token_address = "ScAmT0k3n" + "".join(random.choices("0123456789ABCDEFabcdef", k=30))
    
    print_slow(f"  {Colors.DIM}[{datetime.now().strftime('%H:%M:%S')}]{Colors.END} 🔭 SENTINEL scanning new token launches...")
    await asyncio.sleep(0.5)
    
    print_slow(f"\n  {Colors.YELLOW}⚠️  New token detected on pump.fun{Colors.END}")
    print_slow(f"     Token: {Colors.WHITE}$MOONSHOT{Colors.END}")
    print_slow(f"     Mint:  {Colors.DIM}{token_address[:16]}...{Colors.END}")
    print_slow(f"     Age:   {Colors.WHITE}2 minutes{Colors.END}")
    
    await asyncio.sleep(1)
    
    print_slow(f"\n  {Colors.CYAN}🔍 SCANNER analyzing contract...{Colors.END}")
    await asyncio.sleep(0.3)
    
    # Analysis animation
    checks = [
        ("Checking mint authority", "⚠️ ENABLED - Can mint infinite tokens"),
        ("Checking freeze authority", "⚠️ ENABLED - Can freeze your tokens"),
        ("Testing buy transaction", "✅ Buy successful"),
        ("Testing sell transaction", "❌ SELL BLOCKED - Transfer restricted"),
        ("Checking holder distribution", "🚨 Top holder: 94.7%"),
    ]
    
    for check, result in checks:
        print_slow(f"     • {check}...", delay=0.1, color=Colors.DIM)
        await asyncio.sleep(0.4)
        if "❌" in result or "🚨" in result:
            color = Colors.RED
        elif "⚠️" in result:
            color = Colors.YELLOW
        else:
            color = Colors.GREEN
        print_slow(f"       {color}{result}{Colors.END}", delay=0.2)
    
    await asyncio.sleep(0.5)
    
    # Alert
    print_slow(f"\n  {Colors.BG_RED}{Colors.WHITE}{Colors.BOLD} 🚨 HONEYPOT DETECTED 🚨 {Colors.END}")
    print_slow(f"\n  {Colors.RED}Risk Score: {Colors.BOLD}98/100{Colors.END}")
    print_slow(f"  {Colors.RED}Classification: {Colors.BOLD}HONEYPOT + RUG PULL{Colors.END}")
    print_slow(f"  {Colors.RED}Action: {Colors.BOLD}BLACKLISTED{Colors.END}")
    
    await asyncio.sleep(1)
    
    print_slow(f"\n  {Colors.GREEN}✓ Token added to global blacklist{Colors.END}")
    print_slow(f"  {Colors.GREEN}✓ Alert sent to 1,247 protected wallets{Colors.END}")
    print_slow(f"  {Colors.GREEN}✓ Pattern saved for ML training{Colors.END}")
    
    await asyncio.sleep(2)


async def scene_swapguard():
    """Scene 3: SwapGuard blocks dangerous trade"""
    clear_screen()
    
    print_slow(f"\n{Colors.CYAN}{'═' * 70}{Colors.END}")
    print_slow(f"{Colors.CYAN}  SCENE 3: SWAPGUARD PROTECTS USER FROM SCAM{Colors.END}")
    print_slow(f"{Colors.CYAN}{'═' * 70}{Colors.END}\n")
    
    await asyncio.sleep(1)
    
    user_wallet = "7xK9" + "".join(random.choices("0123456789ABCDEFabcdef", k=40))
    
    print_slow(f"  {Colors.DIM}[{datetime.now().strftime('%H:%M:%S')}]{Colors.END} 💱 Incoming swap request...")
    await asyncio.sleep(0.5)
    
    print_slow(f"\n  {Colors.WHITE}User Request:{Colors.END}")
    print_slow(f"     Wallet: {Colors.DIM}{user_wallet[:16]}...{Colors.END}")
    print_slow(f"     Action: {Colors.WHITE}SWAP 5 SOL → $MOONSHOT{Colors.END}")
    print_slow(f"     Value:  {Colors.WHITE}~$750 USD{Colors.END}")
    
    await asyncio.sleep(0.5)
    
    print_slow(f"\n  {Colors.CYAN}🛡️ SWAPGUARD intercepting...{Colors.END}")
    await asyncio.sleep(0.3)
    
    # Risk analysis
    print_slow(f"\n     {Colors.BOLD}Risk Analysis:{Colors.END}")
    await asyncio.sleep(0.2)
    
    risks = [
        ("Honeypot Risk", 100, Colors.RED),
        ("Rug Pull Risk", 95, Colors.RED),
        ("Liquidity Risk", 80, Colors.YELLOW),
        ("Concentration Risk", 90, Colors.RED),
    ]
    
    for name, score, color in risks:
        bar = "█" * (score // 5) + "░" * (20 - score // 5)
        print_slow(f"     {name:20} {color}[{bar}] {score}%{Colors.END}", delay=0.15)
    
    await asyncio.sleep(0.5)
    
    print_slow(f"\n  {Colors.BG_RED}{Colors.WHITE}{Colors.BOLD} ❌ SWAP BLOCKED ❌ {Colors.END}")
    
    await asyncio.sleep(0.5)
    
    print_slow(f"\n  {Colors.YELLOW}Warnings sent to user:{Colors.END}")
    warnings = [
        "🚨 HONEYPOT DETECTED - Cannot sell this token!",
        "⚠️ Mint authority enabled - Unlimited supply risk",
        "⚠️ Freeze authority enabled - Your tokens can be frozen",
        "⚠️ Top holder owns 94.7% - Extreme concentration",
    ]
    for w in warnings:
        print_slow(f"     {Colors.RED}{w}{Colors.END}", delay=0.2)
    
    await asyncio.sleep(1)
    
    print_slow(f"\n  {Colors.GREEN}{Colors.BOLD}✓ USER PROTECTED - $750 SAVED{Colors.END}")
    
    await asyncio.sleep(2)


async def scene_lazarus():
    """Scene 4: Lazarus Group detection"""
    clear_screen()
    
    print_slow(f"\n{Colors.CYAN}{'═' * 70}{Colors.END}")
    print_slow(f"{Colors.CYAN}  SCENE 4: STATE-ACTOR THREAT DETECTION{Colors.END}")
    print_slow(f"{Colors.CYAN}{'═' * 70}{Colors.END}\n")
    
    await asyncio.sleep(1)
    
    print_slow(f"  {Colors.DIM}[{datetime.now().strftime('%H:%M:%S')}]{Colors.END} 🇰🇵 LAZARUS agent monitoring for DPRK patterns...")
    await asyncio.sleep(0.5)
    
    print_slow(f"\n  {Colors.YELLOW}⚠️  Suspicious activity cluster detected{Colors.END}")
    await asyncio.sleep(0.3)
    
    attacker = "Hx7K" + "".join(random.choices("0123456789ABCDEFabcdef", k=40))
    
    print_slow(f"\n  {Colors.WHITE}Analysis:{Colors.END}")
    
    indicators = [
        ("Transaction timing", "UTC+9 pattern (Pyongyang timezone)", "🚨"),
        ("Fund movement", "Peel chain detected (small amounts)", "🚨"),
        ("Mixer usage", "Funds routed through Tornado Cash", "⚠️"),
        ("Chain hopping", "Bridge to Ethereum detected", "⚠️"),
        ("OFAC check", "Connected to flagged address", "🚨"),
    ]
    
    for name, detail, emoji in indicators:
        print_slow(f"     {emoji} {Colors.WHITE}{name}:{Colors.END} {Colors.DIM}{detail}{Colors.END}", delay=0.25)
    
    await asyncio.sleep(0.5)
    
    print_slow(f"\n  {Colors.BG_YELLOW}{Colors.WHITE}{Colors.BOLD} 🇰🇵 LAZARUS GROUP PATTERN MATCH: 87% CONFIDENCE 🇰🇵 {Colors.END}")
    
    await asyncio.sleep(0.5)
    
    print_slow(f"\n  {Colors.CYAN}Automated response:{Colors.END}")
    actions = [
        "✓ Address flagged in global database",
        "✓ Connected wallets identified (23 wallets)",
        "✓ Fund flow tracked: $2.3M in 48h",
        "✓ Alert sent to ecosystem partners",
        "✓ Pattern saved for future detection",
    ]
    for a in actions:
        print_slow(f"     {Colors.GREEN}{a}{Colors.END}", delay=0.2)
    
    await asyncio.sleep(2)


async def scene_evacuation():
    """Scene 5: Emergency wallet evacuation"""
    clear_screen()
    
    print_slow(f"\n{Colors.RED}{'═' * 70}{Colors.END}")
    print_slow(f"{Colors.RED}  SCENE 5: EMERGENCY WALLET EVACUATION{Colors.END}")
    print_slow(f"{Colors.RED}{'═' * 70}{Colors.END}\n")
    
    await asyncio.sleep(1)
    
    victim_wallet = "VcTm" + "".join(random.choices("0123456789ABCDEFabcdef", k=40))
    safe_wallet = "SaFe" + "".join(random.choices("0123456789ABCDEFabcdef", k=40))
    
    print_slow(f"  {Colors.RED}{Colors.BOLD}🚨 ALERT: WALLET UNDER ATTACK 🚨{Colors.END}")
    await asyncio.sleep(0.5)
    
    print_slow(f"\n  {Colors.WHITE}Compromised wallet:{Colors.END} {Colors.DIM}{victim_wallet[:20]}...{Colors.END}")
    print_slow(f"  {Colors.WHITE}Attack type:{Colors.END} {Colors.RED}Drainer contract triggered{Colors.END}")
    print_slow(f"  {Colors.WHITE}Assets at risk:{Colors.END} {Colors.YELLOW}$12,450 USD{Colors.END}")
    
    await asyncio.sleep(0.5)
    
    print_slow(f"\n  {Colors.CYAN}🚨 EVACUATOR activating emergency protocol...{Colors.END}")
    await asyncio.sleep(0.3)
    
    print_slow(f"\n  {Colors.WHITE}Evacuation Plan:{Colors.END}")
    print_slow(f"     Destination: {Colors.DIM}{safe_wallet[:20]}...{Colors.END}")
    print_slow(f"     Priority: {Colors.RED}CRITICAL (max fees){Colors.END}")
    print_slow(f"     Estimated time: {Colors.WHITE}~3 seconds{Colors.END}")
    
    await asyncio.sleep(0.5)
    
    # Evacuation progress
    print_slow(f"\n  {Colors.YELLOW}Executing evacuation...{Colors.END}\n")
    
    steps = [
        ("Revoking 3 dangerous approvals", 0.4),
        ("Transferring 2,450 USDC", 0.3),
        ("Transferring 1,200 BONK", 0.3),
        ("Transferring 0.5 JUP", 0.2),
        ("Transferring NFT: Okay Bear #4521", 0.4),
        ("Transferring 45.7 SOL", 0.3),
    ]
    
    for step, delay in steps:
        print_slow(f"     ⏳ {step}...", delay=0.1, color=Colors.DIM)
        await asyncio.sleep(delay)
        print_slow(f"     {Colors.GREEN}✓ Complete{Colors.END}", delay=0.1)
    
    await asyncio.sleep(0.5)
    
    print_slow(f"\n  {Colors.BG_GREEN}{Colors.WHITE}{Colors.BOLD} ✅ EVACUATION COMPLETE ✅ {Colors.END}")
    
    print_slow(f"\n  {Colors.GREEN}Results:{Colors.END}")
    print_slow(f"     Assets saved: {Colors.BOLD}$12,450 USD{Colors.END}")
    print_slow(f"     Transactions: {Colors.WHITE}6 confirmed{Colors.END}")
    print_slow(f"     Time elapsed: {Colors.WHITE}2.7 seconds{Colors.END}")
    print_slow(f"     Fees paid: {Colors.WHITE}0.015 SOL (~$2.25){Colors.END}")
    
    await asyncio.sleep(1)
    
    print_slow(f"\n  {Colors.GREEN}{Colors.BOLD}💰 USER FUNDS SECURED BEFORE ATTACKER COULD DRAIN 💰{Colors.END}")
    
    await asyncio.sleep(2)


async def scene_finale():
    """Scene 6: Stats and finale"""
    clear_screen()
    
    print_slow(f"\n{Colors.CYAN}{'═' * 70}{Colors.END}")
    print_slow(f"{Colors.CYAN}  GUARDIAN - PROTECTING SOLANA 24/7{Colors.END}")
    print_slow(f"{Colors.CYAN}{'═' * 70}{Colors.END}\n")
    
    await asyncio.sleep(1)
    
    print_slow(f"  {Colors.BOLD}📊 DEMO SESSION STATISTICS{Colors.END}\n")
    
    stats = [
        ("Agents Active", "16/16"),
        ("Threats Detected", "3"),
        ("Honeypots Caught", "1"),
        ("Scam Swaps Blocked", "1"),
        ("State-Actor Alerts", "1"),
        ("Emergency Evacuations", "1"),
        ("User Funds Protected", "$13,200"),
        ("False Positives", "0"),
    ]
    
    for name, value in stats:
        print_slow(f"     {Colors.WHITE}{name:25}{Colors.END} {Colors.GREEN}{Colors.BOLD}{value}{Colors.END}", delay=0.2)
    
    await asyncio.sleep(1)
    
    print_slow(f"\n{'═' * 70}", color=Colors.DIM)
    
    print_slow(f"\n  {Colors.BOLD}🛡️ GUARDIAN CAPABILITIES:{Colors.END}\n")
    
    capabilities = [
        "✅ Real-time honeypot detection",
        "✅ Lazarus Group / DPRK tracking (FIRST ON SOLANA)",
        "✅ Risk-aware DEX trading protection",
        "✅ Emergency wallet evacuation",
        "✅ Post-quantum cryptography readiness",
        "✅ Active defense with honeypot traps",
        "✅ ML-powered threat prediction",
        "✅ On-chain verifiable AI reasoning",
    ]
    
    for cap in capabilities:
        print_slow(f"     {Colors.CYAN}{cap}{Colors.END}", delay=0.15)
    
    await asyncio.sleep(1)
    
    print_slow(f"\n{'═' * 70}\n", color=Colors.DIM)
    
    # Final banner
    final = """
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║                    🛡️  GUARDIAN v2.2  🛡️                          ║
    ║                                                                   ║
    ║              The Immune System Solana Deserves                    ║
    ║                                                                   ║
    ║         16 Agents • AI-Powered • Fully Autonomous                 ║
    ║                                                                   ║
    ║              github.com/Sugusdaddy/GUARDIAN                       ║
    ║                                                                   ║
    ║                Built for Colosseum Hackathon 2025                 ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """
    print(f"{Colors.CYAN}{Colors.BOLD}{final}{Colors.END}")
    
    await asyncio.sleep(3)


async def run_demo():
    """Run the complete demo"""
    try:
        # Intro
        await scene_intro()
        
        # Scene 2: Honeypot detection
        await scene_honeypot_detection()
        
        # Scene 3: SwapGuard
        await scene_swapguard()
        
        # Scene 4: Lazarus tracking
        await scene_lazarus()
        
        # Scene 5: Emergency evacuation
        await scene_evacuation()
        
        # Finale
        await scene_finale()
        
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Demo interrupted.{Colors.END}")


if __name__ == "__main__":
    print(f"\n{Colors.CYAN}🎬 GUARDIAN Demo Video Script{Colors.END}")
    print(f"{Colors.DIM}Press Ctrl+C to stop at any time{Colors.END}")
    print(f"{Colors.DIM}Start your screen recording NOW!{Colors.END}\n")
    
    input(f"{Colors.YELLOW}Press ENTER to start the demo...{Colors.END}")
    
    asyncio.run(run_demo())
