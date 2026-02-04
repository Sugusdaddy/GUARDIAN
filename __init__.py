"""
GUARDIAN - Solana Immune System
================================

Autonomous multi-agent security infrastructure for Solana with 16 specialized
AI agents providing 24/7 threat detection and response.

Quick Start:
    >>> from GUARDIAN import evaluate_swap, emergency_evacuate
    >>> decision = await evaluate_swap(
    ...     user_wallet="...",
    ...     input_mint="SOL",
    ...     output_mint="TOKEN",
    ...     amount=1.0
    ... )
    >>> print(decision.action)  # APPROVE, WARN, or REJECT

Modules:
    agents: Core agent framework and specialized agents
    app: Web API and dashboard
    cli: Interactive command-line interface
"""

__version__ = "0.1.0"
__author__ = "GUARDIAN Team"
__email__ = "security@guardian.sol"
__license__ = "MIT"
__url__ = "https://github.com/Sugusdaddy/GUARDIAN"

# Version info
VERSION = (0, 1, 0)

__all__ = [
    "__version__",
    "VERSION",
]
