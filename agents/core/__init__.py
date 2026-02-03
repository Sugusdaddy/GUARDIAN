# Solana Immune System - Core Agent Framework

# Always available
from .config import AgentConfig, config
from .database import get_db, GuardianDB

# Try to import optional components
try:
    from .base_agent import AutonomousAgent, Threat, Decision
    HAS_AGENT = True
except ImportError as e:
    HAS_AGENT = False
    AutonomousAgent = None
    Threat = None
    Decision = None

try:
    from .onchain import GuardianOnChain, ActionType, ThreatType, create_onchain_client
    HAS_ONCHAIN = True
except ImportError:
    HAS_ONCHAIN = False
    GuardianOnChain = None
    ActionType = None
    ThreatType = None
    create_onchain_client = None

try:
    from .embeddings import (
        get_embedder, get_classifier, get_scorer,
        ThreatEmbedder, ThreatClassifier, RiskScorer
    )
    HAS_ML = True
except ImportError:
    HAS_ML = False
    get_embedder = None
    get_classifier = None
    get_scorer = None
    ThreatEmbedder = None
    ThreatClassifier = None
    RiskScorer = None

__all__ = [
    # Config (always available)
    "config",
    "AgentConfig",
    # Database (always available)
    "get_db",
    "GuardianDB",
    # Base (may not be available)
    "AutonomousAgent",
    "Threat",
    "Decision",
    # On-chain
    "GuardianOnChain",
    "ActionType",
    "ThreatType",
    "create_onchain_client",
    # ML
    "get_embedder",
    "get_classifier",
    "get_scorer",
    "ThreatEmbedder",
    "ThreatClassifier",
    "RiskScorer",
    # Flags
    "HAS_AGENT",
    "HAS_ONCHAIN",
    "HAS_ML",
]
