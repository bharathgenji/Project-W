"""respx routes for Socrata Open Data API (SODA).

Usage in tests::

    import respx
    from tests.mocks.mock_socrata import mock_socrata_chicago

    @respx.mock
    def test_something(respx_mock):
        mock_socrata_chicago(respx_mock)
        # ... call code that hits data.cityofchicago.org ...
"""
from __future__ import annotations

import json
from pathlib import Path

import httpx
import respx

_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"

# Chicago building permits dataset ID
CHICAGO_DOMAIN = "data.cityofchicago.org"
CHICAGO_DATASET = "ydr8-5enu"
CHICAGO_URL = f"https://{CHICAGO_DOMAIN}/resource/{CHICAGO_DATASET}.json"


def _load_sample_permits() -> list[dict]:
    with open(_FIXTURES / "sample_permits.json", encoding="utf-8") as f:
        return json.load(f)


def mock_socrata_chicago(mock: respx.MockRouter) -> respx.Route:
    """Register a GET route for the Chicago Socrata permits endpoint.

    Returns the route object so tests can inspect call counts.
    """
    sample_data = _load_sample_permits()
    route = mock.get(CHICAGO_URL).mock(
        return_value=httpx.Response(200, json=sample_data)
    )
    return route


def mock_socrata_chicago_empty(mock: respx.MockRouter) -> respx.Route:
    """Register a GET route that returns an empty result set."""
    route = mock.get(CHICAGO_URL).mock(
        return_value=httpx.Response(200, json=[])
    )
    return route


def mock_socrata_chicago_error(mock: respx.MockRouter, status: int = 500) -> respx.Route:
    """Register a GET route that returns an HTTP error."""
    route = mock.get(CHICAGO_URL).mock(
        return_value=httpx.Response(status, json={"error": "Internal Server Error"})
    )
    return route


def mock_socrata_discover(mock: respx.MockRouter) -> respx.Route:
    """Register a GET route for the dataset discovery endpoint."""
    discover_url = f"https://{CHICAGO_DOMAIN}/api/views.json"
    sample_discovery = [
        {
            "id": CHICAGO_DATASET,
            "name": "Building Permits",
            "description": "Building permits issued by the City of Chicago",
            "category": "Buildings",
            "rowsUpdatedAt": 1709000000,
        },
    ]
    route = mock.get(discover_url).mock(
        return_value=httpx.Response(200, json=sample_discovery)
    )
    return route
