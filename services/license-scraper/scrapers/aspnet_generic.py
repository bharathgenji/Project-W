from __future__ import annotations

import re
from typing import Any


async def extract_viewstate(page: Any) -> dict[str, str]:
    """Extract ASP.NET ViewState fields from a Playwright page."""
    fields = {}
    for field_name in ["__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION"]:
        try:
            element = await page.query_selector(f"input[name='{field_name}']")
            if element:
                value = await element.get_attribute("value")
                if value:
                    fields[field_name] = value
        except Exception:
            pass
    return fields


async def submit_aspnet_form(
    page: Any,
    form_data: dict[str, str],
    submit_button_selector: str = "input[type='submit']",
) -> None:
    """Fill and submit an ASP.NET form with ViewState handling."""
    viewstate = await extract_viewstate(page)
    all_data = {**viewstate, **form_data}

    for field_name, value in all_data.items():
        if field_name.startswith("__"):
            continue
        try:
            await page.fill(f"[name='{field_name}']", value)
        except Exception:
            try:
                await page.select_option(f"[name='{field_name}']", value)
            except Exception:
                pass

    await page.click(submit_button_selector)
    await page.wait_for_load_state("networkidle")


def parse_table_rows(html: str) -> list[dict[str, str]]:
    """Parse HTML table rows into list of dicts using regex (lightweight)."""
    rows: list[dict[str, str]] = []
    header_pattern = re.compile(r"<th[^>]*>(.*?)</th>", re.IGNORECASE | re.DOTALL)
    row_pattern = re.compile(r"<tr[^>]*>(.*?)</tr>", re.IGNORECASE | re.DOTALL)
    cell_pattern = re.compile(r"<td[^>]*>(.*?)</td>", re.IGNORECASE | re.DOTALL)

    headers: list[str] = []
    for match in row_pattern.finditer(html):
        row_html = match.group(1)
        header_matches = header_pattern.findall(row_html)
        if header_matches:
            headers = [re.sub(r"<[^>]+>", "", h).strip() for h in header_matches]
            continue
        cells = cell_pattern.findall(row_html)
        if cells and headers:
            cleaned = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]
            row_dict = dict(zip(headers, cleaned))
            if any(row_dict.values()):
                rows.append(row_dict)

    return rows
