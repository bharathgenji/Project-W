from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
import yaml

from shared.clients.firestore_client import FirestoreClient
from shared.clients.storage_client import StorageClient
from shared.config import Settings
from shared.logging_config import get_logger
from shared.models.permit import PermitRecord

from .field_mapper import map_to_permit
from .socrata_client import SocrataClient

logger = get_logger(__name__)


def load_sources() -> list[dict[str, Any]]:
    """Load portal configurations from sources.yaml."""
    sources_path = Path(__file__).parent / "sources.yaml"
    with open(sources_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config.get("portals", [])


async def ingest_portal(
    portal: dict[str, Any],
    socrata: SocrataClient,
    storage: StorageClient,
    firestore: FirestoreClient,
    settings: Settings,
) -> int:
    """Ingest permits from a single Socrata portal. Returns count of records ingested."""
    portal_id = portal["id"]
    domain = portal["domain"]
    dataset_id = portal["dataset_id"]
    field_map = portal.get("field_map", {})
    portal_state = portal.get("state", "")

    # Get last run date
    last_run_info = firestore.get_last_run(portal_id)
    where_clause = None
    if last_run_info and last_run_info.get("last_record_date"):
        last_date = last_run_info["last_record_date"]
        # Try common date field names
        date_field = field_map.get("issued_date") or field_map.get("filed_date")
        if date_field:
            where_clause = f"{date_field} > '{last_date}'"

    try:
        raw_records = await socrata.fetch_all(
            domain=domain,
            dataset_id=dataset_id,
            where_clause=where_clause,
            max_records=5000,
        )
    except httpx.HTTPStatusError as e:
        logger.error("socrata_fetch_failed", portal=portal_id, status=e.response.status_code)
        firestore.update_ingestion_state(portal_id, {
            "source_id": portal_id,
            "last_run": datetime.utcnow(),
            "errors": (last_run_info or {}).get("errors", 0) + 1,
        })
        return 0

    if not raw_records:
        logger.info("no_new_records", portal=portal_id)
        return 0

    # Map to standard schema
    permits: list[PermitRecord] = []
    for row in raw_records:
        try:
            permit = map_to_permit(row, portal_id, field_map, portal_state)
            permits.append(permit)
        except Exception as e:
            logger.warning("field_mapping_error", portal=portal_id, error=str(e))

    # Write to storage
    today = datetime.utcnow().strftime("%Y-%m-%d")
    storage_path = f"permits/{today}/{portal_id}.jsonl"
    records_dicts = [p.model_dump(mode="json") for p in permits]
    storage.write_jsonl(storage_path, records_dicts)

    logger.info("permits_stored", portal=portal_id, count=len(permits), path=storage_path)

    # Trigger ETL pipeline
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{settings.etl_pipeline_url}/process",
                json={"source_type": "permit", "storage_path": storage_path},
            )
    except Exception as e:
        logger.warning("etl_trigger_failed", error=str(e))

    # Update ingestion state
    firestore.update_ingestion_state(portal_id, {
        "source_id": portal_id,
        "last_run": datetime.utcnow(),
        "last_record_date": today,
        "records_ingested": len(permits),
        "errors": 0,
    })

    return len(permits)


async def run_ingestion(mode: str = "incremental") -> dict[str, Any]:
    """Run permit ingestion across all configured Socrata portals."""
    settings = Settings()
    socrata = SocrataClient()
    storage = StorageClient(
        backend=settings.storage_backend,
        local_path=settings.local_storage_path,
        bucket_name=settings.gcs_bucket_name,
    )
    firestore = FirestoreClient.get_instance(settings.firestore_project_id)

    portals = load_sources()
    total_ingested = 0
    errors = 0
    results: dict[str, int] = {}

    for portal in portals:
        try:
            count = await ingest_portal(portal, socrata, storage, firestore, settings)
            results[portal["id"]] = count
            total_ingested += count
        except Exception as e:
            logger.error("portal_ingestion_failed", portal=portal["id"], error=str(e))
            errors += 1
            results[portal["id"]] = -1

    await socrata.close()

    logger.info(
        "ingestion_complete",
        mode=mode,
        total_portals=len(portals),
        total_ingested=total_ingested,
        errors=errors,
    )

    return {
        "mode": mode,
        "total_portals": len(portals),
        "total_ingested": total_ingested,
        "errors": errors,
        "results": results,
    }
