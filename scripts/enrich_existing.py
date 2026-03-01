#!/usr/bin/env python3
"""
Enrich existing Firestore leads with Gemini AI analysis.

Usage:
  python scripts/enrich_existing.py [--limit 300] [--skip-enriched]
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault("FIRESTORE_EMULATOR_HOST", "localhost:8681")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "projectw-e3d92")

from shared.logging_config import setup_logging
setup_logging("WARNING")

from shared.clients.firestore_client import FirestoreClient
from services.etl_pipeline.enricher import enrich_lead, reset_run_counter


async def main(limit: int, skip_enriched: bool) -> None:
    db = FirestoreClient(os.environ["GOOGLE_CLOUD_PROJECT"])
    reset_run_counter()

    print(f"🤖  BuildScope — AI Enrichment (Gemini gemma-3-27b-it)")
    print(f"   Target: {limit} leads | Skip already enriched: {skip_enriched}")
    print(f"   Rate:   ~28 RPM (free tier) → ~{limit * 2.15 / 60:.1f} min estimate")
    print()

    all_docs = list(db.leads().limit(5000).stream())
    print(f"   Found {len(all_docs)} total leads in Firestore")

    to_enrich = []
    for doc in all_docs:
        data = doc.to_dict()
        if skip_enriched and data.get("ai"):
            continue
        title = data.get("title", "")
        if len(title) > 20:
            to_enrich.append((doc.id, data))

    # Sort by score descending — enrich the best leads first
    to_enrich.sort(key=lambda x: x[1].get("score", 0), reverse=True)
    print(f"   Top score in queue: {to_enrich[0][1].get('score') if to_enrich else 0}")

    n = min(len(to_enrich), limit)
    eta = n * 16 / 60
    print(f"   Enriching {n} leads (~{eta:.0f} min at 16s/call — Gemini free tier)")
    print("   ─" * 30)

    enriched = 0
    skipped = 0
    errors = 0

    for doc_id, data in to_enrich[:limit]:
        try:
            result = await enrich_lead(data)
            if result.get("ai"):
                db.leads().document(doc_id).update({"ai": result["ai"]})
                enriched += 1
                ai = result["ai"]
                print(f"  ✅ [{enriched}] {data.get('title','')[:55]}")
                print(f"     → {ai.get('project_type')} | {ai.get('owner_type')} | urgency={ai.get('urgency')}")
            else:
                skipped += 1
        except Exception as e:
            errors += 1
            print(f"  ❌ {doc_id[:8]}: {e}")

    print()
    print("─" * 60)
    print(f"✅ Enrichment Complete")
    print(f"   Enriched:  {enriched}")
    print(f"   Skipped:   {skipped}")
    print(f"   Errors:    {errors}")

    # Invalidate dashboard cache
    try:
        import httpx
        httpx.post("http://localhost:8005/api/cache/clear", timeout=2)
    except Exception:
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=300)
    parser.add_argument("--skip-enriched", action="store_true", default=True)
    args = parser.parse_args()
    asyncio.run(main(args.limit, args.skip_enriched))
