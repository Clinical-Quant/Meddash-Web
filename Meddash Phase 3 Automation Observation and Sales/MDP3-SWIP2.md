# MDP3-SWIP2 — Step-Wise Implementation Plan: n8n/Paperclip Automation Wiring

> **Author:** Hermes Alfred Chief  
> **Date:** 2026-04-26 01:15 UTC  
> **Scope:** Wire SWIP1-refactored scripts into n8n workflows + Paperclip agent triarchy for autonomous Meddash data pipeline  
> **Goal:** Fully automated launch, monitoring, health upkeep, and status reporting for the Meddash pipeline  
> **Depends on:** MDP3-SWIP1 (COMPLETE — 48/48 checkboxes)  
> **Reference docs:** `MDP3-SWIP1.md`, `MDP3-Pre Implementation Plan.md`, wiki `reference/meddash-backend-map.md`

---

## Architecture Overview

### The Triarchy (Same Model as CQ)

| Layer | Instance | Role | Cost | When |
|-------|----------|------|------|------|
| 1 — Hands | n8n | Deterministic schedule/execute | $0/run | No thinking needed |
| 2 — Workers | Paperclip agents | LLM reasoning, role-bound | tokens/run | Judgment, generation, verification |
| 3 — Eye + Fixer | Alfred Chief | Omnipotent overseer | tokens/session | Something broke, cross-system fix |

### Meddash Workflow — Two Trigger Modes

```
TRIGGER 1: n8n Schedule (02:00 UTC daily)
TRIGGER 2: Telegram message to Meddash bot (on-demand)

n8n (02:00 cron OR Telegram trigger)
  → Node 1: Telegram — "🚀 Meddash Pipeline Triggered — {timestamp}"
  → Node 2: Code — Run Engine 01 (nightly_scheduler.py) + Engine 03 (biocrawler.py --mode daily)
  → Node 3: Code — Run Engine 02 (ct_crawler.py --mode delta) if it's a weekday
  → Node 4: Telegram — "✅ Engines 01+03 done — {counts} KOLs, {counts} leads"
  → Node 5: Wait 5 min (let DB writes settle)
  → Node 6: Code — Read pipeline summaries, build health report JSON
  → Node 7: HTTP POST — Create Paperclip issue for Meddash-CTO (health check + brief routing)
  → Node 8: Telegram — "📊 Meddash health report delivered to Meddash-CTO"

On-demand (Engine 04/05/09) — Manual trigger via Telegram bot:
  → Dr. Don sends "/brief [condition]" or "/landscape [disease]" to Meddash bot
  → n8n Telegram Trigger picks up message
  → Code node parses command
  → Runs appropriate script (04_KOL_Briefs or 05_TA_Landscape)
  → Telegram response with result summary
```

### Meddash Pipeline vs CQ Pipeline — Key Differences

| Aspect | CQ Pipeline | Meddash Pipeline |
|--------|-------------|------------------|
| Trigger frequency | Daily 11AM | Daily 2AM (Engines 01/03), on-demand (02/04/05/09) |
| Script complexity | 3 lightweight Python scripts | 3+ heavy engines with PubMed/CT.gov API calls |
| Run duration | ~30 seconds | 5–20 minutes per engine |
| LLM usage | Paperclip agents only | None in engine scripts (LLM calls are in disambiguator/bridge via Gemini) |
| Data output | Supabase rows | SQLite DB rows + summary JSON files |
| Agent roles | CQ-Selector → CQ-Researcher | Meddash-CTO (health + brief routing) |
| Error surface | Low (scripts rarely fail) | High (API timeouts, rate limits, LLM hallucinations) |

---

## SWIP2-A: n8n Workflow — Daily Cron Pipeline (Engines 01 + 03)

### A.1: Set up n8n workflow nodes

- [x] **A.1.1:** Update the existing "Meddash Work Flow" (QMwgjPEngkfq6vgD) — keep the two trigger nodes (Telegram Trigger + Schedule Trigger), add Code node to merge triggers into a single flow
  - *Done: Kept both existing triggers. Both feed into parallel branches: "Alert: Pipeline Triggered" (notification) + "Run Engine 01+03" (pipeline). Same pattern as CQ workflow where Schedule Trigger fans out to Telegram alert + Code node simultaneously.*
  - *The existing workflow already has a Telegram Trigger (Meddash bot credential `fgBFlRQbYkxSlH3P`) and a Schedule Trigger. Both should feed into the same pipeline. Use a Merge node or just connect both triggers to the first Code node.*

- [x] **A.1.2:** Add Code Node "Run Engine 01+03" — execute `nightly_scheduler.py` and `biocrawler.py --mode daily` via `execSync`
  - *Done: Code node runs nightly_scheduler.py --json-summary from 01_KOL_Data_Engine, then biocrawler.py --mode daily from 03_BioCrawler_GTM. Sets MEDDASH_ROOT and PYTHONPATH env vars so scripts find paths.py. Captures stdout/stderr. Reads kol_pipeline_summary.json and biocrawler_summary.json for kol_count, leads_count, rotation_category. Returns JSON: {engine01, engine03, kol_count, leads_count, rotation_category}. Timeout: 600s per engine.*
  - *Script: execSync runs python3 nightly_scheduler.py from 01_KOL_Data_Engine, then python3 biocrawler.py --mode daily from 03_BioCrawler_GTM. Captures stdout/stderr. Returns JSON with kol_count, leads_count, rotation_category, duration_seconds. Uses the same pattern as CQ workflow's Code node.*

- [x] **A.1.3:** Add Telegram Node "Alert: Pipeline Triggered" — send 🚀 message via Meddash bot (`channel="meddash"`)
  - *Done: Telegram node using credential "Telegram account Meddash" (fgBFlRQbYkxSlH3P), chatId 6253013213. Text: "🚀 Meddash Pipeline Triggered — {timestamp}". Both Schedule and Telegram triggers connect here in parallel.*
  - *Credentials: `Telegram account Meddash` (ID: `fgBFlRQbYkxSlH3P`). Text: `=🚀 Meddash Pipeline Triggered — {{ $now.format('yyyy-MM-dd HH:mm') }}`*

- [x] **A.1.4:** Add Telegram Node "Alert: Engines Complete" — send ✅ message with counts from Code node output
  - *Done: Telegram node with expression text: "✅ Meddash Engines Complete — KOLs: {kol_count}, Leads: {leads_count}, Rotation: {rotation_category}". Receives input from Run Engine 01+03 Code node.*
  - *Text: `=✅ Meddash Engines Complete — {{ $json.kol_count }} KOLs processed, {{ $json.leads_count }} leads updated, rotation: {{ $json.rotation_category }}`*

- [x] **A.1.5:** Add Wait Node "Wait 5 min" — give DB writes time to settle before health check
  - *Done: n8n-nodes-base.wait v1.1, resume=timeInterval, amount=5, unit=minutes. Receives input from "Alert: Engines Complete" and feeds into "Health Check".*
  - *Same pattern as CQ workflow's 10-minute wait. Meddash engines are faster; 5 minutes is sufficient for SQLite writes + summary JSON creation.*

- [x] **A.1.6:** Add Code Node "Health Check" — read all `_summary.json` files from `06_Shared_Datastores/pipeline_summaries/` and build a health report
  - *Done: Code node reads kol_pipeline_summary.json and biocrawler_summary.json from pipeline_summaries dir. Also reads mesh_rotation_state.json from pipeline_state. Builds unified health report: {overall_status, engines: [{name, status, duration, last_run, error, kol_count, leads_count}], rotation: {category, week, cycle}, timestamp}. Classifies: healthy (all success), degraded (partial/missing), failed (any failure).*
  - *Uses `pipeline_summary.py`'s `read_all_summaries()` pattern. Returns: engine statuses, durations, error messages, KOL/lead counts, rotation category. This JSON is passed to Meddash-CTO via Paperclip.*

### A.2: Wire connections for daily pipeline

- [x] **A.2.1:** Connection chain: Schedule Trigger → Telegram "Triggered" → Code "Run Engines" → Telegram "Complete" → Wait 5 min → Code "Health Check"
  - *Done: Chain wired as: Both triggers → Alert: Triggered (parallel) + Run Engine 01+03 (main) → Alert: Engines Complete → Wait 5 min → Health Check. Matches CQ workflow fan-out pattern.*
  - *The Telegram Trigger (on-demand) also connects to Telegram "Triggered" node — both triggers produce the same pipeline execution.*

- [x] **A.2.2:** Connection for Telegram Trigger: Telegram Trigger → Telegram "Triggered" (parallel with Schedule Trigger)
  - *Done: Telegram Trigger fans out to both "Alert: Pipeline Triggered" and "Run Engine 01+03" — same parallel pattern as Schedule Trigger. On-demand Telegram messages trigger the entire pipeline.*
  - *Both triggers fire the same pipeline. The Telegram bot message serves as on-demand trigger for ad-hoc runs.*

- [x] **A.2.3:** Verify Schedule Trigger time is set to 02:00 UTC (not AM local — n8n uses UTC)
  - *Done: Schedule Trigger parameters set to rule.interval[0].triggerAtHour=2. n8n uses UTC, so 02:00 UTC = 9PM EST / 10PM EDT. Off-peak for clinical data APIs.*
  - *n8n Schedule Trigger uses cron syntax or interval. Set `rule.interval[0].hour=2` for 02:00 UTC = ~9PM EST = off-peak for clinical data APIs.*

---

## SWIP2-B: n8n Workflow — Health Monitoring + Paperclip Integration

### B.1: Meddash-CTO Paperclip issue creation

- [ ] **B.1.1:** Add HTTP Request Node "Trigger Meddash-CTO via Paperclip" — POST to `http://127.0.0.1:3100/api/companies/cf39ae28-5bd5-44d1-b888-b01f83192fd5/issues`
  - *Body: `{"title": "Meddash Daily Health Check - {date}", "description": "Automated health check from n8n at 02:05 UTC. Verify: 1) Engine 01 (KOL) ran successfully, 2) Engine 03 (BioCrawler) ran successfully, 3) Summary JSONs exist, 4) No errors in pipeline_state. Health data: {JSON from health check}. Assign KOL brief requests from biocrawler leads.", "priority": "high", "assigneeAgentId": "9511e1ea-def0-4c0b-a78b-7d9f63cae6a2"}`*
  - *Meddash-CTO agent ID: `9511e1ea-def0-4c0b-a78b-7d9f63cae6a2`*

- [ ] **B.1.2:** Add Telegram Node "Alert: Health Report Sent" — send 📊 confirmation message
  - *Text: `=📊 Meddash health report delivered to Meddash-CTO. Pipeline status: {{ $json.overall_status || 'check Paperclip' }}`*

- [ ] **B.1.3:** Connection: Health Check Code → Paperclip POST → Telegram Alert
  - *Linear chain: Code "Health Check" → HTTP "Meddash-CTO Issue" → Telegram "Report Sent"*

### B.2: Error handling and retry

- [ ] **B.2.1:** Add Error Trigger Node — catches any node failure in the workflow
  - *n8n Error Trigger (`n8n-nodes-base.errorTrigger`) fires when ANY node in the workflow fails. Connect to a Telegram alert via Meddash bot: `=🚨 Meddash Pipeline ERROR — Node: {{ $json.execution.error.node }} Message: {{ $json.execution.error.message }}`*

- [ ] **B.2.2:** Add Telegram Node "Alert: Pipeline Error" — sends error details via Meddash bot
  - *Uses same credential as other Meddash Telegram nodes (`fgBFlRQbYkxSlH3P`). Severity levels from telegram_notifier.py map to emoji: 🚨 error.*

- [ ] **B.2.3:** Verify Code node captures stderr and non-zero exit codes
  - *The `execSync` calls must capture both stdout AND stderr. Check `error.status` for non-zero exit codes. If Engine 01 fails, log error but continue to Engine 03 (resilient pipeline — don't let one engine failure block others).*

---

## SWIP2-C: n8n Workflow — On-Demand Engine Triggers

### C.1: Telegram command parser for on-demand runs

- [ ] **C.1.1:** Add Code Node "Parse Command" after Telegram Trigger — parse incoming message for `/brief`, `/landscape`, `/ct`, `/status` commands
  - *Example commands: `/brief NSCLC` → runs Engine 04 generate_kol_brief.py, `/landscape "lung cancer"` → runs Engine 05, `/ct delta` → runs Engine 02 ct_crawler.py --mode delta, `/status` → reads pipeline_summaries and returns current state.*

- [ ] **C.1.2:** Add Switch/If Node "Route Command" — branch to different Code nodes based on parsed command
  - *Switch on command type: "brief" → Code Node "Run KOL Brief", "landscape" → Code Node "Run TA Landscape", "ct" → Code Node "Run CT Crawler", "status" → Code Node "Get Status"*

- [ ] **C.1.3:** Add Code Node "Run KOL Brief" — execute `generate_kol_brief.py` with condition from command
  - *Runs from 04_Product_KOL_Briefs/. Uses `--condition` or `--target` parameter to specify the disease area.*

- [ ] **C.1.4:** Add Code Node "Run TA Landscape" — execute `generate_ta_landscape.py` with target from command
  - *Runs from 05_Product_TA_Landscape/. Generates TA landscape report for specified therapeutic area.*

- [ ] **C.1.5:** Add Code Node "Run CT Crawler" — execute `ct_crawler.py --mode delta` or `--mode query --query {condition}`
  - *Runs from 02_CT_Data_Engine/. Default: delta mode (last 24h). With condition: query mode.*

- [ ] **C.1.6:** Add Code Node "Get Pipeline Status" — read all `_summary.json` files and return formatted status
  - *Uses `pipeline_summary.py`'s `read_all_summaries()`. Returns: each engine's last run time, status, duration, counts. Formatted as Telegram-friendly message.*

### C.2: Command response flow

- [ ] **C.2.1:** Add Telegram Node "Reply: Command Result" — send result of on-demand command back to the chat
  - *Each command branch connects to this single response node. Text includes: command name, result summary, duration, any errors.*

- [ ] **C.2.2:** Wire all command branches to converge on the Reply node
  - *4 branches (brief, landscape, ct, status) all feed into the same Telegram response node.*

---

## SWIP2-D: Meddash-CTO Paperclip Agent Instructions

### D.1: Update Meddash-CTO AGENTS.md for health monitoring

- [ ] **D.1.1:** Update Meddash-CTO agent instructions at `/home/doc_victus/.paperclip/instances/default/companies/cf39ae28.../agents/9511e1ea.../instructions/AGENTS.md` — add health check protocol
  - *Protocol: 1) Read pipeline summary JSONs from 06_Shared_Datastores/pipeline_summaries/, 2) Check for error states (status=failure), 3) If failure found, read the error field and create an URGENT issue for Alfred Chief (break-glass escalation), 4) If healthy, confirm counts and note rotation category progress, 5) Check biocrawler leads count and flag if >5% drop from previous day, 6) Summarize in issue comment.*

- [ ] **D.1.2:** Add MeSH rotation awareness to Meddash-CTO instructions — "Check mesh_rotation_state.json and rotation_log.db. Verify this week's category completed."
  - *Weekly rotation context: Current MeSH category is stored in mesh_rotation_state.json. Meddash-CTO should check whether the scheduled rotation completed and report progress.*

- [ ] **D.1.3:** Add KOL brief assignment protocol — "If biocrawler leads contain a high-priority company, assign Engine 04 (KOL Brief) generation via Telegram `/brief {condition}` or by running `generate_kol_brief.py --target {condition}`"
  - *Meddash-CTO acts as gatekeeper for on-demand briefs. When biocrawler finds a high-value lead, CTO can trigger brief generation manually or via the n8n Telegram bot.*

### D.2: Meddash-COO agent oversight

- [ ] **D.2.1:** Update Meddash-COO agent instructions to include daily pipeline status awareness
  - *Meddash-COO (ca4c3f1a) should check: 1) Did the daily pipeline run? 2) Are summary JSONs present and recent? 3) Any error flags? 4) Escalate to Meddash-CTO or Alfred if pipeline misses a scheduled run.*

- [ ] **D.2.2:** Meddash-COO should report to CQ-COO on cross-product status
  - *reportsTo: CQ-COO. Meddash-COO sends a daily summary to CQ-COO via Paperclip issue comment: "Meddash pipeline: X KOLs, Y leads, Z trials. Rotation: {category}. Status: healthy/error."*

---

## SWIP2-E: Pipeline Health Monitoring Framework

### E.1: Automated health checks in n8n

- [ ] **E.1.1:** Code Node "Health Check" reads all `*_summary.json` files from `06_Shared_Datastores/pipeline_summaries/`
  - *Pattern: Read kol_pipeline_summary.json, biocrawler_summary.json, ct_crawler_summary.json. Build a unified health report JSON: {overall_status, engines: [{name, status, duration, error, last_run}], rotation: {category, week, cycle}, total_kols, total_leads}*

- [ ] **E.1.2:** Health check classifies engine status as "healthy", "degraded", or "failed"
  - *Classification: healthy = status=success AND duration < 30 min, degraded = status=success but duration > 30 min OR status=partial, failed = status=failure OR summary JSON missing for >24h*

- [ ] **E.1.3:** Health report is passed to both Telegram alert AND Paperclip issue
  - *Two parallel consumers: 1) Telegram (Dr. Don gets immediate notification), 2) Paperclip issue (Meddash-CTO gets full context for autonomous action)*

### E.2: Stale data detection

- [ ] **E.2.1:** Add staleness check — if `kol_pipeline_summary.json` is older than 24 hours, flag as "stale"
  - *Code: `os.path.getmtime(summary_path)` compared to `time.time()`. If >86400 seconds, status = "stale".*

- [ ] **E.2.2:** Add DB row count check — verify meddash_kols.db and biocrawler_leads.db have grown since last run
  - *Query: `SELECT COUNT(*) FROM kols` and `SELECT COUNT(*) FROM biotech_leads`. Store previous count in pipeline_state/ and compare. Flag if count decreased (data loss) or hasn't changed (pipeline not running).*

- [ ] **E.2.3:** Flag anomalies — >20% count drop in any DB = urgent alert via Telegram
  - *If kols count drops by >20% from previous run, immediately send 🚨 Telegram alert and escalate to Alfred Chief via Paperclip URGENT issue.*

---

## SWIP2-F: Telegram Bot Command Interface

### F.1: Meddash bot command definitions

- [ ] **F.1.1:** Define command set for Meddash Telegram bot: `/status`, `/brief {condition}`, `/landscape {disease}`, `/ct {mode}`, `/run` (force daily pipeline), `/rotation` (show MeSH rotation state)
  - *These commands are parsed by the Code Node "Parse Command" in the n8n workflow. The bot only responds to Dr. Don's chat ID (6253013213).*

- [ ] **F.1.2:** `/status` command — reads all summary JSONs, returns formatted status message
  - *Response format: "📊 Meddash Pipeline Status\n• Engine 01 (KOL): ✅ success, 538 KOLs, 2.3 min\n• Engine 03 (BioCrawler): ✅ success, 47 leads, 1.1 min\n• Rotation: Digestive System Diseases (Week 6/12)\n• Next run: 02:00 UTC"*

- [ ] **F.1.3:** `/rotation` command — reads `mesh_rotation_state.json` and `mesh_rotation_log.db`, returns rotation history
  - *Response: "🔄 MeSH Rotation\n• Current: Digestive System Diseases (C06)\n• Week: 6 of 12\n• Cycle: 1\n• Categories completed: Neoplasms, Musculoskeletal, Respiratory, Nervous System, Cardiovascular\n• Next: Eye Diseases (C11)"*

- [ ] **F.1.4:** `/brief {condition}` command — triggers Engine 04 on-demand
  - *Response: "📋 Generating KOL brief for: {condition}\nThis takes 2-5 minutes. I'll send the result when ready."*

- [ ] **F.1.5:** `/ct {mode}` command — triggers Engine 02 on-demand
  - *Modes: delta (last 24h), full (all trials), query {condition} (specific search). Response: "🔍 CT Crawler: {mode} mode started. Estimated time: {X} min."*

- [ ] **F.1.6:** `/run` command — forces the entire daily pipeline immediately
  - *Same as Schedule Trigger, but on-demand. Runs Engine 01 + Engine 03, then health check. Response: "🚀 Force-running Meddash pipeline now. Will report in ~5 min."*

### F.2: Command response Telegram nodes

- [ ] **F.2.1:** Each Code Node output routes to a "Format Response" Code Node
  - *The Format Response node takes engine output and creates a Telegram-friendly message (emojis, bullet points, <4096 chars).*

- [ ] **F.2.2:** Response is sent back via the Meddash Telegram bot (same chat ID)
  - *Uses the `Telegram account Meddash` credential in n8n. Chat ID comes from the original Telegram trigger message.*

---

## SWIP2-G: End-to-End Testing

### G.1: Dry run the complete workflow

- [ ] **G.1.1:** Test Schedule Trigger: manually trigger the n8n workflow via the "Execute Workflow" button
  - *Verify: both Code nodes run, summary JSONs are created, Telegram messages are sent, Paperclip issue is created.*

- [ ] **G.1.2:** Test Telegram Trigger: send a message to the Meddash bot and verify n8n picks it up
  - *Send `/status` to Meddash bot. Verify: n8n workflow starts, command is parsed, status is returned in Telegram.*

- [ ] **G.1.3:** Test Health Check: verify Code Node reads all 3 summary JSONs correctly
  - *After a manual pipeline run, verify the Health Check Code Node reads kol_pipeline_summary.json, biocrawler_summary.json, and produces a valid unified health report.*

- [ ] **G.1.4:** Test Error Handler: intentionally fail one engine (e.g., set invalid DB path) and verify Error Trigger fires Telegram alert
  - *Set MEDDASH_ROOT to invalid path, run pipeline, verify 🚨 error message arrives via Meddash bot.*

- [ ] **G.1.5:** Test Paperclip Integration: verify Meddash-CTO issue is created with health data
  - *After pipeline run, check Paperclip dashboard at http://localhost:3100 for new issue assigned to Meddash-CTO (9511e1ea).*

- [ ] **G.1.6:** Test on-demand commands: `/status`, `/rotation`, `/brief NSCLC`
  - *Send each command to Meddash bot, verify response format and content.*

- [ ] **G.1.7:** Activate workflow in n8n and verify Schedule Trigger fires at 02:00 UTC
  - *After all tests pass, activate the workflow. Verify the next 02:00 UTC run executes automatically.*

### G.2: Monitoring validation

- [ ] **G.2.1:** Let the pipeline run overnight and check Telegram messages in the morning
  - *Verify: 02:00 UTC trigger fires, engines run, health report is generated, Meddash-CTO issue is created, Telegram messages arrive.*

- [ ] **G.2.2:** Verify Meddash-CTO agent picks up the health check issue on its next heartbeat (5 min interval)
  - *Check Paperclip logs for Meddash-CTO processing the issue. Expected: agent reads health data, posts analysis as issue comment.*

- [ ] **G.2.3:** Verify no duplicate runs — if both Telegram trigger and Schedule trigger fire at the same time, only one pipeline execution should occur
  - *n8n has execution dedup by workflow ID + time window. Verify that rapid double-triggers don't cause duplicate Paperclip issues or duplicate Telegram alerts.*

---

## SWIP2-H: Documentation + Handoff

### H.1: Operational documentation

- [ ] **H.1.1:** Update wiki page `reference/meddash-backend-map.md` with n8n workflow details, Paperclip agent assignments, and health monitoring endpoints
  - *Add: n8n workflow ID, trigger types, Telegram bot details, Paperclip agent IDs, summary JSON schema, health check protocol.*

- [ ] **H.1.2:** Update `concepts/meddash-cq-org-chart.md` with Meddash-COO and Meddash-CTO daily health check responsibilities
  - *Add: Meddash-CTO performs health check within 10 min of pipeline run. Meddash-COO reviews daily status and escalates anomalies to CQ-COO.*

- [ ] **H.1.3:** Create `operations/meddash-runbook.md` — step-by-step manual override instructions
  - *Content: How to manually trigger each engine, how to read summary JSONs, how to restart n8n, how to re-run a failed engine, common error messages and fixes.*

- [ ] **H.1.4:** Update skill `cq-triarchy-pipeline` to include Meddash workflow details alongside CQ workflow
  - *Refactor skill to be a general triarchy skill covering both CQ and Meddash pipelines.*

---

## Summary: SWIP2 Checkbox Count

| Section | Items | Description |
|---------|-------|-------------|
| A: n8n Daily Pipeline | 9 | Wire Engines 01+03 into n8n with cron + Telegram triggers |
| B: Health Monitoring + Paperclip | 5 | Meddash-CTO issue, Telegram alerts, error handling |
| C: On-Demand Commands | 8 | Telegram bot commands for /brief, /landscape, /ct, /status |
| D: Paperclip Agent Instructions | 5 | Meddash-CTO and Meddash-COO health monitoring roles |
| E: Health Monitoring Framework | 6 | Automated health checks, staleness detection, anomaly alerts |
| F: Telegram Command Interface | 8 | Bot commands and response formatting |
| G: End-to-End Testing | 10 | Dry run, error testing, overnight validation |
| H: Documentation | 4 | Wiki updates, runbook, skill update |
| **TOTAL** | **55** | |

---

## n8n Workflow Node Map (Target Architecture)

```
[Schedule Trigger 02:00 UTC] ──┐
                                ├─→ [Telegram: "🚀 Triggered"] 
[Telegram Trigger /run]     ───┘         │
                                         ▼
                               [Code: Run Engine 01+03]
                                         │
                                         ▼
                               [Telegram: "✅ Engines Complete"]
                                         │
                                         ▼
                               [Wait 5 min]
                                         │
                                         ▼
                               [Code: Health Check]
                                         │
                        ┌────────────────┼────────────────┐
                        ▼                                 ▼
          [HTTP: Meddash-CTO Issue]        [Telegram: "📊 Report Sent"]
                        
[Telegram Trigger /command] ──→ [Code: Parse Command]
                                        │
                    ┌───────────┬───────┼────────┬──────────┐
                    ▼           ▼       ▼        ▼          ▼
              [Run Brief] [Run TA] [Run CT] [Run Status] [Force Run]
                    │           │       │        │          │
                    └───────────┴───────┴────────┘          │
                                        │                    │
                                        ▼                    ▼
                               [Telegram: "Reply: Result"]   (→ daily pipeline)

[Error Trigger] ──→ [Telegram: "🚨 Pipeline ERROR"]
```

## Key Technical Decisions

1. **n8n runs Engine 01 and 03 sequentially in one Code node** — they're fast (<5 min combined) and share the same Python environment. Engine 02 (CT Crawler) is on-demand only.

2. **Paperclip issue for Meddash-CTO, not Meddash-COO** — CTO is the technical executor. COO gets summarized status via cross-division reporting to CQ-COO.

3. **Telegram bot is the primary control surface** — Dr. Don interacts with Meddash via the Meddash bot, not the n8n UI. `/status`, `/run`, `/brief`, `/ct` are the four main commands.

4. **5-minute wait (not 10)** — Meddash engines write to SQLite (local), not Supabase (remote). SQLite writes are near-instant. 5 minutes is generous.

5. **Error Trigger catches all node failures** — any crash, timeout, or API error in any node triggers the 🚨 alert. Dr. Don sees it immediately, Alfred Chief gets a Paperclip URGENT issue.

6. **Dual-trigger (cron + Telegram) provides both reliability and flexibility** — if the cron fails, Dr. Don can `/run` manually. If Dr. Don wants an ad-hoc run at noon, Telegram trigger works.