from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from shared.utils import generate_id

from ..dependencies import get_firestore

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


class AlertCreate(BaseModel):
    email: str
    trade: str | None = None
    state: str | None = None
    city: str | None = None
    min_value: float | None = None
    max_value: float | None = None


@router.post("")
def create_alert(
    alert: AlertCreate,
    db: Any = Depends(get_firestore),
) -> dict:
    """Create an email alert for new leads matching criteria."""
    alert_id = generate_id(alert.email, alert.trade or "", alert.state or "")
    alert_data = {
        "id": alert_id,
        "email": alert.email,
        "trade": alert.trade,
        "state": alert.state,
        "city": alert.city,
        "min_value": alert.min_value,
        "max_value": alert.max_value,
        "created": datetime.utcnow().isoformat(),
        "active": True,
    }
    db.alerts().document(alert_id).set(alert_data)
    return {"id": alert_id, "status": "created"}


@router.get("")
def list_alerts(
    email: str | None = None,
    db: Any = Depends(get_firestore),
) -> list[dict]:
    """List all alerts, optionally filtered by email."""
    query = db.alerts()
    if email:
        query = query.where("email", "==", email)

    docs = query.limit(100).stream()
    return [{**doc.to_dict(), "id": doc.id} for doc in docs]


@router.delete("/{alert_id}")
def delete_alert(
    alert_id: str,
    db: Any = Depends(get_firestore),
) -> dict:
    """Delete an alert."""
    db.alerts().document(alert_id).delete()
    return {"id": alert_id, "status": "deleted"}
