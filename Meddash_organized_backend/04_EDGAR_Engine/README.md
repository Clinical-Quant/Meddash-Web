# 04_EDGAR_Engine — SEC EDGAR 8-K Catalyst Crawler

**Engine 04** in the Meddash pipeline. Reads SEC 8-K filings, extracts scheduled biotech catalysts, and pushes them to Supabase `catalyst_events`.

## Files

| File | Purpose |
|------|---------|
| `edgar_catalyst_crawler.py` | Main crawler script |
| `schema_catalyst_events.sql` | Supabase schema migration (catalyst_events + edgar_query_log) |

## What it extracts

Per 8-K hit → `catalyst_events` row:
- PDUFA dates (with extension supersedes logic)
- Top-line readout windows (Q4 2026 / H1 2027 style)
- AdCom meeting dates
- FDA approval mentions
- Complete Response Letter (CRL) mentions

**Don's rule:** Every calendar date traces to a company-filed 8-K. No secondary-calendar scraping, no invented URLs.

## Usage

```bash
# Default watchlist (8 tickers)
python edgar_catalyst_crawler.py

# Custom tickers
python edgar_catalyst_crawler.py --tickers MRK,VTRS,INO

# Smoke test (2 tickers, dry-run)
python edgar_catalyst_crawler.py --smoke-test

# Create Supabase schema
python edgar_catalyst_crawler.py --create-schema
```

## Supabase Tables

- `catalyst_events` — unique on `(ticker, asset, event_type)`, upsert with newer filing_date winning
- `edgar_query_log` — run log mirroring `ct_query_log`, `kol_query_log`, `literature_query_log`

## GitHub Actions

- `edgar-catalyst-pull.yml` — standalone workflow (daily 7 AM UTC + manual dispatch)
- `meddash-daily-pipeline.yml` — Job 5 in the daily pipeline (after biocrawler)

## Spec

See: `edgar-crawler-spec.md` (v2, 2026-10-06)
Wiki: [[EDGAR-Catalyst-Crawler]]