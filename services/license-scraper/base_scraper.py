from __future__ import annotations

import asyncio
import random
from abc import ABC, abstractmethod

from shared.logging_config import get_logger
from shared.models.contractor import ContractorLicense

logger = get_logger(__name__)


class BaseLicenseScraper(ABC):
    """Abstract base class for state contractor license scrapers."""

    state_code: str = ""
    source_name: str = ""
    delay_range: tuple[float, float] = (2.0, 5.0)
    max_records_per_run: int = 500

    @abstractmethod
    async def search(
        self, trade: str = "", page: int = 0, limit: int = 50
    ) -> list[ContractorLicense]:
        """Search for contractor licenses by trade classification."""
        ...

    @abstractmethod
    async def get_details(self, license_number: str) -> ContractorLicense | None:
        """Get full details for a specific license number."""
        ...

    async def rate_limit_delay(self) -> None:
        """Wait a random delay to respect rate limits."""
        delay = random.uniform(*self.delay_range)
        await asyncio.sleep(delay)

    async def scrape_batch(self, trades: list[str] | None = None) -> list[ContractorLicense]:
        """Scrape a batch of licenses across trades, respecting rate limits."""
        all_licenses: list[ContractorLicense] = []
        search_trades = trades or [""]

        for trade in search_trades:
            page = 0
            while len(all_licenses) < self.max_records_per_run:
                try:
                    results = await self.search(trade=trade, page=page)
                    if not results:
                        break
                    all_licenses.extend(results)
                    page += 1
                    await self.rate_limit_delay()
                except Exception as e:
                    logger.warning(
                        "scraper_page_error",
                        source=self.source_name,
                        trade=trade,
                        page=page,
                        error=str(e),
                    )
                    break

        logger.info(
            "scrape_batch_complete",
            source=self.source_name,
            total=len(all_licenses),
        )
        return all_licenses[:self.max_records_per_run]

    async def close(self) -> None:
        """Clean up resources. Override in subclasses if needed."""
        pass
