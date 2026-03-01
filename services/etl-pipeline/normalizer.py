from __future__ import annotations

from shared.constants import PERMIT_TYPE_ALIASES
from shared.utils import normalize_address_street, normalize_business_name, normalize_phone


def normalize_address(raw: dict) -> dict:
    """Normalize an address dict to USPS-like format."""
    return {
        "street": normalize_address_street(raw.get("street", "")),
        "city": (raw.get("city", "") or "").strip().title(),
        "state": (raw.get("state", "") or "").strip().upper()[:2],
        "zip_code": _clean_zip(raw.get("zip_code", "") or raw.get("zip", "")),
        "lat": raw.get("lat"),
        "lng": raw.get("lng"),
    }


def normalize_contact(raw: dict) -> dict:
    """Normalize a contact dict (name, phone, email)."""
    name = (raw.get("name", "") or raw.get("n", "")).strip()
    phone = normalize_phone(raw.get("phone", "") or raw.get("p", ""))
    email = (raw.get("email", "") or raw.get("e", "")).strip().lower()
    return {"name": name, "phone": phone, "email": email}


def normalize_contractor(raw: dict) -> dict:
    """Normalize contractor info with business name parsing."""
    name_raw = raw.get("name", "") or raw.get("n", "")
    clean_name, entity_type = normalize_business_name(name_raw)
    phone = normalize_phone(raw.get("phone", "") or raw.get("p", ""))
    license_num = (raw.get("license_number", "") or raw.get("lic", "")).strip()
    return {
        "name": clean_name,
        "entity_type": entity_type,
        "phone": phone,
        "license_number": license_num,
    }


def normalize_permit_type(raw: str) -> str:
    """Map raw permit type string to standard enum."""
    if not raw:
        return "OTHER"
    lower = raw.strip().lower()
    for keyword, standard in PERMIT_TYPE_ALIASES.items():
        if keyword in lower:
            return standard
    return "OTHER"


def normalize_permit_record(record: dict) -> dict:
    """Fully normalize a raw permit record."""
    address = normalize_address(record.get("address", {}))
    owner = normalize_contact(record.get("owner", {}))
    contractor = normalize_contractor(record.get("contractor", {}))

    return {
        **record,
        "address": address,
        "owner": owner,
        "contractor": contractor,
        "permit_type": normalize_permit_type(record.get("permit_type", "")),
        "work_description": (record.get("work_description", "") or "").strip(),
    }


def normalize_bid_record(record: dict) -> dict:
    """Normalize a bid record."""
    contacts = []
    for c in record.get("contacts", []):
        contacts.append(normalize_contact(c))

    location = record.get("location", {})
    return {
        **record,
        "contacts": contacts,
        "location": {
            "state": (location.get("state", "") or "").strip().upper(),
            "city": (location.get("city", "") or "").strip().title(),
            "zip_code": _clean_zip(location.get("zip_code", "")),
        },
        "title": (record.get("title", "") or "").strip(),
        "description": (record.get("description", "") or "").strip(),
    }


def _clean_zip(raw: str) -> str:
    """Clean a zip code to 5-digit format."""
    if not raw:
        return ""
    cleaned = str(raw).strip().split("-")[0]
    return cleaned[:5] if cleaned.isdigit() else ""
