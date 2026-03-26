# Meddash Pipeline Mapping
This document is based on the comprehensive ecosystem map, detailing data sources, APIs, ML models, and hierarchy.

## 1. KOL Data Engine (`01_KOL_Data_Engine`)
*   **Run Node**: Meddash Backend Run Node (Victus 16)
*   **Trigger**: `nightly_scheduler.py` (Daily Cron: 2:00 AM)
*   **Pipeline Orchestrator**: `run_pipeline.py`
    1.  Calls `extract_publications.py` (NCBI E-utilities API for PubMed XML + ORCID extraction).
    2.  `db_ingestion.py` performs ORCID-first KOL lookup and SQL upsert into `meddash_kols.db`.
    3.  `kol_disambiguator.py` runs a 4-signal scoring engine and writes scored sets to `kol_merge_candidates`.
    4.  `kol_weight.py` recomputes weights (APW = log(1+sum SJR)), joining via ISSN from `journal_metrics` DB.
*   **LLM Interventions**:
    *   `review_disambiguations.py` leverages **Gemini Flash API** for bibliographic advisor review, yielding APPROVE/REJECT/SKIP actions into `meddash_kols.db`.

## 2. CT Engine (`02_CT_Data_Engine`)
*   **Workflow Integration**: Scrapes trials and maps them structurally to products.
*   **Processors**:
    *   *Step 2*: `ct_crawler.py` (ClinicalTrials.gov API v2 crawl).
    *   *Step 3*: `ct_ingestion.py` (JSON → 11 tables in `ct_trials.db`).
    *   *Step 4*: `ct_mesh_mapper.py` (condition → MeSH). Uses **Gemini Flash API** (`--gemini` flag) to resolve terms into the condition_mesh_map cache.
    *   *Step 5*: `ct_kol_bridge.py` (investigator ↔ KOL). Reads KOLs/MeSH from `meddash_kols.db` and writes FKs to `ct_trials.db`.
    *   *Step 6*: `ct_results_parser.py` (outcomes + AEs).
    *   *Step 7*: `ct_pub_bridge.py` (PMID × KOL pubs).
    *   *Step 8*: `ct_eligibility_parser.py` (biomarkers + stage). Uses **Gemini Flash API** (`--gemini` flag) to parse unstructured text.
    *   *Step 9*: `generate_kol_brief.py` consolidates signals leading to formal phase 1 KOL Brief outputs.

## 3. BioCrawler GTM (`03_BioCrawler_GTM`)
*   **Run Node**: CMO Run Node (Victus 16)
*   **Trigger**: `run_biocrawler.bat` (Daily Cron: 5:00 PM)
*   **Processors**:
    *   `biocrawler.py` (API Mode): Touches ClinicalTrials API via C-Tree MeSH Filters.
    *   `biocrawler.py` (Deep Mode): Hits Clearbit, SEC EDGAR, ATS job boards for deeper enrichment.
*   **Data Destination**: Idempotent upserts to `biocrawler_leads.db` (Relationship Graph DB).
*   **Synapse Layer**: `bridge_engine.py` calculates real-time SVS, maps advisory boards, and feeds signals to the SaaS pipeline.

## 4. CRM Integration (`marketing_agent`)
*   **Trigger**: `run_pull_from_sheets_daily.bat` (Daily Cron: 4:00 PM)
*   **Processors**:
    *   `push_to_sheets.py` Extracts 20 daily leads from `biocrawler_leads.db` and appends to Google Sheets.
    *   `pull_from_sheets.py` Reads manual URLs in Google Sheets to Reverse Sync into `biocrawler_leads.db`.

## 5. Product 2: TA Landscape Pipeline
*   **Processors**:
    *   `fetch_ta_landscape_data.py`: Batch API Fetcher across PubMed, CT DB, KOL DB, and BioCrawler DB to build a JSON Cache.
    *   `generate_ta_landscape_stepwise.py`: Stepwise Generation Engine leveraging **Gemini 2.5 Pro API** (Consulting Voice) + Human-in-the-loop review.
*   **Outputs**: `TA_Landscape_Report.md` & `References_Audit.md`
