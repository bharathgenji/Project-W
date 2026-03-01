from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class Address(BaseModel):
    street: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = Field("", alias="zip")
    lat: float | None = None
    lng: float | None = None

    model_config = {"populate_by_name": True}


class ContactInfo(BaseModel):
    name: str = ""
    phone: str = ""
    email: str = ""


class PermitRecord(BaseModel):
    source_id: str
    permit_number: str
    permit_type: str = ""  # BUILDING|ELECTRICAL|PLUMBING|MECHANICAL|DEMOLITION|OTHER
    work_description: str = ""
    address: Address = Field(default_factory=Address)
    estimated_cost: float | None = None
    owner: ContactInfo = Field(default_factory=ContactInfo)
    contractor: ContactInfo = Field(default_factory=ContactInfo)
    contractor_license: str = ""
    status: str = ""  # FILED|ISSUED|COMPLETED|EXPIRED
    filed_date: datetime | None = None
    issued_date: datetime | None = None
    raw_data: dict = Field(default_factory=dict, exclude=True)  # type: ignore[assignment]
