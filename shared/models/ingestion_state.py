from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class IngestionState(BaseModel):
    source_id: str
    last_run: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_record_date: str = ""
    records_ingested: int = 0
    errors: int = 0
