from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Keys
    sam_gov_api_key: str = ""
    census_api_key: str = ""

    # Firestore
    firestore_project_id: str = "leadgen-mvp-local"
    firestore_emulator_host: str | None = None
    google_cloud_project: str = "leadgen-mvp-local"

    # Storage
    storage_backend: str = "local"  # "local" or "gcs"
    local_storage_path: str = "./data/raw"
    gcs_bucket_name: str = "leadgen-mvp-raw-data"

    # Service URLs
    etl_pipeline_url: str = "http://localhost:8003"
    api_server_url: str = "http://localhost:8005"

    # App
    log_level: str = "INFO"
    environment: str = "development"

    @property
    def is_emulator(self) -> bool:
        return self.firestore_emulator_host is not None


def get_settings() -> Settings:
    return Settings()
