from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from ..dependencies import get_firestore

router = APIRouter(prefix="/api/contractors", tags=["contractors"])


@router.get("")
def list_contractors(
    trade: str | None = None,
    state: str | None = None,
    license_status: str | None = None,
    limit: int = Query(default=20, le=100),
    offset: int = 0,
    db: Any = Depends(get_firestore),
) -> list[dict]:
    """Browse/search contractor database."""
    query = db.contractors()

    if trade:
        query = query.where("trades", "array_contains", trade)

    docs = query.limit(limit + offset + 100).stream()
    results = []

    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id

        # In-memory filters
        if state:
            addr = (data.get("addr", "") or "").upper()
            licenses = data.get("licenses", [])
            state_match = state.upper() in addr or any(
                lic.get("state", "").upper() == state.upper() for lic in licenses
            )
            if not state_match:
                continue

        if license_status:
            licenses = data.get("licenses", [])
            status_match = any(
                lic.get("status", "").upper() == license_status.upper()
                for lic in licenses
            )
            if not status_match:
                continue

        results.append(data)

    return results[offset: offset + limit]


@router.get("/{contractor_id}")
def get_contractor(
    contractor_id: str,
    db: Any = Depends(get_firestore),
) -> dict:
    """Get full contractor profile with permit history."""
    doc = db.contractors().document(contractor_id).get()
    if not doc.exists:
        return {"error": "Contractor not found"}

    data = doc.to_dict()
    data["id"] = doc.id

    # Fetch recent leads associated with this contractor
    name = data.get("name", "")
    if name:
        lead_docs = (
            db.leads()
            .where("gc.n", "==", name)
            .limit(20)
            .stream()
        )
        data["recent_leads"] = [
            {**ld.to_dict(), "id": ld.id} for ld in lead_docs
        ]
    else:
        data["recent_leads"] = []

    return data
