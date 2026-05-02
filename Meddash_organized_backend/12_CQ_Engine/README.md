# Clinical Quant (CQ) Engine — README

**Revised:** 2026-05-01 15:57 UTC (v2 — dual-path architecture + Nemotron + revised polling)

## What Is This?

Clinical Quant (CQ) is the financial intelligence arm of Meddash. It ingests SEC filings (8-K, Form 4) for publicly traded biotech companies, extracts catalyst events and insider trades, and pushes structured intelligence to Supabase for the newsletter pipeline.

**The core insight:** No one in the industry interprets biotech catalysts across both the scientific and monetary dimensions simultaneously. CQ fuses SEC filing data with Meddash's KOL/clinical trial data to produce multi-dimensional catalyst intelligence.

## Architecture — One Engine, Two Paths

```
TICKER SPINE (13,257 biotech tickers in Supabase)
       │
       ▼
STEP 0: GLOBAL MONITOR (SEC Latest Filings Feed)
Polls SEC EDGAR for latest 100 filings. Filters against
biotech watchlist. Routes by form type:
  Form 4  → Path B (Deterministic, Zero AI)
  8-K     → Path A (Nemotron-3-super Reasoning)
       │
       ├──────────────────┐
       ▼                  ▼
PATH B: FORM 4         PATH A: 8-K CATALYST
INSIDER TRADES          EXTRACTION
(100% Code)            (Nemotron-3-super)
filing.obj()           filing.markdown()
.transactions          → Section Splice (8.01, 7.01,
→ Filter 'P'             5.02, EX-99.1)
→ Extract name,        → Nemotron classify
  date, shares,        → Strict JSON schema
  price                → Binary gate + validation
       │                  │ PDUFA computation:
       │                  │ acceptance + 6/10 months
       ▼                  ▼
  cq_insider_trades    cq_catalysts
  (Supabase)           (Supabase)
```

### Path A — 8-K Catalyst Extraction (Reasoning Path)

edgartools fetches 8-K filings → `filing.markdown()` converts to clean text → section splicing extracts Items 8.01, 7.01, 5.02, EX-99.1 → Nemotron-3-super classifies with a strict JSON schema → binary gate (`is_catalyst` true/false) + deterministic validation → Supabase `cq_catalysts`.

PDUFA date computation: If the filing states an NDA/BLA acceptance date but not an explicit PDUFA date, the model computes it:
- Priority Review: acceptance_date + 6 months
- Standard Review: acceptance_date + 10 months

### Path B — Form 4 Insider Trades (Deterministic Path)

edgartools fetches Form 4 filings → `filing.obj().transactions` yields structured DataFrame → filter `transaction_code == 'P'` (purchases only) → extract insider name, date, shares, price → direct Supabase `cq_insider_trades`. No LLM. No confidence scoring. 100% code.

## Catalyst Taxonomy

The LLM classifies filings into these event types:

| Category | Event Types |
|----------|-------------|
| Regulatory | PDUFA, AdCom, CRL, FDA Approval |
| Clinical | Phase 1 Data, Phase 2 Data, Phase 3 Data, Interim Analysis |
| Corporate | M&A, Partnering, Offering |

## Polling Schedule

| Period | Frequency |
|--------|-----------|
| NY Market Hours (Mon–Fri 09:30–16:00 ET) | Hourly |
| Off-Market / Weekends | Every 12 hours |

The script is stateless — runs, processes, exits. Schedule is enforced by n8n/cron caller, not by the script.

## Database Schema

### `cq_catalysts` (Path A output — the ONLY CQ catalyst table)

| Column | Type | Purpose |
|--------|------|---------|
| id | UUID | Primary Key |
| ticker | VARCHAR(10) | Indexed for fast lookups |
| accession_number | VARCHAR(20) | Unique Constraint. Prevents duplicate processing of same SEC filing |
| filing_type | VARCHAR(10) | '8-K' (10-K, 10-Q deferred) |
| event_type | VARCHAR(20) | PDUFA, AdCom, Phase 1/2/3 Data, CRL, M&A, etc. |
| catalyst_date | DATE | ISO format. Nullable — OK if LLM can't extract. Computed when possible. |
| source_sentence | TEXT | The exact sentence from the filing where the event was identified |

Plus: `company_name`, `drug_name`, `indication`, `filing_url`, `created_at`

### `cq_insider_trades` (Path B output — NEW table)

| Column | Type | Purpose |
|--------|------|---------|
| id | UUID | Primary Key |
| ticker | VARCHAR(10) | Indexed |
| accession_number | VARCHAR(20) | Unique Constraint |
| insider_name | TEXT | Reporting person name |
| transaction_date | DATE | Date of purchase |
| shares_amount | INTEGER | Number of shares purchased |
| price_per_share | NUMERIC | Nullable — not always reported |

Plus: `company_name`, `filing_url`, `created_at`

## Retained Tables (DO NOT TOUCH)

These Meddash tables feed CQ but are owned by other engines:

- `biotech_tickers` — 13,257 tickers with CIK, exchange, company name (Meddash ticker spine)
- `biotech_ticker_aliases` — Normalized company name aliases per ticker
- `biocrawler_ticker_matches` — BioCrawler reverse-match bridge
- `cq_market_sentiment` — Yahoo RSS news metadata (kept, not part of catalyst pipeline)

## Retired Scripts

These scripts from the old CQ pipeline are RETIRED (renamed with `.RETIRED_MDP3SWIP7`):

| Script | Why Retired |
|--------|-------------|
| `sec_8k_monitor.py` | Only read RSS title/summary — never opened filing body. Keyword matching missed PDUFA dates. Replaced by edgartools + Nemotron. |
| `fda_pdufa_tracker.py` | Scraped wrong FDA page (AdCom calendar, not PDUFA action dates). Missed ARGX, CING, ARVN. Replaced by edgartools 8-K extraction. |
| `pr_wire_aggregator.py` | RSS feeds timeout frequently. Keyword matching on headlines is inferior to LLM classification of filing body text. |
| `alpha_vantage_tracker.py` | Prototype only — hardcoded tickers, stdout only, no DB writes. |
| `massive_tracker.py` | Prototype only — REST endpoint mocked, no production writer. |
| `enrich_tickers.py` | DISABLED — fuzzy matching was producing inaccurate results. |

## Environment Variables

Required in `.env`:

```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
SUPABASE_URI=postgresql://...
OLLAMA_HOST=http://172.23.61.64:11434
OLLAMA_MODEL=nemotron-3-super
EDGAR_IDENTITY=Clinical Quant contact@meddash.ai
```

## Key Files

| File | Purpose |
|------|---------|
| `cq_engine.py` | Main pipeline: global monitor → form router → Path A (Nemotron) / Path B (deterministic) → Supabase push |
| `schema_cq_catalysts.sql` | DDL for both `cq_catalysts` and `cq_insider_trades` tables |
| `README.md` | This file |
| `WORKFLOW.md` | Detailed step-by-step workflow document |