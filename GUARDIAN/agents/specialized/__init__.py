# Specialized Agents for Solana Immune System
# 14 Autonomous Agents - Complete Security Swarm

# Original 10 Agents
from .sentinel_agent import SentinelAgent
from .scanner_agent import ScannerAgent
from .oracle_agent import OracleAgent
from .coordinator_agent import CoordinatorAgent
from .guardian_agent import GuardianAgent
from .intel_agent import IntelAgent
from .reporter_agent import ReporterAgent
from .auditor_agent import AuditorAgent
from .hunter_agent import HunterAgent
from .healer_agent import HealerAgent

# NEW: 4 Additional Agents (v2.0)
from .lazarus_agent import LazarusAgent      # 🇰🇵 DPRK/State-actor tracking
from .quantum_agent import QuantumAgent      # ⚛️ Post-quantum defense
from .honeypot_agent import HoneypotAgent    # 🪤 Active bait wallet traps
from .network_agent import NetworkAgent      # 🌐 Solana infrastructure health

__all__ = [
    # Detection Tier
    "SentinelAgent",    # 👁️ 24/7 wallet monitoring
    "ScannerAgent",     # 🔍 Token/contract vulnerability scanning
    "NetworkAgent",     # 🌐 Solana network health (NEW)
    
    # Intelligence Tier
    "OracleAgent",      # 🔮 ML-powered risk prediction
    "IntelAgent",       # 📚 Threat intelligence database
    "LazarusAgent",     # 🇰🇵 DPRK state-actor tracking (NEW)
    
    # Defense Tier
    "GuardianAgent",    # 🛡️ Active threat defense
    "HoneypotAgent",    # 🪤 Active bait wallet traps (NEW)
    "HunterAgent",      # 🔍 Malicious actor tracking
    
    # Support Tier
    "CoordinatorAgent", # 🎯 Swarm coordination
    "ReporterAgent",    # 📢 Community notifications
    "AuditorAgent",     # ✅ Reasoning verification
    "HealerAgent",      # 💚 Fund recovery & self-healing
    "QuantumAgent",     # ⚛️ Post-quantum readiness (NEW)
]

# Agent count: 14 (10 original + 4 new)
AGENT_COUNT = 14
