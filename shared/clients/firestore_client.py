from __future__ import annotations

import os
from typing import Any

from google.cloud import firestore  # type: ignore[attr-defined]


class FirestoreClient:
    _instance: FirestoreClient | None = None

    def __init__(self, project_id: str | None = None) -> None:
        emulator_host = os.environ.get("FIRESTORE_EMULATOR_HOST")
        if emulator_host:
            os.environ["FIRESTORE_EMULATOR_HOST"] = emulator_host
            self.db: firestore.Client = firestore.Client(
                project=project_id or "leadgen-mvp-local"
            )
        else:
            self.db = firestore.Client(project=project_id)

    @classmethod
    def get_instance(cls, project_id: str | None = None) -> FirestoreClient:
        if cls._instance is None:
            cls._instance = cls(project_id)
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset singleton (useful for testing)."""
        cls._instance = None

    def leads(self) -> firestore.CollectionReference:
        return self.db.collection("leads")

    def contractors(self) -> firestore.CollectionReference:
        return self.db.collection("contractors")

    def ingestion_state(self) -> firestore.CollectionReference:
        return self.db.collection("ingestion_state")

    def alerts(self) -> firestore.CollectionReference:
        return self.db.collection("alerts")

    def pipeline(self) -> firestore.CollectionReference:
        return self.db.collection("pipeline")

    def get_last_run(self, source_id: str) -> dict[str, Any] | None:
        doc = self.ingestion_state().document(source_id).get()
        if doc.exists:
            return doc.to_dict()  # type: ignore[return-value]
        return None

    def update_ingestion_state(self, source_id: str, data: dict[str, Any]) -> None:
        self.ingestion_state().document(source_id).set(data, merge=True)
