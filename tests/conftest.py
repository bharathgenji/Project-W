"""Root conftest.py — shared fixtures for the entire test suite.

Provides:
- Session-scoped Firestore emulator connection
- Auto-cleanup between tests (deletes all docs in test collections)
- Common test helpers
"""
from __future__ import annotations

import os
from typing import Any, Generator

import pytest

# ---------------------------------------------------------------------------
# Firestore emulator environment — set BEFORE any google-cloud imports
# ---------------------------------------------------------------------------
EMULATOR_HOST = "localhost:8681"
os.environ["FIRESTORE_EMULATOR_HOST"] = EMULATOR_HOST


@pytest.fixture(scope="session")
def firestore_emulator():
    """Session-scoped fixture that ensures the emulator env-var is set and
    returns a ``FirestoreClient`` connected to the local emulator.

    The emulator must already be running (``gcloud emulators firestore start
    --host-port=localhost:8681``).  In CI this is typically started via
    ``docker-compose.test.yml``.
    """
    os.environ["FIRESTORE_EMULATOR_HOST"] = EMULATOR_HOST

    from shared.clients.firestore_client import FirestoreClient

    # Reset singleton so it picks up the emulator host
    FirestoreClient.reset()
    client = FirestoreClient(project_id="leadgen-mvp-test")
    yield client
    FirestoreClient.reset()


# Collections that are wiped between every test
_COLLECTIONS_TO_CLEAN = ["leads", "contractors", "ingestion_state", "alerts"]


def _delete_collection(db_client: Any, collection_name: str) -> None:
    """Delete all documents in a Firestore collection (emulator only)."""
    col_ref = db_client.db.collection(collection_name)
    docs = col_ref.limit(500).stream()
    for doc in docs:
        doc.reference.delete()


@pytest.fixture(autouse=True)
def _cleanup_firestore(request):
    """Auto-use fixture that wipes test collections after every integration/e2e test.

    Only activates for tests marked ``integration`` or ``e2e``.  Unit tests
    skip this entirely so they never attempt to connect to the emulator.
    """
    markers = {m.name for m in request.node.iter_markers()}
    if not (markers & {"integration", "e2e"}):
        yield
        return

    # Only request the emulator fixture for integration/e2e tests
    emulator = request.getfixturevalue("firestore_emulator")
    yield
    for col in _COLLECTIONS_TO_CLEAN:
        try:
            _delete_collection(emulator, col)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Convenience fixtures
# ---------------------------------------------------------------------------
@pytest.fixture()
def sample_lead_dict() -> dict[str, Any]:
    """A minimal valid lead dict for quick tests."""
    return {
        "id": "test-lead-001",
        "type": "permit",
        "trade": "ELECTRICAL",
        "title": "Install 200-amp panel",
        "value": 250_000.0,
        "addr": "123 Main St, Houston, TX 77001",
        "owner": {"n": "John Smith", "p": "+17135551234", "e": "john@example.com"},
        "gc": {"n": "Acme Electric", "p": "+17135559999", "lic": "EC-12345"},
        "status": "active",
        "posted": "2026-02-28T12:00:00",
        "score": 85,
        "src": "chicago-ydr8-5enu",
        "keywords": ["electrical", "panel", "install"],
    }


@pytest.fixture()
def sample_contractor_dict() -> dict[str, Any]:
    """A minimal valid contractor dict for quick tests."""
    return {
        "id": "test-contractor-001",
        "name": "Acme Electric Inc",
        "phone": "+17135559999",
        "email": "info@acmeelectric.com",
        "addr": "Houston, TX 77001",
        "trades": ["ELECTRICAL"],
        "licenses": [{"num": "EC-12345", "src": "TX-TDLR", "status": "ACTIVE"}],
        "permit_count": 12,
    }
