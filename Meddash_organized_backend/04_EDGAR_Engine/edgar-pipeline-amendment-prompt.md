# PROMPT FOR HERMES — amend the Meddash EDGAR pipeline into the catalyst data pipeline

> Don: paste everything below the line to Hermes as-is.

---

You are amending the Meddash data pipeline. There is an existing partial SEC
EDGAR line (the "EDGAR Catalyst Pull" workflow, currently green daily) —
**amend it in place, do not replace it.** The goal: extend it into the full
decayable-biotech-data pipeline specified below, then build, smoke test, push
to GitHub, and put it on the daily cron with the rest of the Meddash pipeline.

Read these three spec files first — they are the authority, in this order:
1. `~/workspace/meddash/catalyst-data/catalyst-data-source-catalog.md` — the
   source catalog (v1.0): architecture, entity resolution, P0/P1/P2 sources,
   data-point → source map, daily pipeline spec, your P0 build order (§5).
2. `~/workspace/meddash/catalyst-daily/event-study-schema.md` — the event-study
   schema (v1.1, columns frozen): every field you extract lands in these
   columns. Learn the point-in-time rule — snapshot fields come from sources
   available ON the event date, never reconstructed later.
3. `~/workspace/meddash/catalyst-daily/paper-trade-rules.md` — frozen v1.0;
   read-only context, do not touch.

## 1. Objective

Pull the full breadth of decayable biotech company data (P0 in this pass, P1
as the second wave below), log every detection with date/time stamps, store raw
append-only in Supabase, and clone daily into the local SQLite master dataset
keyed by entity (CIK), not ticker. Price/volume data is EXCLUDED — it is
backfillable anytime and comes in Phase 2, overlapped later by entity_id +
date for correlation analysis.

## 2. Phase 1 — P0 sources (build now)

For EACH source: pull → normalize to entity_id → append to Supabase raw table
with `detected_at` (UTC), `source`, `source_url`, `filed_at`/`published_at`.
Nothing is ever updated in place; corrections are new rows.

### 2.1 EDGAR — extend the existing line
- **company_tickers.json** (`https://www.sec.gov/files/company_tickers.json`):
  pull EVERY run, diff against last run. Any ticker change → new row in
  `ticker_history` (entity_id, ticker, exchange, start/end dates, reason).
  This is the automatic ticker-change detector. Seed `entities` /
  `ticker_history` from it for the 9 catalyst-calendar names first.
- **8-K watcher**: EDGAR full-text search (`efts.sec.gov` JSON API) across
  tracked CIKs, daily. Classify each hit: readout / CRL / partnership /
  financing / management change / M&A / other. Extract: filer CIK, filed date,
  item numbers, headline facts. Log with timestamps.
- **10-Q / 10-K puller**: for tracked entities, pull latest filing; extract
  via companyfacts XBRL API (`https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json`):
  `revenue_ttm`, `cash_m`, `burn_q`; revenue mix from MD&A segment notes
  (LLM extraction, see §4).
- **DEF 14A**: CEO name, tenure, board — annual governance snapshot.
- **Form 4**: insider buys/sells — ticker, insider, transaction date, shares,
  price. Real-time pull.
- SEC etiquette: `User-Agent` header identifying the project, max 10 req/s.

### 2.2 ClinicalTrials.gov v2
`https://clinicaltrials.gov/api/v2/studies` — daily delta for tracked assets:
status changes (recruiting → completed etc.) and RESULTS postings. A results
posting is a readout tripwire: log it, link the NCT ID to the entity.

### 2.3 Press-release RSS watcher
PR Newswire + Business Wire biotech feeds, plus per-company IR news pages
(RSS where available) for the tracked entities. Every release: entity_id,
published_at, headline, URL, full text stored. This is often BEFORE the 8-K.

### 2.4 FDA databases
- Orphan Drug Designations DB (downloadable): new grants for tracked entities.
- Warning Letters (public DB): new letters, dated.
- Drugs@FDA + openFDA (`https://api.fda.gov`): approvals, label revisions —
  pull label text on approval events (feeds the invalidation-clause check).

### 2.5 Detection logging (every source, every hit)
Each detection row: `detected_at` (UTC, the moment WE saw it),
`event_date` (the event's own date), `entity_id`, `catalyst_type` (from the
taxonomy in the catalog), `source`, `source_url`, `filed_at`/`published_at`,
`raw_text_ref`. Append-only. A detection with no timestamp is a failed
detection.

## 3. Phase 2 — P1 sources (second wave, same prompt)

Build these after P0 is green:
- **FINRA + NASDAQ short interest**: bi-monthly published files → per-ticker
  short interest %, mapped to entity_id at date.
- **13F aggregate**: quarterly institutional holdings from EDGAR.
- **13D / 13G**: >5% ownership changes, event-driven.
- **S-1 / 424B**: IPO prospectus extraction (TAM claims, cap table, pipeline
  at listing) for newly tracked entities.
- **IR deck snapshots**: download the PDF on every cron run for tracked
  entities; store the file with pulled_at — decks get silently overwritten,
  the snapshot is the point.
- **FDA AdCom briefing docs** (event-driven scrape) and **EMA EPARs/CHMP
  opinions** (event-driven scrape).

## 4. LLM enrichment — DeepSeek v4.1 Flash via Ollama (you have the keys)

For every detected event, run the enrichment pass with DeepSeek v4.1 Flash
through your local Ollama setup:
- **Classify** `catalyst_type` per the catalog taxonomy.
- **Extract** into the event-study schema v1.1 columns: outcome facts, numbers
  VERBATIM as stated (never computed, never rounded differently), snapshot
  fields from 10-Q/PR text.
- **Rules (hard):** extract, don't infer. Every extracted fact carries
  `source_url` + the source's date. Anything ambiguous → mark UNVERIFIED,
  never invented. A number you cannot trace to a source does not go in a
  column.
- Batch per run; log model version + prompt version with each enriched row
  (reproducibility).

## 5. Entity resolution (catalog §1 — implement exactly)

- `entities(entity_id PK, cik NULLABLE, primary_name, country, exchange,
  first_seen)`; `ticker_history(entity_id, ticker, exchange, start_date,
  end_date, reason)`; `corporate_actions(target, acquirer, type,
  announced_date, close_date, terms_note)`.
- Resolve EVERY mention to `entity_id` at the event date. Ambiguous match →
  flag for human review queue, NEVER auto-create an entity.
- Non-US entities: synthetic `entity_id`, `cik = NULL`, keyed on ISIN.

## 6. Storage

- **Supabase**: `catalyst_raw_filings`, `catalyst_raw_releases`,
  `catalyst_raw_trials`, `catalyst_raw_regulatory`, `catalyst_raw_shortinterest`
  — append-only, all timestamped per §2.5.
- **SQLite (local master)**: normalized tables per §5 + `events` +
  `snapshots` (schema v1.1 columns). The daily cron syncs Supabase → SQLite
  as an idempotent rebuild.

## 7. Build → smoke test → push → cron (do all four)

1. **Build** in the existing repo (Clinical-Quant/Meddash-Web, where the
   EDGAR line lives). Follow repo conventions; don't invent new infra.
2. **Smoke test** — run once manually and verify ALL of:
   - [ ] Rows land in Supabase raw tables with `detected_at` timestamps.
   - [ ] The 9 calendar names resolve to correct `entity_id`s (spot-check 3).
   - [ ] The ticker-diff detects at least one historical ticker change
         correctly (pick a known rename in the test set).
   - [ ] LLM enrichment fills schema v1.1 columns for 5 sample events with
         zero invented facts (hand-verify the numbers against sources).
   - [ ] An ambiguous entity match lands in the human-review queue, not in
         the master tables.
   - [ ] The SQLite clone builds and row counts match Supabase.
3. **Push** to GitHub per repo convention (feature branch + PR, or direct —
   follow what the repo does).
4. **Daily cron** in GitHub Actions, same schedule family as the other Meddash
   pipelines. On failure: alert + log the gap in the run log. NEVER silently
   skip a day — a gap in a point-in-time dataset is data corruption.

## 8. Acceptance criteria (report back on each)

- [ ] All P0 sources pulling; detections timestamped (UTC).
- [ ] Entity resolution live with CIK keys; ticker change detected in smoke test.
- [ ] Enrichment fills schema columns; 5/5 hand-verified with no invented facts.
- [ ] Supabase raw populated; SQLite clone builds idempotently.
- [ ] Cron green 3 consecutive days; failure alerting verified (force one
      failure in staging if needed to prove the alert fires).
- [ ] P1 source list staged as follow-up issues/tickets, not started.

## 9. Out of scope (do not build)

Price/volume/intraday data. Analyst estimates. Anything paid. Real-money
anything. If a source needs a key we don't have, log it as P2 and move on —
do not improvise credentials.
