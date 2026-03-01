from __future__ import annotations

from shared.constants import NAICS_TO_TRADE, TRADE_KEYWORDS


def classify_trade(description: str, naics_code: str = "") -> tuple[str, float]:
    """Classify a construction trade from work description text.

    Returns (trade_name, confidence_score) where confidence is 0.0 to 1.0.
    """
    # If NAICS code is provided, use direct mapping
    if naics_code and naics_code in NAICS_TO_TRADE:
        return (NAICS_TO_TRADE[naics_code], 0.95)

    if not description:
        return ("UNKNOWN", 0.0)

    lower = description.lower()
    scores: dict[str, int] = {}

    for trade, keywords in TRADE_KEYWORDS.items():
        count = 0
        for keyword in keywords:
            if keyword in lower:
                count += 1
        if count > 0:
            scores[trade] = count

    if not scores:
        return ("UNKNOWN", 0.0)

    # Find the trade with the most keyword matches
    best_trade = max(scores, key=scores.get)  # type: ignore[arg-type]
    best_count = scores[best_trade]
    total_keywords = len(TRADE_KEYWORDS[best_trade])

    # Confidence: ratio of matched keywords to total, capped at 1.0
    confidence = min(best_count / max(total_keywords * 0.3, 1), 1.0)

    return (best_trade, round(confidence, 2))
