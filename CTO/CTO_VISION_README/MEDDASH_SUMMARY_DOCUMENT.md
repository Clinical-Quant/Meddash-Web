# Meddash V2.0 - Platform Architecture & Capabilities Summary

*Confidential & Proprietary - Prepared for Open Claw Marketing & GTM Strategy*

---

## Executive Summary
Meddash is a next-generation Medical Intelligence and Key Opinion Leader (KOL) discovery platform. It leverages automated, deterministic web crawlers, real-time public API consumption, AI-driven disambiguation algorithms, and a native PostgreSQL cloud architecture to instantly map, rank, and contextualize global medical expertise. By dynamically bridging clinical trial registries with academic literature, Meddash delivers unparalleled, data-backed insights for life science commercialization arrays, investor targeting, and Medical Affairs workflows.

---

## 1. What We Have Built (Current Capabilities)

The platform currently operates as a highly robust, multi-engine backend microservice architecture connected to a secure cloud database. It executes complex, scalable, entity-resolved extractions against billions of global health records.

### Core Data Engines:
1. **The KOL Data Engine (Academic Authority):** Systematically extracts peer-reviewed literature and identifies the authors (KOLs) driving the science. It calculates an algorithmic "Author Publication Weight" relative to the journal's SCImago ranking (SJR), allowing accurate tiering of experts based on raw scientific impact over time.
2. **The Scholar Engine (Citation Metrics):** Automatically syncs with Google Scholar to extract long-term citation h-indexes. Features a proprietary 4-Tier Disambiguation layer (ORCID, Publication Cross-mapping, Institution/Specialty Fuzzy Matching, Human-in-the-Loop review) to guarantee 100% accurate attribution.
3. **The Clinical Trials Engine (Investigational Leadership):** Maps Principal Investigators and trial sponsors to interventional success. Extracts eligibility criteria, MeSH conditions, phase statuses, and adverse event profiles directly from active registries.
4. **The BioCrawler GTM Engine (Corporate Intelligence):** Analyzes SEC EDGAR filings, Clearbit firmographics, and ATS job boards to detect corporate catalysts (e.g., funding rounds, executive hiring signals) to predict B2B sales cycles or M&A opportunities perfectly timed for outreach.
5. **The MDM Ontology Engine:** An autonomous Medical Data Management script that seamlessly pulls from the NIH Unified Medical Language System (UMLS) APIs, maintaining a fresh, universally standardized dictionary of diseases, drug targets, and anatomical contexts to act as the linguistic backbone of the entire Meddash system.

### Functional Infrastructure:
- **Campaign Sandbox (Client Deliverable Orchestration):** A secure, virtualized staging area for raw crawler data. Allows internal operators to run custom, multi-disease scrapes per client (`Pull ID`s), deduplicate and review the candidate lists, export `.csv` reports, and finally "commit" verified data safely to the global production database without contaminating historical records.
- **FastAPI Bridge Server:** A high-speed API layer exposing the Python backend execution controllers and PostgreSQL data tables natively to modern frontends.

---

## 2. Our Data Sources (The Intelligence Feeds)

Meddash does not rely on static, purchased lists. It dynamically synthesizes intelligence from real-time global, primary sources:

*   **PubMed (NCBI E-Utilities API):** Direct access to >35 million biomedical citations. Feeds the literature base, author metadata, abstract ingestion, and MeSH keyword associations.
*   **ClinicalTrials.gov (API v2):** Daily consumption of >480,000 global clinical studies structurally parsing sponsor data, clinical endpoints, phase progressions, and geographical facility networks.
*   **Google Scholar (SerpApi Enterprise Sync):** Provides the gold standard in academic h-index influence metrics and total citation acceleration over time.
*   **NIH UMLS Terminology Services:** Pulls globally recognized SNOMED CT and MeSH ontologies ensuring every disease processed maps accurately to universally recognized clinical vocabularies.
*   **SCImago Journal Rank (SJR):** Integrates mathematical weighting values reflecting the prestige of journals where publications occurred, ensuring a publication in *The Lancet* vastly outscores a local, non-indexed journal.
*   **Clearbit & SEC EDGAR:** Extracts real-time firmographic funding and catalyst signals on emerging biotech and pharma companies.

---

## 3. Our Cloud Database Architecture (Supabase / PostgreSQL)

Meddash completely transitioned from localized SQLite prototypes into a highly scalable **Supabase PostgreSQL Cloud Model**, architected for speed, relational integrity, and cross-engine foreign key mapping.

**The Multi-Schema PostGres Array:**
1.  **`kols` (The Global Brain):** The unified directory of every expert discovered. Stores names, degrees, verified institutions, ORCID iDs, and aggregate weighting scores. Overlapping campaign associations are tracked dynamically via natively queryable CSV arrays (`"001,002,005"`).
2.  **`kols_staging` (The Sandbox):** An exact isolation clone of the main table. Holds raw, highly-volatile crawler outcomes for human-in-the-loop (HITL) cleaning and deduping entirely separated from production read workflows.
3.  **Cross-Mapping Tables (`kol_authorships`, `publication_mesh_map`):** Highly optimized bridging tables linking KOLs to their distinct publications, and linking publications to their precise disease contexts using strict relational constraints and cascading indexers.
4.  **`kol_scholar_metrics` & `scholar_review_queue`:** Distinct partitions to independently sync long-running API tasks like Google Scholar citations without blocking the main website traffic.
5.  **`ct_trials` & `biotech_leads`:** Permanent storage for tracked interventional studies and corporate B2B sales leads.

---

## 4. What We Can Build Next (The SaaS Horizon)

With the backend data layer and AI deduplication routing fully hardened, Meddash is perfectly positioned for explosive SaaS commercialization.

1.  **Fully Automated Client Dashboards:** Transition the internal "Campaign Sandbox" into client-facing portals. External users (pharma reps, recruiters, investors) can log in, select a disease target, hit "Generate," and immediately receive beautiful, data-verified dashboard analytics covering the top 50 KOLs in that space within minutes, rather than weeks of manual consultancy work.
2.  **Predictive Trial Forecasting AI:** Leverage the `ct_trials` and `publications` bridges to train LLMs (Gemini / Deepseek) to detect hidden correlations (e.g., KOLs whose early publications correctly predict successful Phase 2 trial outcomes 5 years later), generating a proprietary "Success Probability Score" for emerging research.
3.  **Real-Time Outreach Alerts:** Connect the `biotech_leads` table to automated CRM triggers tracking funding rounds or C-Suite executive changes parsed by the Biocrawler, automatically generating highly personalized email outreach copy (via Gemini Flash) tailored to the prospect's real-time events.
4.  **Global Geographical Explorer Map:** Convert the static data tables into interactive, WebGL-rendered global heatmaps showcasing clinical site density, investigator clusters, and institutional trial output by region at a glance.
5.  **Natural Language "Chat with the Data":** Implement a conversational RAG (Retrieval-Augmented Generation) agent directly into the Meddash app, allowing executives to ask questions like: *"Show me the top 10 Thoracic Oncologists in Boston who have published on EGFR mutations in the last 2 years and currently oversee a Phase 3 recruiting trial,"* returning instantaneous, structured UI responses.
