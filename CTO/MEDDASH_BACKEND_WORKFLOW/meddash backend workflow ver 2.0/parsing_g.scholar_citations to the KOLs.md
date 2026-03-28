# Adding Google Scholar Citations to KOL Database

## Objective
Manually enrich our KOL PostgreSQL database with Google Scholar metrics (Total Citations, h-index, i10-index) using user-provided Scholar profile URLs or raw author IDs. This workflow is optional and on-demand, and it supports both the sandbox (staging) and final KOL tables.

## The Challenge with Google Scholar
Unlike PubMed or ClinicalTrials.gov, Google Scholar does not have an official REST API and aggressively blocks scraping attempts (CAPTCHAs/IP bans) when queried in bulk.

## Current Manual Architecture

### 1. Data Source Selection
We cannot rely on raw scraping due to CAPTCHAs. Current production path:
- SerpApi (Google Scholar Author endpoint) using explicit Scholar author IDs extracted from pasted URLs.
- Name-based Scholar search is disabled in this phase because it is unreliable and can mis-tag KOLs.

### 2. Manual ID Extraction (User-Provided)
1. User pastes a full Scholar profile URL or a raw Scholar user ID into the UI.
2. The backend normalizes the input into a scholar_id (the user= parameter in the URL).
3. The sync job queries SerpApi once for that author ID and upserts metrics.

### 3. Database Schema (Supabase PostgreSQL)
We store numeric metrics in a dedicated table and keep identifiers on the KOL rows.

Table: kol_scholar_metrics
- kol_id (Foreign Key pointing to meddash_kols)
- scholar_id (String, Unique)
- total_citations (Integer)
- h_index (Integer)
- i10_index (Integer)
- last_updated_date (Timestamp)

Columns on kols_staging + kols:
- scholar_status (pending | scholar_verified | scholar_failed)
- scholar_id
- scholar_profile_url

### 4. On-Demand Fetching via Next.js UI (Rate Limit Avoidance)
We do not run weekly cron jobs. Scholar enrichment runs only when a user triggers it.
1. Sandbox Manual Lane: Step 3 in Campaign Sandbox, with per-row URLs and checkboxes.
2. Final KOL Manual Lane: Dedicated Scholar Enrichment page that loads final KOLs by pull_id.

### 5. API + Logging
- POST /api/sandbox/run_scholar_sync
  - Payload: { pull_id, targets: [{ kol_id, scholar_url }] }
- GET /api/scholar/final_kols?pull_id=X
- POST /api/scholar/run_final_sync
  - Payload: { pull_id, targets: [{ kol_id, scholar_url }] }
- Logs:
  - scholar_sync_<pull_id>.log (sandbox)
  - scholar_final_<pull_id>.log (final)

---

## Phase 3: Campaign Sandbox Integration (2026-03-27)

Decision: SerpApi is the provider. Scholar parsing is Step 3 in the Campaign Sandbox pipeline and is manual-only in this phase.

### Updated Sandbox Button Flow

```
1. Run Disambiguation Engine        -> Tier 1 auto-verify (ORCID, >=0.70 score, standalone)
2. Human-in-the-Loop Disambiguation -> Tier 2 HITL + Gemini Flash 2.5
3. Manual Scholar Parsing (Sandbox) -> User-pasted Scholar URLs + selected rows only
4. Export Client Text Report        -> enriched with citation metrics
5. Commit to Global DB              -> scholar metrics + pull_ids persist
```

### Checkbox-Based Selective Sync (User-Controlled)
Instead of batch mode, the UI provides per-KOL checkboxes, a Select All toggle, and a manual Scholar URL column:

| UI Element | Behavior |
|------------|----------|
| Checkbox per KOL row | User manually ticks which KOLs to enrich |
| Select All / Deselect All | Header checkbox toggles all rows |
| Manual Scholar URL column | User pastes Scholar profile URL or raw user ID |
| "3. Run Manual Scholar Parsing" button | Fires only for checked rows that have a pasted URL |

API Payload example:
POST /api/sandbox/run_scholar_sync { pull_id: "002", targets: [{ kol_id: 12, scholar_url: "..." }] }

### Database Changes
- kols_staging + kols: scholar_status, scholar_id, scholar_profile_url
- kol_scholar_metrics: Metrics table (no change)

### New API Routes
- POST /api/sandbox/run_scholar_sync — Manual URL-driven scholar sync (sandbox)
- GET /api/scholar/final_kols?pull_id=X — Load final KOLs for manual enrichment
- POST /api/scholar/run_final_sync — Manual URL-driven scholar sync (final)

### Automation-Ready Design
Sandbox scholar sync remains script-backed, but runs only when a user triggers it in the UI to avoid API overuse.

---

## Implementation Snapshot: Final KOL Manual Scholar Parsing (2026-03-27)

### Goal
Keep sandbox Step 3 intact, but add a separate manual enrichment lane for the final kols table so users can process Scholar URLs later by pull_id without reopening the sandbox workflow.

### Current Build (Live)
We support two manual Scholar parsing lanes in parallel:
1. Sandbox Manual Scholar Parsing
   - Existing Step 3 inside Campaign Sandbox
   - Writes to kols_staging
   - Used during active campaign validation before commit
2. Final KOL Manual Scholar Parsing
   - New standalone page accessible from the main dashboard
   - Loads final kols rows filtered by pull_id
   - User matches by KOL name, pastes Scholar URL or raw ID, and runs enrichment only for selected rows
   - Writes directly to final kols

### Backend Implementation
- Final-KOL loader endpoint filtered by pull_id
- Final manual Scholar sync endpoint
- Direct Scholar URL parsing (shared with sandbox)
- Persists on final kols: scholar_status, scholar_id, scholar_profile_url
- Numeric metrics continue in kol_scholar_metrics

### Health and Observability
- Sandbox logs: scholar_sync_<pull_id>.log
- Final logs: scholar_final_<pull_id>.log
- Both visible in System Health Override

### User Experience
- The user thinks in: pull_id, KOL name, pasted Scholar URL
- The system handles the correct table-specific id internally:
  - sandbox mode -> kols_staging.id
  - final mode -> kols.id

### Why This Shape Works
This preserves current sandbox behavior while creating a cleaner back-office enrichment path for optional or outsourced Scholar processing. It avoids forcing the user to care about database IDs while keeping writes safe.
