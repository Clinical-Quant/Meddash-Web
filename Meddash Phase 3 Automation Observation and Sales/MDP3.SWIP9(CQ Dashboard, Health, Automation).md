# MDP3.SWIP9 — CQ Dashboard, Health Monitoring & Automation Hardening

**Created:** 2026-05-02 07:15 UTC
**Author:** Alfred Chief
**Status:** IN PROGRESS — PM2 + Healthchecks.io + Dashboard core implemented. Circuit Board (pure HTML/CSS flow diagram), Data Tables (manual sync), Operations (PM2/Healthchecks). Sections G.12-G.13 (test pipeline/watchdog), C.2-C.4 (n8n hardening), D (health reports) pending.
**Context:** SWIP8 built the full CQ automation pipeline (engine, selector, verifier, composer, approval gate, export) with n8n orchestration, Paperclip agents, and a live animated Streamlit dashboard. SWIP9 hardens the entire stack for production resilience: process management, dead man's switch monitoring, automated health reporting, and a complete dashboard rebuild using deterministic instrumentation instead of heuristic guesswork.

---

## 0. Executive Goal

Turn the fragile, manually-started CQ stack into a self-healing production system that survives reboots, crashes, and silent failures without Dr. Don intervention. Rebuild the dashboard from scratch as a live diagnostic tool — not a static report — with real-time pipeline visibility, manually-synced Supabase data tables, and Plotly analytics.

**The problem today:**
- n8n, Ops API, and Streamlit dashboard are started via Hermes terminal backgrounds
- If the Hermes session dies → everything dies
- If WSL/Windows reboots → manual restart required
- If n8n or a script crashes silently → stays dead until someone notices
- No external monitoring — Dr. Don must open the dashboard to know if the pipeline is alive
- Dashboard is bloated, disorganized, and uses heuristic color logic (guessing from timestamps) instead of deterministic instrumentation
- Frequent Supabase queries burn API quota and CPU — data tables refresh unnecessarily

**The fix:**
1. **PM2** for process resurrection and boot persistence
2. **Healthchecks.io** for dead man's switch monitoring (external ping alerts)
3. **Automated Telegram health reports** on a cron schedule
4. **Dashboard complete rebuild** — stripped down to essentials, deterministic status registry, fragmented execution for targeted refresh, manual data sync

---

## 1. Current Foundation (What SWIP8 Left Us)

| Component | Status | Location / Details |
|---|---|---|
| CQ engine extraction | Built | `cq_engine.py` → `cq_catalysts`, `cq_insider_trades` |
| Candidate selector | Built | `cq_candidate_selector.py` → `cq_selected_candidates` |
| Independent verifier | Built | `cq_independent_verifier.py` → `cq_research_confirmations` |
| Content composer | Built | `cq_content_composer.py` → `cq_content_queue` |
| Approval updater | Built | `cq_approval_updater.py` |
| Publish exporter | Built | `cq_publish_exporter.py` |
| Artifact cleanup | Built | `cq_artifact_cleanup.py` |
| Ops API endpoints | Built | 7 `/cq/automation/*` endpoints on port 8765 |
| n8n workflow | Active | `CQ-Free Newsletter 1100` — 14 nodes, schedule trigger + Healthchecks ping |
| Paperclip agents | Running | CQ-Selector (d16ca8cb), CQ-Researcher (a2984628), CQ-Monitor (476a090d) |
| Streamlit dashboard | Running | Port 5090 — animated pipeline flow, live Supabase status |
| Supabase schema | Built | 4 SWIP8 tables + `cq_automation_status` view |
| Telegram alerts | Wired | CQ-Alerts bot (8672876638) → chat 6253013213 |

**Vulnerability (BEFORE SWIP9):** Every process above is running because Alfred started it. None will survive a crash or reboot. Dashboard uses heuristic timestamp-based color logic that can show "running" when the pipeline is actually hung.

**Vulnerability (AFTER SWIP9 A.1-A.4, B.1-B.4, C.1, E.1-E.2):** All processes managed by PM2 with systemd boot persistence. Healthchecks.io ping wired into n8n workflow. PM2 log rotation active. Crash recovery active. Dashboard rebuild pending (Section G).

---

## 2. Target Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    PM2 (Process Manager)                  │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────┐      │
│  │   n8n    │  │ Ops API  │  │ Streamlit Dashboard│      │
│  │  :5678   │  │  :8765   │  │       :5090        │      │
│  └────┬─────┘  └────┬─────┘  └────────┬──────────┘      │
│       │              │                │                   │
│       │        auto-restart on crash  │                   │
│       │        boot persistence       │                   │
└───────┼──────────────┼────────────────┼───────────────────┘
        │              │                │
        ▼              ▼                ▼
   ┌──────────────────────────────────────────────┐
   │              Supabase (data layer)            │
   │  cq_run_logs │ cq_selected_candidates │ ...   │
   │  (Dashboard reads via st_supabase_connection) │
   └────────────────────┬─────────────────────────┘
                        │
                        ▼
   ┌──────────────────────────────────────────────┐
   │          Healthchecks.io (monitoring)         │
   │                                               │
   │  Cron pings: "I'm alive" signal every N min   │
   │  If ping missed → alert via Telegram/Email    │
   └──────────────────────────────────────────────┘
                        │
                        ▼
   ┌──────────────────────────────────────────────┐
   │     Local SQLite: pipeline_registry           │
   │  (Fast <1ms reads for circuit board status)   │
   │  component_id | status | last_updated         │
   └──────────────────────────────────────────────┘
```

**Key principle:** PM2 keeps processes alive. Healthchecks.io verifies they're producing correct output. The local SQLite `pipeline_registry` provides deterministic, sub-millisecond status for the dashboard circuit board. Together they cover "is it running?", "is it working?", and "what exactly is happening right now?"

---

## 3. Implementation Plan

### Section A — PM2 Installation & Configuration

**A.1** Install PM2 globally:
```bash
npm install -g pm2
```

**A.2** Create PM2 ecosystem file (`ecosystem.config.js`) defining all CQ services with:
- Process names, working directories, interpreter paths
- Auto-restart on crash (max 5 restarts in 60s window)
- Log file paths under `~/.pm2/logs/`
- Memory limits (optional: restart if > 500MB)

**A.3** Start all services via PM2:
```bash
pm2 start ecosystem.config.js
```

**A.4** Configure boot persistence:
```bash
pm2 startup      # generates systemd service for WSL
pm2 save         # freezes current process list
```

**A.5** Verify processes survive WSL restart:
```bash
wsl --terminate <distro>   # simulate crash
wsl                         # restart
pm2 status                  # all should be "online"
```

### Section B — Healthchecks.io Integration

**B.1** Register free account at healthchecks.io (20 checks free tier).

**B.2** Create monitoring checks:
- **CQ Engine heartbeat** — pinged by cron every 60 min (market schedule) / 720 min (off-market fallback)
- **n8n workflow execution** — pinged by n8n's last HTTP Request node on successful completion
- **Dashboard uptime** — pinged by local cron checking `curl http://localhost:5090`
- **Supabase connectivity** — pinged by cron verifying `cq_run_logs` has recent rows

**B.3** Configure alert channels:
- **Primary:** Telegram (Healthchecks.io native Telegram integration)
- **Fallback:** Email (free tier includes email alerts)

**B.4** Write ping scripts:
- `~/.hermes/scripts/healthcheck_ping.py` — reusable script that accepts check UUID + optional status message
- Called by n8n HTTP Request node, local cron, and standalone tests

**B.5** Configure grace periods:
- Market hours: 2-hour grace (if ping missed for 2h → alert)
- Off-market/weekends: 24-hour grace (pipeline runs less frequently)

### Section C — n8n Workflow Hardening

**C.1** Add Healthchecks.io ping as the FINAL node in the `CQ-Free Newsletter 1100` workflow:
```
... → Export → Ping Healthchecks (success) → END
```

**C.2** Add error-path ping: if any node fails, ping Healthchecks with `/fail` signal:
```
Run CQ Detect → on error → Ping Healthchecks (fail) → Telegram alert
```

**C.3** Add retry logic to HTTP Request nodes (currently no retries — one network blip kills the run).

**C.4** Add workflow timeout: if entire workflow exceeds 30 min, fail gracefully with alert.

### Section D — Automated Health Reports

**D.1** Create `~/.hermes/scripts/cq_health_report.py` that:
- Queries Supabase for: last run time, selected/verified/content counts, error count
- Pings Healthchecks.io
- Sends summarized Telegram message if anomalies detected

**D.2** Register as cron job (every 6 hours):
```bash
# Via Hermes cronjob tool or system crontab
0 */6 * * * python3 ~/.hermes/scripts/cq_health_report.py
```

**D.3** Include in report:
- CQ Engine last run time + staleness warning
- Pipeline stage counts (selected/verified/composed/approved/exported)
- Error count in last 24h
- PM2 process status (all online?)
- Dashboard reachability

### Section E — PM2 Log Rotation

**E.1** Install pm2-logrotate:
```bash
pm2 install pm2-logrotate
```

**E.2** Configure retention:
- Max log size: 10MB per file
- Retain: 30 days
- Compress: true (gzip archives)

### Section F — Verification

**F.1** Crash test: kill each process, verify PM2 restarts within 2 seconds.
**F.2** Reboot test: restart WSL, verify all services come back.
**F.3** Healthchecks test: stop a service, wait past grace period, verify Telegram alert fires.
**F.4** End-to-end: trigger full CQ pipeline via n8n manual run, verify all Healthchecks pings arrive.
**F.5** Dashboard verification: confirm dashboard reflects pipeline state correctly after hardened run.

### Section G — Dashboard Complete Rebuild (NEW)

The current dashboard (`cq_panel.py` in `Meddash-CQ_Dashboard/widgets/`) is being completely stripped down and rebuilt using a deterministic instrumentation approach. The existing CSS-heavy animated pipeline flow with heuristic timestamp-based color logic is replaced with a professional, data-driven architecture.

#### G.1 Design Principles

1. **Deterministic over Heuristic:** Pipeline state comes from script-reported statuses in a local SQLite registry table, NOT inferred from Supabase timestamps.
2. **Fragmented Execution:** The heavy Supabase data tables load ONCE and stay static. The circuit board refreshes independently on a 10-30 second interval using `@st.fragment`.
3. **Manual Data Sync:** A "Force Synchronize" button clears the Supabase cache on demand. Dr. Don syncs once per weekday, avoiding unnecessary API quota burn on 15,000-row tables.
4. **Circuit Board Visualization:** A pure HTML/CSS flow diagram — no Mermaid, no iframe, no CDN. Six labeled pipeline rows with nodes driven by the SQLite registry. CSS animations: yellow blink for running, green for success, red pulse for failed, orange for hung. Moving dashed arrows between nodes change color with status. Rendered via `st.markdown(unsafe_allow_html=True)` — instant DOM update on fragment refresh, zero flicker.
5. **Watchdog for Hung Processes:** If a component reports `running` but `last_updated` exceeds 30 minutes, the dashboard overrides the color to blinking orange/red — silent crash detection without log diving.
6. **Plotly on Demand:** Charts and graphs load only after manual sync, reading from the freshly cached Supabase tables.

#### G.2 Architecture

```
Streamlit Dashboard (port 5090)
│
├── Tab 1: 🏭 Circuit Board (fragment — refreshes every 10-30s)
│   ├── Reads local SQLite: pipeline_registry (<1ms query)
│   ├── Dynamically generates Mermaid diagram with live color mapping
│   └── Watchdog column shows hung-process alerts
│
├── Tab 2: 📊 Data Tables (manual sync only)
│   ├── Supabase tables via st_supabase_connection (cached 1h)
│   ├── st.data_editor for interactive editing
│   ├── "Force Synchronize" button to clear cache
│   └── Plotly charts load after sync
│
└── Tab 3: 🔧 Operations (health dashboard)
    ├── PM2 process status
    ├── Healthchecks.io last ping status
    └── Pipeline error log
```

#### G.3 The Status Registry (Local SQLite)

A dedicated lightweight SQLite table acts as the switchboard for the circuit board visualization. Every pipeline script must report its state here.

**Database:** `cq_pipeline_registry.db`
**Location:** `Meddash_organized_backend/06_Shared_Datastores/cq_pipeline_registry.db`
**Table:** `pipeline_registry`

| Column | Type | Description |
|--------|------|-------------|
| `component_id` | TEXT PRIMARY KEY | Unique identifier for each pipeline step |
| `status` | TEXT | `idle`, `running`, `success`, `failed` |
| `last_updated` | TIMESTAMP | ISO 8601 — when the status was last written |
| `run_id` | TEXT | Optional — links to `cq_run_logs.run_id` |
| `error_message` | TEXT | Optional — last error if status is `failed` |

**Component IDs (matching the CQ architecture flow):**
```
n8n_schedule          → n8n Schedule Trigger
ops_api_detect        → Ops API POST /cq/detect
cq_runner             → cq_pipeline_runner.py
cq_engine             → cq_engine.py
sec_feed_fetch        → SEC Atom Feed Fetch
biotech_filter        → CIK Watchlist Filter
path_a_dedup          → Path A 8-K Dedup
path_a_fetch          → Path A 8-K Fetch
path_a_llm_extract    → Path A LLM Extract (nemotron-3-super)
path_a_validate       → Path A Validate
path_a_write          → Path A cq_catalysts INSERT
path_b_dedup          → Path B Form 4 Dedup
path_b_parse          → Path B Parse XML
path_b_filter         → Path B Filter P
path_b_write          → Path B cq_insider_trades INSERT
cq_selector           → Candidate Selector
cq_verifier           → Independent Verifier
cq_composer           → Content Composer
cq_approval           → Dr. Don Approval Gate
cq_export             → Publish Export
healthcheck_ping      → Healthchecks.io Ping
```

#### G.4 Script-Side Instrumentation

Every Python pipeline script must wrap its execution with status updates. The pattern:

```python
import sqlite3
from datetime import datetime, timezone

REGISTRY_DB = "/path/to/cq_pipeline_registry.db"

def update_status(component_id: str, status: str, run_id: str = "", error: str = ""):
    """UPSERT into pipeline_registry without locking."""
    conn = sqlite3.connect(REGISTRY_DB)
    conn.execute("""
        INSERT INTO pipeline_registry (component_id, status, last_updated, run_id, error_message)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(component_id) DO UPDATE SET
            status=excluded.status,
            last_updated=excluded.last_updated,
            run_id=excluded.run_id,
            error_message=excluded.error_message
    """, (component_id, status, datetime.now(timezone.utc).isoformat(), run_id, error))
    conn.commit()
    conn.close()

# Usage at top of script:
update_status("cq_engine", "running", run_id)

try:
    # ... actual pipeline work ...
    update_status("cq_engine", "success", run_id)
except Exception as e:
    update_status("cq_engine", "failed", run_id, str(e))
    raise
```

**Rule:** Every script that appears as a node in the CQ architecture flow MUST call `update_status()` on start, success, and failure.

#### G.5 The Logic-to-Color Mapper

In the Streamlit dashboard, a hard-coded dictionary maps registry statuses to Mermaid hex colors:

| Status | Mermaid Hex | CSS Effect | Visual Meaning |
|--------|------------|------------|----------------|
| `idle` | `#95a5a6` (Grey) | Static | Component waiting for next trigger |
| `running` | `#3498db` (Blue) | Pulsing animation | Script currently executing |
| `success` | `#2ecc71` (Green) | Static | Completed successfully |
| `failed` | `#e74c3c` (Red) | Pulsing animation | Crashed or threw error |
| `hung` (watchdog) | `#f39c12` (Orange) | Fast blink | Status is 'running' but last_updated > 30min ago |

**Watchdog logic:**
```python
def get_effective_status(comp):
    """Override status if component appears hung."""
    if comp['status'] == 'running':
        last = datetime.fromisoformat(comp['last_updated'])
        if (datetime.now(timezone.utc) - last).total_seconds() > 1800:
            return 'hung'  # overrides display to blinking orange
    return comp['status']
```

#### G.6 Dynamic Mermaid Generation

Instead of a static diagram string, the dashboard function assembles Mermaid code by reading the live registry and injecting colors:

```python
def generate_circuit_mermaid(registry: dict) -> str:
    """Build Mermaid 'graph LR' diagram with live status colors."""
    diagram = "graph LR\n"
    
    # Define node styling
    for comp_id, data in registry.items():
        label = comp_id.replace('_', ' ').upper()
        status = get_effective_status(data)
        color = STATUS_COLORS.get(status, '#95a5a6')
        diagram += f"    {comp_id}['{label}']\n"
        diagram += f"    style {comp_id} fill:{color},stroke:#333,stroke-width:2px\n"
    
    # Static connections (match cq-verification-flow.md architecture)
    diagram += """
    n8n_schedule --> ops_api_detect
    ops_api_detect --> cq_runner
    cq_runner --> cq_engine
    cq_engine --> sec_feed_fetch
    sec_feed_fetch --> biotech_filter
    biotech_filter --> path_a_dedup
    biotech_filter --> path_b_dedup
    path_a_dedup --> path_a_fetch --> path_a_llm_extract --> path_a_validate --> path_a_write
    path_b_dedup --> path_b_parse --> path_b_filter --> path_b_write
    path_a_write --> cq_selector
    path_b_write --> cq_selector
    cq_selector --> cq_verifier
    cq_verifier --> cq_composer
    cq_composer --> cq_approval
    cq_approval --> cq_export
    cq_export --> healthcheck_ping
    """
    
    return diagram
```

The Mermaid diagram is rendered inside a `@st.fragment(run_every="10s")` block, giving near-real-time visual feedback as the blue "running" light moves through the pipeline nodes.

#### G.7 Supabase Data Tables (Manual Sync)

Supabase tables are displayed via `st_supabase_connection` with interactive editing support:

```python
from st_supabase_connection import SupabaseConnection
import streamlit as st
import pandas as pd

conn = st.connection("supabase", type=SupabaseConnection)

@st.cache_data(ttl=3600)
def load_supabase_table(table_name: str) -> pd.DataFrame:
    """Cached for 1 hour — cleared by manual sync button."""
    query = conn.table(table_name).select("*").execute()
    return pd.DataFrame(query.data)

# Manual sync button
if st.button("🔄 Force Synchronize — Pull Latest from Supabase"):
    st.cache_data.clear()
    st.rerun()

# Display interactive table
df = load_supabase_table("cq_selected_candidates")
st.data_editor(df, use_container_width=True, num_rows="dynamic")
```

**Tables displayed:**
- `cq_catalysts` — raw 8-K catalyst extractions
- `cq_insider_trades` — raw Form 4 insider trades
- `cq_selected_candidates` — pipeline-selected candidates
- `cq_research_confirmations` — verification results
- `cq_content_queue` — newsletter/tweet/approval state
- `cq_source_artifacts` — SEC artifact index

#### G.8 Plotly Charts & Graphs (Loaded After Sync)

Plotly visualizations load only after manual data sync, reading from cached Supabase tables:

**Planned charts:**
- Catalyst volume by event type (bar chart — SEC_8K, FDA_PDUFA, PR_WIRE)
- Verification funnel (funnel chart — selected → confirmed → drafted → approved)
- Insider purchase heatmap by ticker/week
- Ticker activity timeline (line chart — catalysts per day)
- Signal-to-noise ratio gauge

**Implementation:** Charts are regular Streamlit elements that call `load_supabase_table()` under the hood. They render empty/loading state until the user clicks "Force Synchronize" and the cache populates.

#### G.9 File Structure (New Dashboard)

```
Meddash-CQ_Dashboard/
├── app.py                    # Main router — stripped to 3 tabs
├── config.py                 # DB paths, env vars, Supabase creds
├── supabase_connection.py    # st_supabase_connection wrapper
├── pipeline_registry.py      # SQLite registry read/write helpers
├── mermaid_generator.py      # Dynamic Mermaid diagram builder
├── pages/
│   ├── 01_circuit_board.py   # Tab 1: Live pipeline flow (fragment)
│   ├── 02_data_tables.py     # Tab 2: Supabase tables (manual sync)
│   └── 03_operations.py      # Tab 3: Health dashboard
├── charts/
│   ├── catalyst_bars.py      # Plotly bar charts
│   ├── verification_funnel.py # Plotly funnel
│   └── ticker_activity.py    # Plotly line/timeline
└── styles.css                # Minimal dark theme
```

#### G.10 Deployment Checklist

- [x] **G.1:** Create `cq_pipeline_registry.db` with `pipeline_registry` table in `06_Shared_Datastores/`
  - Created at `Meddash_organized_backend/06_Shared_Datastores/cq_pipeline_registry.db`. 21 components, SQLite table with UPSERT support.
- [ ] **G.2:** Add instrumentation (`update_status()` calls) to all 10 CQ automation scripts
  - NOT YET DONE. Pattern documented in G.4. Each script needs UPSERT calls on start/running, success, and failure.
- [x] **G.3:** Install `st-supabase-connection` in dashboard venv
  - Installed v2.1.3 + plotly.
- [x] **G.4:** Rewrite `app.py` — strip to 3 tabs (Circuit Board, Data Tables, Operations)
  - Rewritten. `@st.fragment(run_every=15s)` on Circuit Board tab.
- [x] **G.5:** Build `pipeline_registry.py` — SQLite read/write helpers with watchdog logic
  - Built. Registry reads, watchdog (running >30min → hung override), status counts, component tables. Original Mermaid generator function retained but no longer used — circuit board now generates HTML/CSS directly.
- [x] **G.6:** Build `pages/01_circuit_board.py` — pure HTML/CSS flow diagram (fragment)
  - **Evolved through 3 versions:** v1 (Mermaid markdown — rendered as raw text), v2 (Mermaid CDN in iframe — flicker + 200KB fetch per cycle), **v3 (current — pure HTML/CSS).** Six labeled pipeline rows: TRIGGER → DATA INGESTION → PATH A (8-K) → PATH B (Form 4) → VERIFICATION → APPROVAL & EXPORT. Each node is a styled div with CSS class from registry status. Yellow blinking = running, green = success, red pulsing = failed, orange = hung. Moving dashed arrows between nodes. Vertical connectors between rows. Status pills + watchdog alerts rendered inline. Zero dependencies, zero iframe, zero flicker — fragment replaces markdown block every 15s.
- [x] **G.7:** Build `pages/02_data_tables.py` — `st_supabase_connection`, cache, manual sync, `st.data_editor`
  - Built. 6 tables in sub-tabs, "Force Synchronize" button, Plotly charts load after sync.
- [x] **G.8:** Build `pages/03_operations.py` — PM2 status, Healthchecks, error log
  - Built. PM2 subprocess, Healthchecks config, pipeline error table, system info.
- [x] **G.9:** Build Plotly charts — load only after sync
  - Built inline in 02_data_tables.py. Status pie chart + candidates timeline. More deferred.
- [x] **G.10:** Delete old widgets — clean slate
  - All 9 old widget files deleted. New structure: app.py, pipeline_registry.py, pages/ (3).
- [x] **G.11:** Restart dashboard via PM2, verify all 3 tabs render
  - PM2 restarted. Dashboard UP (HTTP 200). All 3 tabs verified via browser navigation.
- [ ] **G.12:** Run a test pipeline cycle — verify circuit board lights up through all nodes
  - NOT YET DONE. Requires script instrumentation (G.2).
- [ ] **G.13:** Test watchdog — set component running with old timestamp, verify orange alert
  - NOT YET DONE.

---

## 4. Non-Negotiable Rules

1. **PM2 manages all CQ processes** — no more Hermes terminal backgrounds for production services.
2. **Healthchecks.io is the single source of truth for "is the pipeline alive?"** — not the dashboard, not Telegram.
3. **Every pipeline completion pings Healthchecks** — silence = failure.
4. **Grace periods must reflect actual schedule** — don't alert because the pipeline is sleeping on a Sunday.
5. **PM2 logs are the debug source** — `pm2 logs` replaces hunting through 4 different log files.
6. **Secrets never enter PM2 ecosystem file** — use environment variables.
7. **Script instrumentation is mandatory** — every pipeline script reports status to the registry on start, success, and failure. No script = no dashboard visibility.
8. **Supabase data sync is manual** — no automatic refresh on page load. Dr. Don syncs once per weekday via the "Force Synchronize" button.
9. **Watchdog must catch hung processes** — if a component shows `running` for >30 minutes, the dashboard overrides to blinking orange. No silent failures.
10. **Dashboard is a diagnostic tool, not just a dashboard** — you should be able to watch the blue light move from node to node and know when a paying client's data is delayed.

---

## 5. Deferred / Not in This SWIP

- Full CI/CD pipeline (GitHub Actions → deploy)
- Docker containerization
- Multi-instance load balancing
- Paid Healthchecks.io tier (20 checks is enough for now)
- Grafana/Prometheus metrics dashboard
- PagerDuty on-call rotation
- Historical analytics dashboard (past catalyst trends beyond Plotly charts)

---

## 6. Dependencies

| Dependency | Required? | Status |
|---|---|---|
| PM2 (npm global) | Yes | Installed (v0.40.4) |
| Healthchecks.io account | Yes | Registered — master check UUID: 93e4e6b2; Telegram integration configured |
| Telegram bot (CQ-Alerts) | Yes | Already configured |
| Supabase | Yes | Already configured |
| WSL with systemd | Recommended | systemd service registered |
| st-supabase-connection | Yes (G.3) | To be installed in dashboard venv |
| pm2-logrotate | Yes (E) | Installed & configured |
| Python sqlite3 (stdlib) | Yes (G) | Already available |

---

## 7. Implementation Checklist

### Section A — PM2 Installation

- [x] **A.1:** Install PM2 globally (`npm install -g pm2`)
  - Installed v0.40.4 via npm. All services running: cq-n8n (pid 46619), cq-ops-api (pid 46620), cq-dashboard (pid 46627).
- [x] **A.2:** Create `ecosystem.config.js` defining n8n, Ops API, Streamlit dashboard
  - Created at `/home/doc_victus/ecosystem.config.js`. Three apps: cq-n8n (n8n start), cq-ops-api (Python3 Ops API), cq-dashboard (Streamlit on port 5090). All with max_restarts=5, restart_delay=3000ms. Secrets kept in environment variables, not in the file.
- [x] **A.3:** Start all services via `pm2 start ecosystem.config.js`
  - Launched successfully. All three online after initial port conflicts resolved (stale Hermes-owned processes on 8765/5090 killed first).
- [x] **A.4:** Run `pm2 startup` + `pm2 save` for boot persistence
  - systemd service registered at `/etc/systemd/system/pm2-doc_victus.service`. Windows PATH with spaces broke first attempt — worked around with clean PATH. `pm2 save` executed — process list frozen at `/home/doc_victus/.pm2/dump.pm2`.
- [ ] **A.5:** Verify WSL restart survival
  - NOT YET TESTED. Requires terminating WSL distro and verifying all three come back online. Deferred to Section F.

### Section B — Healthchecks.io

- [x] **B.1:** Register healthchecks.io account
  - Free tier account registered by Dr. Don. 20 checks allowed, 20 alerts/day.
- [x] **B.2:** Create checks: CQ Engine, n8n workflow, Dashboard, Supabase
  - Master check UUID: `93e4e6b2-a224-4355-84ff-1fce82fb39bd`
  - Ping URL: `https://hc-ping.com/93e4e6b2-a224-4355-84ff-1fce82fb39bd`
  - Free tier limit: 20 alerts/day
  - Currently using single master check for the CQ pipeline. Individual checks for Dashboard uptime and Supabase connectivity can be created later as separate UUIDs when needed.
- [x] **B.3:** Configure Telegram alert channel
  - Done. Dr. Don linked the CQ-Alerts bot to Healthchecks.io via the Integrations page. Telegram alerts fire when the master check goes down.
- [x] **B.4:** Write `healthcheck_ping.py` script
  - Created at `~/.hermes/scripts/healthcheck_ping.py`. Supports `success` and `fail` status, optional message param. Tested — returns "OK" from Healthchecks.io API.
- [ ] **B.5:** Configure grace periods (2h market / 24h off-market)
  - NOT YET DONE. Default Healthchecks.io grace period applies. Custom schedules for market vs off-market windows need to be set in the Healthchecks.io UI.

### Section C — n8n Hardening

- [x] **C.1:** Add Healthchecks success ping as final workflow node
  - n8n workflow `CQ-Free Newsletter 1100` updated from 13 to 14 nodes. Final node `Ping Healthchecks.io` sends HTTP POST to `https://hc-ping.com/93e4e6b2-a224-4355-84ff-1fce82fb39bd` after `Send Latest CQ Report Telegram via Ops API` completes successfully.
- [x] **C.2:** Add Healthchecks fail ping on error paths
  - Added `Ping Healthchecks.io (FAIL)` node (15th node). All 10 critical HTTP Request nodes now have error output connections → fail ping. Any node failure triggers `POST https://hc-ping.com/93e4e6b2-a224-4355-84ff-1fce82fb39bd/fail` → immediate Telegram alert via Healthchecks.io.
- [x] **C.3:** Add retry logic to HTTP Request nodes
  - All 14 HTTP Request nodes configured with retry: max 3 attempts, 5-second wait between retries. Network blips no longer kill the run.
- [x] **C.4:** Add workflow timeout (30 min)
  - Workflow-level timeout set: 1800 seconds. If the entire pipeline exceeds 30 minutes, n8n force-stops it. Prevents indefinite hangs on slow SEC EDGAR responses.

### Section D — Health Reports

- [x] **D.1:** Create `cq_health_report.py`
  - Built at `~/.hermes/scripts/cq_health_report.py`. Queries 6 Supabase tables for pipeline counts (selected/verified/content/raw data/artifacts), reads pipeline_registry.db for component status + watchdog detection, checks PM2 liveness (`pm2 status` subprocess), verifies dashboard reachability (HTTP 200 on port 5090). Always pings Healthchecks.io (proves reporter itself is alive). Sends Telegram alert via CQ-Alerts bot ONLY when anomalies detected. Handles timezone-aware datetime parsing, graceful Supabase failure (-1 sentinel), hung process detection (>30min running override). Run manually: `python3 ~/.hermes/scripts/cq_health_report.py`. First test run detected 17h-stale pipeline and sent Telegram alert successfully.
- [x] **D.2:** Register as 6-hourly cron job
  - Registered via Hermes `cronjob` tool. Job ID: `d95e310a3ea9`, name: "CQ Health Report (6-hourly)", schedule: `0 */6 * * *` (runs at 00:00, 06:00, 12:00, 18:00 UTC daily). Next run: 2026-05-03 00:00 EDT. Script: `cq_health_report.py` (pre-run data collection). Delivery: local (results logged to cron history).
- [x] **D.3:** Include all pipeline stage counts + PM2 status
  - Report format includes: Supabase section (selected/verified/content/raw catalysts+trades/artifacts counts + last run timestamp + staleness check), Registry section (running/success/failed/hung/idle counts + hung component list), PM2 status (ONLINE/OFFLINE), Dashboard (UP/DOWN with HTTP code), Anomalies section (only when issues found). Telegram alert fires only on anomalies — silence = everything healthy.

### Section E — Log Rotation

- [x] **E.1:** Install pm2-logrotate
  - Installed v3.0.0 via `pm2 install pm2-logrotate`. Running as PM2 module (pid 46950).
- [x] **E.2:** Configure: 10MB max, 30-day retention, compress
  - Set: max_size=10M, retain=30 days, compress=true. Rotates daily at midnight.

### Section F — Verification

- [ ] **F.1:** Crash test — kill each process
  - NOT YET DONE.
- [ ] **F.2:** Reboot test — restart WSL
  - NOT YET DONE.
- [ ] **F.3:** Healthchecks alert test — stop service past grace period
  - NOT YET DONE.
- [ ] **F.4:** End-to-end pipeline run with Healthchecks pings
  - NOT YET DONE.
- [ ] **F.5:** Dashboard reflects hardened pipeline state (post-rebuild)
  - NOT YET DONE.

### Section G — Dashboard Complete Rebuild

- [ ] **G.1:** Create `cq_pipeline_registry.db` with `pipeline_registry` table in `06_Shared_Datastores/`
- [x] **G.1:** Create `cq_pipeline_registry.db` with `pipeline_registry` table in `06_Shared_Datastores/`
  - Created at `Meddash_organized_backend/06_Shared_Datastores/cq_pipeline_registry.db`. 21 components, SQLite table with UPSERT support.
- [ ] **G.2:** Add instrumentation (`update_status()` calls) to all 10 CQ automation scripts
  - NOT YET DONE. Pattern documented in G.4. Each script needs UPSERT calls on start/running, success, and failure.
- [x] **G.3:** Install `st-supabase-connection` in dashboard venv
  - Installed v2.1.3 + plotly.
- [x] **G.4:** Rewrite `app.py` — strip to 3 tabs (Circuit Board, Data Tables, Operations)
  - Rewritten. `@st.fragment(run_every=15s)` on Circuit Board tab.
- [x] **G.5:** Build `pipeline_registry.py` — SQLite read/write helpers with watchdog logic
  - Built. Registry reads, watchdog (running >30min → hung override), status counts, component tables. Original Mermaid generator function retained but no longer used — circuit board now generates HTML/CSS directly.
- [x] **G.6:** Build `pages/01_circuit_board.py` — pure HTML/CSS flow diagram (fragment)
  - **Evolved through 3 versions:** v1 (Mermaid markdown — rendered as raw text), v2 (Mermaid CDN in iframe — flicker + 200KB fetch per cycle), **v3 (current — pure HTML/CSS).** Six labeled pipeline rows: TRIGGER → DATA INGESTION → PATH A (8-K) → PATH B (Form 4) → VERIFICATION → APPROVAL & EXPORT. Each node is a styled div with CSS class from registry status. Yellow blinking = running, green = success, red pulsing = failed, orange = hung. Moving dashed arrows between nodes. Vertical connectors between rows. Status pills + watchdog alerts rendered inline. Zero dependencies, zero iframe, zero flicker — fragment replaces markdown block every 15s.
- [x] **G.7:** Build `pages/02_data_tables.py` — `st_supabase_connection`, cache, manual sync, `st.data_editor`
  - Built. 6 tables in sub-tabs, "Force Synchronize" button, Plotly charts load after sync.
- [x] **G.8:** Build `pages/03_operations.py` — PM2 status, Healthchecks, error log
  - Built. PM2 subprocess, Healthchecks config, pipeline error table, system info.
- [x] **G.9:** Build Plotly charts — load only after sync
  - Built inline in 02_data_tables.py. Status pie chart + candidates timeline. More deferred.
- [x] **G.10:** Delete old widgets — clean slate
  - All 9 old widget files deleted. New structure: app.py, pipeline_registry.py, pages/ (3).
- [x] **G.11:** Restart dashboard via PM2, verify all 3 tabs render
  - PM2 restarted. Dashboard UP (HTTP 200). All 3 tabs verified via browser navigation.
- [ ] **G.12:** Run a test pipeline cycle — verify circuit board lights up through all nodes
  - NOT YET DONE. Requires script instrumentation (G.2).
- [ ] **G.13:** Test watchdog — set component running with old timestamp, verify orange alert
  - NOT YET DONE.
