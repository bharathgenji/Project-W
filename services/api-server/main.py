from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from shared.config import get_settings
from shared.logging_config import setup_logging

from .routers import alerts, contractors, dashboard, leads, markets, search

settings = get_settings()
setup_logging(settings.log_level)

app = FastAPI(title="LeadGen MVP API", version="0.1.0")

# CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8000"],
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


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "api-server"}


# Serve React frontend (built static files)
frontend_dist = Path(__file__).parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
