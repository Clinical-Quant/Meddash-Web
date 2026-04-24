# Issue 6 — API Server SQL Injection (Partial Fix)

**Date:** 2026-04-24  
**Status:** ⚠️ PARTIAL FAIL — REOPENED  
**Severity:** HIGH (upgraded from MODERATE)  
**Team:** Meddash-CTO  
**File:** `Meddash_organized_backend/api_server.py`

---

## What Was Fixed

- `/api/db/kols` endpoint now uses SQLAlchemy parameterized queries (`:search`, `:limit`)
- Global `X-API-Key` authentication dependency added to all endpoints

## What Was NOT Fixed

These 4 endpoints still use f-string interpolation — direct SQL injection vectors:

| Endpoint | Vulnerable Parameter | Pattern |
|----------|---------------------|---------|
| `/api/db/trials` | `limit` | `f"...LIMIT {limit}"` |
| `/api/db/leads` | `search`, `filters` | `f"SELECT ... FROM biotech_leads ..."` |
| `/api/db/sandbox` | `pull_id` | `f"...WHERE '{pull_id}' = ANY(...)"` |
| `/api/db/sandbox/export` | `pull_id` | similar f-string pattern |

## Required Fix

Convert all f-string queries to parameterized binding:

```python
# BEFORE (vulnerable):
query = f"SELECT nct_id, brief_title FROM trials LIMIT {limit}"

# AFTER (parameterized):
query = text("SELECT nct_id, brief_title FROM trials LIMIT :limit")
params = {"limit": limit}
result = session.execute(query, params)
```

## Additional Issue: Corrupted Line 17

```python
# BROKEN:
API_KEY=os.get...EY", "meddash-secret-key")

# CORRECT:
API_KEY = os.getenv("API_KEY", "meddash-secret-key")
```

This will crash on startup if `.env` doesn't define `API_KEY`.

---

*See also:* [[Meddash CTO Walkthrough - QA Verification]] · [[Meddash CTO Implementation Plan - QA Review]]