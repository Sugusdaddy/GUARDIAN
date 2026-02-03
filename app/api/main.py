"""
GUARDIAN API Server - FastAPI backend for dashboard and integrations
"""
import asyncio
import json
import sys
from datetime import datetime
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
    description="Solana Immune System API",
    version="2.0.0",
    lifespan=lifespan
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

@app.get("/api/status")
async def get_status():
    """Get system status"""
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
            "SELECT * FROM threats ORDER BY detected_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
        threats = [dict(r) for r in rows]
    
    if min_severity:
        threats = [t for t in threats if t.get("severity", 0) >= min_severity]
    
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


# ============== Health ==============

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# ============== Run ==============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
