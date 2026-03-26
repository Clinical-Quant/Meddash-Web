# Meddash Pipeline Backend File Paths (Version 2.0)
This document outlines the file paths and responsibilities of the strictly finalized Version 1.0 backend scripts, databases, and LLM interventions, orienting them towards the Phase 2 UI unification.

## 01_KOL_Data_Engine
**Path:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\01_KOL_Data_Engine`

*   `nightly_scheduler.py` - Daily Cron (2:00 AM) orchestrating the master KOL run pipeline.
*   `run_pipeline.py` - Core orchestrator initializing extraction, DB ingestion, and disambiguation limits.
*   `extract_publications.py` - NCBI E-utilities extraction (+ ORCID extraction).
*   `db_ingestion.py` - ORCID-first KOL lookup and native SQLite upsert into `meddash_kols.db`.
*   `kol_disambiguator.py` - 4-signal scoring engine tracking candidate pairs and threshold filtering.
*   `kol_weight.py` - Recomputes structural weights computing `APW = log(1+sum SJR)`.
*   `review_disambiguations.py` - Deduplication queue resolution leveraging an integrated **Gemini Flash** (Bibliographic Advisor) Review.
*   `load_sjr.py` - Fetches and loads SCImago journal metrics locally.

## 02_CT_Data_Engine
**Path:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\02_CT_Data_Engine`

*   `ct_crawler.py` - (Step 2) API v2 crawl tracking ClinicalTrials.gov endpoints.
*   `ct_ingestion.py` - (Step 3) Downstream data converter isolating JSON blocks into 11 discrete tables.
*   `ct_mesh_mapper.py` - (Step 4) condition → MeSH term normalization strictly backed by **Gemini Flash API** (`--gemini`).
*   `ct_kol_bridge.py` - (Step 5) The junction mapping Principal Investigators (PI roles) to the Meddash KOL profiles.
*   `ct_results_parser.py` - (Step 6) Extracts complex analytical outcomes and Phase outcomes.
*   `ct_pub_bridge.py` - (Step 7) Intersects trial PMIDs with the KOL publication signals.
*   `ct_eligibility_parser.py` - (Step 8) Converts loose raw string blocks into structured Stage/Biomarker queries utilizing **Gemini Flash API** (`--gemini`).

## 03_BioCrawler_GTM
**Path:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\03_BioCrawler_GTM`

*   `run_biocrawler.bat` - Windows execution script (Daily Cron: 5:00 PM) triggering the BioCrawler Engine on tracking environments.
*   `biocrawler.py` - Dual-node engine aggregating external corporate intelligence via Mode: API (ClinicalTrials subsets) & Mode: Deep (Clearbit/SEC EDGAR/ATS).
*   `bridge_engine.py` - The integral Synapse Layer mathematically calculating Real-time SVS models and Mapping Advisory Board networks into the Modular SaaS Phase 2 models.
*   `push_to_sheets.py` - Marketing-Agent syncing (Daily Cron: 4:00 PM) exporting validated subsets limits (Top 20 Leads) directly to localized Google Sheets.
*   `pull_from_sheets.py` - Reverse synchronization hook ingesting marketing manual URL overrides back into the base DB.

## 04_Product_KOL_Briefs
**Path:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\04_Product_KOL_Briefs`

*   `generate_kol_brief.py` - (Step 9 of CT Engine Pathway) Capstone generative algorithm executing Phase 1 deliverables that map Trial Aggregates against Live Publication Signals.
*   `export_kols.py` - Standard formatting utility filtering and preparing isolated subset logs.

## 05_Product_TA_Landscape
**Path:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\05_Product_TA_Landscape`

*   `fetch_ta_landscape_data.py` - Extensive Batch Data Fetcher simultaneously crossing PubMed nodes, CT DB logic, KOL datasets, and BioCrawler outputs.
*   `generate_ta_landscape_stepwise.py` - Stepwise analytical generation mechanism exclusively utilizing **Gemini 2.5 Pro API** formulated with Consulting Voice boundaries natively supporting Human-in-the-Loop review loops.
*   `ta_landscape_cache/` - Isolated JSON/SQLite sub-folders locally caching massive responses to offset redundant pipeline polling costs.

## 06_Shared_Datastores
**Path:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\06_Shared_Datastores`

*   `meddash_kols.db` - The absolute Core Intelligence Database serving backend analytics on rankings and expert taxonomy.
*   `ct_trials.db` - Segmented 11-table database architecture dedicated to normalized clinical schemas.
*   `biocrawler_leads.db` - Relationship Graph Data tracking Catalyst signals for the `bridge_engine.py` processing layers.
*   `journal_metrics.db` - Central instance connecting scientific rankings (`load_sjr.py`).
*   `kol_merge_candidates/` - Sub-directory isolating temporary JSON sets tracking Human and LLM deduplication queues.

## 08_MDM_Ontology_Engine
**Path:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\08_MDM_Ontology_Engine`

## 09_Scholar_Engine
**Path:** `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\09_Scholar_Engine`

*   `sync_scholar_citations.py` - Core engine: 4-tier KOL identity disambiguation (ORCID → Publications → Institution+Specialty → Manual Queue) followed by SerpApi citation upsert.
*   `migrate_scholar.py` - Provisions the `kol_scholar_metrics` PostgreSQL table in Supabase.
*   `migrate_review_queue.py` - Provisions the `scholar_review_queue` PostgreSQL table in Supabase.
*   `kol_scholar_metrics_schema.sql` - SQL reference for the KOL Scholar Metrics table.
*   `scholar_review_queue_schema.sql` - SQL reference for the Manual Review Queue table.
*   `Scholar_Engine_Plan.md` - Full architecture spec, SerpApi pricing, and disambiguation tier logic.

