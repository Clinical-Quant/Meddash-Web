# Meddash Backend Reorganization Plan

## The Challenge
Currently, scripts are mixed in the `scratch/meddash`, `scratch/biocrawler_marketing`, and `marketing_agent` folders. Because databases like `meddash_kols.db` and `biocrawler_leads.db` heavily cross-pollinate (e.g., via `bridge_engine.py`), organizing *strictly* by database creates friction. 

## The Solution: Domain-Driven AI Workspaces (7 Folders)
To make this ideal for a single-owner SaaS and scalable for dedicated AI Agents, we should split the architecture into **Operational Pipelines** (data ingestion), **Product Workflows** (AI generation/output), and a **Shared Central Core**. 

The new backend structure under `C:\Users\email\.gemini\antigravity\Meddash_organized_backend` will consist of the following 7 agent workspaces:

### 1. `01_KOL_Data_Engine` (Data Engineer Agent Workspace)
**Purpose:** Purely operational intelligence gathering for KOL data.
**Cron:** 2:00 AM Nightly
- `nightly_scheduler.py`
- `run_pipeline.py`
- `extract_publications.py`
- `db_ingestion.py`
- `kol_disambiguator.py` & `kol_weight.py`
- `review_disambiguations.py`
- `load_sjr.py`

### 2. `02_CT_Data_Engine` (Clinical Data Agent Workspace)
**Purpose:** Multi-step pipeline for crawling and parsing ClinicalTrials.gov.
- `ct_initializer.py`
- `ct_crawler.py` & `ct_ingestion.py`
- `ct_mesh_mapper.py` & `ct_kol_bridge.py`
- `ct_results_parser.py`, `ct_pub_bridge.py`, `ct_eligibility_parser.py`

### 3. `03_BioCrawler_GTM` (Marketing/SDR Agent Workspace)
**Purpose:** Go-to-Market workflow. Connects lead gen with CRM sync.
**Cron:** 4:00 PM & 5:00 PM Daily
- `run_biocrawler.bat` & `biocrawler.py`
- `bridge_engine.py` (Synapse layer connecting KOL data to Leads data for SDR outreach)
- `run_pull_from_sheets_daily.bat`
- `push_to_sheets.py`, `pull_from_sheets.py`, `manual_url_ingest.py`

### 4. `04_Product_KOL_Briefs` (Product 1 Agent Workspace)
**Purpose:** Downstream product output generation using parsed data.
**Action required:** Move the existing `C:\Users\email\.gemini\antigravity\CTO\KOL_BRIEF_PRODUCT_1` intact here.
- `generate_kol_brief.py`
- `export_kols.py` (for SVS exports)
- The existing `/kol_briefs` output folder

### 5. `05_Product_TA_Landscape` (Product 2 Agent Workspace)
**Purpose:** Semi-automated, Human-in-the-Loop AI content generation. 
- `fetch_ta_landscape_data.py`
- `generate_ta_landscape_stepwise.py`
- The `ta_landscape_cache/`
- Output md reports and audits

### 6. `06_Shared_Datastores` (Universal Read/Write Space)
**Purpose:** Prevent locking and permission issues across pipelines. By keeping DBs central, any Agent can access them without messing with another agent's dedicated folder. 
- `meddash_kols.db`
- `ct_trials.db`
- `biocrawler_leads.db`
- `csv_exports/` and other shared flat files

### 7. `07_DevOps_Observability` (Tech Liaison Agent / CTO Workspace)
**Purpose:** Telemetry, global alerts, and environment management.
- `telegram_notifier.py`
- `backup_antigravity.ps1`
- Logs directory
- The Master Filepaths map 
- The Phase 2 SaaS setup files (remains in CTO/building_meddash_saas for now)

## Next Steps for Approval
1. Review the 7 proposed workspaces above.
2. If this aligns with your vision for simplicity and expandability, give me the green light (with any tweaks you want) and I will execute the script migrations, update the `meddash_filepaths.md`, and resolve all import paths.
