from __future__ import annotations

from shared.logging_config import get_logger
from shared.models.contractor import ContractorLicense

from ..base_scraper import BaseLicenseScraper

logger = get_logger(__name__)

TDLR_URL = "https://www.tdlr.texas.gov/LicenseSearch/"


class TexasTDLRScraper(BaseLicenseScraper):
    state_code = "TX"
    source_name = "TX-TDLR"
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
            await browser_page.goto(TDLR_URL)
            await browser_page.wait_for_load_state("networkidle")

            # TDLR has a search by license type
            if trade:
                type_select = browser_page.locator("select[id*='licenseType'], select[name*='type']")
                if await type_select.count() > 0:
                    try:
                        await type_select.first.select_option(label=trade)
                    except Exception:
                        pass

            # Submit search
            search_btn = browser_page.locator("button:has-text('Search'), input[value='Search']")
            if await search_btn.count() > 0:
                await search_btn.first.click()
                await browser_page.wait_for_load_state("networkidle")

            # Parse results table
            rows = browser_page.locator("table tbody tr, .search-results tr")
            count = await rows.count()
            for i in range(min(count, limit)):
                try:
                    row = rows.nth(i)
                    cells = row.locator("td")
                    cell_count = await cells.count()
                    if cell_count >= 3:
                        cell_texts = [
                            await cells.nth(j).inner_text() for j in range(cell_count)
                        ]
                        licenses.append(ContractorLicense(
                            source="TX-TDLR",
                            license_number=cell_texts[0].strip() if len(cell_texts) > 0 else "",
                            business_name=cell_texts[1].strip() if len(cell_texts) > 1 else "",
                            trade_classification=cell_texts[2].strip() if len(cell_texts) > 2 else trade,
                            address_state="TX",
                            status=cell_texts[3].strip().upper() if len(cell_texts) > 3 else "ACTIVE",
                        ))
                except Exception as e:
                    logger.debug("tdlr_row_parse_error", row=i, error=str(e))

        except Exception as e:
            logger.error("tdlr_search_error", trade=trade, error=str(e))
        finally:
            await browser_page.close()

        return licenses

    async def get_details(self, license_number: str) -> ContractorLicense | None:
        context = await self._get_browser()
        page = await context.new_page()
        try:
            await page.goto(TDLR_URL)
            await page.wait_for_load_state("networkidle")

            lic_input = page.locator("input[id*='licenseNumber'], input[name*='license']")
            if await lic_input.count() > 0:
                await lic_input.first.fill(license_number)

            search_btn = page.locator("button:has-text('Search'), input[value='Search']")
            if await search_btn.count() > 0:
                await search_btn.first.click()
                await page.wait_for_load_state("networkidle")

            # Parse detail page
            name_el = page.locator(".licensee-name, td:has-text('Name') + td")
            name = await name_el.first.inner_text() if await name_el.count() > 0 else ""

            if name.strip():
                return ContractorLicense(
                    source="TX-TDLR",
                    license_number=license_number,
                    business_name=name.strip(),
                    address_state="TX",
                    status="ACTIVE",
                )
            return None
        except Exception as e:
            logger.error("tdlr_detail_error", license=license_number, error=str(e))
            return None
        finally:
            await page.close()

    async def close(self) -> None:
        if self._browser:
            await self._browser.close()
            self._browser = None
            self._context = None
