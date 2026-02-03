#!/usr/bin/env python3
"""Quick test of demo - runs automatically without input"""
import sys
import os

if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8')

import asyncio

# Import from demo_video
sys.path.insert(0, 'scripts')
from demo_video import (
    scene_intro,
    scene_honeypot_detection,
    scene_swapguard,
    scene_lazarus,
    scene_evacuation,
    scene_finale,
    Colors
)

async def quick_demo():
    """Run full demo automatically"""
    print(f"\n{Colors.CYAN}🎬 Running GUARDIAN Demo...{Colors.END}\n")
    
    await scene_intro()
    await scene_honeypot_detection()
    await scene_swapguard()
    await scene_lazarus()
    await scene_evacuation()
    await scene_finale()

if __name__ == "__main__":
    asyncio.run(quick_demo())
