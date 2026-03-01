"""Unit tests for services/etl-pipeline/deduplicator — deterministic IDs and fuzzy matching."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

_etl_path = str(Path(__file__).resolve().parents[2] / "services" / "etl-pipeline")
if _etl_path not in sys.path:
    sys.path.insert(0, _etl_path)

from deduplicator import (  # noqa: E402
    find_duplicate_contractor,
    generate_contractor_id,
    generate_lead_id,
    merge_contractor_profiles,
)


# ---------------------------------------------------------------------------
# generate_lead_id
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestGenerateLeadId:
    def test_same_inputs_produce_same_id(self):
        record = {"type": "permit", "source_id": "chicago-abc", "permit_number": "BLD-001"}
        id1 = generate_lead_id(record)
        id2 = generate_lead_id(record)
        assert id1 == id2
        assert len(id1) == 24  # SHA256 truncated to 24 hex chars

    def test_different_inputs_produce_different_ids(self):
        r1 = {"type": "permit", "source_id": "chicago-abc", "permit_number": "BLD-001"}
        r2 = {"type": "permit", "source_id": "chicago-abc", "permit_number": "BLD-002"}
        assert generate_lead_id(r1) != generate_lead_id(r2)

    def test_bid_type_uses_source_and_bid_id(self):
        record = {"type": "bid", "source": "sam.gov", "bid_id": "SAM-123"}
        lead_id = generate_lead_id(record)
        assert len(lead_id) == 24

    def test_missing_fields_still_produces_id(self):
        """Even with missing fields the function should not crash."""
        record = {"type": "permit"}
        lead_id = generate_lead_id(record)
        assert isinstance(lead_id, str)
        assert len(lead_id) == 24

    def test_deterministic_across_calls(self):
        """Multiple calls with identical data must return the same hash."""
        r1 = {"type": "bid", "source": "sam.gov", "bid_id": "SAM-XYZ"}
        ids = {generate_lead_id(r1) for _ in range(10)}
        assert len(ids) == 1


# ---------------------------------------------------------------------------
# generate_contractor_id
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestGenerateContractorId:
    def test_deterministic(self):
        assert generate_contractor_id("Acme Co", "TX") == generate_contractor_id("Acme Co", "TX")

    def test_case_insensitive(self):
        """Name is lowered, state is uppercased — so case should not matter."""
        assert generate_contractor_id("ACME CO", "tx") == generate_contractor_id("acme co", "TX")

    def test_whitespace_stripped(self):
        assert generate_contractor_id("  Acme Co  ", " TX ") == generate_contractor_id(
            "Acme Co", "TX"
        )


# ---------------------------------------------------------------------------
# find_duplicate_contractor
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestFindDuplicateContractor:
    @pytest.fixture()
    def existing_contractors(self) -> list[dict]:
        return [
            {
                "id": "ctr-001",
                "name": "Acme Electric Inc",
                "addr": "Houston, TX 77001",
                "licenses": [{"num": "EC-12345", "src": "TX-TDLR"}],
            },
            {
                "id": "ctr-002",
                "name": "Pacific Plumbing LLC",
                "addr": "Los Angeles, CA 90036",
                "licenses": [{"num": "CSLB-1045678", "src": "CA-CSLB"}],
            },
            {
                "id": "ctr-003",
                "name": "Top Tier Roofing",
                "addr": "Chicago, IL 60707",
                "licenses": [],
            },
        ]

    def test_exact_license_match_100_percent(self, existing_contractors):
        match_id, confidence = find_duplicate_contractor(
            name="Acme Electric",
            city="Houston",
            zip_code="77001",
            license_number="EC-12345",
            existing_contractors=existing_contractors,
        )
        assert match_id == "ctr-001"
        assert confidence == 1.0

    def test_similar_name_same_city_90_percent(self, existing_contractors):
        """Jaro-Winkler similarity > 0.85 + same city -> 90% confidence."""
        match_id, confidence = find_duplicate_contractor(
            name="Acme Electric Inc",  # very similar to "Acme Electric Inc"
            city="Houston",
            zip_code="",
            license_number="",
            existing_contractors=existing_contractors,
        )
        assert match_id == "ctr-001"
        assert confidence == 0.90

    def test_similar_name_same_zip_85_percent(self, existing_contractors):
        """Jaro-Winkler similarity > 0.85 + same zip -> 85% confidence."""
        match_id, confidence = find_duplicate_contractor(
            name="Acme Electric Inc",
            city="",  # no city provided
            zip_code="77001",
            license_number="",
            existing_contractors=existing_contractors,
        )
        assert match_id == "ctr-001"
        assert confidence == 0.85

    def test_no_match_returns_none(self, existing_contractors):
        match_id, confidence = find_duplicate_contractor(
            name="Completely Different Company",
            city="New York",
            zip_code="10001",
            license_number="XX-99999",
            existing_contractors=existing_contractors,
        )
        assert match_id is None
        assert confidence == 0.0

    def test_empty_name_returns_none(self, existing_contractors):
        match_id, confidence = find_duplicate_contractor(
            name="",
            city="Houston",
            zip_code="77001",
            license_number="",
            existing_contractors=existing_contractors,
        )
        assert match_id is None
        assert confidence == 0.0

    def test_no_existing_contractors(self):
        match_id, confidence = find_duplicate_contractor(
            name="Acme Electric",
            city="Houston",
            zip_code="77001",
            license_number="EC-12345",
            existing_contractors=[],
        )
        assert match_id is None
        assert confidence == 0.0

    def test_license_match_takes_priority_over_name(self, existing_contractors):
        """Even if the name is completely different, a license match wins."""
        match_id, confidence = find_duplicate_contractor(
            name="Totally Different Name Corp",
            city="Somewhere Else",
            zip_code="99999",
            license_number="EC-12345",
            existing_contractors=existing_contractors,
        )
        assert match_id == "ctr-001"
        assert confidence == 1.0


# ---------------------------------------------------------------------------
# merge_contractor_profiles
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestMergeContractorProfiles:
    def test_non_empty_new_data_preferred(self):
        existing = {"name": "Acme", "phone": "", "email": "", "trades": ["ELECTRICAL"]}
        new_data = {"name": "Acme Electric Inc", "phone": "+17135551234", "trades": ["HVAC"]}
        merged = merge_contractor_profiles(existing, new_data)
        assert merged["name"] == "Acme Electric Inc"  # longer new name wins
        assert merged["phone"] == "+17135551234"
        assert set(merged["trades"]) == {"ELECTRICAL", "HVAC"}

    def test_licenses_merged_without_duplicates(self):
        existing = {"licenses": [{"num": "EC-001", "src": "TX"}]}
        new_data = {
            "licenses": [
                {"num": "EC-001", "src": "TX"},  # duplicate
                {"num": "PL-002", "src": "CA"},  # new
            ]
        }
        merged = merge_contractor_profiles(existing, new_data)
        nums = [lic["num"] for lic in merged["licenses"]]
        assert "EC-001" in nums
        assert "PL-002" in nums
        assert len(merged["licenses"]) == 2

    def test_permit_count_summed(self):
        existing = {"permit_count": 5}
        new_data = {"permit_count": 3}
        merged = merge_contractor_profiles(existing, new_data)
        assert merged["permit_count"] == 8
