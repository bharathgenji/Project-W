"""E2E test configuration — Playwright fixtures for browser-based tests.

Requires:
- The API server running at http://localhost:8000
- The frontend dev server or built static files served
- ``pip install pytest-playwright`` and ``playwright install``
"""
from __future__ import annotations

import pytest


@pytest.fixture(scope="session")
def base_url() -> str:
    """Base URL for the running application."""
    return "http://localhost:8000"


@pytest.fixture(scope="session")
def browser_context_args() -> dict:
    """Default browser context arguments for Playwright."""
    return {
        "viewport": {"width": 1280, "height": 720},
        "ignore_https_errors": True,
    }
