# Meddash Backend & Workflow Version 2.0 Sequence
*Date and Time Stamp: 2026-03-25 11:20:44 EST*

## Vision & Readme
**Vision Statement:**
Version 2.0 represents the critical evolution of Meddash. While Version 1.0 successfully segmented our data engines (KOL, CT, BioCrawler, etc.) into robust, domain-driven standalone scripts, Version 2.0 is unifying the built Meddash backends and file systems with a centralized Front-End UI. This UI is designed specifically for services implementation, providing quick access and streamlined maintenance as the operational hub for our Medical Affairs and Biotech SaaS offerings.

**Readme for Updates:**
*This living document serves as our ground-truth sequence and audit trail for Version 2.0. As new workflow steps, scripts, or UI components are amended, this file MUST be updated with a new timestamp, detailing What We Did, Why We Did It, Issues Faced, Resolutions, and Achievements to maintain a coherent human context window.*

---

## Process Sequence & Audit Trail

### Phase 1: Foundation & Scaffold (COMPLETED)

**1. Active Infrastructure Provisioning**
* **What We Had:** A Windows Victus node with no native frontend environment.
* **What We Did:** Installed the Node.js LTS environment natively via `winget`.
* **Why We Did:** Required to run the Next.js framework compilation engine natively without external cloud dependencies.
* **Issues Faced:** The initial `npx` execution failed because the `npm` binary was not recognized in the system path.
* **Resolution:** Halted the automated progression, explicitly verified the missing dependency, and prompted the CEO for a root-level Windows Package Manager installation.
* **Achieved:** Node.js v24.14 environment successfully established.

**2. Next.js Initialization**
* **What We Had:** A backend-only Python codebase.
* **What We Did:** Initialized the Next.js frontend directory (`meddash-frontend`) using Vanilla CSS (no Tailwind).
* **Why We Did:** To decouple our robust Python backend from the complex JavaScript ecosystem, enabling a standalone React app to serve the GUI independently.
* **Issues Faced:** `npm` blocked the installation because our target folder `Meddash_Frontend` contained capital letters. The interactive prompt also froze waiting for Next.js compiler input.
* **Resolution:** Renamed the target directory to `meddash-frontend` dynamically and bypassed standard CLI blocks by piping programmatic newline inputs (`\n`) directly into the background process over terminal.
* **Achieved:** Functional standalone React application scaffolded.

**3. UI Styling Definition**
* **What We Had:** Default Next.js boilerplate styling.
* **What We Did:** Set up global CSS incorporating a premium, dark-mode aesthetic with glassmorphism and built the main `page.tsx` 4-button dashboard layout.
* **Why We Did:** The operation requires a highly customized, dynamic, and premium interface that commands immediate visual authority internally.
* **Issues Faced:** Null.
* **Resolution:** Null.
* **Achieved:** Premium visual foundation laid for the dashboard.

**4. FastAPI Sidecar Scaffold**
* **What We Had:** Python backend scripts and a React frontend unable to natively trigger them.
* **What We Did:** Scaffolded the FastAPI bridge (`api_server.py`) alongside its `requirements.txt` in the organized backend folder.
* **Why We Did:** Next.js cannot natively trigger Python ML models or crawl operations securely on the host OS. The FastAPI Sidecar translates Next.js HTTP requests into raw Python subprocess execution commands safely.
* **Issues Faced:** Null.
* **Resolution:** Null.
* **Achieved:** Secure bridge established between Node.js frontend and Python backend.

---

### Phase 2: Database Visualizer & PostgreSQL (COMPLETED)

**5. PostgreSQL Cloud Initialization & Data Migration**
* **What We Had:** 3 primary decentralised SQLite datastores (KOLs, Trials, Leads).
* **What We Did:** Migrated these datastores to a unified PostgreSQL server instance on Supabase via Python DevOps script (`migrate_sqlite_to_pg.py`).
* **Why We Did:** Phase 2 implies heavy simultaneous scaling. SQLite's file-level locking limits concurrent read/write and risks `database is locked` bottlenecks as crawlers and UI clash simultaneously.
* **Issues Faced:** The standard Supabase direct link crashed our Python pipeline because standard ISPs failed to resolve its strict IPv6 DNS record natively.
* **Resolution:** Pivoted connection strategy to the "Session Pooler" IPv4 bypass URL, allowing the automation to complete.
* **Achieved:** Unified, cloud-ready, collision-free PostgreSQL database.

**6. FastAPI Supabase Integration**
* **What We Had:** Raw DBs in the cloud, unreadable by the browser.
* **What We Did:** Overwrote `api_server.py` with SQLAlchemy engines feeding through Pandas to expose API routes: `/api/db/kols`, `/api/db/trials`, `/api/db/leads`.
* **Why We Did:** React frontend cannot safely access a proprietary PostgreSQL database without exposing DB credentials to the browser.
* **Issues Faced:** SQL queries returned raw tuples which break Next.js JSON parsers, especially when encountering missing data (`NaN`).
* **Resolution:** Wrapped PostgreSQL extractions in Pandas DataFrames, applying `.fillna(0)` and explicit `orient="records"` transformations to guarantee perfect JSON arrays.
* **Achieved:** Standardized REST endpoints for frontend consumption.

**7. Next.js Data Visualizer GUI**
* **What We Had:** APIs returning data, but no UI to see it.
* **What We Did:** Engineered `src/app/explorer/page.tsx` using responsive React State arrays to construct a dynamic, tabbed data table.
* **Why We Did:** The CEO needed a visual management replacement for `pgAdmin` or `DB Browser for SQLite` native to the actual Meddash SaaS app.
* **Issues Faced:** Frontend router needed to map array keys into table columns securely across 3 entirely different schema profiles dynamically.
* **Resolution:** Wrote a dynamic `<table/>` iterator that loops over `Object.keys()` of the very first JSON array payload to derive exact PostgreSQL column headers dynamically.
* **Achieved:** A native, dynamic database explorer UI within Meddash.

---

### Phase 3: System Health & Execution Control (COMPLETED)

**8. FastAPI Subprocess Dispatcher**
* **What We Had:** No way to run Python crawlers from the Next.js UI.
* **What We Did:** Engineered `/api/system/run` and `/api/system/logs/{script}` routes natively into `api_server.py`.
* **Why We Did:** The browser sandbox cannot natively touch OS execution layers. We needed middleware to launch crawlers in protected background threads.
* **Issues Faced:** Native subprocess executions block the main web server thread, crashing all subsequent web traffic until the crawler finishes (potentially hours).
* **Resolution:** Encapsulated the Python `subprocess.Popen` logic into independent `threading.Thread` daemon instances, keeping the FastAPI bridge unlocked and responsive.
* **Achieved:** Safe, asynchronous remote execution of backend engines.

**9. Next.js Virtual Terminal UI**
* **What We Had:** Background scripts running blindly.
* **What We Did:** Engineered a glassmorphism terminal UI (`src/app/health/page.tsx`) mapped to a 1.5-second state polling array against the FastAPI logs.
* **Why We Did:** The CEO needed real-time observability over the background crawling systems visually identical to monitoring a local terminal.
* **Issues Faced:** React re-renders long text arrays strictly top-down, forcing users to constantly scroll manually to see new strings.
* **Resolution:** Deployed a React `useRef` mounted statically to the terminal floor, paired with a `useEffect` hook to force an automated `scrollIntoView(smooth)` trigger the instant new python logs drop.
* **Achieved:** Real-time executable tracking natively in the frontend.

---

### Phase 4/5: Ontology Engine (IN PROGRESS / PAUSED)

**10. Database Provisioning**
* **What We Had:** Unstructured, hardcoded disease arrays in various backend scripts.
* **What We Did:** Created the `disease_criteria` DB schema in PostgreSQL with tables for `ontology_mesh`, `ontology_icd10`, `ontology_snomed`, and `ontology_crosswalk`.
* **Why We Did:** Implementing an MDM (Master Data Management) layer natively rather than integrating large global ontologies into `kol.db`.
* **Issues Faced:** Null.
* **Resolution:** Null.
* **Achieved:** Core structured MDM schemas live in Supabase.

**11. Python Ingestion Engine (PAUSED)**
* **What We Had:** Empty schemas for disease criteria.
* **What We Did:** Engineered `08_MDM_Ontology_Engine/build_disease_ontology.py`.
* **Why We Did:** To connect securely to the NIH UMLS REST API to query and sync standardized medical ontology data.
* **Issues Faced:** Awaiting NIH UMLS API key approval.
* **Resolution:** Engine construction completely paused, awaiting the final credential to connect and populate the database loops.
* **Achieved:** Logic framework scaffolded and pending execution authorization.

**12. App Integration (UI)**
* **What We Had:** No UI for interacting with Disease Criteria data.
* **What We Did:** Upgraded `src/app/control/page.tsx` with physical form inputs for Disease Name, MeSH, ICD-10, and SNOMED.
* **Why We Did:** To bind these physical inputs later to React `onChange` listeners that fire fast typearound/autocomplete queries to the FastAPI bridge.
* **Issues Faced:** Null.
* **Resolution:** Null.
* **Achieved:** UI parameters prepped to capture future ontology mappings dynamically.
