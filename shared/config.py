from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Data source API keys
    sam_gov_api_key: str = ""
    census_api_key: str = ""

    # Firestore / GCP
    firestore_project_id: str = "leadgen-mvp-local"
    firestore_emulator_host: str | None = None
    google_cloud_project: str = "leadgen-mvp-local"
    google_application_credentials: str = ""

    # Storage
    storage_backend: str = "local"  # "local" | "gcs"
    local_storage_path: str = "./data/raw"
    gcs_bucket_name: str = "leadgen-mvp-raw-data"

    # Service URLs
    etl_pipeline_url: str = "http://localhost:8003"
    api_server_url: str = "http://localhost:8005"

    # Firebase Auth
    firebase_project_id: str = ""
    firebase_web_api_key: str = ""

    # AI Enrichment (Anthropic)
    anthropic_api_key: str = ""
    ai_enrichment_enabled: bool = False
    ai_enrichment_model: str = "claude-haiku-4-5"

    # Email (Resend)
    resend_api_key: str = ""
    email_from: str = "alerts@buildscope.app"

    # Maps
    google_maps_api_key: str = ""

    # App
    log_level: str = "INFO"
    environment: str = "development"

    @property
    def is_emulator(self) -> bool:
        return bool(self.firestore_emulator_host)

    @property
    def has_ai_enrichment(self) -> bool:
        return bool(self.anthropic_api_key) and self.ai_enrichment_enabled

    @property
    def has_email(self) -> bool:
        return bool(self.resend_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
