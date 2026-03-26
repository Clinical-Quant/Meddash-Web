# Meddash Disease Criteria Database (Ontology Engine)

## Strategic Brief & CTO Advisory

### 1. Architecture: Separate DB vs KOL tables?
**Recommendation: Separate PostgreSQL Database (`disease_criteria`)**
Integrating global medical ontologies (MeSH, ICD-10, SNOMED) into the `kol.db` is an architectural anti-pattern. These are universal data standards, not KOL-specific attributes. By deploying them into an isolated `disease_criteria` PostgreSQL database, we create a "Master Data Management" (MDM) layer. This allows the KOL engine, Clinical Trials engine, and BioCrawler to all securely reference the exact same truth without polluting their own schemas. 

### 2. Data Sourcing: APIs vs Crawling?
**Recommendation: Official Bulk API Downloads (NIH UMLS)**
You cannot reliably "crawl" these standards via web scraping. SNOMED CT alone contains over 300,000 highly structured relationships.
- **MeSH:** Managed by the National Library of Medicine (NLM). 
- **ICD-10:** Managed by CDC/WHO.
- **SNOMED CT:** Requires a free US/UK affiliate license via the NIH. 
*Conclusion:* We will use the NIH **UMLS (Unified Medical Language System) API**, which beautifully cross-maps MeSH <-> ICD <-> SNOMED automatically. We will build a dedicated Python engine to periodically sync these datasets natively into your database.

### 3. Commercial Viability: Selling as a Standalone API?
**Recommendation: HIGHLY LUCRATIVE (DaaS - Data as a Service)**
The problem of "Clinical Cross-Walking" (translating a doctor's SNOMED note into an ICD-10 billing code, or mapping it to a ClinicalTrials API MeSH term) is a massive, expensive problem for HealthTech startups, EHR systems, and CROs. If you expose your `disease_criteria` DB via a secure API endpoint, it can be immediately monetized as a B2B SaaS product independently of the core Meddash platform.

---

## Technical Execution Sequence

### Phase 1: Database Provisioning & Schema (COMPLETED)
- [x] Create the `disease_criteria` PostgreSQL schema in Supabase.
- [x] Build the core tables:
   - `ontology_mesh` (ID, Term, Tree_Numbers)
   - `ontology_icd10` (Code, Description, Chapter)
   - `ontology_snomed` (Concept_ID, Fully_Specified_Name)
   - `ontology_crosswalk` (Mapping between the three systems)
   - `system_changelog` (Tracks version updates, null drops, and timestamps automatically).

### Phase 2: Python Ingestion Engine (PAUSED - AWAITING API KEY)
- [x] Engineer a new pipeline component: `08_MDM_Ontology_Engine/build_disease_ontology.py`.
- [ ] Connect securely to the NIH UMLS REST API and CMS databases (Requires API Key).
- [ ] Build the upsert logic to dynamically populate the PostgreSQL tables and write natively to the `system_changelog` on every execution loop.

### Phase 3: Application Integration & Next.js UI (IN PROGRESS)
- [ ] Update `api_server.py` to expose `/api/ontology/search?query=...` for lightning-fast typeahead UI functionality.
- [x] Upgrade `src/app/control/page.tsx` with physical inputs for Disease Name, MeSH, ICD-10, and SNOMED.
- [ ] Bind the UI inputs to React `onChange` listeners firing autocomplete requests to the FastAPI bridge.
- [x] Refactor `ver 2.0_organized_meddashbackend_schema.txt` and blueprint files to permanently log the new structural additions.
