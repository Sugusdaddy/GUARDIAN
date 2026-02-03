"""
Solana Immune System - Swarm Orchestrator

Main entry point for running the autonomous multi-agent security swarm.
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
from specialized.sentinel_agent import SentinelAgent
from specialized.scanner_agent import ScannerAgent
from specialized.oracle_agent import OracleAgent
from specialized.coordinator_agent import CoordinatorAgent

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
    
    Initializes and coordinates all autonomous security agents
    as a unified swarm protecting the Solana ecosystem.
    """
    
    def __init__(self, config: AgentConfig = config):
        self.config = config
        self.agents: List[AutonomousAgent] = []
        self.running = False
        self.start_time = None
        
        logger.info("🛡️ Initializing Solana Immune System...")
        
        # Validate configuration
        config.validate()
        
        # Initialize all agents
        self._initialize_agents()
        
        # Connect agents to each other (swarm networking)
        self._connect_swarm()
        
        logger.info(
            f"✅ Swarm initialized with {len(self.agents)} agents",
            agents=[a.role for a in self.agents]
        )
    
    def _initialize_agents(self):
        """Initialize all security agents"""
        
        # Core agents for MVP (4 agents)
        agent_classes = [
            SentinelAgent,   # Transaction monitoring
            ScannerAgent,    # Contract analysis
            OracleAgent,     # Risk prediction
            CoordinatorAgent,# Swarm coordination
        ]
        
        # TODO: Add remaining agents for full 10-agent swarm
        # GuardianAgent,  # Threat defense
        # IntelAgent,     # Knowledge base
        # ReporterAgent,  # Community alerts
        # AuditorAgent,   # Reasoning verification
        # HunterAgent,    # Actor tracking
        # HealerAgent,    # Fund recovery
        
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
        
        logger.info("🚀 Starting Solana Immune System...")
        logger.info(f"   Network: {self.config.network}")
        logger.info(f"   Agents: {len(self.agents)}")
        logger.info(f"   Model: {self.config.model}")
        
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
        
        logger.info("🛑 Stopping Solana Immune System...")
        self.running = False
        
        # Stop all agents
        for agent in self.agents:
            await agent.stop()
        
        logger.info("✅ Swarm stopped gracefully")
    
    async def _monitor_swarm(self):
        """Monitor swarm health and performance"""
        
        while self.running:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Collect stats from all agents
                stats = {
                    "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
                    "agents_active": sum(1 for a in self.agents if a.running),
                    "total_threats_detected": sum(len(a.threat_history) for a in self.agents),
                    "total_memory_entries": sum(len(a.memory) for a in self.agents),
                }
                
                logger.info(
                    "📊 Swarm Status",
                    uptime=f"{stats['uptime_seconds']:.0f}s",
                    agents=f"{stats['agents_active']}/{len(self.agents)}",
                    threats=stats['total_threats_detected'],
                    memory=stats['total_memory_entries']
                )
                
            except Exception as e:
                logger.error("Monitor error", error=str(e))
    
    def get_stats(self) -> dict:
        """Get current swarm statistics"""
        return {
            "running": self.running,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "agents": [
                {
                    "role": a.role,
                    "type": a.agent_type,
                    "running": a.running,
                    "threats_detected": len(a.threat_history),
                    "memory_entries": len(a.memory)
                }
                for a in self.agents
            ],
            "total_threats": sum(len(a.threat_history) for a in self.agents)
        }


async def main():
    """Main entry point"""
    
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║     🛡️  SOLANA IMMUNE SYSTEM  🛡️                              ║
    ║                                                              ║
    ║     Autonomous Multi-Agent Security Infrastructure           ║
    ║     Protecting the Solana Ecosystem 24/7                     ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
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
