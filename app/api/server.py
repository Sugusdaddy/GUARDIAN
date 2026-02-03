"""
Solana Immune System - API Server
Provides real-time data for the dashboard
"""
import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, List

from aiohttp import web
import structlog

# Add agents to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'agents'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

logger = structlog.get_logger()

# Global state (in production, use Redis or database)
swarm_state = {
    "running": False,
    "start_time": None,
    "agents": [],
    "threats": [],
    "stats": {
        "total_threats": 0,
        "blocked_threats": 0,
        "false_positives": 0,
        "sol_protected": 0
    }
}


async def get_status(request):
    """GET /api/status - Get system status"""
    return web.json_response({
        "status": "active" if swarm_state["running"] else "inactive",
        "uptime_seconds": (datetime.now() - swarm_state["start_time"]).total_seconds() 
                         if swarm_state["start_time"] else 0,
        "network": os.getenv("SOLANA_NETWORK", "devnet"),
        "timestamp": datetime.now().isoformat()
    })


async def get_agents(request):
    """GET /api/agents - Get all agents status"""
    agents = [
        {"role": "SENTINEL", "type": "Sentinel", "status": "active", "threats": 12},
        {"role": "SCANNER", "type": "Scanner", "status": "active", "threats": 28},
        {"role": "ORACLE", "type": "Oracle", "status": "active", "threats": 45},
        {"role": "COORDINATOR", "type": "Coordinator", "status": "active", "threats": 0},
        {"role": "GUARDIAN", "type": "Guardian", "status": "active", "threats": 8},
        {"role": "INTEL", "type": "Intel", "status": "active", "threats": 0},
        {"role": "REPORTER", "type": "Reporter", "status": "active", "threats": 0},
        {"role": "AUDITOR", "type": "Auditor", "status": "active", "threats": 2},
        {"role": "HUNTER", "type": "Hunter", "status": "active", "threats": 5},
        {"role": "HEALER", "type": "Healer", "status": "active", "threats": 0},
    ]
    return web.json_response({"agents": agents, "total": len(agents)})


async def get_threats(request):
    """GET /api/threats - Get recent threats"""
    # Simulated threats for demo
    threats = [
        {
            "id": 47,
            "type": "RugPull",
            "target": "ScamToken111...111",
            "severity": 94,
            "detected_by": "SCANNER",
            "status": "blocked",
            "timestamp": "2026-02-03T19:30:00Z"
        },
        {
            "id": 46,
            "type": "Honeypot",
            "target": "HoneyPot222...xyz",
            "severity": 89,
            "detected_by": "SCANNER",
            "status": "blocked",
            "timestamp": "2026-02-03T19:25:00Z"
        },
        {
            "id": 45,
            "type": "SuspiciousTransfer",
            "target": "Whale333...abc",
            "severity": 62,
            "detected_by": "SENTINEL",
            "status": "monitoring",
            "timestamp": "2026-02-03T19:20:00Z"
        },
        {
            "id": 44,
            "type": "PriceManipulation",
            "target": "Token444...def",
            "severity": 58,
            "detected_by": "ORACLE",
            "status": "investigating",
            "timestamp": "2026-02-03T19:15:00Z"
        },
        {
            "id": 43,
            "type": "PhishingContract",
            "target": "FakeDex555...ghi",
            "severity": 91,
            "detected_by": "SCANNER",
            "status": "blocked",
            "timestamp": "2026-02-03T19:10:00Z"
        }
    ]
    return web.json_response({"threats": threats, "total": len(threats)})


async def get_stats(request):
    """GET /api/stats - Get system statistics"""
    stats = {
        "agents_active": 10,
        "agents_total": 10,
        "threats_detected_24h": 47,
        "threats_blocked": 12,
        "false_positives": 2,
        "accuracy_rate": 94.7,
        "avg_response_time_seconds": 28,
        "sol_protected": 15000,
        "timestamp": datetime.now().isoformat()
    }
    return web.json_response(stats)


async def get_reasoning(request):
    """GET /api/reasoning/{threat_id} - Get reasoning for a threat"""
    threat_id = request.match_info.get('threat_id', '0')
    
    # Simulated reasoning data
    reasoning = {
        "threat_id": int(threat_id),
        "agent": "SCANNER",
        "commit_hash": "77cabcf76d401713df6ea14b78bf91bb...",
        "commit_timestamp": "2026-02-03T19:29:00Z",
        "reveal_timestamp": "2026-02-03T19:30:00Z",
        "reasoning_text": """Analysis of token ScamToken111...111:

1. MINT AUTHORITY: ENABLED - Critical risk. Can mint unlimited tokens.
2. FREEZE AUTHORITY: ENABLED - Can freeze user accounts.
3. TOP HOLDER: 95% - Single wallet controls almost entire supply.
4. LIQUIDITY: $500 - Extremely low, easy to drain.
5. TOKEN AGE: 2 hours - Very new, unestablished.

VERDICT: 94% probability of rug pull.
RECOMMENDATION: BLOCK immediately and alert community.

Reasoning committed on-chain before action.
Hash verified after reveal.""",
        "verified": True,
        "solana_signature": "3m11Amh6bTvmXrbRC2xnq9dwfqSwh9koLKzBQwBuU7gg..."
    }
    return web.json_response(reasoning)


async def health_check(request):
    """GET /health - Health check endpoint"""
    return web.json_response({"status": "healthy", "timestamp": datetime.now().isoformat()})


def create_app():
    """Create the web application"""
    app = web.Application()
    
    # Enable CORS
    async def cors_middleware(app, handler):
        async def middleware_handler(request):
            if request.method == "OPTIONS":
                response = web.Response()
            else:
                response = await handler(request)
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
            return response
        return middleware_handler
    
    app.middlewares.append(cors_middleware)
    
    # Routes
    app.router.add_get("/health", health_check)
    app.router.add_get("/api/status", get_status)
    app.router.add_get("/api/agents", get_agents)
    app.router.add_get("/api/threats", get_threats)
    app.router.add_get("/api/stats", get_stats)
    app.router.add_get("/api/reasoning/{threat_id}", get_reasoning)
    
    return app


def main():
    """Run the API server"""
    print("""
    ==============================================================
    |  SOLANA IMMUNE SYSTEM - API Server                         |
    ==============================================================
    """)
    
    swarm_state["running"] = True
    swarm_state["start_time"] = datetime.now()
    
    app = create_app()
    port = int(os.getenv("API_PORT", "8080"))
    
    print(f"Starting API server on http://localhost:{port}")
    print(f"Dashboard: Open app/dashboard/index.html in browser")
    print(f"API Docs: http://localhost:{port}/api/status")
    
    web.run_app(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
