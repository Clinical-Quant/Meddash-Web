# Meddash Pipeline Backend File Paths
This document outlines the file paths and responsibilities of the individual scripts, databases, and structural components of the organized Meddash backend. It is organized into 7 distinct modules reflecting the broader funnel architecture.

## 01_KOL_Data_Engine
**Path:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\01_KOL_Data_Engine`

* `nightly_scheduler.py` - CRON job script that triggers daily pipeline execution (e.g., at 2:00 AM).
* `run_pipeline.py` - Core entry point/orchestrator for the KOL data aggregation pipeline.
* `extract_publications.py` - Responsible for extracting raw publication data from scholarly sources.
* `db_ingestion.py` - Processes and ingests the raw publication logs into the central database.
* `kol_disambiguator.py` - Executes parsing algorithms to disambiguate variations in distinct KOL profiles.
* `kol_weight.py` - Computes the Authority/Power Weight (APW) using `log(1 + sum SJR)`.
* `review_disambiguations.py` - Human-in-the-loop or LLM interface to manually verify ambiguous merges.
* `load_sjr.py` - Bulk loads the Scientific Journal Rankings (SJR) metrics into the datasets.

## 02_CT_Data_Engine
**Path:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\02_CT_Data_Engine`

* `ct_crawler.py` - Daily crawler targeting clinical trial registries to detect new or updated trials.
* `ct_ingestion.py` - Pushes initial fetched trial metadata down into the respective tables.
* `ct_mesh_mapper.py` - Normalizes conditions and interventions against MeSH term mappings.
* `ct_kol_bridge.py` - The integral bridge connecting investigators in trials to the main KOL profiles.
* `ct_results_parser.py` - Extracts outcomes and adverse event insights from completed trial histories.
* `ct_pub_bridge.py` - Connects CT studies to corresponding academic publications.
* `ct_eligibility_parser.py` - Translates inclusion/exclusion criteria blocks for targeted querying.

## 03_BioCrawler_GTM
**Path:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\03_BioCrawler_GTM`

* `run_biocrawler.bat` - Execution script governing the BioCrawler runs (e.g., Daily Cron at 5:00 PM).
* `biocrawler.py` - Gathers intel and updates tracking on external startup networks / leads.
* `bridge_engine.py` - Acting as "The Synapse Layer," tying lead intelligence back into SVS metrics and KOL targets.
* `run_pull_from_sheets_daily.bat` - Trigger for pulling offline updates from Google Sheets.
* `push_to_sheets.py` - Pushes extracted leads (e.g., top 20 prospects) over to CRM V1.0 (Google Sheets).
* `pull_from_sheets.py` - Merges manually updated URLs and status tags back into the database.

## 04_Product_KOL_Briefs
**Path:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\04_Product_KOL_Briefs`

* `generate_kol_brief.py` - Consolidates CT and KOL dataset inputs internally to generate a complete intelligence brief.
* `export_kols.py` - Utility to filter and export distinct batches of curated KOL intelligence.

## 05_Product_TA_Landscape
**Path:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\05_Product_TA_Landscape`

* `fetch_ta_landscape_data.py` - Collects high-level queries spanning Biocrawler metrics, clinical trials, and publications for a Therapeutic Area (TA).
* `generate_ta_landscape_stepwise.py` - Aggregates the gathered intelligence to produce sequential and structural landscape reports.
* `ta_landscape_cache/` - Local file cache repository capturing interim report states during generation.

## 06_Shared_Datastores
**Path:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\06_Shared_Datastores`

* `meddash_kols.db` - The core SQLite hub storing integrated KOL profiles and historical journal metrics.
* `ct_trials.db` - Isolated context containing normalized clinical trials structure and associations.
* `biocrawler_leads.db` - Datastore monitoring prospective targets and company insights.
* `kol_merge_candidates/` - Transient holding records pending deduplication approvals.
* `csv_exports/` - Active directory capturing static snapshots of outbound data payload iterations.

## 07_DevOps_Observability
**Path:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\07_DevOps_Observability`

* `telegram_notifier.py` - Pushes alert flags across messaging platforms upon errors or task completions.
* `backup_antigravity.ps1` - Routine backup script shielding against critical database or codebase corruption.
* `patch_paths.py` - Utility for globally aligning the dependency architecture references.
* `logs/` - Log sinks retaining step execution diagnostics.
