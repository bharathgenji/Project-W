"""Unit tests for services/etl-pipeline/trade_classifier — pure function tests."""
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

from trade_classifier import classify_trade  # noqa: E402


@pytest.mark.unit
class TestClassifyTrade:
    """Tests for the keyword-based trade classifier."""

    # ---- Keyword-based classification ----

    def test_electrical_high_confidence(self):
        trade, confidence = classify_trade(
            "Install new 200-amp electrical panel and rewire circuit breakers"
        )
        assert trade == "ELECTRICAL"
        assert confidence > 0.5

    def test_roofing(self):
        trade, confidence = classify_trade("Replace roof shingles and install new flashing")
        assert trade == "ROOFING"
        assert confidence > 0.0

    def test_plumbing(self):
        trade, confidence = classify_trade(
            "Replace all plumbing pipes and install new water heater with backflow preventer"
        )
        assert trade == "PLUMBING"
        assert confidence > 0.5

    def test_hvac(self):
        trade, confidence = classify_trade(
            "Install new furnace, ductwork, and air conditioning system"
        )
        assert trade == "HVAC"
        assert confidence > 0.0

    def test_concrete(self):
        trade, confidence = classify_trade("Pour concrete foundation and slab for new building")
        assert trade == "CONCRETE"
        assert confidence > 0.0

    def test_demolition(self):
        trade, confidence = classify_trade("Complete demolition and removal of existing structure")
        assert trade == "DEMOLITION"
        assert confidence > 0.0

    def test_general_renovation(self):
        trade, confidence = classify_trade("General renovation of office space and build-out")
        assert trade == "GENERAL"
        assert confidence > 0.0

    def test_painting(self):
        trade, confidence = classify_trade("Interior painting and wall coating of 5 floors")
        assert trade == "PAINTING"
        assert confidence > 0.0

    def test_flooring(self):
        trade, confidence = classify_trade("Install hardwood flooring and ceramic tile in lobby")
        assert trade == "FLOORING"
        assert confidence > 0.0

    # ---- Edge cases ----

    def test_empty_string_returns_unknown(self):
        trade, confidence = classify_trade("")
        assert trade == "UNKNOWN"
        assert confidence == 0.0

    def test_none_description_returns_unknown(self):
        """None input (unusual, but should not crash)."""
        trade, confidence = classify_trade(None)  # type: ignore[arg-type]
        assert trade == "UNKNOWN"
        assert confidence == 0.0

    def test_no_keywords_matched(self):
        trade, confidence = classify_trade("Standard office lease agreement signed")
        assert trade == "UNKNOWN"
        assert confidence == 0.0

    # ---- NAICS code mapping ----

    def test_naics_electrical(self):
        trade, confidence = classify_trade("any text", naics_code="238210")
        assert trade == "ELECTRICAL"
        assert confidence == 0.95

    def test_naics_roofing(self):
        trade, confidence = classify_trade("any text", naics_code="238160")
        assert trade == "ROOFING"
        assert confidence == 0.95

    def test_naics_hvac(self):
        trade, confidence = classify_trade("any text", naics_code="238220")
        assert trade == "HVAC"
        assert confidence == 0.95

    def test_naics_overrides_keyword(self):
        """When a valid NAICS code is provided it should take priority over keywords."""
        trade, confidence = classify_trade(
            "Install new electrical panel", naics_code="238160"
        )
        # Despite electrical keywords, NAICS 238160 = ROOFING
        assert trade == "ROOFING"
        assert confidence == 0.95

    def test_unknown_naics_falls_through_to_keywords(self):
        """An unrecognised NAICS code should fall through to keyword matching."""
        trade, confidence = classify_trade(
            "Install new electrical panel", naics_code="999999"
        )
        assert trade == "ELECTRICAL"
        assert confidence > 0.0

    # ---- Confidence range ----

    def test_confidence_between_0_and_1(self):
        """Confidence should always be in [0.0, 1.0]."""
        descriptions = [
            "electrical wiring circuit panel conduit voltage transformer switchgear outlet lighting generator",
            "roof",
            "",
            "some unrelated text about cats and dogs",
        ]
        for desc in descriptions:
            _, confidence = classify_trade(desc)
            assert 0.0 <= confidence <= 1.0, f"Out of range for: {desc!r}"
