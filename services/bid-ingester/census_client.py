from __future__ import annotations

from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from shared.logging_config import get_logger

logger = get_logger(__name__)

CENSUS_BPS_BASE = "https://api.census.gov/data/timeseries/eits/bps"
USER_AGENT = "LeadGenMVP/1.0"


class CensusClient:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers={"User-Agent": USER_AGENT},
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    async def fetch_permit_survey(
        self,
        year: int | None = None,
        month: int | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch Census Building Permits Survey data (aggregate counts by MSA)."""
        client = await self._get_client()

        params: dict[str, str] = {
            "get": "PERMITS",
            "for": "metropolitan statistical area/micropolitan statistical area:*",
            "key": self.api_key,
        }
        if year:
            params["time"] = f"{year}" if not month else f"{year}-{month:02d}"

        response = await client.get(CENSUS_BPS_BASE, params=params)
        response.raise_for_status()
        raw = response.json()

        if not raw or len(raw) < 2:
            return []

        # First row is headers, rest is data
        headers = raw[0]
        results = []
        for row in raw[1:]:
            record = dict(zip(headers, row))
            results.append(record)

        logger.info("census_bps_fetched", records=len(results))
        return results

    async def get_hot_markets(self, min_permits: int = 100) -> list[dict[str, Any]]:
        """Identify MSAs with high permit activity."""
        data = await self.fetch_permit_survey()
        hot = []
        for record in data:
            try:
                permits = int(record.get("PERMITS", "0"))
                if permits >= min_permits:
                    hot.append({
                        "msa": record.get(
                            "metropolitan statistical area/micropolitan statistical area", ""
                        ),
                        "permits": permits,
                        "time": record.get("time", ""),
                    })
            except (ValueError, TypeError):
                continue
        return sorted(hot, key=lambda x: x["permits"], reverse=True)
