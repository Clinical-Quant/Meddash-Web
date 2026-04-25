# CEO Notes — 2026-04-24 (Plan #1 Ideated)

## Plan #1: MEDDASH-CQ FACTORY DASHBOARD — Ideated with AC Comments

### LAYER 1: THE PULSE (Top Bar — Always Visible)

| Widget | What It Shows | Why |
|--------|---------------|-----|
| Pipeline Heartbeat | Green/Yellow/Red per engine | Instant health check |
| KOLs in Database | Total count, new this week | Core asset size |
| Biotech Leads | Total, by tier (A/B/C) | Prospecting pipeline |
| CQ Catalysts Today | Count of new SEC 8K, FDA, PR events | Trading signal freshness |
| Revenue Funnel | Briefs sold / outreach sent / responses | Are we making money yet? |

AC:<add 3 things: (1) "Last Crawl" timestamp per engine — a green light that hasn't crawled in 6 hours is a lying green light, show STALENESS not just health. (2) "Data Delta" indicator — "+47 KOLs since yesterday" is more actionable than "12,341 total". Totals are vanity, deltas are decisions. (3) a dollar sign next to Revenue Funnel that turns from grey to green once the first $2,450 brief is sold — psychological anchor for the 30-day $3K goal.>

---

### LAYER 2: MEDDASH PANEL (Medical Affairs Engine)

| Section | Widget | Data Source |
|---------|--------|------------|
| KOL Engine | KOLs discovered / disambiguated / verified | kols + kols_staging + kol_merge_candidates |
| KOL Engine | Stuck in Tier 2/3 review queue | kol_merge_candidates + deep_disambiguation_needed count |
| CT Engine | Trials ingested / last crawl date | ct_trials count + ct_crawl_state.json |
| CT Engine | Trials by phase (I/II/III/IV) | ct_trials.phase aggregation |
| BioCrawler | Leads discovered / Tier A count | biotech_leads with tier breakdown |
| BioCrawler | Tickers populated vs missing | biotech_leads.ticker IS NULL ratio |
| Products | KOL Briefs generated (this month) | File count in 04_Product_KOL_Briefs/ |
| Products | TA Landscapes generated (this month) | File count in 05_Product_TA_Landscape/ |
| Scholar | KOLs with Scholar metrics vs awaiting review | kol_scholar_metrics vs scholar_review_queue |

AC:<two additions: (1) "KOL Pipeline Funnel" — show discovered → disambiguated → verified → briefed as an actual funnel chart. If 5,000 discovered but only 200 verified, the disambiguator is a bottleneck. Every verified KOL is a potential brief. (2) "Product Velocity" — briefs generated per week. If velocity is 0, we're not selling.>

---

### LAYER 3: CLINICAL QUANT PANEL (Market Intelligence Engine)

| Section | Widget | Data Source |
|---------|--------|------------|
| Phase 1 | SEC 8K / FDA PDUFA / PR Wire events (today/week) | cq_regulatory_catalysts by source_type |
| Phase 1 | Unique tickers covered vs total in biotech_leads | ticker count ratio |
| Phase 2-4 | Greyed out with unlock milestones | "Unlock when Phase 1 hits 100 catalysts" |
| Newsletter | Subscribers (Clinical Quant + Clinical Simplified) | Substack API |

> [!CEO: we will need a permant agent to do get catalysts-> deep reseaerch->verify->draft->for CEO approval, I don think this process chould be automated by py scripts, 1 catalyst-1 Post, this could be one branch of the cq worlflow,an end the CQ-Free News letter]
> AC:<biggest gap: no "Catalyst-to-Newsletter Pipeline" visibility. Show: catalysts detected → interpretations written → posts published. If catalysts pile up but interpretations don't go out, the content engine is broken. Also add "Signal-to-Noise Ratio" — what % of SEC filings are actual biotech catalysts vs noise.>

AC:<for not-started phases, show greyed-out with gamification: "Unlock when Phase 1 reaches 100 catalysts" — you see progression.>

---

### LAYER 4: OPERATIONS (The Nuts & Bolts)

| Section | Widget | Data Source |
|---------|--------|------------|
| Cron Health | Last run time + success/fail per script | Script logs |
| Cron Health | Time since last successful crawl | Timestamps |
| DB Sync | SQLite vs PG record counts | Compare local vs Supabase |
| DB Sync | Ticker sync + migration status | Execution logs |
| Supabase | Connection health + table row counts | Health check endpoint |
| Alerts | Pipeline errors (last 24h) | Error logs |

AC:<SQLite vs PG is TEMPORARY. Mark it with a sunset: "Auto-hide after 30 days of PG-only operation." Don't clutter the dashboard with ghosts.>

AC:<add "Cost Monitor" — Supabase free tier is 500MB/50K row reads per month. Show current usage vs limits. If you hit the cap mid-month, the whole factory stops.>

AC:<for Alerts, build a "last 10 things that broke" widget with timestamps. Actionable, not overwhelming.>

---

### LAYER 5: THE BRIDGE (Meddash → CQ — The Spine)

AC:<(1) ANIMATED DATA FLOW DIAGRAM — Active engines pulse green, idle grey, broken flash red. Arrow thickness = data volume. Thin arrow = 5 leads, thick = 500. You SEE the factory moving.>

AC:<(2) "DATA INVENTORY" — each DB/table as a warehouse icon with count. "kols: 12,341 items" "biotech_leads: 847 (239 with tickers)" "cq_regulatory_catalysts: 1,205". If inventory is low, you can't fulfill orders.>

AC:<(3) "FACTORY OUTPUT" — end-of-line products. Meddash: KOL Briefs/week. CQ: Newsletter Posts/week. If output = 0, the factory runs but produces nothing. That's worse than broken.>

AC:<(4) Visual separation — Meddash zone gets blue header bar. CQ zone gets green. Same dashboard, different departments. Workers wear different uniforms, but it's one company.>

---

### ARCHITECTURE DECISIONS

AC:<build as modular Streamlit app with config-driven widget registry. Each widget = Python function in /widgets/ folder. New widget = new file, zero changes to app.py. When you spawn a permanent agent, it gets its own widget file. Scale without rewrite.>

> [!CEO: can we add this as a seprate clickabel tab to dashboard to lauch, or we could keep it open separate local host if the merging is goin gcomplicate which it might, unless it doesnt]
> AC:<Dr. Don's KOL Ingest Tool (streamlit → mesh criteria → g.scholar → push to DB) is a SEPARATE operational tool, not a dashboard widget. Keep it as a sidebar page "KOL Ingest Tool". Dashboard WATCHES, the tool DOES. Don't mix them.>

---

*Ideated by Alfred Chief (AC) — 2026-04-24*
*Original plan by Dr. Don — CEO Notes/2026-04-24.md*