"""
GUARDIAN - Solana Immune System
Autonomous multi-agent security infrastructure for Solana

This package provides 16 specialized AI agents for 24/7 threat detection
and autonomous response on the Solana blockchain.
"""

__version__ = "0.1.0"
__author__ = "GUARDIAN Team"
__license__ = "MIT"

from agents.core.base_agent import AutonomousAgent, Threat, Decision
from agents.core.config import AgentConfig, config
from agents.core.database import get_db, GuardianDB

__all__ = [
    "AutonomousAgent",
    "Threat",
    "Decision",
    "AgentConfig",
    "config",
    "get_db",
    "GuardianDB",
]
