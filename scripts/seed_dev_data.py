"""Seed development Firestore emulator with sample leads and contractors."""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("FIRESTORE_EMULATOR_HOST", "localhost:8681")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "leadgen-mvp-local")

from shared.clients.firestore_client import FirestoreClient
from shared.utils import generate_id, extract_keywords

db = FirestoreClient.get_instance("leadgen-mvp-local")

SAMPLE_LEADS = [
    {
        "type": "permit", "trade": "ELECTRICAL",
        "title": "ELECTRICAL - Commercial panel upgrade and rewiring, 3-story office building",
        "value": 185000, "addr": "1234 Commerce St, Houston, TX 77002",
        "owner": {"n": "Houston Business Park LLC", "p": "+17135551234", "e": "owner@hbp.com"},
        "gc": {"n": "", "p": "", "lic": ""},
        "status": "active", "posted": (datetime.utcnow() - timedelta(days=3)).isoformat(),
        "src": "houston-djnh-at8a", "score": 85,
    },
    {
        "type": "permit", "trade": "PLUMBING",
        "title": "PLUMBING - Full plumbing replacement, residential 4-bedroom",
        "value": 42000, "addr": "5678 Oak Ave, Austin, TX 78701",
        "owner": {"n": "Smith Family Trust", "p": "+15125559876", "e": ""},
        "gc": {"n": "Austin Plumbing Co", "p": "+15125550001", "lic": "TX-PLB-12345"},
        "status": "active", "posted": (datetime.utcnow() - timedelta(days=1)).isoformat(),
        "src": "austin-3syk-w9eu", "score": 72,
    },
    {
        "type": "permit", "trade": "ROOFING",
        "title": "ROOFING - Complete roof replacement, commercial warehouse 40,000 sqft",
        "value": 320000, "addr": "9900 Industrial Blvd, Dallas, TX 75201",
        "owner": {"n": "DFW Logistics LLC", "p": "+12145550123", "e": "ops@dfwlog.com"},
        "gc": {"n": "", "p": "", "lic": ""},
        "status": "active", "posted": (datetime.utcnow() - timedelta(days=5)).isoformat(),
        "src": "dallas-e7gq-4sah", "score": 91,
    },
    {
        "type": "permit", "trade": "HVAC",
        "title": "HVAC - New HVAC system installation, 12-unit apartment complex",
        "value": 95000, "addr": "2200 Congress Ave, Austin, TX 78704",
        "owner": {"n": "Congress Properties", "p": "+15125553333", "e": "pm@congressprop.com"},
        "gc": {"n": "Lone Star HVAC", "p": "+15125554444", "lic": "TX-HVAC-67890"},
        "status": "active", "posted": (datetime.utcnow() - timedelta(days=12)).isoformat(),
        "src": "austin-3syk-w9eu", "score": 68,
    },
    {
        "type": "bid", "trade": "CONCRETE",
        "title": "Federal: Concrete foundation work, VA Medical Center parking structure",
        "value": 2800000, "addr": "Houston, TX 77030",
        "owner": {"n": "Dept of Veterans Affairs", "p": "+18005551234", "e": "procurement@va.gov"},
        "gc": {"n": "", "p": "", "lic": ""},
        "status": "active",
        "posted": (datetime.utcnow() - timedelta(days=2)).isoformat(),
        "deadline": (datetime.utcnow() + timedelta(days=28)).isoformat(),
        "src": "sam.gov", "score": 95,
    },
    {
        "type": "permit", "trade": "GENERAL",
        "title": "GENERAL - Full gut renovation, historic downtown building conversion to lofts",
        "value": 1200000, "addr": "456 Main St, Chicago, IL 60601",
        "owner": {"n": "Chicago Loft Partners", "p": "+13125558888", "e": "dev@chicagoloft.com"},
        "gc": {"n": "Midwest Construction Group", "p": "+13125559999", "lic": "IL-GC-11111"},
        "status": "active", "posted": (datetime.utcnow() - timedelta(days=7)).isoformat(),
        "src": "chicago-ydr8-5enu", "score": 88,
    },
    {
        "type": "permit", "trade": "ELECTRICAL",
        "title": "ELECTRICAL - Solar panel installation + battery storage, commercial rooftop",
        "value": 225000, "addr": "789 Sunset Blvd, Los Angeles, CA 90028",
        "owner": {"n": "Sunset Entertainment LLC", "p": "+13235550000", "e": ""},
        "gc": {"n": "", "p": "", "lic": ""},
        "status": "active", "posted": (datetime.utcnow() - timedelta(days=4)).isoformat(),
        "src": "losangeles-yv23-pmwf", "score": 80,
    },
    {
        "type": "bid", "trade": "ELECTRICAL",
        "title": "Federal: Electrical upgrades, US Postal Service distribution center",
        "value": 450000, "addr": "Chicago, IL 60607",
        "owner": {"n": "US Postal Service", "p": "+18005552222", "e": "bids@usps.gov"},
        "gc": {"n": "", "p": "", "lic": ""},
        "status": "active",
        "posted": (datetime.utcnow() - timedelta(days=6)).isoformat(),
        "deadline": (datetime.utcnow() + timedelta(days=14)).isoformat(),
        "src": "sam.gov", "score": 78,
    },
]

SAMPLE_CONTRACTORS = [
    {
        "name": "Lone Star HVAC",
        "trades": ["HVAC"],
        "licenses": [{"state": "TX", "num": "TX-HVAC-67890", "type": "HVAC Contractor", "exp": "2027-06-30", "status": "ACTIVE"}],
        "addr": "1100 Lamar St, Austin, TX 78701",
        "phone": "+15125554444", "email": "info@lonestarhvac.com", "website": "lonestarhvac.com",
        "permit_count": 87, "avg_project_value": 78000,
    },
    {
        "name": "Austin Plumbing Co",
        "trades": ["PLUMBING"],
        "licenses": [{"state": "TX", "num": "TX-PLB-12345", "type": "Master Plumber", "exp": "2026-12-31", "status": "ACTIVE"}],
        "addr": "2200 S Lamar Blvd, Austin, TX 78704",
        "phone": "+15125550001", "email": "dispatch@austinplumbing.com", "website": "",
        "permit_count": 134, "avg_project_value": 35000,
    },
    {
        "name": "Midwest Construction Group",
        "trades": ["GENERAL", "CONCRETE", "FRAMING"],
        "licenses": [{"state": "IL", "num": "IL-GC-11111", "type": "General Contractor", "exp": "2027-03-15", "status": "ACTIVE"}],
        "addr": "500 N Michigan Ave, Chicago, IL 60611",
        "phone": "+13125559999", "email": "bids@midwestcg.com", "website": "midwestcg.com",
        "permit_count": 312, "avg_project_value": 895000,
    },
]

print("Seeding leads...")
for lead in SAMPLE_LEADS:
    lead_id = generate_id(lead["src"], lead["title"][:50], lead.get("addr", ""))
    lead["id"] = lead_id
    lead["keywords"] = extract_keywords(f"{lead['title']} {lead['trade']} {lead.get('addr','')}")
    lead["updated"] = datetime.utcnow().isoformat()
    db.leads().document(lead_id).set(lead)
    print(f"  + Lead: {lead['title'][:60]}...")

print("\nSeeding contractors...")
for contractor in SAMPLE_CONTRACTORS:
    contractor_id = generate_id(contractor["name"], contractor["licenses"][0]["state"])
    contractor["id"] = contractor_id
    contractor["updated"] = datetime.utcnow().isoformat()
    db.contractors().document(contractor_id).set(contractor)
    print(f"  + Contractor: {contractor['name']}")

print(f"\n✅ Seeded {len(SAMPLE_LEADS)} leads and {len(SAMPLE_CONTRACTORS)} contractors into Firestore emulator.")
