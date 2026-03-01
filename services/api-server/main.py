from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from shared.config import get_settings
from shared.logging_config import setup_logging

from .dependencies import get_cache, get_firestore
from .routers import alerts, contractors, dashboard, leads, markets, pipeline, search
from .websocket_manager import manager as ws_manager

settings = get_settings()
setup_logging(settings.log_level)

app = FastAPI(title="LeadGen MVP API", version="0.2.0")

# CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(leads.router)
app.include_router(search.router)
app.include_router(contractors.router)
app.include_router(dashboard.router)
app.include_router(markets.router)
app.include_router(alerts.router)
app.include_router(pipeline.router)


# ─── Health ────────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "api-server", "version": "0.2.0"}


# ─── Admin ─────────────────────────────────────────────────────────────────────

@app.post("/api/admin/cache/clear")
def clear_cache() -> dict:
    """Bust the in-memory TTL cache (useful after manual data updates)."""
    cache = get_cache()
    cache.clear()
    return {
        "status": "cache cleared",
        "ts": datetime.now(timezone.utc).isoformat(),
    }


# ─── Internal (ETL → API) ──────────────────────────────────────────────────────

class NotifyLeadRequest(BaseModel):
    lead: dict[str, Any]


@app.post("/api/internal/notify-lead")
async def notify_lead(body: NotifyLeadRequest) -> dict:
    """Called by ETL pipeline after storing a new lead — pushes WS alerts."""
    db = get_firestore()
    await ws_manager.broadcast_new_lead(body.lead, db)
    return {"notified": True}


# ─── WebSocket ─────────────────────────────────────────────────────────────────

@app.websocket("/api/ws/alerts")
async def ws_alerts(websocket: WebSocket, email: str = "") -> None:
    """Real-time lead alerts. Connect with ?email=your@email.com"""
    if not email:
        await websocket.close(code=1008, reason="email query param required")
        return

    await ws_manager.connect(email, websocket)
    try:
        while True:
            # Keep-alive: client can send pings, we echo back
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(email)


# ─── Frontend (static React build) ─────────────────────────────────────────────

frontend_dist = Path(__file__).parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
