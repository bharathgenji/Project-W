from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any


def score_lead(lead: dict[str, Any]) -> int:
    """Score a lead on a 0-100 scale based on multiple factors.

    Factors (redesigned for permit-heavy datasets with limited contact info):
    - Base:            5  (any valid construction lead)
    - Project value:   $0=0, $1-50K=8, $50-200K=18, $200K-1M=28, $1M+=35
    - Recency:         <7d=25, <30d=18, <60d=10, <90d=4
    - Trade known:     specific trade=12, GENERAL=4, UNKNOWN=0
    - Description:     has meaningful text=8
    - Contact:         name=5, phone=10, phone+email=15
    - No incumbent GC: 5  (open opportunity signal)
    """
    score = 5  # base — every real lead starts here

    # 1. Project value (max 35 points)
    value = lead.get("value") or lead.get("estimated_cost") or 0
    try:
        value = float(value)
    except (ValueError, TypeError):
        value = 0

    if value >= 1_000_000:
        score += 35
    elif value >= 200_000:
        score += 28
    elif value >= 50_000:
        score += 18
    elif value > 0:
        score += 8

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
                now = now.astimezone(posted.tzinfo)
            else:
                now = now.replace(tzinfo=None)
            age = now - posted
            if age <= timedelta(days=7):
                score += 25
            elif age <= timedelta(days=30):
                score += 18
            elif age <= timedelta(days=60):
                score += 10
            elif age <= timedelta(days=90):
                score += 4

    # 3. Trade specificity (max 12 points)
    trade = lead.get("trade", "UNKNOWN")
    if trade and trade not in ("UNKNOWN", "OTHER", ""):
        score += 12 if trade != "GENERAL" else 4

    # 4. Description quality (max 8 points)
    title = lead.get("title", "")
    description = lead.get("work_description", "")
    text = (title + " " + description).strip()
    # Has meaningful content beyond just the permit type prefix
    content = text.split(" - ", 1)[-1].strip() if " - " in text else text
    if len(content) > 30:
        score += 8
    elif len(content) > 10:
        score += 4

    # 5. Contact completeness (max 15 points)
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
        score += 15
    elif has_phone:
        score += 10
    elif has_name:
        score += 5

    # 6. Open opportunity (max 5 points)
    gc_name = gc.get("n") or gc.get("name") or ""
    if not gc_name:
        score += 5

    return min(score, 100)
