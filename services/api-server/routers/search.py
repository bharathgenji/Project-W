from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from google.cloud.firestore_v1.base_query import FieldFilter

from ..dependencies import get_firestore

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
def search(
    q: str = Query(..., min_length=2),
    limit: int = Query(default=20, le=100),
    db: Any = Depends(get_firestore),
) -> dict:
    """Full-text search across leads and contractors using keyword matching."""
    keywords = q.lower().split()
    results: dict[str, list[dict]] = {"leads": [], "contractors": []}

    # Search leads by keyword array-contains
    if keywords:
        primary_keyword = keywords[0]
        lead_docs = (
            db.leads()
            .where(filter=FieldFilter("keywords", "array_contains", primary_keyword))
            .limit(limit)
            .stream()
        )
        for doc in lead_docs:
            data = doc.to_dict()
            data["id"] = doc.id
            # Filter by additional keywords in-memory
            doc_keywords = set(data.get("keywords", []))
            if all(k in doc_keywords for k in keywords):
                results["leads"].append(data)

    # Search contractors by name (in-memory filter)
    contractor_docs = db.contractors().limit(200).stream()
    q_lower = q.lower()
    for doc in contractor_docs:
        data = doc.to_dict()
        name = (data.get("name", "") or "").lower()
        if q_lower in name:
            data["id"] = doc.id
            results["contractors"].append(data)
            if len(results["contractors"]) >= limit:
                break

    return results
