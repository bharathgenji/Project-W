from __future__ import annotations

from datetime import datetime
from typing import Any

from shared.clients.firestore_client import FirestoreClient
from shared.clients.storage_client import StorageClient
from shared.config import Settings
from shared.logging_config import get_logger

from .base_scraper import BaseLicenseScraper
from .scrapers.arizona_roc import ArizonaROCScraper
from .scrapers.california_cslb import CaliforniaCSLBScraper
from .scrapers.florida_dbpr import FloridaDBPRScraper
from .scrapers.illinois_idfpr import IllinoisIDFPRScraper
from .scrapers.minnesota_dli import MinnesotaDLIScraper
from .scrapers.new_york_dob import NewYorkDOBScraper
from .scrapers.texas_tdlr import TexasTDLRScraper
from .scrapers.washington_lni import WashingtonLNIScraper

logger = get_logger(__name__)

# Rotating schedule: maps day_of_month (1-30) to scraper
SCRAPER_SCHEDULE: list[type[BaseLicenseScraper]] = [
    CaliforniaCSLBScraper,   # Day 1, 16
    TexasTDLRScraper,        # Day 2, 17
    FloridaDBPRScraper,      # Day 3, 18
    NewYorkDOBScraper,       # Day 4, 19
    IllinoisIDFPRScraper,    # Day 5, 20
    ArizonaROCScraper,       # Day 6, 21
    WashingtonLNIScraper,    # Day 7, 22
    MinnesotaDLIScraper,     # Day 8, 23
    # Additional scrapers can be added here
]


def get_scraper_for_day(day_of_month: int) -> BaseLicenseScraper:
    """Get the appropriate scraper based on day of month rotation."""
    index = (day_of_month - 1) % len(SCRAPER_SCHEDULE)
    scraper_class = SCRAPER_SCHEDULE[index]
    return scraper_class()


async def run_scrape(day_of_month: int | None = None) -> dict[str, Any]:
    """Run the license scraper for the scheduled state."""
    if day_of_month is None:
        day_of_month = datetime.utcnow().day

    settings = Settings()
    storage = StorageClient(
        backend=settings.storage_backend,
        local_path=settings.local_storage_path,
        bucket_name=settings.gcs_bucket_name,
    )
    firestore = FirestoreClient.get_instance(settings.firestore_project_id)
    today = datetime.utcnow().strftime("%Y-%m-%d")

    scraper = get_scraper_for_day(day_of_month)
    source_name = scraper.source_name

    logger.info("scrape_starting", source=source_name, day=day_of_month)

    try:
        licenses = await scraper.scrape_batch()

        if licenses:
            storage_path = f"licenses/{today}/{source_name.lower()}.jsonl"
            records = [lic.model_dump(mode="json") for lic in licenses]
            storage.write_jsonl(storage_path, records)
            logger.info("licenses_stored", source=source_name, count=len(licenses), path=storage_path)

            # Trigger ETL
            try:
                import httpx
                async with httpx.AsyncClient(timeout=10.0) as client:
                    await client.post(
                        f"{settings.etl_pipeline_url}/process",
                        json={"source_type": "license", "storage_path": storage_path},
                    )
            except Exception as e:
                logger.warning("etl_trigger_failed", error=str(e))

        # Update ingestion state
        firestore.update_ingestion_state(f"scraper-{source_name}", {
            "source_id": f"scraper-{source_name}",
            "last_run": datetime.utcnow(),
            "last_record_date": today,
            "records_ingested": len(licenses),
            "errors": 0,
        })

        return {
            "source": source_name,
            "state": scraper.state_code,
            "records": len(licenses),
            "day_of_month": day_of_month,
        }

    except Exception as e:
        logger.error("scrape_failed", source=source_name, error=str(e))
        firestore.update_ingestion_state(f"scraper-{source_name}", {
            "source_id": f"scraper-{source_name}",
            "last_run": datetime.utcnow(),
            "errors": 1,
        })
        return {"source": source_name, "error": str(e)}
    finally:
        await scraper.close()
