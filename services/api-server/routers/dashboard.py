from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone, timedelta
from typing import Any

from fastapi import APIRouter, Depends

from ..dependencies import get_cache, get_firestore

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def dashboard_stats(
    db: Any = Depends(get_firestore),
    cache: Any = Depends(get_cache),
) -> dict:
    """Dashboard statistics: totals, by trade/state/value, new today/week, hot markets."""
    cached = cache.get("dashboard_stats")
    if cached is not None:
        return cached  # type: ignore[return-value]

    stats: dict[str, Any] = {
        "total_leads": 0,
        "total_contractors": 0,
        "total_value": 0,
        "avg_score": 0,
        "new_today": 0,
        "new_this_week": 0,
        "by_trade": {},
        "by_type": {"permit": 0, "bid": 0},
        "by_value_range": {"under_50k": 0, "50k_200k": 0, "over_200k": 0},
        "hot_markets": [],
    }
    score_sum = 0

    # Use naive UTC datetimes for comparison (stored posted values are naive ISO strings)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)

    trade_counter: Counter[str] = Counter()
    city_counter: Counter[str] = Counter()

    # Aggregate lead stats
    lead_docs = db.leads().limit(5000).stream()
    for doc in lead_docs:
        data = doc.to_dict()
        stats["total_leads"] += 1

        # By type
        lead_type = data.get("type", "permit")
        stats["by_type"][lead_type] = stats["by_type"].get(lead_type, 0) + 1

        # By trade
        trade = data.get("trade", "UNKNOWN")
        trade_counter[trade] += 1

        # Total value + score
        value = data.get("value") or 0
        stats["total_value"] += value
        score_sum += data.get("score") or 0

        # By value
        if value >= 200_000:
            stats["by_value_range"]["over_200k"] += 1
        elif value >= 50_000:
            stats["by_value_range"]["50k_200k"] += 1
        else:
            stats["by_value_range"]["under_50k"] += 1

        # Recency
        posted = data.get("posted")
        if posted:
            if isinstance(posted, str):
                try:
                    posted = datetime.fromisoformat(posted.replace("Z", "+00:00"))
                except ValueError:
                    posted = None
            if isinstance(posted, datetime):
                posted_naive = posted.replace(tzinfo=None) if posted.tzinfo else posted
                if posted_naive >= today_start:
                    stats["new_today"] += 1
                if posted_naive >= week_start:
                    stats["new_this_week"] += 1

        # City for hot markets — map src portal prefix to real city name
        _PORTAL_CITY = {
            "chicago": "Chicago, IL",
            "austin": "Austin, TX",
            "sf": "San Francisco, CA",
            "nyc": "New York City, NY",
            "san-diego": "San Diego, CA",
            "usaspending": "Federal (Various)",
            "sam": "Federal (Various)",
        }
        src = data.get("src", "")
        city = ""
        for portal_key, city_name in _PORTAL_CITY.items():
            if src.startswith(portal_key):
                city = city_name
                break
        if not city:
            # Fallback: try addr parsing
            addr = data.get("addr", "")
            if addr:
                parts = [p.strip() for p in addr.split(",")]
                if len(parts) >= 3:
                    city = parts[1]
                elif len(parts) == 2:
                    city = parts[0]
        if city:
            city_counter[city] += 1

    stats["by_trade"] = dict(trade_counter.most_common(15))
    if stats["total_leads"]:
        stats["avg_score"] = round(score_sum / stats["total_leads"])
    stats["hot_markets"] = [
        {"city": city, "count": count}
        for city, count in city_counter.most_common(10)
    ]

    # Count contractors
    contractor_docs = db.contractors().limit(5000).stream()
    for _ in contractor_docs:
        stats["total_contractors"] += 1

    cache.set("dashboard_stats", stats)
    return stats
