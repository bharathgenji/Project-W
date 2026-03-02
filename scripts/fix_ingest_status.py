"""
Sync the _meta/ingest_status Firestore document to reflect the actual
lead/contractor counts (used after a CLI-based ingest run that bypassed
the API's in-memory state tracker).

Usage:
    python scripts/fix_ingest_status.py
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
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


def main() -> None:
    settings = Settings()
    db = FirestoreClient.get_instance(settings.firestore_project_id)

    print("\n📊  Syncing ingest status to Firestore...")

    lead_count = sum(1 for _ in db.leads().limit(20000).stream())
    contractor_count = sum(1 for _ in db.contractors().limit(10000).stream())

    # Detect which source portals are represented
    srcs: set[str] = set()
    for doc in db.leads().limit(1000).stream():
        src = doc.to_dict().get("src", "")
        if src:
            portal = src.rsplit("-", 1)[0] if "-" in src else src
            srcs.add(portal)

    now = datetime.now(timezone.utc).isoformat()
    status = {
        "last_run":            now,
        "leads_stored":        lead_count,
        "contractors_updated": contractor_count,
        "sources":             sorted(srcs),
        "success":             True,
        "error":               None,
    }

    db.db.collection("_meta").document("ingest_status").set(status)
    print(f"  ✅ Updated _meta/ingest_status")
    print(f"     leads:       {lead_count}")
    print(f"     contractors: {contractor_count}")
    print(f"     sources:     {sorted(srcs)}")
    print(f"     last_run:    {now}\n")


if __name__ == "__main__":
    main()
