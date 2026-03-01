from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ContractorLicense(BaseModel):
    source: str  # CA-CSLB | TX-TDLR | FL-DBPR | ...
    license_number: str
    business_name: str = ""
    owner_name: str = ""
    trade_classification: str = ""
    address_street: str = ""
    address_city: str = ""
    address_state: str = ""
    address_zip: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""
    status: str = ""  # ACTIVE|EXPIRED|SUSPENDED|REVOKED
    issue_date: datetime | None = None
    expiration_date: datetime | None = None
    bond_amount: float | None = None
    insurance: str = ""
    workers_comp: str = ""
