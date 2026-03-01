from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from shared.clients.firestore_client import FirestoreClient
from shared.clients.storage_client import StorageClient
from shared.config import Settings
from shared.logging_config import get_logger
from shared.utils import extract_keywords, generate_id, normalize_phone

from .deduplicator import generate_contractor_id, generate_lead_id
from .enricher import enrich_lead
from .normalizer import normalize_bid_record, normalize_permit_record
from .scorer import score_lead
from .trade_classifier import classify_trade

logger = get_logger(__name__)


async def process_batch(source_type: str, storage_path: str) -> dict[str, Any]:
    """Process a batch of raw records through the ETL pipeline.

    Steps: Load -> Normalize -> Classify Trade -> Score -> Store in Firestore
    """
    settings = Settings()
    storage = StorageClient(
        backend=settings.storage_backend,
        local_path=settings.local_storage_path,
        bucket_name=settings.gcs_bucket_name,
    )
    firestore = FirestoreClient.get_instance(settings.firestore_project_id)

    # Load raw records from storage
    records = storage.read_jsonl(storage_path)
    if not records:
        logger.info("no_records_to_process", path=storage_path)
        return {"processed": 0, "stored": 0}

    logger.info("processing_batch", source_type=source_type, records=len(records))

    leads_stored = 0
    contractors_updated = 0

    for record in records:
        try:
            if source_type == "permit":
                lead = _process_permit(record)
            elif source_type == "bid":
                lead = _process_bid(record)
            elif source_type == "license":
                _process_license(record, firestore)
                contractors_updated += 1
                continue
            else:
                logger.warning("unknown_source_type", source_type=source_type)
                continue

            if lead:
                # AI enrichment — adds project_type, owner_type, materials, urgency
                lead = await enrich_lead(lead)

                # Store in Firestore
                firestore.leads().document(lead["id"]).set(lead, merge=True)
                leads_stored += 1

                # Push real-time WebSocket alert to matching subscribers
                try:
                    async with httpx.AsyncClient(timeout=2.0) as _notify_client:
                        await _notify_client.post(
                            f"{settings.api_server_url}/api/internal/notify-lead",
                            json={"lead": lead},
                        )
                except Exception:
                    pass  # non-blocking — don't fail ETL on notification errors

                # Update contractor profile if contractor info exists
                _update_contractor_from_lead(lead, firestore)

        except Exception as e:
            logger.warning(f"record_processing_error: {e}")

    logger.info(
        "batch_complete",
        source_type=source_type,
        processed=len(records),
        leads_stored=leads_stored,
        contractors_updated=contractors_updated,
    )

    return {
        "processed": len(records),
        "leads_stored": leads_stored,
        "contractors_updated": contractors_updated,
    }


def _process_permit(record: dict[str, Any]) -> dict[str, Any] | None:
    """Process a single permit record into a lead."""
    normalized = normalize_permit_record(record)
    description = normalized.get("work_description", "")
    trade, confidence = classify_trade(description)

    address = normalized.get("address", {})
    addr_str = _build_address_string(address)
    owner = normalized.get("owner", {})
    contractor = normalized.get("contractor", {})

    lead: dict[str, Any] = {
        "id": generate_lead_id({"type": "permit", **normalized}),
        "type": "permit",
        "trade": trade,
        "title": f"{normalized.get('permit_type', 'BUILDING')} - {description[:100]}",
        "value": normalized.get("estimated_cost"),
        "addr": addr_str,
        "city": address.get("city", "").strip().title() or normalized.get("source_id", "").replace("-", " ").title(),
        "state": address.get("state", "").strip().upper(),
        "geo_lat": address.get("lat"),
        "geo_lng": address.get("lng"),
        "owner": {
            "n": owner.get("name", ""),
            "p": owner.get("phone", ""),
            "e": owner.get("email", ""),
        },
        "gc": {
            "n": contractor.get("name", ""),
            "p": contractor.get("phone", ""),
            "lic": contractor.get("license_number", ""),
        },
        "status": "active",
        "posted": normalized.get("issued_date") or normalized.get("filed_date"),
        "src": normalized.get("source_id", ""),
        "keywords": extract_keywords(f"{description} {trade} {addr_str}"),
        "updated": datetime.now(timezone.utc).isoformat(),
    }

    lead["score"] = score_lead(lead)
    return lead


def _process_bid(record: dict[str, Any]) -> dict[str, Any] | None:
    """Process a single bid record into a lead."""
    normalized = normalize_bid_record(record)
    description = normalized.get("description", "") or normalized.get("title", "")
    naics = normalized.get("naics_code", "")
    trade, _confidence = classify_trade(description, naics)

    location = normalized.get("location", {})
    addr_str = f"{location.get('city', '')}, {location.get('state', '')} {location.get('zip_code', '')}".strip(", ")

    contacts = normalized.get("contacts", [])
    primary_contact = contacts[0] if contacts else {}

    lead: dict[str, Any] = {
        "id": generate_lead_id({"type": "bid", **normalized}),
        "type": "bid",
        "trade": normalized.get("trade_category") or trade,
        "title": normalized.get("title", "")[:200],
        "value": normalized.get("estimated_value"),
        "addr": addr_str,
        "owner": {
            "n": normalized.get("agency", ""),
            "p": primary_contact.get("phone", ""),
            "e": primary_contact.get("email", ""),
        },
        "gc": {"n": "", "p": "", "lic": ""},
        "status": "active",
        "posted": normalized.get("posted_date"),
        "deadline": normalized.get("response_deadline"),
        "src": normalized.get("source", ""),
        "keywords": extract_keywords(f"{description} {trade} {addr_str}"),
        "updated": datetime.now(timezone.utc).isoformat(),
    }

    lead["score"] = score_lead(lead)
    return lead


def _process_license(record: dict[str, Any], firestore: FirestoreClient) -> None:
    """Process a license record to update the contractor collection."""
    name = record.get("business_name", "")
    state = record.get("address_state", "")
    if not name or not state:
        return

    contractor_id = generate_contractor_id(name, state)
    addr_parts = [
        record.get("address_street", ""),
        record.get("address_city", ""),
        record.get("address_state", ""),
        record.get("address_zip", ""),
    ]
    addr_str = ", ".join(p for p in addr_parts if p)

    contractor_data: dict[str, Any] = {
        "id": contractor_id,
        "name": name,
        "trades": [record.get("trade_classification", "")],
        "licenses": [{
            "state": state,
            "num": record.get("license_number", ""),
            "type": record.get("trade_classification", ""),
            "exp": record.get("expiration_date"),
            "status": record.get("status", "ACTIVE"),
        }],
        "addr": addr_str,
        "phone": normalize_phone(record.get("phone", "")),
        "email": record.get("email", ""),
        "website": record.get("website", ""),
        "updated": datetime.now(timezone.utc).isoformat(),
    }

    firestore.contractors().document(contractor_id).set(contractor_data, merge=True)


def _update_contractor_from_lead(lead: dict[str, Any], firestore: FirestoreClient) -> None:
    """Update contractor profile from a lead's contractor info."""
    gc = lead.get("gc", {})
    name = gc.get("n", "")
    if not name:
        return

    # Extract state from address
    addr = lead.get("addr", "")
    state = ""
    parts = addr.split(",")
    for part in parts:
        stripped = part.strip()
        if len(stripped) == 2 and stripped.isalpha():
            state = stripped.upper()
            break
        # Check for "STATE ZIP" pattern
        tokens = stripped.split()
        if len(tokens) >= 2 and len(tokens[0]) == 2 and tokens[0].isalpha():
            state = tokens[0].upper()
            break

    if not state:
        return

    contractor_id = generate_contractor_id(name, state)
    update: dict[str, Any] = {
        "id": contractor_id,
        "name": name,
        "last_permit": lead.get("posted"),
        "updated": datetime.now(timezone.utc).isoformat(),
    }

    firestore.contractors().document(contractor_id).set(update, merge=True)


def _build_address_string(address: dict[str, Any]) -> str:
    """Build a compact address string from address dict."""
    parts = [
        address.get("street", ""),
        address.get("city", ""),
        address.get("state", ""),
        address.get("zip_code", ""),
    ]
    return ", ".join(p for p in parts if p)
