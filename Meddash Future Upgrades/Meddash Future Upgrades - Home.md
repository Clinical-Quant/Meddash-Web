# Meddash Future Upgrades — Home

**Created:** 2026-04-24  
**Maintainer:** Alfred Chief (CTO / QA)  
**Vault:** `C:\Users\email\.gemini\antigravity`  

---

> This is the Meddash-CQ operations office. Every update, fix, plan, and architecture decision lives here.

## Active Documents

### QA Reports
Issues found, fixes reviewed, approvals and cautions.

- [[Issue 5 - CQ Ticker Fuzzy Matching Fix]] — ✅ APPROVED WITH CAUTION

### Implementation Plans
CTO plans reviewed by QA with required amendments before execution.

- [[Meddash CTO Implementation Plan - QA Review]] — ⚠️ APPROVED WITH 4 AMENDMENTS

### Architecture Decisions
ADR (Architecture Decision Records) for structural choices that affect the whole system.

- [[MEDDASH-CQ Architecture Decision Log]] — 5 decisions logged:
  - ADR-001: SQLite + PG dual database topology (⚠️ being fixed)
  - ADR-002: UPSERT over append for migrations
  - ADR-003: Config-driven pipeline parameters
  - ADR-004: X-API-Key auth for internal APIs
  - ADR-005: Local SIC cache for SEC API rate limiting

### Cross-Team Coordination
Meddash × CQ coordination items — shared data, dependency chains, shared state.

- [[Cross-Team Coordination Log]] — 3 items:
  - COORD-001: Ticker matching dual fix (CQ done, Meddash pending)
  - COORD-002: Bug fix dependency chain order
  - COORD-003: Graph Memory shared state across agents

---

## Open Issues Status

| # | Severity | Issue | Owner | Status |
|---|----------|-------|-------|--------|
| 1 | CRITICAL | SQLite→PG data sync | Meddash-CTO | ✅ FIXED — psycopg2 + SUPABASE_URI |
| 2 | CRITICAL | Nightly scheduler `--targets` | Meddash-CTO | ✅ FIXED — DB-driven targets + NSCLC fallback |
| 3 | CRITICAL | KOL disambiguator disabled | Meddash-CTO | ✅ FIXED — uncommented in pipeline |
| 4 | CRITICAL | Bridge engine mocked data | Meddash-CTO | ✅ FIXED — real Supabase queries |
| 5 | CRITICAL | Biotech leads missing tickers | **Both CTOs** | 🔄 CQ fix done, Meddash biocrawler fix pending |
| 6 | **HIGH** | SQL injection + no auth | Meddash-CTO | ⚠️ PARTIAL — auth done, SQL injection in 4 endpoints + corrupted line 17 |
| 7 | MODERATE | Destructive migration | Meddash-CTO | ✅ FIXED — on_conflict_do_nothing() |

---

## Graph Memory Nodes

| Node | Project | Status |
|------|---------|--------|
| `MEM_MEDDASH-CQ_20260423_155217` | MEDDASH-CQ | Full empire audit |
| `MEM_MEDDASH-CQ_20260423_231312` | MEDDASH-CQ | Dual business model |
| `MEM_CLINICAL-QUANT_20260424_002910` | CQ | CQ-Team audit |
| `MEM_MEDDASH_20260424_005348` | Meddash | Pipeline audit (7 issues) |
| `MEM_CLINICAL-QUANT_20260424_022636` | CQ | Issue 5 fix approved |

---

*Last updated: 2026-04-24 by Alfred Chief*