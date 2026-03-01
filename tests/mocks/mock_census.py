"""respx routes for Census Bureau Building Permits Survey (BPS) API.

Usage in tests::

    import respx
    from tests.mocks.mock_census import mock_census_bps

    @respx.mock
    def test_something(respx_mock):
        mock_census_bps(respx_mock)
        # ... call code that hits api.census.gov ...
"""
from __future__ import annotations

import httpx
import respx

CENSUS_BPS_URL = "https://api.census.gov/data/timeseries/eits/bps"


def _sample_bps_response() -> list:
    """Build a realistic Census BPS response (list of lists, first row = headers)."""
    return [
        [
            "PERMITS",
            "time",
            "metropolitan statistical area/micropolitan statistical area",
        ],
        ["1250", "2026-01", "16980"],  # Chicago-Naperville-Elgin MSA
        ["980", "2026-01", "26420"],   # Houston-The Woodlands-Sugar Land MSA
        ["1450", "2026-01", "19100"],  # Dallas-Fort Worth-Arlington MSA
        ["350", "2026-01", "33460"],   # Minneapolis-St. Paul MSA
        ["75", "2026-01", "44060"],    # Springfield, IL MSA (below threshold)
    ]


def mock_census_bps(mock: respx.MockRouter) -> respx.Route:
    """Register a GET route for Census BPS returning sample MSA permit counts."""
    route = mock.get(CENSUS_BPS_URL).mock(
        return_value=httpx.Response(200, json=_sample_bps_response())
    )
    return route


def mock_census_bps_empty(mock: respx.MockRouter) -> respx.Route:
    """Register a GET route that returns an empty BPS response (headers only)."""
    route = mock.get(CENSUS_BPS_URL).mock(
        return_value=httpx.Response(200, json=[["PERMITS", "time", "metropolitan statistical area/micropolitan statistical area"]])
    )
    return route


def mock_census_bps_error(mock: respx.MockRouter, status: int = 500) -> respx.Route:
    """Register a GET route that returns an HTTP error."""
    route = mock.get(CENSUS_BPS_URL).mock(
        return_value=httpx.Response(status, text="Internal Server Error")
    )
    return route
