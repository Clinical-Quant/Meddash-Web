# Meddash CTO Walkthrough — QA Verification

**Date:** 2026-04-24  
**Reviewer:** Alfred Chief (CTO / QA)  
**Source:** [[walkthrough.md.resolved]] + [[implementation_plan.md.resolved]]  
**Status:** ⚠️ 6 of 7 PASS — 1 PARTIAL FAIL (api_server.py)

---

## Verification Results

| # | Script | Issue | Result | Notes |
|---|--------|-------|--------|-------|
| 1 | `kol_weight.py` | Issue 1: SQLite→PG | ✅ PASS | Uses `psycopg2.connect(SUPABASE_URI)`. No sqlite3. |
| 2 | `load_sjr.py` | Issue 1: SQLite→PG | ✅ PASS | Uses `psycopg2.connect(SUPABASE_URI)`. No sqlite3. |
| 3 | `run_pipeline.py` | Issue 3: Disambiguator | ✅ PASS | Both imports uncommented. `run_disambiguation()` and `compute_all_weights()` in pipeline flow. |
| 4 | `bridge_engine.py` | Issue 4: Mock data | ✅ PASS | "Dr. Sarah Chen" hardcoded data REMOVED. Now queries Supabase PG with `DictCursor`, ILIKE filtering on publication titles/abstracts. |
| 5 | `nightly_scheduler.py` | Issue 2: —targets | ✅ PASS | Reads targets dynamically from `biocrawler_leads.db` via `SELECT DISTINCT primary_indication`. Falls back to NSCLC. |
| 6 | `api_server.py` | Issue 6: SQL injection + auth | ⚠️ PARTIAL FAIL | Auth: ✅ PASS. SQL injection: ❌ FAIL — only `/api/db/kols` is parameterized. `/trials`, `/leads`, `/sandbox`, `/sandbox/export` still use f-strings. |
| 7 | `migrate_sqlite_to_pg.py` | Issue 7: Destructive migration | ✅ PASS | Uses `on_conflict_do_nothing()`. `if_exists='append'` only used for schema creation with empty frame, not data insertion. |

---

## Amendment Compliance Check

| Amendment | Description | Complied? | Evidence |
|-----------|-------------|-----------|----------|
| 1 | Dependency chain order (Issue 1 before 3,4,5) | ✅ YES | Issue 1 (PG migration) done first. Issues 3 and 4 depend on PG data — correct order. |
| 2 | UPSERT with `ON CONFLICT DO NOTHING`, not append | ✅ YES | `migrate_sqlite_to_pg.py` uses `stmt.on_conflict_do_nothing()`. |
| 3 | Config-driven targets, not hardcoded | ✅ YES | `nightly_scheduler.py` reads from DB with NSCLC fallback. |
| 4 | X-API-Key auth (confirmed acceptable) | ✅ YES | Global `Depends(verify_api_key)` on all endpoints. |

---

## Open Issues — Must Fix Before Next Release

### ISSUE-6-PARTIAL: SQL Injection Still Present in 4 Endpoints

**Severity:** MODERATE → UPGRADED TO HIGH  
**File:** `api_server.py`

The CTO only parameterized `/api/db/kols`. These 4 endpoints still use f-string interpolation:

1. `/api/db/trials` — `f"SELECT ... FROM trials LIMIT {limit}"`
2. `/api/db/leads` — `f"SELECT ... FROM biotech_leads ..."`
3. `/api/db/sandbox` — `f"SELECT ... FROM kols_staging WHERE '{pull_id}' = ANY(...)"`
4. `/api/db/sandbox/export` — similar pattern

**Fix required:**

```python
# BEFORE (vulnerable):
query = f"SELECT nct_id, brief_title FROM trials LIMIT {limit}"

# AFTER (parameterized):
query = "SELECT nct_id, brief_title FROM trials LIMIT :limit"
params = {"limit": limit}
result = session.execute(text(query), params)
```

This is a **blocking issue** — any user-supplied `limit`, `search`, or `pull_id` parameter in those endpoints is an injection vector.

### ISSUE-CORRUPT: Line 17 Corrupted in api_server.py

**Severity:** LOW  
**File:** `api_server.py`, line 17

```python
API_KEY=os.get...EY", "meddash-secret-key")
```

This should be:
```python
API_KEY = os.getenv("API_KEY", "meddash-secret-key")
```

The `os.getenv` got truncated. This will crash on startup if the `.env` file doesn't set `API_KEY`, and even if it does, the current line is broken Python.

---

## Non-Blocking Observations

1. **`bridge_engine.py` still uses sqlite3** for `fetch_new_tier_a_leads()` — this reads from `biocrawler_leads.db` (the lead DB), which is separate from the KOL scoring path. This is fine — the KOL scoring path correctly uses PG.

2. **`migrate_sqlite_to_pg.py`** — The `if_exists='append'` on line 51 is only for schema creation (`df.head(0).to_sql(...)` with an empty DataFrame). This is correct — it creates the table structure without inserting data. Actual data insertion uses `on_conflict_do_nothing()`. No issue here.

3. **The dependency chain was followed correctly.** Issue 1 (PG migration) was done first, enabling Issues 3 and 4 to work with real data.

---

## Verdict

**6 of 7 issues fully resolved. 1 issue partially resolved with remaining security vulnerability.**

Before next nightly run:
- [ ] Fix SQL injection in 4 remaining endpoints
- [ ] Fix corrupted line 17 in api_server.py
- [ ] Verify frontend sends `X-API-Key` header

After those fixes, all 7 issues are clear for production.

---

*Filed by: Alfred Chief (QA / CTO)*  
*Graph Memory:*