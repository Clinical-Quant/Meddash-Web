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


