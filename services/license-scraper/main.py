from __future__ import annotations

from fastapi import BackgroundTasks, FastAPI

from shared.config import get_settings
from shared.logging_config import setup_logging

from .orchestrator import run_scrape

settings = get_settings()
setup_logging(settings.log_level)

app = FastAPI(title="License Scraper", version="0.1.0")


@app.post("/scrape")
async def scrape(
    background_tasks: BackgroundTasks, day_of_month: int | None = None
) -> dict:
    """Triggered by Cloud Scheduler daily. Rotates through state scrapers."""
    background_tasks.add_task(run_scrape, day_of_month)
    return {"status": "started", "day_of_month": day_of_month}


@app.post("/scrape/sync")
async def scrape_sync(day_of_month: int | None = None) -> dict:
    """Synchronous scrape (for testing)."""
    result = await run_scrape(day_of_month)
    return result


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "license-scraper"}
