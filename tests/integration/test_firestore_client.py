"""Integration tests for shared.clients.firestore_client — requires Firestore emulator.

Run the emulator before executing these tests:
    gcloud emulators firestore start --host-port=localhost:8681

Or use docker-compose.test.yml which starts it automatically.
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pytest

_PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


@pytest.mark.integration
class TestFirestoreLeads:
    """Lead collection CRUD against the Firestore emulator."""

    def test_write_and_read_lead(self, firestore_emulator, sample_lead_dict):
        """Write a lead document and read it back."""
        db = firestore_emulator
        lead_id = sample_lead_dict["id"]

        # Write
        db.leads().document(lead_id).set(sample_lead_dict)

        # Read
        doc = db.leads().document(lead_id).get()
        assert doc.exists
        data = doc.to_dict()
        assert data["id"] == lead_id
        assert data["type"] == "permit"
        assert data["trade"] == "ELECTRICAL"
        assert data["value"] == 250_000.0
        assert data["owner"]["n"] == "John Smith"

    def test_compound_query_filter_by_trade(self, firestore_emulator):
        """Write multiple leads and query by trade."""
        db = firestore_emulator

        leads = [
            {"id": "q-001", "trade": "ELECTRICAL", "type": "permit", "score": 80},
            {"id": "q-002", "trade": "PLUMBING", "type": "permit", "score": 70},
            {"id": "q-003", "trade": "ELECTRICAL", "type": "bid", "score": 60},
            {"id": "q-004", "trade": "ROOFING", "type": "permit", "score": 50},
        ]
        for lead in leads:
            db.leads().document(lead["id"]).set(lead)

        # Query: trade == ELECTRICAL
        results = list(db.leads().where("trade", "==", "ELECTRICAL").stream())
        assert len(results) == 2
        trades = {doc.to_dict()["trade"] for doc in results}
        assert trades == {"ELECTRICAL"}

    def test_query_by_type(self, firestore_emulator):
        """Query leads filtered by type (permit vs bid)."""
        db = firestore_emulator
        leads = [
            {"id": "t-001", "type": "permit", "trade": "ELECTRICAL"},
            {"id": "t-002", "type": "bid", "trade": "ELECTRICAL"},
            {"id": "t-003", "type": "permit", "trade": "PLUMBING"},
        ]
        for lead in leads:
            db.leads().document(lead["id"]).set(lead)

        results = list(db.leads().where("type", "==", "bid").stream())
        assert len(results) == 1
        assert results[0].to_dict()["id"] == "t-002"

    def test_update_lead(self, firestore_emulator, sample_lead_dict):
        """Update a field on an existing lead."""
        db = firestore_emulator
        lead_id = sample_lead_dict["id"]
        db.leads().document(lead_id).set(sample_lead_dict)

        # Update score
        db.leads().document(lead_id).update({"score": 99})

        doc = db.leads().document(lead_id).get()
        assert doc.to_dict()["score"] == 99
        assert doc.to_dict()["trade"] == "ELECTRICAL"  # other fields unchanged

    def test_delete_lead(self, firestore_emulator, sample_lead_dict):
        """Delete a lead and confirm it no longer exists."""
        db = firestore_emulator
        lead_id = sample_lead_dict["id"]
        db.leads().document(lead_id).set(sample_lead_dict)
        db.leads().document(lead_id).delete()

        doc = db.leads().document(lead_id).get()
        assert not doc.exists

    def test_read_nonexistent_lead(self, firestore_emulator):
        """Reading a document that does not exist should return exists=False."""
        doc = firestore_emulator.leads().document("does-not-exist-abc").get()
        assert not doc.exists


@pytest.mark.integration
class TestFirestoreContractors:
    """Contractor collection tests."""

    def test_write_and_read_contractor(self, firestore_emulator, sample_contractor_dict):
        db = firestore_emulator
        cid = sample_contractor_dict["id"]
        db.contractors().document(cid).set(sample_contractor_dict)

        doc = db.contractors().document(cid).get()
        assert doc.exists
        data = doc.to_dict()
        assert data["name"] == "Acme Electric Inc"
        assert "ELECTRICAL" in data["trades"]
        assert data["licenses"][0]["num"] == "EC-12345"

    def test_query_contractors_by_trade(self, firestore_emulator):
        db = firestore_emulator
        contractors = [
            {"id": "c-001", "name": "Elec Co", "trades": ["ELECTRICAL"]},
            {"id": "c-002", "name": "Plumb Co", "trades": ["PLUMBING"]},
            {"id": "c-003", "name": "Multi Co", "trades": ["ELECTRICAL", "HVAC"]},
        ]
        for c in contractors:
            db.contractors().document(c["id"]).set(c)

        results = list(
            db.contractors()
            .where("trades", "array_contains", "ELECTRICAL")
            .stream()
        )
        assert len(results) == 2
        names = {doc.to_dict()["name"] for doc in results}
        assert "Elec Co" in names
        assert "Multi Co" in names


@pytest.mark.integration
class TestFirestoreIngestionState:
    """Ingestion state collection tests."""

    def test_write_and_read_ingestion_state(self, firestore_emulator):
        db = firestore_emulator
        source_id = "chicago-ydr8-5enu"
        state_data = {
            "source_id": source_id,
            "last_run": datetime.utcnow().isoformat(),
            "last_record_date": "2026-02-25",
            "records_ingested": 150,
            "errors": 2,
        }
        db.update_ingestion_state(source_id, state_data)

        result = db.get_last_run(source_id)
        assert result is not None
        assert result["source_id"] == source_id
        assert result["records_ingested"] == 150
        assert result["errors"] == 2

    def test_update_ingestion_state_merge(self, firestore_emulator):
        """update_ingestion_state uses merge=True, so partial updates work."""
        db = firestore_emulator
        source_id = "test-source-merge"

        db.update_ingestion_state(source_id, {"source_id": source_id, "records_ingested": 10})
        db.update_ingestion_state(source_id, {"errors": 1})

        result = db.get_last_run(source_id)
        assert result is not None
        assert result["records_ingested"] == 10  # preserved
        assert result["errors"] == 1  # merged

    def test_get_last_run_nonexistent(self, firestore_emulator):
        result = firestore_emulator.get_last_run("nonexistent-source")
        assert result is None


@pytest.mark.integration
class TestFirestoreAlerts:
    """Alerts collection tests."""

    def test_write_and_read_alert(self, firestore_emulator):
        db = firestore_emulator
        alert_data = {
            "id": "alert-001",
            "email": "user@example.com",
            "trade": "ELECTRICAL",
            "state": "TX",
            "active": True,
        }
        db.alerts().document("alert-001").set(alert_data)

        doc = db.alerts().document("alert-001").get()
        assert doc.exists
        data = doc.to_dict()
        assert data["email"] == "user@example.com"
        assert data["trade"] == "ELECTRICAL"
        assert data["active"] is True

    def test_query_alerts_by_email(self, firestore_emulator):
        db = firestore_emulator
        alerts = [
            {"id": "a-001", "email": "alice@test.com", "trade": "ELECTRICAL"},
            {"id": "a-002", "email": "bob@test.com", "trade": "PLUMBING"},
            {"id": "a-003", "email": "alice@test.com", "trade": "ROOFING"},
        ]
        for a in alerts:
            db.alerts().document(a["id"]).set(a)

        results = list(db.alerts().where("email", "==", "alice@test.com").stream())
        assert len(results) == 2
