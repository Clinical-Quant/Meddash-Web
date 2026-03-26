# Meddash Local Admin Dashboard: Architecture & Build Plan

## Objective
To build a lightweight, locally hosted web application (browser-based UI) that serves as the command center for the Meddash backend. This will streamline your workflow by allowing you to:
1.  **Configure Crawler Inputs:** Set custom MeSH keywords and search parameters dynamically based on client requests.
2.  **Visualize Databases:** Inspect and edit data directly without needing external tools like DB Browser for SQLite.
3.  **Monitor System Health:** Track pipeline execution states, view logs, and trigger cron jobs on-demand.
4.  **Product Generation:** Trigger the generation of KOL Briefs and TA Landscapes directly from the UI.

## Technology Stack

*   **Frontend Framework:** Next.js (React) - Chosen for its simplified routing, powerful component system, and ability to handle API routes seamlessly in a single project.
*   **Styling:** Vanilla CSS - Ensuring a clean, highly customized, and premium "glassmorphism" darkmode aesthetic.
*   **Backend Integration (API Layer):** FastAPI (Python) - Since your backend is entirely Python, FastAPI is the strongly recommended approach to act as the bridge between next.js and your Python scripts/SQLite DBs. It's incredibly fast and self-documenting.
*   **Database Interaction:** `sqlite3` driver in Python (FastAPI).

## Core Application Tabs / Views

### 1. The Configuration Hub (Crawler Control)
*   **Purpose:** Form-based interface to manage input parameters for the various data engines.
*   **Features:**
    *   Input fields for custom MeSH terms, specific KOL names, or target Therapeutics Areas (TAs).
    *   Save configurations to a local JSON (`crawler_config.json`) or SQLite settings table.
    *   "Run Crawler Now" buttons that execute `ct_crawler.py` or `biocrawler.py` with the defined parameters.

### 2. The Data Inspector (DB Visualizer)
*   **Purpose:** A web-based equivalent to "DB Browser for SQLite".
*   **Features:**
    *   Dropdown selector to switch between the core datastores (`meddash_kols.db`, `ct_trials.db`, `biocrawler_leads.db`).
    *   Interactive data tables with pagination, search, and filtering capabilities.
    *   (Optional Next Phase) Inline editing of specific fields, such as approving KOL merge candidates.

### 3. System Health & Observability (Mission Control)
*   **Purpose:** Real-time monitoring of the backend pipeline infrastructure.
*   **Features:**
    *   Status indicators (Green/Red/Running) for the main scripts and cron jobs.
    *   Tail the `logs/` directory in a scrolling terminal-like window on the frontend.
    *   Manual overrides to restart failed jobs or force-sync the Google Sheets CRM.

### 4. Product Generation Engine
*   **Purpose:** Trigger the creation of end-products based on the collected intel.
*   **Features:**
    *   One-click buttons to execute `generate_kol_brief.py` and `generate_ta_landscape_stepwise.py`.
    *   A view to access and download the resulting PDFs or outputs in `csv_exports`.

## Recommended Architecture / Bridging Strategy

Currently, your backend relies on raw scripts and cron jobs. To connect a modern frontend to this securely, we need an API.

**The "Sidecar API" Pattern:**
1.  We will build a small **FastAPI** app (`api_server.py`) inside `C:\Users\email\.gemini\antigravity\Meddash_organized_backend`.
2.  This API server will have endpoints like `GET /api/db/kols`, `POST /api/run/biocrawler`, `GET /api/logs/tail`.
3.  The **Next.js Frontend** will run on `localhost:3000` and make HTTP calls to the FastAPI app (running on `localhost:8000`).
4.  This isolates the UI from the DB connections, and allows the API to spawn `.subprocess()` calls safely to your existing scripts.

## Proposed Build Plan (Next Steps)

1.  **Phase 1: Foundation & Scaffold**
    *   Initialize the Next.js frontend directory (`Meddash_Frontend`).
    *   Set up the global CSS incorporating a premium, dark-mode aesthetic with glassmorphism.
    *   Scaffold the FastAPI bridge (`api_server.py`) in the existing backend.
2.  **Phase 2: Database Visualizer**
    *   Build the FastAPI endpoints to read from the 3 SQLite databases.
    *   Build the UI components (data tables) in Next.js to display the data.
3.  **Phase 3: System Health & Execution Control**
    *   Create API endpoints to trigger Python subprocesses (running the scripts).
    *   Build the UI dashboard to show status and logs.
4.  **Phase 4: Configuration & Product Generation**
    *   Build the input forms for MeSH terms and configuration.
    *   Wire up the buttons to trigger KOL brief generation.

---

> [!NOTE]
> Review this architectural plan. Because your entire backend is Python and SQLite based, wrapping it with a small FastAPI server is the safest, most robust way to allow a beautiful Next.js frontend to securely command your scripts.
