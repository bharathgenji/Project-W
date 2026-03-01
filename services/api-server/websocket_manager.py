"""WebSocket connection manager for real-time lead alerts."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import WebSocket
from google.cloud.firestore_v1.base_query import FieldFilter

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections keyed by user email."""

    def __init__(self) -> None:
        self.connections: dict[str, WebSocket] = {}

    async def connect(self, email: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections[email] = websocket
        logger.info("ws_connected", extra={"email": email, "total": len(self.connections)})

    def disconnect(self, email: str) -> None:
        self.connections.pop(email, None)
        logger.info("ws_disconnected", extra={"email": email})

    async def send(self, email: str, payload: dict[str, Any]) -> None:
        ws = self.connections.get(email)
        if ws:
            try:
                await ws.send_json(payload)
            except Exception as exc:
                logger.warning("ws_send_failed", extra={"email": email, "error": str(exc)})
                self.disconnect(email)

    async def broadcast_new_lead(self, lead: dict[str, Any], db: Any) -> None:
        """Notify all connected users whose alerts match this lead."""
        if not self.connections:
            return  # no one online, skip DB query

        try:
            alert_docs = (
                db.alerts()
                .where(filter=FieldFilter("active", "==", True))
                .limit(500)
                .stream()
            )
            for doc in alert_docs:
                alert = doc.to_dict()
                if alert.get("email") in self.connections and self._matches(lead, alert):
                    await self.send(alert["email"], {"type": "new_lead", "lead": lead})
        except Exception as exc:
            logger.warning("broadcast_failed", extra={"error": str(exc)})

    @staticmethod
    def _matches(lead: dict[str, Any], alert: dict[str, Any]) -> bool:
        """Return True if a lead satisfies an alert's filter criteria."""
        if alert.get("trade") and alert["trade"] != lead.get("trade"):
            return False
        if alert.get("state"):
            addr = (lead.get("addr") or "").upper()
            if alert["state"].upper() not in addr:
                return False
        if alert.get("city"):
            addr = (lead.get("addr") or "").lower()
            if alert["city"].lower() not in addr:
                return False
        if alert.get("min_value") and (lead.get("value") or 0) < alert["min_value"]:
            return False
        if alert.get("max_value") and (lead.get("value") or 0) > alert["max_value"]:
            return False
        return True


# Singleton — shared across the FastAPI app
manager = ConnectionManager()
