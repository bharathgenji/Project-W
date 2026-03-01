from __future__ import annotations

from collections import Counter
from typing import Any

from fastapi import APIRouter, Depends

from ..dependencies import get_cache, get_firestore

router = APIRouter(prefix="/api/markets", tags=["markets"])


@router.get("/{state}")
def market_overview(
    state: str,
    db: Any = Depends(get_firestore),
    cache: Any = Depends(get_cache),
) -> dict:
    """Market overview for a state: permit trends, top contractors, avg values."""
    state_upper = state.upper()
    cache_key = f"market:{state_upper}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached  # type: ignore[return-value]

    stats: dict[str, Any] = {
        "state": state_upper,
        "total_leads": 0,
        "avg_value": 0,
        "top_contractors": [],
        "trade_breakdown": {},
    }

    values: list[float] = []
    trade_counter: Counter[str] = Counter()
    contractor_counter: Counter[str] = Counter()

    # Query leads in this state
    lead_docs = db.leads().limit(5000).stream()
    for doc in lead_docs:
        data = doc.to_dict()
        addr = (data.get("addr", "") or "").upper()
        if f", {state_upper}" not in addr and f" {state_upper} " not in addr:
            continue

        stats["total_leads"] += 1
        value = data.get("value") or 0
        if value:
            values.append(float(value))

        trade = data.get("trade", "UNKNOWN")
        trade_counter[trade] += 1

        gc_name = data.get("gc", {}).get("n", "")
        if gc_name:
            contractor_counter[gc_name] += 1

    if values:
        stats["avg_value"] = round(sum(values) / len(values), 2)

    stats["trade_breakdown"] = dict(trade_counter.most_common(10))
    stats["top_contractors"] = [
        {"name": name, "permits": count}
        for name, count in contractor_counter.most_common(10)
    ]

    cache.set(cache_key, stats)
    return stats
