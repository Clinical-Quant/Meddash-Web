-- CQ Engine — Schema: cq_catalysts + cq_insider_trades
-- Created: 2026-05-01
-- Revised: 2026-05-01 15:57 UTC (v2 — added cq_insider_trades for Path B)
--
-- FILTER LOGIC:
--   Path A (8-K): Binary gate from Nemotron (is_catalyst: true/false) + deterministic validation.
--   No confidence_score column — not stored, not used.
--   A null catalyst_date with is_catalyst=true is still written; PDUFA dates computed when possible.
--
--   Path B (Form 4): 100% deterministic, no LLM, no confidence.
--   Only transaction_code 'P' (purchases) are captured.
--
-- DEPENDENCIES: biotech_tickers must exist (Meddash-owned, do not alter)
--
-- RETIRED TABLES (safe to drop after migration):
--   cq_regulatory_catalysts  — replaced by cq_catalysts
--   cq_market_events         — no longer used by catalyst pipeline
--   cq_price_bars             — empty, no production writer
--   biotech_leads             — legacy pre-ticker-spine table

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================
-- TABLE 1: cq_catalysts (Path A output — 8-K catalyst events)
-- ============================================================

CREATE TABLE IF NOT EXISTS public.cq_catalysts (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker            VARCHAR(10) NOT NULL,
    company_name      TEXT,
    accession_number  VARCHAR(20) NOT NULL,
    filing_type       VARCHAR(10) NOT NULL,          -- '8-K', '10-K', '10-Q'
    event_type        VARCHAR(20) NOT NULL,          -- PDUFA, AdCom, Phase 3 Data, CRL, M&A...
    catalyst_date     DATE,                          -- ISO format, nullable (computed when possible)
    drug_name         TEXT,
    indication        TEXT,
    source_sentence   TEXT,                           -- exact quote from filing for manual verification
    filing_url        TEXT,                           -- SEC EDGAR link
    created_at        TIMESTAMPTZ DEFAULT now()
);

-- Unique dedup: same SEC filing never processed twice
CREATE UNIQUE INDEX IF NOT EXISTS idx_cq_catalysts_accession ON public.cq_catalysts (accession_number);

-- Fast lookups
CREATE INDEX IF NOT EXISTS idx_cq_catalysts_ticker ON public.cq_catalysts (ticker);
CREATE INDEX IF NOT EXISTS idx_cq_catalysts_event_type ON public.cq_catalysts (event_type);
CREATE INDEX IF NOT EXISTS idx_cq_catalysts_catalyst_date ON public.cq_catalysts (catalyst_date DESC);

-- ============================================================
-- TABLE 2: cq_insider_trades (Path B output — Form 4 purchases)
-- ============================================================

CREATE TABLE IF NOT EXISTS public.cq_insider_trades (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker            VARCHAR(10) NOT NULL,
    company_name      TEXT,
    accession_number  VARCHAR(20) NOT NULL,
    insider_name      TEXT NOT NULL,                 -- Reporting person (director, officer, 10%+ owner)
    transaction_date  DATE NOT NULL,                 -- Date of purchase
    shares_amount     INTEGER,                       -- Number of shares purchased
    price_per_share   NUMERIC,                        -- Nullable — not always reported in Form 4
    filing_url        TEXT,                           -- SEC EDGAR link
    created_at        TIMESTAMPTZ DEFAULT now()
);

-- Unique dedup: same SEC filing never processed twice
CREATE UNIQUE INDEX IF NOT EXISTS idx_cq_insider_trades_accession ON public.cq_insider_trades (accession_number);

-- Fast lookups
CREATE INDEX IF NOT EXISTS idx_cq_insider_trades_ticker ON public.cq_insider_trades (ticker);
CREATE INDEX IF NOT EXISTS idx_cq_insider_trades_date ON public.cq_insider_trades (transaction_date DESC);

-- ============================================================
-- RETAIN: biotech_tickers (Meddash Ticker Spine — DO NOT ALTER)
-- ============================================================
-- biotech_tickers           — 13,257 tickers with CIK, exchange, company_name
-- biotech_ticker_aliases    — Normalized company name aliases per ticker
-- biocrawler_ticker_matches — BioCrawler reverse-match bridge
-- cq_market_sentiment       — Yahoo RSS news metadata (still used, not part of catalyst pipeline)

-- ============================================================
-- RETIRE: Drop these tables when ready
-- ============================================================
-- DROP TABLE IF EXISTS public.cq_regulatory_catalysts;
-- DROP TABLE IF EXISTS public.cq_market_events;
-- DROP TABLE IF EXISTS public.cq_price_bars;
-- DROP TABLE IF EXISTS public.biotech_leads;