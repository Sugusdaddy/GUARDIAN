# GUARDIAN v2.0 - Elite Agents Module
# 4 Advanced specialized agents for Solana security

from .agents.specialized import (
    LazarusAgent,
    QuantumAgent,
    HoneypotAgent,
    NetworkAgent,
)

__version__ = "2.0.0"
__all__ = [
    "LazarusAgent",
    "QuantumAgent", 
    "HoneypotAgent",
    "NetworkAgent",
]
