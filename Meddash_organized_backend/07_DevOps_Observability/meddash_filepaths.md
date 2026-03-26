# Meddash Global Architecture & Filepaths Map

**Attention AI Agents:** This file serves as your master navigation map perfectly detailing the Meddash architecture. Use these absolute paths to locate databases, execution scripts, and strategic planning documents so you do not search blindly.

## ⚠️ Agent — Read This First
*   **Agent Standing Rules:** `C:\Users\email\.gemini\antigravity\scratch\meddash\AGENT_RULES.md` ← **READ THIS BEFORE ANY CHANGE.** Mandatory protocol for decision log updates, filepath changes, and Mermaid diagram updates.

## Core Meddash Backend Pipeline
*   **Workspace:** `C:\Users\email\.gemini\antigravity\scratch\meddash`
*   **Master KOL Database:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\06_Shared_Datastores\meddash_kols.db`
*   **Central Pipeline Engine:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\01_KOL_Data_Engine\run_pipeline.py`
*   **NCBI Extraction Script:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\01_KOL_Data_Engine\extract_publications.py`
*   **Database Ingestion Engine:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\01_KOL_Data_Engine\db_ingestion.py`
*   **KOL Publication Weight Calculator:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\01_KOL_Data_Engine\kol_weight.py` (Computes APW = log(1 + sum of SJR scores) for every KOL nightly)
*   **KOL Disambiguation Engine:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\01_KOL_Data_Engine\kol_disambiguator.py` (4-signal weighted scoring: co-author 0.40 + MeSH 0.30 + name 0.25 + temporal 0.05; ORCID trump; outputs to `kol_merge_candidates` table for human review)
*   **Disambiguation Review CLI:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\01_KOL_Data_Engine\review_disambiguations.py` (v2.0 — interactive terminal reviewer with Gemini Flash AI recommendations per candidate. Run after nightly pipeline: `a`=approve, `r`=reject, `s`=skip, `q`=quit. Requires `GEMINI_API_KEY` env var.)
*   **Decision Log:** `C:\Users\email\.gemini\antigravity\scratch\meddash\meddash_decision_log.md` (Permanent timestamped record of all architectural/algorithmic decisions made during the build — weight rationale, algorithm design, LLM integration choices, live results.)
*   **SCImago SJR Journal Importer:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\01_KOL_Data_Engine\load_sjr.py` (Imports ~31k journals from sjr_raw.csv into journal_metrics table)
*   **SCImago Raw Data File:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\06_Shared_Datastores\csv_exports\sjr_raw.csv` (Annual refresh: re-download from scimagojr.com/journalrank.php)
*   **SVS Calculation & Exporter:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\04_Product_KOL_Briefs\export_kols.py`
*   **Nightly Cron Scheduler:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\01_KOL_Data_Engine\nightly_scheduler.py`
*   **Schema Map:** `C:\Users\email\.gemini\antigravity\scratch\meddash\meddash_mesh_schema_v2.0.sql`
*   **Mermaid Workflow Schema (All 4 Diagrams):** `C:\Users\email\.gemini\antigravity\scratch\meddash\txt_files\meddash_workflow_schema.txt` (Plain text file — paste any diagram into mermaid.live to visualize)

## Organized File Subfolders
*   **CSV Exports:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\06_Shared_Datastores\csv_exports\` (KOL Exports, SJR Raw Data)
*   **Logs:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\07_DevOps_Observability\logs\` (All pipeline and crawler logs)
*   **Text Files:** `C:\Users\email\.gemini\antigravity\scratch\meddash\txt_files\` (Workflow schemas, output files)

## Marketing & Lead Generation Pipeline (BioCrawler)
*   **Workspace:** `C:\Users\email\.gemini\antigravity\scratch\biocrawler_marketing`
*   **Crawler Database (Biotechs & Relationships):** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\06_Shared_Datastores\biocrawler_leads.db`
*   **Server Execution Logic:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\03_BioCrawler_GTM\biocrawler.py`
*   **BioCrawler Cron Job / Task Scheduler Wrapper:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\03_BioCrawler_GTM\run_biocrawler.bat`
*   **Sales Bridge Engine (KOL to Biotech):** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\03_BioCrawler_GTM\bridge_engine.py`
*   **Marketing Schema Documentation:** `C:\Users\email\.gemini\antigravity\scratch\biocrawler_marketing\database_schema_design.md`
*   **Go-To-Market Strategy:** `C:\Users\email\.gemini\antigravity\scratch\biocrawler_marketing\go_to_market_strategy.md`

## CRM Integration & Sync Scripts
*   **Workspace:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\03_BioCrawler_GTM`
*   **Push to Google Sheets:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\03_BioCrawler_GTM\push_to_sheets.py` (Appends new BioCrawler leads to the live CRM)
*   **Pull from Google Sheets:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\03_BioCrawler_GTM\pull_from_sheets.py` (Two-way reverse sync for manual website additions)
*   **Automated Reverse Sync (Cron):** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\03_BioCrawler_GTM\run_pull_from_sheets_daily.bat` (Executes the pull from sheets script. Scheduled via Windows Task Scheduler at 4:00 PM daily).
*   **Manual URL Ingestion:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\03_BioCrawler_GTM\manual_url_ingest.py` (Bypasses crawler to securely push ad-hoc URLs to DB)
*   **Marketing Manager Log:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\03_BioCrawler_GTM\marketing_log.md`

## Content Generation & Social Positioning (MBD_content_agent)
*   **Workspace:** `C:\Users\email\.gemini\antigravity\scratch\MBD_content_agent`
*   **Content Agent Directive:** `C:\Users\email\.gemini\antigravity\scratch\MBD_content_agent\README.md` (Instructs AI on generating high-credibility LinkedIn content for the "Clinical Simplified" series)

## Tech Liaison & DevOps
*   **Workspace:** `C:\Users\email\.gemini\antigravity\scratch\tech_liaison`
*   **Data Structure Rules:** `C:\Users\email\.gemini\antigravity\scratch\tech_liaison\meddash_highlevel_schema.md`
*   **KOL/Biotech Merge Ideas:** `C:\Users\email\.gemini\antigravity\scratch\tech_liaison\KOL_BIOTECH_merge_for_CQ.md`
*   **Automated Ecosystem Backup Script:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\07_DevOps_Observability\backup_antigravity.ps1` (Zips entire environment and drops it in Google Drive daily)
*   **Telegram Notification Module:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\07_DevOps_Observability\telegram_notifier.py` (Core reusable alert hub — call `send_alert()` from any script to push real-time updates to phone)
*   **Novita API Models Manifest:** `C:\Users\email\.gemini\antigravity\scratch\meddash\NOVITA_API_MODELS\MODEL_TYPES.MD` (Manifest of available models and instructions for MCP bridge routing)


## Shared Network Drives
*   **Victus-Lenovo Bridge:** `C:\Users\email\victus_CQCrawler` (Local shared folder acting as a bridge for file transfers between the Victus host and remote Lenovo machine)

## ClinicalTrials.gov Intelligence Engine (CT Engine — all 9 steps complete)
*   **CT Database:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\06_Shared_Datastores\ct_trials.db` (11 tables, 31 indexes)
*   **CT Schema DDL:** `C:\Users\email\.gemini\antigravity\scratch\meddash\ct_schema.sql`
*   **CT DB Initializer:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\02_CT_Data_Engine\ct_initializer.py`
*   **Step 2 — CT Crawler:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\02_CT_Data_Engine\ct_crawler.py` (API v2; full/delta/query modes; crash-safe via `ct_crawl_state.json`; saves to `ct_raw_json/`)
*   **Step 3 — CT Ingestion:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\02_CT_Data_Engine\ct_ingestion.py` (JSON→all 11 tables; batch commits; privacy-safe)
*   **Step 4 — CT MeSH Mapper:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\02_CT_Data_Engine\ct_mesh_mapper.py` (NLM API + optional Qwen 2.5 7B via `--qwen`; caches to `condition_mesh_map`)
*   **Step 5 — KOL Bridge:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\02_CT_Data_Engine\ct_kol_bridge.py` (3-signal probabilistic match: name 40% + institution 35% + MeSH 25%; logs to `ct_bridge_review.tsv`)
*   **Step 6 — Results Parser:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\02_CT_Data_Engine\ct_results_parser.py` (outcome values, p-values, AE counts, why_stopped classification)
*   **Step 7 — Publication Bridge:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\02_CT_Data_Engine\ct_pub_bridge.py` (PMID cross-reference; SJR enrichment; high_evidence flag)
*   **Step 8 — Eligibility Parser:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\02_CT_Data_Engine\ct_eligibility_parser.py` (50+ biomarker/stage/prior-tx regex; Qwen 2.5 7B fallback via `--qwen`)
*   **Step 9 — KOL Brief Generator:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\04_Product_KOL_Briefs\generate_kol_brief.py` (Phase 1 product: Markdown + JSON brief output to `kol_briefs/`)
*   **CT Raw JSON Store:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\02_CT_Data_Engine\ct_raw_json\` (one file per trial: `{nct_id}.json`)
*   **KOL Bridge Review Queue:** `C:\Users\email\.gemini\antigravity\scratch\meddash\ct_bridge_review.tsv` (human review candidates, score 0.45–0.69)
*   **Sample Brief Output:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\04_Product_KOL_Briefs\kol_briefs\kol_brief_kras_g12c_lung_cancer.md`

## Product 2: TA Landscape Intelligence Pipeline (Semi-HIL Brief)
*   **Workspace:** `C:\Users\email\.gemini\antigravity\scratch\meddash`
*   **TA Pre-computation Data Fetcher:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\05_Product_TA_Landscape\fetch_ta_landscape_data.py` (Product 2 - Executes the single up-front API fetch strategy across ClinicalTrials.gov, PubMed, NCCN, and internal databases `ct_trials.db`, `meddash_kols.db`, `biocrawler.db`. Created: 2026-03-12. Caches data to JSON/SQLite.)
*   **Stepwise Generation Engine:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\05_Product_TA_Landscape\generate_ta_landscape_stepwise.py` (Product 2 - Core Stepwise Generation Engine. Runs section-by-section based on the Style Guide, pausing for human-in-the-loop review, and outputs the parallel References Audit. Created: 2026-03-12.)

## AI Agent Directives
1.  **Do not duplicate databases:** If an agent needs access to KOL data, connect to the exact `.db` paths listed above using `sqlite3`.
2.  **Respect Workspace Boundaries:** The BioCrawler agent must not modify the core `meddash` backend scripts, and vice-versa.
3.  **Use Absolute Paths:** Never use relative paths when reading files across the architecture. Always use the paths outlined in this document.
4.  **Maintain the Map:** Whenever an AI agent creates a new architectural file, database, or script, they MUST add its absolute path and a short description to this `meddash_filepaths.md` document for reference.
