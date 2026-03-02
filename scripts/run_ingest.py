"""
Full end-to-end ingestion runner — no static data.

Flow:
  1. Clear existing leads + contractors from Firestore emulator
  2. Ingest live permits from Socrata APIs (top-priority cities)
  3. Ingest live federal bids from SAM.gov + USASpending
  4. Run ETL pipeline (normalize → classify → score → AI enrich → store)

Usage:
  python scripts/run_ingest.py [--days DAYS] [--cities CITY,...] [--clear]

Defaults:
  --days  14        (look back 14 days for new records)
  --cities  all     (all enabled cities)
  --clear           (wipe existing leads before ingest, default: True)
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

# ── bootstrap path + env ─────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("FIRESTORE_EMULATOR_HOST", "localhost:8681")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "projectw-e3d92")

# Load .env
env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

# ── imports ───────────────────────────────────────────────────────────────────
from shared.clients.firestore_client import FirestoreClient
from shared.clients.storage_client import StorageClient
from shared.config import Settings
from shared.logging_config import setup_logging

setup_logging("WARNING")  # suppress INFO noise; show warnings/errors only

# ── helpers ───────────────────────────────────────────────────────────────────
def section(title: str) -> None:
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")

def ok(msg: str) -> None:
    print(f"  ✅ {msg}")

def info(msg: str) -> None:
    print(f"  ℹ️  {msg}")

def warn(msg: str) -> None:
    print(f"  ⚠️  {msg}")

def err(msg: str) -> None:
    print(f"  ❌ {msg}")


# ── 1. Clear Firestore ────────────────────────────────────────────────────────

def clear_collections(db: FirestoreClient) -> None:
    """Delete all leads and contractors from Firestore."""
    for coll_name, coll_ref in [("leads", db.leads()), ("contractors", db.contractors())]:
        batch_size = 500
        deleted = 0
        while True:
            docs = list(coll_ref.limit(batch_size).stream())
            if not docs:
                break
            for doc in docs:
                doc.reference.delete()
                deleted += 1
        ok(f"Cleared {deleted} {coll_name}")


# ── 2. Permit ingestion (Socrata) ────────────────────────────────────────────

# Priority cities — tested Socrata endpoints only
PRIORITY_PORTALS = {
    "austin":    ("data.austintexas.gov",  "3syk-w9eu",  "TX"),
    "chicago":   ("data.cityofchicago.org","ydr8-5enu",  "IL"),
    "houston":   ("data.houstontx.gov",    "djnh-at8a",  "TX"),
    "dallas":    ("www.dallasopendata.com","e7gq-4sah",  "TX"),
    "nashville": ("data.nashville.gov",    "3h5w-q8b7",  "TN"),
    "la":        ("data.lacity.org",       "yv23-pmwf",  "CA"),
    "seattle":   ("data.seattle.gov",      "76t5-zmmm",  "WA"),
    "sf":        ("data.sfgov.org",        "i98e-djp9",  "CA"),
    "boston":    ("data.boston.gov",       "hfbi-6lbg",  "MA"),
    "denver":    ("data.denvergov.org",    "p2dh-wkgq",  "CO"),
    "miami-dade":("opendata.miamidade.gov","dv5p-i7yv",  "FL"),
    "dc":        ("opendata.dc.gov",       "awjx-nebs",  "DC"),
    "nyc":       ("data.cityofnewyork.us", "ipu4-2q9a",  "NY"),
    "portland":  ("data.portlandoregon.gov","uyux-8gax", "OR"),
    "san-diego": ("data.sandiegocounty.gov","dyzh-7eat", "CA"),
}

async def ingest_permits_direct(
    settings: Settings,
    storage: StorageClient,
    db: FirestoreClient,
    days_back: int,
    city_filter: list[str] | None,
    max_per_portal: int = 1000,
) -> dict[str, int]:
    """Ingest permits from Socrata APIs, write JSONL to local storage."""
    from services.permit_ingester.socrata_client import SocrataClient
    from services.permit_ingester.field_mapper import map_to_permit
    from services.permit_ingester.ingester import load_sources

    client = SocrataClient()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    since = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y-%m-%dT00:00:00")
    results: dict[str, int] = {}
    storage_paths: list[tuple[str, str]] = []  # (source_type, path)

    sources = load_sources()
    # Deduplicate by id (sources.yaml has some dupes)
    seen_ids: set[str] = set()
    deduped: list[dict] = []
    for s in sources:
        sid = s["id"]
        if sid not in seen_ids:
            seen_ids.add(sid)
            deduped.append(s)
    sources = deduped

    for portal in sources:
        pid = portal["id"]
        if city_filter and pid not in city_filter:
            continue

        domain = portal["domain"]
        dataset_id = portal["dataset_id"]
        field_map = portal.get("field_map", {})
        state = portal.get("state", "")
        date_fmt = portal.get("date_format", "iso")  # iso | mdy
        date_field = field_map.get("issued_date") or field_map.get("filed_date")

        # Portals with non-ISO date storage: sort by date DESC, take most recent N
        # rather than using a where filter (which requires ISO format)
        if date_fmt == "mdy" or not date_field:
            where = None
        else:
            where = f"{date_field} > '{since}'"

        print(f"  📡 {pid} ({domain}/{dataset_id}) {'since ' + since[:10] if where else 'most recent'}...", end=" ", flush=True)
        try:
            rows = await client.fetch_all(
                domain=domain,
                dataset_id=dataset_id,
                where_clause=where,
                max_records=max_per_portal,
            )
            if not rows:
                print("0 records")
                results[pid] = 0
                continue

            permits = []
            for row in rows:
                try:
                    p = map_to_permit(row, pid, field_map, state)
                    permits.append(p.model_dump(mode="json"))
                except Exception:
                    pass

            path = f"permits/{today}/{pid}.jsonl"
            storage.write_jsonl(path, permits)
            storage_paths.append(("permit", path))
            results[pid] = len(permits)
            print(f"{len(permits)} permits ✓")

        except Exception as e:
            print(f"FAILED: {e}")
            results[pid] = -1

    await client.close()
    return results, storage_paths


# ── 3. Bid ingestion (SAM.gov + USASpending) ─────────────────────────────────

async def ingest_bids_direct(
    settings: Settings,
    storage: StorageClient,
    db: FirestoreClient,
    days_back: int,
) -> dict[str, int]:
    """Ingest federal bids from SAM.gov and USASpending."""
    from services.bid_ingester.sam_client import SamGovClient
    from services.bid_ingester.usaspending_client import USASpendingClient

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    storage_paths: list[tuple[str, str]] = []
    results: dict[str, int] = {}

    # SAM.gov
    if not settings.sam_gov_api_key:
        warn("SAM_GOV_API_KEY not set — skipping SAM.gov")
        results["sam_gov"] = 0
    else:
        print(f"  📡 SAM.gov (construction NAICS, last {days_back} days)...", end=" ", flush=True)
        sam = SamGovClient(settings.sam_gov_api_key)
        try:
            bids = await sam.fetch_construction_opportunities(days_back=days_back)
            if bids:
                path = f"bids/{today}/sam-gov.jsonl"
                storage.write_jsonl(path, [b.model_dump(mode="json") for b in bids])
                storage_paths.append(("bid", path))
                results["sam_gov"] = len(bids)
                print(f"{len(bids)} bids ✓")
            else:
                results["sam_gov"] = 0
                print("0 bids")
        except Exception as e:
            err(f"SAM.gov failed: {e}")
            results["sam_gov"] = 0
        finally:
            await sam.close()

    # USASpending
    print(f"  📡 USASpending.gov (awarded contracts, last {days_back} days)...", end=" ", flush=True)
    usa = USASpendingClient()
    try:
        awards = await usa.fetch_construction_awards(days_back=days_back)
        if awards:
            path = f"bids/{today}/usaspending.jsonl"
            storage.write_jsonl(path, [a.model_dump(mode="json") for a in awards])
            storage_paths.append(("bid", path))
            results["usaspending"] = len(awards)
            print(f"{len(awards)} awards ✓")
        else:
            results["usaspending"] = 0
            print("0 awards")
    except Exception as e:
        err(f"USASpending failed: {e}")
        results["usaspending"] = 0
    finally:
        await usa.close()

    return results, storage_paths


# ── 4. ETL pipeline ───────────────────────────────────────────────────────────

async def run_etl(
    storage_paths: list[tuple[str, str]],
    storage: StorageClient,
) -> dict[str, Any]:
    """Run ETL pipeline on all ingested JSONL files."""
    from services.etl_pipeline.pipeline import process_batch
    from services.etl_pipeline.enricher import reset_run_counter
    reset_run_counter()  # reset per-run cap and quota error counter

    total_leads = 0
    total_errors = 0

    for source_type, rel_path in storage_paths:
        # Make path absolute for storage client
        full_path = storage.local_path / rel_path
        if not full_path.exists():
            warn(f"File not found: {full_path}")
            continue

        record_count = sum(1 for _ in open(full_path))
        print(f"  ⚙️  ETL: {source_type} {rel_path} ({record_count} records)...", end=" ", flush=True)
        try:
            result = await process_batch(source_type, rel_path)
            stored = result.get("leads_stored", 0)
            total_leads += stored
            print(f"{stored} leads stored ✓")
        except Exception as e:
            err(f"ETL failed for {rel_path}: {e}")
            import traceback; traceback.print_exc()
            total_errors += 1

    return {"total_leads": total_leads, "errors": total_errors}


# ── 5. Also walk any existing raw files (re-process if needed) ────────────────

def find_all_raw_files(storage: StorageClient) -> list[tuple[str, str]]:
    """Find all JSONL files in storage from today."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    paths = []
    raw = storage.local_path
    for source_type in ("permit", "bid"):
        folder = raw / (source_type + "s") / today
        if folder.exists():
            for f in sorted(folder.glob("*.jsonl")):
                rel = str(f.relative_to(raw))
                paths.append((source_type, rel))
    return paths


# ── Main ──────────────────────────────────────────────────────────────────────

async def main(args: argparse.Namespace) -> None:
    print("\n🏗️  BuildScope — Live Data Ingestion")
    print(f"   Days back: {args.days}  |  Max per portal: {args.max_per_portal}")
    print(f"   Firestore: {os.environ.get('FIRESTORE_EMULATOR_HOST')} (emulator)")
    print(f"   Storage:   {ROOT}/data/raw")

    settings = Settings()
    storage = StorageClient(
        backend="local",
        local_path=str(ROOT / "data" / "raw"),
    )
    db = FirestoreClient.get_instance(settings.firestore_project_id)

    city_filter = [c.strip() for c in args.cities.split(",")] if args.cities else None

    all_storage_paths: list[tuple[str, str]] = []

    # ── Step 1: Clear ──────────────────────────────────────────────────────────
    if args.clear:
        section("Step 1 — Clearing existing data")
        clear_collections(db)

    # ── Step 2: Permits ────────────────────────────────────────────────────────
    section("Step 2 — Permit Ingestion (Socrata SODA APIs)")
    permit_results, permit_paths = await ingest_permits_direct(
        settings, storage, db, args.days, city_filter, args.max_per_portal
    )
    all_storage_paths.extend(permit_paths)
    total_raw_permits = sum(v for v in permit_results.values() if v > 0)
    ok(f"Raw permits fetched: {total_raw_permits} across {len([v for v in permit_results.values() if v > 0])} cities")

    # ── Step 2b: CKAN Permits (San Antonio, Boston) ────────────────────────────
    section("Step 2b — CKAN Permit Ingestion (San Antonio, Boston)")
    try:
        from services.permit_ingester.ckan_client import CKAN_SOURCES, fetch_ckan_permits
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        for ckan_src in CKAN_SOURCES:
            city_id = ckan_src["id"]
            print(f"  📡 {city_id} ({ckan_src['base_url']})...", end=" ", flush=True)
            try:
                records = await fetch_ckan_permits(ckan_src, days_back=args.days, max_records=args.max_per_portal)
                if records:
                    rel_path = f"permits/{today}/{city_id}.jsonl"
                    storage.write_jsonl(rel_path, records)
                    all_storage_paths.append(("permit", rel_path))
                    total_raw_permits += len(records)
                    print(f"{len(records)} permits ✓")
                else:
                    print("0 records")
            except Exception as e:
                print(f"error: {e}")
    except ImportError as e:
        print(f"  ⚠️  CKAN client unavailable: {e}")

    # ── Step 2c: ArcGIS Permits (Nashville, …) ────────────────────────────────
    section("Step 2c — ArcGIS Permit Ingestion (Nashville)")
    try:
        from services.permit_ingester.arcgis_client import fetch_arcgis_permits
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        arcgis_records = await fetch_arcgis_permits(days=args.days, max_per_source=args.max_per_portal)
        if arcgis_records:
            # Group by portal_id for separate files
            by_portal: dict[str, list] = {}
            for rec in arcgis_records:
                pid = rec.pop("src_portal", "arcgis")
                by_portal.setdefault(pid, []).append(rec)
            for pid, recs in by_portal.items():
                rel_path = f"permits/{today}/{pid}.jsonl"
                storage.write_jsonl(rel_path, recs)
                all_storage_paths.append(("permit", rel_path))
                total_raw_permits += len(recs)
                print(f"  ✓ {pid}: {len(recs)} permits")
        else:
            print("  0 records from ArcGIS sources")
    except Exception as e:
        print(f"  ⚠️  ArcGIS client error: {e}")

    # ── Step 3: Bids ───────────────────────────────────────────────────────────
    section("Step 3 — Bid Ingestion (SAM.gov + USASpending)")
    bid_results, bid_paths = await ingest_bids_direct(
        settings, storage, db, args.days
    )
    all_storage_paths.extend(bid_paths)
    total_raw_bids = sum(v for v in bid_results.values() if v > 0)
    ok(f"Raw bids fetched: {total_raw_bids}")

    if not all_storage_paths:
        err("No data fetched from any source. Check API connectivity and keys.")
        sys.exit(1)

    # ── Step 4: ETL ────────────────────────────────────────────────────────────
    section("Step 4 — ETL Pipeline (normalize → classify → score → store)")
    etl_result = await run_etl(all_storage_paths, storage)

    # ── Step 5: Summary ────────────────────────────────────────────────────────
    section("✅ Ingestion Complete")

    # Final counts from Firestore
    lead_count = sum(1 for _ in db.leads().limit(5000).stream())
    contractor_count = sum(1 for _ in db.contractors().limit(5000).stream())

    print(f"""
  Leads stored:       {lead_count}
  Contractors:        {contractor_count}
  ETL errors:         {etl_result['errors']}

  Sources:
    Permits:  {total_raw_permits} raw → {etl_result['total_leads']} leads
    SAM.gov:  {bid_results.get('sam_gov', 0)} bids
    USA Spending: {bid_results.get('usaspending', 0)} awards

  Raw files in: {ROOT}/data/raw/
  Visit:        http://localhost:8005
""")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run live data ingestion for BuildScope")
    parser.add_argument("--days", type=int, default=14,
                        help="Days back to fetch (default: 14)")
    parser.add_argument("--max-per-portal", type=int, default=1000,
                        help="Max records per Socrata portal (default: 1000)")
    parser.add_argument("--cities", type=str, default="",
                        help="Comma-separated portal IDs to run (default: all). "
                             "Options: austin,chicago,houston,dallas,nashville,la,seattle,sf,boston,denver,miami-dade,dc,nyc,portland,san-diego")
    parser.add_argument("--no-clear", dest="clear", action="store_false",
                        help="Don't clear existing leads before ingest")
    parser.set_defaults(clear=True)
    args = parser.parse_args()
    asyncio.run(main(args))
