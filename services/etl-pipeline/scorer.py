from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any


def score_lead(lead: dict[str, Any]) -> int:
    """Score a lead on a 0-100 scale based on multiple factors.

    Factors:
    - Project value: $0-50K=10, $50-200K=20, $200K+=30
    - Recency: <7d=25, <30d=15, <90d=5
    - Contact completeness: phone+email=20, phone only=10, name only=5
    - Trade specificity: exact known trade=15, GENERAL=5
    - Competition: single/no contractor listed=10
    """
    score = 0

    # 1. Project value (max 30 points)
    value = lead.get("value") or lead.get("estimated_cost") or 0
    try:
        value = float(value)
    except (ValueError, TypeError):
        value = 0

    if value >= 200_000:
        score += 30
    elif value >= 50_000:
        score += 20
    elif value > 0:
        score += 10

    # 2. Recency (max 25 points)
    posted = lead.get("posted") or lead.get("issued_date") or lead.get("filed_date")
    if posted:
        if isinstance(posted, str):
            try:
                posted = datetime.fromisoformat(posted.replace("Z", "+00:00"))
            except ValueError:
                posted = None

        if isinstance(posted, datetime):
            now = datetime.now(timezone.utc)
            if posted.tzinfo:
                # posted is timezone-aware: align now to same tzinfo
                now = now.astimezone(posted.tzinfo)
            else:
                # posted is naive: strip tz from now to match
                now = now.replace(tzinfo=None)
            age = now - posted
            if age <= timedelta(days=7):
                score += 25
            elif age <= timedelta(days=30):
                score += 15
            elif age <= timedelta(days=90):
                score += 5

    # 3. Contact completeness (max 20 points)
    owner = lead.get("owner", {})
    gc = lead.get("gc", lead.get("contractor", {}))
    has_phone = bool(
        owner.get("p") or owner.get("phone") or gc.get("p") or gc.get("phone")
    )
    has_email = bool(
        owner.get("e") or owner.get("email") or gc.get("e") or gc.get("email")
    )
    has_name = bool(
        owner.get("n") or owner.get("name") or gc.get("n") or gc.get("name")
    )

    if has_phone and has_email:
        score += 20
    elif has_phone:
        score += 10
    elif has_name:
        score += 5

    # 4. Trade specificity (max 15 points)
    trade = lead.get("trade", "UNKNOWN")
    if trade and trade not in ("UNKNOWN", "OTHER"):
        if trade != "GENERAL":
            score += 15
        else:
            score += 5

    # 5. Competition (max 10 points)
    # Fewer contractors on a project = better opportunity
    gc_name = gc.get("n") or gc.get("name") or ""
    if not gc_name:
        score += 10  # No contractor listed = untapped opportunity

    return min(score, 100)
