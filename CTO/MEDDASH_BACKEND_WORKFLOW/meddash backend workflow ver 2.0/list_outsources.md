# Meddash V2.0 Global Target Map (External Dependencies)

As our SaaS ecosystem expands conceptually, we rely on a mesh of external intelligence endpoints. This ledger documents every URL the Meddash engines physically map to, how they interact, and why the data is strictly necessary for our operation.

---

### 1. ClinicalTrials.gov (CT Data Engine)
* **URL:** `https://clinicaltrials.gov/api/v2/studies`
* **API Driven:** Yes (Official REST v2 Endpoint)
* **Purpose:** To extract granular, ongoing, and completed clinical trial telemetry. We ingest statuses, biological phases, MeSH conditions, investigator nodes, and adverse events to cross-walk clinical testing against individual KOL execution tracking.

### 2. NCBI PubMed (KOL Data Engine)
* **URL:** `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi` / `efetch.fcgi`
* **API Driven:** Yes (Official E-utilities XML REST API)
* **Purpose:** The core ingestion pipeline for scientific publications. We bounce keyword terminology against this node to rapidly scrape author arrays, affiliations, abstracts, and metadata. This provides the primary volume metric used to formulate the KOL Scientific Value Score (SVS).

### 3. Google Scholar via SerpApi (Scholar Engine)
* **URL:** `https://serpapi.com/search`
* **API Driven:** Yes (Third-Party Managed Proxy API)
* **Purpose:** Google Scholar physically bans native python IP scraping. We use the `google_scholar_author` logic inside SerpApi to seamlessly extract high-value vanity metrics (Lifetime Citations, h-index, and i10-index) for our existing KOL roster to display directly in the Next.js UI.

### 4. NIH Unified Medical Language System (Ontology Engine)
* **URL:** `https://uts-ws.nlm.nih.gov/rest/`
* **API Driven:** Yes (REST API requiring strict affiliation licensing)
* **Purpose:** Master Data Management (MDM). Acts as the ultimate ground-truth translational layer, allowing the Next.js UI completely normalize messy doctor queries between SNOMED CT terminology, ICD-10 billing identifiers, and abstract MeSH keywords automatically.

### 5. Google Gemini Cloud (Cognitive Analysis Engine)
* **URL:** `https://generativelanguage.googleapis.com/v1beta/models/`
* **API Driven:** Yes (REST Endpoint bridging via Google `genai` SDK)
* **Purpose:** Deep-pattern fallback logic. This REST endpoint handles reading our scraped clinical context physically cross-walking KOL disambiguation collisions (e.g., verifying if "J. Smith" publishing in Oncology is the exact same biological entity as "J. Smith" running a clinical trial based in Boston). It also synthesizes the final KOL PDF Briefs.

### 6. SCImago Journal & Country Rank (SJR Weighting)
* **URL:** `https://www.scimagojr.com/`
* **API Driven:** No (Static Batch Download / CSV Ingestion)
* **Purpose:** Provides our internal impact-weighting algorithm (APW). By loading SJR rankings into our PostgreSQL database, our crawler weights a KOL publication in *The New England Journal of Medicine* exponentially heavier than a publication in a 4th-tier unreviewed journal.

### 7. Supabase PostgreSQL Cluster (Cloud Backbone)
* **URL:** `postgresql://...aws-0-...pooler.supabase.com:5432` / `https://....supabase.co`
* **API Driven:** Yes (Persistent TCP Database Connection / PostgREST)
* **Purpose:** The physical brain. This cloud endpoint entirely replaces local `.db` SQLite files in Version 2.0 to resolve concurrent file locking. All user UI actions and background python engines stream data entirely against this unified Supabase target.

### 8. SEC EDGAR / Clearbit / ATS (BioCrawler GTM Engine)
* **URL:** Scattered/Dynamic arrays (e.g., `https://www.sec.gov/edgar/searchedgar/companysearch`)
* **API Driven:** Mixed (HTML Scraping + Headless Browser execution)
* **Purpose:** To execute deep intelligence sweeps discovering biotech pipelines and series funding flags. This specific engine searches the open web and formal financial filings to alert the SaaS to high-probability commercialization leads.
