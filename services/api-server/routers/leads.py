from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from google.cloud.firestore_v1.base_query import FieldFilter

from ..dependencies import get_cache, get_firestore

router = APIRouter(prefix="/api/leads", tags=["leads"])


@router.get("")
def list_leads(
    trade: str | None = None,
    state: str | None = None,
    city: str | None = None,
    zip_code: str | None = Query(None, alias="zip"),
    min_value: float | None = None,
    max_value: float | None = None,
    posted_after: str | None = None,
    status: str | None = None,
    sort_by: str = "score",
    limit: int = Query(default=20, le=100),
    offset: int = 0,
    db: Any = Depends(get_firestore),
    cache: Any = Depends(get_cache),
) -> list[dict]:
    """List leads with optional filters."""
    cache_key = f"leads:{trade}:{state}:{city}:{min_value}:{max_value}:{sort_by}:{limit}:{offset}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached  # type: ignore[return-value]

    query = db.leads()

    if trade:
        query = query.where(filter=FieldFilter("trade", "==", trade))
    if status:
        query = query.where(filter=FieldFilter("status", "==", status))

    # Firestore compound queries are limited, so we do some filtering in-memory
    docs = query.limit(limit + offset).stream()
    results = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id

        # In-memory filters for fields Firestore can't compound-query efficiently
        if state and state.upper() not in (data.get("addr", "") or "").upper():
            continue
        if city and city.lower() not in (data.get("addr", "") or "").lower():
            continue
        if zip_code and zip_code not in (data.get("addr", "") or ""):
            continue
        if min_value and (data.get("value") or 0) < min_value:
            continue
        if max_value and (data.get("value") or 0) > max_value:
            continue

        results.append(data)

    # Sort
    if sort_by == "score":
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
    elif sort_by == "value":
        results.sort(key=lambda x: x.get("value", 0) or 0, reverse=True)
    elif sort_by == "date":
        results.sort(key=lambda x: x.get("posted", "") or "", reverse=True)

    # Paginate
    paginated = results[offset: offset + limit]
    cache.set(cache_key, paginated)
    return paginated


@router.get("/{lead_id}")
def get_lead(
    lead_id: str,
    db: Any = Depends(get_firestore),
) -> dict:
    """Get full details for a single lead."""
    doc = db.leads().document(lead_id).get()
    if not doc.exists:
        return {"error": "Lead not found"}
    data = doc.to_dict()
    data["id"] = doc.id
    return data
