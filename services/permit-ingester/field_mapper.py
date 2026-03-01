from __future__ import annotations

from datetime import datetime
from typing import Any

from shared.constants import PERMIT_TYPE_ALIASES
from shared.models.permit import Address, ContactInfo, PermitRecord


def _get(row: dict[str, Any], field_map: dict[str, str], key: str) -> str:
    """Safely get a mapped field value from a Socrata row."""
    mapped_key = field_map.get(key, "")
    if not mapped_key:
        return ""
    value = row.get(mapped_key, "")
    return str(value).strip() if value else ""


def _get_float(row: dict[str, Any], field_map: dict[str, str], key: str) -> float | None:
    """Get a float value from a mapped field."""
    raw = _get(row, field_map, key)
    if not raw:
        return None
    try:
        cleaned = raw.replace(",", "").replace("$", "").strip()
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def _parse_date(raw: str) -> datetime | None:
    """Parse various date formats from Socrata APIs."""
    if not raw:
        return None
    for fmt in [
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%m/%d/%y",
    ]:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def _normalize_permit_type(raw: str) -> str:
    """Map raw permit type to standard enum."""
    if not raw:
        return "OTHER"
    lower = raw.lower()
    for keyword, standard_type in PERMIT_TYPE_ALIASES.items():
        if keyword in lower:
            return standard_type
    return "OTHER"


def _build_address(row: dict[str, Any], field_map: dict[str, str], portal_state: str) -> Address:
    """Build a standard Address from mapped fields."""
    street_parts = []
    for key in ["address_street", "address_direction", "address_street_name", "address_suffix"]:
        val = _get(row, field_map, key)
        if val:
            street_parts.append(val)

    street = " ".join(street_parts) if street_parts else _get(row, field_map, "address_street")
    city = _get(row, field_map, "address_city")
    lat = _get_float(row, field_map, "lat")
    lng = _get_float(row, field_map, "lng")

    return Address(
        street=street,
        city=city,
        state=portal_state,
        zip=_get(row, field_map, "address_zip"),
        lat=lat,
        lng=lng,
    )


def map_to_permit(
    row: dict[str, Any],
    portal_id: str,
    field_map: dict[str, str],
    portal_state: str,
) -> PermitRecord:
    """Map a raw Socrata API row to a standardized PermitRecord."""
    return PermitRecord(
        source_id=f"{portal_id}-{_get(row, field_map, 'permit_number') or 'unknown'}",
        permit_number=_get(row, field_map, "permit_number"),
        permit_type=_normalize_permit_type(_get(row, field_map, "permit_type")),
        work_description=_get(row, field_map, "work_description"),
        address=_build_address(row, field_map, portal_state),
        estimated_cost=_get_float(row, field_map, "estimated_cost"),
        owner=ContactInfo(
            name=_get(row, field_map, "owner_name"),
            phone=_get(row, field_map, "owner_phone"),
            email=_get(row, field_map, "owner_email"),
        ),
        contractor=ContactInfo(
            name=_get(row, field_map, "contractor_name"),
            phone=_get(row, field_map, "contractor_phone"),
            email=_get(row, field_map, "contractor_email"),
        ),
        contractor_license=_get(row, field_map, "contractor_license"),
        status=_get(row, field_map, "status").upper() or "FILED",
        filed_date=_parse_date(_get(row, field_map, "filed_date")),
        issued_date=_parse_date(_get(row, field_map, "issued_date")),
        raw_data=row,
    )
