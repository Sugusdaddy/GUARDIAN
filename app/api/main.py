"""
GUARDIAN API Server - FastAPI backend for dashboard and integrations
"""
import asyncio
import json
import sys
import os
from datetime import datetime

# Fix Windows encoding
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import structlog

# Add agents to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "agents"))

from core.database import get_db
from core.config import config
from core.embeddings import get_scorer

# Import swap routes
try:
    from swap_routes import router as swap_router
    HAS_SWAP_ROUTES = True
except ImportError:
    HAS_SWAP_ROUTES = False

# Import evacuate routes
try:
    from evacuate_routes import router as evacuate_router
    HAS_EVACUATE_ROUTES = True
except ImportError:
    HAS_EVACUATE_ROUTES = False

logger = structlog.get_logger()

# WebSocket connections for real-time updates
websocket_connections: List[WebSocket] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown"""
    logger.info("GUARDIAN API starting...")
    yield
    logger.info("GUARDIAN API shutting down...")


app = FastAPI(
    title="GUARDIAN API",
    description="""
# GUARDIAN - Solana Immune System API

Autonomous multi-agent security infrastructure for Solana with 16 specialized AI agents
providing 24/7 threat detection and autonomous response.

## Features

* 🔭 **Real-time Monitoring** - Continuous transaction and contract monitoring
* 🧠 **AI-Powered Analysis** - Claude Opus integration for threat analysis
* 🤖 **ML Risk Prediction** - Machine learning for risk scoring
* 🛡️ **Risk-Aware Trading** - SwapGuard protects every DEX transaction
* 🚨 **Emergency Evacuation** - One-click wallet protection
* 🍯 **Active Defense** - Honeypot traps for attackers
* 🇰🇵 **State-Actor Tracking** - First on Solana
* 🌐 **Network Health** - Infrastructure monitoring

## Authentication

Currently open API. Authentication will be added in future versions.

## Rate Limiting

No rate limiting currently applied. Fair usage expected.
    """,
    version="0.1.0",
    lifespan=lifespan,
    contact={
        "name": "GUARDIAN Team",
        "url": "https://github.com/Sugusdaddy/GUARDIAN",
        "email": "security@guardian.sol"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    openapi_tags=[
        {
            "name": "status",
            "description": "System status and health checks"
        },
        {
            "name": "threats",
            "description": "Threat detection and management"
        },
        {
            "name": "intelligence",
            "description": "Blacklist, watchlist, and threat intelligence"
        },
        {
            "name": "agents",
            "description": "Agent statistics and management"
        },
        {
            "name": "swap",
            "description": "SwapGuard - Risk-aware trading protection"
        },
        {
            "name": "evacuate",
            "description": "Evacuator - Emergency wallet protection"
        },
        {
            "name": "network",
            "description": "Solana network health monitoring"
        },
        {
            "name": "quantum",
            "description": "Quantum readiness assessment"
        }
    ]
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include swap routes (SwapGuard - Risk-Aware Trading)
if HAS_SWAP_ROUTES:
    app.include_router(swap_router)
    logger.info("🛡️ SwapGuard routes loaded")

# Include evacuate routes (Emergency Evacuation)
if HAS_EVACUATE_ROUTES:
    app.include_router(evacuate_router)
    logger.info("🚨 Evacuator routes loaded")


# ============== Pydantic Models ==============

class ThreatCreate(BaseModel):
    threat_type: str
    severity: float
    target_address: Optional[str] = None
    description: str
    evidence: Optional[Dict] = None
    detected_by: str = "API"


class ThreatUpdate(BaseModel):
    status: Optional[str] = None
    resolution: Optional[str] = None


class BlacklistEntry(BaseModel):
    address: str
    reason: str
    severity: int = 50


class WatchlistEntry(BaseModel):
    address: str
    label: Optional[str] = None
    reason: Optional[str] = None


class RiskScoreRequest(BaseModel):
    address: str
    threat_type: Optional[str] = "Unknown"
    context: Optional[Dict] = None


# ============== Dashboard ==============

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve dashboard"""
    dashboard_path = Path(__file__).parent.parent / "dashboard" / "index.html"
    if dashboard_path.exists():
        return FileResponse(dashboard_path)
    return HTMLResponse("<h1>GUARDIAN Dashboard</h1><p>Dashboard not found</p>")


# ============== Status ==============

@app.get("/api/status", tags=["status"])
async def get_status():
    """
    Get system status and health information.

    Returns current system status including:
    - Active and resolved threats
    - Agent statistics
    - Network configuration
    - Database health
    """
    db = get_db()
    stats = db.get_threat_stats()
    agents = db.get_all_agent_stats()
    
    return {
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "network": config.network,
        "model": config.model,
        "threats": {
            "active": stats.get("by_status", {}).get("active", 0),
            "resolved": stats.get("by_status", {}).get("resolved", 0),
            "last_24h": stats.get("last_24h", 0),
            "avg_severity": stats.get("avg_severity", 0),
        },
        "agents": {
            "count": len(agents),
            "total_scans": sum(a.get("total_scans", 0) for a in agents),
            "total_threats": sum(a.get("threats_detected", 0) for a in agents),
        },
        "intelligence": {
            "blacklisted": len(db.get_blacklist()),
            "watched": len(db.get_watchlist()),
            "patterns": len(db.get_patterns()),
        }
    }


@app.get("/api/stats")
async def get_stats():
    """Get detailed statistics"""
    db = get_db()
    return db.get_threat_stats()


# ============== Threats ==============

@app.get("/api/threats")
async def list_threats(
    status: Optional[str] = Query(None, description="Filter by status"),
    threat_type: Optional[str] = Query(None, description="Filter by type"),
    min_severity: Optional[float] = Query(None, description="Minimum severity"),
    limit: int = Query(50, le=500)
):
    """List threats with optional filters"""
    db = get_db()
    
    if status == "active":
        threats = db.get_active_threats(limit=limit)
    elif threat_type:
        threats = db.get_threats_by_type(threat_type, limit=limit)
    else:
        rows = db.conn.execute(
            "SELECT * FROM threats ORDER BY severity DESC, detected_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
        threats = [dict(r) for r in rows]
    
    if min_severity:
        threats = [t for t in threats if t.get("severity", 0) >= min_severity]
    
    # Parse JSON evidence if it's a string
    for t in threats:
        if isinstance(t.get("evidence"), str):
            try:
                t["evidence"] = json.loads(t["evidence"])
            except:
                pass
    
    return {"threats": threats, "count": len(threats)}


@app.get("/api/threats/{threat_id}")
async def get_threat(threat_id: int):
    """Get single threat with reasoning"""
    db = get_db()
    threat = db.get_threat(threat_id)
    
    if not threat:
        raise HTTPException(status_code=404, detail="Threat not found")
    
    reasoning = db.get_reasoning_for_threat(threat_id)
    
    return {
        "threat": threat,
        "reasoning": reasoning
    }


@app.post("/api/threats")
async def create_threat(threat: ThreatCreate):
    """Create a new threat manually"""
    db = get_db()
    
    threat_data = threat.model_dump()
    threat_id = db.insert_threat(threat_data)
    
    # Broadcast to WebSocket clients
    await broadcast_event("threat_created", {"id": threat_id, **threat_data})
    
    return {"id": threat_id, "status": "created"}


@app.patch("/api/threats/{threat_id}")
async def update_threat(threat_id: int, update: ThreatUpdate):
    """Update threat status"""
    db = get_db()
    
    threat = db.get_threat(threat_id)
    if not threat:
        raise HTTPException(status_code=404, detail="Threat not found")
    
    if update.status:
        db.update_threat_status(threat_id, update.status, update.resolution)
    
    return {"status": "updated"}


# ============== Blacklist ==============

@app.get("/api/blacklist")
async def get_blacklist(min_severity: int = Query(0)):
    """Get blacklisted addresses"""
    db = get_db()
    return {"addresses": db.get_blacklist(min_severity=min_severity)}


@app.post("/api/blacklist")
async def add_to_blacklist(entry: BlacklistEntry):
    """Add address to blacklist"""
    db = get_db()
    db.add_to_blacklist(entry.address, entry.reason, "API", entry.severity)
    return {"status": "added"}


@app.delete("/api/blacklist/{address}")
async def remove_from_blacklist(address: str):
    """Remove address from blacklist"""
    db = get_db()
    db.conn.execute("DELETE FROM blacklist WHERE address = ?", (address,))
    db.conn.commit()
    return {"status": "removed"}


# ============== Watchlist ==============

@app.get("/api/watchlist")
async def get_watchlist():
    """Get watched addresses"""
    db = get_db()
    return {"addresses": db.get_watchlist()}


@app.post("/api/watchlist")
async def add_to_watchlist(entry: WatchlistEntry):
    """Add address to watchlist"""
    db = get_db()
    db.add_to_watchlist(entry.address, entry.label or entry.address[:8], "API", entry.reason)
    return {"status": "added"}


@app.delete("/api/watchlist/{address}")
async def remove_from_watchlist(address: str):
    """Remove address from watchlist"""
    db = get_db()
    db.conn.execute("DELETE FROM watchlist WHERE address = ?", (address,))
    db.conn.commit()
    return {"status": "removed"}


# ============== Agents ==============

@app.get("/api/agents")
async def get_agents():
    """Get agent statistics"""
    db = get_db()
    return {"agents": db.get_all_agent_stats()}


# ============== Patterns ==============

@app.get("/api/patterns")
async def get_patterns(
    pattern_type: Optional[str] = None,
    min_confidence: float = Query(0.0, ge=0, le=1)
):
    """Get learned patterns"""
    db = get_db()
    return {"patterns": db.get_patterns(pattern_type, min_confidence)}


# ============== Risk Scoring ==============

@app.post("/api/score")
async def score_address(request: RiskScoreRequest):
    """Score an address for risk"""
    db = get_db()
    scorer = get_scorer()
    
    # Build threat-like object for scoring
    threat = {
        "threat_type": request.threat_type,
        "severity": 50,
        "target_address": request.address,
        "description": f"Risk assessment for {request.address}",
        "evidence": request.context or {}
    }
    
    blacklist = set(b["address"] for b in db.get_blacklist())
    patterns = db.get_patterns(min_confidence=0.5)
    
    result = scorer.score_threat(threat, blacklist, patterns)
    
    return {
        "address": request.address,
        "risk_score": result["final_score"],
        "recommendation": result["recommendation"],
        "details": result
    }


# ============== WebSocket for Real-time Updates ==============

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        while True:
            # Keep connection alive, receive any messages
            data = await websocket.receive_text()
            # Could handle client messages here
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)


async def broadcast_event(event_type: str, data: Dict):
    """Broadcast event to all WebSocket clients"""
    message = json.dumps({"type": event_type, "data": data, "timestamp": datetime.now().isoformat()})
    
    for ws in websocket_connections[:]:
        try:
            await ws.send_text(message)
        except Exception:
            websocket_connections.remove(ws)


# ============== Pump.fun Monitoring ==============

@app.get("/api/pumpfun/new")
async def get_new_pumpfun_tokens(limit: int = Query(30, le=100)):
    """Get recently launched pump.fun tokens with risk analysis"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "agents"))
        from integrations.pumpfun import get_pumpfun_monitor
        
        monitor = get_pumpfun_monitor()
        tokens = await monitor.scan_new_tokens(limit=limit)
        return {"tokens": tokens, "count": len(tokens), "network": "mainnet"}
    except Exception as e:
        logger.error(f"Pump.fun scan error: {e}")
        return {"tokens": [], "count": 0, "error": str(e)}

@app.get("/api/pumpfun/trending")
async def get_trending_pumpfun_tokens(limit: int = Query(20, le=50)):
    """Get trending pump.fun tokens"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "agents"))
        from integrations.pumpfun import get_pumpfun_monitor
        
        monitor = get_pumpfun_monitor()
        tokens = await monitor.scan_trending(limit=limit)
        return {"tokens": tokens, "count": len(tokens)}
    except Exception as e:
        return {"tokens": [], "count": 0, "error": str(e)}

@app.get("/api/pumpfun/analyze/{mint}")
async def analyze_pumpfun_token(mint: str):
    """Analyze a specific pump.fun token"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "agents"))
        from integrations.pumpfun import get_pumpfun
        
        pf = get_pumpfun()
        token_info = await pf.get_token_details(mint)
        if token_info:
            analysis = await pf.analyze_token(token_info)
            return analysis
        return {"error": "Token not found", "mint": mint}
    except Exception as e:
        return {"error": str(e), "mint": mint}

@app.get("/api/dex/liquidity/{token}")
async def get_token_liquidity(token: str):
    """Get liquidity info from DexScreener"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "agents"))
        from integrations.pumpfun import get_dexscreener
        
        dex = get_dexscreener()
        result = await dex.analyze_liquidity(token)
        return result
    except Exception as e:
        return {"error": str(e), "token": token}


# ============== Live Solana Analysis ==============

@app.get("/api/analyze/token/{mint}")
async def analyze_token(mint: str):
    """Analyze a Solana token for risks"""
    try:
        from integrations.solana_scanner import get_scanner
        scanner = get_scanner()
        result = await scanner.analyze_token(mint)
        return result
    except ImportError:
        return {"error": "Scanner not available", "mint": mint}
    except Exception as e:
        return {"error": str(e), "mint": mint}

@app.get("/api/analyze/address/{address}")
async def analyze_address(address: str):
    """Analyze a Solana address for suspicious activity"""
    try:
        from integrations.solana_scanner import get_scanner
        scanner = get_scanner()
        result = await scanner.check_address(address)
        return result
    except ImportError:
        # Fallback to database check
        db = get_db()
        is_blacklisted = db.is_blacklisted(address)
        return {
            "address": address,
            "risk_score": 90 if is_blacklisted else 20,
            "blacklisted": is_blacklisted,
            "recommendation": "BLOCK" if is_blacklisted else "SAFE"
        }
    except Exception as e:
        return {"error": str(e), "address": address}

@app.get("/api/analyze/tx/{signature}")
async def analyze_transaction(signature: str):
    """Analyze a Solana transaction"""
    try:
        from integrations.solana_scanner import get_scanner
        scanner = get_scanner()
        result = await scanner.analyze_transaction(signature)
        return result
    except Exception as e:
        return {"error": str(e), "signature": signature}


# ============== Health ==============

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# ============== Run ==============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
