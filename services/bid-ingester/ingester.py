from __future__ import annotations

from datetime import datetime
from typing import Any

from shared.clients.firestore_client import FirestoreClient
from shared.clients.storage_client import StorageClient
from shared.config import Settings
from shared.logging_config import get_logger

from .census_client import CensusClient
from .sam_client import SamGovClient
from .usaspending_client import USASpendingClient

logger = get_logger(__name__)


async def run_bid_ingestion(mode: str = "incremental") -> dict[str, Any]:
    """Run bid ingestion from SAM.gov, USASpending, and Census."""
    settings = Settings()
    storage = StorageClient(
        backend=settings.storage_backend,
        local_path=settings.local_storage_path,
        bucket_name=settings.gcs_bucket_name,
    )
    firestore = FirestoreClient.get_instance(settings.firestore_project_id)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    results: dict[str, Any] = {}

    # 1. SAM.gov opportunities
    sam_count = 0
    if settings.sam_gov_api_key:
        sam_client = SamGovClient(settings.sam_gov_api_key)
        try:
            bids = await sam_client.fetch_construction_opportunities(
                days_back=7 if mode == "incremental" else 30
            )
            if bids:
                storage_path = f"bids/{today}/sam-gov.jsonl"
                records = [b.model_dump(mode="json") for b in bids]
                storage.write_jsonl(storage_path, records)
                sam_count = len(bids)
                logger.info("sam_bids_stored", count=sam_count, path=storage_path)
        except Exception as e:
            logger.error("sam_ingestion_failed", error=str(e))
        finally:
            await sam_client.close()
    results["sam_gov"] = sam_count

    # 2. USASpending awards
    usa_count = 0
    usa_client = USASpendingClient()
    try:
        awards = await usa_client.fetch_construction_awards(
            days_back=7 if mode == "incremental" else 30
        )
        if awards:
            storage_path = f"bids/{today}/usaspending.jsonl"
            records = [a.model_dump(mode="json") for a in awards]
            storage.write_jsonl(storage_path, records)
            usa_count = len(awards)
            logger.info("usaspending_stored", count=usa_count, path=storage_path)
    except Exception as e:
        logger.error("usaspending_ingestion_failed", error=str(e))
    finally:
        await usa_client.close()
    results["usaspending"] = usa_count

    # 3. Census Building Permits Survey (monthly context)
    census_count = 0
    if settings.census_api_key:
        census_client = CensusClient(settings.census_api_key)
        try:
            market_data = await census_client.get_hot_markets()
            if market_data:
                storage_path = f"census/{today}/hot-markets.jsonl"
                storage.write_jsonl(storage_path, market_data)
                census_count = len(market_data)
        except Exception as e:
            logger.error("census_ingestion_failed", error=str(e))
        finally:
            await census_client.close()
    results["census"] = census_count

    # Update ingestion state
    firestore.update_ingestion_state("bid-ingester", {
        "source_id": "bid-ingester",
        "last_run": datetime.utcnow(),
        "last_record_date": today,
        "records_ingested": sam_count + usa_count,
        "errors": 0,
    })

    total = sam_count + usa_count + census_count
    logger.info("bid_ingestion_complete", mode=mode, total=total, results=results)
    return {"mode": mode, "total": total, "results": results}
