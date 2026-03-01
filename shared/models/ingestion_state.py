from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class IngestionState(BaseModel):
    source_id: str
    last_run: datetime = Field(default_factory=datetime.utcnow)
    last_record_date: str = ""
    records_ingested: int = 0
    errors: int = 0
