# Configuration Guide — What You Need to Set Up

This document lists everything that requires external accounts or API keys.  
Everything in this section is optional for local development but required for production.

---

## 1. 🔐 Firebase Auth (User Accounts) — **HIGH PRIORITY**

**Why:** Currently the pipeline CRM uses email via localStorage (no real auth). Firebase Auth adds proper Google/email login.

**Steps:**
1. Go to [console.firebase.google.com](https://console.firebase.google.com)
2. Create a project (or use an existing one)
3. Go to **Authentication → Sign-in method** → Enable **Email/Password** and **Google**
4. Go to **Project Settings → General** → copy the **Web API Key** and **Project ID**
5. Go to **Project Settings → Service Accounts** → generate a new private key → save as `service-account.json`

**Add to `.env`:**
```bash
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_WEB_API_KEY=AIzaSy...
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

**Code location:** `services/api-server/` — add `firebase-admin` to requirements, create `auth_middleware.py` with:
```python
import firebase_admin
from firebase_admin import auth
# verify_id_token(token) on each request
```

---

## 2. 💳 Stripe (Subscription Billing) — **HIGH PRIORITY**

**Why:** The entire business model. Free/Pro/Growth/Enterprise tiers.

**Steps:**
1. Create account at [stripe.com](https://stripe.com)
2. Go to **Developers → API Keys** → copy **Publishable key** and **Secret key**
3. Create 3 products in Stripe Dashboard:
   - **Pro** — $49/month recurring
   - **Growth** — $149/month recurring  
   - **Enterprise** — $499/month recurring
4. Copy the **Price IDs** for each (starts with `price_...`)
5. Set up a **Webhook** endpoint: `https://your-domain/api/billing/webhook`
   - Events: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`

**Add to `.env`:**
```bash
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_PRO=price_...
STRIPE_PRICE_GROWTH=price_...
STRIPE_PRICE_ENTERPRISE=price_...
```

**Install:** `pip install stripe` (add to `services/api-server/requirements.txt`)

---

## 3. 📧 SendGrid or Resend (Email Alerts Delivery) — **HIGH PRIORITY**

**Why:** The alerts system saves preferences to Firestore but never actually sends emails. This is a 1-day implementation once you have a key.

**Option A — SendGrid (industry standard):**
1. Sign up at [sendgrid.com](https://sendgrid.com) — free tier: 100 emails/day
2. Go to **Settings → API Keys** → Create API Key (Full Access)
3. Verify your sender domain under **Settings → Sender Authentication**

**Option B — Resend (modern, simpler):**
1. Sign up at [resend.com](https://resend.com) — free tier: 3,000 emails/month
2. Go to **API Keys** → Create API Key
3. Add your domain under **Domains**

**Add to `.env`:**
```bash
# SendGrid:
SENDGRID_API_KEY=SG....
EMAIL_FROM=alerts@yourdomain.com

# OR Resend:
RESEND_API_KEY=re_...
EMAIL_FROM=alerts@yourdomain.com
```

**Code to implement:** `services/api-server/jobs/alert_delivery.py` — a cron job that:
1. Queries all active alerts from Firestore
2. For each alert, finds leads posted since `last_notified`
3. Sends a batched digest email
4. Updates `last_notified` timestamp

**Run daily via Cloud Scheduler:** `POST /api/internal/run-alert-delivery`

---

## 4. 🤖 Anthropic API (AI Lead Enrichment) — **MEDIUM PRIORITY**

**Why:** Parse messy permit descriptions into structured data, classify owner types, infer contact details. ~$0.002/lead with Claude Haiku.

**Steps:**
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Go to **API Keys** → Create Key

**Add to `.env`:**
```bash
ANTHROPIC_API_KEY=sk-ant-...
AI_ENRICHMENT_ENABLED=true
AI_ENRICHMENT_MODEL=claude-haiku-4-5  # cheapest, fast enough
```

**Code location:** `services/etl-pipeline/enricher.py` (create this file):
```python
import anthropic

client = anthropic.Anthropic()

async def enrich_permit_description(description: str) -> dict:
    """Extract structured data from messy permit text."""
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": f"""Extract structured data from this building permit description.
Return valid JSON only with these fields:
- project_type: new_build | renovation | repair | addition | compliance
- owner_type: residential | small_commercial | large_commercial | institutional | industrial
- units: number (null if not mentioned)
- sqft: number (null if not mentioned)
- key_materials: list of strings

Description: {description}"""
        }]
    )
    return json.loads(response.content[0].text)
```

---

## 5. 🗺️ Google Maps API (Geocoding + Map Display) — **MEDIUM PRIORITY**

**Why:** Better address → lat/lng geocoding for permits that don't include coordinates. Also enables proper map clustering.

**Steps:**
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Enable **Maps JavaScript API** and **Geocoding API**
3. Go to **APIs & Services → Credentials** → Create API Key
4. Restrict the key to your domain in production

**Add to `.env`:**
```bash
GOOGLE_MAPS_API_KEY=AIzaSy...
```

**Frontend:** Replace the placeholder Leaflet map in `MarketMaps.jsx` with Google Maps or use Leaflet with proper tile layers.

---

## 6. ☁️ Google Cloud Platform (Production Deployment) — **FOR LAUNCH**

**Why:** The whole project is designed to run on GCP free tier.

**Services needed:**
| Service | Free Tier | Purpose |
|---------|-----------|---------|
| Cloud Run | 2M requests/month | Host all 5 services |
| Firestore | 1GB storage, 50K reads/day | Main database |
| Cloud Storage | 5GB | Raw permit data files |
| Cloud Scheduler | 3 jobs/month free | Cron for ingesters |
| Cloud Pub/Sub | 10GB/month | ETL job queue |

**Steps:**
1. Create GCP project at [console.cloud.google.com](https://console.cloud.google.com)
2. Enable billing (required for Cloud Run, but free tier covers ~$0/month at low volume)
3. Enable APIs: Cloud Run, Firestore, Cloud Storage, Cloud Scheduler, Pub/Sub
4. Install `gcloud` CLI: `curl https://sdk.cloud.google.com | bash`
5. Authenticate: `gcloud auth login`
6. Deploy each service:
```bash
gcloud run deploy api-server \
  --source services/api-server \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "FIRESTORE_PROJECT_ID=your-project-id,..."
```

**Add production `.env` values:**
```bash
FIRESTORE_PROJECT_ID=your-gcp-project-id
GCS_BUCKET_NAME=your-project-permits-raw
STORAGE_BACKEND=gcs
ENVIRONMENT=production
```

---

## 7. 📊 Optional Integrations (Phase 3)

### Redis/Upstash (Multi-instance Cache)
- Sign up at [upstash.com](https://upstash.com) — free tier: 10K requests/day
- Replace `TTLCache` with Redis cache when scaling beyond 1 Cloud Run instance
```bash
REDIS_URL=rediss://default:...@...upstash.io:6379
```

### Twilio (Phone Validation)
- Validate phone numbers from permits before showing in leads list
- Free: 250 lookups/month
```bash
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
```

### Sentry (Error Monitoring)
- Free tier: 5,000 errors/month
```bash
SENTRY_DSN=https://...@sentry.io/...
```

---

## Summary Table

| Service | Priority | Monthly Cost (prod) | Time to Set Up |
|---------|----------|---------------------|----------------|
| Firebase Auth | 🔴 High | Free | 30 min |
| Stripe | 🔴 High | 2.9% + $0.30/txn | 2 hours |
| SendGrid/Resend | 🔴 High | Free → $20/mo | 1 hour |
| GCP (Cloud Run + Firestore) | 🔴 High | ~$0-20/mo | 2 hours |
| Anthropic API | 🟡 Medium | ~$5-50/mo (usage) | 30 min |
| Google Maps | 🟡 Medium | Free → $7/1000 req | 30 min |
| Redis/Upstash | 🟢 Low | Free → $10/mo | 30 min |
| Twilio | 🟢 Low | Free → $0.005/lookup | 30 min |
| Sentry | 🟢 Low | Free | 15 min |
