# BuildScope — Pitch Script & FAQ Guide

**Use this for:** cold outreach calls, association demos, trade show conversations,
beta user onboarding, and investor questions.

---

## THE OPENING (30-second version)

> "BuildScope pulls every building permit filed in your city — daily — and turns
> them into qualified leads for your trade. So instead of waiting for a GC to call
> you, you call them first. We cover 12 major US cities right now, 5,000+ active
> permits, and it takes about 5 minutes to get set up."

**Longer version (for a warm call or intro meeting):**

> "Most subcontractors find out about a new job one of two ways: a GC they already
> know calls them, or they stumble across it. Both are reactive. BuildScope makes
> you proactive. Every day, city governments publish building permits — who's
> building, what kind of work, the address, the project value. That's public
> information, but it's buried in government databases. We pull it, clean it,
> classify it by trade, and surface the ones that are relevant to you. You wake up,
> open your dashboard, and see every electrical / plumbing / HVAC / roofing job
> that was permitted in your market yesterday."

---

## PART 1 — NON-TECHNICAL QUESTIONS

---

### "What exactly is a building permit, and why does it matter to me?"

When a property owner or general contractor plans to do construction work —
new build, addition, renovation, major HVAC replacement — they have to file a
permit with the city before work starts. That permit lists:

- The address
- The type of work
- The estimated project value
- Often the owner's name and the GC on record

That permit is filed **before** the work begins. That means you have a window —
sometimes weeks — to reach the GC or owner before they've locked in a sub.
BuildScope surfaces that window every single day.

---

### "How is this different from just Googling for jobs?"

Google shows you job boards — which are either GC-controlled (they post when they
want you to bid) or consumer platforms (Angi, HomeAdvisor) where you're one of
10 contractors bidding on the same small job.

BuildScope shows you permits that were just filed — often before the GC has even
started calling subs. You're not responding to a listing; you're showing up
**before the listing exists.**

---

### "I already get plenty of work through referrals. Why do I need this?"

Referrals are great — until they dry up. One slow quarter, one GC relationship
that goes cold, one big job that ends with no follow-on work. BuildScope isn't a
replacement for your network; it's insurance and growth on top of it.

Also — referrals are reactive. Someone has to think of you. With BuildScope, you
decide which projects to chase and when. You're in control of your own pipeline.

---

### "I don't have time to chase leads. I'm already busy."

Two things:

1. The best time to build your pipeline is when you're busy — because by the time
   you need the work, the opportunity will be gone. Permits filed today are jobs
   starting in 4–12 weeks.

2. BuildScope takes about 10 minutes a day. Filter by your trade, your city, your
   minimum project value. You're not doing research — the research is done for you.
   You're just deciding which ones to call.

---

### "What cities do you cover?"

Currently live: **Nashville, Los Angeles, Austin, Chicago, Seattle, San Francisco,
Boston, New York City, Dallas, San Antonio, Denver, Miami-Dade, Portland.**

Plus federal bids nationwide from SAM.gov and USASpending.gov.

We're adding cities continuously — if your city isn't listed, tell us and we'll
prioritize it.

---

### "What trades does it cover?"

Electrical, Plumbing, HVAC/Mechanical, Roofing, Concrete/Foundation, Framing,
General Construction, Demolition, Fire Protection, Flooring, Drywall, Painting,
Windows & Doors, Site Work, Solar, Signage.

Every permit is automatically classified by trade — you only see leads relevant
to your work.

---

### "How much does it cost?"

We're in beta right now — **free for the first 60 days**, no credit card required.

After beta, pricing will be **$49–$149/month** depending on the number of cities
and features. Beta users lock in founder pricing — whatever tier they're on at
launch, they keep for life.

To put that in perspective: one electrical rough-in on a new build is $8,000–
$25,000. One lead that converts pays for 2–3 years of BuildScope.

---

### "How do I actually use it?"

1. Sign up (email only, no credit card)
2. Set your trade and cities
3. Open your dashboard — leads are sorted by score (a combination of project
   value, recency, and permit type)
4. Click any lead to see full details: address, project type, owner info, GC on
   record, estimated value, when it was filed
5. Save leads to your pipeline (Kanban board: New → Contacted → Proposal Sent →
   Won / Lost)
6. Set up email alerts so new high-value permits hit your inbox the morning
   they're filed

Total time to first lead: under 5 minutes.

---

### "What do I do once I find a lead?"

You reach out — ideally to the GC on record (if listed) or the property owner
directly. Here's a script that works:

> "Hi, my name is [Name] from [Your Company]. I saw you pulled a permit for
> [project type] at [address]. We specialize in [trade] in this area and wanted
> to introduce ourselves before your subs are locked in. Can I get 5 minutes?"

Early outreach = high response rate. Most subs call when the GC is already deep
into bidding. You're calling when they haven't started yet.

---

### "Will other subs be using this and calling the same leads?"

Yes, eventually — but right now you're one of the first. Early adopters get
months of lead time before this becomes standard practice. And even when it does,
the contractors who win are the ones who respond fastest and have the better
pitch — BuildScope just gets you to the conversation earlier.

---

### "What about federal bids? I've never done government work."

Federal bids are different from permits — they're formal solicitations, usually
larger ($500K–$50M), with a structured bid process. They're not for everyone,
but if you want to break into government work, these are the opportunities. We
show them filtered by construction NAICS codes so you only see relevant ones.

---

### "Is there a mobile app?"

Not yet — it's a web app, optimized for desktop and tablet. Mobile-friendly UI
is on the roadmap. For now, the email alert system means you don't need to open
the app every day — the important ones come to you.

---

### "What happens to my data? Do you sell it?"

No. Your account data (email, saved leads, pipeline) is never sold to third
parties. The permit data itself is public record — we're just organizing it.

---

## PART 2 — TECHNICAL QUESTIONS

---

### "Where does the permit data come from?"

Three sources:

1. **Socrata SODA APIs** — most major US cities publish permit data through
   Socrata's open data platform. We pull from 13 cities including Chicago, Austin,
   LA, Seattle, SF, NYC, Denver, Miami, Dallas, and Portland.

2. **ArcGIS FeatureServer APIs** — cities like Nashville and Portland use ArcGIS
   for their permit systems. We have a dedicated client for those.

3. **CKAN open data portals** — some cities (San Antonio, Boston) use CKAN. Same
   idea, different API format.

All three are official government APIs — real-time, authoritative data.

---

### "How fresh is the data? How often does it update?"

We run full ingestion daily. Most city permit APIs update within 24–48 hours of
a permit being filed. In practice, you're seeing permits that were filed 1–3
days ago.

For Nashville specifically (ArcGIS source), data is filed same-day. For busier
cities like LA and Chicago, there's sometimes a 48-hour processing lag on the
city's end before it appears in their API.

---

### "How do you classify permits by trade? What if it's wrong?"

We use a keyword-based classifier that looks at the permit description, permit
type, and NAICS code (for federal bids). It's trained on actual permit language
across all our source cities.

Accuracy is high for clear descriptions ("install new HVAC system" → HVAC,
"replace roof shingles" → ROOFING) and occasionally general for vague ones
("remodel existing space" → GENERAL). We show trade confidence scoring so you
can see how certain the classifier was.

If you see a misclassified permit, you can flag it — that feedback improves the
model.

---

### "What is the lead score? How is it calculated?"

Each lead gets a score from 0–100 based on:

- **Project value** (higher value = higher score)
- **Permit type** (new construction scores higher than minor alterations)
- **Recency** (filed this week scores higher than 6 weeks ago)
- **Data completeness** (owner/GC contact info available → higher score)
- **Federal bids** get a boost if they have a clear deadline

You can sort by score, value, or date. Score is the default because it balances
freshness with opportunity size.

---

### "How do you get owner and GC contact info?"

Contact info comes directly from the permit filing when available. Many permits
require the property owner and/or general contractor to list a phone number or
email. Not all cities require this, and not all filers provide complete info.

Coverage varies by city:
- Nashville: good GC contact data (~60% have a name, ~30% have phone)
- LA: owner info is spotty, GC info better for commercial permits
- Chicago: fairly complete on commercial, lighter on residential

Where contact info is missing, you can usually find the GC via their contractor
license (which we also track) or the property address via county records.

---

### "Can I export leads to my CRM?"

Yes — CSV export is available for any filtered lead set. We're working on direct
integrations with ServiceTitan, Jobber, and BuilderTrend. If you use something
else, tell us — integrations are driven by what beta users actually need.

---

### "How does the pipeline / CRM board work?"

It's a Kanban board with 5 stages: **New → Contacted → Proposal Sent → Won →
Lost.** You save a lead to your pipeline, move it through stages as you make
progress, add notes after each interaction. It's deliberately simple — not meant
to replace a full CRM, just to track the leads you're actively working.

---

### "Do you have an API so I can pull data into my own system?"

Not publicly documented yet, but the same REST API the web app uses is available.
During beta, if you want direct API access, reach out and we'll set you up with
a key. This is on the product roadmap for a post-launch feature.

---

### "Is the data GDPR / privacy compliant?"

The permit data we serve is public record — filed with government agencies and
available through official open data portals. There's no privacy concern with
surfacing this data.

For user account data (your email, saved leads, pipeline), we store it in
Firebase/Firestore with standard Google Cloud security. We don't collect anything
beyond what's needed to run the service.

---

### "What's your uptime / reliability?"

We run on GCP (Google Cloud Platform). The database is Firestore (Google's
managed NoSQL), which has 99.999% uptime SLA. The API and frontend are
containerized with Docker and can be scaled horizontally.

During beta we're transparent about this: you may see occasional downtime during
deploys or if a city API changes its format. We fix issues within hours, not
days. You'll always be told.

---

### "What happens when a city changes their API?"

It happens — cities update field names, switch platforms, add pagination. We
monitor ingestion runs daily and get alerts when a source drops to zero records.
Typical fix time is under 24 hours. We currently cover 3 API formats (Socrata,
ArcGIS, CKAN) and have built enough abstraction that most changes are a config
update, not a code rewrite.

---

### "How do you handle duplicate permits?"

We generate a deterministic ID from the source portal + permit number. If the
same permit is re-published (cities sometimes republish updated records), the
new record overwrites the existing one — it doesn't create a duplicate lead.
The deduplication runs at the ETL layer before anything hits Firestore.

---

## PART 3 — HARD / SKEPTICAL QUESTIONS

---

### "I tried a lead service before and the leads were garbage."

That's fair. Most lead services sell the same lead to 5–10 contractors, or the
data is weeks old by the time you see it. BuildScope is different in two ways:

1. The data is raw government permit filings — it's not curated or sold by
   anyone else. You're seeing it the same day we pull it.
2. We don't sell leads to your competitors. You find them on your own. It's
   intelligence, not a lead marketplace.

---

### "Isn't this just public data I could look up myself?"

Yes, technically. The city permit portals are public. The problem is they're
designed for compliance, not for sales prospecting. They're clunky, don't cover
multiple cities in one view, have no trade filtering, no scoring, no alerts,
no CRM, and require you to know the right portal for each city. BuildScope turns
10+ hours of weekly research into a 10-minute daily check.

---

### "How do you make money if it's free right now?"

Beta is free because we want feedback more than revenue right now. Post-launch
it's $49–$149/month. The business model is simple: contractors get 10x their
subscription cost in one job, so churn is low and word-of-mouth is strong.

---

### "What if I'm in a city you don't cover?"

Tell us. City prioritization for the next expansion phase is driven by what
beta users ask for. If you have 5 subs in Phoenix all asking for it, Phoenix
is next.

---

### "I only do residential. Are the permits useful for me?"

Yes — residential permits are the majority of our volume in most cities.
Nashville, Portland, Austin are heavily residential. A new single-family home
requires electrical, plumbing, HVAC, framing, roofing — all from separate subs.
You can filter to residential only and by minimum project value.

---

### "What's the catch?"

Honestly? The contact info isn't complete on every permit. Some permits just
say "owner: John Smith" with no phone. You'll still need to do some digging —
county tax records, LinkedIn, GC license lookup. We're improving contact
enrichment, but we'll never pretend it's a one-click dial. It's intelligence
that gets you to the right conversation faster, not a magic dial button.

---

### "Are you going to raise prices once I'm hooked?"

Beta users get founder pricing — locked in at whatever rate you're paying when
we go live. That's in writing. We'd rather have 200 contractors paying $49/month
forever who love us than churn through people every 90 days.

---

### "What's your team? Why should I trust you?"

[Customize with your own background. Template:]

> "I've been in [background] for [X] years. I built this because I kept hearing
> from subcontractors that the biggest problem wasn't the work — it was finding
> the work. The permit data has always been public. Nobody had connected it to a
> useful sales tool for subs. That's what BuildScope is."

---

## PART 4 — CLOSING / NEXT STEPS

---

### "Okay I'm interested. What does signing up look like?"

1. Go to [your URL]
2. Enter your email — that's it to start
3. Set your trade and cities
4. You're looking at leads in under 5 minutes
5. I'll personally check in with you after 2 weeks to see what's working

No credit card. No sales call. Just the product.

---

### "What do you need from me as a beta user?"

Three things:
1. Use it for at least 30 days before forming an opinion
2. Tell me what's confusing, broken, or missing — even small things
3. Let me know if you win a job from a BuildScope lead (that's the best feedback
   there is)

In exchange: free access, founder pricing at launch, and you'll have shaped what
the product becomes.

---

### One-liner closers by audience:

| Audience | Closer |
|---|---|
| Electrician | "Every permit in Nashville this week is a potential rough-in. You want to see them?" |
| Roofer (LA) | "There are 300+ wildfire rebuild permits filed in LA county right now. You want the list?" |
| HVAC | "New construction HVAC in Austin: 250 permits in the last 14 days. Want me to pull them up?" |
| Association exec | "We'd like to offer your members 60 days free before we open to the public. No cost to you or them." |
| Skeptic | "Give me 5 minutes on the live dashboard. If you can't find one lead worth calling, I'll leave you alone." |

---

*Last updated: March 2026 | BuildScope beta*
