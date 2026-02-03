# Specialized Agents for Solana Immune System
# 16 Autonomous Agents - Complete Security Swarm

# Original 10 Agents (in agents/specialized/)
# - SentinelAgent, ScannerAgent, OracleAgent, CoordinatorAgent
# - GuardianAgent, IntelAgent, ReporterAgent, AuditorAgent
# - HunterAgent, HealerAgent

# Elite Agents v2.0+ (in GUARDIAN/agents/specialized/)
from .lazarus_agent import LazarusAgent      # 🇰🇵 DPRK/State-actor tracking
from .quantum_agent import QuantumAgent      # ⚛️ Post-quantum defense
from .honeypot_agent import HoneypotAgent    # 🪤 Active bait wallet traps
from .network_agent import NetworkAgent      # 🌐 Solana infrastructure health
from .swapguard_agent import SwapGuardAgent  # 🛡️ Risk-aware DEX trading (v2.1)
from .evacuator_agent import EvacuatorAgent  # 🚨 Emergency wallet evacuation (v2.2)

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

# Evacuator convenience exports
from .evacuator_agent import (
    EvacuationPlan,
    EvacuationResult,
    EvacuationStatus,
    ThreatUrgency,
    WalletAsset,
    get_evacuator,
    emergency_evacuate,
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
    
    # Emergency Evacuation (v2.2)
    "EvacuatorAgent",   # 🚨 Emergency wallet evacuation
    "EvacuationPlan",
    "EvacuationResult",
    "EvacuationStatus",
    "ThreatUrgency",
    "WalletAsset",
    "get_evacuator",
    "emergency_evacuate",
]

# Agent count: 16 (10 original + 6 elite)
AGENT_COUNT = 16
ELITE_AGENT_COUNT = 6
