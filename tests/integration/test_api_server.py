"""Integration tests for the FastAPI API server — all endpoints via TestClient.

Uses dependency overrides to inject a Firestore emulator client and a fresh cache,
so these tests do NOT require a running server — only the Firestore emulator.
"""
from __future__ import annotations

import importlib
import os
import sys
import types
from pathlib import Path
from typing import Any, Generator

import pytest
from fastapi.testclient import TestClient

_PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Ensure emulator env-var is set before importing the app
os.environ.setdefault("FIRESTORE_EMULATOR_HOST", "localhost:8681")

# ---------------------------------------------------------------------------
# The api-server directory uses a hyphen which is not valid in Python import
# paths. We register it as a package under an underscore alias so that the
# relative imports inside main.py (``from .routers import ...``) resolve.
# ---------------------------------------------------------------------------
_api_dir = Path(__file__).resolve().parents[2] / "services" / "api-server"
_services_dir = str(Path(__file__).resolve().parents[2] / "services")
if _services_dir not in sys.path:
    sys.path.insert(0, _services_dir)


def _make_client(firestore_emulator: Any) -> Generator[TestClient, None, None]:
    """Build a FastAPI TestClient with dependency overrides for Firestore and cache."""
    # Import inside function to avoid import-time side-effects when emulator is down.
    # We import from the hyphenated package by adding its path and using importlib
    # for the main module (which has relative imports).
    _api_str = str(_api_dir)
    if _api_str not in sys.path:
        sys.path.insert(0, _api_str)

    from cache import TTLCache  # noqa: E402

    # For main.py we need special handling because it uses relative imports
    # (from .routers import ...). We register a synthetic package first.
    pkg_name = "api_server_pkg"
    if pkg_name not in sys.modules:
        pkg = types.ModuleType(pkg_name)
        pkg.__path__ = [_api_str]  # type: ignore[attr-defined]
        pkg.__package__ = pkg_name
        sys.modules[pkg_name] = pkg

    # Now import submodules under that package
    importlib.import_module(f"{pkg_name}.cache")  # ensure cache module is loaded
    deps_mod = importlib.import_module(f"{pkg_name}.dependencies")
    main_mod = importlib.import_module(f"{pkg_name}.main")

    app = main_mod.app
    get_firestore = deps_mod.get_firestore
    get_cache = deps_mod.get_cache

    fresh_cache = TTLCache(ttl_seconds=60)

    app.dependency_overrides[get_firestore] = lambda: firestore_emulator
    app.dependency_overrides[get_cache] = lambda: fresh_cache

    client = TestClient(app)
    yield client

    # Cleanup overrides
    app.dependency_overrides.clear()


@pytest.fixture()
def api_client(firestore_emulator):
    """Provide a TestClient with injected Firestore emulator."""
    yield from _make_client(firestore_emulator)


# ---------------------------------------------------------------------------
# GET /api/health
# ---------------------------------------------------------------------------
@pytest.mark.integration
class TestHealthEndpoint:
    def test_health_returns_ok(self, api_client: TestClient):
        response = api_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "api-server"


# ---------------------------------------------------------------------------
# GET /api/leads
# ---------------------------------------------------------------------------
@pytest.mark.integration
class TestLeadsEndpoint:
    def test_list_leads_empty(self, api_client: TestClient):
        """When no leads exist, the endpoint returns an empty list."""
        response = api_client.get("/api/leads")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_leads_with_data(self, api_client: TestClient, firestore_emulator):
        """Seed leads and verify they are returned."""
        leads = [
            {"id": "api-001", "type": "permit", "trade": "ELECTRICAL", "score": 80, "value": 100_000, "addr": "Chicago, IL"},
            {"id": "api-002", "type": "bid", "trade": "PLUMBING", "score": 60, "value": 50_000, "addr": "Houston, TX"},
        ]
        for lead in leads:
            firestore_emulator.leads().document(lead["id"]).set(lead)

        response = api_client.get("/api/leads")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_leads_filter_by_trade(self, api_client: TestClient, firestore_emulator):
        leads = [
            {"id": "f-001", "type": "permit", "trade": "ELECTRICAL", "score": 80},
            {"id": "f-002", "type": "permit", "trade": "PLUMBING", "score": 70},
            {"id": "f-003", "type": "bid", "trade": "ELECTRICAL", "score": 60},
        ]
        for lead in leads:
            firestore_emulator.leads().document(lead["id"]).set(lead)

        response = api_client.get("/api/leads", params={"trade": "ELECTRICAL"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(d["trade"] == "ELECTRICAL" for d in data)

    def test_list_leads_sorted_by_score(self, api_client: TestClient, firestore_emulator):
        leads = [
            {"id": "s-001", "type": "permit", "trade": "ELECTRICAL", "score": 50},
            {"id": "s-002", "type": "permit", "trade": "ELECTRICAL", "score": 90},
            {"id": "s-003", "type": "permit", "trade": "ELECTRICAL", "score": 70},
        ]
        for lead in leads:
            firestore_emulator.leads().document(lead["id"]).set(lead)

        response = api_client.get("/api/leads", params={"sort_by": "score"})
        data = response.json()
        scores = [d["score"] for d in data]
        assert scores == sorted(scores, reverse=True)


# ---------------------------------------------------------------------------
# GET /api/leads/{id}
# ---------------------------------------------------------------------------
@pytest.mark.integration
class TestGetLeadEndpoint:
    def test_get_existing_lead(self, api_client: TestClient, firestore_emulator, sample_lead_dict):
        lead_id = sample_lead_dict["id"]
        firestore_emulator.leads().document(lead_id).set(sample_lead_dict)

        response = api_client.get(f"/api/leads/{lead_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == lead_id
        assert data["trade"] == "ELECTRICAL"

    def test_get_nonexistent_lead_returns_error(self, api_client: TestClient):
        response = api_client.get("/api/leads/nonexistent-id-12345")
        assert response.status_code == 200  # endpoint returns 200 with error dict
        data = response.json()
        assert "error" in data
        assert data["error"] == "Lead not found"


# ---------------------------------------------------------------------------
# GET /api/dashboard
# ---------------------------------------------------------------------------
@pytest.mark.integration
class TestDashboardEndpoint:
    def test_dashboard_returns_stats_dict(self, api_client: TestClient):
        response = api_client.get("/api/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "total_leads" in data
        assert "total_contractors" in data
        assert "new_today" in data
        assert "new_this_week" in data
        assert "by_trade" in data
        assert "by_type" in data
        assert "by_value_range" in data
        assert "hot_markets" in data

    def test_dashboard_with_data(self, api_client: TestClient, firestore_emulator):
        from datetime import datetime

        leads = [
            {"id": "d-001", "type": "permit", "trade": "ELECTRICAL", "value": 300_000,
             "posted": datetime.utcnow().isoformat(), "addr": "Chicago, IL 60611"},
            {"id": "d-002", "type": "bid", "trade": "PLUMBING", "value": 80_000,
             "posted": datetime.utcnow().isoformat(), "addr": "Houston, TX 77001"},
        ]
        for lead in leads:
            firestore_emulator.leads().document(lead["id"]).set(lead)

        response = api_client.get("/api/dashboard")
        data = response.json()
        assert data["total_leads"] == 2
        assert data["by_type"]["permit"] == 1
        assert data["by_type"]["bid"] == 1


# ---------------------------------------------------------------------------
# POST /api/alerts
# ---------------------------------------------------------------------------
@pytest.mark.integration
class TestAlertsEndpoint:
    def test_create_alert(self, api_client: TestClient):
        payload = {
            "email": "test@example.com",
            "trade": "ELECTRICAL",
            "state": "TX",
        }
        response = api_client.post("/api/alerts", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["status"] == "created"

    def test_create_alert_minimal(self, api_client: TestClient):
        """Only email is strictly required."""
        payload = {"email": "minimal@example.com"}
        response = api_client.post("/api/alerts", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "created"

    def test_list_alerts(self, api_client: TestClient):
        # Create two alerts
        api_client.post("/api/alerts", json={"email": "a@test.com", "trade": "ELECTRICAL"})
        api_client.post("/api/alerts", json={"email": "b@test.com", "trade": "PLUMBING"})

        response = api_client.get("/api/alerts")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    def test_list_alerts_filter_by_email(self, api_client: TestClient):
        api_client.post("/api/alerts", json={"email": "filter@test.com", "trade": "ROOFING"})
        api_client.post("/api/alerts", json={"email": "other@test.com", "trade": "HVAC"})

        response = api_client.get("/api/alerts", params={"email": "filter@test.com"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all(d["email"] == "filter@test.com" for d in data)

    def test_delete_alert(self, api_client: TestClient):
        # Create an alert
        create_resp = api_client.post(
            "/api/alerts", json={"email": "delete@test.com", "trade": "ELECTRICAL"}
        )
        alert_id = create_resp.json()["id"]

        # Delete it
        del_resp = api_client.delete(f"/api/alerts/{alert_id}")
        assert del_resp.status_code == 200
        assert del_resp.json()["status"] == "deleted"
