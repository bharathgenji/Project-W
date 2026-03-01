"""Unit tests for shared.models — Pydantic model validation and defaults."""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pytest

_PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from shared.models import (  # noqa: E402
    Address,
    BidContact,
    BidLocation,
    BidRecord,
    ContactInfo,
    ContractorLicense,
    IngestionState,
    Lead,
    LeadContact,
    LeadContractor,
    PermitRecord,
)


# ---------------------------------------------------------------------------
# PermitRecord
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestPermitRecord:
    def test_valid_data_constructs(self):
        permit = PermitRecord(
            source_id="chicago-BLD-001",
            permit_number="BLD-001",
            permit_type="BUILDING",
            work_description="New commercial building",
            estimated_cost=500_000.0,
            status="ISSUED",
        )
        assert permit.source_id == "chicago-BLD-001"
        assert permit.permit_number == "BLD-001"
        assert permit.permit_type == "BUILDING"
        assert permit.estimated_cost == 500_000.0
        assert permit.status == "ISSUED"

    def test_defaults(self):
        permit = PermitRecord(source_id="test", permit_number="P-001")
        assert permit.permit_type == ""
        assert permit.work_description == ""
        assert permit.estimated_cost is None
        assert permit.contractor_license == ""
        assert permit.status == ""
        assert permit.filed_date is None
        assert permit.issued_date is None

    def test_address_defaults(self):
        permit = PermitRecord(source_id="test", permit_number="P-002")
        assert permit.address.street == ""
        assert permit.address.city == ""
        assert permit.address.state == ""
        assert permit.address.zip_code == ""
        assert permit.address.lat is None
        assert permit.address.lng is None

    def test_contact_defaults(self):
        permit = PermitRecord(source_id="test", permit_number="P-003")
        assert permit.owner.name == ""
        assert permit.owner.phone == ""
        assert permit.owner.email == ""
        assert permit.contractor.name == ""

    def test_raw_data_excluded_from_dict(self):
        permit = PermitRecord(
            source_id="test",
            permit_number="P-004",
            raw_data={"original": "data"},
        )
        d = permit.model_dump()
        assert "raw_data" not in d


# ---------------------------------------------------------------------------
# Address
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestAddress:
    def test_zip_alias_works(self):
        """The ``zip`` alias should populate ``zip_code``."""
        addr = Address(street="123 Main St", city="Houston", state="TX", zip="77001")
        assert addr.zip_code == "77001"

    def test_populate_by_name(self):
        """``populate_by_name=True`` means both ``zip`` and ``zip_code`` work."""
        addr = Address(zip_code="90210")
        assert addr.zip_code == "90210"

    def test_lat_lng(self):
        addr = Address(lat=29.76, lng=-95.36)
        assert addr.lat == pytest.approx(29.76)
        assert addr.lng == pytest.approx(-95.36)


# ---------------------------------------------------------------------------
# Lead
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestLead:
    def test_full_construction(self):
        lead = Lead(
            id="lead-001",
            type="permit",
            trade="ELECTRICAL",
            title="Install panel",
            value=100_000.0,
            addr="123 Main St, Houston, TX 77001",
            score=85,
            src="chicago-test",
        )
        assert lead.id == "lead-001"
        assert lead.type == "permit"
        assert lead.trade == "ELECTRICAL"
        assert lead.score == 85

    def test_defaults(self):
        lead = Lead(id="lead-002", type="bid")
        assert lead.trade == ""
        assert lead.title == ""
        assert lead.value is None
        assert lead.addr == ""
        assert lead.status == "active"
        assert lead.score == 0
        assert lead.src == ""
        assert lead.keywords == []
        assert lead.geo_lat is None
        assert lead.geo_lng is None
        assert lead.deadline is None

    def test_owner_defaults(self):
        lead = Lead(id="lead-003", type="permit")
        assert lead.owner.n == ""
        assert lead.owner.p == ""
        assert lead.owner.e == ""

    def test_gc_defaults(self):
        lead = Lead(id="lead-004", type="permit")
        assert lead.gc.n == ""
        assert lead.gc.p == ""
        assert lead.gc.lic == ""

    def test_updated_timestamp_set(self):
        lead = Lead(id="lead-005", type="permit")
        assert isinstance(lead.updated, datetime)


# ---------------------------------------------------------------------------
# BidRecord
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestBidRecord:
    def test_valid_construction(self):
        bid = BidRecord(
            source="sam.gov",
            bid_id="SAM-001",
            title="Electrical Upgrade",
            agency="VA",
            contacts=[
                BidContact(name="Jane", email="jane@gov.gov", phone="555-0001", role="primary"),
                BidContact(name="Bob", email="bob@gov.gov", role="secondary"),
            ],
        )
        assert bid.source == "sam.gov"
        assert len(bid.contacts) == 2
        assert bid.contacts[0].name == "Jane"
        assert bid.contacts[1].role == "secondary"

    def test_defaults(self):
        bid = BidRecord(source="sam.gov", bid_id="SAM-002")
        assert bid.title == ""
        assert bid.description == ""
        assert bid.agency == ""
        assert bid.naics_code == ""
        assert bid.trade_category == ""
        assert bid.estimated_value is None
        assert bid.set_aside == "NONE"
        assert bid.contacts == []
        assert bid.documents == []
        assert bid.status == ""

    def test_location_defaults(self):
        bid = BidRecord(source="sam.gov", bid_id="SAM-003")
        assert bid.location.state == ""
        assert bid.location.city == ""
        assert bid.location.zip_code == ""


# ---------------------------------------------------------------------------
# ContractorLicense
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestContractorLicense:
    def test_valid_construction(self):
        lic = ContractorLicense(
            source="TX-TDLR",
            license_number="EC-2024-1187",
            business_name="Windy City Electric Inc",
            status="ACTIVE",
        )
        assert lic.source == "TX-TDLR"
        assert lic.license_number == "EC-2024-1187"
        assert lic.status == "ACTIVE"

    def test_defaults(self):
        lic = ContractorLicense(source="CA-CSLB", license_number="CSLB-999")
        assert lic.business_name == ""
        assert lic.owner_name == ""
        assert lic.phone == ""
        assert lic.email == ""
        assert lic.bond_amount is None
        assert lic.issue_date is None
        assert lic.expiration_date is None


# ---------------------------------------------------------------------------
# IngestionState
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestIngestionState:
    def test_valid_construction(self):
        state = IngestionState(source_id="chicago-ydr8-5enu")
        assert state.source_id == "chicago-ydr8-5enu"
        assert state.records_ingested == 0
        assert state.errors == 0
        assert state.last_record_date == ""
        assert isinstance(state.last_run, datetime)


# ---------------------------------------------------------------------------
# LeadContact / LeadContractor
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestLeadContact:
    def test_defaults(self):
        c = LeadContact()
        assert c.n == ""
        assert c.p == ""
        assert c.e == ""

    def test_values(self):
        c = LeadContact(n="John", p="+17135551234", e="john@test.com")
        assert c.n == "John"


@pytest.mark.unit
class TestLeadContractor:
    def test_defaults(self):
        gc = LeadContractor()
        assert gc.n == ""
        assert gc.p == ""
        assert gc.lic == ""
