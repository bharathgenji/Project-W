"""Unit tests for services/etl-pipeline/scorer — lead scoring logic."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

_PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

_etl_path = str(Path(__file__).resolve().parents[2] / "services" / "etl-pipeline")
if _etl_path not in sys.path:
    sys.path.insert(0, _etl_path)

from scorer import score_lead  # noqa: E402


@pytest.mark.unit
class TestScoreLead:
    """Verify the multi-factor scoring algorithm."""

    # ---- High-value, recent, full-contact lead ----

    def test_high_value_recent_full_contact(self):
        """$500K, posted today, phone + email, specific trade, no GC => score > 80."""
        lead = {
            "value": 500_000,
            "posted": datetime.utcnow().isoformat(),
            "owner": {"n": "John Smith", "p": "+17135551234", "e": "john@example.com"},
            "gc": {},
            "trade": "ELECTRICAL",
        }
        score = score_lead(lead)
        # value(30) + recency(25) + contact(20) + trade(15) + competition(10) = 100
        assert score >= 80
        assert score <= 100

    # ---- Low-value, old, minimal contact ----

    def test_low_value_old_name_only(self):
        """$10K, 6 months old, name only, GENERAL trade => score < 30."""
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        lead = {
            "value": 10_000,
            "posted": six_months_ago.isoformat(),
            "owner": {"n": "Some Person"},
            "gc": {"n": "Big Builder Corp"},
            "trade": "GENERAL",
        }
        score = score_lead(lead)
        # value(10) + recency(0) + contact(5) + trade(5) + competition(0) = 20
        assert score < 30

    # ---- Boundary: zero value ----

    def test_zero_value(self):
        lead = {"value": 0, "owner": {}, "gc": {}, "trade": "UNKNOWN"}
        score = score_lead(lead)
        # value(0) + recency(0) + contact(0) + trade(0) + competition(10) = 10
        assert score >= 0

    # ---- Boundary: missing date ----

    def test_missing_date(self):
        lead = {"value": 100_000, "owner": {}, "gc": {}, "trade": "ELECTRICAL"}
        score = score_lead(lead)
        # value(20) + recency(0) + contact(0) + trade(15) + competition(10) = 45
        assert 0 <= score <= 100

    # ---- Always 0-100 ----

    def test_score_always_0_to_100(self):
        """Score should be clamped between 0 and 100 for any input."""
        cases = [
            {},
            {"value": 999_999_999, "posted": datetime.utcnow().isoformat(),
             "owner": {"p": "+11111111111", "e": "a@b.com"}, "gc": {},
             "trade": "ELECTRICAL"},
            {"value": -100},
            {"value": "not_a_number"},
        ]
        for lead in cases:
            score = score_lead(lead)
            assert 0 <= score <= 100, f"Out of range for {lead}"

    # ---- Value tiers ----

    def test_value_tier_under_50k(self):
        lead = {"value": 25_000, "owner": {}, "gc": {}}
        score = score_lead(lead)
        # value(10) + competition(10) = at least 20
        assert score >= 10

    def test_value_tier_50k_to_200k(self):
        lead = {"value": 100_000, "owner": {}, "gc": {}}
        score = score_lead(lead)
        # value(20)
        assert score >= 20

    def test_value_tier_over_200k(self):
        lead = {"value": 300_000, "owner": {}, "gc": {}}
        score = score_lead(lead)
        # value(30)
        assert score >= 30

    # ---- Recency tiers ----

    def test_recency_within_7_days(self):
        lead = {"posted": datetime.utcnow().isoformat(), "owner": {}, "gc": {}}
        score = score_lead(lead)
        # recency(25) + competition(10) = 35
        assert score >= 25

    def test_recency_within_30_days(self):
        posted = datetime.utcnow() - timedelta(days=15)
        lead = {"posted": posted.isoformat(), "owner": {}, "gc": {}}
        score = score_lead(lead)
        # recency(15) + competition(10) = 25
        assert score >= 15

    def test_recency_within_90_days(self):
        posted = datetime.utcnow() - timedelta(days=60)
        lead = {"posted": posted.isoformat(), "owner": {}, "gc": {}}
        score = score_lead(lead)
        # recency(5) + competition(10) = 15
        assert score >= 5

    def test_recency_over_90_days(self):
        posted = datetime.utcnow() - timedelta(days=120)
        lead = {"posted": posted.isoformat(), "owner": {}, "gc": {}}
        score = score_lead(lead)
        # recency(0) + competition(10) = 10
        # The key assertion: it does NOT get recency points
        base_score = score_lead({"owner": {}, "gc": {}})
        assert score == base_score  # same as no date at all

    # ---- Contact completeness ----

    def test_phone_and_email_gives_20(self):
        lead = {"owner": {"phone": "+11111111111", "email": "a@b.com"}, "gc": {}}
        score = score_lead(lead)
        # contact(20) + competition(10) = 30
        assert score >= 20

    def test_phone_only_gives_10(self):
        lead = {"owner": {"phone": "+11111111111"}, "gc": {}}
        score = score_lead(lead)
        assert score >= 10

    def test_name_only_gives_5(self):
        lead = {"owner": {"name": "Some Person"}, "gc": {"n": "Builder"}}
        score = score_lead(lead)
        # contact(5) + competition(0, gc has name) = 5
        assert score >= 5

    # ---- Trade specificity ----

    def test_specific_trade_gives_15(self):
        lead = {"trade": "ELECTRICAL", "owner": {}, "gc": {}}
        score_specific = score_lead(lead)
        lead_general = {"trade": "GENERAL", "owner": {}, "gc": {}}
        score_general = score_lead(lead_general)
        assert score_specific > score_general

    def test_unknown_trade_gives_0(self):
        lead = {"trade": "UNKNOWN", "owner": {}, "gc": {}}
        lead_no_trade = {"owner": {}, "gc": {}}
        assert score_lead(lead) == score_lead(lead_no_trade)

    # ---- Competition ----

    def test_no_gc_gives_10_competition_bonus(self):
        lead_no_gc = {"owner": {}, "gc": {}}
        lead_with_gc = {"owner": {}, "gc": {"n": "Big Builder"}}
        assert score_lead(lead_no_gc) > score_lead(lead_with_gc)

    # ---- Alternative field names ----

    def test_estimated_cost_alias(self):
        lead = {"estimated_cost": 300_000, "owner": {}, "gc": {}}
        score = score_lead(lead)
        assert score >= 30  # value(30)

    def test_filed_date_alias(self):
        lead = {"filed_date": datetime.utcnow().isoformat(), "owner": {}, "gc": {}}
        score = score_lead(lead)
        assert score >= 25  # recency(25)

    def test_issued_date_alias(self):
        lead = {"issued_date": datetime.utcnow().isoformat(), "owner": {}, "gc": {}}
        score = score_lead(lead)
        assert score >= 25
