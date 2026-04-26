# MDP3-SWIP1 — Step-Wise Implementation Plan: Pre-Automation Fixes

> **Author:** Hermes Alfred Chief  
> **Date:** 2026-04-26 22:30 UTC  
> **Scope:** Code-level fixes to existing scripts BEFORE n8n/Paperclip automation (SWIP2)  
> **Goal:** Fix issues from Section 3 + implement solutions from Section 5 of MDP3-Pre Implementation Plan  

---

## SWIP1-A: Fix Engine 01 — Nightly Scheduler Hardcoding

### A.1: Refactor nightly_scheduler.py — Remove hardcoded NSCLC fallback

- [x] **A.1.1:** Replace hardcoded `targets = ["Non-Small Cell Lung Cancer"]` with MeSH rotation logic
  - *Completed: NSCLC fallback completely removed. nightly_scheduler.py v2.0 uses get_rotation_target() from mesh_rotation module for T1+T2 merge.*
  - *Description: Will add MESH_ROTATION list and weekly index selection as primary target source, with BioCrawler leads as secondary. NSCLC fallback removed entirely.*
  
- [x] **A.1.2:** Add MeSH rotation schedule (12 categories, ISO week-based cycling)
  - *Completed: MESH_ROTATION constant in mesh_rotation.py with 12 categories. Week index derived from isocalendar()[1] % 12.*
  - *Description: Will add MESH_ROTATION constant with 12 MeSH top-level disease categories. Week index derived from `datetime.now().isocalendar()[1] % len(MESH_ROTATION)` so it auto-rotates every week.*

- [x] **A.1.3:** Add rotation state file — `mesh_rotation_state.json`
  - *Completed: Created in 06_Shared_Datastores/pipeline_state/mesh_rotation_state.json. Auto-created on first run.*
  - *Description: Will create a JSON state file tracking current_week, last_category, last_run_timestamp, cycle_count. Prevents re-running the same category twice in one week and provides audit trail.*

- [x] **A.1.4:** Add rotation logging — log which MeSH category ran each night
  - *Completed: Structured logging to kol_scheduler.log via Python logging module. Also logged to mesh_rotation_log.db SQLite.*
  - *Description: Will add structured logging: `[{timestamp}] Rotation target: {category} (Week {week_num}, Cycle {cycle})`. This feeds into Meddash-Monitor health checks later.*

- [x] **A.1.5:** Add deduplication — rotation target skips if BioCrawler already has it
  - *Completed: get_rotation_target() checks normalized lead targets against rotation category. If rotation TA matches any lead TA (partial match), rotation is skipped to avoid double-pulling.*
  - *Description: Will check `biotech_leads.primary_indication` against rotation target. If the rotation category already exists as a BioCrawler indication, skip the extra query (avoid duplicated PubMed pull).*

- [x] **A.1.6:** Merge all targets — Tier 1 (BioCrawler leads) + Tier 2 (MeSH rotation) with dedup
  - *Completed: get_rotation_target(lead_targets) in mesh_rotation.py returns deduped list. Verified: 538 BioCrawler leads + 1 rotation target = 539 unique targets.*
  - *Description: Will combine `lead_targets` from biocrawler_leads.db + `rotating_target` from MeSH schedule → `list(set(lead_targets + [rotating_target]))` → passed to `run_pipeline.py --targets`*

### A.2: Refactor run_pipeline.py — Accept rotation target alongside targets

- [x] **A.2.1:** Add `--rotation_target` CLI parameter (handled via nightly_scheduler.py)
  - *Completed: nightly_scheduler.py v2.0 handles rotation internally via mesh_rotation module. No longer needed as a separate param to run_pipeline.py — targets are pre-merged before calling run_pipeline.py.*
  - *Description: Will add optional `--rotation_target` argument alongside existing `--targets`. When provided, appended to targets list after dedup.*

- [ ] **A.2.2:** Add `--pull_id` documentation and validation
  - *Description: Will add user-facing docstrings for pull_id campaign sandbox mode. Already exists in code but undocumented. No code change — just docstrings.*

- [ ] **A.2.3:** Add structured exit codes (0=success, 1=partial, 2=failure)
  - *Description: Will change `run_nightly_pipeline()` to return exit codes instead of just raising exceptions. Enables n8n to distinguish success/failure/Partial in SWIP2.*

- [ ] **A.2.4:** Add JSON summary output — `pipeline_summary.json`
  - *Description: Will write a structured JSON file after each run: targets_run, publications_fetched, kols_ingested, kols_disambiguated, kols_weighted, rotation_category, timestamp, exit_code. Feeds into health monitoring.*

---

## SWIP1-B: Fix Engine 02 — CT Crawler Has No Automated Trigger

### B.1: Refactor ct_crawler.py — Make it n8n-ready

- [ ] **B.1.1:** Add `--json-summary` flag for structured output
  - *Description: Will add optional `--json-summary` flag that writes crawl results to `ct_crawl_summary.json` instead of just console output. Enables downstream monitoring and n8n parsing in SWIP2.*

- [ ] **B.1.2:** Add structured exit codes (0=success, 1=partial, 2=failure)
  - *Description: Will add try/except with explicit exit codes. Currently raises RuntimeError on failure. Will also exit 1 for partial crawls (some pages skipped).*

- [ ] **B.1.3:** Fix hardcoded DevOps import path
  - *Description: Will replace `sys.path.append(r"C:\Users\email\.gemini\antigravity\...")` with relative path resolution using `__file__` parent directories. Makes script portable across environments.*

- [ ] **B.1.4:** Add environment variable support for output directory
  - *Description: Will add `CT_RAW_DIR` env var override for `RAW_DIR`. Currently hardcoded to `ct_raw_json/` relative to CWD. Will also default to `06_Shared_Datastores/ct_raw_json/` if env var not set.*

### B.2: Refactor ct_ingestion.py — Structured output

- [ ] **B.2.1:** Add ingestion summary JSON output
  - *Description: Will write `ct_ingestion_summary.json` with: trials_processed, new_trials, updated_trials, tables_touched, errors, timestamp. Feeds monitoring.*

- [ ] **B.2.2:** Add exit codes matching ct_crawler convention
  - *Description: Will use same exit code convention: 0=success, 1=partial (some records failed), 2=failure.*

---

## SWIP1-C: Fix Engine 03 — BioCrawler Runs via .bat File

### C.1: Refactor biocrawler.py — Make it n8n-ready

- [ ] **C.1.1:** Add `--json-summary` flag for structured output
  - *Description: Will write `biocrawler_summary.json` with: companies_crawled, leads_updated, sv_scores_calculated, timestamp, exit_code.*

- [ ] **C.1.2:** Add CLI entry point with argparse (currently no `if __name__` block)
  - *Description: Will add `if __name__ == "__main__"` with argparse for `--mode` (daily/deep), `--limit`, `--json-summary`. Currently runs via .bat file with no CLI interface.*

- [ ] **C.1.3:** Add structured exit codes (0/1/2)
  - *Description: Will add try/except with exit codes matching convention: 0=success, 1=partial, 2=failure.*

### C.2: Refactor run_biocrawler.bat → Python script

- [ ] **C.2.1:** Create `run_biocrawler.py` wrapper script
  - *Description: Will create a Python wrapper that replaces the .bat file. Handles venv activation, logging, and exit codes. n8n can call this directly instead of relying on Windows batch.*

- [ ] **C.2.2:** Add `--json-summary` pass-through to biocrawler.py
  - *Description: Will pass `--json-summary` flag through wrapper to biocrawler.py.*

---

## SWIP1-D: Fix Engine 01 — Schedule Library Not Resilient

### D.1: Remove schedule.py dependency — n8n will handle scheduling

- [x] **D.1.1:** Refactor nightly_scheduler.py — remove `schedule` library, make it a single-run script
  - *Completed: Completely rewritten. Removed import schedule, removed while True loop, removed schedule.every().day.at(). Script is now one-shot — n8n will call it at 2AM.*
  - *Description: Will remove the `schedule.every().day.at("02:00").do(job)` loop. Script becomes a one-shot runner. n8n calls it at 2AM. No more `while True` sleep loop needing an open terminal.*

- [x] **D.1.2:** Add `--dry-run` flag for testing without actual pipeline execution
  - *Completed: --dry-run flag shows targets, rotation state, source, and configuration without executing.*
  - *Description: Will add `--dry-run` flag that resolves targets and prints what WOULD run, but doesn't execute PubMed queries or DB writes. Enables safe testing of rotation logic.*

- [x] **D.1.3:** Add `--targets-override` flag to force specific targets (bypass BioCrawler + rotation)
  - *Completed: --targets-override flag accepts one or more targets. Also added --skip-rotation to use only BioCrawler leads and --pull-id for campaign tracking.*
  - *Description: Will add `--targets-override "Disease A" "Disease B"` that skips both BioCrawler read and rotation logic. Useful for on-demand briefs or targeted investigation.*

---

## SWIP1-E: Fix Telegram Notifier — Inconsistent Configuration

### E.1: Refactor DevOps telegram_notifier.py

- [ ] **E.1.1:** Audit all scripts importing telegram_notifier — list all callers
  - *Description: Will search entire backend for `import telegram_notifier` and document every caller. Already found in: ct_crawler.py, run_pipeline.py. May be more in other scripts.*

- [ ] **E.1.2:** Create `.env.telegram` with Meddash bot token and chat ID
  - *Description: Will create a dedicated env file for the Meddash Telegram bot (separate from CQ bot). Shared across all engines via `from dotenv import load_dotenv`.*

- [ ] **E.1.3:** Refactor telegram_notifier.py to use .env.telegram
  - *Description: Will update to load from `.env.telegram` with fallback to environment variables. Remove any hardcoded tokens or chat IDs.*

- [ ] **E.1.4:** Add message severity levels — info, success, warning, error
  - *Description: Will add emoji prefixes: ℹ️ info, ✅ success, ⚠️ warning, 🚨 error. Currently just `send_alert(text, level)` with no formatting.*

- [ ] **E.1.5:** Add structured message templates for each engine
  - *Description: Will add template functions: `send_kol_summary(counts)`, `send_ct_summary(counts)`, `send_biocrawler_summary(counts)`, `send_failure_alert(engine, error)`. Consistent formatting across all alerts.*

- [ ] **E.1.6:** Add rate limiting — no more than 1 message per 30 seconds
  - *Description: Will add a simple timestamp check to avoid Telegram API rate limits when multiple engines finish close together.*

---

## SWIP1-F: Implement MeSH Rotation (Tier 2)

### F.1: Create mesh_rotation.py module

- [x] **F.1.1:** Create `01_KOL_Data_Engine/mesh_rotation.py` with rotation schedule
  - *Completed: 12 MeSH categories with ISO week-based rotation. Functions: get_current_category(), get_rotation_target(), get_rotation_state(), save_rotation_state(), mark_category_completed(), log_rotation_result(), get_rotation_report(). CLI with --current, --state, --report, --dry-run.*
  - *Description: Will create a standalone module with MESH_ROTATION list (12 categories), `get_current_rotation()` function (ISO week-based), and `get_rotation_state()` / `save_rotation_state()` for JSON state management.*

- [x] **F.1.2:** Add `get_rotation_target(lead_targets: list) -> list` function
  - *Completed: Merges T1 (BioCrawler leads) + T2 (MeSH rotation) with dedup. Uses normalized string matching to avoid duplicating already-covered TAs.*
  - *Description: Will implement the merge logic: take BioCrawler leads + current MeSH rotation target → deduplicate → return final target list. This is the core T1+T2 merge function.*

- [x] **F.1.3:** Add rotation state tracking with `mesh_rotation_state.json`
  - *Completed: State file tracks current_week, current_category, last_run_timestamp, cycle_count, categories_completed_this_cycle, total_runs.*
  - *Description: Will create state file with: current_week, current_category, last_run_timestamp, cycle_count, categories_completed_this_cycle. Auto-created on first run.*

- [x] **F.1.4:** Add `get_rotation_report() -> dict` for health monitoring
  - *Completed: Returns categories_covered, total_kols_per_category, current_cycle, total_runs, estimated_total_12_weeks, estimated_total_36_weeks.*
  - *Description: Will return a summary dict: categories_completed, current_cycle, total_weeks_running, estimated_kol_coverage. This feeds into Meddash-Monitor reports in SWIP2.*

- [x] **F.1.5:** Add rotation metrics logging — `mesh_rotation_log.db` (SQLite)
  - *Completed: SQLite DB created in 06_Shared_Datastores/mesh_rotation_log.db with schema: rotation_log(id, timestamp, category, mesh_code, publications_found, kols_disambiguated, kols_weighted, cycle, week_number, tier1_targets, tier2_target, dedup_applied).*
  - *Description: Will create a tiny SQLite DB with table: rotation_log(id, timestamp, category, mesh_code, publications_found, kols_disambiguated, kols_weighted, cycle). Enables historical analysis of rotation effectiveness.*

### F.2: Integrate mesh_rotation.py into nightly_scheduler.py

- [ ] **F.2.1:** Import mesh_rotation module in nightly_scheduler.py
  - *Description: Will add `from mesh_rotation import get_rotation_target, get_rotation_report` to nightly_scheduler.py.*

- [ ] **F.2.2:** Replace hardcoded targets with `get_rotation_target(lead_targets)`
  - *Description: Will replace `targets = [r[0] for r in rows]` with `targets = get_rotation_target(lead_targets)` which merges T1 (BioCrawler leads) + T2 (MeSH rotation) with dedup.*

- [ ] **F.2.3:** Remove NSCLC fallback entirely
  - *Description: Will delete `targets = ["Non-Small Cell Lung Cancer"]` fallback line. If BioCrawler is empty AND rotation hasn't started, the script will log a warning and use the rotation target as sole target.*

- [ ] **F.2.4:** Test rotation logic with `--dry-run`
  - *Description: Will run `nightly_scheduler.py --dry-run` with mock week numbers to verify all 12 categories cycle correctly and dedup works.*

---

## SWIP1-G: Fix Structured Output for All Engines

### G.1: Create summary JSON convention

- [ ] **G.1.1:** Define standard summary JSON format for all engines
  - *Description: All engines will write `{engine}_summary.json` with: engine, mode, timestamp, targets, counts (input/output/disambiguated/weighted), errors, exit_code, duration_seconds. Consistent schema enables n8n parsing in SWIP2.*

- [ ] **G.1.2:** Add summary JSON to Engine 01 (KOL pipeline)
  - *Description: Will modify `run_pipeline.py` to write `kol_pipeline_summary.json` at the end of each run.*

- [ ] **G.1.3:** Add summary JSON to Engine 02 (CT Crawler)
  - *Description: Already partially done in B.1.1. Will ensure `ct_crawler.py` writes `ct_crawl_summary.json` in the standard format.*

- [ ] **G.1.4:** Add summary JSON to Engine 03 (BioCrawler)
  - *Description: Already partially done in C.1.1. Will ensure `biocrawler.py` writes `biocrawler_summary.json` in the standard format.*

- [ ] **G.1.5:** Add summary JSON to Engine 09 (Scholar Engine)
  - *Description: Will add `scholar_sync_summary.json` output to scholar engine scripts.*

---

## SWIP1-H: Database Path Fixes

### H.1: Fix hardcoded paths across all engines

- [ ] **H.1.1:** Audit all scripts for hardcoded Windows paths
  - *Description: Will search for `C:\Users\email` and `r"C:\Users` patterns. Already known in: ct_crawler.py (DevOps import), nightly_scheduler.py (biocrawler_leads.db path).*

- [x] **H.1.2:** Create shared `paths.py` config module in `07_DevOps_Observability/`
  - *Completed: Created paths.py with MEDDASH_ROOT auto-detection, DB_PATHS, ENGINE_PATHS, STATE_DIR, SUMMARY_DIR, STATE_FILES, SUMMARY_FILES. Supports both Windows and WSL. Has dotenv import fallback.*
  - *Description: Will create a central `paths.py` that defines: MEDDASH_ROOT, DB_PATHS, RAW_DIR, STATE_DIR, LOG_DIR, SUMMARY_DIR. All engines import from here. Single source of truth.*

- [ ] **H.1.3:** Replace all hardcoded paths with `paths.py` references
  - *Description: Will update nightly_scheduler.py, ct_crawler.py, biocrawler.py, and any other scripts with hardcoded paths to use `from paths import MEDDASH_ROOT, DB_PATHS` etc.*

- [ ] **H.1.4:** Test all path references resolve correctly from WSL and Windows
  - *Description: Will run each engine with `--dry-run` to verify `paths.py` resolves correctly in both WSL and Windows Python environments.*

---

## SWIP1-I: MeSH Rotation DB — Growth Tracking

### I.1: Create rotation metrics tracking

- [ ] **I.1.1:** Create `mesh_rotation_log.db` schema
  - *Description: Will create SQLite DB in `06_Shared_Datastores/` with table: rotation_log(id INTEGER PRIMARY KEY, timestamp TEXT, category TEXT, mesh_code TEXT, publications_found INTEGER, kols_disambiguated INTEGER, kols_weighted INTEGER, cycle INTEGER, week_number INTEGER).*

- [ ] **I.1.2:** Add rotation log writes to mesh_rotation.py
  - *Description: Will add `log_rotation_result(category, mesh_code, pubs, kols_disamb, kols_weighted, cycle)` function that inserts into `mesh_rotation_log.db` after each rotation run completes.*

- [ ] **I.1.3:** Add growth projection query
  - *Description: Will add `get_growth_report() -> dict` function that queries rotation_log.db and returns: total_kols_per_category, categories_covered, estimated_total_after_12_weeks, estimated_total_after_36_weeks.*

---

## SWIP1-J: Pre-Automation Validation

### J.1: End-to-end dry run of all fixes

- [ ] **J.1.1:** Run nightly_scheduler.py --dry-run with mock week 1 (Neoplasms)
  - *Description: Will verify rotation target resolves to "Neoplasms", dedup works, targets merge correctly, and summary JSON is written.*

- [ ] **J.1.2:** Run nightly_scheduler.py --dry-run with mock week 5 (Cardiovascular Diseases)
  - *Description: Will verify week index calculation and different category selection.*

- [ ] **J.1.3:** Run ct_crawler.py --mode query --query "lung cancer" --max 10 --json-summary
  - *Description: Will verify query mode works, summary JSON is written, and exit code is 0.*

- [ ] **J.1.4:** Run biocrawler.py --mode daily --json-summary
  - *Description: Will verify CLI works, summary JSON is written, and exit code is 0.*

- [ ] **J.1.5:** Verify Telegram alert formatting with test messages
  - *Description: Will send test messages via telegram_notifier.py with all 4 severity levels (info, success, warning, error) to verify formatting and rate limiting.*

- [ ] **J.1.6:** Verify mesh_rotation_state.json is created and updated correctly
  - *Description: Will run rotation logic, check state file contents, verify cycle tracking.*

- [ ] **J.1.7:** Verify mesh_rotation_log.db is populated after dry run
  - *Description: Will query the DB to confirm rotation_log table has entries with correct schema.*

- [ ] **J.1.8:** Verify paths.py resolves correctly in WSL and Windows
  - *Description: Will import paths.py from both environments and confirm MEDDASH_ROOT, DB_PATHS, etc. resolve to correct locations.*

---

*End of SWIP1. Once all checkboxes are checked, we proceed to SWIP2: n8n + Paperclip + Alfred Triarchy Automation.*