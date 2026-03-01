from __future__ import annotations

from functools import lru_cache

from shared.clients.firestore_client import FirestoreClient
from shared.config import Settings

from .cache import TTLCache


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_firestore() -> FirestoreClient:
    settings = get_settings()
    return FirestoreClient.get_instance(settings.firestore_project_id)


@lru_cache
def get_cache() -> TTLCache:
    return TTLCache(ttl_seconds=3600)
