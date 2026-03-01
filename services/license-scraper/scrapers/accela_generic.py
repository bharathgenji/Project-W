from __future__ import annotations

from typing import Any

from shared.logging_config import get_logger

logger = get_logger(__name__)


async def search_accela_portal(
    page: Any,
    base_url: str,
    license_type: str = "",
    search_name: str = "",
) -> list[dict[str, str]]:
    """Generic search handler for Accela-powered license portals.

    Accela is used by Michigan, Maryland, and many smaller states.
    The UI pattern is standardized across deployments.
    """
    await page.goto(base_url)
    await page.wait_for_load_state("networkidle")

    # Accela portals typically have a license type dropdown and name search
    if license_type:
        try:
            select = page.locator("select[id*='LicenseType'], select[id*='licType']")
            if await select.count() > 0:
                await select.first.select_option(label=license_type)
        except Exception as e:
            logger.debug("accela_type_select_failed", error=str(e))

    if search_name:
        try:
            name_input = page.locator(
                "input[id*='BusinessName'], input[id*='LastName'], input[id*='searchName']"
            )
            if await name_input.count() > 0:
                await name_input.first.fill(search_name)
        except Exception as e:
            logger.debug("accela_name_fill_failed", error=str(e))

    # Click search button
    try:
        search_btn = page.locator("button:has-text('Search'), input[value='Search']")
        if await search_btn.count() > 0:
            await search_btn.first.click()
            await page.wait_for_load_state("networkidle")
    except Exception as e:
        logger.warning("accela_search_click_failed", error=str(e))
        return []

    # Parse results table
    results: list[dict[str, str]] = []
    try:
        rows = page.locator("table.ACA_Grid_Default tr, table[id*='Result'] tr")
        count = await rows.count()
        headers: list[str] = []
        for i in range(count):
            row = rows.nth(i)
            ths = row.locator("th")
            if await ths.count() > 0:
                headers = [await ths.nth(j).inner_text() for j in range(await ths.count())]
                continue
            tds = row.locator("td")
            td_count = await tds.count()
            if td_count > 0 and headers:
                cells = [await tds.nth(j).inner_text() for j in range(td_count)]
                row_dict = dict(zip(headers, cells))
                if any(row_dict.values()):
                    results.append(row_dict)
    except Exception as e:
        logger.warning("accela_parse_failed", error=str(e))

    return results
