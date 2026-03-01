from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class LeadContact(BaseModel):
    """Compact contact info for leads (short field names for Firestore size)."""
    n: str = ""  # name
    p: str = ""  # phone
    e: str = ""  # email


class LeadContractor(BaseModel):
    """Compact contractor info for leads."""
    n: str = ""  # name
    p: str = ""  # phone
    lic: str = ""  # license number


class Lead(BaseModel):
    """Unified lead document for Firestore. Target: <2KB per document."""
    id: str
    type: str  # permit | bid
    trade: str = ""
    title: str = ""
    value: float | None = None
    addr: str = ""
    geo_lat: float | None = None
    geo_lng: float | None = None
    owner: LeadContact = Field(default_factory=LeadContact)
    gc: LeadContractor = Field(default_factory=LeadContractor)
    status: str = "active"
    posted: datetime | None = None
    deadline: datetime | None = None
    score: int = 0
    src: str = ""  # source_id
    keywords: list[str] = Field(default_factory=list)
    updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
