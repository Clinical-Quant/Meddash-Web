# Chat / Session Archive — MDP3 Pipeline Finalization + Architecture Blueprint

Archived: 2026-04-29 12:00:39 EDT
Project: MEDDASH-CQ / MDP3
Session type: operational build + architecture preservation
Primary human: Dr. Don
Assistant persona: Alfred Chief

This archive is intentionally detailed. It preserves the practical sequence of work, fixes, decisions, files, and caveats from the session so future agents do not have to reconstruct the pipeline from memory.

---

## 0. User’s final preservation request

Dr. Don requested a graph memory node and a chat archive in a `.archive` folder with everything done in this session, without over-summarizing, because the steps are important for future operations.

This file is that chat/session archive.

---

## 1. Session starting context

The session continued after a large MDP3 operational build where the goal was to finalize the Meddash + Clinical Quant automation stack to a functioning ~98% level.

The key live systems involved:

- Meddash organized backend:
  `/mnt/c/Users/email/.gemini/antigravity/Meddash_organized_backend/`
- CQ Team scripts:
  `/mnt/c/Users/email/.gemini/antigravity/CTO/CQ_Team/scripts/`
- Meddash Phase 3 operating folder:
  `/mnt/c/Users/email/.gemini/antigravity/Meddash Phase 3 Automation Observation and Sales/`
- Hermes/Obsidian vault:
  `/mnt/c/Users/email/Hermes Agent Win Files/`
- n8n local DB:
  `/home/doc_victus/.n8n/database.sqlite`
- Ops API:
  `http://127.0.0.1:8765`
- n8n:
  `http://127.0.0.1:5678`
- Paperclip:
  `http://127.0.0.1:3100`
- Streamlit dashboard:
  `http://localhost:5090`

Important principles applied:

- n8n is only the clock/router.
- Ops API is the local execution bridge.
- Paperclip agents are the reasoning workers.
- Telegram is centralized through Ops API, not n8n Telegram nodes.
- Supabase is the shared cloud data layer.
- Local SQLite DBs remain important engine state/data stores.
- Obsidian/Hermes vault is the durable operational brain.
- No secrets are documented; credentials remain `[REDACTED]`.

---

## 2. CQ ticker-spine finalization

### 2.1 Problem being solved

The older CQ data path was unsafe because BioCrawler company names and weak ticker fields could drive market/news/SEC pulls. That created risk of fuzzy company-name → wrong ticker → wrong catalyst/news mapping.

The corrected direction was:

```text
market/security source → biotech_tickers → market/news/price/SEC pulls → reverse-match BioCrawler + clinical trials
```

Not:

```text
BioCrawler scraped company name → fuzzy ticker guess → SEC/market/news pulls
```

### 2.2 Supabase ticker spine schema

Created/applied migration-safe schema:

`/mnt/c/Users/email/.gemini/antigravity/CTO/CQ_Team/scripts/market_data/create_ticker_spine_schema.sql`

Created schema applier:

`/mnt/c/Users/email/.gemini/antigravity/CTO/CQ_Team/scripts/market_data/apply_ticker_spine_schema.py`

The schema/migration created or safely updated:

- `biotech_tickers`
- `biotech_ticker_aliases`
- `biocrawler_ticker_matches`
- `cq_market_sentiment`
- `cq_price_bars`
- `cq_market_events`

The first schema attempt failed because some market/event table names already existed but did not have the new `ticker_id` column. The SQL was rewritten to be migration-safe using `CREATE TABLE IF NOT EXISTS` and `ALTER TABLE ADD COLUMN IF NOT EXISTS` patterns.

### 2.3 Ticker registry builder

Created:

`/mnt/c/Users/email/.gemini/antigravity/CTO/CQ_Team/scripts/market_data/build_biotech_ticker_registry.py`

The first run timed out after 180 seconds because the initial implementation used many individual upserts. The builder was patched to use bulk upserts. After patching, it completed successfully.

Final reported output:

- Alpha/listing rows: 13,320
- SEC ticker rows: 10,348
- `biotech_tickers` upserted: 13,257
- exact BioCrawler reverse matches: 126
- existing ticker candidates: 68
- fuzzy auto-writes: 0

### 2.4 Actual Supabase counts after implementation

A later verification query showed:

- `biotech_tickers`: 13,257
- `biotech_ticker_aliases`: 13,257
- `biocrawler_ticker_matches`: 194
- `cq_market_sentiment`: 111
- `cq_price_bars`: 0
- `cq_market_events`: 111

### 2.5 Old fuzzy ticker path disabled

The old risky fuzzy script was disabled:

- Guard stub now at:
  `/mnt/c/Users/email/.gemini/antigravity/CTO/CQ_Team/scripts/enrich_tickers.py`

- Original preserved as disabled artifact:
  `/mnt/c/Users/email/.gemini/antigravity/CTO/CQ_Team/scripts/enrich_tickers.py.DISABLED_FUZZY_DO_NOT_RUN`

Decision: production code must not write fuzzy ticker guesses into `biotech_leads`.

---

## 3. CQ runner and Ops API coupling

### 3.1 CQ runner patched

Patched:

`/mnt/c/Users/email/.gemini/antigravity/CTO/CQ_Team/scripts/cq_pipeline_runner.py`

The runner now includes:

- ticker spine refresh stage
- Yahoo ticker-news link stage
- existing Phase 1 regulatory detection stages:
  - SEC 8-K monitor
  - FDA/PDUFA tracker
  - PR Wire aggregator

The command surface includes:

- `detect`
- `ticker_spine`
- `yahoo_ticker_news`
- `select_file`

### 3.2 Phase 1 regulatory scripts patched to use ticker spine

Patched:

- `/mnt/c/Users/email/.gemini/antigravity/CTO/CQ_Team/scripts/phase1_regulatory/sec_8k_monitor.py`
- `/mnt/c/Users/email/.gemini/antigravity/CTO/CQ_Team/scripts/phase1_regulatory/fda_pdufa_tracker.py`
- `/mnt/c/Users/email/.gemini/antigravity/CTO/CQ_Team/scripts/phase1_regulatory/pr_wire_aggregator.py`

These scripts were moved away from `biotech_leads.ticker` and toward the canonical ticker spine / exact reverse matches.

Notes from successful run:

- PR Wire fetched 125 verified targets.
- FDA analyzed 237 verified aliases.
- CQ run completed successfully.

### 3.3 Yahoo Finance RSS link ingestion

Created:

`/mnt/c/Users/email/.gemini/antigravity/CTO/CQ_Team/scripts/market_data/pull_yahoo_ticker_news.py`

Purpose:

- lightweight ticker-news metadata ingestion
- stores links/headlines/source/published time only
- does not store full articles

Current verified output:

- 40 tickers scanned
- 111 Yahoo Finance RSS news links stored
- written to `cq_market_sentiment` and `cq_market_events`

### 3.4 Ops API ticker-spine endpoint

Patched:

`/mnt/c/Users/email/.gemini/antigravity/Meddash_organized_backend/07_DevOps_Observability/meddash_ops_api.py`

Added route:

`POST /cq/ticker-spine`

This calls:

```text
python3 cq_pipeline_runner.py ticker_spine
```

Verification:

- Ops API restarted.
- `/health` returned OK.
- `/cq/ticker-spine` returned success.
- elapsed around 12.28 seconds in a verified run.

Note: one background process notification later reported an Ops API process was listening on `127.0.0.1:8765`. The relevant endpoint was verified after restart.

---

## 4. n8n workflow corrections

### 4.1 User asked whether the last ticker engine trigger was added to n8n

Initial answer after inspection:

- No, not originally as a visible separate n8n node.
- The ticker spine was running inside `/cq/detect`, but n8n did not yet show a dedicated ticker engine trigger.

### 4.2 Added visible ticker trigger to CQ-Free Newsletter n8n workflow

Patched workflow in:

`/home/doc_victus/.n8n/database.sqlite`

CQ workflow ID used:

`dfb3zednYhdcdqxE`

Added node:

`Run CQ Ticker Spine via Ops API`

Endpoint:

`POST http://127.0.0.1:8765/cq/ticker-spine`

Rewired chain:

```text
Daily Schedule 11:00 UTC
→ Run CQ Ticker Spine via Ops API
→ Run CQ Detection via Ops API
→ Create CQ-Selector Paperclip Issue
→ Create CQ-Monitor Paperclip Issue
→ Send Latest CQ Report Telegram via Ops API
```

### 4.3 Paperclip issue assignment/wakeup correction

While building the architecture inventory, a live bug was found:

- CQ n8n Paperclip issue nodes still used short `assignee` fields.
- They did not have explicit wakeup nodes.

Corrected:

- Replaced short `assignee` with full `assigneeAgentId`.
- Corrected CQ-Monitor assignment.
- Added explicit wakeup nodes:
  - `Wake CQ-Selector Agent`
  - `Wake CQ-Monitor Agent`

Correct Paperclip rule:

```text
Create issue with assigneeAgentId → call POST /api/agents/:id/wakeup
```

Important UUIDs:

- Company: `cf39ae28-5bd5-44d1-b888-b01f83192fd5`
- CQ-Selector: `31049770-807e-4e82-9a87-15ccdb43845f`
- CQ-Monitor: `bb9deb04-97d7-4f35-89bc-130f67d8f759`

No Paperclip credential values were archived.

### 4.4 n8n caveat

n8n workflow DB showed main workflows with `active=0` during architecture mapping.

Operational caveat:

- After DB-level patches, the n8n UI should be hard-refreshed.
- Intended workflows should be toggled active in UI.

---

## 5. Architecture markdown blueprint creation

### 5.1 User request

Dr. Don requested a timestamped architecture markdown file in the Meddash Phase 3 folder:

```text
mdp3.architecture<date/time>.md
```

It had to map every granular step in the system:

- n8n triggers
- Telegram triggers
- n8n scripts/endpoints
- Paperclip agents
- all interconnections/dependencies
- Meddash pipeline
- CQ pipeline
- local DB updates
- Supabase connections
- workflow reversal
- triarchical/quariarchical system
- internal/external dependencies
- Mermaid diagrams
- no shortcuts

### 5.2 Created architecture markdown

Created:

`/mnt/c/Users/email/.gemini/antigravity/Meddash Phase 3 Automation Observation and Sales/mdp3.architecture.20260429-0215.md`

Initial file details:

- about 47 KB initially
- 1,363 lines initially
- secret scan passed

After later no-loose-ends addendum:

- 72,330 bytes
- 1,732 lines

### 5.3 Content included in the architecture markdown

The blueprint includes:

- live n8n workflow maps
- Meddash daily workflow
- CQ daily workflow
- Ops API route map
- Meddash engine internals
- CQ ticker spine / Yahoo / SEC / FDA / PR internals
- Supabase tables and current counts
- local SQLite DBs and counts
- Paperclip agent roster and hierarchy
- Telegram trigger paths
- Hermes/Obsidian/Agent Zero relationship
- disabled/deprecated scripts
- major dependencies and guardrails
- multiple Mermaid diagrams ready for HTML conversion

### 5.4 SWIP4 updated for architecture source

Updated:

`/mnt/c/Users/email/.gemini/antigravity/Meddash Phase 3 Automation Observation and Sales/MDP3-SWIP4.md`

D.1 marked complete with architecture source artifact path and notes.

---

## 6. HTML architecture atlas creation

### 6.1 User asked whether HTML or Streamlit was better

Recommendation made:

- Use standalone pure HTML first.
- Optionally embed into Streamlit later.

Reasoning:

- complex architecture diagrams need full-browser space
- Streamlit constrains layout and looks dashboard-like/bland for this use case
- pure HTML supports full-page atlas, sticky nav, animated maps, collapsible sections, search/filter, better visual hierarchy
- Streamlit should remain the operational cockpit, not the architecture atlas renderer

### 6.2 Created standalone HTML atlas

Created:

`/mnt/c/Users/email/.gemini/antigravity/Meddash Phase 3 Automation Observation and Sales/mdp3.architecture.20260429-0215.html`

Initial verified file:

- 125,393 bytes
- opened in browser successfully
- browser console: 0 JS errors
- obvious secret-pattern scan passed

After no-loose-ends patch:

- 147,324 bytes
- 2,542 lines
- HTML parser OK
- browser console: 0 JS errors
- secret scan clean

### 6.3 Initial HTML contents

Initial atlas included:

- dark Tailwind-style visual design
- sticky sidebar navigation
- search/filter box
- animated SVG master architecture map
- Meddash daily pipeline timeline
- CQ daily pipeline timeline
- n8n workflow surface
- Ops API route map
- Supabase table cards with counts
- local SQLite DB counts
- Paperclip agent roster
- Telegram paths
- guardrails / disabled paths
- current gaps/watch items
- external source surface
- 12 rendered Mermaid diagrams from source architecture
- full source markdown appendix

### 6.4 User identified missing details

Dr. Don correctly observed that the first HTML/master map missed or under-mapped critical items:

- data sources were not explicitly mapped on the master map
- source modality was missing: XML crawl vs API-based vs RSS vs HTML crawl vs manual
- manual KOL brief generator was missing
- front-end dashboard was missing
- deduplication engine was missing
- CQ free newsletter path was not granular enough
- Phase 2 workflow architecture had more detail

Reference file given:

`C:\Users\email\.gemini\antigravity\CTO\MEDDASH_BACKEND_WORKFLOW\ver 2.0_organized_meddashbackend_schema.txt`

WSL path:

`/mnt/c/Users/email/.gemini/antigravity/CTO/MEDDASH_BACKEND_WORKFLOW/ver 2.0_organized_meddashbackend_schema.txt`

### 6.5 Phase 2 architecture reference read

The Phase 2 file mapped:

- Next.js 15 local SaaS UI
- dashboard UI page
- crawler control/execution UI
- campaign sandbox validation UI
- Scholar enrichment UI
- system health/log streaming UI
- FastAPI `api_server.py` REST bridge
- KOL data engine
- Scholar engine
- CT data engine
- BioCrawler GTM
- TA landscape engine
- MDM ontology engine
- shared datastores
- PubMed NCBI API/XML
- ClinicalTrials.gov API
- Clearbit/SEC/EDGAR deep scan
- Google Sheets CRM sync
- disease criteria ontology layer
- Gemini fallback/HITL lanes

### 6.6 No-loose-ends architecture patch

Patched markdown and HTML with a major addendum:

Markdown addendum title:

`Architecture Addendum — No-Loose-Ends Operational Blueprint Patch`

HTML section ID:

`no-loose-ends-patch`

Sidebar link added:

`No-Loose-Ends Patch`

### 6.7 Data source matrix added

Added explicit source/modality/consumer/persistence notes for:

1. PubMed / NCBI — API + XML/JSON extraction
2. ORCID identifiers in publication metadata
3. SCImago / journal metrics
4. ClinicalTrials.gov v2 — API JSON
5. ClinicalTrials.gov nested records
6. BioCrawler company discovery — API mode + HTML/deep crawl
7. Company websites / IR pages — HTML crawl
8. Clearbit / company enrichment — API-based where configured
9. SEC EDGAR company filings — API/JSON/filing text
10. SEC ticker/CIK mapping — SEC JSON/listing map
11. Alpha Vantage LISTING_STATUS — API CSV/listing source
12. Alpha Vantage NEWS_SENTIMENT — API JSON prototype
13. Yahoo Finance ticker headline RSS — RSS/XML
14. PR Newswire / GlobeNewswire / BusinessWire-like feeds — RSS/XML
15. FDA/PDUFA public data — public scrape/API-like parse
16. Massive market data — API/prototype
17. Google Scholar via SerpApi — API + manual URL/ID mode
18. UMLS/disease ontology APIs — API
19. Google Sheets CRM — Sheets API/manual sync
20. Supabase Postgres/REST
21. local SQLite shared datastores
22. n8n workflow DB
23. Paperclip API
24. Telegram Bot API
25. Obsidian/Hermes Agent Win Files
26. Substack manual publishing
27. LinkedIn manual publishing
28. X/Twitter planned Paperclip/X bot
29. Base44 Meddash lite/search web surface
30. Streamlit Meddash-CQ Dashboard

### 6.8 Deduplication/identity gates added

Explicitly mapped:

- KOL identity Tier 1: `kol_disambiguator.py`
- KOL identity Tier 2: sandbox/manual duplicate review through UI/API
- KOL identity Tier 3: deep disambiguation queue
- Scholar identity: `sync_scholar_citations.py` 4-tier matching
- Centrality reliability: duplicate-warning penalty in `reliability.py`
- Ticker identity: `build_biotech_ticker_registry.py`
- Old ticker enrichment guard: `enrich_tickers.py` stub
- CQ posted catalyst dedup: `posted-events-log.md`
- CQ source/link dedup: Yahoo/PR source URL uniqueness patterns
- Paperclip issue dedup/trace: issue/comment history
- n8n workflow dedup/run discipline

### 6.9 Manual KOL brief generator lane added

Added:

- generator:
  `/mnt/c/Users/email/.gemini/antigravity/Meddash_organized_backend/04_Product_KOL_Briefs/generate_kol_brief.py`
- export helper:
  `/mnt/c/Users/email/.gemini/antigravity/Meddash_organized_backend/04_Product_KOL_Briefs/export_kols.py`
- output dir:
  `/mnt/c/Users/email/.gemini/antigravity/Meddash_organized_backend/04_Product_KOL_Briefs/kol_briefs/`

Current outputs include:

- `kol_brief_kras_g12c_lung_cancer.md`
- `kol_brief_kras_g12c_lung_cancer.json`
- TA Landscape Markdown/chart files for KRAS examples

Generator dependencies:

- `ct_trials.db`
- `meddash_kols.db`
- trial investigators
- trial sponsors
- trial phase/status
- eligibility/biomarkers
- CT↔KOL bridge outputs
- publications/journal/SJR/KOL therapeutic area metadata

Scoring:

- 50% trial activity
- 30% publication signal
- 20% indication specificity

Outputs:

- Markdown human-readable KOL intelligence brief
- JSON machine-readable output for future SaaS/API/dashboard

### 6.10 Dashboard/front-end lane added

Added current Streamlit dashboard:

`/mnt/c/Users/email/.gemini/antigravity/CTO/Meddash-CQ_Dashboard/`

Important files mapped:

- `app.py`
- `config.py`
- `supabase_client.py`
- `widgets/factory_floor.py`
- `widgets/pulse.py`
- `widgets/pipeline_health.py`
- `widgets/meddash_panel.py`
- `widgets/cq_panel.py`
- `widgets/kol_ingest.py`
- `widgets/operations.py`
- `widgets/meddash_crm.py`

Dashboard dependencies:

- Supabase
- local SQLite DBs:
  - `meddash_kols.db`
  - `ct_trials.db`
  - `biocrawler_leads.db`
- KOL brief output folder
- TA landscape output folder

Phase 2 UI lineage added:

- Next.js 15 local SaaS UI pages
- FastAPI `api_server.py` REST bridge
- subprocess manager
- sandbox dedup/commit endpoints
- manual Scholar endpoints

### 6.11 CQ Free Newsletter path added

Explicit path now mapped:

```text
n8n Daily Schedule / Manual Test Trigger
→ Run CQ Ticker Spine via Ops API
→ Run CQ Detection via Ops API
→ meddash_ops_api.py
→ cq_pipeline_runner.py detect
→ build_biotech_ticker_registry.py
→ pull_yahoo_ticker_news.py
→ sec_8k_monitor.py
→ fda_pdufa_tracker.py
→ pr_wire_aggregator.py
→ Supabase ticker/news/catalyst tables
→ Create CQ-Selector Paperclip Issue with assigneeAgentId
→ Wake CQ-Selector
→ CQ-Selector reads catalysts + posted-events log
→ dedup/select/research/draft
→ create or use CQ-Researcher path if catalyst exists
→ write daily brief draft in Obsidian newsletter folder
→ Create CQ-Monitor Paperclip Issue with assigneeAgentId
→ Wake CQ-Monitor
→ Monitor QA/status/logging
→ Ops API latest report / Telegram alert
→ Dr. Don manual review
→ manual Substack publish
→ manual LinkedIn publish
```

Newsletter files:

- drafts:
  `/mnt/c/Users/email/Hermes Agent Win Files/projects/clinical-quant/newsletter/`
- current example:
  `2026-04-29-daily-brief.md`
- dedup log:
  `/mnt/c/Users/email/Hermes Agent Win Files/projects/clinical-quant/posted-events-log.md`
- template:
  `/mnt/c/Users/email/Hermes Agent Win Files/projects/clinical-quant/daily-brief-template.md`
- design reference:
  `/mnt/c/Users/email/Hermes Agent Win Files/projects/clinical-quant/newsletter-pipeline-design.md`

### 6.12 Final validation after no-loose-ends patch

Final markdown:

- path: `mdp3.architecture.20260429-0215.md`
- bytes: 72,330
- lines: 1,732
- contains:
  - No-Loose-Ends
  - Data Source
  - KOL Brief
  - Dashboard
  - Dedup
  - CQ Free Newsletter
  - Phase 2
- suspicious secret patterns: none

Final HTML:

- path: `mdp3.architecture.20260429-0215.html`
- bytes: 147,324
- lines: 2,542
- HTML parser OK
- browser opened successfully
- browser console: 0 JS errors
- contains:
  - No-Loose-Ends
  - Data Source
  - KOL Brief
  - Dashboard
  - Dedup
  - CQ Free Newsletter
  - Phase 2
- suspicious secret patterns: none

One false positive secret scan hit was `sk-` inside the CSS property `mask-image`; it was removed to keep future scans clean.

---

## 7. SWIP4 updates

Updated the operational index:

`/mnt/c/Users/email/.gemini/antigravity/Meddash Phase 3 Automation Observation and Sales/MDP3-SWIP4.md`

Main updates added during this session:

- ticker-spine schema/populator/old fuzzy disablement status
- n8n ticker trigger added
- architecture markdown source complete
- HTML architecture atlas complete
- HTML/markdown patched with no-loose-ends addendum after review
- Paperclip `assigneeAgentId` + wakeup correction documented

Current task state at end of session:

- `d-blueprint-source`: completed
- `d-blueprint-html`: completed
- `c-runs`: still in progress / next major operational item

---

## 8. Important files created or modified

### Architecture artifacts

- `/mnt/c/Users/email/.gemini/antigravity/Meddash Phase 3 Automation Observation and Sales/mdp3.architecture.20260429-0215.md`
- `/mnt/c/Users/email/.gemini/antigravity/Meddash Phase 3 Automation Observation and Sales/mdp3.architecture.20260429-0215.html`
- `/mnt/c/Users/email/.gemini/antigravity/Meddash Phase 3 Automation Observation and Sales/MDP3-SWIP4.md`

### Archive artifact

- `/mnt/c/Users/email/.gemini/antigravity/Meddash Phase 3 Automation Observation and Sales/.archive/20260429-120039-mdp3-pipeline-finalization-architecture-session.md`

### Ticker spine / CQ files

- `/mnt/c/Users/email/.gemini/antigravity/CTO/CQ_Team/scripts/market_data/create_ticker_spine_schema.sql`
- `/mnt/c/Users/email/.gemini/antigravity/CTO/CQ_Team/scripts/market_data/apply_ticker_spine_schema.py`
- `/mnt/c/Users/email/.gemini/antigravity/CTO/CQ_Team/scripts/market_data/build_biotech_ticker_registry.py`
- `/mnt/c/Users/email/.gemini/antigravity/CTO/CQ_Team/scripts/market_data/pull_yahoo_ticker_news.py`
- `/mnt/c/Users/email/.gemini/antigravity/CTO/CQ_Team/scripts/cq_pipeline_runner.py`
- `/mnt/c/Users/email/.gemini/antigravity/CTO/CQ_Team/scripts/phase1_regulatory/sec_8k_monitor.py`
- `/mnt/c/Users/email/.gemini/antigravity/CTO/CQ_Team/scripts/phase1_regulatory/fda_pdufa_tracker.py`
- `/mnt/c/Users/email/.gemini/antigravity/CTO/CQ_Team/scripts/phase1_regulatory/pr_wire_aggregator.py`
- `/mnt/c/Users/email/.gemini/antigravity/CTO/CQ_Team/scripts/enrich_tickers.py`
- `/mnt/c/Users/email/.gemini/antigravity/CTO/CQ_Team/scripts/enrich_tickers.py.DISABLED_FUZZY_DO_NOT_RUN`

### Ops/n8n/Paperclip-related files

- `/mnt/c/Users/email/.gemini/antigravity/Meddash_organized_backend/07_DevOps_Observability/meddash_ops_api.py`
- `/home/doc_victus/.n8n/database.sqlite`

### Reference files read/used

- `/mnt/c/Users/email/.gemini/antigravity/CTO/MEDDASH_BACKEND_WORKFLOW/ver 2.0_organized_meddashbackend_schema.txt`
- `/mnt/c/Users/email/Hermes Agent Win Files/SCHEMA.md`
- `/mnt/c/Users/email/Hermes Agent Win Files/index.md`
- `/mnt/c/Users/email/Hermes Agent Win Files/reference/meddash-backend-map.md`
- `/mnt/c/Users/email/Hermes Agent Win Files/concepts/meddash-data-spine.md`
- `/mnt/c/Users/email/Hermes Agent Win Files/projects/clinical-quant/newsletter-pipeline-design.md`
- `/mnt/c/Users/email/Hermes Agent Win Files/projects/clinical-quant/posted-events-log.md`

---

## 9. Operational decisions captured

1. Pure HTML is the best format for the architecture atlas; Streamlit remains the live operational cockpit.
2. The architecture atlas can later be embedded into Streamlit, but should not be authored as Streamlit-native UI.
3. Mermaid is useful for focused diagrams, but the top-level master map should be custom HTML/SVG/cards to avoid cramped spaghetti.
4. Ticker identity must be source-of-truth from market/security sources, not BioCrawler fuzzy name matching.
5. Old fuzzy ticker enrichment must stay disabled.
6. n8n must remain simple: schedule/manual trigger + HTTP Request nodes only.
7. Ops API owns local script execution and Telegram notification logic.
8. Paperclip issues must use full `assigneeAgentId` and explicit wakeup.
9. CQ newsletter publishing remains manual after agent draft, to avoid automated public-posting risk.
10. `posted-events-log.md` is append-only and is part of the CQ dedup mechanism.
11. The architecture blueprint is now an operational reference, not a decorative diagram.

---

## 10. Known caveats / next actions

### Caveats

- n8n workflow active flags were seen as `active=0`; UI hard refresh and manual activation may be required.
- Massive price-bar ingestion is table-ready but still prototype-level.
- Alpha Vantage news sentiment exists as prototype; Yahoo RSS is the current bounded production-ish link metadata stage.
- Streamlit dashboard is useful but visually older; the HTML atlas is the better architecture visualization.
- Base44 Meddash lite/search remains separate from meddash.ai and the Streamlit cockpit.
- Twitter/X bot is planned but not production-wired.

### Next major item

Continue `c-runs`:

- run/verify full Meddash pipeline
- run/verify full CQ pipeline through n8n/Ops/Paperclip
- confirm summaries
- confirm Telegram behavior
- confirm Paperclip issue assignment/wakeup/agent activity
- confirm CQ draft/report output

---

## 11. Graph-memory checkpoint linkage

Graph-memory node created for this session:

`MEM_MEDDASH-CQ_20260429_120337`

Expected graph-memory root:

`~/.hermes/graph-memory/`

This archive should be linked from the checkpoint as a chat/archive artifact.
