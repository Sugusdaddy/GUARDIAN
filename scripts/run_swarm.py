#!/usr/bin/env python3
"""
Solana Immune System - Run the Full Swarm

This script starts all 10 autonomous agents and runs them continuously.
"""
import asyncio
import os
import sys

# Add agents to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agents'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


async def main():
    """Start the swarm"""
    
    # Import here after path is set
    from swarm import SolanaImmuneSystem, main as swarm_main
    
    # Run the swarm
    await swarm_main()


if __name__ == "__main__":
    print("Starting Solana Immune System swarm...")
    print("Press Ctrl+C to stop")
    asyncio.run(main())
