"""Unit tests for services/etl-pipeline/normalizer — pure function tests, no external deps."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure project root is on sys.path so shared.* imports work
_PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Service dirs use hyphens — importlib handles them where dot-syntax cannot
_etl_path = str(Path(__file__).resolve().parents[2] / "services" / "etl-pipeline")
if _etl_path not in sys.path:
    sys.path.insert(0, _etl_path)

from normalizer import (  # noqa: E402
    normalize_address,
    normalize_bid_record,
    normalize_contact,
    normalize_contractor,
    normalize_permit_type,
)


# ---------------------------------------------------------------------------
# normalize_address
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestNormalizeAddress:
    def test_full_address_normalizes(self):
        raw = {
            "street": "123 MAIN STREET APT 4",
            "city": "HOUSTON",
            "state": "TX",
            "zip_code": "77001",
            "lat": 29.76,
            "lng": -95.36,
        }
        result = normalize_address(raw)

        assert result["street"] == "123 Main St Apt 4"
        assert result["city"] == "Houston"
        assert result["state"] == "TX"
        assert result["zip_code"] == "77001"
        assert result["lat"] == 29.76
        assert result["lng"] == -95.36

    def test_zip_alias_field(self):
        """``zip`` should be accepted as an alias for ``zip_code``."""
        raw = {"zip": "90210"}
        result = normalize_address(raw)
        assert result["zip_code"] == "90210"

    def test_empty_inputs_return_defaults(self):
        result = normalize_address({})
        assert result["street"] == ""
        assert result["city"] == ""
        assert result["state"] == ""
        assert result["zip_code"] == ""
        assert result["lat"] is None
        assert result["lng"] is None

    def test_none_values_handled(self):
        raw = {"street": None, "city": None, "state": None, "zip_code": None}
        result = normalize_address(raw)
        assert result["street"] == ""
        assert result["city"] == ""
        assert result["state"] == ""

    def test_zip_with_plus4_stripped(self):
        raw = {"zip_code": "77001-1234"}
        result = normalize_address(raw)
        assert result["zip_code"] == "77001"

    def test_state_truncated_to_two_chars(self):
        raw = {"state": "Texas"}
        result = normalize_address(raw)
        assert result["state"] == "TE"

    def test_city_title_case(self):
        raw = {"city": "  new york  "}
        result = normalize_address(raw)
        assert result["city"] == "New York"


# ---------------------------------------------------------------------------
# normalize_contact (via normalizer, which delegates to shared.utils)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestNormalizeContact:
    def test_phone_e164(self):
        raw = {"phone": "(713) 555-1234"}
        result = normalize_contact(raw)
        assert result["phone"] == "+17135551234"

    def test_email_lowered(self):
        raw = {"email": "John@Example.COM"}
        result = normalize_contact(raw)
        assert result["email"] == "john@example.com"

    def test_short_field_aliases(self):
        raw = {"n": "Jane Doe", "p": "7135551234", "e": "JANE@TEST.COM"}
        result = normalize_contact(raw)
        assert result["name"] == "Jane Doe"
        assert result["phone"] == "+17135551234"
        assert result["email"] == "jane@test.com"

    def test_empty_returns_defaults(self):
        result = normalize_contact({})
        assert result["name"] == ""
        assert result["phone"] == ""
        assert result["email"] == ""


# ---------------------------------------------------------------------------
# normalize_contractor
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestNormalizeContractor:
    def test_business_name_parsed(self):
        raw = {"name": "SMITH PLUMBING LLC", "phone": "(713) 555-1234"}
        result = normalize_contractor(raw)
        assert result["name"] == "Smith Plumbing"
        assert result["entity_type"] == "LLC"
        assert result["phone"] == "+17135551234"

    def test_license_number_stripped(self):
        raw = {"name": "Test Co", "license_number": "  EC-12345  "}
        result = normalize_contractor(raw)
        assert result["license_number"] == "EC-12345"

    def test_short_field_aliases(self):
        raw = {"n": "ABC CORP", "p": "3125551000", "lic": "GC-001"}
        result = normalize_contractor(raw)
        assert result["name"] == "Abc"
        assert result["entity_type"] == "CORP"

    def test_empty_returns_defaults(self):
        result = normalize_contractor({})
        assert result["name"] == ""
        assert result["entity_type"] == ""
        assert result["phone"] == ""
        assert result["license_number"] == ""


# ---------------------------------------------------------------------------
# normalize_permit_type
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestNormalizePermitType:
    def test_building_match(self):
        assert normalize_permit_type("Building Permit") == "BUILDING"

    def test_electrical_match(self):
        assert normalize_permit_type("ELECTRICAL PERMIT") == "ELECTRICAL"

    def test_plumbing_match(self):
        assert normalize_permit_type("plumbing work") == "PLUMBING"

    def test_demolition_match(self):
        assert normalize_permit_type("PERMIT - WRECKING/DEMOLITION") == "DEMOLITION"

    def test_unknown_returns_other(self):
        assert normalize_permit_type("some random text") == "OTHER"

    def test_empty_returns_other(self):
        assert normalize_permit_type("") == "OTHER"

    def test_none_input_returns_other(self):
        assert normalize_permit_type(None) == "OTHER"  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# normalize_bid_record
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestNormalizeBidRecord:
    def test_contacts_normalized(self):
        raw = {
            "title": "  ROOF REPLACEMENT  ",
            "description": "  Replace roof  ",
            "contacts": [{"phone": "(303) 555-1000", "email": "BID@Test.COM"}],
            "location": {"state": " co ", "city": " denver ", "zip_code": "80202"},
        }
        result = normalize_bid_record(raw)
        assert result["title"] == "ROOF REPLACEMENT"
        assert result["description"] == "Replace roof"
        assert result["contacts"][0]["phone"] == "+13035551000"
        assert result["contacts"][0]["email"] == "bid@test.com"
        assert result["location"]["state"] == "CO"
        assert result["location"]["city"] == "Denver"

    def test_empty_bid_record(self):
        result = normalize_bid_record({})
        assert result["title"] == ""
        assert result["description"] == ""
        assert result["contacts"] == []
        assert result["location"]["state"] == ""
