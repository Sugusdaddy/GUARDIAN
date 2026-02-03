# Specialized Agents for Solana Immune System
# 15 Autonomous Agents - Complete Security Swarm

# Original 10 Agents (in agents/specialized/)
# - SentinelAgent, ScannerAgent, OracleAgent, CoordinatorAgent
# - GuardianAgent, IntelAgent, ReporterAgent, AuditorAgent
# - HunterAgent, HealerAgent

# Elite Agents v2.0 (in GUARDIAN/agents/specialized/)
from .lazarus_agent import LazarusAgent      # 🇰🇵 DPRK/State-actor tracking
from .quantum_agent import QuantumAgent      # ⚛️ Post-quantum defense
from .honeypot_agent import HoneypotAgent    # 🪤 Active bait wallet traps
from .network_agent import NetworkAgent      # 🌐 Solana infrastructure health
from .swapguard_agent import SwapGuardAgent  # 🛡️ Risk-aware DEX trading (NEW v2.1)

# SwapGuard convenience exports
from .swapguard_agent import (
    SwapRequest,
    SwapDecision,
    SwapAction,
    SwapRisk,
    TokenAnalysis,
    get_swapguard,
    evaluate_swap,
)

__all__ = [
    # Elite Agents (v2.0)
    "LazarusAgent",     # 🇰🇵 DPRK state-actor tracking
    "QuantumAgent",     # ⚛️ Post-quantum readiness
    "HoneypotAgent",    # 🪤 Active bait wallet traps
    "NetworkAgent",     # 🌐 Solana network health
    
    # Trading Protection (v2.1)
    "SwapGuardAgent",   # 🛡️ Risk-aware DEX trading
    "SwapRequest",
    "SwapDecision", 
    "SwapAction",
    "SwapRisk",
    "TokenAnalysis",
    "get_swapguard",
    "evaluate_swap",
]

# Agent count: 15 (10 original + 5 elite)
AGENT_COUNT = 15
ELITE_AGENT_COUNT = 5
