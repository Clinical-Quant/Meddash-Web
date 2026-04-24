# Cross-Team Coordination Log — Meddash × CQ

**Created:** 2026-04-24  
**Maintainer:** Alfred Chief (CTO / QA)

---

## COORD-001: Ticker Matching — Dual Fix Required

**Date:** 2026-04-24  
**Status:** 🔄 IN PROGRESS  
**Impact:** Both Meddash and CQ pipelines  

### Context

Issue 5 (missing tickers in `biotech_leads`) affects both teams. The root cause is that `biocrawler.py` `scrape_sec_edgar_for_funding()` has weak string matching that fails on SEC naming mismatches (e.g., "Company Inc." vs "Company"). Downstream, `enrich_tickers.py` tries to patch missing tickers via fuzzy matching but was too aggressive (0.85 cutoff, Strategy D token overlap producing garbage like "Chordia" → "COYA").

### Dual Fix

| Team | Fix | Status | Role |
|------|-----|--------|------|
| **CQ-CTO** | `enrich_tickers.py` — tightened fuzzy matching, disabled Strategy D, added SEC SIC validation | ✅ COMPLETE | Downstream bandage (heals existing gaps) |
| **Meddash-CTO** | `biocrawler.py` — improve `scrape_sec_edgar_for_funding()` string matching | ⏳ PENDING | Source vaccine (prevents future gaps) |

### Data Flow Impact

```
BioCrawler (biocrawler.py)
  └─ scrape_sec_edgar_for_funding()  ← Meddash fix goes HERE (source)
       └─ biotech_leads (Supabase)
            └─ sync_tickers_to_supabase.py
                 └─ enrich_tickers.py  ← CQ fix went HERE (downstream)
                      └─ biotech_leads.ticker (populated)
                           └─ CQ Phase 1 scripts (sec_8k, fda_pdufa, pr_wire)
```

### Coordination Notes

- Both fixes are independent and can be deployed separately
- CQ fix is live now — tickers are being populated
- Meddash fix will reduce the number of companies that NEED downstream enrichment
- After Meddash fix is deployed, re-run `enrich_tickers.py` to validate end-to-end flow

---

## COORD-002: Dependency Chain for Bug Fixes

**Date:** 2026-04-24  
**Status:** 📋 PLANNED  
**Impact:** Meddash pipeline execution order  

### Execution Status (Updated 2026-04-24)

```
Step 1: Issue 1 (sqlite→PG)          ✅ DONE — psycopg2 + SUPABASE_URI
    ↓
Step 2: Issue 3 (re-enable disambiguator + weight) ✅ DONE — uncommented in pipeline
    ↓
Step 3: Issue 4 (bridge_engine real KOL data)      ✅ DONE — DictCursor + ILIKE query
    ↓
Step 4: Issue 2 (nightly scheduler targets)         ✅ DONE — DB-driven with NSCLC fallback
    ↓
Step 5: Issue 5 (biocrawler ticker matching)        ⏳ PENDING — CQ side done, Meddash side still needed
    ↓
Step 6: Issue 6 (API security)                      ⚠️ PARTIAL — auth done, 4 endpoints still vulnerable to SQL injection
Step 7: Issue 7 (migration safety)                   ✅ DONE — on_conflict_do_nothing()
```

**New blocking issue:** 4 endpoints in api_server.py still have SQL injection via f-strings. Line 17 corrupted (`os.get...EY`). Must fix before next release.

### Why This Order

- Issue 3 depends on Issue 1: disambiguator + weight scripts must write to PG BEFORE we enable them
- Issue 4 depends on Issue 1: bridge engine queries KOL data from PG — if weights aren't in PG yet, queries return nothing
- Issue 2 is a scheduler fix — can go in parallel with 3-5 but logically follows the data flow
- Issues 6+7 are infrastructure hardening — can go last, no pipeline dependency

---

## COORD-003: Graph Memory — Shared State

**Date:** 2026-04-24  
**Status:** ✅ ACTIVE  

### Cross-Agent Communication

Both Agent Zero agents (agent-cq on port 5081, agent-QSL on port 5080) and Alfred Chief share the same Graph Memory files via host mount.

### Current Nodes

| Node ID | Project | Status | Summary |
|---------|---------|--------|---------|
| `MEM_MEDDASH-CQ_20260423_155217` | MEDDASH-CQ | active | Full empire audit |
| `MEM_MEDDASH-CQ_20260423_231312` | MEDDASH-CQ | active | Dual business model architecture |
| `MEM_CLINICAL-QUANT_20260424_002910` | CQ | active | CQ-Team audit |
| `MEM_MEDDASH_20260424_005348` | Meddash | active | Pipeline audit (7 issues found) |
| `MEM_CLINICAL-QUANT_20260424_022636` | CQ | completed | Issue 5 fix approved |

### Communication Protocol

- **Alfred Chief** reads/writes directly from `~/.hermes/graph-memory/`
- **Agent Zero agents** read/write from their container mount (`/a0/CTO/Graph Memory/`)
- **Host sync** is manual — Dr. Don copies between `~/.hermes/graph-memory/` and the C: drive path when needed

---

*Cross-references:* [[Issue 5 - CQ Ticker Fuzzy Matching Fix]] · [[Meddash CTO Implementation Plan - QA Review]] · [[MEDDASH-CQ Architecture Decision Log]]