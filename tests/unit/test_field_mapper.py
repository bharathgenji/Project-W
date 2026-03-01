"""Unit tests for services/permit-ingester/field_mapper — Socrata row mapping."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

_permit_path = str(Path(__file__).resolve().parents[2] / "services" / "permit-ingester")
if _permit_path not in sys.path:
    sys.path.insert(0, _permit_path)

from field_mapper import map_to_permit  # noqa: E402

# Chicago portal field mapping (mirrors the real config)
CHICAGO_FIELD_MAP: dict[str, str] = {
    "permit_number": "permit_",
    "permit_type": "permit_type",
    "work_description": "work_description",
    "address_street": "street_number",
    "address_direction": "street_direction",
    "address_street_name": "street_name",
    "address_suffix": "suffix",
    "address_city": "city",
    "address_zip": "zip_code",
    "estimated_cost": "reported_cost",
    "owner_name": "contact_1_name",
    "owner_phone": "contact_1_phone",
    "contractor_name": "contractor_1_name",
    "contractor_phone": "contractor_1_phone",
    "contractor_license": "contractor_license_",
    "status": "permit_status",
    "filed_date": "application_start_date",
    "issued_date": "issue_date",
    "lat": "latitude",
    "lng": "longitude",
}

PORTAL_ID = "chicago-ydr8-5enu"
PORTAL_STATE = "IL"


@pytest.mark.unit
class TestMapToPermit:
    """Verify Socrata raw rows are mapped to PermitRecord correctly."""

    def test_chicago_row_maps_to_permit_record(self):
        row = {
            "permit_": "BLD-2026-00451",
            "permit_type": "PERMIT - NEW CONSTRUCTION",
            "work_description": "Install new 200-amp electrical panel",
            "street_number": "4521",
            "street_direction": "N",
            "street_name": "MICHIGAN",
            "suffix": "AVE",
            "city": "CHICAGO",
            "zip_code": "60611",
            "reported_cost": "$475,000.00",
            "issue_date": "2026-02-25T00:00:00.000",
            "application_start_date": "2026-02-10T00:00:00.000",
            "contact_1_name": "LAKEFRONT PROPERTIES LLC",
            "contact_1_phone": "3125551001",
            "contractor_1_name": "WINDY CITY ELECTRIC INC",
            "contractor_1_phone": "3125552001",
            "contractor_license_": "EC-2024-1187",
            "latitude": "41.8910",
            "longitude": "-87.6240",
        }

        permit = map_to_permit(row, PORTAL_ID, CHICAGO_FIELD_MAP, PORTAL_STATE)

        assert permit.permit_number == "BLD-2026-00451"
        assert permit.source_id == f"{PORTAL_ID}-BLD-2026-00451"
        assert permit.work_description == "Install new 200-amp electrical panel"
        assert permit.address.street == "4521 N MICHIGAN AVE"
        assert permit.address.state == "IL"
        assert permit.address.zip_code == "60611"
        assert permit.estimated_cost == 475_000.0
        assert permit.owner.name == "LAKEFRONT PROPERTIES LLC"
        assert permit.contractor.name == "WINDY CITY ELECTRIC INC"
        assert permit.contractor_license == "EC-2024-1187"
        assert permit.issued_date is not None
        assert permit.issued_date.year == 2026
        assert permit.address.lat == pytest.approx(41.891)
        assert permit.address.lng == pytest.approx(-87.624)

    def test_cost_parsing_dollar_sign_and_commas(self):
        row = {
            "permit_": "TEST-001",
            "reported_cost": "$500,000",
        }
        permit = map_to_permit(row, PORTAL_ID, CHICAGO_FIELD_MAP, PORTAL_STATE)
        assert permit.estimated_cost == 500_000.0

    def test_cost_parsing_plain_number(self):
        row = {
            "permit_": "TEST-002",
            "reported_cost": "250000",
        }
        permit = map_to_permit(row, PORTAL_ID, CHICAGO_FIELD_MAP, PORTAL_STATE)
        assert permit.estimated_cost == 250_000.0

    def test_cost_parsing_invalid_returns_none(self):
        row = {
            "permit_": "TEST-003",
            "reported_cost": "N/A",
        }
        permit = map_to_permit(row, PORTAL_ID, CHICAGO_FIELD_MAP, PORTAL_STATE)
        assert permit.estimated_cost is None

    def test_missing_fields_handled_gracefully(self):
        """A row with only the permit number should not crash."""
        row = {"permit_": "BLD-MINIMAL"}
        permit = map_to_permit(row, PORTAL_ID, CHICAGO_FIELD_MAP, PORTAL_STATE)

        assert permit.permit_number == "BLD-MINIMAL"
        assert permit.work_description == ""
        assert permit.estimated_cost is None
        assert permit.owner.name == ""
        assert permit.contractor.name == ""
        assert permit.contractor_license == ""
        assert permit.issued_date is None
        assert permit.filed_date is None
        assert permit.address.state == "IL"  # portal_state still set

    def test_completely_empty_row(self):
        """An empty dict should still produce a PermitRecord with defaults."""
        permit = map_to_permit({}, PORTAL_ID, CHICAGO_FIELD_MAP, PORTAL_STATE)
        assert permit.source_id == f"{PORTAL_ID}-unknown"
        assert permit.permit_number == ""
        assert permit.status == "FILED"  # fallback default

    def test_permit_type_normalized(self):
        row = {"permit_": "T-001", "permit_type": "PERMIT - WRECKING/DEMOLITION"}
        permit = map_to_permit(row, PORTAL_ID, CHICAGO_FIELD_MAP, PORTAL_STATE)
        assert permit.permit_type == "DEMOLITION"

    def test_building_permit_type(self):
        row = {"permit_": "T-002", "permit_type": "PERMIT - NEW CONSTRUCTION building"}
        permit = map_to_permit(row, PORTAL_ID, CHICAGO_FIELD_MAP, PORTAL_STATE)
        assert permit.permit_type == "BUILDING"

    def test_date_parsing_various_formats(self):
        # ISO with fractional seconds
        row = {"permit_": "T-003", "issue_date": "2026-02-25T00:00:00.000"}
        permit = map_to_permit(row, PORTAL_ID, CHICAGO_FIELD_MAP, PORTAL_STATE)
        assert permit.issued_date is not None
        assert permit.issued_date.month == 2
        assert permit.issued_date.day == 25

    def test_date_parsing_mm_dd_yyyy(self):
        row = {"permit_": "T-004", "issue_date": "02/25/2026"}
        permit = map_to_permit(row, PORTAL_ID, CHICAGO_FIELD_MAP, PORTAL_STATE)
        assert permit.issued_date is not None

    def test_status_defaults_to_filed(self):
        row = {"permit_": "T-005"}
        permit = map_to_permit(row, PORTAL_ID, CHICAGO_FIELD_MAP, PORTAL_STATE)
        assert permit.status == "FILED"

    def test_status_uppercased(self):
        row = {"permit_": "T-006", "permit_status": "issued"}
        permit = map_to_permit(row, PORTAL_ID, CHICAGO_FIELD_MAP, PORTAL_STATE)
        assert permit.status == "ISSUED"

    def test_raw_data_preserved(self):
        row = {"permit_": "T-007", "extra_field": "should be in raw_data"}
        permit = map_to_permit(row, PORTAL_ID, CHICAGO_FIELD_MAP, PORTAL_STATE)
        assert permit.raw_data == row
