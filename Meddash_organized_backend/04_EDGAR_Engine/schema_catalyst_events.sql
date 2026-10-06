-- EDGAR Catalyst Crawler — Supabase schema migration
-- Creates: catalyst_events + edgar_query_log
-- Run on Supabase project tlyhaedxqrgluphwfkgu
-- Part of [[EDGAR-Catalyst-Crawler]] — SEQ-0041

-- ── Table: catalyst_events ──
create table if not exists public.catalyst_events (
  id uuid primary key default gen_random_uuid(),
  company text,
  ticker text not null,
  cik text,
  asset text not null,
  indication text,
  event_type text not null,              -- PDUFA | readout_window | AdCom | approval | CRL | other_regulatory
  date_or_window text not null,          -- '2026-11-27' or 'Q4 2026'
  date_precision text not null default 'exact',  -- exact | window
  priority_review boolean not null default false,
  verification_source text not null,     -- EDGAR filing index URL, 8-K (or flagged IR exception)
  accession_number text,
  filing_date date,
  excerpt text,                          -- 1-2 sentence proof quote
  status text not null default 'upcoming',       -- upcoming | occurred
  ingested_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (ticker, asset, event_type)      -- the upsert key
);

create index if not exists idx_catalyst_events_status_date
  on public.catalyst_events (status, date_or_window);

-- ── Table: edgar_query_log ──
create table if not exists public.edgar_query_log (
  id uuid primary key default gen_random_uuid(),
  run_timestamp timestamptz not null default now(),
  tickers_searched text,                 -- e.g. 'MRK,VTRS,INO,CAPR,BBIO,PRAX,COGT,PFE'
  filings_scanned integer not null default 0,
  total_found integer not null default 0,
  total_ingested integer not null default 0,   -- upserted rows
  status text not null default 'success',      -- success | partial | failed
  error_detail text
);

-- ── Enable RLS (default Supabase convention) ──
alter table public.catalyst_events enable row level security;
alter table public.edgar_query_log enable row level security;

-- NOTE: RLS blocks anon key reads. The Lovable /catalyst-calendar page must
-- read with a key that bypasses RLS (sb_secret_* key in apikey header) or
-- a dedicated SELECT policy must be added. See spec section 3.