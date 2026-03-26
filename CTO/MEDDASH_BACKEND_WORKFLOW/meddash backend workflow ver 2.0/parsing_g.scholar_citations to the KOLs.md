# Adding Google Scholar Citations to KOL Database

## Objective
To dynamically enrich our KOL PostgreSQL database with Google Scholar metrics (Total Citations, h-index, i10-index, and publication-specific citations) and establish a weekly automated pipeline to keep these metrics continuously updated for the Next.js UI.

## The Challenge with Google Scholar
Unlike PubMed or ClinicalTrials.gov, **Google Scholar does not have an official REST API** and aggressively blocks scraping attempts (IP bans/CAPTCHAs) when queried in bulk natively.

## Proposed Architectural Solution

### 1. Data Source Selection
We cannot use standard `requests` or `BeautifulSoup` directly due to CAPTCHAs. We have two viable paths:
* **Option A: Managed Third-Party API (Recommended)** 
  * Use **SerpApi (Google Scholar Search API)**. It handles proxy rotation, headless browsers, and CAPTCHA solving natively. We send it a name, it returns clean JSON with the Author ID and citation charts.
* **Option B: Open Source + Proxies**
  * Use the Python `scholarly` library combined with a paid rotating proxy service (e.g., BrightData). `scholarly` is excellent for extracting the exact data shapes we need but requires manual proxy management to avoid rate limits.

### 2. Matching & ID Extraction (The Bootstrap Phase)
To get the Google Scholar ID for our existing and future KOLs:
1. **Query Construction:** The Python script will pull the KOL's `first_name`, `last_name`, and `institution` from the `meddash_kols_db`.
2. **Search Execution:** It will query the Google Scholar Author Search (e.g., "John Doe Harvard").
3. **ID Extraction:** The API will return the top matched author profile. We extract their unique Google Scholar ID (the `user=` parameter in their profile URL).
4. **Validation:** We will cross-reference the author's listed interests or recent publications with our PubMed data to ensure a positive match.

### 3. Database Schema Upgrades (`meddash_kols_db`)
We will add a dedicated table to our Supabase PostgreSQL cluster to prevent bloating the core KOL table:

**Table: `kol_scholar_metrics`**
* `kol_id` (Foreign Key pointing to `meddash_kols`)
* `scholar_id` (String, Unique)
* `total_citations` (Integer)
* `h_index` (Integer)
* `i10_index` (Integer)
* `last_updated_date` (Timestamp)

### 4. On-Demand Fetching via Next.js UI (Rate Limit Avoidance)
To guarantee we do not accidentally exceed the SerpApi monthly limits (e.g., 100 free searches/month), we will **NOT** use automated weekly cron jobs. 
Instead, citations will be pulled strictly on-demand via the Phase 2 KOL dashboard UI.
1. **New Script:** `09_Scholar_Engine/sync_scholar_citations.py` (Exposed via FastAPI `/api/system/run`).
2. **Execution Flow:** 
   * A user views a KOL on the frontend and clicks an explicit `[Fetch Real-Time Scholar Metrics]` button.
   * Next.js fires a POST payload via the FastAPI bridge containing the KOL's `scholar_id`.
   * The script hits the SerpApi endpoint *exactly once* for that specific KOL.
   * It performs an SQL `UPSERT`, replacing the old metrics and setting `last_updated_date` to `NOW()`.
3. **Rate Limitations to Enforce:** The Next.js UI will disable the "Fetch" button if the database says the KOL was successfully synced within the last 7 days. This prevents redundant API triggers by different users viewing the same KOL.

### 5. UI Integration (Phase 2)
* Upgrading our `/api/db/kols` FastAPI endpoint to `JOIN` the `kol_scholar_metrics` table.
* The Next.js Data Visualizer will render a new column: **"Lifetime Citations"** and **"h-index"**, giving the CEO and users an immediate gauge of a KOL's global influence beyond just the SJR journal weight.

---
**Next Steps for Approval:** 
Please review this approach. If approved, we will begin by provisioning the `kol_scholar_metrics` table in Supabase and writing the Python extractor. 

*Question:* Do you prefer we proceed with a third-party bridge like **SerpApi**, or attempt the open-source **scholarly + proxy** route?

---

## Phase 3: Campaign Sandbox Integration (2026-03-26)

> **Decision**: SerpApi confirmed as the API provider. Scholar parsing is now **Step 3** in the Campaign Sandbox pipeline, positioned between HITL Disambiguation and Client Export.

### Updated Sandbox Button Flow

```
1. Run Disambiguation Engine        → Tier 1 auto-verify (ORCID, ≥0.70 score, standalone)
2. Human-in-the-Loop Disambiguation → Tier 2 HITL + Gemini Flash 2.5
3. Google Scholar Citation Parsing   → 4-tier citation lookup (checkbox-selected KOLs)  ← NEW
4. Export Client Text Report         → enriched with citation metrics
5. Commit to Global DB              → scholar metrics + pull_ids persist
```

### Checkbox-Based Selective Sync (User-Controlled)

Instead of batch mode, the UI provides **per-KOL checkboxes** and a **Select All** toggle:

| UI Element | Behavior |
|------------|----------|
| Checkbox per KOL row | User manually ticks which KOLs to enrich |
| Select All / Deselect All | Header checkbox toggles all rows |
| "3. Run Scholar Parsing" button | Fires only for checked KOLs (sends `kol_ids[]` to API) |
| Progress tracker | Shows `Processing 3 of 12 selected...` with per-KOL status badges |
| Rate limiter | Disables checkbox for KOLs synced within last 7 days |

**API Payload**: `POST /api/sandbox/run_scholar_sync { kol_ids: [12, 45, 67], pull_id: "002" }`

### Database Changes
- `kols_staging` + `kols`: Add columns `scholar_status TEXT DEFAULT 'pending'`, `scholar_id TEXT`
- `kol_scholar_metrics`: Already provisioned (no changes)
- `scholar_review_queue`: Already provisioned (no changes)

### New API Routes
- `POST /api/sandbox/run_scholar_sync` — Iterate selected KOLs through 4-tier disambiguation
- `GET /api/sandbox/scholar_status?pull_id=X` — Per-KOL scholar sync status for UI badges
- `GET /api/sandbox/scholar_review_queue?pull_id=X` — Tier 4 failed candidates for manual review
- `POST /api/sandbox/resolve_scholar` — Human approves/rejects a Scholar candidate

### Automation-Ready Design
All sandbox steps are **idempotent CLI scripts** with `--pull_id` arguments:
```bash
python run_pipeline.py --pull_id 003
python kol_disambiguator.py --pull_id 003
python sync_scholar_citations.py --pull_id 003
python export_sandbox.py --pull_id 003
```

