from __future__ import annotations

import asyncio
import subprocess
import sys
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
from .jobs.alert_delivery import run_alert_delivery
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


@app.post("/api/internal/run-alert-delivery")
async def run_alerts() -> dict:
    """Trigger email alert delivery job (call from Cloud Scheduler or cron)."""
    db = get_firestore()
    return await run_alert_delivery(db)


# ── Ingest state (in-memory, persisted to Firestore _meta doc) ────────────────
_ingest_running = False
_REPO_ROOT = Path(__file__).parent.parent.parent


def _read_ingest_status(db: Any) -> dict:
    try:
        doc = db.db.collection("_meta").document("ingest_status").get()
        return doc.to_dict() if doc.exists else {}
    except Exception:
        return {}


def _write_ingest_status(db: Any, status: dict) -> None:
    try:
        db.db.collection("_meta").document("ingest_status").set(status)
    except Exception:
        pass


@app.get("/api/ingest/status")
def ingest_status() -> dict:
    """Return last ingestion run metadata."""
    db = get_firestore()
    meta = _read_ingest_status(db)
    return {
        "running": _ingest_running,
        "last_run": meta.get("last_run"),
        "last_run_leads": meta.get("leads_stored", 0),
        "last_run_contractors": meta.get("contractors_updated", 0),
        "last_run_sources": meta.get("sources", []),
        "success": meta.get("success"),
        "error": meta.get("error"),
    }


@app.post("/api/ingest/run")
async def run_ingest(days: int = 30, max_per_portal: int = 500) -> dict:
    """Trigger a full live data ingestion in the background."""
    global _ingest_running
    if _ingest_running:
        return {"status": "already_running", "message": "Ingestion already in progress"}

    _ingest_running = True
    db = get_firestore()
    started_at = datetime.now(timezone.utc).isoformat()

    async def _run():
        global _ingest_running
        try:
            env = {
                "PYTHONPATH": str(_REPO_ROOT),
                "FIRESTORE_EMULATOR_HOST": "localhost:8681",
                "GOOGLE_CLOUD_PROJECT": get_settings().firestore_project_id,
            }
            # Copy current process env and overlay
            import os
            full_env = {**os.environ, **env}

            proc = await asyncio.create_subprocess_exec(
                sys.executable,
                str(_REPO_ROOT / "scripts" / "run_ingest.py"),
                "--days", str(days),
                "--max-per-portal", str(max_per_portal),
                cwd=str(_REPO_ROOT),
                env=full_env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            stdout, _ = await proc.communicate()
            output = stdout.decode() if stdout else ""

            # Parse lead count from output
            leads_stored = 0
            contractors = 0
            for line in output.splitlines():
                if "Leads stored:" in line:
                    try: leads_stored = int(line.split(":")[1].strip())
                    except: pass
                if "Contractors:" in line:
                    try: contractors = int(line.split(":")[1].strip())
                    except: pass

            _write_ingest_status(db, {
                "last_run": datetime.now(timezone.utc).isoformat(),
                "started_at": started_at,
                "leads_stored": leads_stored,
                "contractors_updated": contractors,
                "sources": ["chicago", "austin", "sf", "nyc", "san-diego", "sam.gov", "usaspending"],
                "exit_code": proc.returncode,
                "success": proc.returncode == 0,
            })
            # Clear dashboard cache so next load shows fresh counts
            get_cache().clear()

        except Exception as exc:
            _write_ingest_status(db, {
                "last_run": datetime.now(timezone.utc).isoformat(),
                "error": str(exc),
                "success": False,
            })
        finally:
            _ingest_running = False

    asyncio.create_task(_run())
    return {"status": "started", "message": "Ingestion running in background — check /api/ingest/status"}


@app.get("/api/config")
def get_app_config() -> dict:
    """Frontend app configuration — exposes public keys and feature flags."""
    s = get_settings()
    return {
        "firebase_project_id": s.firebase_project_id,
        "firebase_web_api_key": s.firebase_web_api_key,
        "google_maps_api_key": s.google_maps_api_key,
        "features": {
            "ai_enrichment": s.has_ai_enrichment,
            "email_alerts": s.has_email,
            "auth": bool(s.firebase_project_id and s.firebase_web_api_key),
            "maps": bool(s.google_maps_api_key),
        },
    }


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


# ─── Frontend (static React build + SPA catch-all) ──────────────────────────────

frontend_dist = Path(__file__).parent / "frontend" / "dist"
if frontend_dist.exists():
    # Serve static assets (JS/CSS/images) under /assets
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    # SPA catch-all: serve index.html for all non-API routes so React Router works
    from fastapi.responses import FileResponse

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str) -> FileResponse:
        # If it looks like a static file, try to serve it
        candidate = frontend_dist / full_path
        if candidate.is_file():
            return FileResponse(str(candidate))
        # Otherwise serve index.html (React Router handles the path)
        return FileResponse(str(frontend_dist / "index.html"))
