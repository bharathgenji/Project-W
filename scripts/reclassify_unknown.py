"""
Re-classify UNKNOWN leads in Firestore using the updated trade classifier.

Does NOT re-fetch permits — reads existing leads from Firestore, re-runs
classify_trade() on the title/description, and writes back only changed docs.

Usage:
    python scripts/reclassify_unknown.py [--dry-run]
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("FIRESTORE_EMULATOR_HOST", "localhost:8681")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "projectw-e3d92")

env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

from shared.clients.firestore_client import FirestoreClient
from shared.config import Settings
from services.etl_pipeline.trade_classifier import classify_trade


def main(dry_run: bool = False) -> None:
    settings = Settings()
    db = FirestoreClient.get_instance(settings.firestore_project_id)

    print("\n🔄  Re-classifying UNKNOWN leads...")
    print(f"   Firestore: {os.environ.get('FIRESTORE_EMULATOR_HOST')}")
    print(f"   Dry run:   {dry_run}\n")

    # Fetch all leads (UNKNOWN + all others so we can also catch misclassified)
    all_docs = list(db.leads().limit(20000).stream())
    print(f"   Total leads in Firestore: {len(all_docs)}")

    unknown_docs = [d for d in all_docs if d.to_dict().get("trade") in ("UNKNOWN", "", None)]
    print(f"   UNKNOWN / unclassified:   {len(unknown_docs)}\n")

    updated = 0
    trade_changes: dict[str, int] = {}

    for doc in unknown_docs:
        data = doc.to_dict()
        title = data.get("title", "")
        # Strip the "PERMIT_TYPE - " prefix to get the work description
        if " - " in title:
            _, _, desc = title.partition(" - ")
        else:
            desc = title

        # Also include addr city/state text to help with location-based classification
        classify_text = f"{desc} {data.get('addr', '')}".strip()

        new_trade, confidence = classify_trade(classify_text)

        if new_trade != "UNKNOWN" and new_trade != data.get("trade"):
            trade_changes[new_trade] = trade_changes.get(new_trade, 0) + 1
            if not dry_run:
                doc.reference.update({"trade": new_trade})
            updated += 1

    print("  Results:")
    for trade, count in sorted(trade_changes.items(), key=lambda x: -x[1]):
        print(f"    {trade:<25} {count:>5}")
    print(f"\n  {'[DRY RUN] Would update' if dry_run else 'Updated'}: {updated} leads")

    if not dry_run and updated > 0:
        # Invalidate the leads cache so dashboard reflects new trades
        print("\n  Clearing API cache (restart uvicorn or wait for TTL)...")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
