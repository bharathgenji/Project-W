"""Lead pipeline CRM — save, track, and annotate leads per user (email-keyed pre-auth)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from google.cloud.firestore_v1.base_query import FieldFilter
from pydantic import BaseModel, EmailStr

from shared.utils import generate_id

from ..dependencies import get_firestore

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])

VALID_STATUSES = {"NEW", "CONTACTED", "PROPOSAL_SENT", "WON", "LOST", "SKIP"}


def _pipeline_id(user_email: str, lead_id: str) -> str:
    return generate_id(user_email.lower(), lead_id)


# ─── Request models ────────────────────────────────────────────────────────────

class SaveLeadRequest(BaseModel):
    user_email: str
    notes: str = ""


class UpdateLeadRequest(BaseModel):
    user_email: str
    status: str | None = None
    notes: str | None = None


class AddNoteRequest(BaseModel):
    user_email: str
    note: str


# ─── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/leads/{lead_id}/save")
def save_lead(
    lead_id: str,
    body: SaveLeadRequest,
    db: Any = Depends(get_firestore),
) -> dict:
    """Bookmark a lead into the user's pipeline with status=NEW."""
    now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    doc_id = _pipeline_id(body.user_email, lead_id)

    # Check if lead exists
    lead_doc = db.leads().document(lead_id).get()
    if not lead_doc.exists:
        raise HTTPException(status_code=404, detail="Lead not found")

    data: dict[str, Any] = {
        "id": doc_id,
        "user_email": body.user_email.lower(),
        "lead_id": lead_id,
        "status": "NEW",
        "notes": [{"text": body.notes, "created": now}] if body.notes else [],
        "saved_at": now,
        "updated_at": now,
    }
    db.pipeline().document(doc_id).set(data)
    return {"id": doc_id, "status": "NEW", "saved": True}


@router.patch("/leads/{lead_id}")
def update_pipeline_lead(
    lead_id: str,
    body: UpdateLeadRequest,
    db: Any = Depends(get_firestore),
) -> dict:
    """Update status or append a note on a pipeline item."""
    doc_id = _pipeline_id(body.user_email, lead_id)
    doc_ref = db.pipeline().document(doc_id)
    doc = doc_ref.get()

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Lead not in your pipeline")

    now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    updates: dict[str, Any] = {"updated_at": now}

    if body.status:
        status = body.status.upper()
        if status not in VALID_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(sorted(VALID_STATUSES))}",
            )
        updates["status"] = status

    if body.notes is not None:
        current = doc.to_dict() or {}
        existing_notes: list = current.get("notes", [])
        existing_notes.append({"text": body.notes, "created": now})
        updates["notes"] = existing_notes

    doc_ref.update(updates)
    result = doc_ref.get().to_dict() or {}
    result["id"] = doc_id
    return result


@router.post("/leads/{lead_id}/notes")
def add_note(
    lead_id: str,
    body: AddNoteRequest,
    db: Any = Depends(get_firestore),
) -> dict:
    """Append a timestamped note to a pipeline item."""
    doc_id = _pipeline_id(body.user_email, lead_id)
    doc_ref = db.pipeline().document(doc_id)
    doc = doc_ref.get()

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Lead not in your pipeline. Save it first.")

    now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    current = doc.to_dict() or {}
    notes: list = current.get("notes", [])
    new_note = {"text": body.note, "created": now}
    notes.append(new_note)

    doc_ref.update({"notes": notes, "updated_at": now})
    return {"id": doc_id, "note": new_note, "total_notes": len(notes)}


@router.get("")
def get_pipeline(
    email: str = Query(..., description="User email"),
    db: Any = Depends(get_firestore),
) -> list[dict]:
    """Get all pipeline items for a user, with full lead data joined."""
    pipeline_docs = (
        db.pipeline()
        .where(filter=FieldFilter("user_email", "==", email.lower()))
        .order_by("updated_at", direction="DESCENDING")
        .limit(200)
        .stream()
    )

    items = []
    for doc in pipeline_docs:
        item = doc.to_dict() or {}
        item["id"] = doc.id

        # Join full lead data
        lead_id = item.get("lead_id", "")
        if lead_id:
            lead_doc = db.leads().document(lead_id).get()
            if lead_doc.exists:
                item["lead"] = {**(lead_doc.to_dict() or {}), "id": lead_doc.id}
            else:
                item["lead"] = None  # lead may have been purged

        items.append(item)

    return items


@router.delete("/leads/{lead_id}")
def remove_from_pipeline(
    lead_id: str,
    email: str = Query(...),
    db: Any = Depends(get_firestore),
) -> dict:
    """Remove a lead from the user's pipeline."""
    doc_id = _pipeline_id(email, lead_id)
    db.pipeline().document(doc_id).delete()
    return {"id": doc_id, "status": "removed"}
