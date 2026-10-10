-- Catalyst Data Pipeline — Supabase Schema (P0)
-- Builds the 4th pillar: decayable biotech company data for hedge fund roots
-- SEQ-0049 | 2026-10-09
-- Append-only raw tables + entity resolution + detection logging

-- ════════════════════════════════════════════════════════════════
-- Entity Resolution (§5)
-- ════════════════════════════════════════════════════════════════

create table if not exists public.entities (
  entity_id uuid primary key default gen_random_uuid(),
  cik text unique,
  primary_name text not null,
  country text,
  exchange text,
  first_seen timestamptz not null default now(),
  isin text,
  status text not null default 'active',  -- active | merged | delisted
  ambiguity_flag boolean not null default false  -- true = needs human review
);

create index if not exists idx_entities_cik on public.entities (cik);
create index if not exists idx_entities_name on public.entities (primary_name);

create table if not exists public.ticker_history (
  id uuid primary key default gen_random_uuid(),
  entity_id uuid not null references public.entities(entity_id),
  ticker text not null,
  exchange text,
  start_date date not null,
  end_date date,
  reason text,  -- 'ipo' | 'rename' | 'merger' | 'delisting' | 'ticker_change'
  detected_at timestamptz not null default now()
);

create index if not exists idx_ticker_history_entity on public.ticker_history (entity_id);
create index if not exists idx_ticker_history_ticker on public.ticker_history (ticker);

create table if not exists public.corporate_actions (
  id uuid primary key default gen_random_uuid(),
  target_entity_id uuid references public.entities(entity_id),
  acquirer_entity_id uuid references public.entities(entity_id),
  action_type text not null,  -- 'merger' | 'acquisition' | 'spinoff' | 'reverse_split'
  announced_date date,
  close_date date,
  terms_note text,
  detected_at timestamptz not null default now()
);

-- ════════════════════════════════════════════════════════════════
-- Detection Log (§2.5 — every source, every hit)
-- ════════════════════════════════════════════════════════════════

create table if not exists public.catalyst_detections (
  id uuid primary key default gen_random_uuid(),
  detected_at timestamptz not null default now(),  -- when WE saw it (UTC)
  event_date date,                                  -- the event's own date
  entity_id uuid references public.entities(entity_id),
  ticker text,
  catalyst_type text not null,  -- from taxonomy: PDUFA | readout | CRL | approval | AdCom | partnership | financing | management_change | ma | trial_status_change | results_posting | orphan_designation | warning_letter | label_revision | insider_buy | insider_sell | other
  source text not null,         -- 'edgar_8k' | 'edgar_10q' | 'edgar_10k' | 'edgar_def14a' | 'edgar_form4' | 'ctgov' | 'pr_newswire' | 'business_wire' | 'fda_orphan' | 'fda_warning' | 'fda_drugsatfda'
  source_url text,
  filed_at date,                -- SEC filing date or press release date
  published_at timestamptz,     -- for press releases / FDA actions
  raw_text_ref text,            -- excerpt or reference to raw text
  verification_status text not null default 'unverified',  -- verified | rejected | unverified
  verification_note text,
  enriched_data jsonb,          -- LLM-extracted schema v1.1 fields
  llm_model text,               -- model version for reproducibility
  prompt_version text           -- prompt version for reproducibility
);

create index if not exists idx_detections_entity on public.catalyst_detections (entity_id);
create index if not exists idx_detections_date on public.catalyst_detections (detected_at);
create index if not exists idx_detections_type on public.catalyst_detections (catalyst_type);
create index if not exists idx_detections_source on public.catalyst_detections (source);

-- ════════════════════════════════════════════════════════════════
-- Raw Append-Only Tables (§6 — Supabase)
-- ════════════════════════════════════════════════════════════════

-- Raw SEC filings (8-K, 10-Q, 10-K, DEF 14A, Form 4)
create table if not exists public.catalyst_raw_filings (
  id uuid primary key default gen_random_uuid(),
  detected_at timestamptz not null default now(),
  entity_id uuid references public.entities(entity_id),
  cik text,
  ticker text,
  form_type text not null,       -- '8-K' | '10-Q' | '10-K' | 'DEF 14A' | 'Form 4'
  accession_number text,
  filing_date date not null,
  item_numbers text,             -- for 8-K items
  headline text,
  key_facts jsonb,               -- extracted facts (revenue, cash, burn, etc.)
  source_url text not null,
  raw_text text,                 -- full document text or excerpt
  detected_items text[]          -- classified catalyst types from this filing
);

create index if not exists idx_raw_filings_entity on public.catalyst_raw_filings (entity_id);
create index if not exists idx_raw_filings_date on public.catalyst_raw_filings (filing_date);
create index if not exists idx_raw_filings_form on public.catalyst_raw_filings (form_type);

-- Raw press releases
create table if not exists public.catalyst_raw_releases (
  id uuid primary key default gen_random_uuid(),
  detected_at timestamptz not null default now(),
  entity_id uuid references public.entities(entity_id),
  ticker text,
  published_at timestamptz not null,
  headline text not null,
  body_text text,
  source text not null,          -- 'pr_newswire' | 'business_wire' | 'ir_page'
  source_url text not null,
  raw_rss_xml text
);

create index if not exists idx_raw_releases_entity on public.catalyst_raw_releases (entity_id);
create index if not exists idx_raw_releases_date on public.catalyst_raw_releases (published_at);

-- Raw CT.gov trial changes
create table if not exists public.catalyst_raw_trials (
  id uuid primary key default gen_random_uuid(),
  detected_at timestamptz not null default now(),
  entity_id uuid references public.entities(entity_id),
  nct_id text not null,
  trial_title text,
  previous_status text,
  new_status text,
  status_change_date date,
  has_results boolean not null default false,
  results_posting_date date,
  source_url text,
  raw_data jsonb
);

create index if not exists idx_raw_trials_entity on public.catalyst_raw_trials (entity_id);
create index if not exists idx_raw_trials_nct on public.catalyst_raw_trials (nct_id);

-- Raw FDA regulatory actions
create table if not exists public.catalyst_raw_regulatory (
  id uuid primary key default gen_random_uuid(),
  detected_at timestamptz not null default now(),
  entity_id uuid references public.entities(entity_id),
  ticker text,
  action_type text not null,     -- 'orphan_designation' | 'warning_letter' | 'approval' | 'label_revision'
  action_date date not null,
  drug_name text,
  indication text,
  source text not null,          -- 'fda_orphan' | 'fda_warning' | 'fda_drugsatfda' | 'openfda'
  source_url text not null,
  raw_text text
);

create index if not exists idx_raw_regulatory_entity on public.catalyst_raw_regulatory (entity_id);
create index if not exists idx_raw_regulatory_date on public.catalyst_raw_regulatory (action_date);

-- ════════════════════════════════════════════════════════════════
-- Events (enriched, schema v1.1 — normalized for SQLite master)
-- ════════════════════════════════════════════════════════════════

create table if not exists public.catalyst_events_master (
  id uuid primary key default gen_random_uuid(),
  detection_id uuid references public.catalyst_detections(id),
  entity_id uuid not null references public.entities(entity_id),
  event_date date not null,
  catalyst_type text not null,
  asset text,
  indication text,
  event_outcome text,            -- 'positive' | 'negative' | 'neutral' | 'pending'
  -- Schema v1.1 columns (frozen per event-study-schema.md)
  pdufa_date date,
  trial_phase text,
  trial_nct_id text,
  endpoint_result text,          -- 'met' | 'missed' | 'partial' | 'pending'
  revenue_ttm numeric,
  cash_m numeric,                -- in millions
  burn_q numeric,                -- quarterly burn in millions
  priority_review boolean,
  orphan_designation boolean,
  insider_transaction_type text, -- 'buy' | 'sell'
  insider_shares numeric,
  insider_price numeric,
  -- Point-in-time rule: snapshot fields from sources available ON event date
  snapshot_date date,            -- date of the source providing snapshot fields
  -- Audit
  source_url text not null,
  enriched_at timestamptz,
  llm_model text,
  prompt_version text,
  verification_status text not null default 'unverified'
);

create index if not exists idx_events_master_entity on public.catalyst_events_master (entity_id);
create index if not exists idx_events_master_date on public.catalyst_events_master (event_date);
create index if not exists idx_events_master_type on public.catalyst_events_master (catalyst_type);

-- ════════════════════════════════════════════════════════════════
-- Human Review Queue (ambiguous entity matches)
-- ════════════════════════════════════════════════════════════════

create table if not exists public.entity_review_queue (
  id uuid primary key default gen_random_uuid(),
  detected_at timestamptz not null default now(),
  mentioned_name text not null,
  mentioned_ticker text,
  source text not null,
  source_url text,
  candidate_entity_ids uuid[],
  status text not null default 'pending',  -- pending | resolved | rejected
  resolved_entity_id uuid references public.entities(entity_id),
  resolved_by text,
  resolved_at timestamptz
);

-- ════════════════════════════════════════════════════════════════
-- Ticker Diff State (for change detection across runs)
-- ════════════════════════════════════════════════════════════════

create table if not exists public.ticker_diff_state (
  id uuid primary key default gen_random_uuid(),
  checked_at timestamptz not null default now(),
  ticker text not null,
  old_cik text,
  new_cik text,
  old_name text,
  new_name text,
  change_type text,              -- 'new' | 'removed' | 'cik_change' | 'name_change'
  resolved_entity_id uuid references public.entities(entity_id)
);

-- ════════════════════════════════════════════════════════════════
-- RLS (Supabase convention)
-- ════════════════════════════════════════════════════════════════

alter table public.entities enable row level security;
alter table public.ticker_history enable row level security;
alter table public.corporate_actions enable row level security;
alter table public.catalyst_detections enable row level security;
alter table public.catalyst_raw_filings enable row level security;
alter table public.catalyst_raw_releases enable row level security;
alter table public.catalyst_raw_trials enable row level security;
alter table public.catalyst_raw_regulatory enable row level security;
alter table public.catalyst_events_master enable row level security;
alter table public.entity_review_queue enable row level security;
alter table public.ticker_diff_state enable row level security;