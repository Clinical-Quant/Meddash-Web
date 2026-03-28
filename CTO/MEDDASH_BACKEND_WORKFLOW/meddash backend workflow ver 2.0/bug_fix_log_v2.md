# Meddash Version 2.0 - Bug Fix & Incident Log

## [2026-03-25] - Explorer 500 Internal Server Error (Schema Mismatch)

### Incident Description
During the `Step 3.3` UI testing phase, opening the Data Explorer Dashboard triggered a series of `500 Internal Server Error` failures on the `/api/db/kols`, `/api/db/trials`, and `/api/db/leads` FastAPI bridge routes.

### Root Cause Analysis (RCA)
The original Next.js integration `api_server.py` was hardcoded to expect the old SQLite tabular layout (`kol_id`, `name`, `target_ta`, `priority_score`, etc). However, the `migrate_sqlite_to_pg.py` script constructed the new unified PostgreSQL cloud schemas securely utilizing Pandas engine structures, resolving naming conventions into formal columns (`id`, `brief_title`, `primary_indication`, `tier`). The Next.js API route crashed attempting to pull columns that officially vanished or were renamed during the cloud migration phase.

### Resolution
1. Introspected the live Supabase execution logic.
2. Modified the `/api/db/kols` sidecar route to dynamically map the new robust schema (`k.id AS kol_id`, `k.first_name || ' ' || k.last_name AS name`, `k.author_publication_weight AS weight`).
3. Re-mapped the Next.js target properties (`LEFT JOIN` on `kol_scholar_metrics s ON k.id::text = s.kol_id::text`).
4. Modified `/api/db/trials` to extract the correct Pandas-mapped `brief_title` rather than the legacy `title`.
5. Modified `/api/db/leads` to extract `primary_indication`, `trial_phases`, and `tier` instead of the deprecated `target_ta`, `funding_stage`, and `priority_score`.

6. Fixed a secondary schema mismatch in `09_Scholar_Engine/sync_scholar_citations.py` where the extraction logic attempted to query legacy `name` and `kol_id` columns instead of the unified `id`, `first_name`, and `last_name` columns.

The frontend rendering table successfully handles this transparently because of the `Object.keys()` generic mapper algorithm written during Phase 2.

---

## [2026-03-25] - Scholar Sync: Identity Disambiguation Architecture

### Incident Description
The initial `sync_scholar_citations.py` implementation would blindly accept the first Google Scholar profile returned by SerpApi for a given name search. This introduced a data integrity risk: two researchers with the same name (e.g., "Hiroki Takashima") could result in a different person's Citation metrics being written against the wrong KOL record in the database.

### Resolution
Implemented a 4-tier identity verification protocol inside `sync_scholar_citations.py` before any data is committed:
- **Tier 1 (ORCID):** If our database stores an ORCID for the KOL, it checks if that ORCID appears in the Scholar profile description. Auto-accepts on match.
- **Tier 2 (Publications):** Fetches up to 10 Scholar article titles. Requires ≥3 fuzzy title matches (70% threshold) against our known KOL publication records. Auto-accepts on match.
- **Tier 3 (Institution + Specialty):** Both the Scholar profile's `affiliations` and `interests` must independently fuzzy-match our KOL's institution and specialty simultaneously. Auto-accepts when both pass.
- **Tier 4 (Manual Queue):** If all tiers fail, the top 3 Scholar candidates are written to the new `scholar_review_queue` PostgreSQL table for human review, and no metrics are saved.

### New Tables Provisioned
- `kol_scholar_metrics` (existing, updated with `kol_id::text` cast fix)
- `scholar_review_queue` (new, auto-provisioned via `migrate_review_queue.py`)

---

## [2026-03-25] - Scholar Sync: 422 Unprocessable Content (Type Mismatch)

### Incident Description
Clicking the `[Fetch Metrics]` button in the Next.js Explorer triggered a `422 Unprocessable Content` error in the FastAPI terminal. The UI showed no updates, and the background sync was blocked.

### Root Cause Analysis (RCA)
The FastAPI `ScholarSyncPayload` Pydantic model defines `kol_id` as a `str`. However, the Supabase `kols` table identifies specific records using an integer `id`. The Next.js frontend was serializing the raw integer value (e.g., `{"kol_id": 1}`), which caused a strict validation failure in FastAPI before the request was ever dispatched to the Python engine.

### Resolution
Modified `src/app/explorer/page.tsx` to explicitly cast the `kol_id` to a string using `String(kol_id)` before serialization. This ensures the payload correctly arrives as `{"kol_id": "1"}`, satisfying the Pydantic type constraints.
---

## [2026-03-25] - Pipeline Control: 400 Invalid Target Engine (KOL Engine)

### Incident Description
When entering a Target Disease (e.g., "mutated NSCLC") and a Pull ID (e.g., "001") on the Crawler Control UI and selecting the "KOL Data Engine", launching the crawler returned a `400 Invalid target engine` error, failing to start the backend scripts.

### Root Cause Analysis (RCA)
Although the Next.js dropdown correctly dispatched `{ "engine": "kol_engine" }`, the FastAPI bridge (`api_server.py`) at the `/api/system/run_advanced` endpoint did not have `"kol_engine"` mapped in its `allowed` execution dictionary. Furthermore, the subprocess argument builder (`build_args`) was not configured to translate the UI inputs into the `--targets` and `--pull_id` CLI flags required by `run_pipeline.py`.

### Resolution
1. Added `"kol_engine": "01_KOL_Data_Engine/run_pipeline.py"` to the `allowed` execution routes in `api_server.py`.
2. Expanded the `AdvancedPayload` Pydantic model to accept the optional `pull_id` string.
3. Updated the `build_args` dictionary logic. When `script_rel_path` matches `run_pipeline`, it now correctly appends `--targets [query_term]` and `--pull_id [pull_id]` to the Python subprocess call.

---

## [2026-03-25] - Campaign Sandbox: Empty Staging Table / Fetch Failure

### Incident Description
After successfully launching a targeted pipeline extraction with a Pull ID from the Next.js control panel, entering the Sandbox Validation Bay and hitting "Loads" returned zero KOL records, despite the Python scraper reporting success earlier.

### Root Cause Analysis (RCA)
While Phase 1 (Pubmed Extraction) succeeded, Phase 2 (`db_ingestion.py`) was failing silently during the PostgreSQL database commit. The legacy SQLite driver code used `conn.execute("SELECT LASTVAL()")` to fetch the primary key of the newly inserted KOL. In Supabase/PostgreSQL, `LASTVAL()` frequently throws sequence context errors if `ON CONFLICT` clauses bypass an insert or if multiple connections run concurrently. Because the script couldn't retrieve the `kol_id`, the ingestion aborted, leaving `kols_staging` completely empty for that `pull_id`.

### Resolution
Refactored the SQLAlchemy execution block in `db_ingestion.py`. Removed `SELECT LASTVAL()` entirely. Instead, appended the PostgreSQL-native `RETURNING id` clause to the `INSERT INTO` statements, instantly capturing and passing the safe Primary Key into `res[0]`. Ingestion loops now process reliably.

---

## [2026-03-25] - Campaign Sandbox: Database Ingestion Crash Loop (Identity Schema Missing)

### Incident Description
Even after fixing the `LASTVAL()` crash, Campaign `pull_id` batches were reporting "Successfully ingested" on the backend, yet returning 0 records in the PostgreSQL `kols_staging` table. The entire database load cycle was silently aborting inside the SQLAlchemy sub-transactions.

### Root Cause Analysis (RCA)
1. **Schema Defect**: The primary `publications` table in Supabase was completely missing its `AUTOINCREMENT` identity generator mapping for the `id` column. Because PostgreSQL allows `NULL` by default, the script inserted rows with `id = NULL`. Every downstream bridging table (like `kol_authorships`) utterly failed trying to link to a Null ID pointer.
2. **Transaction Bubble**: Because `db_ingestion.py` bundled all 50 publications into a single master loop transaction, a single constraint failure (e.g. duplicate MeSH tag) aborted the entire master transaction (`InFailedSqlTransaction`), refusing any subsequent valid inserts.

### Resolution
1. **Database Level**: Executed native SQL against Supabase to strip all corrupt null rows, lock `publications.id` to `NOT NULL`, and attach a `GENERATED BY DEFAULT AS IDENTITY` sequence mapped to start at the maximum historical ID (`2227`).
2. **Backend Level**: Patched `db_ingestion.py` mapping queries on `kol_authorships` and `publication_mesh_map` to target their authentic composite primary keys instead of searching for a surrogate `id`. 
3. **Application Level**: Wrapped all sub-table inserts in SQLAlchemy `with conn.begin_nested():` blocks. This utilizes PostgreSQL `SAVEPOINT`s natively, ensuring duplicate violations instantly rollback isolated statements without aborting the master publication payload.

---

## [2026-03-25] - Sandbox API: NaN JSON Serialization Crash (500 Error on Pull ID 002)

### Incident Description
Loading Pull ID `002` in the Campaign Sandbox UI triggered a `500 Internal Server Error`. Pull ID `001` returned 0 results silently.

### Root Cause Analysis
- **002 crash**: Pandas `read_sql` returns Python `NaN` floats for NULL PostgreSQL fields (e.g. empty `institution`). Python's `json.dumps` raises `ValueError: Out of range float values` on NaN. The sandbox endpoint lacked sanitization.
- **001 empty**: Pull ID `001` genuinely contained 0 records — those early batches were ingested before the identity schema fix and were cleaned by the `DELETE FROM publications WHERE id IS NULL` repair.

### Resolution
Added `df.fillna("")` before `df.to_dict(orient="records")` in the `/api/db/sandbox` endpoint.

---

## [2026-03-25] - Architecture: CSV-Array Pull ID Migration (Preventing Row Cloning Bloat)

### Change Description
Replaced the row-cloning isolation strategy with a CSV-array `pull_id` column. KOLs appearing in multiple campaigns now store all their Pull IDs as a single comma-separated string (e.g. `"001,002,005"`) instead of being duplicated per campaign.

### Files Modified
- `db_ingestion.py` — Appends new pull_ids to CSV string instead of cloning rows
- `api_server.py` — All sandbox queries use `ANY(string_to_array(pull_id, ','))` for filtering, `array_remove` for surgical pull_id deletion
- `kol_disambiguator.py` — Updated ORCID and KOL scan queries to use CSV-aware array parsing

---

## [2026-03-26] - Feature: 3-Tier KOL Disambiguation Workflow

### Feature Description
Implemented a complete multi-tier disambiguation pipeline with real-time UI observability.

### Components Built
1. **Tier 1 (Automatic)** — `kol_disambiguator.py` now auto-merges ORCID-confirmed pairs, auto-merges high-confidence scored pairs (≥ 0.70), and auto-verifies standalone unique KOLs.
2. **Tier 2 (HITL + Gemini Flash 2.5)** — New Sandbox HITL Review Panel with side-by-side KOL comparison cards, Gemini Flash advisory reasoning, and 3 resolution buttons (Same Person / Two People / Escalate).
3. **Tier 3 (Deep Disambiguation)** — New `deep_disambiguation_needed` PostgreSQL table for truly ambiguous pairs requiring manual research.
4. **System Health Tab** — New "Sandbox Disambiguation" tab on System Health page with dynamic pull_id log streaming.

### New API Routes
- `GET /api/sandbox/pending_pairs?pull_id=XYZ`
- `POST /api/sandbox/gemini_review`
- `POST /api/sandbox/resolve_pair`

### Prerequisite
Add `GOOGLE_API_KEY=your_gemini_api_key` to `.env` to enable Gemini Flash 2.5 HITL review.

---

## [2026-03-26] - Disambiguation Engine: Missing Column & Integer Parse Crash

### Incident Description
When the user clicked "Run Disambiguation Engine" on the UI, the engine script crashed internally but reported success on the frontend. Specifically, the system log `sandbox_dedup_002.log` showed two sequential crashes:
1. `psycopg2.errors.UndefinedColumn: column "pull_id" does not exist` when trying to index `kol_merge_candidates`.
2. `invalid input syntax for type integer: "Unkn"` when aggregating `published_date` temporal scoring.

### Root Cause Analysis
1. **Missing Column**: The `kol_merge_candidates` table had already been provisioned in an earlier iteration. The SQL update `CREATE TABLE IF NOT EXISTS` block gracefully skipped recreating it, causing the new `pull_id` column to be omitted entirely. When the engine attempted to create an index on `pull_id`, the database crashed.
2. **Date Parse Error**: Publications returned a non-standard string like `'Unknown'` for `published_date`. The temporal engine attempted to cast `SUBSTR('Unknown', 1, 4)` (`'Unkn'`) to an integer, triggering the Postgres parse exception.

### Resolution
1. **Schema Hotfix**: Added `ALTER TABLE kol_merge_candidates ADD COLUMN IF NOT EXISTS pull_id TEXT;` right after the table definition in `kol_disambiguator.py` to seamlessly hot-patch existing databases without a hard wipe.
2. **Regex Filter**: Updated the temporal query to `WHERE p.published_date IS NOT NULL AND p.published_date ~ '^[0-9]{4}'` utilizing PostgreSQL regex to isolate only clean, numeric ISO format years.
---

## [2026-03-26] - API Server: 501 Unsupported Method / Failed to Fetch (Port 8000 Conflict)

### Incident Description
When attempting to launch crawler pipelines or fetch staged records from the frontend, the UI would report "Failed to fetch" and the backend would appear non-responsive or return "501 Unsupported Method" errors.

### Root Cause Analysis (RCA)
A standard Python static file server (`python -m http.server 8000`) was accidentally running in the background on port `8000`, which is the same port used by the Meddash FastAPI sidecar (`api_server.py`). The basic HTTP server intercepted incoming REST `POST` and `GET` requests; while it served some GET requests as file listings, it explicitly rejected `POST` requests with a `501 Unsupported Method` error, preventing the crawler engines from being triggered.

### Resolution
1. **Diagnostics**: Used `Get-NetTCPConnection -LocalPort 8000` to identify the owning process ID (`33484`).
2. **Process Analysis**: Confirmed via WMI that the process was indeed `python.exe -m http.server 8000`.
3. **Termination**: Forcefully stopped the rogue process using `Stop-Process -Id 33484 -Force`.
4. **Restoration**: Restarted the Meddash `api_server.py` on port 8000, restoring all bridge communication and pipeline functionality.

---

## [2026-03-26] - Sandbox UI: Step 3 Scholar Checkbox Auto-Select Regression

### Incident Description
In `Step 3 - Google Scholar Citation Parsing` on the Campaign Sandbox Validation page, clicking one KOL checkbox could visually select all KOL checkboxes even when the `Select All` button was not pressed.

### Root Cause Analysis (RCA)
Primary root cause was an identifier mismatch between backend payload and frontend state logic:
1. **Backend contract**: `/api/db/sandbox` returns `id AS kol_id`.
2. **Frontend bug**: Selection state used `kol.id` in checkbox `checked`, row toggle, preselect-verified logic, and select-all list generation.
3. **Effect**: Because `kol.id` was undefined for sandbox rows, checkboxes could share a non-unique selection state and appear bulk-selected after single-row interaction.

### Resolution
1. Rewired Step 3 selection logic to use `kol.kol_id` consistently for:
   - per-row checkbox `checked`
   - per-row checkbox toggle handler
   - preselecting verified KOLs
   - select-all list generation
2. Added ID guards (`Number.isFinite`) so only valid numeric KOL IDs are selectable.
3. Updated row keying to `kol.kol_id || idx` to stabilize rendering.
4. Kept the explicit bulk action control (`Select All` / `Deselect All`) and retained `e.stopPropagation()` in row checkbox handlers.

### Files Modified
- `meddash-frontend/src/app/sandbox/page.tsx`

---

## [2026-03-26] - Scholar Sync: No-Candidate Failures Hidden From System Health

### Incident Description
During `Step 3 - Google Scholar Citation Parsing` for Pull ID `001`, the selected KOLs `Guohua Liu` and `Xinyue Cheng` both resolved to `scholar_failed`. At the same time, the `System Health Override` page showed no useful execution log for the Scholar batch run, making it difficult to determine whether the issue was a script crash, API issue, or a genuine no-candidate search result.

### Root Cause Analysis (RCA)
1. **Observability Wiring Gap**: The backend writes Scholar batch logs to `scholar_sync_<pull_id>.log`, but the frontend `System Health` page only knew how to resolve dynamic log names for `sandbox_dedup_<pull_id>`. As a result, Step 3 logs were being generated on disk but were not visible in the override UI.
2. **Process Tracking Gap**: `/api/sandbox/run_scholar_sync` launched the sync in a background thread without registering the batch under `active_processes`, so the health monitor could not reliably surface live execution status for a Scholar batch.
3. **Search Recall Weakness**: `sync_scholar_citations.py` only queried SerpApi once using the exact full KOL name. For common names or transliterated East Asian author profiles, that single query path was too brittle and could return zero candidates even when an author profile might still be discoverable through variant search forms.

### Resolution
1. **System Health UI Fix**: Added a dedicated `Scholar Sync` log viewer mode on the frontend health page. It now resolves Pull ID scoped Scholar logs as `scholar_sync_<pull_id>`.
2. **Backend Process Tracking Fix**: Updated `/api/sandbox/run_scholar_sync` to:
   - create and track a stable process key `scholar_sync_<pull_id>`
   - write launch context into the same log file used by the Scholar engine
   - register the subprocess in `active_processes` so execution state is visible to the health monitor
3. **Scholar Search Hardening**: Updated `sync_scholar_citations.py` to try multiple fallback Scholar profile queries before declaring a no-candidate failure:
   - exact full name
   - first-initial + last-name form
   - inverted last-name query
   - name plus institution hint
4. **Deeper Logging**: Added query-attempt logging so future failures explicitly show which Scholar profile searches were attempted and how many candidates each returned.

### Files Modified
- `Meddash_organized_backend/api_server.py`
- `Meddash_organized_backend/09_Scholar_Engine/sync_scholar_citations.py`
- `meddash-frontend/src/app/health/page.tsx`

---

## [2026-03-26] - Scholar Sync: Optional Manual URL Enrichment Mode

### Change Description
Retained `Step 3 - Google Scholar Citation Parsing` on the Campaign Sandbox Validation page, but refactored its operational role from automatic author discovery into an optional manual enrichment lane. Users can now paste a direct Google Scholar profile URL or raw Scholar `user` ID per KOL and run the step only for the rows they choose to enrich.

### Why This Change Was Needed
Automatic name-based Scholar discovery is currently unreliable because upstream Scholar profile search via SerpApi is no longer dependable for author lookup. However, direct author-profile fetch by known Scholar `user` ID remains viable. This makes manual URL-driven enrichment the most stable short-term workflow.

### Resolution
1. Added an editable `Scholar Profile URL` column to the sandbox KOL table when Step 3 is opened.
2. Changed the Step 3 submission flow to only process selected KOLs that have a pasted Scholar URL or raw Scholar ID.
3. Added backend parsing logic to extract the Scholar `user` ID from either:
   - a full Google Scholar profile URL
   - a raw Scholar ID string
4. Updated the backend to fetch author metrics directly from the Scholar author endpoint and persist:
   - `scholar_id`
   - `scholar_status`
   - `scholar_profile_url`
   - citation metrics in `kol_scholar_metrics`
5. Left Step 3 fully optional so sandbox KOL validation and eventual commit can continue even when no Scholar data is manually attached.

### Files Modified
- `meddash-frontend/src/app/sandbox/page.tsx`
- `Meddash_organized_backend/api_server.py`
- `Meddash_organized_backend/09_Scholar_Engine/sync_scholar_citations.py`

---

## [2026-03-27] - Manual Scholar URL Sync: Direct Author Fetch Parameter Bug

### Incident Description
After pasting a valid direct Google Scholar profile URL for `Chanjiang Liu` in Pull ID `001`, the manual Scholar sync still failed. The log showed:

`Scholar author fetch failed for scholar_id=ni8I7m0AAAAJ`

even though the Scholar profile URL and extracted Scholar ID were valid.

### Root Cause Analysis (RCA)
The manual Scholar sync path correctly extracted the Scholar profile ID from the pasted URL, but the backend author-fetch request sent the wrong SerpApi parameter. The code used:

- `user=<scholar_id>`

However, SerpApi's `google_scholar_author` endpoint expects:

- `author_id=<scholar_id>`

Because of that mismatch, the API response did not contain a valid `author` payload, and the sync logic marked the KOL as `scholar_failed`.

### Resolution
1. Updated `fetch_scholar_author_data()` to call SerpApi with `author_id` instead of `user`.
2. Added clearer warning logging when SerpApi returns:
   - an explicit `error`
   - a `search_metadata.status = Error`
   - a low-level request exception

### Files Modified
- `Meddash_organized_backend/09_Scholar_Engine/sync_scholar_citations.py`

---

## [2026-03-27] - Final KOL Scholar Enrichment: URL Input Mirrors Across All Rows

### Incident Description
On the Final KOL Scholar Enrichment page, pasting a Scholar profile URL into one row caused the same value to appear in every row, even without clicking any bulk action.

### Root Cause Analysis (RCA)
The UI state used `kol.id` as the key for both manual URL inputs and checkbox selection. For some final KOL rows, `id` was missing or non-numeric, so multiple rows shared the same undefined key. React state updates then appeared to apply to all rows at once.

### Resolution
1. Added a stable per-row key (`__rowKey`) derived from a valid KOL ID when available, or a row index fallback.
2. Re-keyed the manual Scholar URL state to `__rowKey` to prevent cross-row mirroring.
3. Updated checkbox selection to use `__rowKey`, and disabled selection for rows lacking a valid KOL ID.
4. Added a guard message when a pull_id returns rows without valid IDs.

### Files Modified
- `meddash-frontend/src/app/scholar/page.tsx`

---

## [2026-03-27] - Final KOL Scholar Enrichment: Checkboxes Disabled and Run Button Inactive

### Incident Description
After the row-level URL input bug was fixed, the Final KOL Scholar Enrichment page still could not be used operationally. The Scholar URL field could be edited per row, but:
- row selection checkboxes were disabled or non-interactive
- `Run Manual Scholar Parsing` remained inactive

### Root Cause Analysis (RCA)
This was caused by a deeper database integrity issue rather than the React checkbox component:
1. The final `kols` table contained a large number of rows where `kols.id` was `NULL`.
2. The Final Scholar Enrichment page correctly protects the sync action unless a valid writable KOL ID exists.
3. Because the API payload is built from final `kols.id`, rows with missing IDs could not be selected safely, which left the run button disabled.
4. The same schema defect also meant future commits into `kols` were at risk of continuing to create null IDs if the default sequence was not restored.

### Resolution
1. Added an automatic `kols` identity repair step in the backend:
   - create `kols_id_seq` if missing
   - backfill missing `kols.id` values
   - restore `ALTER TABLE kols ALTER COLUMN id SET DEFAULT nextval('kols_id_seq')`
2. Applied this repair before:
   - loading final KOLs for Scholar enrichment
   - running final Scholar sync
   - committing sandbox KOLs into final `kols`
3. Mirrored the same protection inside the Scholar sync engine so direct script execution also works safely against final `kols`.

### Outcome
Final KOL rows for pull `001` now return valid IDs across the board, which re-enables row selection and allows the manual Scholar parsing action to run normally.

### Files Modified
- `Meddash_organized_backend/api_server.py`
- `Meddash_organized_backend/09_Scholar_Engine/sync_scholar_citations.py`

---

## [2026-03-27] - Final Scholar Enrichment: Invalid URL Submission + Status Looping

### Incident Description
After the final KOL Scholar Enrichment page became selectable again, two additional UX issues appeared during live use:
- clicking `Run Manual Scholar Parsing` could mark a row as `scholar_failed`
- the page repeatedly refreshed the left-side status box with `Loaded 196 final KOLs for pull ID 001`

### Root Cause Analysis (RCA)
1. **Invalid Input Submission**: The final scholar sync accepted any pasted string and forwarded it to the backend. In the observed run, the submitted value was not a Google Scholar URL at all, but:
   - `https://www.youtube.com/shorts/EtkJ-vDGnc4`
   The backend correctly classified this as an invalid Scholar URL/ID, but the overall UX looked like a sync failure instead of a user-input validation issue.
2. **Polling Status Spam**: After launching a sync, the frontend started a 3-second polling loop that reused the same `loadKols()` function as a manual page load. That function always reset `actionStatus`, which caused the UI to repeatedly show the generic `Loaded 196 final KOLs...` message during background refreshes.

### Resolution
1. Added frontend validation so the final Scholar page now only accepts:
   - a real `scholar.google.com` profile URL containing `user=`
   - or a raw Scholar user ID
2. If invalid entries are present in selected rows, the sync is blocked client-side and the UI shows a targeted correction message instead of dispatching the background job.
3. Refactored `loadKols()` to support `silent` refresh mode for polling.
4. Updated the polling loop after `Run Manual Scholar Parsing` to call silent refreshes only, preventing the `Loaded 196 final KOLs...` message from looping.
5. Hardened the backend manual sync path so invalid inputs are logged as `invalid_input` without writing `scholar_failed` to the database.

### Outcome
The final Scholar page now behaves cleanly:
- invalid non-Scholar URLs are blocked before submission
- background refresh no longer spams the load-status message
- malformed pasted input no longer pollutes `scholar_status` as a false backend failure

### Files Modified
- `meddash-frontend/src/app/scholar/page.tsx`
- `Meddash_organized_backend/09_Scholar_Engine/sync_scholar_citations.py`

---

## [2026-03-27] - Workflow Documentation Sync: Manual Scholar Enrichment Architecture

### Change Description
After stabilizing the manual Google Scholar workflow, the v2.0 architecture documents were updated to match the live implementation.

### Documentation Updates
1. Synced the Mermaid schema to show:
   - optional sandbox manual Scholar parsing
   - dedicated final KOL Scholar enrichment tab
   - System Health visibility for `scholar_sync_<pull_id>` and `scholar_final_<pull_id>`
   - backend repair of missing final `kols.id` values before final Scholar sync
2. Updated the filepaths map to include:
   - final Scholar enrichment page
   - System Health page
   - final Scholar log path
   - final Scholar columns on `kols`
3. Preserved the bug log as the operational incident history for the new Scholar workflow shape.

### Files Modified
- `MEDDASH_BACKEND_WORKFLOW/ver 2.0_organized_meddashbackend_schema.txt`
- `Meddash_organized_backend/07_DevOps_Observability/meddash_filepaths.md`
- `MEDDASH_BACKEND_WORKFLOW/meddash backend workflow ver 2.0/bug_fix_log_v2.md`
