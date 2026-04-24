# Meddash QA Bug Fixes (2026-04-24)

| # | Severity | Issue | Status |
|---|----------|-------|--------|
| 1 | CRITICAL | kol_weight + load_sjr write to SQLite but pipeline reads PG -- weight data never reaches Supabase | `[x]` |
| 2 | CRITICAL | nightly_scheduler.py calls run_pipeline.py without --targets -- always fails | `[x]` |
| 3 | CRITICAL | KOL disambiguator DISABLED in pipeline -- raw KOLs go to PG without dedup | `[x]` |
| 4 | CRITICAL | bridge_engine.py SDR outreach uses FAKE KOL data (hardcoded names) | `[x]` |
| 5 | CRITICAL | biotech_leads ticker column empty -- CQ limited to 9-ticker watchlist | `[x]` |
| 6 | MODERATE | api_server.py has SQL injection + no authentication | `[x]` |
| 7 | MODERATE | migrate_sqlite_to_pg.py uses destructive if_exists='replace' | `[x]` |

## Fix Log

*Details of fixes will be populated here as they are completed.*
