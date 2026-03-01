"""respx routes for SAM.gov Opportunities API.

Usage in tests::

    import respx
    from tests.mocks.mock_sam import mock_sam_opportunities

    @respx.mock
    def test_something(respx_mock):
        mock_sam_opportunities(respx_mock)
        # ... call code that hits api.sam.gov ...
"""
from __future__ import annotations

import json
from pathlib import Path

import httpx
import respx

_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"

SAM_SEARCH_URL = "https://api.sam.gov/prod/opportunities/v2/search"


def _load_sample_bids() -> list[dict]:
    with open(_FIXTURES / "sample_bids.json", encoding="utf-8") as f:
        return json.load(f)


def _wrap_sam_response(opportunities: list[dict]) -> dict:
    """Wrap opportunities in the SAM.gov response envelope."""
    return {
        "totalRecords": len(opportunities),
        "limit": 100,
        "offset": 0,
        "opportunitiesData": opportunities,
    }


def mock_sam_opportunities(mock: respx.MockRouter) -> respx.Route:
    """Register a GET route for SAM.gov opportunity search returning sample data."""
    sample_data = _load_sample_bids()
    route = mock.get(SAM_SEARCH_URL).mock(
        return_value=httpx.Response(200, json=_wrap_sam_response(sample_data))
    )
    return route


def mock_sam_empty(mock: respx.MockRouter) -> respx.Route:
    """Register a GET route that returns zero opportunities."""
    route = mock.get(SAM_SEARCH_URL).mock(
        return_value=httpx.Response(200, json=_wrap_sam_response([]))
    )
    return route


def mock_sam_error(mock: respx.MockRouter, status: int = 403) -> respx.Route:
    """Register a GET route that returns an HTTP error (e.g. bad API key)."""
    route = mock.get(SAM_SEARCH_URL).mock(
        return_value=httpx.Response(status, json={"error": {"code": "OPPS_INVALID_API_KEY"}})
    )
    return route


def mock_sam_single_opportunity(mock: respx.MockRouter) -> respx.Route:
    """Register a GET route returning a single opportunity for targeted tests."""
    single = {
        "noticeId": "SAM-UNIT-TEST-001",
        "title": "Unit Test Electrical Work",
        "description": "Test opportunity for unit test coverage",
        "fullParentPathName": "TEST AGENCY",
        "postedDate": "2026-02-28T00:00:00",
        "responseDeadLine": "2026-03-28T17:00:00",
        "type": "o",
        "naicsCode": "238210",
        "typeOfSetAside": "",
        "pointOfContact": [
            {
                "fullName": "Test Contact",
                "email": "test@agency.gov",
                "phone": "202-555-0100",
                "type": "primary",
            }
        ],
        "placeOfPerformance": {
            "city": {"name": "Washington"},
            "state": {"code": "DC", "name": "District of Columbia"},
            "zip": "20001",
        },
    }
    route = mock.get(SAM_SEARCH_URL).mock(
        return_value=httpx.Response(200, json=_wrap_sam_response([single]))
    )
    return route
