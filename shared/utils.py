from __future__ import annotations

import hashlib
import re

import phonenumbers


def normalize_phone(raw: str) -> str:
    """Normalize phone number to E.164 format. Returns empty string if invalid."""
    if not raw or not raw.strip():
        return ""
    cleaned = re.sub(r"[^\d+]", "", raw.strip())
    if not cleaned:
        return ""
    try:
        parsed = phonenumbers.parse(cleaned, "US")
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        pass
    return ""


STREET_ABBREVIATIONS: dict[str, str] = {
    "street": "St",
    "avenue": "Ave",
    "boulevard": "Blvd",
    "drive": "Dr",
    "lane": "Ln",
    "road": "Rd",
    "court": "Ct",
    "place": "Pl",
    "circle": "Cir",
    "terrace": "Ter",
    "highway": "Hwy",
    "parkway": "Pkwy",
    "way": "Way",
    "north": "N",
    "south": "S",
    "east": "E",
    "west": "W",
    "northeast": "NE",
    "northwest": "NW",
    "southeast": "SE",
    "southwest": "SW",
    "apartment": "Apt",
    "suite": "Ste",
    "unit": "Unit",
    "building": "Bldg",
    "floor": "Fl",
}


def normalize_address_street(raw: str) -> str:
    """Standardize street address to USPS-like format."""
    if not raw or not raw.strip():
        return ""
    parts = raw.strip().split()
    result = []
    for part in parts:
        lower = part.lower().rstrip(".,")
        if lower in STREET_ABBREVIATIONS:
            result.append(STREET_ABBREVIATIONS[lower])
        else:
            result.append(part.strip(".,").title())
    return " ".join(result)


def normalize_business_name(raw: str) -> tuple[str, str]:
    """Parse business name into (clean_name, entity_type).

    Example: "SMITH PLUMBING LLC" -> ("Smith Plumbing", "LLC")
    """
    if not raw or not raw.strip():
        return ("", "")
    entity_types = ["LLC", "INC", "CORP", "CO", "LTD", "LP", "LLP", "PC", "PLLC", "DBA"]
    cleaned = raw.strip()
    entity_type = ""
    upper = cleaned.upper()
    for et in entity_types:
        patterns = [f" {et}.", f" {et}", f", {et}.", f", {et}"]
        for pattern in patterns:
            if upper.endswith(pattern):
                entity_type = et
                cleaned = cleaned[: -len(pattern)].strip().rstrip(",").strip()
                break
        if entity_type:
            break
    cleaned = cleaned.title()
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return (cleaned, entity_type)


def generate_id(*parts: str) -> str:
    """Generate a deterministic SHA256 hash ID from parts."""
    combined = "|".join(str(p).strip().lower() for p in parts if p)
    return hashlib.sha256(combined.encode()).hexdigest()[:24]


def clean_text(raw: str) -> str:
    """Clean and normalize text: strip, collapse whitespace."""
    if not raw:
        return ""
    return re.sub(r"\s+", " ", raw.strip())


def extract_keywords(text: str) -> list[str]:
    """Extract searchable keywords from text for Firestore array-contains queries."""
    if not text:
        return []
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return list(set(w for w in words if len(w) >= 3))
