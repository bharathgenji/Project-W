from __future__ import annotations

from fastapi import BackgroundTasks, FastAPI

from shared.config import get_settings
from shared.logging_config import setup_logging

from .ingester import run_ingestion

settings = get_settings()
setup_logging(settings.log_level)

app = FastAPI(title="Permit Ingester", version="0.1.0")


@app.post("/ingest")
async def ingest(background_tasks: BackgroundTasks, mode: str = "incremental") -> dict:
    """Triggered by Cloud Scheduler daily to ingest permits from Socrata portals."""
    background_tasks.add_task(run_ingestion, mode)
    return {"status": "started", "mode": mode}


@app.post("/ingest/sync")
async def ingest_sync(mode: str = "incremental") -> dict:
    """Synchronous ingestion (for testing)."""
    result = await run_ingestion(mode)
    return result


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "permit-ingester"}
