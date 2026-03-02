from __future__ import annotations

import csv
import io
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from google.cloud.firestore_v1.base_query import FieldFilter

from ..dependencies import get_cache, get_firestore

router = APIRouter(prefix="/api/leads", tags=["leads"])


def _apply_filters(
    docs: Any,
    state: str | None,
    city: str | None,
    zip_code: str | None,
    min_value: float | None,
    max_value: float | None,
) -> list[dict]:
    """Stream Firestore docs and apply in-memory filters. Returns list of dicts."""
    results = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        addr = (data.get("addr") or "").upper()
        if state and state.upper() not in addr:
            continue
        if city and city.lower() not in (data.get("addr") or "").lower():
            continue
        if zip_code and zip_code not in (data.get("addr") or ""):
            continue
        if min_value and (data.get("value") or 0) < min_value:
            continue
        if max_value and (data.get("value") or 0) > max_value:
            continue
        results.append(data)
    return results


def _sort_results(results: list[dict], sort_by: str) -> list[dict]:
    if sort_by == "score":
        return sorted(results, key=lambda x: x.get("score", 0), reverse=True)
    if sort_by == "value":
        return sorted(results, key=lambda x: x.get("value", 0) or 0, reverse=True)
    if sort_by == "date":
        return sorted(results, key=lambda x: x.get("posted") or "", reverse=True)
    return results


@router.get("")
def list_leads(
    q: str | None = None,
    trade: str | None = None,
    src: str | None = None,
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
) -> dict:
    """List leads with optional filters. Returns paginated envelope with total count."""
    cache_key = f"leads:{q}:{trade}:{src}:{state}:{city}:{zip_code}:{min_value}:{max_value}:{status}:{sort_by}"
    cached = cache.get(cache_key)

    if cached is None:
        query = db.leads()
        if trade:
            query = query.where(filter=FieldFilter("trade", "==", trade))
        if status:
            query = query.where(filter=FieldFilter("status", "==", status))

        # Fetch enough docs to support deep pagination + filtering headroom
        fetch_limit = max(5000, offset + limit + 500)
        docs = query.limit(fetch_limit).stream()
        results = _apply_filters(docs, state, city, zip_code, min_value, max_value)

        # src filter (portal prefix e.g. "chicago", "los-angeles")
        if src:
            results = [r for r in results if r.get("src", "").startswith(src)]

        # full-text search on title + addr + work_description
        if q:
            ql = q.lower()
            results = [r for r in results if
                       ql in (r.get("title") or "").lower() or
                       ql in (r.get("addr") or "").lower() or
                       ql in (r.get("work_description") or "").lower()]

        results = _sort_results(results, sort_by)
        cache.set(cache_key, results)
    else:
        results = cached

    total = len(results)
    page = results[offset: offset + limit]
    return {
        "data": page,
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": offset + limit < total,
    }


@router.get("/export")
def export_leads_csv(
    trade: str | None = None,
    state: str | None = None,
    city: str | None = None,
    zip_code: str | None = Query(None, alias="zip"),
    min_value: float | None = None,
    max_value: float | None = None,
    status: str | None = None,
    db: Any = Depends(get_firestore),
) -> StreamingResponse:
    """Export all matching leads as a CSV file (max 5,000 rows)."""
    query = db.leads()
    if trade:
        query = query.where(filter=FieldFilter("trade", "==", trade))
    if status:
        query = query.where(filter=FieldFilter("status", "==", status))

    docs = query.limit(5000).stream()
    results = _apply_filters(docs, state, city, zip_code, min_value, max_value)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "type", "trade", "title", "value", "address",
        "owner_name", "owner_phone", "owner_email",
        "contractor_name", "contractor_phone", "contractor_license",
        "status", "posted_date", "deadline", "source", "score",
    ])
    for lead in results:
        owner = lead.get("owner") or {}
        gc = lead.get("gc") or {}
        writer.writerow([
            lead.get("id", ""),
            lead.get("type", ""),
            lead.get("trade", ""),
            lead.get("title", ""),
            lead.get("value", ""),
            lead.get("addr", ""),
            owner.get("n", ""),
            owner.get("p", ""),
            owner.get("e", ""),
            gc.get("n", ""),
            gc.get("p", ""),
            gc.get("lic", ""),
            lead.get("status", ""),
            lead.get("posted", ""),
            lead.get("deadline", ""),
            lead.get("src", ""),
            lead.get("score", ""),
        ])

    output.seek(0)
    filename = f"leads-export-{trade or 'all'}-{state or 'all'}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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
