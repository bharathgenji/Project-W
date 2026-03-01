# Project-W: Enhancement Analysis & Roadmap
_Compiled 2026-03-01 after full codebase review, local run, and market research_

---

## 1. Current State — What's Built

### ✅ Working & Solid
| Component | Status | Notes |
|-----------|--------|-------|
| Permit Ingester | ✅ Complete | 25+ Socrata portals, incremental sync, field mapping |
| Bid Ingester | ✅ Complete | SAM.gov, USASpending, Census BPS |
| ETL Pipeline | ✅ Complete | Normalize → classify → score → Firestore |
| License Scraper | ✅ Complete | 10 states (CA, TX, FL, NY, IL, PA, OH, AZ, WA, MN) |
| API Server | ✅ Complete | 7 endpoints: leads, search, contractors, dashboard, markets, alerts |
| React Frontend | ✅ Complete | Dashboard, Lead Browser, Contractor Directory, Market Maps, Alerts |
| Lead Scoring | ✅ Complete | 0-100 score: value + recency + contact + trade + competition |
| Trade Classification | ✅ Complete | Keyword + NAICS-based |
| Deduplication | ✅ Complete | Fuzzy name match + license number |
| Tests | ✅ 178 passing | Unit tests only; integration needs Firestore emulator |

### ⚠️ Partially Built
- **License Scraper Logic**: Playwright-based framework exists but actual page-interaction code is skeletal (California CSLB has the most complete implementation)
- **Frontend Map View**: `MapView.jsx` component exists but Leaflet integration is minimal — no actual permit pin clustering
- **Alerts**: Create/delete works; no email delivery job implemented yet

### ❌ Not Built (in plan but missing)
- Email delivery for alerts (no SendGrid/SMTP integration)
- BigQuery analytics export
- Authentication / user accounts
- Subscription/billing

---

## 2. Bugs Fixed in This Session

| # | Bug | Impact | Fix |
|---|-----|--------|-----|
| 1 | **Module import error** — `api-server`, `bid-ingester` etc. have hyphens, Python can't import them | **Critical** — Docker builds would fail at startup | Symlinks in all 5 Dockerfiles + local `services/` dir; Makefile auto-creates |
| 2 | **Makefile Windows-only** — `.venv/Scripts/pip` fails on Linux/Mac | **Critical** — CI and any non-Windows dev can't run tests | OS-detect with `ifeq(OS,Windows_NT)` |
| 3 | **Deprecated Firestore `.where()` API** — positional args deprecated in google-cloud-firestore 2.16+ | Medium — works but noisy, will break in future | Updated all 5 routers to `filter=FieldFilter(...)` |
| 4 | **`datetime.utcnow()` deprecated** — Python 3.14 removes it | Medium — 19 usages across 9 files | Replaced with `datetime.now(timezone.utc)`, fixed naive/aware mismatch |
| 5 | **Hot markets shows streets, not cities** — `addr.split(",")[0]` gets street on full addresses | Medium — bad dashboard UX | Fixed to take `parts[1]` for 3-part addresses |
| 6 | **Frontend bundle 802KB** — no code splitting | Low — slow initial load | Added `manualChunks` in vite.config.js → 5 chunks, 98KB main |

---

## 3. Near-Term Enhancements (Low-Effort, High-Impact)

### 3.1 Add Pagination Metadata to API
Currently `GET /api/leads` returns a list with no total count. Frontend can't show "1,234 results" or accurate pagination.

```python
# leads.py router — return envelope instead of bare list
return {
    "data": paginated,
    "total": len(results),  # in-memory total after filtering
    "offset": offset,
    "limit": limit,
    "has_more": len(results) > offset + limit,
}
```

### 3.2 Cache Invalidation Endpoint
Currently the only way to bust the 1-hour dashboard/market cache is to restart the server. A simple admin endpoint fixes this:

```python
@app.post("/api/admin/cache/clear")
def clear_cache(cache: TTLCache = Depends(get_cache)):
    cache.clear()
    return {"status": "cache cleared"}
```

### 3.3 `GET /api/leads/export` — CSV Export
Contractors need to export leads to spreadsheets, CRMs. One endpoint:
```python
@router.get("/export")
def export_leads_csv(trade: str | None = None, state: str | None = None, ...):
    # Returns StreamingResponse with text/csv
```

### 3.4 Complete the Email Alerts Job
Framework is there, delivery is missing. Simple fix:
- Add `sendgrid` or `resend` to requirements
- Add a cron job / Cloud Scheduler task that:
  1. Reads all active alerts from Firestore
  2. Queries leads posted since `last_notified` timestamp
  3. Groups matches by alert email
  4. Sends batched digest email

### 3.5 Fix `vite.config.js` Dev Proxy Port
Currently proxies `/api` to `:8080` (Docker port), but local dev runs on `:8000`/`:8005`. Developers running `npm run dev` get CORS errors:
```js
proxy: {
  '/api': {
    target: process.env.VITE_API_URL || 'http://localhost:8000',
    changeOrigin: true,
  },
},
```

### 3.6 Add Health Checks to All Services
Currently only `api-server` has `/api/health`. The other services (permit-ingester, etc.) have `/health` but it's not wired into docker-compose health checks.

---

## 4. Market-Driven Feature Enhancements

### 4.1 🔥 AI-Powered Lead Enrichment (HIGH PRIORITY)
**Market signal:** The construction tech market is exploding. Shovels.ai raised $6M in 2024. BuildZoom's value prop is contact enrichment. The #1 complaint from subcontractors using lead services is "I can't reach anyone."

**What to add:**
- **Phone validation**: Validate phone numbers against carrier lookup (Twilio Lookup API, free 250/month)
- **Email validation**: Use `mailvalidator` or ZeroBounce to verify emails before alerting
- **Google Business lookup**: Cross-reference contractor/owner name + city against Google Places API to get website, rating, real phone
- **LinkedIn scraping**: Many GCs have LinkedIn; `linkedin_url` field on contractor profile
- **Domain inference**: "Smith Construction LLC Houston TX" → try `smithconstructionhouston.com`, etc.

```python
# New: shared/enrichment.py
async def enrich_lead(lead: dict) -> dict:
    """Try to fill in missing contact info from public sources."""
    if not lead["owner"]["e"] and lead["owner"]["n"]:
        lead["owner"]["e"] = await lookup_email_from_name_city(
            lead["owner"]["n"], extract_city(lead["addr"])
        )
    if not lead["gc"]["p"] and lead["gc"]["lic"]:
        lead["gc"]["p"] = await lookup_phone_from_license(lead["gc"]["lic"])
    return lead
```

### 4.2 🔥 Contractor Outreach CRM (HIGH PRIORITY)
**Market signal:** Most subcontractors don't have a CRM. They find a lead, call once, forget about it. The "sticky" feature that drives retention.

**What to add:**
- `POST /api/leads/{id}/save` — bookmark a lead to user's pipeline
- `POST /api/leads/{id}/notes` — add notes (called, left voicemail, etc.)
- `GET /api/pipeline` — user's saved leads with status
- Lead status enum: `NEW → CONTACTED → PROPOSAL → WON/LOST`
- This requires user auth (see 4.6)

### 4.3 ⚡ Real-Time WebSocket Alerts
**Market signal:** In fast-moving markets (electrical after a hurricane, roofing after hail storms), timing matters. An email digest is too slow.

**What to add:**
- FastAPI WebSocket endpoint: `WS /api/ws/alerts/{user_id}`
- When ETL pipeline stores a new lead that matches a user alert, push immediately
- Frontend: toast notification + badge on lead browser

```python
# New: services/api-server/websocket.py
from fastapi import WebSocket
active_connections: dict[str, WebSocket] = {}

@app.websocket("/api/ws/alerts/{user_id}")
async def alert_websocket(websocket: WebSocket, user_id: str):
    await websocket.accept()
    active_connections[user_id] = websocket
    # ETL pipeline POSTs to /api/internal/notify when new match found
```

### 4.4 📊 Market Intelligence Dashboard
**Market signal:** Contractors aren't just looking for leads — they want to know if Houston is slowing down, if LA electrical is hot, if their competition is growing. This is a premium upsell.

**What to add:**
- **Permit velocity charts**: Permit count per week by city, filterable by trade
- **Average project value trends**: Is commercial roofing getting more expensive?
- **Contractor density maps**: How saturated is each market by trade?
- **Permit-to-award ratio**: What % of permits result in GC bids on SAM.gov?
- **Seasonal patterns**: "Roofing spikes in April in TX (hail season)"

Backend additions:
```python
# New endpoint: GET /api/analytics/trends
# Aggregates leads by week/month, returns time series
# Store aggregates in Firestore collection: "analytics_snapshots"
```

### 4.5 🗺️ Fix & Enhance Market Maps
The current `MarketMaps.jsx` uses Leaflet but has no actual data — it's a shell. This is one of the most visually compelling features.

**What to add:**
- Permit heatmap by zip code using choropleth (Leaflet's GeoJSON layer)
- Cluster markers for individual permits (drill-down from zip to street)
- Layer toggles: permits / bids / contractors
- "Hot zip" score combining permit volume + avg value + low contractor density
- US zip code GeoJSON is freely available from Census TIGER data

### 4.6 🔐 User Auth + Subscription Tiers
**Market signal:** This is the monetization engine. Without auth, you can't track usage, limit access, or charge.

**Implementation:**
- Auth: Use [Supabase Auth](https://supabase.com/auth) (free tier, supports Google/email)
  - Or: Firebase Auth (already using Firebase stack)
- Tiers:
  | Tier | Price | Limits |
  |------|-------|--------|
  | Free | $0 | 10 leads/day, no export, no alerts |
  | Pro | $49/mo | 500 leads/day, CSV export, email alerts |
  | Team | $149/mo | Unlimited, API access, 5 seats, CRM features |
- Store `user_id` + `tier` in Firestore `users` collection
- Add `Depends(get_current_user)` to all routers
- Rate limit via `slowapi` + user tier

### 4.7 📱 Mobile-Responsive Improvements
The current frontend is desktop-first. On mobile, the lead table is unreadable.

**What to add:**
- Card view mode for mobile (already have `LeadCard.jsx` — just use it on mobile)
- Swipe gestures to save/skip leads (Tinder-style for speed)
- "Click to call" on phone numbers (mobile browsers handle `tel:` links)
- PWA manifest so contractors can "install" it on their phone

### 4.8 🏗️ Expand Data Sources — Current Gaps

**High-value sources not yet covered:**

| Source | What | Why | Effort |
|--------|------|-----|--------|
| **Dodge Data & Analytics** | Pre-bid project leads, architect drawings | Industry standard — early signal | 💰 Paid ($200+/mo) |
| **PlanHub / BuildingConnected** | GC-to-sub bidding platforms | Direct bid invitations | Medium scrape |
| **State DOT bid boards** | Road/infrastructure bids | Big $$ for concrete/civil | Medium (50 states) |
| **ArcGIS permit portals** | Philadelphia, Phoenix, etc. | Fills Socrata gaps | Medium (custom per city) |
| **Granicus/Legistar** | Planning commission agendas | 60-day early signal before permits | Hard (PDF parsing) |
| **Code violation databases** | Code enforcement portals | Property needing repair = lead | Medium |
| **FEMA flood damage** | Post-disaster housing data | Hurricane/flood remediation | Easy (FEMA API) |

**Immediate low-effort wins:**
```yaml
# Add to sources.yaml — confirmed working Socrata portals not yet in the list:
- id: washington-dc
  domain: opendata.dc.gov
  dataset_id: awjx-nebs
  state: DC
  priority: high

- id: nashville
  domain: data.nashville.gov
  dataset_id: 3h5w-q8b7
  state: TN
  priority: high

- id: miami-dade
  domain: opendata.miamidade.gov
  dataset_id: dv5p-i7yv
  state: FL
  priority: high
```

### 4.9 🤖 AI-Powered Lead Qualification (2026 Must-Have)
**Market signal:** Every SaaS in construction is adding AI in 2026. The opportunity is genuine — permit descriptions are noisy and AI can extract what matters.

**What to add:**
- **Permit description parsing**: Use Claude claude-haiku-4 to extract from messy city data:
  - "demo existing & install 3-ton 16-SEER split system w/new ductwork" → `{units: 1, system_type: "split", tonnage: 3, ductwork: true}`
  - Structured JSON extraction enables better filtering ("find all 3+ ton HVAC jobs")
- **Project intent classifier**: Is this a new build, renovation, repair, or compliance fix? Different sales approaches for each.
- **Owner type classifier**: Residential homeowner vs. small commercial vs. institutional — affects pricing
- **Competitive intelligence**: Parse contractor names from permits to build win/loss patterns ("Smith Electric wins 60% of Houston commercial electrical > $100K")

Implementation (cheap with Haiku):
```python
# ETL pipeline addition — costs ~$0.002 per lead enriched
async def ai_enrich_permit(raw_description: str) -> dict:
    response = await anthropic_client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": f"Extract structured data from this permit description. Return JSON only.\n\n{raw_description}"
        }]
    )
    return json.loads(response.content[0].text)
```

---

## 5. Architectural Improvements

### 5.1 Replace In-Memory Cache with Redis
The current `TTLCache` is an in-memory dict. Fine for single-instance but breaks when:
- Running multiple Cloud Run instances (each has separate cache)
- Deploying updates (cache lost on restart)

Redis via Upstash (free tier: 10,000 requests/day) solves this.

### 5.2 Add Firestore Composite Indexes
Several queries do in-memory filtering because Firestore requires composite indexes for multi-field queries. These should be defined in `firestore.indexes.json`:

```json
{
  "indexes": [
    {
      "collectionGroup": "leads",
      "fields": [
        {"fieldPath": "trade", "order": "ASCENDING"},
        {"fieldPath": "score", "order": "DESCENDING"}
      ]
    },
    {
      "collectionGroup": "leads",
      "fields": [
        {"fieldPath": "status", "order": "ASCENDING"},
        {"fieldPath": "posted", "order": "DESCENDING"}
      ]
    }
  ]
}
```

### 5.3 Background Job Queue
Currently ETL is triggered synchronously by ingesters. For large batches, this can timeout. Add a proper job queue:
- **Lightweight option**: Keep ARQ (already used in PlanLedger) with Redis
- **GCP native**: Cloud Tasks (free tier: 1M tasks/month)

### 5.4 Pub/Sub Instead of HTTP Triggers
The ingesters directly HTTP-POST the ETL pipeline URL. If ETL is slow or down, permits are lost. Use Cloud Pub/Sub instead:
- Ingester publishes to `permits-raw` topic
- ETL subscribes — guaranteed delivery, automatic retry

---

## 6. Revenue Model Analysis

Based on comparable tools in the market:

| Competitor | Price | Differentiation |
|-----------|-------|----------------|
| Shovels.ai | $199-599/mo | Broadest coverage, API-first |
| BuildZoom Pro | $299/mo | GC focus, project history |
| Dodge Data | $500+/mo | Earliest signal (pre-permit) |
| ConstructConnect | $300+/mo | Large enterprise |
| **Project-W** | **$49-149/mo** | **Sub-contractor focused, cheap** |

**Recommended pricing:**
- Free: 10 leads/day (acquisition funnel)
- Pro ($49/mo): 500 leads/day, email alerts, CSV export
- Growth ($149/mo): Unlimited, API, CRM pipeline, 5 seats
- Enterprise ($499/mo): White-label, custom data sources, dedicated support

**Estimated revenue potential:**
- 1,000 Pro subs = $49K MRR
- 200 Growth subs = $30K MRR
- 20 Enterprise = $10K MRR
- **Target: $89K MRR within 18 months** (aggressive but achievable in a $1.8T market)

---

## 7. Priority Roadmap

### Phase 1 — Make It Sellable (2-3 weeks)
1. ✅ Fix all 6 bugs (done this session)
2. User auth (Firebase Auth — 2 days)
3. Subscription tiers with rate limiting (Stripe + slowapi — 3 days)
4. Email alerts delivery (SendGrid — 1 day)
5. CSV export (1 day)
6. Fix Leaflet map with real permit pins (2 days)
7. Add 3 more Socrata cities (DC, Nashville, Miami-Dade) (1 day)

### Phase 2 — Make It Sticky (3-4 weeks)
1. Lead pipeline CRM (save + notes + status) (3 days)
2. AI enrichment with Claude Haiku (2 days)
3. WebSocket real-time alerts (2 days)
4. Mobile-responsive card view (1 day)
5. Firestore composite indexes (1 day)
6. Pagination metadata in API (1 day)

### Phase 3 — Make It Scale (4-6 weeks)
1. Analytics/trends dashboard with charts (4 days)
2. More license scraper states (PA, OH, GA, AZ, WA) (3 days)
3. Redis cache (1 day)
4. Cloud Pub/Sub for ETL (2 days)
5. ArcGIS source adapters for uncovered cities (5 days)
6. FEMA disaster leads integration (1 day)

---

## 8. Quick Wins You Can Do Today

1. **Deploy to Cloud Run** — the GCP setup is already designed for free tier; just needs `gcloud run deploy`
2. **Add 3 more cities** to `sources.yaml` — DC, Nashville, Miami-Dade are confirmed working
3. **Run the permit ingester** against real Austin/Chicago APIs — instant real data
4. **Register SAM.gov API key** and run the bid ingester — free federal leads immediately
5. **Add a `/api/leads/export` CSV endpoint** — 30 lines of code, massive user value
