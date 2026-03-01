from __future__ import annotations

from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from shared.logging_config import get_logger

logger = get_logger(__name__)

DEFAULT_LIMIT = 1000
DEFAULT_TIMEOUT = 30.0
USER_AGENT = "LeadGenMVP/1.0"


class SocrataClient:
    def __init__(self, app_token: str | None = None) -> None:
        self.app_token = app_token
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers: dict[str, str] = {"User-Agent": USER_AGENT}
            if self.app_token:
                headers["X-App-Token"] = self.app_token
            self._client = httpx.AsyncClient(
                headers=headers,
                timeout=DEFAULT_TIMEOUT,
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
    async def fetch_page(
        self,
        domain: str,
        dataset_id: str,
        offset: int = 0,
        limit: int = DEFAULT_LIMIT,
        where_clause: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch a single page of data from a Socrata SODA API endpoint."""
        client = await self._get_client()
        url = f"https://{domain}/resource/{dataset_id}.json"
        params: dict[str, str | int] = {
            "$limit": limit,
            "$offset": offset,
        }
        if where_clause:
            params["$where"] = where_clause

        logger.info(
            "fetching_socrata_page",
            domain=domain,
            dataset_id=dataset_id,
            offset=offset,
            limit=limit,
        )

        response = await client.get(url, params=params)
        response.raise_for_status()
        data: list[dict[str, Any]] = response.json()
        return data

    async def fetch_all(
        self,
        domain: str,
        dataset_id: str,
        where_clause: str | None = None,
        max_records: int = 5000,
    ) -> list[dict[str, Any]]:
        """Fetch all pages of data, up to max_records."""
        all_records: list[dict[str, Any]] = []
        offset = 0

        while offset < max_records:
            limit = min(DEFAULT_LIMIT, max_records - offset)
            page = await self.fetch_page(
                domain=domain,
                dataset_id=dataset_id,
                offset=offset,
                limit=limit,
                where_clause=where_clause,
            )
            if not page:
                break
            all_records.extend(page)
            if len(page) < limit:
                break
            offset += limit

        logger.info(
            "socrata_fetch_complete",
            domain=domain,
            dataset_id=dataset_id,
            total_records=len(all_records),
        )
        return all_records

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def discover_datasets(
        self, domain: str, query: str = "building permit"
    ) -> list[dict[str, Any]]:
        """Discover datasets on a Socrata portal by search query."""
        client = await self._get_client()
        url = f"https://{domain}/api/views.json"
        params = {"q": query, "limit": 20}

        response = await client.get(url, params=params)
        response.raise_for_status()
        results: list[dict[str, Any]] = response.json()
        return results
