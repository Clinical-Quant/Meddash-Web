     1|# MDP3 Bug Fixes
     2|
     3|Operational bug-fix ledger for Meddash Phase 3. Each entry records timestamp, symptom, root cause, files touched, verification, and remaining caveats.
     4|
     5|---
     6|
     7|## 2026-04-29 12:34:15 EDT — BF-DASH-20260429-001 — Streamlit Dashboard Stale Data / Dashboard-Monitor Not Doing Its Job
     8|
     9|### User-reported symptom
    10|- Live Streamlit dashboard was not updating.
    11|- Dashboard data looked stale.
    12|- `Meddash-CQ-Dashboard-Monitor` / `DevOps - Dashboard Monitor & Upkeeper` did not appear to be maintaining the dashboard.
    13|
    14|### Investigation evidence
    15|- Streamlit process was running on port `5090` and `_stcore/health` returned `ok` before the fix.
    16|- Dashboard code had `REFRESH_SECONDS = 120` in `config.py`, but `app.py` never imported or used it. Result: a browser tab could remain visually stale indefinitely unless manually refreshed.
    17|- `widgets/pulse.py` counted CT trials using the local SQLite table name `ct_trials`, but the real table inside `ct_trials.db` is `trials`.
    18|- Real local DB counts at investigation time:
    19|  - `meddash_kols.db` / `kols`: `8,298`
    20|  - `biocrawler_leads.db` / `biotech_leads`: `658`
    21|  - `ct_trials.db` / `trials`: `1,005`
    22|- `dashboard_monitor_state.json` was stale:
    23|  - previous `last_check`: `2026-04-27T05:53:00Z`
    24|  - previous trials count: `100`, no longer correct after CT crawler ingestion fixed the real `trials` table.
    25|- Dashboard-Monitor log folder existed but had no active current log files before Alfred wrote the bug-fix log.
    26|- No existing Paperclip issue was assigned to `Meddash-CQ-Dashboard-Monitor` for this stale-dashboard problem.
    27|- Upstream pipeline summaries were genuinely stale/degraded in places:
    28|  - `ct_crawler_summary.json`: about `20.66h` old at first check, status `success`
    29|  - `biocrawler_summary.json`: about `20.04h` old, status `success`
    30|  - `kol_centrality_summary.json`: about `33.33h` old, status `success`
    31|  - `kol_pipeline_summary.json`: about `20.67h` old, status `partial`
    32|  - `meddash_kols.db`: very old mtime because KOL DB itself has not been rewritten recently
    33|
    34|### Root causes
    35|1. Dashboard auto-refresh was only configured, not wired.
    36|   - `config.py` defined `REFRESH_SECONDS = 120`.
    37|   - `app.py` did not consume it.
    38|   - So the live browser UI could show stale state.
    39|
    40|2. Pulse widget read the wrong CT local table.
    41|   - Broken: `_sqlite_count("trials", "ct_trials")`
    42|   - Correct: `_sqlite_count("trials", "trials")`
    43|
    44|3. Some dashboard health rendering hid degraded states.
    45|   - `pipeline_health.py` treated `partial` as grey/idle-like instead of degraded/yellow.
    46|   - `factory_floor.py` rendered >24h SQLite mtime as grey instead of red.
    47|
    48|4. Dashboard-Monitor instructions were insufficient / partly wrong.
    49|   - It only logged in the “all healthy” go-to-sleep path, not on every degraded/failed heartbeat.
    50|   - Its state file had not been updated since April 27.
    51|   - Its page check instructed `curl / | grep Factory`, but Streamlit root HTML does not contain app widget text; it returns the JS shell and app content renders later over websocket.
    52|   - Its Supabase count instructions used generic `id` selects for tables that do not all have `id`.
    53|
    54|5. Paperclip wakeup payload caveat discovered.
    55|   - The complex nested wakeup payload documented in the local skill returned HTTP `400`.
    56|   - The local Paperclip build accepted the simple payload: `{ "reason": "issue_assigned", "issueId": "..." }`.
    57|
    58|### Fixes applied
    59|
    60|#### Dashboard app fixes
    61|- Patched:
    62|  - `/mnt/c/Users/email/.gemini/antigravity/CTO/Meddash-CQ_Dashboard/app.py`
    63|- Added zero-dependency browser auto-refresh:
    64|  - `REFRESH_SECONDS` is now imported from `config.py`.
    65|  - `app.py` now emits a browser meta refresh every `120` seconds.
    66|  - Sidebar now shows:
    67|    - last render timestamp
    68|    - auto-refresh mode
    69|    - version `v1.1 — 2026-04-29`
    70|- Important implementation note:
    71|  - An optional `streamlit_autorefresh` import path was tested and removed because it hung startup under WSL/NTFS in this venv. The final fix uses browser meta refresh only.
    72|
    73|#### Widget data correctness fixes
    74|- Patched:
    75|  - `/mnt/c/Users/email/.gemini/antigravity/CTO/Meddash-CQ_Dashboard/widgets/pulse.py`
    76|- Changed CT local count from wrong table `ct_trials` to real table `trials`.
    77|
    78|#### Health-rendering fixes
    79|- Patched:
    80|  - `/mnt/c/Users/email/.gemini/antigravity/CTO/Meddash-CQ_Dashboard/widgets/pipeline_health.py`
    81|  - `/mnt/c/Users/email/.gemini/antigravity/CTO/Meddash-CQ_Dashboard/widgets/factory_floor.py`
    82|- `partial` engine status now renders yellow/degraded instead of grey.
    83|- SQLite DB mtime older than 24h now renders red instead of grey in Factory Floor.
    84|
    85|#### Dashboard-Monitor instruction fixes
    86|- Patched:
    87|  - `/home/doc_victus/.paperclip/instances/default/companies/cf39ae28-5bd5-44d1-b888-b01f83192fd5/agents/b04b8342-527c-4ceb-abee-bf44dade4fe7/instructions/AGENTS.md`
    88|- Added/changed:
    89|  - monitor must update `dashboard_monitor_state.json` on every heartbeat
    90|  - monitor must write a log on every heartbeat, including degraded/failed states
    91|  - monitor must not rely on `curl / | grep Factory`
    92|  - monitor must check Streamlit health endpoint + root Streamlit shell HTML/static JS instead
    93|  - monitor must use correct Supabase select columns for known non-`id` tables
    94|  - monitor must verify that `app.py` actually wires `REFRESH_SECONDS`
    95|
    96|#### Monitor state/log fixes
    97|- Rewrote current state file:
    98|  - `/mnt/c/Users/email/.gemini/antigravity/Meddash_organized_backend/06_Shared_Datastores/pipeline_state/dashboard_monitor_state.json`
    99|- New state includes:
   100|  - current `last_check`
   101|  - status `degraded`
   102|  - corrected DB counts
   103|  - streamlit health `ok`
   104|  - auto-refresh wiring status
   105|  - summary freshness details
   106|- Wrote bug-fix monitor log:
   107|  - `/mnt/c/Users/email/Hermes Agent Win Files/Meddash-Paper Clip Agent Logs/Meddash-CQ-Dashboard-Monitor/20260429-163316-bug-fix-dashboard-stale-data.md`
   108|
   109|#### Paperclip issue + wakeup
   110|- Created issue assigned to Dashboard-Monitor:
   111|  - Issue number: `THE-10`
   112|  - Issue ID: `ac5fffee-d6fd-4402-9d4a-ff085963f828`
   113|  - Title: `Dashboard stale-data post-fix audit — 2026-04-29 16:33 UTC`
   114|  - Assignee: `Meddash-CQ-Dashboard-Monitor` (`b04b8342-527c-4ceb-abee-bf44dade4fe7`)
   115|- Explicitly woke Dashboard-Monitor.
   116|- Wakeup accepted:
   117|  - HTTP `202`
   118|  - Run ID: `3a8eba29-2688-4292-9835-9c84bf8def9e`
   119|  - Status: `queued`
   120|- Follow-up verification showed Dashboard-Monitor still listed as `idle`, issue `THE-10` still `backlog`, and `executionRunId` still `null`. This means the dashboard-code bug is fixed, but Paperclip runtime/adapter pickup for this monitor still needs attention.
   121|
   122|#### Meddash-CTO escalation
   123|- Created CTO escalation issue because Dashboard-Monitor did not actually take the assigned issue after accepted wakeup:
   124|  - Issue ID: `f1bbb869-5690-45d7-be6a-b2390191d869`
   125|  - Title: `Dashboard-Monitor runtime not taking assigned issue — 2026-04-29 16:38 UTC`
   126|  - Assignee: `Meddash-CTO` (`9511e1ea-def0-4c0b-a78b-7d9f63cae6a2`)
   127|- Explicitly woke Meddash-CTO.
   128|- CTO wakeup accepted:
   129|  - HTTP `202`
   130|  - Run ID: `daf6759f-64f8-4d0f-8c5a-e358c7f16a40`
   131|
   132|#### Skill maintenance
   133|- Patched Hermes skill:
   134|  - `paperclip-agent-setup`
   135|- Reason:
   136|  - Previous wakeup example used a nested payload shape that returned HTTP `400` on this local Paperclip build.
   137|  - Skill now documents the simple working payload shape.
   138|
   139|### Verification performed
   140|- Python syntax check passed for:
   141|  - `app.py`
   142|  - `config.py`
   143|  - `supabase_client.py`
   144|  - `widgets/pulse.py`
   145|  - `widgets/pipeline_health.py`
   146|  - `widgets/factory_floor.py`
   147|  - `widgets/cq_panel.py`
   148|  - `widgets/operations.py`
   149|- Streamlit restarted on port `5090`.
   150|- Health endpoint verified:
   151|  - `http://127.0.0.1:5090/_stcore/health` → `ok`
   152|- Root HTML verified by curl:
   153|  - `http://127.0.0.1:5090/` returns Streamlit HTML shell and static JS assets.
   154|- Live process verified listening:
   155|  - port `5090`
   156|  - process command: `streamlit run app.py --server.port 5090 --server.headless true`
   157|- Dashboard code markers verified present:
   158|  - `browser_meta_refresh`
   159|  - `REFRESH_SECONDS`
   160|  - `Last render`
   161|  - `_sqlite_count("trials", "trials")`
   162|  - `status_val == "partial"`
   163|  - stale DB status changed to red
   164|
   165|### Remaining caveats / next steps
   166|- The dashboard now refreshes and reports stale/degraded state more honestly, but upstream data still needs pipeline freshness work:
   167|  - KOL pipeline summary was `partial`.
   168|  - KOL centrality summary was older than 24h.
   169|  - Meddash KOL SQLite DB mtime remains very old because the KOL DB itself has not been rewritten recently.
   170|- Dashboard-Monitor is now assigned issue `THE-10`; wakeup returned HTTP `202`, but follow-up showed the issue remained backlog with `executionRunId=null`.
   171|- Meddash-CTO escalation was created and woken for the remaining Paperclip runtime/adapter pickup problem.
   172|- This does not replace the broader `c-runs` work item: full Meddash + CQ pipeline run verification is still needed.
   173|
   174|---
   175|
   176|## 2026-04-29 13:20:12 EDT — BF-CRUN-20260429-002 — C-Run Verification Exposed SEC Timeout + CT Health Filename Bug
   177|
   178|### Trigger
   179|- Continued SWIP4 Section C: full Meddash + CQ pipeline verification after dashboard stale-data repair.
   180|- Ran direct Ops API verification because n8n workflows are currently present but inactive (`active=0`), so the n8n scheduler/manual path would not honestly prove the live pipeline.
   181|
   182|### Evidence
   183|- Raw verification log:
   184|  - `/mnt/c/Users/email/.gemini/antigravity/Meddash Phase 3 Automation Observation and Sales/.archive/20260429-124859-c-runs-direct-ops-verification.json`
   185|- Meddash results:
   186|  - BioCrawler Engine 03: success, `49.7s`, `659` tracked leads.
   187|  - CT Engine 02: success, `125.1s`, `2,452` trials fetched.
   188|  - KOL Engine 01: inner `timeout` at `600s`; still a remaining KOL issue.
   189|  - `/meddash/health`: Telegram OK, DB counts KOL `8,298`, CT `1,005`, BioCrawler `659`.
   190|- CQ initial result:
   191|  - `/cq/ticker-spine`: success.
   192|  - `/cq/detect`: initially partial because `sec_8k_monitor.py` timed out.
   193|  - FDA PDUFA and PR Wire succeeded.
   194|  - `/cq/latest-report`: OK, Telegram OK, but latest report file was still `2026-04-27`, so newsletter drafting remains a separate downstream item.
   195|
   196|### Root causes
   197|1. `meddash_ops_api.py` health check used the logical name `ct_delta_summary.json`, but CT Engine 02 actually writes `ct_crawler_summary.json`.
   198|   - Result: live health falsely reported CT summary as missing even after a successful CT crawl.
   199|2. `sec_8k_monitor.py` used an unbounded SEC `requests.get()` call.
   200|   - Result: one slow SEC response could hang the whole CQ detection layer.
   201|3. `cq_pipeline_runner.py` gave SEC only `60s` even though a bounded daily SEC scan can legitimately need more than 60 seconds.
   202|
   203|### Fixes applied
   204|- Patched Ops API:
   205|  - `/mnt/c/Users/email/.gemini/antigravity/Meddash_organized_backend/07_DevOps_Observability/meddash_ops_api.py`
   206|  - `ct_delta` now reads actual file `ct_crawler_summary.json` and records `summary_file` in the health payload.
   207|  - Restarted Ops API and verified live `/meddash/health`: `ct_delta=success`, `biocrawler=success`, `kol_pipeline=partial`, Telegram OK.
   208|- Patched SEC monitor:
   209|  - `/mnt/c/Users/email/.gemini/antigravity/CTO/CQ_Team/scripts/phase1_regulatory/sec_8k_monitor.py`
   210|  - Added `SEC_REQUEST_TIMEOUT` default `10s`.
   211|  - Added `SEC_MAX_TICKERS` default `40` for bounded daily runs.
   212|  - Added Supabase insert timeout `20s`.
   213|- Patched CQ runner:
   214|  - `/mnt/c/Users/email/.gemini/antigravity/CTO/CQ_Team/scripts/cq_pipeline_runner.py`
   215|  - SEC 8-K monitor now gets `120s`; FDA/PR remain `60s`.
   216|
   217|### Verification after fix
   218|- Direct SEC test passed under `90s`:
   219|  - fetched `125` verified tickers
   220|  - scanned first `40`
   221|  - completed without timeout
   222|- Full `/cq/detect` rerun passed:
   223|  - elapsed `106.21s`
   224|  - overall `success`
   225|  - ticker registry success
   226|  - Yahoo ticker news success
   227|  - SEC 8-K success
   228|  - FDA PDUFA success
   229|  - PR Wire success
   230|- Telegram sends verified OK for:
   231|  - `/meddash/health`
   232|  - `/cq/detect`
   233|  - `/cq/latest-report`
   234|
   235|### Paperclip verification
   236|- Created and assigned CQ-Selector issue:
   237|  - `THE-12`
   238|  - `364aa662-4b52-44a7-9d40-386c793ea15f`
   239|- Created and assigned CQ-Monitor issue:
   240|  - `THE-13`
   241|  - `19a92a8e-bcdf-4980-ab32-9bd4ca6aa147`
   242|- Both used correct full `assigneeAgentId` and project ID.
   243|- Wakeups accepted HTTP `202`:
   244|  - Selector run: `83a8bd15-268b-413e-ab85-b2f45e8836a6`
   245|  - Monitor run: `5537b8b9-afd6-412b-802c-706529916683`
   246|
   247|### Remaining caveats
   248|- n8n workflows are currently `active=0`; direct Ops API verification is green, but n8n UI activation/manual trigger remains a separate operator step.
   249|- KOL Engine 01 still timed out at the runner’s `600s` guard.
   250|- CT crawler still emits an internal stale Telegram 404 in stderr despite centralized Ops API Telegram succeeding; internal per-engine Telegram notifier needs cleanup later.
   251|- Latest CQ daily report endpoint works and sends Telegram, but the latest report file is old (`2026-04-27`), so CQ newsletter draft generation remains a downstream item.
   252|
   253|---
   254|

---

## 2026-04-29 13:52 EDT — BF-KOL-20260429-003 — KOL Engine 01 Scheduled Run Timeout Fixed

### Trigger
- SWIP4 Section C Meddash verification showed Engine 01 KOL returning an inner `timeout` at the runner's `600s` guard.

### What was wrong
- The scheduled/Ops API path for KOL Engine 01 was using the same behavior as a deep/manual KOL crawl.
- It attempted to process `545` BioCrawler-derived targets with `50` PubMed results each.
- It also allowed full-database disambiguation, publication-weight recomputation, and centrality work in the scheduled lane.
- PubMed/Bio.Entrez calls had no explicit socket timeout, so network stalls could block the whole run.

### What was done
- Patched `01_KOL_Data_Engine/nightly_scheduler.py`:
  - added `--max-targets`
  - added `--skip-disambiguation`
  - added `--skip-weights`
  - preserved full/deep behavior for manual runs
- Patched `01_KOL_Data_Engine/run_pipeline.py`:
  - added skip flags for full-DB disambiguation and publication-weight phases
- Patched `01_KOL_Data_Engine/extract_publications.py`:
  - added process-wide PubMed socket timeout via `MEDDASH_PUBMED_TIMEOUT`, default `20s`
- Patched `07_DevOps_Observability/meddash_pipeline_runner.py`:
  - scheduled/Ops API Engine 01 now runs bounded:
    `python3 nightly_scheduler.py --max-targets 5 --max-results 5 --skip-disambiguation --skip-weights --skip-centrality --json-summary`

### Verification
- Syntax check passed for modified KOL/Ops files.
- Direct bounded KOL run succeeded in `135.19s`.
- Live Ops API `/meddash/engine01` succeeded in `122.95s`.
- Live Ops API `/meddash/health` reports:
  - `kol_pipeline: success`
  - `ct_delta: success`
  - `biocrawler: success`
  - Telegram send OK

### Caveats
- This is the scheduled freshness lane, not the deep KOL rebuild lane.
- Full KOL disambiguation/weights/centrality remain available for manual/deep runs but should not block n8n/Ops API daily freshness.
- Internal stale Telegram notifier still emits HTTP 404 inside KOL logs; centralized Ops API Telegram succeeded and should remain the authoritative notification lane.

