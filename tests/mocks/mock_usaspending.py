"""respx routes for USASpending API.

Usage in tests::

    import respx
    from tests.mocks.mock_usaspending import mock_usaspending_awards

    @respx.mock
    def test_something(respx_mock):
        mock_usaspending_awards(respx_mock)
        # ... call code that hits api.usaspending.gov ...
"""
from __future__ import annotations

import httpx
import respx

USASPENDING_URL = "https://api.usaspending.gov/api/v2/search/spending_by_award/"


def _sample_awards_response() -> dict:
    """Build a realistic USASpending search response."""
    return {
        "limit": 100,
        "page_metadata": {"page": 1, "count": 3, "hasNext": False},
        "results": [
            {
                "Award ID": "47QFCA22F0001",
                "Recipient Name": "MIDWEST CONSTRUCTION GROUP INC",
                "Award Amount": 1_250_000.0,
                "Awarding Agency": "GENERAL SERVICES ADMINISTRATION",
                "Description": "Renovation and modernization of federal office building HVAC system and electrical infrastructure",
                "Place of Performance State Code": "IL",
                "Place of Performance City Name": "CHICAGO",
                "Start Date": "2026-01-15",
            },
            {
                "Award ID": "W912DQ26C0042",
                "Recipient Name": "EAGLE ROOFING AND WATERPROOFING LLC",
                "Award Amount": 485_000.0,
                "Awarding Agency": "DEPARTMENT OF DEFENSE",
                "Description": "Roof replacement and waterproofing at Army Reserve Center",
                "Place of Performance State Code": "TX",
                "Place of Performance City Name": "SAN ANTONIO",
                "Start Date": "2026-02-01",
            },
            {
                "Award ID": "15B30526C0008",
                "Recipient Name": "PACIFIC PLUMBING AND MECHANICAL LLC",
                "Award Amount": 320_000.0,
                "Awarding Agency": "DEPARTMENT OF JUSTICE",
                "Description": "Plumbing system replacement at federal courthouse",
                "Place of Performance State Code": "CA",
                "Place of Performance City Name": "LOS ANGELES",
                "Start Date": "2026-02-10",
            },
        ],
    }


def mock_usaspending_awards(mock: respx.MockRouter) -> respx.Route:
    """Register a POST route for USASpending spending_by_award search."""
    route = mock.post(USASPENDING_URL).mock(
        return_value=httpx.Response(200, json=_sample_awards_response())
    )
    return route


def mock_usaspending_empty(mock: respx.MockRouter) -> respx.Route:
    """Register a POST route that returns zero results."""
    empty_response = {
        "limit": 100,
        "page_metadata": {"page": 1, "count": 0, "hasNext": False},
        "results": [],
    }
    route = mock.post(USASPENDING_URL).mock(
        return_value=httpx.Response(200, json=empty_response)
    )
    return route


def mock_usaspending_error(mock: respx.MockRouter, status: int = 500) -> respx.Route:
    """Register a POST route that returns an HTTP error."""
    route = mock.post(USASPENDING_URL).mock(
        return_value=httpx.Response(status, json={"detail": "Internal error"})
    )
    return route
