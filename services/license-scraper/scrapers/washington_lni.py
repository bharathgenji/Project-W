from __future__ import annotations

import httpx
from bs4 import BeautifulSoup

from shared.logging_config import get_logger
from shared.models.contractor import ContractorLicense

from ..base_scraper import BaseLicenseScraper

logger = get_logger(__name__)

LNI_URL = "https://secure.lni.wa.gov/verify/"
USER_AGENT = "LeadGenMVP/1.0"


class WashingtonLNIScraper(BaseLicenseScraper):
    state_code = "WA"
    source_name = "WA-LNI"
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
            params = {"ContractorName": trade or "construction", "page": page}
            response = await client.get(LNI_URL, params=params)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            results = soup.find_all("div", class_="result-item")

            if not results:
                table = soup.find("table")
                if table:
                    rows = table.find_all("tr")[1:]
                    for row in rows[:limit]:
                        cells = row.find_all("td")
                        if len(cells) >= 4:
                            licenses.append(ContractorLicense(
                                source="WA-LNI",
                                license_number=cells[0].get_text(strip=True),
                                business_name=cells[1].get_text(strip=True),
                                trade_classification=cells[2].get_text(strip=True),
                                address_state="WA",
                                status=cells[3].get_text(strip=True).upper() or "ACTIVE",
                            ))
            else:
                for item in results[:limit]:
                    name = item.find("h3") or item.find("strong")
                    lic_num = item.find("span", class_="license-number")
                    status = item.find("span", class_="status")

                    if name:
                        licenses.append(ContractorLicense(
                            source="WA-LNI",
                            license_number=lic_num.get_text(strip=True) if lic_num else "",
                            business_name=name.get_text(strip=True),
                            address_state="WA",
                            status=status.get_text(strip=True).upper() if status else "ACTIVE",
                        ))
        except Exception as e:
            logger.error("lni_search_error", trade=trade, error=str(e))

        return licenses

    async def get_details(self, license_number: str) -> ContractorLicense | None:
        client = await self._get_client()
        try:
            params = {"LicenseNumber": license_number}
            response = await client.get(LNI_URL, params=params)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            name_el = soup.find("h2") or soup.find("strong")
            if name_el:
                return ContractorLicense(
                    source="WA-LNI",
                    license_number=license_number,
                    business_name=name_el.get_text(strip=True),
                    address_state="WA",
                    status="ACTIVE",
                )
            return None
        except Exception as e:
            logger.error("lni_detail_error", license=license_number, error=str(e))
            return None

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
