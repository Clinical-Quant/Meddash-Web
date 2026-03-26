# Implementing Organized Meddash Backend (Version 2.0)

**Vision Statement:**
Version 2.0 represents the critical evolution of Meddash. While Version 1.0 successfully segmented our data engines (KOL, CT, BioCrawler, etc.) into robust, domain-driven standalone scripts, **Version 2.0 is unifying the built Meddash backends and file systems with a centralized Front-End UI**. 

This UI is designed specifically for services implementation, providing user quick access and streamlined maintenance as the operational hub for our Medical Affairs and Biotech SaaS offerings.

## Key Upgrades & Resilience Implementation (v2.0)

To support a live SaaS dashboard where human users and scheduled cron-jobs interact with the ecosystem simultaneously, the following architectural upgrades are mandated in the v2.0 lifecycle:

### 1. Resilience & Exponential Backoffs
As the UI pulls real-time data, our outbound crawlers (reaching NCBI, ClinicalTrials.gov, and BioCrawler targets) must not stall the pipeline when encountering API rate-limits or timeouts. 
- **Implementation Plan**: Every external crawler script will wrap HTTP requests in an exponential backoff retry mechanism (e.g., Python's `tenacity` library). This guarantees that network degradation does not interrupt the automated nightly data synthesis.

### 2. Automated Regression Testing (CI/CD)
The backend features highly sensitive and complex ranking algorithms (such as the APW calculations from SJR metrics in `kol_weight.py` and the 4-signal deduplication scoring threshold in `kol_disambiguator.py`).
- **Implementation Plan**: A formal `pytest` suite will be scaffolded. Any future logic changes must pass automated mathematical testing to ensure that the Scientific Value Score (SVS) and KOL ranking integrity are never inadvertently broken.

### 3. Transitioning to PostgreSQL (Phase 2 SaaS Roadmap)
- *Note: This requirement has been formally logged in the `ideation_meddash` strategy documents.* The transition from decentralized SQLite databases (which suffer from concurrency locking) to a unified PostgreSQL cluster is scheduled to eliminate `database is locked` errors once UI traffic scales.

## Path Forward
The architecture mapped in `meddash_backend_workflow_final_version1.0_2026-03-20.txt` serves as our read-only Ground Truth. Utilizing this schema, we will now proceed to instantiate the Next.js + FastAPI bridging layer intended for Version 2.0.
