# Meddash Phase 2 UI: Implementation Task List & Audit Trail

This is the exact sequence of events mapping to our frontend plan. Completed items include strict audit trails for future architectural reference to document why choices were made and how bugs were circumvented.

## Phase 1: Foundation & Scaffold (COMPLETED)

- [x] **Active Infrastructure Provisioning:** Installed the Node.js LTS environment natively on the Victus node.
  - **Why:** Required to run the Next.js framework compilation engine natively without external cloud dependencies.
  - **What:** Executed automated `winget` installation to pull Node.js v24.14.
  - **Issues/Restrictions:** The initial `npx` execution failed because the `npm` binary was not recognized in the system path.
  - **Resolution:** Halted the automated progression, explicitly verified the missing dependency, and prompted the CEO for a root-level Windows Package Manager installation.

- [x] **Next.js Initialization:** Initialized the Next.js frontend directory (`meddash-frontend`) using Vanilla CSS.
  - **Why:** To decouple our robust Python backend from the complex JavaScript ecosystem, enabling a standalone React app to serve the GUI independently.
  - **What:** Executed `npx create-next-app` asynchronously without Tailwind (enforcing Vanilla CSS schemas).
  - **Issues/Restrictions:** `npm` blocked the installation because our target folder `Meddash_Frontend` contained capital letters (an outdated naming convention). The interactive prompt also froze waiting for Next.js compiler input.
  - **Resolution:** Renamed the target directory to `meddash-frontend` dynamically and bypassed standard CLI blocks by piping programmatic newline inputs (`\n`) directly into the background process over terminal.

- [x] **UI Styling Definition:** Set up the global CSS incorporating a premium, dark-mode aesthetic with glassmorphism.
  - **Why:** The operation requires a highly customized, dynamic, and premium interface that commands immediate visual authority internally.
  - **What:** Overwrote `globals.css` with dynamic gradient tracking and glass-panel CSS rules, and built the main `page.tsx` 4-button dashboard layout.
  - **Issues/Restrictions:** `null`
  - **Resolution:** `null`

- [x] **FastAPI Sidecar Scaffold:** Scaffolded the FastAPI bridge (`api_server.py`) alongside its `requirements.txt`.
  - **Why:** Next.js cannot natively trigger Python ML models or crawl operations securely on the host operating system. The FastAPI Sidecar translates Next.js HTTP requests into raw Python subprocess execution commands safely.
  - **What:** Deposited `api_server.py` and the raw `python` dependencies directly into `Meddash_organized_backend`.
  - **Issues/Restrictions:** `null`
  - **Resolution:** `null`

## Phase 2: Database Visualizer & PostgreSQL (IN PROGRESS)

- [x] **PostgreSQL Cloud Initialization & Data Migration:** Migrated the 3 primary SQLite datastores to a unified PostgreSQL server instance on Supabase.
  - **Why:** Phase 2 implies heavy simultaneous scaling. SQLite's file-level locking limits concurrent read/write and risks `database is locked` bottlenecks as crawlers and the UI clash simultaneously on disk.
  - **What:** Provisioned a Supabase free-tier cluster. Stored credentials natively in `.env`. Authored a Python DevOps script (`migrate_sqlite_to_pg.py`) using Pandas/SQLAlchemy to natively map and blast 13MB of raw SQLite intelligence into the Cloud automatically.
  - **Issues/Restrictions:** The standard Supabase direct link (`db....supabase.co`) immediately crashed our Python migration pipeline because Windows standard ISPs failed to resolve its strict IPv6 DNS record natively.
  - **Resolution:** Pivoted the connection strategy away from Direct Connection and extracted the "Session Pooler" IPv4 bypass URL (`aws-1-...pooler.supabase.com:5432`), allowing the automation iteration to complete cleanly.

- [x] **FastAPI Supabase Integration:** Built the FastAPI python endpoints (`psycopg2` / `asyncpg`) to read and stream from the PostgreSQL databases.
  - **Why:** The React frontend cannot natively access a proprietary PostgreSQL database securely without exposing DB credentials to the browser.
  - **What:** Overwrote `api_server.py` with SQLAlchemy engines feeding through Pandas `.to_dict()` logic to expose three strict API routes: `/api/db/kols`, `/api/db/trials`, and `/api/db/leads`.
  - **Issues/Restrictions:** Typical SQL queries return raw tuples which break Next.js JSON parsers, especially when encountering missing data (`NaN`).
  - **Resolution:** Wrapped all PostgreSQL extractions in Pandas DataFrames, applying `.fillna(0)` and explicit `orient="records"` transformations to guarantee perfectly formatted JSON arrays.

- [x] **Next.js Data Visualizer GUI:** Built the interactive React UI component (`Explorer`) to consume the FastAPI endpoints and display the dataset arrays cleanly.
  - **Why:** The CEO needed a visual management replacement for `pgAdmin` or `DB Browser for SQLite` native to the actual Meddash SaaS app.
  - **What:** Engineered `src/app/explorer/page.tsx` using responsive React State arrays to construct a dynamic, tabbed data table that mounts directly to the FastAPI sidecar on port 8000.
  - **Issues/Restrictions:** The frontend router needed to dynamically map array keys into table columns securely across 3 entirely different schema profiles dynamically.
  - **Resolution:** Wrote a dynamic `<table/>` iterator that loops over `Object.keys()` of the very first JSON array payload to derive exact PostgreSQL column headers dynamically.

## Phase 3: System Health & Execution Control (COMPLETED)
- [x] **FastAPI Subprocess Dispatcher:** Built secure FastAPI routing endpoints allowing authorized `.subprocess()` triggers for local python scripts directly from Next.js HTTP payloads.
  - **Why:** The browser sandbox cannot natively touch operating system execution layers. We needed a middleware layer capable of launching `ct_crawler.py` and `biocrawler.py` in protected background threads.
  - **What:** Engineered `/api/system/run` and `/api/system/logs/{script}` routes natively into `api_server.py`.
  - **Issues/Restrictions:** Native subprocess executions block the main web server thread, crashing all subsequent web traffic until the crawler finishes (which could take hours).
  - **Resolution:** Encapsulated the Python `subprocess.Popen` execution logic into independent `threading.Thread` daemon instances, allowing the FastAPI bridge to remain completely unlocked and responsive while heavy Python pipelines execute asynchronously.

- [x] **Next.js Virtual Terminal UI:** Built the System Health dashboard to track global execution topologies securely.
  - **Why:** The CEO needed real-time observability over the background crawling systems visually identical to monitoring a local terminal.
  - **What:** Engineered a glassmorphism terminal UI (`src/app/health/page.tsx`) mapped to a 1.5-second state polling array against the FastAPI `/logs` logic.
  - **Issues/Restrictions:** React re-renders long text arrays strictly top-down, forcing users to constantly scroll down manually to see new streaming strings natively.
  - **Resolution:** Deployed a React `useRef` mounted statically to the terminal floor, paired with a `useEffect` hook to force an automated `scrollIntoView(smooth)` trigger the instant new python logs drop into the stream.

## Phase 4: Configuration & Product Generation (PENDING)

### ⚠️ DESIGN APPROVAL REQUIRED: Dynamic Engine Parameters
Before we write the React forms, we must map the hardcoded variables hidden inside your python pipelines into safe UI text fields. Please review and approve this target architecture:

**1. KOL Data Engine (`01_KOL_Data_Engine/run_pipeline.py`)**
- **Current State:** Hardcoded python array `TARGETS = ['Oncology', 'Cardiology', 'Immunology', 'Neurology']`
- **Proposed UI Parameters:** 
  - `Search Targets`: Multi-Select Dropdown (Allowing you to pick Oncology, Neurology, or type a custom term like 'Glioblastoma')
  - `Publication Count Limit`: Number input (default 50)

**2. Clinical Trials Engine (`02_CT_Data_Engine/ct_crawler.py`)**
- **Current State:** Command Line Arguments (`--mode`, `--query`, `--max`)
- **Proposed UI Parameters:**
  - `Execution Mode`: Dropdown (Full Array, Delta/Nightly Updates, or Targeted Query)
  - `Target Query`: Text Input for specific conditions (e.g. "HER2 Breast Cancer")
  - `Max Result Cap`: Number Input (e.g. 1000)

**3. BioCrawler GTM Engine (`03_BioCrawler_GTM/biocrawler.py`)**
- **Current State:** Hardcoded MeSH Ontology Tree `["Neoplasms", "Carcinoma, Non-Small-Cell Lung", "Melanoma", "Lymphoma", "Leukemia, Myeloid, Acute"]`
- **Proposed UI Parameters:**
  - `Execution Mode`: Dropdown (Fast API Mode vs Slow Deep-Enrichment Mode)
  - `Custom MeSH Ontology Array`: Dynamic "Tag" Input allowing you to delete default tags and type new highly specific ontological keywords before clicking RUN.

**4. TA Landscape Generator (`05_Product_TA_Landscape`)**
- **Proposed UI Parameters:**
  - `Therapeutic Area Select`: Dropdown populated by all existing keywords the database has successfully collected intel on.

- [ ] Await CEO approval of the mapped paramater lists for each crawler engine.
- [ ] Build the Crawler Control UI React forms to inject these variables.
- [ ] Wire the frontend layout buttons to pass these variables via JSON POST to the FastAPI executing bridge.
- [ ] Wire the Product Generation front-end buttons to securely execute `generate_kol_brief.py` and extract visual PDFs.
