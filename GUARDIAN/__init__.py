# GUARDIAN v2.1 - Elite Agents Module
# 5 Advanced specialized agents for Solana security

from .agents.specialized import (
    # Elite Agents
    LazarusAgent,
    QuantumAgent,
    HoneypotAgent,
    NetworkAgent,
    SwapGuardAgent,
    
    # SwapGuard utilities
    SwapRequest,
    SwapDecision,
    SwapAction,
    SwapRisk,
    TokenAnalysis,
    get_swapguard,
    evaluate_swap,
)

__version__ = "2.1.0"
__all__ = [
    # Agents
    "LazarusAgent",
    "QuantumAgent", 
    "HoneypotAgent",
    "NetworkAgent",
    "SwapGuardAgent",
    
    # SwapGuard utilities
    "SwapRequest",
    "SwapDecision",
    "SwapAction", 
    "SwapRisk",
    "TokenAnalysis",
    "get_swapguard",
    "evaluate_swap",
]
