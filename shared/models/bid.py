from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class BidLocation(BaseModel):
    state: str = ""
    city: str = ""
    zip_code: str = ""


class BidContact(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    role: str = ""


class BidDocument(BaseModel):
    url: str = ""
    doc_type: str = ""


class BidRecord(BaseModel):
    source: str  # sam.gov | usaspending
    bid_id: str
    title: str = ""
    description: str = ""
    agency: str = ""
    posted_date: datetime | None = None
    response_deadline: datetime | None = None
    naics_code: str = ""
    trade_category: str = ""
    estimated_value: float | None = None
    set_aside: str = "NONE"
    location: BidLocation = Field(default_factory=BidLocation)
    contacts: list[BidContact] = Field(default_factory=list)
    documents: list[BidDocument] = Field(default_factory=list)
    status: str = ""  # PRESOLICITATION|ACTIVE|CLOSED|AWARDED
    raw_data: dict = Field(default_factory=dict, exclude=True)  # type: ignore[assignment]
