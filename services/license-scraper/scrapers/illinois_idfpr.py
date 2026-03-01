from __future__ import annotations

from shared.logging_config import get_logger
from shared.models.contractor import ContractorLicense

from ..base_scraper import BaseLicenseScraper
from .aspnet_generic import extract_viewstate

logger = get_logger(__name__)

IDFPR_URL = "https://www.idfpr.com/Applications/Licenselookup/Licenselookup.aspx"


class IllinoisIDFPRScraper(BaseLicenseScraper):
    state_code = "IL"
    source_name = "IL-IDFPR"
    delay_range = (2.0, 4.0)

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
            await browser_page.goto(IDFPR_URL)
            await browser_page.wait_for_load_state("networkidle")

            # Get ASP.NET ViewState
            await extract_viewstate(browser_page)

            # Fill search criteria
            profession_select = browser_page.locator("select[id*='Profession']")
            if await profession_select.count() > 0 and trade:
                try:
                    await profession_select.first.select_option(label=trade)
                except Exception:
                    pass

            # Submit
            search_btn = browser_page.locator(
                "input[id*='btnSearch'], input[type='submit']"
            )
            if await search_btn.count() > 0:
                await search_btn.first.click()
                await browser_page.wait_for_load_state("networkidle")

            # Parse results
            rows = browser_page.locator("table[id*='grd'] tr, table.results tr")
            count = await rows.count()
            for i in range(1, min(count, limit + 1)):
                try:
                    row = rows.nth(i)
                    cells = row.locator("td")
                    cell_count = await cells.count()
                    if cell_count >= 3:
                        texts = [await cells.nth(j).inner_text() for j in range(cell_count)]
                        licenses.append(ContractorLicense(
                            source="IL-IDFPR",
                            license_number=texts[0].strip(),
                            business_name=texts[1].strip(),
                            trade_classification=texts[2].strip() if len(texts) > 2 else "",
                            address_state="IL",
                            address_city=texts[3].strip() if len(texts) > 3 else "",
                            status=texts[4].strip().upper() if len(texts) > 4 else "ACTIVE",
                        ))
                except Exception:
                    continue

        except Exception as e:
            logger.error("idfpr_search_error", error=str(e))
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
