# 09 Scholar Engine Plan & Workflow
*Last Updated: 2026-03-25*

## Overview
This engine enriches `meddash_kols_db` with real-time Google Scholar citations, h-index, and i10-index metrics via SerpApi. To prevent writing incorrect metrics to the wrong researcher, a 4-tier identity verification system is applied before any data is committed to the database.

## API Provider: SerpApi
**Website:** [https://serpapi.com/google-scholar-api](https://serpapi.com/google-scholar-api)

**Cost Structure & API Limits:**
* **Free Tier:** 100 successful searches per month. *(Sandbox only.)*
* **Developer Plan:** $50/month for 5,000 successful searches.
* **Production Plan:** $130/month for 15,000 searches.

**Rate Mitigation Strategy:**
API queries fire **strictly On-Demand** when a user manually clicks `[Fetch Metrics]` in the Next.js Dashboard. The UI hard-locks the fetch trigger if the KOL's data is newer than 7 days. **No automated cron jobs.**

**API Architecture Constraint (1:1 Request Model):**
SerpApi requires exactly one API call per author for detailed metrics. There is no batch endpoint available.

---

## 4-Tier KOL Identity Disambiguation

Before any citations are committed to the database, the engine runs this tiered verification:

| Tier | Signal | Condition | Result |
|------|--------|-----------|--------|
| 1 | ORCID | ORCID in our DB appears in Scholar profile | ✅ Auto-Accept |
| 2 | Publications | ≥3 publication title overlaps (70% fuzzy match) | ✅ Auto-Accept |
| 3 | Institution + Specialty | Both affiliations AND research interests fuzzy match | ✅ Auto-Accept |
| 4 | None of above | All signals inconclusive | 🔍 Write to `scholar_review_queue` |

---

## PostgreSQL Tables (Supabase)

### `kol_scholar_metrics`
* `kol_id` (TEXT, Primary Key)
* `scholar_id` (TEXT, Unique)
* `total_citations` (Integer)
* `h_index` (Integer)
* `i10_index` (Integer)
* `last_updated_date` (Timestamp)

### `scholar_review_queue`
* `id` (SERIAL, Primary Key)
* `kol_id` (TEXT)
* `kol_name` (TEXT)
* `candidate_scholar_id` (TEXT)
* `candidate_name` / `candidate_affiliation` / `candidate_interests` (TEXT)
* `disambiguation_tier_failed` (TEXT)
* `confidence_score` (Integer)
* `reviewed` (Boolean, default false)
* `created_at` (Timestamp)

---

## Script Files

| File | Purpose |
|------|---------|
| `sync_scholar_citations.py` | Main engine: 4-tier disambiguation + upsert |
| `migrate_scholar.py` | Provisions `kol_scholar_metrics` in Supabase |
| `migrate_review_queue.py` | Provisions `scholar_review_queue` in Supabase |
| `kol_scholar_metrics_schema.sql` | SQL reference for `kol_scholar_metrics` |
| `scholar_review_queue_schema.sql` | SQL reference for `scholar_review_queue` |

---

## Required Environment Variables (`.env`)
```env
SERPAPI_KEY=your_api_key_here
SUPABASE_URI=your_supabase_uri
```
