# MDP3-SWIP4: Pipeline Operations Day — Fix, Run, Sample, Outreach

**Created:** 2026-04-28  
**Status:** IN PROGRESS  
**Owner:** Alfred Chief  
**Mission:** Get both pipelines running like clockwork, fix all silenced alerts, produce first sample KOL brief, and make first outreach contact. No more building — start selling.

---

## Preamble

Dr. Don has received zero Telegram notifications from either pipeline despite days of setup work. The CQ newsletter has never fired successfully. n8n has persistent issues (Telegram webhooks failing on localhost, Code node module restrictions, credential encryption problems). Today we fix everything end-to-end, run the pipelines, and produce the first sellable output.

---

## Section A: CEO Lead List — Full BioCrawler Export to Google Sheets

### A.1: Diagnose and Fix Google Sheets API

- [x] **A.1.1:** Verified — service_account.json at `/mnt/c/Users/email/Downloads/service_account.json`, project avid-grid-424623-r3, private key valid
- [x] **A.1.2:** Installed gspread 6.2.1 + oauth2client 4.1.3 (also installed google-auth, google-auth-oauthlib)
- [x] **A.1.3:** Connected to Google Sheets API — can read/write. Found 1 existing sheet "Futures Trades Extractor". "Biocrawler Biotech List" sheet shared by Dr. Don found at ID 1iA8Oo6VnkP6FCXUQBjYjZG1xwjbGx9VCtmncojDZoWg
- [x] **A.1.4:** Dr. Don shared "Biocrawler Biotech List" sheet — accessible and writable

### A.2: Put push_to_sheets.py to Sleep, Upgrade pull_from_sheets.py

- [x] **A.2.1:** Renamed `push_to_sheets.py` to `push_to_sheets.py.DISABLED` — retired (20-lead limit)
- [x] **A.2.2:** Created `export_all_leads_to_sheets.py` — exports ALL 655 companies (23 Tier B, 632 Tier C), 22 columns (11 DB + 11 CRM), dedup by company_slug, batch writes of 100
- [x] **A.2.3:** Rewrote `pull_from_sheets.py` — now syncs CRM columns (contact_name, role, linkedin, email, kanban_stage, etc.) back to new `crm_contacts` table in `biocrawler_leads.db`. Also syncs website/ticker back to biotech_leads. Tested: 655 rows scanned, 11 DB updates, 0 CRM inserts (Dr. Don hasn't filled any yet)
- [x] **A.2.4:** Exported 655 companies to "Biocrawler Biotech List" Google Sheet at https://docs.google.com/spreadsheets/d/1iA8Oo6VnkP6FCXUQBjYjZG1xwjbGx9VCtmncojDZoWg

### A.3: CEO-Facing Watch List

- [x] **A.3.1:** The Google Sheet IS the CEO watch list. All 655 companies exported with CRM columns ready for Dr. Don to fill in.

---

## Section B: n8n Overhaul — Fix Once and For All

### B.1: Diagnose n8n Core Issues

- [x] **B.1.1:** Audited all 3 workflows. Found: Meddash Work Flow had 4 Telegram nodes pointing to DELETED credential fgBFlRQbYkxSlH3P (3 fixed → FC6UZCW25OrnoHXG, 1 was already gone). Found: 6 Code nodes using require() which n8n sandbox blocks. Found: CQ workflow chain breaks after Monitor node — no connection to Load Daily Update. Found: Command Listener OLD DISABLED still in DB (harmless, active=0).
- [x] **B.1.2:** CQ workflow had 7/8 failed executions. Root cause: Code node with require('child_process') blocked by n8n sandbox + missing Python modules (feedparser, bs4, dotenv) + disconnected chain after Monitor node
- [x] **B.1.3:** Meddash workflow: 5 Code nodes all use require() which n8n sandbox blocks — zero Telegram alerts were going out because (a) stale Telegram credentials and (b) require() blocked

### B.2: Fix n8n Telegram Integration (Permanent Solution)

- [x] **B.2.1:** Removed ALL Telegram Trigger/webhook nodes from ALL workflows. Telegram Trigger requires HTTPS webhooks and is unsuitable for localhost.
- [x] **B.2.2:** Abandoned n8n Telegram SEND nodes too for now; all Telegram delivery is centralized through the local Python Ops API to avoid stale credential/cache problems.
- [x] **B.2.3:** Command Listener now uses Schedule Trigger → HTTP Request to `http://127.0.0.1:8765/telegram/poll` (webhook-free, Code-free, ExecuteCommand-free).
- [x] **B.2.4:** All stale credential references to `fgBFlRQbYkxSlH3P` and leftover `webhookId` fields purged from the operational workflows.

### B.3: Fix Meddash Work Flow

- [x] **B.3.1:** Created `meddash_pipeline_runner.py` as Python wrapper for engine01/engine02/engine03/health. It is now called by the Ops API, not by n8n Execute Command.
- [x] **B.3.2:** Created local Python Ops API: `07_DevOps_Observability/meddash_ops_api.py`, serving on `http://127.0.0.1:8765`.
- [x] **B.3.3:** Rebuilt Meddash Work Flow as HTTP-only: Schedule(06:00 UTC) → `/meddash/engine01` → `/meddash/engine02` → `/meddash/engine03` → `/meddash/health`. Uses only built-in Schedule Trigger + HTTP Request nodes. No Code, no Execute Command, no Telegram Trigger, no custom/private nodes.
- [x] **B.3.4:** Fixed Engine 03 BioCrawler stop: root cause was `biocrawler.py --mode all` doing slow Clearbit/SEC/ATS deep enrichment plus old internal Telegram 404. Patched runner to set `DISABLE_INTERNAL_TELEGRAM=1` and use workflow-safe `biocrawler.py --mode test` for scheduled runs. Verified `/meddash/engine03` succeeds through Ops API in 47.25 seconds; DB now 658 companies.
- [ ] **B.3.5:** Confirm Dr. Don receives Telegram notification after successful complete Meddash pipeline run

### B.4: Fix CQ-Free Newsletter Workflow

- [x] **B.4.1:** Read CQ workflow node-by-node — original had 11 nodes, broken chain after Monitor, 2 Code nodes with require().
- [x] **B.4.2:** CQ detection scripts traced: `sec_8k_monitor.py`, `fda_pdufa_tracker.py`, `pr_wire_aggregator.py`. Root cause of PR Wire timeout found: `pr_wire_aggregator.py` used `feedparser.parse(url)` directly with no request timeout, and one old BusinessWire URL was an HTML industry page, not a stable RSS feed, so the CQ run could hang until the outer 60s guard killed it.
- [x] **B.4.3:** Installed missing Python deps: feedparser, bs4, python-dotenv. Patched `pr_wire_aggregator.py` to use `requests.get(..., timeout=15)` + `feedparser.parse(response.content)`, removed the bad BusinessWire HTML URL, kept PRNewswire Health RSS + GlobeNewswire Pharma RSS, and made each feed fail independently. Verified `/cq/detect` now completes in 31.15s with SEC, FDA, and PR Wire all successful.
- [x] **B.4.4:** Created `cq_pipeline_runner.py` — detect command runs 3 scripts with timeout; select/latest-report support added.
- [x] **B.4.5:** Rebuilt CQ-Free Newsletter 1100 as HTTP-only: Schedule(11:00 UTC) → `/cq/detect` → Paperclip issue HTTP requests → `/cq/latest-report`. No Code nodes and no Execute Command nodes.
- [>] **B.4.6:** CQ workflow manual dry-run issue found: manual execution stopped at Daily Schedule node because Schedule Trigger does not emit downstream items in this manual-test path. Fixed by adding `Manual Test Trigger` connected to `Run CQ Detection via Ops API`. Both Manual Test Trigger and Daily Schedule now feed the same CQ chain.
- [x] **B.4.7:** Set all CQ HTTP Request node timeouts to 300000 ms so `/cq/detect` has enough time to return when SEC/PR feed scripts hit their 60s guard timeouts.
- [x] **B.4.8:** Paperclip issue trigger issue found/fixed. Original n8n issue body used wrong field `assignee`; Paperclip requires `assigneeAgentId` with full agent UUID. THE-6 was created but unassigned, so CQ-Selector did not act. Patched CQ workflow to create assigned issues and added explicit wakeup HTTP nodes:
  - `Wake CQ-Selector Agent` → `POST /api/agents/31049770-807e-4e82-9a87-15ccdb43845f/wakeup`
  - `Wake CQ-Monitor Agent` → `POST /api/agents/bb9deb04-97d7-4f35-89bc-130f67d8f759/wakeup`
  - Removed stale n8n Telegram nodes; Telegram remains centralized through Ops API.
- [>] **B.4.9:** Confirm Dr. Don receives CQ Telegram notification with daily update after hard-refresh + rerun of Manual Test Trigger

### B.5: n8n Restart and Activation Protocol

- [x] **B.5.1:** n8n restarted clean — no startup errors, no webhook complaints, no credential issues
- [x] **B.5.2:** Final n8n fix: abandoned Execute Command nodes because n8n UI treated them as unrecognized/disabled. Rebuilt workflows with only built-in Schedule Trigger + HTTP Request nodes. No custom/private node install required; the private-node Docker guide is not applicable because we are not building a custom node.
- [x] **B.5.3:** Dr. Don hard-refreshed and activated Meddash Work Flow. Engine 01 and Engine 02 ran successfully; Engine 03 initially stopped due BioCrawler runtime issue, then fixed in B.3.4.
- [x] **B.5.4:** Documented in SWIP4 itself. Key lesson: for this localhost n8n, do NOT use Telegram Trigger, Code nodes with require(), or Execute Command nodes. Use Schedule Trigger + HTTP Request to local Python Ops API.

---

## Section C: Full Pipeline Runs

- [>] **C.1:** Full Meddash pipeline run — Engine 01 and Engine 02 ran cleanly in n8n. Engine 03 initially stopped; fixed by switching BioCrawler scheduled mode from unbounded `--mode all` to bounded `--mode test` and disabling internal Telegram. Verified Engine 03 endpoint directly: success in 47.25s. Next: rerun full Meddash workflow in n8n and confirm final health Telegram.
- [>] **C.2:** Full CQ pipeline run — detection layer repaired and verified. `/cq/detect` now returns overall success in 31.15s: SEC 8-K success, FDA PDUFA success, PR Wire success. Remaining CQ validation: run full n8n manual path and confirm Paperclip Selector/Monitor issue creation + wakeups + Telegram latest-report.
- [ ] **C.3:** After both runs, check Paperclip for new issues created (CQ-Selector, CQ-Monitor, Meddash-CTO)
- [ ] **C.4:** After both runs, check Telegram for all expected notifications sent to Dr. Don

---

## Section D: Master Mermaid/HTML Blueprint

- [ ] **D.1:** Generate a full architecture diagram (Mermaid + HTML) showing both pipelines, all 13 agents, n8n workflows, Telegram bots, DBs, and data flows
- [ ] **D.2:** Render as standalone HTML with dark theme (viewable in browser, not requiring Streamlit)

---

## Section E: CQ Newsletter Engine Fix

- [ ] **E.1:** CQ newsletter pipeline diagnosis (overlaps with B.4 — consolidate findings here)
- [ ] **E.2:** Fix whatever prevents the CQ daily draft from being generated
- [ ] **E.3:** Verify CQ draft saves to Obsidian vault at expected path
- [ ] **E.4:** Verify CQ draft content quality — is it readable, is it accurate, is it worth posting?

---

## Section F: Paperclip Twitter/X Bot

- [ ] **F.1:** Set up a Paperclip agent or script that can post to X/Twitter (xurl CLI or API)
- [ ] **F.2:** Configure X API credentials
- [ ] **F.3:** Test posting a CQ daily insight tweet
- [ ] **F.4:** Wire into n8n CQ workflow as an optional post step

---

## Section G: First KOL Brief Templates and Samples

- [ ] **G.1:** Create KOL Brief template in Markdown/PDF format — the $2,450 Clinical KOL Intelligence Brief
  - Structure: Cover page, executive summary, methodology, top 50 KOLs ranked by SVS, rising stars highlight, institution network map, 1-page interpretation
- [ ] **G.2:** Generate first sample brief for a high-value indication (NSCLC — you have the data)
- [ ] **G.3:** Generate 3-profile teaser sample (the "foot in the door" freebie for outreach)
- [ ] **G.4:** Save to `Meddash Phase 3/` or `EXPORT CLIENT TEXT REPORTS/` with clear naming

---

## Section H: First Outreach

- [ ] **H.1:** From the 23 Tier B companies in biocrawler_leads.db, identify top 5 targets for personalized outreach
- [ ] **H.2:** For each target, use BioCrawler + KOL pipeline data to craft a hyper-personalized LinkedIn message
- [ ] **H.3:** Send first 3 LinkedIn connection requests + messages
- [ ] **H.4:** Document outreach in the CRM Google Sheet (kanban_stage = "Contacted")

---

## Section I: Base44 Meddash on Subdomain

- [ ] **I.1:** Assess current meddash-frontend status (Next.js app at `/mnt/c/Users/email/.gemini/antigravity/meddash-frontend/`)
- [ ] **I.2:** Determine deployment target (Vercel, Railway, Base44, custom subdomain)
- [ ] **I.3:** Deploy to staging subdomain
- [ ] **I.4:** Verify accessible from browser

---

## Summary: SWIP4 Checkbox Count

| Section | Items | Description |
|---------|-------|-------------|
| A: CEO Lead List | 9 | Google Sheets API fix, full export, reverse sync |
| B: n8n Overhaul | 16 | Diagnose, fix Telegram, fix Meddash WF, fix CQ WF, restart protocol |
| C: Pipeline Runs | 4 | Full Meddash + CQ runs, verify outputs |
| D: Master Blueprint | 2 | Architecture diagram |
| E: CQ Newsletter Fix | 4 | Newsletter engine diagnosis and fix |
| F: X/Twitter Bot | 4 | Paperclip X posting setup |
| G: KOL Brief Samples | 4 | Templates, samples, teaser |
| H: First Outreach | 4 | Top 5 targets, LinkedIn messages |
| I: Base44 Deploy | 4 | Meddash frontend deployment |
| **TOTAL** | **51** | |

---

## Today's 8 Tracked Items (Dr. Don's List)

| # | Item | Maps to SWIP4 Section |
|---|------|----------------------|
| 1 | Full Meddash run | C.1, B.3 |
| 2 | Full CQ pipeline run | C.2, B.4, E |
| 3 | Master Mermaid/HTML blueprint | D |
| 4 | Run/fix/rerun CQ free newsletter engine | B.4, E |
| 5 | Create Paperclip Twitter/X bot | F |
| 6 | Set up first KOL brief templates and samples | G |
| 7 | Make the first outreach | H |
| 8 | Fix and launch Base44 Meddash on subdomain | I |

---

## Key Context

- **Google Service Account:** `/mnt/c/Users/email/Downloads/service_account.json` (project: avid-grid-424623-r3)
- **Google Sheet:** "Biocrawler Biotech List" — shared to service account and populated with all BioCrawler companies
- **BioCrawler DB:** 658 companies after bounded Engine 03 repair run; Tier mix to re-check after next full CRM export
- **n8n workflows:** Rebuilt as HTTP-only. Operational rule: Schedule Trigger + HTTP Request only.
- **Local Ops API:** `/mnt/c/Users/email/.gemini/antigravity/Meddash_organized_backend/07_DevOps_Observability/meddash_ops_api.py`, running at `http://127.0.0.1:8765`
- **CQ schedule:** 11:00 UTC daily via HTTP-only n8n workflow
- **Meddash schedule:** 06:00 UTC daily via HTTP-only n8n workflow
- **Telegram delivery:** centralized through Ops API direct Telegram HTTP calls, not n8n Telegram Trigger or n8n Telegram Send nodes
- **Paperclip:** Running at localhost:3100, 1 company, 13 agents
- **Last CQ daily update:** 2026-04-27 03:17 (stale, no new one generated yet)
- **Current n8n lesson:** Do not use Telegram Trigger, Code node `require()`, or Execute Command nodes in this localhost n8n. Do not install private/custom nodes for this problem. Use local Python Ops API + HTTP Request.

---


---

## CQ Market Data / Catalyst Data Integration Index — Alpha Vantage + Massive

This section answers, in plain language, Dr. Don’s question: “Did we already link market/catalyst data, are we pulling it, do we have tables for it, and do we have scripts?”

### Simple Answer — Current State

PR Wire timeout:
- Yes, PR Wire was timing out.
- Root cause: `pr_wire_aggregator.py` was using `feedparser.parse(url)` directly with no per-request timeout.
- One BusinessWire URL was an HTML industry page, not a reliable RSS feed, and it could hang the CQ run until the outer 60s guard killed it.

Fix applied:
- Patched:
  `/mnt/c/Users/email/.gemini/antigravity/CTO/CQ_Team/scripts/phase1_regulatory/pr_wire_aggregator.py`
- Added `requests.get(..., timeout=15)` before feed parsing.
- Removed the bad BusinessWire HTML URL.
- Kept:
  - PRNewswire Health RSS
  - GlobeNewswire Pharma RSS
- Each feed now fails independently instead of blocking the whole CQ run.

Verification:
- Ran:
  `POST http://127.0.0.1:8765/cq/detect`
- Result: success.
- Runtime: 31.15 seconds.
- All three scripts succeeded:
  - SEC 8-K monitor: success
  - FDA PDUFA tracker: success
  - PR Wire aggregator: success
- PR Wire output:
  - PRNewswire feed OK, 20 entries
  - GlobeNewswire feed OK, 0 entries
  - No valid Phase 1 Trial Readouts found

Alpha Vantage / Massive / Polygon status:
- Credentials exist in:
  `/mnt/c/Users/email/.gemini/antigravity/CTO/CQ_Team/.env`
- Verified presence only, no secrets printed.
- Present:
  - Supabase credentials
  - Alpha Vantage API key
  - Massive S3 credentials
  - Massive endpoint/bucket settings

Scripts found:
- Alpha Vantage:
  `/mnt/c/Users/email/.gemini/antigravity/CTO/CQ_Team/scripts/phase3_sentiment/alpha_vantage_tracker.py`
  - Calls Alpha Vantage `NEWS_SENTIMENT`.
  - Uses hardcoded test tickers: `COGT`, `PFE`.
  - Prints results to stdout.
  - Does not write to Supabase yet.
  - Has TODO for `cq_market_sentiment`.

- Massive:
  `/mnt/c/Users/email/.gemini/antigravity/CTO/CQ_Team/scripts/phase4_quant/massive_tracker.py`
  - Initializes Massive S3 client.
  - Can list candidate flatfiles by ticker/prefix.
  - REST API call is currently mocked/placeheld.
  - Does not write to Supabase yet.

- Polygon:
  - No active Polygon-specific ingestion script found.
  - In this codebase, “Massive” appears to be the market data path, not an active Polygon REST pipeline.

Tables checked:
- Supabase:
  - `biotech_leads`: exists, 640 rows at check time.
  - `cq_regulatory_catalysts`: exists, 0 rows at check time.
- Missing/not present:
  - `stock_prices`
  - `price_history`
  - `market_data`
  - `pr_news`
  - `alpha_vantage_prices`
  - `polygon_prices`
  - `massive_prices`
  - `ticker_price_history`
  - `daily_prices`
  - `ohlcv`
  - `news_events`
  - `cq_market_events`

Operational answer:
- PR Wire is now fixed and actively pulled by `/cq/detect`.
- Alpha Vantage is linked at credential/prototype-script level only.
- Massive is linked at credential/prototype-script level only.
- Price charts / OHLCV / market sentiment are not currently being production-pulled into CQ tables.
- The tables for those market data streams do not currently exist in Supabase.
- The next build step is to create tables such as:
  - `cq_market_sentiment`
  - `cq_price_bars`
  - `cq_market_events`
  and then promote the Phase 3/4 scripts into `cq_pipeline_runner.py` as bounded optional stages.

### Supabase Table Build Checklist — Required Next

Purpose: create the storage spine now, even if we only lightly populate it at first. This lets the business mature into price analytics later without blocking the current newsletter/GTM mission.

#### Table 1: `cq_market_sentiment` — required

Use case:
- Store ticker-level news/sentiment metadata from Alpha Vantage or another source.
- CQ-Selector can use this as a signal: “Is there unusual positive/negative attention around this ticker?”

Checklist:
- [ ] Create Supabase table `cq_market_sentiment`.
- [ ] Suggested columns:
  - `id` UUID primary key
  - `ticker` text, indexed
  - `company_name` text nullable
  - `source` text, e.g. `alpha_vantage`, `yahoo_finance_rss`
  - `headline` text
  - `summary` text nullable
  - `url` text
  - `published_at` timestamptz nullable
  - `sentiment_score` numeric nullable
  - `sentiment_label` text nullable
  - `relevance_score` numeric nullable
  - `raw_payload` jsonb nullable
  - `created_at` timestamptz default now()
- [ ] Add unique guard to prevent duplicate articles, preferably on `(ticker, url)`.
- [ ] Modify `phase3_sentiment/alpha_vantage_tracker.py` to upsert into `cq_market_sentiment`.
- [ ] Keep the script bounded: limit tickers per run and set request timeouts.
- [ ] Add it to `cq_pipeline_runner.py` only as an optional stage after Phase 1 is stable.

#### Table 2: `cq_price_bars` — create now, mature later

Use case:
- Store OHLCV price bars by ticker/timeframe.
- Not needed for immediate newsletter launch, but useful later for price reaction analytics around catalysts.
- Dr. Don’s current decision: create the table now; mature analytics later as the business grows.

Checklist:
- [ ] Create Supabase table `cq_price_bars`.
- [ ] Suggested columns:
  - `id` UUID primary key
  - `ticker` text, indexed
  - `bar_time` timestamptz, indexed
  - `timeframe` text, e.g. `1h`, `1d`
  - `open` numeric
  - `high` numeric
  - `low` numeric
  - `close` numeric
  - `volume` bigint nullable
  - `source` text, e.g. `massive`, `alpha_vantage`, `yfinance`
  - `adjusted` boolean default false
  - `raw_payload` jsonb nullable
  - `created_at` timestamptz default now()
- [ ] Add unique guard on `(ticker, timeframe, bar_time, source)`.
- [ ] For now, do not spend much time on advanced price analytics.
- [ ] Later: pull hourly OHLC values for watchlist tickers only, not all biotech leads.
- [ ] Later: compute event-window returns around catalyst dates: T-1d, T+1h, T+1d, T+5d.

#### Table 3: `cq_market_events` — required

Use case:
- Store structured market/catalyst events that CQ-Selector can score and deduplicate.
- This is the most important table after `cq_regulatory_catalysts` because it becomes the normalized event queue.

Checklist:
- [ ] Create Supabase table `cq_market_events`.
- [ ] Suggested columns:
  - `id` UUID primary key
  - `ticker` text, indexed
  - `company_name` text nullable
  - `event_type` text, e.g. `pr_wire`, `sec_8k`, `fda`, `earnings`, `trial_readout`, `analyst`, `partnership`, `financing`, `stock_move`, `news_link`
  - `event_title` text
  - `event_summary` text nullable
  - `event_url` text nullable
  - `source` text
  - `event_time` timestamptz nullable
  - `detected_at` timestamptz default now()
  - `severity_score` numeric nullable
  - `novelty_score` numeric nullable
  - `selector_status` text default `new`, e.g. `new`, `selected`, `rejected`, `duplicate`, `needs_research`
  - `raw_payload` jsonb nullable
- [ ] Add unique guard on `(ticker, event_url)` where `event_url` is not null.
- [ ] Later add fuzzy dedup against title/date/source.
- [ ] Feed PR Wire, SEC, FDA, and free ticker-news links into this table as normalized events.
- [ ] CQ-Selector should read from `cq_market_events` first, then decide what deserves deep research.

### Free Stock/Ticker News Sources — Recommended Lightweight Pattern

Question: can we use a free stock-market news source related to our tickers, like Yahoo Finance, and have Selector read/summarize the link instead of saving unnecessary full articles in DB?

Answer: yes, that is possible and it is the better first version.

Recommended pattern:
- Do not store full articles in DB at first.
- Store only metadata:
  - ticker
  - headline
  - URL
  - source
  - published time if available
  - short summary if available
  - fetch timestamp
- CQ-Selector receives candidate links from `cq_market_events` / `cq_market_sentiment`.
- CQ-Selector opens/reads only the few selected links it actually needs to summarize.
- This keeps the DB lean and avoids hoarding low-value news text.

Verified free Yahoo Finance option:
- The Yahoo Finance ticker RSS pattern works:
  `https://feeds.finance.yahoo.com/rss/2.0/headline?s=CRSP&region=US&lang=en-US`
- Test result for `CRSP`: HTTP 200, XML RSS feed returned.
- The regular Yahoo Finance webpage path may block/scrape poorly; use RSS, not page scraping.

Potential free/low-cost sources to evaluate:
- Yahoo Finance ticker RSS — good first source for headline links.
- Alpha Vantage `NEWS_SENTIMENT` — already credentialed; good for sentiment metadata.
- SEC EDGAR RSS/company filings — already in Phase 1.
- PRNewswire / GlobeNewswire RSS — already in Phase 1.
- Company investor-relations RSS pages — useful but must be per-company and slower to maintain.

Operational rule:
- First build link-level ingestion, not article-hoarding.
- Save metadata and links in Supabase.
- Let CQ-Selector decide which links are worth reading and summarizing.
- Only store extracted article text later if there is a clear product reason.

### Canonical Ticker Mapping Solution — Reverse the Direction

Problem found:
- BioCrawler company-name → ticker fuzzy matching is dangerous.
- Earlier fuzzy matching caused wrong ticker/company mappings.
- Wrong mappings are catastrophic because they pollute SEC checks, market news, price analytics, and clinical-trial/company joins.
- Current local BioCrawler DB has 658 companies but only 23 rows with a non-empty `ticker` field.
- Some current metadata is visibly suspect, e.g. wrong website/ticker-style mappings can enter the lead table.

Decision:
- Do **not** make BioCrawler company names the source of truth for tickers.
- Reverse the direction.
- Create a canonical Supabase table called `biotech_tickers`.
- Pull ticker → company name → exchange → CIK/FIGI/other metadata from market/security-master sources first.
- Then use that verified ticker registry to match back to BioCrawler, clinical trials, SEC filings, and market news.

Why this is better:
- Tickers are structured identifiers; scraped company names are messy text.
- Market/security-master sources know the listed entity, exchange, active/delisted status, and sometimes CIK.
- SEC matching should prefer CIK/ticker from `biotech_tickers`, not fuzzy company names.
- ClinicalTrials matching can then use aliases from the verified listed company table.
- News parsing becomes safer: query by ticker and verified company aliases, then store links/events against `ticker_id`.

#### Required Table: `biotech_tickers`

Use case:
- Canonical listed-biotech/security registry.
- Every market-news, price-bar, SEC, and catalyst event should reference this table when possible.
- This becomes the bridge between stock-market data and BioCrawler company/clinical-trial data.

Checklist:
- [ ] Create Supabase table `biotech_tickers`.
- [ ] Suggested columns:
  - `id` UUID primary key
  - `ticker` text not null
  - `exchange` text nullable
  - `company_name` text not null
  - `company_name_normalized` text nullable
  - `legal_name` text nullable
  - `cik` text nullable
  - `figi` text nullable
  - `isin` text nullable
  - `cusip` text nullable
  - `country` text nullable
  - `sector` text nullable
  - `industry` text nullable
  - `is_biotech` boolean default false
  - `is_active_listing` boolean default true
  - `source` text, e.g. `alpha_vantage`, `massive`, `yfinance`, `nasdaq`, `manual_review`
  - `source_confidence` numeric nullable
  - `raw_payload` jsonb nullable
  - `created_at` timestamptz default now()
  - `updated_at` timestamptz default now()
- [ ] Add unique guard on `(ticker, exchange)`.
- [ ] Add index on `cik`.
- [ ] Add index on `company_name_normalized`.
- [ ] Add optional alias table later: `biotech_ticker_aliases` with `ticker_id`, `alias`, `alias_type`, `source`.

#### Matching Rule Going Forward

Safe matching hierarchy:
1. Exact ticker + exchange match.
2. Exact CIK match.
3. Exact normalized legal/company name match against `biotech_tickers` or aliases.
4. High-confidence alias match only if reviewed/approved.
5. Fuzzy name match is allowed only as a candidate suggestion, never as an automatic write.

Never again:
- Do not automatically write fuzzy ticker matches into production tables.
- Do not run SEC/news/price pulls from unverified BioCrawler ticker guesses.
- Do not trust company-name-only joins for listed-company workflows.

#### New Dataflow

Preferred direction:

`Market/security source → biotech_tickers → market news / price bars / SEC pulls → match back to BioCrawler + clinical trials`

Not preferred:

`BioCrawler scraped company name → fuzzy ticker guess → SEC/market/news pulls`

#### How It Solves CQ News + Clinical Trials

Once `biotech_tickers` exists:
- Market news pulls use verified tickers.
- Yahoo Finance RSS/Alpha Vantage queries use verified tickers.
- SEC monitors can use ticker/CIK from the canonical table.
- ClinicalTrials matching can reverse-search BioCrawler companies against verified listed-company names and aliases.
- CQ-Selector can reason over one stable `ticker_id`, instead of fragile free-text company names.

#### Implementation Checklist

- [ ] Create `biotech_tickers` table in Supabase.
- [ ] Create optional `biotech_ticker_aliases` table.
- [ ] Create ingestion script: `scripts/market_data/build_biotech_ticker_registry.py`.
- [ ] Seed registry from a reliable listing source first.
- [ ] Enrich with Alpha Vantage/Massive/Yahoo metadata where available.
- [ ] Store CIK where available for SEC-safe joins.
- [ ] Add manual review flag for uncertain mappings.
- [ ] Backfill only high-confidence matches from `biotech_tickers` into BioCrawler/ClinicalTrials joins.
- [ ] Update `cq_market_sentiment`, `cq_price_bars`, and `cq_market_events` to carry `ticker_id` as a foreign key to `biotech_tickers`.
- [ ] Update CQ-Selector instructions: use `biotech_tickers` as source of truth for listed-company identity.

---

## CQ Paperclip Trigger Architecture — First Principles Index

This section is the canonical reference for how the CQ-Free Newsletter workflow triggers Paperclip agents. It exists because creating a Paperclip issue is not the same as making an agent act unless the issue is assigned correctly and the agent is explicitly woken.

### Final CQ Workflow Chain

Manual test path:

`Manual Test Trigger → Run CQ Detection via Ops API → Create CQ-Selector Paperclip Issue → Wake CQ-Selector Agent → Create CQ-Monitor Paperclip Issue → Wake CQ-Monitor Agent → Send Latest CQ Report Telegram via Ops API`

Scheduled path:

`Daily Schedule 11:00 UTC → Run CQ Detection via Ops API → Create CQ-Selector Paperclip Issue → Wake CQ-Selector Agent → Create CQ-Monitor Paperclip Issue → Wake CQ-Monitor Agent → Send Latest CQ Report Telegram via Ops API`

### First-Principles Explanation

1. **n8n is only the scheduler/router.** It does not run CQ-Selector itself.
2. **n8n starts from either a Manual Test Trigger or the Daily Schedule.** Manual tests should use `Manual Test Trigger`, not the Schedule node, because Schedule Trigger manual runs can stop at the trigger without emitting downstream data.
3. **n8n calls the local Ops API:** `POST http://127.0.0.1:8765/cq/detect`.
4. **Ops API runs CQ detection scripts:** SEC 8-K monitor, FDA PDUFA tracker, and PR wire aggregator. Long/hanging scripts are bounded by timeouts.
5. **n8n creates a Paperclip issue for CQ-Selector.** This issue is the work order.
6. **The issue must be assigned using `assigneeAgentId`, not `assignee`.** Paperclip ignores the short `assignee` field for agent execution.
7. **n8n explicitly wakes CQ-Selector after issue creation.** This makes action deterministic instead of waiting for heartbeat.
8. **n8n then creates and wakes CQ-Monitor.** Monitor checks/accountability happens after Selector issue creation.
9. **Ops API sends Telegram status/daily report.** Telegram delivery stays out of n8n Telegram nodes.

### Critical Paperclip IDs

- Paperclip company: `The Clinical Quant`
- Company ID/API bearer token: `cf39ae28-5bd5-44d1-b888-b01f83192fd5`
- CQ-Selector agent ID: `31049770-807e-4e82-9a87-15ccdb43845f`
- CQ-Monitor agent ID: `bb9deb04-97d7-4f35-89bc-130f67d8f759`
- CQ-Researcher agent ID: `26105f52` prefix in memory; verify full UUID before wiring direct wakeups.

### Correct Paperclip Issue Body Pattern

Use this field:

```json
{
  "title": "CQ Daily Catalyst Selection",
  "description": "...",
  "priority": "high",
  "status": "backlog",
  "assigneeAgentId": "31049770-807e-4e82-9a87-15ccdb43845f"
}
```

Do **not** use only:

```json
{
  "assignee": "31049770"
}
```

That created THE-6 as an issue but left `assigneeAgentId = null`, so CQ-Selector did not act.

### Deterministic Wakeup Pattern

After creating the assigned issue, immediately call:

```http
POST http://localhost:3100/api/agents/31049770-807e-4e82-9a87-15ccdb43845f/wakeup
Authorization: Bearer cf39ae...2fd5
Content-Type: application/json
```

Payload pattern:

```json
{
  "source": "automation",
  "triggerDetail": "system",
  "reason": "issue_assigned",
  "payload": {
    "issueId": "<created_issue_id>",
    "mutation": "create",
    "source": "n8n-cq-workflow"
  },
  "idempotencyKey": "cq-selector-<issue_identifier>"
}
```

For CQ-Monitor, use:

```http
POST http://localhost:3100/api/agents/bb9deb04-97d7-4f35-89bc-130f67d8f759/wakeup
```

### What Actually Happened During SWIP4 Debugging

- n8n successfully created THE-6.
- THE-6 was created with `assigneeAgentId = null` because the workflow used the wrong field, `assignee`.
- Therefore, CQ-Selector did not wake or start.
- The correct route to patch an issue is `PATCH /api/issues/:id`, not `/api/companies/:companyId/issues/:id`.
- Once THE-6 was assigned with the full CQ-Selector UUID and CQ-Selector was explicitly woken, Paperclip changed THE-6 to `in_progress` and CQ-Selector status became `running`.

### Operational Rule

Do not rely on “the agent will wake later” for daily production CQ. Heartbeat exists but can delay action. Production automation must do both:

1. Create issue with correct `assigneeAgentId`.
2. Immediately call the assigned agent’s `/wakeup` endpoint.

### Current n8n CQ Workflow Node Inventory

The intended final node inventory is:

- `Manual Test Trigger` — built-in manual trigger for immediate dry runs
- `Daily Schedule 11:00 UTC` — built-in schedule trigger for production
- `Run CQ Detection via Ops API` — HTTP Request to local Ops API
- `Create CQ-Selector Paperclip Issue` — HTTP Request to Paperclip issue API using `assigneeAgentId`
- `Wake CQ-Selector Agent` — HTTP Request to Paperclip agent wakeup API
- `Create CQ-Monitor Paperclip Issue` — HTTP Request to Paperclip issue API using `assigneeAgentId`
- `Wake CQ-Monitor Agent` — HTTP Request to Paperclip agent wakeup API
- `Send Latest CQ Report Telegram via Ops API` — HTTP Request to Ops API

No CQ workflow node should be:

- n8n Telegram Trigger
- n8n Telegram Send node
- n8n Code node
- n8n Execute Command node
- custom/private node

### Verification Checklist

- [ ] Hard refresh n8n UI after DB-level workflow JSON edits.
- [ ] Run from `Manual Test Trigger`, not the Daily Schedule node, for immediate testing.
- [ ] Confirm new Paperclip issue has non-null `assigneeAgentId`.
- [ ] Confirm CQ-Selector issue transitions from `backlog` to `in_progress`.
- [ ] Confirm CQ-Selector agent status becomes `running`.
- [ ] Confirm CQ-Monitor issue and wakeup run after Selector issue creation.
- [ ] Confirm Telegram status/report arrives through Ops API.

## n8n Fix Reference — Do/Don't

**Final working architecture:**

`n8n Schedule Trigger → n8n HTTP Request → local Python Ops API → local Python scripts / Telegram / Paperclip`

**Why this works:**
- n8n only handles scheduling and HTTP orchestration.
- Python owns filesystem, subprocess, SQLite, Telegram API, Paperclip API, and long-running script logic.
- All n8n nodes are standard built-ins recognized by the UI.

**What failed and should not be repeated:**
- Telegram Trigger nodes: fail on localhost because Telegram requires HTTPS webhook URLs.
- n8n Code nodes with `require()`: sandbox blocks `child_process`, `https`, `fs`, `better-sqlite3`, etc.
- Execute Command nodes: present in package but UI treated them as unrecognized/disabled in this n8n 2.17.7 setup.
- Private/custom node Docker installation: not applicable because we were not creating a custom node type.
- Direct DB credential writing: unsafe because n8n encrypts credentials; use UI/API only.

**Files created/modified for the fix:**
- `07_DevOps_Observability/meddash_ops_api.py` — local HTTP API used by n8n; patched to handle BrokenPipe/ConnectionReset cleanly when browser/n8n/curl disconnects before a long engine response is written
- `07_DevOps_Observability/meddash_pipeline_runner.py` — Python wrapper for Meddash engines
- `03_BioCrawler_GTM/biocrawler.py` — patched to respect `DISABLE_INTERNAL_TELEGRAM=1`
- n8n SQLite workflow JSON — operational workflows rebuilt with Schedule Trigger + HTTP Request only

**Engine 03 BioCrawler note:**
- Original command `biocrawler.py --mode all` can exceed n8n/Ops API execution windows due slow deep crawl enrichment.
- Scheduled command now uses `biocrawler.py --mode test` for reliable daily bounded sync.
- Full deep BioCrawler should be run manually or as a separate long-running Paperclip/background task, not in the clockwork daily n8n chain.