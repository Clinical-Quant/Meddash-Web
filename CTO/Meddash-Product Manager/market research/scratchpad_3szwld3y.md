# Meddash Mermaid Viewer Testing Checklist

- [x] Navigate to http://localhost:8000
- [x] Wait for CodeMirror and Mermaid to load
- [x] Interact with the editor: Click, Ctrl+A, Delete
- [x] Paste the provided Mermaid code:
  ```mermaid
  ---
  config:
    layout: elk
  ---
  flowchart TB
   subgraph frontend["Meddash Local SaaS UI Next.js 15"]
          ui_dashboard["Dashboard UI Page"]
          ui_pipeline["Crawler Control & Execution UI"]
          ui_sandbox["Campaign Sandbox Validation UI"]
          ui_health["System Health & Log Streaming UI"]
    end

   subgraph api["FastAPI Middleware & Subprocess Manager"]
          api_server["api_server.py REST Bridge"]
    end

   subgraph backend["01_KOL_Data_Engine"]
          nightly_scheduler_py["nightly_scheduler.py Daily Cron 2:00 AM"]
          run_pipeline_py["run_pipeline.py Command Controller"]
    end

   subgraph datastores["06_Shared_Datastores PostgreSQL Cluster"]
          kols_staging_db[("kols_staging Pull ID Sandbox")]
          meddash_kols_db[("meddash_kols Global Intelligence Target")]
    end

      ui_pipeline -- POST Configuration --> api_server
      api_server -- Subprocess threads --> run_pipeline_py
      nightly_scheduler_py -- Triggers --> run_pipeline_py
  ```
- [x] Verify diagram rendering (SVG visibility)
- [x] Check for error messages (red text)
- [x] Test the ELK hierarchical layout checkbox
- [x] Capture screenshot and report findings

## Findings
- The diagram rendered successfully in the right pane.
- Initially, there was a syntax error due to the `---` blocks (Mermaid v11.13.0 complained about them not being un-indented or unrecognized in the front-matter).
- Removing the front-matter or ensuring proper indentation (though it appeared correct) resolved the parsing issue, but the diagram still rendered even when the error message was visible.
- The **ELK Hierarchical Engine** checkbox works correctly:
  - When checked, the layout is more organized and hierarchical.
  - When unchecked, the layout reverts to the default Mermaid engine (TB flowchart).
- A "Syntax error in text" message with a bomb icon persists at the bottom of the screen, possibly due to the `app.js` not clearing previous errors or a minor syntax issue in the provided diagram (though it renders).
