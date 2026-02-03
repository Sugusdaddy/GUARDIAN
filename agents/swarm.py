"""
Solana Immune System - Swarm Orchestrator

Main entry point for running the autonomous multi-agent security swarm.
All 10 agents working together to protect the Solana ecosystem.
"""
import asyncio
import os
import signal
import sys
from datetime import datetime
from typing import List

import structlog
from dotenv import load_dotenv

from core.base_agent import AutonomousAgent
from core.config import AgentConfig, config

# Import all 10 specialized agents
from specialized.sentinel_agent import SentinelAgent
from specialized.scanner_agent import ScannerAgent
from specialized.oracle_agent import OracleAgent
from specialized.coordinator_agent import CoordinatorAgent
from specialized.guardian_agent import GuardianAgent
from specialized.intel_agent import IntelAgent
from specialized.reporter_agent import ReporterAgent
from specialized.auditor_agent import AuditorAgent
from specialized.hunter_agent import HunterAgent
from specialized.healer_agent import HealerAgent

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Load environment variables
load_dotenv()


class SolanaImmuneSystem:
    """
    Main orchestrator for the Solana Immune System.
    
    Initializes and coordinates all 10 autonomous security agents
    as a unified swarm protecting the Solana ecosystem.
    
    AGENTS:
    1. SENTINEL  - Transaction monitoring
    2. SCANNER   - Contract/token analysis
    3. ORACLE    - Risk prediction (AI/ML)
    4. COORDINATOR - Swarm orchestration
    5. GUARDIAN  - Threat defense
    6. INTEL     - Knowledge base
    7. REPORTER  - Community alerts
    8. AUDITOR   - Reasoning verification
    9. HUNTER    - Actor tracking
    10. HEALER   - Fund recovery
    """
    
    def __init__(self, config: AgentConfig = config):
        self.config = config
        self.agents: List[AutonomousAgent] = []
        self.running = False
        self.start_time = None
        
        logger.info("============================================")
        logger.info("   SOLANA IMMUNE SYSTEM - Initializing")
        logger.info("============================================")
        
        # Validate configuration
        config.validate()
        
        # Initialize all 10 agents
        self._initialize_agents()
        
        # Connect agents to each other (swarm networking)
        self._connect_swarm()
        
        logger.info(f"Swarm initialized with {len(self.agents)} agents")
        logger.info("Agents: " + ", ".join([a.role for a in self.agents]))
        logger.info("============================================")
    
    def _initialize_agents(self):
        """Initialize all 10 security agents"""
        
        # All 10 agent classes
        agent_classes = [
            SentinelAgent,      # 1. Transaction monitoring
            ScannerAgent,       # 2. Contract analysis
            OracleAgent,        # 3. Risk prediction
            CoordinatorAgent,   # 4. Swarm coordination
            GuardianAgent,      # 5. Threat defense
            IntelAgent,         # 6. Knowledge base
            ReporterAgent,      # 7. Community alerts
            AuditorAgent,       # 8. Reasoning verification
            HunterAgent,        # 9. Actor tracking
            HealerAgent,        # 10. Fund recovery
        ]
        
        for AgentClass in agent_classes:
            try:
                agent = AgentClass(config=self.config)
                self.agents.append(agent)
            except Exception as e:
                logger.error(f"Failed to initialize {AgentClass.__name__}", error=str(e))
    
    def _connect_swarm(self):
        """Connect all agents to each other for swarm communication"""
        for agent in self.agents:
            # Each agent gets references to all other agents
            agent.other_agents = [a for a in self.agents if a != agent]
    
    async def start(self):
        """Start the autonomous swarm"""
        
        self.running = True
        self.start_time = datetime.now()
        
        logger.info("============================================")
        logger.info("   SOLANA IMMUNE SYSTEM - Starting")
        logger.info("============================================")
        logger.info(f"Network: {self.config.network}")
        logger.info(f"Agents: {len(self.agents)}")
        logger.info(f"Model: {self.config.model}")
        logger.info("============================================")
        
        # Start all agents concurrently
        agent_tasks = [agent.start() for agent in self.agents]
        
        # Also start the monitoring task
        monitor_task = asyncio.create_task(self._monitor_swarm())
        
        # Wait for all tasks (runs forever until stopped)
        try:
            await asyncio.gather(*agent_tasks, monitor_task)
        except asyncio.CancelledError:
            logger.info("Swarm tasks cancelled")
    
    async def stop(self):
        """Stop the swarm gracefully"""
        
        logger.info("Stopping Solana Immune System...")
        self.running = False
        
        # Stop all agents
        for agent in self.agents:
            await agent.stop()
        
        logger.info("Swarm stopped gracefully")
    
    async def _monitor_swarm(self):
        """Monitor swarm health and performance"""
        
        while self.running:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Collect stats from all agents
                stats = self.get_stats()
                
                logger.info(
                    "SWARM STATUS",
                    uptime=f"{stats['uptime_seconds']:.0f}s",
                    agents=f"{stats['agents_active']}/{len(self.agents)}",
                    threats=stats['total_threats'],
                    memory=stats['total_memory']
                )
                
            except Exception as e:
                logger.error("Monitor error", error=str(e))
    
    def get_stats(self) -> dict:
        """Get current swarm statistics"""
        
        uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        
        return {
            "running": self.running,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "uptime_seconds": uptime,
            "agents_active": sum(1 for a in self.agents if a.running),
            "total_threats": sum(len(a.threat_history) for a in self.agents),
            "total_memory": sum(len(a.memory) for a in self.agents),
            "agents": [
                {
                    "role": a.role,
                    "type": a.agent_type,
                    "running": a.running,
                    "threats_detected": len(a.threat_history),
                    "memory_entries": len(a.memory)
                }
                for a in self.agents
            ]
        }
    
    def get_agent(self, agent_type: str) -> AutonomousAgent:
        """Get a specific agent by type"""
        return next((a for a in self.agents if a.agent_type == agent_type), None)


async def main():
    """Main entry point"""
    
    print("""
    ==============================================================
    |                                                            |
    |     SOLANA IMMUNE SYSTEM                                   |
    |                                                            |
    |     Autonomous Multi-Agent Security Infrastructure         |
    |     Protecting the Solana Ecosystem 24/7                   |
    |                                                            |
    |     10 AI Agents | Verifiable Reasoning | Real-time        |
    |                                                            |
    ==============================================================
    """)
    
    # Create the immune system
    swarm = SolanaImmuneSystem()
    
    # Handle shutdown signals
    loop = asyncio.get_event_loop()
    
    def shutdown_handler():
        logger.info("Received shutdown signal")
        asyncio.create_task(swarm.stop())
    
    # Register signal handlers (Unix only)
    if sys.platform != "win32":
        loop.add_signal_handler(signal.SIGINT, shutdown_handler)
        loop.add_signal_handler(signal.SIGTERM, shutdown_handler)
    
    try:
        # Start the swarm
        await swarm.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        await swarm.stop()
    finally:
        logger.info("Solana Immune System shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
