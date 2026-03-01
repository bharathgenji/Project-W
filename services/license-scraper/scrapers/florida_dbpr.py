from __future__ import annotations

import re

import httpx
from bs4 import BeautifulSoup

from shared.logging_config import get_logger
from shared.models.contractor import ContractorLicense

from ..base_scraper import BaseLicenseScraper

logger = get_logger(__name__)

DBPR_SEARCH_URL = "https://www.myfloridalicense.com/wl11.asp"
USER_AGENT = "LeadGenMVP/1.0"


class FloridaDBPRScraper(BaseLicenseScraper):
    state_code = "FL"
    source_name = "FL-DBPR"
    delay_range = (2.0, 4.0)

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers={"User-Agent": USER_AGENT},
                timeout=30.0,
                follow_redirects=True,
            )
        return self._client

    async def search(
        self, trade: str = "", page: int = 0, limit: int = 50
    ) -> list[ContractorLicense]:
        client = await self._get_client()
        licenses: list[ContractorLicense] = []

        try:
            # Florida DBPR uses form POST for searches
            form_data = {
                "SID": "",
                "LicenseType": trade or "CGC",  # Certified General Contractor
                "BoardCode": "DBPR",
                "LicenseNumber": "",
                "LastName": "",
                "FirstName": "",
                "City": "",
                "County": "",
                "ZipCode": "",
                "BusinessName": "",
            }

            response = await client.post(DBPR_SEARCH_URL, data=form_data)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            table = soup.find("table", {"class": re.compile(r"results|data|grid", re.I)})
            if not table:
                tables = soup.find_all("table")
                table = tables[-1] if tables else None

            if not table:
                return licenses

            rows = table.find_all("tr")[1:]  # Skip header
            for row in rows[:limit]:
                cells = row.find_all("td")
                if len(cells) >= 4:
                    license_num = cells[0].get_text(strip=True)
                    name = cells[1].get_text(strip=True)
                    lic_type = cells[2].get_text(strip=True)
                    status = cells[3].get_text(strip=True)
                    county = cells[4].get_text(strip=True) if len(cells) > 4 else ""

                    if name:
                        licenses.append(ContractorLicense(
                            source="FL-DBPR",
                            license_number=license_num,
                            business_name=name,
                            trade_classification=lic_type or trade,
                            address_city=county,
                            address_state="FL",
                            status=status.upper() if status else "ACTIVE",
                        ))

        except Exception as e:
            logger.error("dbpr_search_error", trade=trade, error=str(e))

        return licenses

    async def get_details(self, license_number: str) -> ContractorLicense | None:
        client = await self._get_client()
        try:
            form_data = {
                "SID": "",
                "LicenseNumber": license_number,
                "LastName": "",
                "FirstName": "",
            }
            response = await client.post(DBPR_SEARCH_URL, data=form_data)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            # Parse detail fields
            name = _extract_field(soup, "Name", "Business Name")
            address = _extract_field(soup, "Address")
            phone = _extract_field(soup, "Phone")
            status = _extract_field(soup, "Status")
            county = _extract_field(soup, "County")

            if name:
                return ContractorLicense(
                    source="FL-DBPR",
                    license_number=license_number,
                    business_name=name,
                    address_street=address,
                    address_city=county,
                    address_state="FL",
                    phone=phone,
                    status=status.upper() if status else "ACTIVE",
                )
            return None
        except Exception as e:
            logger.error("dbpr_detail_error", license=license_number, error=str(e))
            return None

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()


def _extract_field(soup: BeautifulSoup, *labels: str) -> str:
    """Extract a field value from Florida DBPR detail page by label."""
    for label in labels:
        el = soup.find(string=re.compile(label, re.I))
        if el:
            parent = el.find_parent("td") or el.find_parent("th")
            if parent:
                next_td = parent.find_next_sibling("td")
                if next_td:
                    return next_td.get_text(strip=True)
    return ""
