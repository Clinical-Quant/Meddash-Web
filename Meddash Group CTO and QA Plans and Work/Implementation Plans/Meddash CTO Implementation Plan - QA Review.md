# Meddash CTO Implementation Plan — QA Review

**Date:** 2026-04-24  
**Reviewer:** Alfred Chief (CTO / QA)  
**Status:** ⚠️ APPROVED WITH 4 AMENDMENTS  
**Source:** [[implementation_plan.md.resolved]]  
**Related QA Reports:** [[Issue 5 - CQ Ticker Fuzzy Matching Fix]]

---

## Summary

The Meddash CTO submitted a plan to address all 7 QA-identified issues (5 CRITICAL, 2 MODERATE). Technical approach for each fix is sound. However, 4 amendments are required before execution.

---

## Issues & Fix Assessment

### Issue 1 — SQLite→PG Data Sync *(CRITICAL)*

- **Files:** `kol_weight.py`, `load_sjr.py`
- **Plan:** Replace hardcoded SQLite connections with PostgreSQL connections to `SUPABASE_URI`
- **Assessment:** ✅ Correct approach. This is the first domino — must be done before Issues 3, 4, 5.

### Issue 2 — Nightly Scheduler Missing `--targets` *(CRITICAL)*

- **File:** `nightly_scheduler.py`
- **Plan:** Add `--targets "Non-Small Cell Lung Cancer"` to subprocess call
- **Assessment:** ⚠️ **AMENDMENT 3** — See below.

### Issue 3 — KOL Disambiguator Disabled *(CRITICAL)*

- **File:** `run_pipeline.py`
- **Plan:** Uncomment imports and function calls for `kol_disambiguator.py` and `kol_weight.py`
- **Assessment:** ✅ Correct. But MUST follow Issue 1 being completed first, or weighted data goes nowhere.

### Issue 4 — Bridge Engine Mocked Data *(CRITICAL)*

- **File:** `bridge_engine.py`
- **Plan:** Replace hardcoded `mock_rising_stars` with SQL query to `associated_kols` table + SVS score computation
- **Assessment:** ✅ Correct. But MUST follow Issue 1 being completed first, or the query returns empty results.

### Issue 5 — Biotech Leads Missing Tickers *(CRITICAL)*

- **File:** `biocrawler.py`
- **Plan:** Improve `scrape_sec_edgar_for_funding()` string matching for SEC naming mismatches
- **Assessment:** ✅ Correct. The **source fix** — prevents the problem upstream.
- **Cross-team:** CQ-CTO already patched downstream via `enrich_tickers.py` (see [[Issue 5 - CQ Ticker Fuzzy Matching Fix]]).

### Issue 6 — SQL Injection + No Auth *(MODERATE)*

- **File:** `api_server.py`
- **Plan:** Parameterized queries with SQLAlchemy `text()` + `X-API-Key` header dependency
- **Assessment:** ✅ Correct. API Key is sufficient for internal tool (see Amendment 4).

### Issue 7 — Destructive Migration *(MODERATE)*

- **File:** `migrate_sqlite_to_pg.py`
- **Plan:** Change `if_exists='replace'` to `if_exists='append'`
- **Assessment:** ⚠️ **AMENDMENT 2** — See below.

---

## 4 Required Amendments

### Amendment 1 — Dependency Chain Enforcement

Fixes must be applied in this order:

```
Issue 1 (SQLite→PG) ──→ Issue 3 (re-enable disambiguator+weight)
                       ──→ Issue 4 (bridge_engine queries real KOL data)
                       ──→ Issue 5 (ticker matching needs weight data flowing)
```

If Issue 4 is fixed before Issue 1, the bridge engine queries PG for KOL data that ISN'T THERE YET. The current mock data at least returns something. Broken real queries return nothing.

**Action:** Add this sequence to the implementation plan as a hard dependency.

### Amendment 2 — Use UPSERT, Not APPEND

Changing `if_exists='replace'` to `if_exists='append'` creates a different problem: **duplicate rows on every migration run**. Without primary key constraints, every run doubles the data.

**Correct approach:**

```python
from sqlalchemy.dialects.postgresql import insert

stmt = insert(table).values(rows)
stmt = stmt.on_conflict_do_nothing(index_elements=['primary_key_column'])
session.execute(stmt)
```

**Action:** 
1. Define primary key constraints on all Supabase tables first
2. Use `ON CONFLICT DO NOTHING` (or `DO UPDATE` for upsert)
3. Simple `append` is NOT safe

### Amendment 3 — Config-Driven Targets, Not Hardcoded

Hardcoding `--targets "Non-Small Cell Lung Cancer"` means the nightly run only ever processes one indication. 

**Correct approach:**
- Read targets from a config file OR from `biotech_leads` table (the indications column from CT.gov data)
- NSCLC is fine as a default fallback
- Same applies to the MeSH terms question for `bridge_engine.py` — pull from data, don't hardcode

**Action:** `--targets` should accept CLI args with `biotech_leads` as source, NSCLC as default fallback.

### Amendment 4 — API Key Auth Is Sufficient

`X-API-Key` header is the right call. This is an internal tool, not a public API. JWT/OAuth is overkill at this stage.

**Action:** Proceed with API Key auth. No change needed — this is a confirmation, not a correction.

---

## Quick Reference: CTO Questions Answered

| CTO Question | QA Answer |
|---------------|-----------|
| Auth method preference? | X-API-Key header. Ship it. |
| `if_exists` append or truncate? | Neither. UPSERT with `ON CONFLICT DO NOTHING` + proper primary keys. |
| Default `--targets`? | NSCLC as fallback, but read from config/DB. Don't hardcode. |
| MeSH terms for bridge_engine? | Pull from `biotech_leads` indication data. Don't hardcode. |

---

## Execution Result — CTO Walkthrough Verified 2026-04-24

| # | Issue | Result | Amendment Complied? |
|---|-------|--------|---------------------|
| 1 | SQLite→PG | ✅ PASS | Yes — done first |
| 2 | Nightly scheduler | ✅ PASS | Yes — dynamic targets from DB, NSCLC fallback |
| 3 | Disambiguator re-enabled | ✅ PASS | Yes — after Issue 1 |
| 4 | Bridge engine real data | ✅ PASS | Yes — queries Supabase PG with DictCursor |
| 5 | Ticker matching | ✅ PASS (CQ side) | N/A — Meddash biocrawler fix still pending |
| 6 | SQL injection + auth | ⚠️ PARTIAL FAIL | Auth: PASS. SQL injection: 4 of 5 endpoints still vulnerable |
| 7 | Destructive migration | ✅ PASS | Yes — `on_conflict_do_nothing()` implemented |

**New blocking issue:** [[Issue 6 - API Server SQL Injection Partial Fix]]

---

*Filed by: Alfred Chief (QA / CTO)*  
*Graph Memory:*
*See also:* [[Meddash CTO Walkthrough - QA Verification]]