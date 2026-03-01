from __future__ import annotations

from typing import Any

import jellyfish

from shared.logging_config import get_logger
from shared.utils import generate_id

logger = get_logger(__name__)

JARO_WINKLER_THRESHOLD = 0.85


def generate_lead_id(record: dict[str, Any]) -> str:
    """Generate a deterministic ID for a lead record."""
    record_type = record.get("type", "permit")
    if record_type == "permit":
        return generate_id(
            record.get("source_id", ""),
            record.get("permit_number", ""),
        )
    else:
        return generate_id(
            record.get("source", ""),
            record.get("bid_id", ""),
        )


def generate_contractor_id(name: str, state: str) -> str:
    """Generate a deterministic ID for a contractor."""
    return generate_id(name.lower().strip(), state.upper().strip())


def find_duplicate_contractor(
    name: str,
    city: str,
    zip_code: str,
    license_number: str,
    existing_contractors: list[dict[str, Any]],
) -> tuple[str | None, float]:
    """Find a matching contractor in existing records.

    Returns (existing_id, confidence) or (None, 0.0) if no match.
    """
    if not name:
        return (None, 0.0)

    name_clean = name.strip().upper()

    for contractor in existing_contractors:
        existing_name = (contractor.get("name", "") or "").strip().upper()
        existing_city = (contractor.get("addr", "").split(",")[0] if contractor.get("addr") else "").strip().upper()
        existing_id = contractor.get("id", "")

        # Exact license number match -> 100% confidence
        existing_licenses = contractor.get("licenses", [])
        if license_number:
            for lic in existing_licenses:
                if lic.get("num", "") == license_number:
                    return (existing_id, 1.0)

        # Fuzzy name matching
        if not existing_name:
            continue

        similarity = jellyfish.jaro_winkler_similarity(name_clean, existing_name)

        if similarity >= JARO_WINKLER_THRESHOLD:
            # Name match + same city -> 90% confidence
            if city and existing_city and city.strip().upper() == existing_city:
                return (existing_id, 0.90)

            # Name match + same zip -> 85% confidence
            existing_zip = ""
            addr = contractor.get("addr", "")
            if addr:
                parts = addr.split()
                for part in parts:
                    if part.isdigit() and len(part) == 5:
                        existing_zip = part
                        break
            if zip_code and existing_zip and zip_code == existing_zip:
                return (existing_id, 0.85)

    return (None, 0.0)


def merge_contractor_profiles(
    existing: dict[str, Any], new_data: dict[str, Any]
) -> dict[str, Any]:
    """Merge two contractor profiles, preferring more complete data."""
    merged = {**existing}

    # Prefer non-empty values from new data
    for key in ["name", "phone", "email", "website", "addr"]:
        new_val = new_data.get(key, "")
        existing_val = existing.get(key, "")
        if new_val and (not existing_val or len(str(new_val)) > len(str(existing_val))):
            merged[key] = new_val

    # Merge trades list
    existing_trades = set(existing.get("trades", []))
    new_trades = set(new_data.get("trades", []))
    merged["trades"] = list(existing_trades | new_trades)

    # Merge licenses list (avoid duplicates by license number)
    existing_licenses = {
        lic.get("num", ""): lic for lic in existing.get("licenses", [])
    }
    for lic in new_data.get("licenses", []):
        num = lic.get("num", "")
        if num and num not in existing_licenses:
            existing_licenses[num] = lic
    merged["licenses"] = list(existing_licenses.values())

    # Update stats
    merged["permit_count"] = existing.get("permit_count", 0) + new_data.get("permit_count", 0)

    return merged
