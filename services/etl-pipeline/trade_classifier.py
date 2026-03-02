from __future__ import annotations

import re

from shared.constants import NAICS_TO_TRADE, TRADE_KEYWORDS

# Permit-type → trade fallback (when description alone doesn't resolve)
_PERMIT_TYPE_TRADE: dict[str, str] = {
    "building":      "GENERAL",
    "residential":   "GENERAL",
    "commercial":    "GENERAL",
    "electrical":    "ELECTRICAL",
    "plumbing":      "PLUMBING",
    "mechanical":    "HVAC",
    "hvac":          "HVAC",
    "roofing":       "ROOFING",
    "demolition":    "DEMOLITION",
    "fire":          "FIRE_PROTECTION",
    "sprinkler":     "FIRE_PROTECTION",
    "solar":         "ELECTRICAL",
    "sign":          "SIGNAGE",
    "grading":       "SITE_WORK",
    "excavation":    "SITE_WORK",
}


def _normalize(text: str) -> str:
    """Lowercase + replace hyphens/underscores with spaces for better keyword matching."""
    return re.sub(r"[-_/]", " ", text.lower())


def classify_trade(description: str, naics_code: str = "") -> tuple[str, float]:
    """Classify a construction trade from work description text.

    Returns (trade_name, confidence_score) where confidence is 0.0 to 1.0.
    """
    # If NAICS code is provided, use direct mapping
    if naics_code and naics_code in NAICS_TO_TRADE:
        return (NAICS_TO_TRADE[naics_code], 0.95)

    if not description:
        return ("UNKNOWN", 0.0)

    # Normalize: lowercase + treat hyphens/underscores as spaces so
    # "single-family" matches keyword "single family", "re-roof" matches "reroof" etc.
    lower = _normalize(description)
    # Pad with spaces so we can do simple whole-word boundary checks
    padded = f" {lower} "
    scores: dict[str, int] = {}

    for trade, keywords in TRADE_KEYWORDS.items():
        count = 0
        for keyword in keywords:
            kw = _normalize(keyword)
            # For short single-word keywords use regex word boundaries so that
            # "sign" doesn't match "signed" but "pipe" correctly matches "pipe"
            # (note: "pipes"/"piping" are in the keyword list explicitly)
            if " " not in kw and len(kw) <= 6:
                if re.search(r"\b" + re.escape(kw) + r"\b", lower):
                    count += 1
            else:
                if kw in lower:
                    count += 1
        if count > 0:
            scores[trade] = count

    if scores:
        best_trade = max(scores, key=scores.get)  # type: ignore[arg-type]
        best_count = scores[best_trade]
        total_keywords = len(TRADE_KEYWORDS[best_trade])
        confidence = min(best_count / max(total_keywords * 0.3, 1), 1.0)
        return (best_trade, round(confidence, 2))

    # Fallback: scan for permit-type clues in the description (word-boundary safe)
    for token, trade in _PERMIT_TYPE_TRADE.items():
        if re.search(r"\b" + re.escape(token) + r"\b", lower):
            return (trade, 0.3)

    # Last-resort: if the text has ANY construction-adjacent word, call it GENERAL
    _construction_signals = {"permit", "build", "work", "install", "repair", "replace",
                              "addition", "convert", "change", "modify", "construct"}
    if any(re.search(r"\b" + sig + r"\b", lower) for sig in _construction_signals):
        return ("GENERAL", 0.1)

    return ("UNKNOWN", 0.0)  # truly non-construction text
