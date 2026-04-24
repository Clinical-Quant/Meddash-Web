# MEDDASH-CQ Architecture Decision Log

**Created:** 2026-04-24  
**Maintainer:** Alfred Chief (CTO / QA)

---

## ADR-001: Dual Database Topology — SQLite + Supabase PG

**Date:** 2026-04-24  
**Status:** ⚠️ ACTIVE PROBLEM (being addressed)

### Context

Multiple scripts in the Meddash pipeline write to SQLite (`meddash_kols.db`, `ct_trials.db`) while the API and frontend read from Supabase PostgreSQL. This creates a data gap where weight data, journal metrics, and KOL deduplication results never reach the serving layer.

### Decision

All scripts must write to Supabase PG (via `SUPABASE_URI`). SQLite is acceptable as a local cache/scratchpad but must NOT be the source of truth for any data the API serves.

### Consequences

- `kol_weight.py` and `load_sjr.py` must be migrated to PG connections (Issue 1 in CTO plan)
- Any new scripts must default to PG, not SQLite
- SQLite→PG migration script needs UPSERT, not append (see ADR-002)

---

## ADR-002: Migration Safety — UPSERT Over Append

**Date:** 2026-04-24  
**Status:** ACCEPTED

### Context

`migrate_sqlite_to_pg.py` uses `df.to_sql(if_exists='replace')`, which destroys data and schema constraints on every run. Simply changing to `if_exists='append'` creates duplicate rows.

### Decision

Use `ON CONFLICT DO NOTHING` (or `DO UPDATE` for full upsert) with proper primary key constraints on all Supabase tables. No migration script should ever destroy existing data.

### Consequences

- Primary key constraints must be defined on all Supabase tables before migration
- `migrate_sqlite_to_pg.py` must use SQLAlchemy's `insert().on_conflict_do_nothing()`
- This pattern becomes the standard for all future migration scripts

---

## ADR-003: Config-Driven Pipeline Parameters

**Date:** 2026-04-24  
**Status:** ACCEPTED

### Context

`nightly_scheduler.py` calls `run_pipeline.py` without a `--targets` argument, causing it to fail. The CTO's plan proposes hardcoding `"Non-Small Cell Lung Cancer"` as the default. This makes the pipeline brittle — every indication change requires a code change.

### Decision

Pipeline parameters (targets, MeSH terms, disease indications) must come from:
1. **CLI arguments** (highest priority)
2. **Config file** (middle priority)
3. **Database lookup** (`biotech_leads.indications`) (fallback)
4. **Hardcoded default** (last resort only)

### Consequences

- `nightly_scheduler.py` should read targets from a config or the database, not hardcode them
- Same pattern applies to `bridge_engine.py` MeSH term selection
- A `pipeline_config.yaml` or similar should be created as the single source of truth for default parameters

---

## ADR-004: Authentication Strategy for Internal APIs

**Date:** 2026-04-24  
**Status:** ACCEPTED

### Context

`api_server.py` has no authentication and uses string interpolation for SQL queries (injection vulnerability).

### Decision

- **Auth:** `X-API-Key` header with a dependency check. Sufficient for internal tooling.
- **SQL:** Parameterized queries via SQLAlchemy `text()` with bind variables (`:search`).
- **No JWT/OAuth** at this stage — overengineering for an internal tool.

### Consequences

- Frontend must send `X-API-Key` header in all requests
- API key should be stored in `.env` and never committed to git
- When Meddash goes multi-tenant (if ever), upgrade to JWT

---

## ADR-005: SEC API Rate Limiting — Local SIC Cache

**Date:** 2026-04-24  
**Status:** RECOMMENDED (not blocking)

### Context

`enrich_tickers.py` Strategy C now makes a live SEC Submissions API call per fuzzy match to validate SIC codes. At current scale (~100 matches per nightly run), this is fine. At dashboard scale (real-time queries), this will hit SEC rate limits (~10 req/sec).

### Decision

Implement a local `cik_to_sic.json` cache. On each run:
1. Check cache first
2. Only call SEC API for CIKs not in cache
3. Write new entries to cache
4. This turns 100 API calls into ~10 new ones per run after the first week

### Consequences

- Initial run still makes all SEC calls (cold cache)
- Subsequent runs are mostly cache hits
- Cache file lives at `CTO/CQ_Team/scripts/cik_to_sic.json` or alongside `enrich_tickers.py`
- Must handle stale SIC codes (cache TTL or manual refresh)

---

*Cross-references:* [[Issue 5 - CQ Ticker Fuzzy Matching Fix]] · [[Meddash CTO Implementation Plan - QA Review]]