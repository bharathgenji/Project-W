from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from shared.logging_config import get_logger
from shared.models.bid import BidContact, BidLocation, BidRecord

logger = get_logger(__name__)

USASPENDING_BASE = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
USER_AGENT = "LeadGenMVP/1.0"


class USASpendingClient:
    def __init__(self) -> None:
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
    async def fetch_construction_awards(
        self,
        days_back: int = 30,
        limit: int = 100,
    ) -> list[BidRecord]:
        """Fetch recent federal construction contract awards."""
        client = await self._get_client()
        to_date = datetime.utcnow()
        from_date = to_date - timedelta(days=days_back)

        payload = {
            "filters": {
                "time_period": [
                    {
                        "start_date": from_date.strftime("%Y-%m-%d"),
                        "end_date": to_date.strftime("%Y-%m-%d"),
                    }
                ],
                "award_type_codes": ["A", "B", "C", "D"],  # Contract types
                "naics_codes": {
                    "require": ["2362", "2381", "2382", "2383", "2389"],
                },
            },
            "fields": [
                "Award ID",
                "Recipient Name",
                "Award Amount",
                "Awarding Agency",
                "Description",
                "Place of Performance State Code",
                "Place of Performance City Name",
                "Start Date",
            ],
            "limit": limit,
            "page": 1,
            "sort": "Award Amount",
            "order": "desc",
        }

        response = await client.post(USASPENDING_BASE, json=payload)
        response.raise_for_status()
        data = response.json()

        awards = []
        for result in data.get("results", []):
            try:
                bid = BidRecord(
                    source="usaspending",
                    bid_id=str(result.get("Award ID", "")),
                    title=str(result.get("Description", ""))[:200],
                    description=str(result.get("Description", "")),
                    agency=str(result.get("Awarding Agency", "")),
                    posted_date=_parse_date(result.get("Start Date")),
                    estimated_value=_parse_amount(result.get("Award Amount")),
                    location=BidLocation(
                        state=str(result.get("Place of Performance State Code", "")),
                        city=str(result.get("Place of Performance City Name", "")),
                    ),
                    contacts=[
                        BidContact(
                            name=str(result.get("Recipient Name", "")),
                            role="awardee",
                        )
                    ],
                    status="AWARDED",
                )
                awards.append(bid)
            except Exception as e:
                logger.warning("usaspending_parse_error", error=str(e))

        logger.info("usaspending_fetch_complete", total_awards=len(awards))
        return awards


def _parse_date(raw: Any) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.strptime(str(raw), "%Y-%m-%d")
    except ValueError:
        return None


def _parse_amount(raw: Any) -> float | None:
    if raw is None:
        return None
    try:
        return float(raw)
    except (ValueError, TypeError):
        return None
