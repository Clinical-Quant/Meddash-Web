# Dashboard Building Plan — Final

**Date:** 2026-04-24  
**Built by:** Alfred Chief  
**Status:** BUILT — Ready for startup and testing

---

## What Was Built

A unified Streamlit dashboard for the MEDDASH-CQ factory — one dashboard, two departments (Meddash blue, CQ green), with animated data flow visualization as the centerpiece.

## Architecture

```
Meddash-CQ_Dashboard/
├── app.py                    # Main router — sidebar navigation to 6 tabs
├── config.py                 # All paths, env vars, SQL queries — single source of truth
├── supabase_client.py        # REST client for Supabase (read-only counts + selects)
├── styles.css                # Custom CSS: pulse animations, department colors, cards
├── .env                      # Combined credentials from Meddash + CQ .env files (DO NOT COMMIT)
├── venv/                     # Python 3.12 virtualenv with streamlit, plotly, supabase, pandas
└── widgets/
    ├── __init__.py
    ├── factory_floor.py       # LAYER 5: Animated data flow + data inventory + factory output
    ├── pulse.py               # LAYER 1: Engine heartbeat, delta metrics, staleness
    ├── meddash_panel.py       # LAYER 2: KOL funnel, CT engine, BioCrawler, product velocity
    ├── cq_panel.py            # LAYER 3: Catalyst pipeline, agent workflow, newsletter, phases 2-4 locked
    ├── operations.py          # LAYER 4: Supabase health, cost monitor, sync, last 10 breaks
    └── kol_ingest.py          # SEPARATE TAB: Dr. Don's KOL ingest tool (not a dashboard widget)
```

## 6 Sidebar Tabs

1. **🏭 Factory Floor** — The centerpiece. Animated engine status (pulse green/yellow/red/grey), data inventory, factory output metrics (briefs/week, CQ posts/week), Meddash→CQ bridge spine, CQ Permanent Agent pipeline (Detect→Research→Verify→Draft→Approve→Publish)
2. **💗 Pulse** — Engine heartbeat with staleness timestamps (green <6h, yellow <24h, red >24h). Core metrics with deltas. Revenue funnel with dollar sign (grey → green at first $2,450)
3. **🔬 Meddash** — KOL Pipeline Funnel (Discovered→Disambiguated→Verified→Briefed), CT Engine, BioCrawler tier breakdown, Product Velocity
4. **💊 Clinical Quant** — Catalyst-to-Newsletter pipeline (6-stage agent workflow), Phase 1 data by source, Phases 2-4 locked with gamification unlock thresholds, Permanent Agent section, Signal-to-Noise Ratio
5. **⚙️ Operations** — Supabase health + table counts, Cost Monitor (free tier limits), SQLite vs PG sync (auto-hide after 30 days), Cron health, Last 10 Things That Broke
6. **🔧 KOL Ingest** — Separate tab per CEO request. MeSH search → Scholar parse → Push to DB. Placeholder for VS Code tool integration

## CEO Comments Incorporated

### Layer 3 (CQ Panel):
- CEO: "Permanent agent to do: get catalysts → deep research → verify → draft → for CEO approval. 1 catalyst = 1 post. This is one branch of the CQ workflow, end of CQ-Free Newsletter."
- **AC Response:** Built as 6-stage pipeline visual on the CQ panel (Detect→Research→Verify→Draft→Approve→Publish). First 4 stages labeled AGENT/AUTO, last 2 labeled MANUAL. Permanent agent section explains deployment path (Hermes cron → agent per catalyst → draft queue → CEO approves → Substack publish). Blocked on Substack API key + publication URL.

### Architecture Decisions:
- CEO: "Can we add this as a separate clickable tab to dashboard to launch, or keep it open separate localhost if merging is going to complicate which it might, unless it doesn't."
- **AC Response:** Added as a **separate sidebar tab** "KOL Ingest" in the same dashboard on port 5090. Zero merge complexity — it's just another page in the sidebar. Dashboard watches, tool does. Same localhost, same process, no port conflicts. If it ever needs to be split out, it's a separate .py file that can be its own app in 5 minutes.

## Key Design Decisions

1. **Port 5090** per Dr. Don's preference (not 8501)
2. **One dashboard, two departments** — Meddash gets blue headers, CQ gets green headers
3. **Modular widgets** — Each tab is a separate Python file. Add a new widget = add a new file, no changes to app.py
4. **Factory Output is the #1 metric** — Briefs/week and CQ posts/week. If output = 0, the factory is running but producing nothing
5. **Staleness over health** — Green lights that haven't crawled in 6 hours are lying. Every engine shows last-modified timestamp and age
6. **Deltas over totals** — "+47 KOLs since yesterday" beats "12,341 total"
7. **Cost Monitor** — Supabase free tier limits shown. Hitting the cap stops the factory
8. **Phases 2-4 locked** with gamification — "Unlock when Phase 1 hits 100 catalysts"
9. **CQ Agent pipeline** — Not Python scripts. 1 catalyst = 1 post. Agent researches, CEO approves

## Startup Instructions

```bash
cd /mnt/c/Users/email/.gemini/antigravity/CTO/Meddash-CQ_Dashboard
source venv/bin/activate
streamlit run app.py --server.port 5090
```

Then open in browser: **http://localhost:5090**

## Data Sources

- **SQLite (local):** meddash_kols.db, ct_trials.db, biocrawler_leads.db — in Meddash_organized_backend/06_Shared_Datastores/
- **Supabase (cloud):** PostgREST API using service_role_key — reads kols, biotech_leads, ct_trials, cq_regulatory_catalysts, kol_scholar_metrics, kol_merge_candidates, kols_staging
- **File system:** KOL Briefs in 04_Product_KOL_Briefs/kol_briefs/, TA Landscapes in 05_Product_TA_Landscape/ta_reports/
- **env:** Combined from Meddash + CQ .env files, loaded by config.py with dotenv

## Refresh

Dashboard auto-refreshes every 2 minutes (config.REFRESH_SECONDS = 120). Each refresh costs ~10-15 Supabase API reads. Adjust if approaching free tier limits.

## Known Limitations (v1.0)

1. **No write operations** — Dashboard is read-only. KOL Ingest tool is placeholder (needs backend implementation)
2. **Scholar parsing** — Requires SERPAPI_KEY, not yet wired
3. **CQ Agent** — Not deployed. Needs Hermes cron job + Substack API key
4. **Cron health** — Shows known issues from QA. Full log monitoring needs log directory config
5. **Delta tracking** — Needs baseline snapshots stored somewhere for "since yesterday" comparisons. Currently shows current counts only
6. **Substack subscriber counts** — Need Substack API integration + publication URL
7. **MarketUX** — Registration email never received, blocks CQ Phase 2 data access
8. **Issue 6** — 4 SQL injection endpoints + corrupted line 17 in api_server.py still open with Meddash CTO

## Next Sprint Priorities

1. Start the dashboard and verify Supabase connectivity
2. Wire CQ Permanent Agent (Hermes cron → catalyst detection → research → draft → approval queue)
3. Get Substack API key and publication URL for subscriber metrics
4. Integrate VS Code KOL Ingest tool into the dashboard kol_ingest.py
5. Add delta tracking (store daily snapshots for trend comparison)
6. Deploy to a persistent process (systemd or nohup) so it stays running

---

*Built by Alfred Chief for Dr. Don — 2026-04-24*