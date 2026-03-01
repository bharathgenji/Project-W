from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from shared.constants import CONSTRUCTION_NAICS, NAICS_TO_TRADE
from shared.logging_config import get_logger
from shared.models.bid import BidContact, BidLocation, BidRecord

logger = get_logger(__name__)

SAM_API_BASE = "https://api.sam.gov/prod/opportunities/v2/search"
USER_AGENT = "LeadGenMVP/1.0"


class SamGovClient:
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
    async def _fetch_page(
        self,
        naics_code: str,
        posted_from: str,
        posted_to: str,
        offset: int = 0,
        limit: int = 100,
    ) -> dict[str, Any]:
        client = await self._get_client()
        params = {
            "api_key": self.api_key,
            "limit": limit,
            "offset": offset,
            "postedFrom": posted_from,
            "postedTo": posted_to,
            "ptype": "o,p,k",  # solicitations, presolicitations, combined
            "ncode": naics_code,
        }
        response = await client.get(SAM_API_BASE, params=params)
        response.raise_for_status()
        return response.json()

    def _parse_opportunity(self, opp: dict[str, Any], naics_code: str) -> BidRecord:
        """Parse a SAM.gov opportunity into a BidRecord."""
        contacts = []
        for poc in (opp.get("pointOfContact") or []):
            if not isinstance(poc, dict):
                continue
            contacts.append(BidContact(
                name=poc.get("fullName") or "",
                email=poc.get("email") or "",
                phone=poc.get("phone") or "",
                role=poc.get("type") or "",
            ))

        place = opp.get("placeOfPerformance") or {}
        city_info = place.get("city") or {}
        state_info = place.get("state") or {}

        return BidRecord(
            source="sam.gov",
            bid_id=opp.get("noticeId", ""),
            title=opp.get("title", ""),
            description=opp.get("description", "")[:500],
            agency=opp.get("fullParentPathName", ""),
            posted_date=_parse_date(opp.get("postedDate")),
            response_deadline=_parse_date(opp.get("responseDeadLine")),
            naics_code=naics_code,
            trade_category=NAICS_TO_TRADE.get(naics_code, "GENERAL"),
            estimated_value=None,
            set_aside=_normalize_set_aside(opp.get("typeOfSetAside", "")),
            location=BidLocation(
                state=state_info.get("code", ""),
                city=city_info.get("name", ""),
                zip_code=place.get("zip", ""),
            ),
            contacts=contacts,
            status=_normalize_status(opp.get("type", "")),
            raw_data=opp,
        )

    async def fetch_construction_opportunities(
        self,
        days_back: int = 7,
        max_per_naics: int = 100,
    ) -> list[BidRecord]:
        """Fetch all construction opportunities across NAICS codes."""
        to_date = datetime.now(timezone.utc)
        from_date = to_date - timedelta(days=days_back)
        posted_from = from_date.strftime("%m/%d/%Y")
        posted_to = to_date.strftime("%m/%d/%Y")

        all_bids: list[BidRecord] = []

        for naics in CONSTRUCTION_NAICS:
            try:
                result = await self._fetch_page(
                    naics_code=naics,
                    posted_from=posted_from,
                    posted_to=posted_to,
                    limit=max_per_naics,
                )
                opportunities = result.get("opportunitiesData", [])
                for opp in opportunities:
                    try:
                        bid = self._parse_opportunity(opp, naics)
                        all_bids.append(bid)
                    except Exception as e:
                        logger.warning("sam_parse_error", naics=naics, error=str(e))
                logger.info("sam_naics_fetched", naics=naics, count=len(opportunities))
            except httpx.HTTPStatusError as e:
                logger.error("sam_fetch_failed", naics=naics, status=e.response.status_code)

        logger.info("sam_fetch_complete", total_bids=len(all_bids))
        return all_bids


def _parse_date(raw: str | None) -> datetime | None:
    if not raw:
        return None
    for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%m/%d/%Y"]:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def _normalize_set_aside(raw: str) -> str:
    mapping = {
        "SBA": "SMALL_BUSINESS",
        "8A": "8A",
        "HZC": "HUBZONE",
        "WOSB": "WOSB",
        "SDVOSBC": "SDVOSB",
    }
    return mapping.get(raw.upper(), "NONE") if raw else "NONE"


def _normalize_status(raw: str) -> str:
    mapping = {
        "p": "PRESOLICITATION",
        "o": "ACTIVE",
        "k": "ACTIVE",
        "a": "AWARDED",
    }
    return mapping.get(raw.lower(), "ACTIVE") if raw else "ACTIVE"
