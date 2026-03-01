from __future__ import annotations

import httpx
from bs4 import BeautifulSoup

from shared.logging_config import get_logger
from shared.models.contractor import ContractorLicense

from ..base_scraper import BaseLicenseScraper

logger = get_logger(__name__)

ROC_URL = "https://roc.az.gov/contractor-search"
USER_AGENT = "LeadGenMVP/1.0"


class ArizonaROCScraper(BaseLicenseScraper):
    state_code = "AZ"
    source_name = "AZ-ROC"
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
            params = {"trade": trade, "page": page}
            response = await client.get(ROC_URL, params=params)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            table = soup.find("table")
            if not table:
                return licenses

            rows = table.find_all("tr")[1:]
            for row in rows[:limit]:
                cells = row.find_all("td")
                if len(cells) >= 3:
                    licenses.append(ContractorLicense(
                        source="AZ-ROC",
                        license_number=cells[0].get_text(strip=True),
                        business_name=cells[1].get_text(strip=True),
                        trade_classification=cells[2].get_text(strip=True) or trade,
                        address_state="AZ",
                        phone=cells[3].get_text(strip=True) if len(cells) > 3 else "",
                        status="ACTIVE",
                    ))
        except Exception as e:
            logger.error("roc_search_error", trade=trade, error=str(e))

        return licenses

    async def get_details(self, license_number: str) -> ContractorLicense | None:
        results = await self.search()
        for lic in results:
            if lic.license_number == license_number:
                return lic
        return None

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
