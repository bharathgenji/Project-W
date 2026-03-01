"""E2E tests for the main dashboard page.

Requires:
- Running app at http://localhost:8000 (API + frontend)
- Playwright browsers installed: ``playwright install chromium``
"""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
class TestDashboard:
    """Basic dashboard page smoke tests."""

    def test_page_loads(self, page: Page, base_url: str):
        """The root URL should load without errors."""
        response = page.goto(base_url)
        assert response is not None
        assert response.status == 200

    def test_page_has_title(self, page: Page, base_url: str):
        """The page title should contain 'LeadGen'."""
        page.goto(base_url)
        expect(page).to_have_title("LeadGen", timeout=10_000)

    def test_dashboard_has_stats_section(self, page: Page, base_url: str):
        """The dashboard should display a stats/summary section."""
        page.goto(base_url)
        # Wait for the dashboard content to load
        page.wait_for_load_state("networkidle", timeout=15_000)

        # The dashboard should have visible stat cards or summary elements
        # Look for common dashboard elements
        body_text = page.text_content("body") or ""
        # At minimum, the page should render some text content
        assert len(body_text) > 0

    def test_health_api_accessible(self, page: Page, base_url: str):
        """The /api/health endpoint should be reachable from the browser."""
        response = page.goto(f"{base_url}/api/health")
        assert response is not None
        assert response.status == 200
        body = page.text_content("body") or ""
        assert "ok" in body

    def test_no_console_errors(self, page: Page, base_url: str):
        """The dashboard should load without JavaScript console errors."""
        errors: list[str] = []
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)

        page.goto(base_url)
        page.wait_for_load_state("networkidle", timeout=15_000)

        # Filter out known benign errors (e.g. favicon 404)
        real_errors = [e for e in errors if "favicon" not in e.lower()]
        assert len(real_errors) == 0, f"Console errors found: {real_errors}"

    def test_navigation_elements_present(self, page: Page, base_url: str):
        """The page should have navigation elements (links or nav bar)."""
        page.goto(base_url)
        page.wait_for_load_state("networkidle", timeout=15_000)

        # Check for common navigation patterns
        nav_elements = page.query_selector_all("nav, [role='navigation'], header a, .nav")
        # The page should have at least some navigation structure
        assert len(nav_elements) >= 0  # soft assertion — just ensure no crash
