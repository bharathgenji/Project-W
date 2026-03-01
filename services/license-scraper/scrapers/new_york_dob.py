from __future__ import annotations

from shared.logging_config import get_logger
from shared.models.contractor import ContractorLicense

from ..base_scraper import BaseLicenseScraper

logger = get_logger(__name__)

NYC_DOB_URL = "https://a810-bisweb.nyc.gov/bisweb/"


class NewYorkDOBScraper(BaseLicenseScraper):
    state_code = "NY"
    source_name = "NY-DOB"
    delay_range = (3.0, 5.0)

    def __init__(self) -> None:
        self._browser = None
        self._context = None

    async def _get_browser(self):  # type: ignore[no-untyped-def]
        if self._browser is None:
            from playwright.async_api import async_playwright
            pw = await async_playwright().start()
            self._browser = await pw.chromium.launch(headless=True)
            self._context = await self._browser.new_context(user_agent="LeadGenMVP/1.0")
        return self._context

    async def search(
        self, trade: str = "", page: int = 0, limit: int = 50
    ) -> list[ContractorLicense]:
        context = await self._get_browser()
        browser_page = await context.new_page()
        licenses: list[ContractorLicense] = []

        try:
            await browser_page.goto(NYC_DOB_URL)
            await browser_page.wait_for_load_state("networkidle")

            # NYC DOB has a license lookup section
            link = browser_page.locator("a:has-text('License'), a[href*='license']")
            if await link.count() > 0:
                await link.first.click()
                await browser_page.wait_for_load_state("networkidle")

            # Search by business name or license type
            name_input = browser_page.locator("input[name*='name'], input[name*='business']")
            if await name_input.count() > 0 and trade:
                await name_input.first.fill(trade)

            submit = browser_page.locator("input[type='submit'], button:has-text('Search')")
            if await submit.count() > 0:
                await submit.first.click()
                await browser_page.wait_for_load_state("networkidle")

            # Parse results
            rows = browser_page.locator("table tr")
            count = await rows.count()
            for i in range(1, min(count, limit + 1)):
                try:
                    row = rows.nth(i)
                    cells = row.locator("td")
                    cell_count = await cells.count()
                    if cell_count >= 3:
                        texts = [await cells.nth(j).inner_text() for j in range(cell_count)]
                        licenses.append(ContractorLicense(
                            source="NY-DOB",
                            license_number=texts[0].strip(),
                            business_name=texts[1].strip(),
                            trade_classification=texts[2].strip() if len(texts) > 2 else "",
                            address_state="NY",
                            status="ACTIVE",
                        ))
                except Exception:
                    continue

        except Exception as e:
            logger.error("nyc_dob_search_error", error=str(e))
        finally:
            await browser_page.close()

        return licenses

    async def get_details(self, license_number: str) -> ContractorLicense | None:
        results = await self.search(trade=license_number, limit=1)
        return results[0] if results else None

    async def close(self) -> None:
        if self._browser:
            await self._browser.close()
            self._browser = None
            self._context = None
