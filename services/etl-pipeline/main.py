from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from shared.config import get_settings
from shared.logging_config import setup_logging

from .pipeline import process_batch

settings = get_settings()
setup_logging(settings.log_level)

app = FastAPI(title="ETL Pipeline", version="0.1.0")


class ProcessRequest(BaseModel):
    source_type: str  # permit | bid | license
    storage_path: str


@app.post("/process")
async def process(request: ProcessRequest) -> dict:
    """Process a batch of raw records through the ETL pipeline."""
    result = await process_batch(request.source_type, request.storage_path)
    return result


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "etl-pipeline"}
