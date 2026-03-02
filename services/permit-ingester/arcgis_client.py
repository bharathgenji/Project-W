"""
ArcGIS FeatureServer permit client.

Supports city permit layers that expose data via ArcGIS REST API.
Field normalization follows the same output contract as Socrata/CKAN clients.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# ── ArcGIS Source Registry ────────────────────────────────────────────────────
ARCGIS_SOURCES = [
    {
        "portal_id": "nashville",
        "city": "Nashville",
        "state": "TN",
        "url": (
            "https://maps.nashville.gov/arcgis/rest/services/"
            "Codes/BuildingPermits/MapServer/0/query"
        ),
        "field_map": {
            "permit_number":    "CASE_NUMBER",
            "permit_type":      "CASE_TYPE_DESC",
            "work_description": "SCOPE",
            "address_raw":      "LOCATION",
            "issued_date_ms":   "DATE_ISSUED",   # Unix ms timestamp
            "value":            "CONSTVAL",
            "status":           "STATUS_CODE",
            "sqft":             "BLDG_SQ_FT",
            "sub_type":         "SUB_TYPE_DESC",
            "units":            "UNITS",
        },
        "date_field": "DATE_ISSUED",
        "date_type":  "ms",   # epoch milliseconds → use DATE literal in query
        "page_size": 1000,
    },
    {
        "portal_id":  "portland",
        "city":       "Portland",
        "state":      "OR",
        "url": (
            "https://www.portlandmaps.com/arcgis/rest/services/"
            "Public/BDS_Permit/FeatureServer/2/query"
        ),
        "field_map": {
            "permit_number":    "APPLICATION",
            "permit_type":      "TYPE",
            "work_description": "WORK_DESCRIPTION",
            "address_parts":    ["HOUSE", "DIRECTION", "PROPSTREET", "STREETTYPE"],
            "issued_date_ms":   None,             # ISSUED is often null
            "value":            "SUBMITTEDVALUATION",
            "status":           "STATUS",
            "sqft":             "TOTALSQFT",
            "units":            "NUMNEWUNITS",
        },
        "date_field": "CREATEDATE",
        "date_type":  "literal",                  # DATE 'YYYY-MM-DD' syntax
        "page_size":  1000,
    },
    {
        "portal_id":  "portland-residential",
        "city":       "Portland",
        "state":      "OR",
        "url": (
            "https://www.portlandmaps.com/arcgis/rest/services/"
            "Public/BDS_Permit/FeatureServer/5/query"
        ),
        "field_map": {
            "permit_number":    "APPLICATION",
            "permit_type":      "TYPE",
            "work_description": "WORK_DESCRIPTION",
            "address_parts":    ["HOUSE", "DIRECTION", "PROPSTREET", "STREETTYPE"],
            "issued_date_ms":   None,
            "value":            "SUBMITTEDVALUATION",
            "status":           "STATUS",
            "sqft":             "TOTALSQFT",
            "units":            "NUMNEWUNITS",
        },
        "date_field": "CREATEDATE",
        "date_type":  "literal",
        "page_size":  1000,
    },
]

_BASE_PARAMS = {
    "f": "json",
    "outFields": "*",
    "returnGeometry": "false",
    "spatialRel": "esriSpatialRelIntersects",
}


def _ms_to_iso(ms: int | None) -> str | None:
    """Convert Unix milliseconds → ISO-8601 string."""
    if not ms:
        return None
    try:
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat()
    except (OSError, OverflowError):
        return None


def _parse_address(raw: str) -> dict[str, str]:
    """Parse ArcGIS address strings like '312 B NIX DR 37115'."""
    if not raw:
        return {"street": "", "city": "", "state": "", "zip": ""}
    raw = raw.strip()
    parts = raw.rsplit(" ", 1)
    zip_code = ""
    street = raw
    if len(parts) == 2 and parts[1].isdigit() and len(parts[1]) == 5:
        zip_code = parts[1]
        street = parts[0].strip()
    return {"street": street, "city": "", "state": "", "zip": zip_code}


def _build_address(source: dict, fm: dict, attrs: dict[str, Any]) -> dict:
    """Build address dict — handles both raw string and multi-part field configs."""
    # Multi-part address (e.g. Portland: HOUSE + DIRECTION + PROPSTREET + STREETTYPE)
    parts_keys = fm.get("address_parts")
    if parts_keys:
        parts = [str(attrs.get(k) or "").strip() for k in parts_keys]
        street = " ".join(p for p in parts if p).strip()
        return {
            "street": street,
            "city":   source["city"],
            "state":  source["state"],
            "zip":    "",
        }
    # Raw string (e.g. Nashville: "312 B NIX DR 37115")
    raw = str(attrs.get(fm.get("address_raw", ""), "") or "").strip()
    return {**_parse_address(raw), "city": source["city"], "state": source["state"]}


def _normalize_record(source: dict, attrs: dict[str, Any]) -> dict[str, Any]:
    """Map ArcGIS attributes → standard permit record format."""
    fm = source["field_map"]

    def g(key: str) -> Any:
        field = fm.get(key)
        return attrs.get(field) if field else None

    permit_number = str(g("permit_number") or "")
    permit_type   = str(g("permit_type") or "")
    work_desc     = str(g("work_description") or g("sub_type") or "")
    issued_ms     = g("issued_date_ms")
    value         = g("value")
    status        = str(g("status") or "")
    sqft          = g("sqft")
    units         = g("units")

    addr      = _build_address(source, fm, attrs)
    issued_iso = _ms_to_iso(issued_ms)

    # Fallback date: look for createdate string
    if not issued_iso:
        for df in ("CREATEDATE", "INTAKECOMPLETEDATE", "DATE_ACCEPTED"):
            raw_dt = attrs.get(df)
            if raw_dt:
                issued_iso = _ms_to_iso(raw_dt) if isinstance(raw_dt, int) else str(raw_dt)[:19]
                break

    portal_id = source["portal_id"]
    # Use source_id format matching Socrata/CKAN: "{portal_id}-{permit_number}"
    src_id = f"{portal_id}-{permit_number}" if permit_number else portal_id

    return {
        "source_id":        src_id,          # → lead.src in ETL pipeline
        "permit_number":    permit_number,
        "permit_type":      permit_type,
        "work_description": work_desc,
        "address":          addr,
        "issued_date":      issued_iso,
        "estimated_cost":   float(value) if value is not None and float(value) > 0 else None,
        "status":           status.lower() if status else "unknown",
        "applicant_name":   "",
        "owner":       {"name": "", "phone": "", "email": ""},
        "contractor":  {"name": "", "phone": "", "license": ""},
        "extra": {
            "sqft":       float(sqft)  if sqft  is not None else None,
            "units":      int(float(units)) if units is not None else None,
            "raw_status": status,
        },
        "src_portal": portal_id,
    }


async def fetch_arcgis_permits(
    days: int = 30,
    max_per_source: int = 500,
    timeout: float = 30.0,
) -> list[dict[str, Any]]:
    """Fetch recent permits from all configured ArcGIS sources."""
    all_records: list[dict] = []

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        for source in ARCGIS_SOURCES:
            portal_id = source["portal_id"]
            logger.info("ArcGIS ingest: %s", portal_id)
            try:
                records = await _fetch_source(client, source, days, max_per_source)
                logger.info("ArcGIS %s: %d records", portal_id, len(records))
                all_records.extend(records)
            except Exception as exc:
                logger.warning("ArcGIS %s failed: %s", portal_id, exc)

    return all_records


async def _fetch_source(
    client: httpx.AsyncClient,
    source: dict,
    days: int,
    max_records: int,
) -> list[dict[str, Any]]:
    url = source["url"]
    date_field = source.get("date_field")
    page_size = source.get("page_size", 1000)

    # Build time filter using ArcGIS date literal syntax (epoch ms NOT supported)
    where = "1=1"
    if date_field and days:
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)
        date_str = cutoff.strftime("%Y-%m-%d")
        where = f"{date_field} >= DATE '{date_str}'"

    records: list[dict] = []
    offset = 0

    while len(records) < max_records:
        batch_size = min(page_size, max_records - len(records))
        params = {
            **_BASE_PARAMS,
            "where": where,
            "resultRecordCount": batch_size,
            "resultOffset": offset,
            "orderByFields": f"{date_field} DESC" if date_field else "",
        }

        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

        if "error" in data:
            raise RuntimeError(f"ArcGIS error: {data['error'].get('message')}")

        features = data.get("features", [])
        if not features:
            break

        for feat in features:
            attrs = feat.get("attributes", {})
            try:
                records.append(_normalize_record(source, attrs))
            except Exception as exc:
                logger.debug("ArcGIS normalize error: %s", exc)

        if len(features) < batch_size:
            break  # No more pages

        offset += batch_size
        await asyncio.sleep(0.1)  # polite delay

    return records
