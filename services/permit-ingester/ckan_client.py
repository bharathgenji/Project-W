"""CKAN Datastore API client for city permit portals.

Supports: San Antonio (data.sanantonio.gov), Boston (data.boston.gov),
          Philadelphia, Milwaukee, Louisville, San Jose, and any CKAN portal.

API pattern: /api/3/action/datastore_search?resource_id=<id>&limit=N&filters={}
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Any

import httpx

from shared.logging_config import get_logger

logger = get_logger(__name__)

CKAN_SOURCES = [
    {
        "id": "san-antonio",
        "name": "San Antonio",
        "state": "TX",
        "base_url": "https://data.sanantonio.gov",
        "resource_id": "c22b1ef2-dcf8-4d77-be1a-ee3638092aab",
        "field_map": {
            "permit_number": "PERMIT #",
            "permit_type":   "PERMIT TYPE",
            "work_description": "WORK TYPE",
            "address_street": "ADDRESS",
            "estimated_cost": "DECLARED VALUATION",
            "owner_name":     "PRIMARY CONTACT",
            "issued_date":    "DATE ISSUED",
            "lat":            "Y_COORD",
            "lng":            "X_COORD",
        },
        "date_field": "DATE ISSUED",    # field name for recency filter
        "date_format": "iso",
    },
    {
        "id": "boston",
        "name": "Boston",
        "state": "MA",
        "base_url": "https://data.boston.gov",
        "resource_id": "6ddcd912-32a0-43df-9908-63574f8c7e77",
        "field_map": {
            "permit_number":    "permitnumber",
            "permit_type":      "permittypedescr",
            "work_description": "description",
            "address_street":   "address",
            "address_zip":      "zip",
            "estimated_cost":   "declared_valuation",
            "contractor_name":  "applicant",
            "issued_date":      "issued_date",
        },
        "date_field": "issued_date",
        "date_format": "iso",
    },
]


async def fetch_ckan_permits(
    source: dict[str, Any],
    days_back: int = 30,
    max_records: int = 500,
) -> list[dict[str, Any]]:
    """Fetch permit records from a CKAN Datastore resource."""
    base_url = source["base_url"]
    resource_id = source["resource_id"]
    field_map = source["field_map"]
    date_field = source.get("date_field")

    since = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y-%m-%d")

    records: list[dict[str, Any]] = []
    offset = 0
    page_size = min(100, max_records)

    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        while len(records) < max_records:
            params: dict[str, Any] = {
                "resource_id": resource_id,
                "limit": page_size,
                "offset": offset,
            }
            # CKAN SQL filter for recency (only if date field exists and is reliable)
            # We use limit+sort instead of filters since date formats vary

            try:
                resp = await client.get(
                    f"{base_url}/api/3/action/datastore_search",
                    params=params,
                )
                resp.raise_for_status()
                data = resp.json()

                if not data.get("success"):
                    logger.warning(f"ckan_fetch_failed: {source['id']} — {data.get('error')}")
                    break

                rows = data["result"]["records"]
                if not rows:
                    break

                # Normalize each row using field_map
                for row in rows:
                    normalized = _normalize_row(row, field_map, source)
                    if normalized:
                        records.append(normalized)

                total = data["result"].get("total", 0)
                offset += len(rows)
                if offset >= total or offset >= max_records:
                    break

                await asyncio.sleep(0.2)  # be polite

            except Exception as e:
                logger.warning(f"ckan_fetch_error: {source['id']} — {e}")
                break

    logger.info(f"ckan_fetch_complete: {source['id']} records={len(records)}")
    return records[:max_records]


def _normalize_row(
    row: dict[str, Any],
    field_map: dict[str, str],
    source: dict[str, Any],
) -> dict[str, Any] | None:
    """Normalize a CKAN row using field_map to standard permit record format."""
    def get(key: str) -> Any:
        mapped = field_map.get(key)
        return row.get(mapped, "") if mapped else ""

    permit_number = str(get("permit_number") or "").strip()
    if not permit_number or permit_number == "nan":
        return None

    # Parse cost
    cost_raw = get("estimated_cost")
    try:
        cost = float(str(cost_raw).replace("$", "").replace(",", "")) if cost_raw else None
    except (ValueError, TypeError):
        cost = None

    # Parse coords
    lat, lng = None, None
    try:
        lat_raw = get("lat"); lng_raw = get("lng")
        if lat_raw: lat = float(lat_raw)
        if lng_raw: lng = float(lng_raw)
    except (ValueError, TypeError):
        pass

    return {
        "source_id":       f"{source['id']}-{permit_number}",
        "permit_number":   permit_number,
        "permit_type":     str(get("permit_type") or "BUILDING").strip().upper(),
        "work_description": str(get("work_description") or "").strip(),
        "address": {
            "street":   str(get("address_street") or "").strip().title(),
            "city":     source["name"],
            "state":    source["state"],
            "zip_code": str(get("address_zip") or "").strip(),
            "lat":      lat,
            "lng":      lng,
        },
        "estimated_cost": cost,
        "owner": {
            "name": str(get("owner_name") or "").strip(),
            "phone": "",
            "email": "",
        },
        "contractor": {
            "name": str(get("contractor_name") or "").strip(),
            "phone": "",
            "license_number": "",
        },
        "issued_date": str(get("issued_date") or "").strip() or None,
        "filed_date":  None,
        "status":      "active",
    }
