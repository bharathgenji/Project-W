# Construction Lead Generation MVP — Full Implementation Plan
## For Claude Code / Agentic Build on GCP Free Tier

---

## 1. ARCHITECTURE OVERVIEW

### GCP Free Tier Budget

| Service | Free Tier Limit | Our Usage | Fits? |
|---------|----------------|-----------|-------|
| **Cloud Run** | 180K vCPU-sec, 360K GiB-sec, 2M requests/mo (us-central1) | Scraper workers + API server | ✅ Yes |
| **Firestore** | 1 GB storage, 50K reads/day, 20K writes/day | Lead database, user profiles | ✅ Yes (with careful design) |
| **Cloud Scheduler** | 3 free jobs | Trigger daily/weekly scrapes | ✅ Yes |
| **Cloud Storage** | 5 GB (us-central1/us-east1), 1 GB egress | Raw scraped data, cached files | ✅ Yes |
| **Artifact Registry** | 500 MB storage | Docker images | ✅ Yes |
| **Cloud Build** | 120 build-min/day | CI/CD pipeline | ✅ Yes |
| **BigQuery** | 1 TB query/mo, 10 GB storage | Analytics (optional) | ✅ Yes |
| **Secret Manager** | 6 active secret versions | API keys storage | ✅ Yes |

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLOUD SCHEDULER                          │
│   (3 free cron jobs: daily-permits, weekly-bids, daily-scrape) │
└──────────┬──────────────────┬──────────────────┬────────────────┘
           │                  │                  │
           ▼                  ▼                  ▼
┌──────────────────┐ ┌────────────────┐ ┌────────────────────────┐
│  CLOUD RUN:      │ │ CLOUD RUN:     │ │ CLOUD RUN:             │
│  Permit Ingester │ │ Bid Ingester   │ │ Web Scraper            │
│  (Socrata APIs + │ │ (SAM.gov API)  │ │ (Playwright + Scrapy)  │
│   Census API)    │ │                │ │ (State license DBs,    │
│                  │ │                │ │  planning commissions) │
└────────┬─────────┘ └───────┬────────┘ └───────────┬────────────┘
         │                   │                      │
         ▼                   ▼                      ▼
┌────────────────────────────────────────────────────────────────┐
│                    CLOUD STORAGE (RAW DATA)                     │
│              JSON files organized by source/date                │
└───────────────────────────┬────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│                  CLOUD RUN: ETL Pipeline                        │
│         Normalize → Deduplicate → Classify → Geocode           │
│         (Triggered by Pub/Sub or HTTP from ingesters)          │
└───────────────────────────┬────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│                      FIRESTORE                                  │
│    Collections: leads, contractors, permits, bids, users       │
│    (1 GB free — carefully designed document structure)          │
└───────────────────────────┬────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│              CLOUD RUN: API Server (FastAPI)                    │
│          /leads, /search, /contractors, /dashboard              │
│          + Simple React frontend (static on GCS)               │
└────────────────────────────────────────────────────────────────┘
```

---

## 2. COMPLETE DATA SOURCE REGISTRY

### PHASE A: Socrata Open Data Portals (Free APIs, Structured JSON)

These are the highest-value, lowest-effort sources. All use the same SODA API pattern.

**API Pattern:** `https://{domain}/resource/{dataset_id}.json?$where=issue_date > '{date}'&$limit=1000`

| # | City/County | Domain | Dataset ID | Data Fields | Records | Priority |
|---|------------|--------|-----------|-------------|---------|----------|
| 1 | **New York City** | `data.cityofnewyork.us` | `ipu4-2q9a` | Permit type, job description, owner, contractor, cost, address, borough, coordinates | 3.98M+ | 🔴 Critical |
| 2 | **Chicago** | `data.cityofchicago.org` | `ydr8-5enu` | Permit #, type, work description, contractor (up to 15), address, reported cost, issue date | 800K+ | 🔴 Critical |
| 3 | **Los Angeles** | `data.lacity.org` | `yv23-pmwf` | Permit type, work description, address, valuation, contractor, issue date | 1.5M+ | 🔴 Critical |
| 4 | **Houston** | `data.houstontx.gov` | `djnh-at8a` | Permit #, project name, address, applicant, contractor, valuation, status | 500K+ | 🔴 Critical |
| 5 | **San Francisco** | `data.sfgov.org` | `i98e-djp9` | Permit type, description, address, existing/proposed use, cost, neighborhoods | 600K+ | 🔴 Critical |
| 6 | **Austin** | `data.austintexas.gov` | `3syk-w9eu` | Permit type, work class, address, contractor, project valuation, status | 400K+ | 🟡 High |
| 7 | **Dallas** | `www.dallasopendata.com` | `e7gq-4sah` | Permit type, address, applicant, contractor, project value | 200K+ | 🟡 High |
| 8 | **Seattle** | `data.seattle.gov` | `76t5-zmmm` | Permit type, action, description, value, contractor, address, coordinates | 250K+ | 🟡 High |
| 9 | **San Diego County** | `data.sandiegocounty.gov` | `dyzh-7eat` | Permit type, address, description, valuation, status | 300K+ | 🟡 High |
| 10 | **Denver** | `data.denvergov.org` | `p2dh-wkgq` | Permit type, address, contractor, cost, status | 200K+ | 🟡 High |
| 11 | **Portland** | `data.portlandoregon.gov` | `uyux-8gax` | Permit type, description, address, valuation, contractor | 200K+ | 🟡 High |
| 12 | **Boston** | `data.boston.gov` | `hfbi-6lbg` | Permit type, applicant, owner, address, work description | 150K+ | 🟡 High |
| 13 | **New Orleans** | `data.nola.gov` | `wc9q-fj3m` | Permit type, address, contractor, owner, project cost | 100K+ | 🟢 Medium |
| 14 | **Kansas City** | `data.kcmo.org` | `ibhq-vfej` | Permit type, address, contractor, cost | 100K+ | 🟢 Medium |
| 15 | **Baltimore** | `data.baltimorecity.gov` | `fqd2-swkr` | Permit type, description, address, contractor | 80K+ | 🟢 Medium |
| 16 | **Miami-Dade County** | `opendata.miamidade.gov` | `dv5p-i7yv` | Permit type, address, applicant, valuation | 200K+ | 🟡 High |
| 17 | **King County (Seattle area)** | `data.kingcounty.gov` | (search "permits") | Various permit datasets | Varies | 🟢 Medium |
| 18 | **Cook County (Chicago area)** | `datacatalog.cookcountyil.gov` | (search "permits") | County-level permits | Varies | 🟢 Medium |
| 19 | **Fort Worth** | `data.fortworthtexas.gov` | (search "permits") | City permits | Varies | 🟢 Medium |
| 20 | **San Jose** | `data.sanjoseca.gov` | `6s5y-scdv` | Building permits | 100K+ | 🟢 Medium |
| 21 | **Columbus, OH** | `data.columbus.gov` | (search "permits") | Building permits | Varies | 🟢 Medium |
| 22 | **Nashville** | `data.nashville.gov` | `3h5w-q8b7` | Building permits | 150K+ | 🟡 High |
| 23 | **Washington DC** | `opendata.dc.gov` | `awjx-nebs` | Building permits, address, owner, permit type | 200K+ | 🟡 High |
| 24 | **Philadelphia** | `opendataphilly.org` | (ArcGIS-based — needs custom approach) | Permits, licenses | 300K+ | 🟡 High |
| 25 | **Phoenix** | `phoenixopendata.com` | (search "permits") | Building permits | 200K+ | 🟡 High |

**IMPORTANT NOTE ON DATASET IDs:** The dataset IDs listed above are based on research and may change. Your Claude Code agent's FIRST task for each city should be:

```bash
# Discovery step — find the actual building permit dataset for each city
curl "https://data.cityofchicago.org/api/views.json?q=building+permits&limit=10" | jq '.[].id'
```

### PHASE B: Federal Government APIs (100% Free, Structured)

| Source | API Endpoint | Auth | Rate Limit | What You Get |
|--------|-------------|------|-----------|-------------|
| **SAM.gov Opportunities** | `https://api.sam.gov/prod/opportunities/v2/search` | Free API key (register at sam.gov) | 1,000/day (registered) | All federal construction bids, RFPs, solicitations. Filter by NAICS 23xxxx for construction. Includes: title, agency, deadline, contact email/phone, award amount, set-aside type |
| **USASpending.gov** | `https://api.usaspending.gov/` | No auth needed | Generous | Federal contract awards — who won what, amounts, agencies. Great for understanding competitive landscape |
| **Census Building Permits** | `https://api.census.gov/data/timeseries/eits/bps` | Free API key | Generous | Aggregate monthly permit counts by metro area / county. Useful for market sizing and trends |
| **FOIA.gov** | `https://www.foia.gov/api/` | No auth | Standard | FOIA requests and responses related to construction contracts |

**SAM.gov Integration Code Pattern:**

```python
# Filter for construction opportunities
params = {
    "api_key": SAM_API_KEY,
    "limit": 100,
    "postedFrom": "01/01/2026",
    "postedTo": "02/28/2026",
    "ptype": "o",  # solicitations only
    "ncode": "236220",  # Commercial/Institutional Building Construction
    # Other useful NAICS: 238210 (Electrical), 238220 (Plumbing/HVAC), 
    # 238110 (Concrete), 238160 (Roofing), 238310 (Drywall)
}
# Response includes: title, agency, deadline, contact info, place of performance
```

**Key NAICS codes for construction subcontractors:**
- 236220 — Commercial/Institutional Building Construction
- 238110 — Poured Concrete
- 238120 — Structural Steel/Precast Concrete
- 238130 — Framing
- 238140 — Masonry
- 238150 — Glass/Glazing
- 238160 — Roofing
- 238210 — Electrical Contractors
- 238220 — Plumbing, Heating, AC
- 238290 — Other Building Equipment
- 238310 — Drywall/Insulation
- 238320 — Painting/Wall Covering
- 238330 — Flooring
- 238340 — Tile/Terrazzo
- 238350 — Finish Carpentry
- 238390 — Other Finishing
- 238910 — Site Preparation
- 238990 — All Other Specialty Trade

### PHASE C: State Contractor License Databases (Free, Requires Scraping)

These are CRITICAL for contact enrichment — they contain verified business names, addresses, phone numbers, license types, and status.

| # | State | URL | Format | Scrape Method | Fields Available | Priority |
|---|-------|-----|--------|--------------|-----------------|----------|
| 1 | **California (CSLB)** | `https://www.cslb.ca.gov/OnlineServices/CheckLicenseII/CheckLicense.aspx` | ASP.NET form | Playwright (JS-rendered) | License #, name, address, phone, classification, status, bonds, insurance | 🔴 Critical (300K+ active) |
| 2 | **Texas (TDLR)** | `https://www.tdlr.texas.gov/LicenseSearch/` | HTML search | Playwright | License type, name, address, status, expiration | 🔴 Critical |
| 3 | **Florida (DBPR)** | `https://www.myfloridalicense.com/wl11.asp` | HTML search | Playwright + requests | Name, license #, address, county, status, classification | 🔴 Critical |
| 4 | **New York** | `https://www.nyc.gov/site/buildings/safety/licensing.page` | Mixed | Playwright | License type, name, status | 🟡 High |
| 5 | **Illinois** | `https://www.idfpr.com/Applications/Licenselookup/Licenselookup.aspx` | ASP.NET | Playwright | Name, license #, address, status, type | 🟡 High |
| 6 | **Pennsylvania** | `https://www.pals.pa.gov/#/page/search` | Angular SPA | Playwright (heavy JS) | Name, license #, address, status | 🟡 High |
| 7 | **Ohio** | `https://elicense.ohio.gov/OH_HomePage` | Modern SPA | Playwright | Name, license, type, status | 🟡 High |
| 8 | **Georgia** | `https://verify.sos.ga.gov/verification/` | HTML form | requests + Playwright | Name, license, type, address | 🟢 Medium |
| 9 | **North Carolina** | `https://www.nclbgc.org/licensees/search` | HTML | requests | Name, license #, classification, city | 🟢 Medium |
| 10 | **Arizona** | `https://roc.az.gov/` | HTML search | requests | Name, license, type, address, phone | 🟡 High |
| 11 | **Michigan** | `https://aca-prod.accela.com/LARA/` | Accela platform | Playwright | Name, license, type, status | 🟢 Medium |
| 12 | **Minnesota** | `https://www.dli.mn.gov/license-and-registration-lookup` | HTML + **nightly CSV downloads** | requests (CSV = goldmine!) | Full downloadable license data | 🟢 Medium |
| 13 | **Colorado** | `https://apps.colorado.gov/dora/licensing/Lookup/LicenseLookup.aspx` | ASP.NET | Playwright | Name, license, type, status, address | 🟢 Medium |
| 14 | **Washington** | `https://secure.lni.wa.gov/verify/` | HTML form | requests | Contractor name, license, type, bond, insurance | 🟡 High |
| 15 | **Virginia** | `https://www.dpor.virginia.gov/LicenseLookup/` | HTML | Playwright | Name, license, classification, address | 🟢 Medium |

**Scraping Strategy for State License DBs:**

```python
# Group by platform type for reusable scrapers:
# 
# ACCELA PLATFORM (same scraper, different configs):
#   Michigan, Maryland, many smaller states
#   → Playwright-based, interact with Accela's standard UI
#
# ASP.NET FORMS (same pattern):
#   California CSLB, Illinois IDFPR, Colorado DORA
#   → Playwright with __VIEWSTATE handling
#
# STANDARD HTML FORMS:
#   Florida DBPR, Washington LNI, Arizona ROC
#   → Simple requests + BeautifulSoup, faster
#
# BULK DOWNLOADS (best case):
#   Minnesota (nightly CSV), some others
#   → Just download and parse, no scraping needed
```

### PHASE D: Additional Scrapeable Government Sources

| Source Type | Example URLs | What You Get | Scrape Difficulty |
|-------------|-------------|-------------|-------------------|
| **State DOT bid boards** | `txdot.gov/business/letting-bids.html`, `dot.ca.gov/programs/procurement` (each state) | Transportation/infrastructure construction bids | Medium — each state different |
| **Municipal bid boards** | `houstonplanbidconnections.com`, `purchasing.cityofchicago.gov` | Local government construction bids | Medium-High |
| **Planning commission agendas** | Granicus/Legistar platforms across cities (e.g., `chicago.legistar.com`) | Pre-permit project signals — earliest indicator | High (PDF + HTML parsing) |
| **Code violation databases** | City code enforcement portals | Properties needing remediation → contractor opportunity | Medium |
| **County assessor records** | County assessor websites (3,143 counties) | Property ownership, value changes indicating renovation | High (massive fragmentation) |

---

## 3. IMPLEMENTATION PLAN — STEP BY STEP

### STEP 0: Project Setup (Day 1)

**Prompt for Claude Code:**

```
Create a new GCP project called "leadgen-mvp" in us-central1 (free tier region).
Set up the following:
1. Enable APIs: Cloud Run, Firestore, Cloud Storage, Cloud Scheduler, 
   Cloud Build, Secret Manager, Artifact Registry
2. Create a Firestore database in Native mode (us-central1)
3. Create a Cloud Storage bucket: "leadgen-mvp-raw-data"
4. Store API keys in Secret Manager:
   - sam-gov-api-key
   - census-api-key
5. Create a monorepo structure:

leadgen-mvp/
├── services/
│   ├── permit-ingester/       # Socrata API consumer
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   ├── sources.yaml       # All Socrata endpoints config
│   │   └── requirements.txt
│   ├── bid-ingester/          # SAM.gov + state bid boards
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   └── requirements.txt
│   ├── license-scraper/       # State contractor license DBs
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   ├── scrapers/
│   │   │   ├── california_cslb.py
│   │   │   ├── texas_tdlr.py
│   │   │   ├── florida_dbpr.py
│   │   │   ├── accela_generic.py
│   │   │   └── aspnet_generic.py
│   │   └── requirements.txt
│   ├── etl-pipeline/          # Normalize + deduplicate + geocode
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   ├── normalizer.py
│   │   ├── deduplicator.py
│   │   ├── geocoder.py
│   │   └── requirements.txt
│   └── api-server/            # FastAPI backend + React frontend
│       ├── Dockerfile
│       ├── main.py
│       ├── routers/
│       │   ├── leads.py
│       │   ├── search.py
│       │   ├── contractors.py
│       │   └── dashboard.py
│       ├── frontend/          # React app (built into static)
│       └── requirements.txt
├── shared/
│   ├── models.py              # Pydantic models
│   ├── firestore_client.py    # Shared DB client
│   └── config.py              # Environment configs
├── deploy/
│   ├── cloudbuild.yaml
│   └── scheduler-setup.sh
└── README.md
```

### STEP 1: Permit Ingester Service (Days 2-5)

**Prompt for Claude Code:**

```
Build the permit-ingester service that pulls building permit data from 
every Socrata-powered open data portal in the US.

Requirements:
1. Create sources.yaml with ALL the Socrata endpoints listed below 
   (I want EVERY city covered)
2. For each source:
   - Use SODA API: GET https://{domain}/resource/{dataset_id}.json
   - Paginate with $offset and $limit=1000
   - Filter by date: $where=issue_date > '{last_run_date}'
   - Handle rate limiting with exponential backoff
3. Normalize all permit data to a standard schema:
   {
     "source_id": "chicago-ydr8-5enu",
     "permit_number": "...",
     "permit_type": "BUILDING|ELECTRICAL|PLUMBING|MECHANICAL|DEMOLITION|OTHER",
     "work_description": "...",
     "address": { "street": "", "city": "", "state": "", "zip": "", "lat": 0, "lng": 0 },
     "estimated_cost": 0,
     "owner": { "name": "", "phone": "", "email": "" },
     "contractor": { "name": "", "license_number": "", "phone": "", "address": "" },
     "status": "FILED|ISSUED|COMPLETED|EXPIRED",
     "filed_date": "",
     "issued_date": "",
     "raw_data": {}  // original response for debugging
   }
4. Store normalized JSON in Cloud Storage: gs://leadgen-mvp-raw-data/permits/{date}/{source_id}.jsonl
5. After storage, trigger ETL pipeline via HTTP POST
6. Track last_run_date per source in Firestore (collection: "ingestion_state")
7. The service should be an HTTP Cloud Run service triggered by Cloud Scheduler
8. IMPORTANT: Implement a discovery mode that auto-finds building permit 
   datasets on any Socrata portal:
   GET https://{domain}/api/views.json?q=building+permit&limit=20

Here are the confirmed Socrata portals to include in sources.yaml:
[Include all 25+ portals from Phase A above]

Use Python with httpx (async), pydantic for models. 
Docker image should be <200MB.
Cloud Run config: 1 vCPU, 512MB RAM, 15min timeout, concurrency 1.
```

### STEP 2: Federal Bid Ingester (Days 5-7)

**Prompt for Claude Code:**

```
Build the bid-ingester service for SAM.gov federal construction opportunities.

Requirements:
1. SAM.gov Opportunities API integration:
   - Endpoint: https://api.sam.gov/prod/opportunities/v2/search
   - API key from Secret Manager
   - Pull ALL construction NAICS codes: 236220, 238110-238990
   - Filter: ptype=o (solicitations), p (presolicitations), k (combined)
   - Paginate through all results (limit=100 per page)
   - Extract: title, agency, deadline, contact info (name, email, phone), 
     place of performance (state, zip), set-aside type, NAICS, 
     solicitation number, award info if available
   
2. USASpending.gov integration:
   - Endpoint: https://api.usaspending.gov/api/v2/search/spending_by_award/
   - Pull recent construction contract awards
   - Extract: recipient (contractor who won), award amount, agency, 
     description, place of performance
   
3. Normalize to standard bid schema:
   {
     "source": "sam.gov|usaspending",
     "bid_id": "...",
     "title": "...",
     "description": "...",
     "agency": "...",
     "posted_date": "",
     "response_deadline": "",
     "naics_code": "",
     "trade_category": "ELECTRICAL|PLUMBING|HVAC|CONCRETE|ROOFING|GENERAL|...",
     "estimated_value": 0,
     "set_aside": "SMALL_BUSINESS|8A|HUBZONE|WOSB|SDVOSB|NONE",
     "location": { "state": "", "city": "", "zip": "" },
     "contacts": [{ "name": "", "email": "", "phone": "", "role": "" }],
     "documents": [{ "url": "", "type": "" }],
     "status": "PRESOLICITATION|ACTIVE|CLOSED|AWARDED"
   }

4. Store in Cloud Storage and trigger ETL
5. Also pull Census Building Permit Survey data monthly for market context:
   https://api.census.gov/data/timeseries/eits/bps?get=PERMITS&for=metropolitan+statistical+area/micropolitan+statistical+area:*

Cloud Run config: 1 vCPU, 256MB RAM, 10min timeout
Triggered by Cloud Scheduler: daily at 6am CT
```

### STEP 3: State License Scraper (Days 7-14)

**Prompt for Claude Code:**

```
Build the license-scraper service that scrapes state contractor license databases.

This is the most complex service. Build it with a modular scraper architecture:

1. Base scraper class:
   class BaseLicenseScraper:
       async def search(self, trade: str, state: str, page: int) -> list[ContractorLicense]
       async def get_details(self, license_number: str) -> ContractorLicense
   
   ContractorLicense schema:
   {
     "source": "CA-CSLB|TX-TDLR|FL-DBPR|...",
     "license_number": "",
     "business_name": "",
     "owner_name": "",
     "trade_classification": "",  # e.g., "C-10 Electrical", "C-36 Plumbing"
     "address": { "street": "", "city": "", "state": "", "zip": "" },
     "phone": "",
     "email": "",  # if available
     "status": "ACTIVE|EXPIRED|SUSPENDED|REVOKED",
     "issue_date": "",
     "expiration_date": "",
     "bond_amount": 0,
     "insurance": "",
     "workers_comp": "",
     "website": ""  # if available
   }

2. Platform-specific scrapers (prioritize by market size):

   TIER 1 — Build first (largest contractor populations):
   
   a) california_cslb.py (CSLB — 300K+ contractors)
      URL: https://www.cslb.ca.gov/OnlineServices/CheckLicenseII/CheckLicense.aspx
      Method: Playwright (ASP.NET form with __VIEWSTATE)
      Strategy: Search by classification code (A, B, C-1 through C-61)
      Rate limit: 2-3 sec delay between requests
      
   b) texas_tdlr.py (TDLR + TSBPE for electricians)
      URL: https://www.tdlr.texas.gov/LicenseSearch/
      Method: Playwright
      Also: Texas State Board of Plumbing Examiners
      
   c) florida_dbpr.py (DBPR — 200K+ contractors)
      URL: https://www.myfloridalicense.com/wl11.asp
      Method: requests + BeautifulSoup (simpler HTML)
      
   d) new_york.py (NYC DOB + NYS DOS)
      URL: https://a810-bisweb.nyc.gov/bisweb/
      Method: Playwright
      
   TIER 2 — Build second:
   
   e) illinois_idfpr.py
   f) pennsylvania_pals.py  
   g) ohio_elicense.py
   h) arizona_roc.py
   i) washington_lni.py (great data quality)
   j) georgia_sos.py
   
   TIER 3 — Bulk download states (easiest):
   
   k) minnesota_dli.py — Downloads nightly CSV
   l) Any other state with downloadable data

3. Scraping infrastructure:
   - Use Playwright with chromium for JS-heavy sites
   - Use httpx + BeautifulSoup for simple HTML sites
   - Implement rotating delays (2-5 sec between requests)
   - Respect robots.txt
   - Use headless browser in Docker: mcr.microsoft.com/playwright/python:v1.40.0
   - Store results in Cloud Storage as JSONL
   
4. Docker considerations:
   - Playwright Docker image is ~1.5GB — use multi-stage build
   - Final image should be under 800MB if possible
   - Cloud Run allows up to 32GB, so this is fine
   
5. Batch strategy (to stay within free tier):
   - DON'T scrape all states at once
   - Process 1-2 states per day, rotating through
   - Each scrape: search for active licenses, limit to 500-1000 per run
   - Full refresh cycle: 30 days for all 15 states
   - Incremental: focus on newly issued/renewed licenses

Cloud Run config: 2 vCPU, 2GB RAM (Playwright needs it), 30min timeout
Triggered by Cloud Scheduler: rotating daily schedule
```

### STEP 4: ETL Pipeline (Days 10-12)

**Prompt for Claude Code:**

```
Build the ETL pipeline that normalizes, deduplicates, classifies, and stores 
all ingested data into Firestore.

Requirements:

1. NORMALIZER (normalizer.py):
   - Accept raw data from Cloud Storage (permits, bids, licenses)
   - Standardize addresses using USPS format
   - Parse contractor names: "SMITH PLUMBING LLC" → { "name": "Smith Plumbing", "entity_type": "LLC" }
   - Normalize phone numbers to E.164 format
   - Classify trade from description using keyword matching:
     
     TRADE_KEYWORDS = {
       "ELECTRICAL": ["electrical", "wiring", "circuit", "panel", "conduit", "voltage"],
       "PLUMBING": ["plumbing", "pipe", "water heater", "sewer", "drain", "fixture"],
       "HVAC": ["hvac", "heating", "cooling", "air conditioning", "duct", "furnace"],
       "ROOFING": ["roof", "shingle", "gutter", "flashing"],
       "CONCRETE": ["concrete", "foundation", "slab", "masonry", "block"],
       "FRAMING": ["framing", "structural", "carpentry", "lumber"],
       "DRYWALL": ["drywall", "plaster", "insulation", "acoustical"],
       "PAINTING": ["painting", "coating", "wallpaper", "finishing"],
       "GENERAL": ["general", "remodel", "renovation", "addition", "new construction"],
       ...
     }

2. DEDUPLICATOR (deduplicator.py):
   - Match permits from different sources that reference the same project
   - Match contractors across permits and license databases
   - Use fuzzy matching on business name + address:
     - Exact license number match → 100% confidence
     - Name similarity (Jaro-Winkler > 0.85) + same city → 90% confidence  
     - Name similarity + same zip → 85% confidence
   - Create a unified contractor profile linking all their permits + licenses

3. LEAD SCORER (scorer.py):
   - Score each lead (permit/bid) based on:
     - Project value (higher = better): $0-50K=1, $50-200K=3, $200K+=5
     - Recency (newer = better): <7d=5, <30d=3, <90d=1
     - Trade match specificity: exact match=5, related=3, general=1
     - Contact completeness: phone+email=5, phone only=3, name only=1
     - Competition level: fewer contractors listed = better opportunity

4. FIRESTORE STORAGE (stay within 1 GB / 50K reads/day):
   
   Collection: "leads" (primary — the permit/bid opportunities)
   Document structure (optimized for size):
   {
     "id": "sha256-hash-of-key-fields",
     "type": "permit|bid",
     "trade": "ELECTRICAL",
     "title": "Commercial electrical renovation...",
     "value": 150000,
     "addr": "123 Main St, Houston, TX 77001",
     "geo": GeoPoint(29.76, -95.37),
     "owner": { "n": "ABC Corp", "p": "713-555-1234", "e": "..." },
     "gc": { "n": "Smith GC", "p": "...", "lic": "..." },
     "status": "active",
     "posted": Timestamp,
     "deadline": Timestamp,  // for bids
     "score": 78,
     "src": "houston-djnh-at8a",
     "updated": Timestamp
   }
   
   Collection: "contractors" (enriched contractor profiles)
   {
     "id": "normalized-name-state-hash",
     "name": "Smith Electrical LLC",
     "trades": ["ELECTRICAL"],
     "licenses": [{ "state": "TX", "num": "...", "type": "...", "exp": "..." }],
     "addr": "...",
     "phone": "...",
     "email": "...",
     "website": "...",
     "permit_count": 47,
     "avg_project_value": 125000,
     "active_since": "2018",
     "last_permit": Timestamp,
     "rating": null  // can enrich later from Google
   }
   
   Collection: "ingestion_state" (tracking)
   {
     "source_id": "chicago-ydr8-5enu",
     "last_run": Timestamp,
     "last_record_date": "2026-02-27",
     "records_ingested": 1523,
     "errors": 0
   }

   IMPORTANT SIZE MANAGEMENT:
   - Use short field names (n, p, e, addr) to save bytes
   - Don't store raw_data in Firestore — keep in Cloud Storage
   - Target < 2KB per lead document, < 1KB per contractor
   - At 2KB/doc, 1GB = ~500K leads = plenty for MVP
   - Use compound queries to minimize reads
   - Cache frequent queries in the API layer

Cloud Run config: 1 vCPU, 1GB RAM, 15min timeout
Triggered by: HTTP POST from ingesters after they complete
```

### STEP 5: API Server + Frontend (Days 12-18)

**Prompt for Claude Code:**

```
Build the API server (FastAPI) and a React frontend for the lead gen MVP.

API ENDPOINTS:

1. GET /api/leads
   - Query params: trade, state, city, zip, min_value, max_value, 
     posted_after, status, sort_by, limit, offset
   - Returns paginated leads with score
   - Uses Firestore compound queries
   - CACHE responses for 1 hour in memory (dict-based, not Redis)
   
2. GET /api/leads/{id}
   - Full lead details including contacts
   
3. GET /api/search?q=...
   - Full-text search across leads and contractors
   - Use Firestore array-contains for keyword matching
   - Store searchable keywords as array field in documents
   
4. GET /api/contractors
   - Browse/search contractor database
   - Filter by trade, state, license status
   
5. GET /api/contractors/{id}
   - Full contractor profile with permit history
   
6. GET /api/dashboard
   - Stats: total leads, by trade, by state, by value range
   - New leads today/this week
   - Hot markets (highest permit volume)
   
7. POST /api/alerts
   - Create email alerts for new leads matching criteria
   - Store in Firestore collection "alerts"
   
8. GET /api/markets/{state}
   - Market overview: permit trends, top contractors, avg values

FRONTEND (React + Tailwind — built into static and served from Cloud Run):

Pages:
1. Dashboard — overview with stats cards, charts, recent leads
2. Lead Browser — filterable, sortable table of leads
3. Lead Detail — full information with map, contacts, similar leads
4. Contractor Directory — searchable contractor database
5. Contractor Profile — full profile with permit history
6. Market Maps — heatmap of construction activity by zip code
7. Alerts — set up automated notifications

Build as a single-page React app using:
- React 18 + React Router
- Tailwind CSS (via CDN for simplicity)
- Recharts for charts
- Leaflet/OpenStreetMap for maps (FREE, no API key needed)
- Build with Vite, output static files to /frontend/dist/
- FastAPI serves static files from that dist folder

Docker: Single container running FastAPI that serves both API + static frontend
Cloud Run: 1 vCPU, 512MB RAM, concurrency 80, min instances 0
```

### STEP 6: Deployment & Scheduling (Days 18-20)

**Prompt for Claude Code:**

```
Set up CI/CD and scheduling for the entire system.

1. cloudbuild.yaml — builds and deploys all 4 Cloud Run services
2. Cloud Scheduler jobs (3 free):
   
   Job 1: "daily-permits" 
   - Schedule: 0 5 * * * (5am CT daily)
   - Target: POST https://permit-ingester-xxxx.run.app/ingest
   - Body: {"mode": "incremental"}
   
   Job 2: "daily-bids"
   - Schedule: 0 6 * * * (6am CT daily)
   - Target: POST https://bid-ingester-xxxx.run.app/ingest
   - Body: {"mode": "incremental"}
   
   Job 3: "daily-scrape" 
   - Schedule: 0 2 * * * (2am CT daily — overnight for scraping)
   - Target: POST https://license-scraper-xxxx.run.app/scrape
   - Body: {"day_of_month": auto}  
   - Rotates through states: Day 1=CA, Day 2=TX, Day 3=FL, etc.

3. Monitoring:
   - Cloud Run built-in metrics (free)
   - Set up error alerting to email
   - Log scraping success/failure rates

4. Cost guard:
   - Set Cloud Run max-instances=2 per service
   - Set billing alerts at $1, $5, $10
   - Ensure all services in us-central1

5. Custom domain (optional):
   - Map a domain to the api-server Cloud Run service
   - Free SSL via Cloud Run managed certificates
```

---

## 4. FIRESTORE DATA BUDGET ANALYSIS

Staying within 50K reads/day and 20K writes/day:

| Operation | Daily Volume | Free Limit | Status |
|-----------|-------------|------------|--------|
| **Writes: Permit ingestion** | ~500-2,000 new permits/day across all sources | 20K/day | ✅ Safe |
| **Writes: Bid ingestion** | ~50-200 new bids/day | (shared) | ✅ Safe |
| **Writes: License updates** | ~200-500/day (1 state rotation) | (shared) | ✅ Safe |
| **Writes: Ingestion state** | ~30/day (1 per source) | (shared) | ✅ Safe |
| **Reads: API queries** | ~200-500 queries × ~20 docs each = 4K-10K | 50K/day | ✅ Safe |
| **Reads: Dashboard stats** | Cache in memory, refresh hourly = ~50 reads/hour | (shared) | ✅ Safe |
| **Reads: ETL dedup checks** | ~2,000/day | (shared) | ✅ Safe |
| **TOTAL WRITES** | ~3,000-5,000/day | 20,000 | ✅ 15-25% of limit |
| **TOTAL READS** | ~10,000-15,000/day | 50,000 | ✅ 20-30% of limit |

**Storage (1 GB limit):**
- 500K lead documents × 2KB avg = 1 GB
- Strategy: Archive leads older than 90 days to Cloud Storage (5 GB free)
- Keep only active/recent leads in Firestore

---

## 5. COVERAGE STRATEGY — "EVERY CITY IN USA"

**Realistic coverage approach:**

| Tier | Cities | Coverage Method | Population Covered |
|------|--------|----------------|-------------------|
| **Tier 1** | Top 25 Socrata cities (NYC, Chicago, LA, Houston, etc.) | Direct SODA API | ~35% of US population |
| **Tier 2** | Additional 25-50 cities with open data portals (ArcGIS, custom) | Custom scrapers per platform | +15% (total ~50%) |
| **Tier 3** | State-level permit aggregation (Census data) | Census Building Permits Survey | ~100% (aggregate only) |
| **Tier 4** | Federal construction bids (all US) | SAM.gov API | 100% of federal work |
| **Tier 5** | Contractor database (15 states) | State license scraping | ~70% of US contractors |

**Total MVP coverage: ~50% of US construction permits at project level, 100% of federal bids, ~70% of licensed contractors.**

For truly "every city" — that requires either:
1. **Shovels.ai ($599/mo)** — covers 85% via their aggregation
2. **Building your own scraper network** for 200+ individual city portals over 6-12 months
3. **Hybrid** — use Census aggregate data to identify HOT markets, then build scrapers for those specific cities

---

## 6. SCRAPING BEST PRACTICES FOR CLAUDE CODE

```
When building scrapers, follow these rules:

1. ALWAYS respect robots.txt — check before scraping
2. Set User-Agent to identify yourself: "LeadGenMVP/1.0 (research@yourdomin.com)"
3. Rate limiting: minimum 2-3 seconds between requests to same domain
4. Error handling: retry 3x with exponential backoff, then skip
5. Data validation: every scraped record must pass Pydantic schema validation
6. Logging: log every scrape attempt with source, records found, errors
7. Idempotency: if same data is scraped twice, don't create duplicates
8. Session management: for ASP.NET sites, maintain session cookies/viewstate
9. Proxy: NOT needed for government sites (they're public, not blocking)
10. Storage: raw HTML/JSON goes to Cloud Storage, parsed data to Firestore
11. Monitoring: track scraper health — if a source breaks, alert immediately
12. Legal: ONLY scrape publicly accessible government data, no login-walls
```

---

## 7. 20-DAY BUILD TIMELINE

| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | GCP project setup, Firestore, Cloud Storage, Secret Manager | Infrastructure ready |
| 2-3 | Permit ingester — Socrata integration for top 10 cities | Pulling live permit data |
| 4-5 | Permit ingester — expand to all 25+ Socrata cities, normalize | Full Socrata coverage |
| 5-6 | Bid ingester — SAM.gov integration | Federal bids flowing |
| 6-7 | Bid ingester — USASpending + Census data | Complete federal data |
| 7-9 | License scraper — California CSLB + Texas TDLR | 2 biggest state DBs |
| 10-11 | License scraper — Florida + 2-3 more states | 5 state coverage |
| 10-12 | ETL pipeline — normalizer + deduplicator + scorer | Clean data in Firestore |
| 12-14 | API server — FastAPI endpoints | Working REST API |
| 15-17 | Frontend — React dashboard, lead browser, search | Usable web UI |
| 18-19 | Deployment — Cloud Run, Scheduler, CI/CD | Running in production |
| 20 | Testing, monitoring, billing alerts | Production-ready MVP |

---

## 8. COST SUMMARY

| Item | Monthly Cost |
|------|-------------|
| GCP Cloud Run (free tier) | $0 |
| GCP Firestore (free tier) | $0 |
| GCP Cloud Storage (free tier) | $0 |
| GCP Cloud Scheduler (3 jobs) | $0 |
| SAM.gov API | $0 |
| Socrata APIs (all cities) | $0 |
| Census API | $0 |
| State license scraping | $0 |
| Custom domain (optional) | ~$12/year |
| **TOTAL** | **$0 - $1/month** |

The only scenario you'd exceed free tier is if the API server gets heavy traffic (>2M requests/month) or Firestore gets hammered with reads (>50K/day). Both are solvable with caching.
