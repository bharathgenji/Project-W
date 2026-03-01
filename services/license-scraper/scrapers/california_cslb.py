from __future__ import annotations

from shared.logging_config import get_logger
from shared.models.contractor import ContractorLicense

from ..base_scraper import BaseLicenseScraper

logger = get_logger(__name__)

CSLB_URL = "https://www.cslb.ca.gov/OnlineServices/CheckLicenseII/CheckLicense.aspx"

# California CSLB classification codes
CA_CLASSIFICATIONS = [
    "A", "B",
    "C-2", "C-4", "C-5", "C-6", "C-7", "C-8", "C-9", "C-10",
    "C-11", "C-12", "C-13", "C-15", "C-16", "C-17", "C-20",
    "C-21", "C-22", "C-23", "C-27", "C-28", "C-29", "C-31",
    "C-32", "C-33", "C-34", "C-35", "C-36", "C-38", "C-39",
    "C-42", "C-43", "C-45", "C-46", "C-47", "C-50", "C-51",
    "C-53", "C-54", "C-55", "C-57", "C-60", "C-61",
]


class CaliforniaCSLBScraper(BaseLicenseScraper):
    state_code = "CA"
    source_name = "CA-CSLB"
    delay_range = (2.0, 4.0)

    def __init__(self) -> None:
        self._browser = None
        self._context = None

    async def _get_browser(self):  # type: ignore[no-untyped-def]
        if self._browser is None:
            from playwright.async_api import async_playwright
            pw = await async_playwright().start()
            self._browser = await pw.chromium.launch(headless=True)
            self._context = await self._browser.new_context(
                user_agent="LeadGenMVP/1.0"
            )
        return self._context

    async def search(
        self, trade: str = "", page: int = 0, limit: int = 50
    ) -> list[ContractorLicense]:
        """Search CSLB by classification code."""
        classification = trade or "B"
        context = await self._get_browser()
        browser_page = await context.new_page()

        try:
            await browser_page.goto(CSLB_URL)
            await browser_page.wait_for_load_state("networkidle")

            # Fill in classification search
            classification_input = browser_page.locator("#ContentPlaceHolder1_txtLicNum")
            if await classification_input.count() > 0:
                # Search by license number range for pagination
                start_num = page * limit
                await classification_input.fill(str(start_num + 1))

            # Submit the form
            submit_btn = browser_page.locator(
                "#ContentPlaceHolder1_btnSearch, input[type='submit']"
            )
            if await submit_btn.count() > 0:
                await submit_btn.first.click()
                await browser_page.wait_for_load_state("networkidle")

            # Parse results
            results = await self._parse_results(browser_page, classification)
            return results

        except Exception as e:
            logger.error("cslb_search_error", classification=classification, error=str(e))
            return []
        finally:
            await browser_page.close()

    async def _parse_results(
        self, browser_page: object, classification: str
    ) -> list[ContractorLicense]:
        """Parse CSLB search results page."""
        licenses: list[ContractorLicense] = []

        try:
            page = browser_page  # type: ignore[assignment]
            # Try to find license info on detail page
            name_el = page.locator("#ContentPlaceHolder1_lblBusinessName, .business-name")  # type: ignore[union-attr]
            if await name_el.count() > 0:  # type: ignore[union-attr]
                business_name = await name_el.first.inner_text()  # type: ignore[union-attr]

                lic_num_el = page.locator("#ContentPlaceHolder1_lblLicNum, .license-number")  # type: ignore[union-attr]
                lic_num = (
                    await lic_num_el.first.inner_text()  # type: ignore[union-attr]
                    if await lic_num_el.count() > 0  # type: ignore[union-attr]
                    else ""
                )

                status_el = page.locator("#ContentPlaceHolder1_lblStatus, .status")  # type: ignore[union-attr]
                status = (
                    await status_el.first.inner_text()  # type: ignore[union-attr]
                    if await status_el.count() > 0  # type: ignore[union-attr]
                    else ""
                )

                addr_el = page.locator("#ContentPlaceHolder1_lblAddress, .address")  # type: ignore[union-attr]
                address = (
                    await addr_el.first.inner_text()  # type: ignore[union-attr]
                    if await addr_el.count() > 0  # type: ignore[union-attr]
                    else ""
                )

                phone_el = page.locator("#ContentPlaceHolder1_lblPhone, .phone")  # type: ignore[union-attr]
                phone = (
                    await phone_el.first.inner_text()  # type: ignore[union-attr]
                    if await phone_el.count() > 0  # type: ignore[union-attr]
                    else ""
                )

                if business_name.strip():
                    licenses.append(ContractorLicense(
                        source="CA-CSLB",
                        license_number=lic_num.strip(),
                        business_name=business_name.strip(),
                        trade_classification=classification,
                        address_street=address.strip(),
                        address_state="CA",
                        phone=phone.strip(),
                        status=_normalize_status(status),
                    ))
        except Exception as e:
            logger.debug("cslb_parse_error", error=str(e))

        return licenses

    async def get_details(self, license_number: str) -> ContractorLicense | None:
        """Look up a specific license by number."""
        context = await self._get_browser()
        page = await context.new_page()
        try:
            await page.goto(CSLB_URL)
            await page.wait_for_load_state("networkidle")

            lic_input = page.locator("#ContentPlaceHolder1_txtLicNum")
            if await lic_input.count() > 0:
                await lic_input.fill(license_number)

            submit = page.locator("#ContentPlaceHolder1_btnSearch, input[type='submit']")
            if await submit.count() > 0:
                await submit.first.click()
                await page.wait_for_load_state("networkidle")

            results = await self._parse_results(page, "")
            return results[0] if results else None
        except Exception as e:
            logger.error("cslb_detail_error", license=license_number, error=str(e))
            return None
        finally:
            await page.close()

    async def close(self) -> None:
        if self._browser:
            await self._browser.close()
            self._browser = None
            self._context = None


def _normalize_status(raw: str) -> str:
    raw_upper = raw.strip().upper()
    if "ACTIVE" in raw_upper:
        return "ACTIVE"
    if "EXPIRE" in raw_upper:
        return "EXPIRED"
    if "SUSPEND" in raw_upper:
        return "SUSPENDED"
    if "REVOKE" in raw_upper:
        return "REVOKED"
    return raw_upper or "UNKNOWN"
