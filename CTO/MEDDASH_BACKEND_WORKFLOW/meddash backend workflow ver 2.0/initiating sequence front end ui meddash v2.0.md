# Meddash Phase 2.0: System Initialization Sequence

To successfully bring the entire unified architecture (Python Data Engines + PostgreSQL Cloud + Next.js UI) online on a local or remote node, follow this strict architectural sequence.

## Pre-Flight Checks
1. Ensure your core `.env` file exists directly inside `C:\Users\email\.gemini\antigravity\Meddash_organized_backend\.env`.
2. Ensure it contains the mandatory keys: `SUPABASE_URI` and `SERPAPI_KEY`.
3. Verify Node.js v24.14+ and Python 3.10+ are active in the system paths.

---

## Step 1: Boot the Python FastAPI Sidecar (The Bridge)
The Next.js browser GUI cannot natively execute your Python crawler scripts or securely talk to PostgreSQL without exposing secrets. The `api_server.py` daemon must be brought online first.

**Execution:**
1. Open up **PowerShell** (Terminal 1).
2. Navigate to the core routing folder:
   ```bash
   cd "C:\Users\email\.gemini\antigravity\Meddash_organized_backend"
   ```
3. Boot the execution listener on Port 8000:
   ```bash
   python -m uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
   ```
*Verification:* The terminal should output `PostgreSQL Pipeline: Connected!` and `Application startup complete`. The background engines are now armed and listening.

---

## Step 2: Boot the Next.js Frontend Framework
Once the Python backend is actively guarding the databases, we compile the React interface.

**Execution:**
1. Open up **PowerShell** (Terminal 2) (Leave Terminal 1 running untouched).
2. Navigate to the React frontend folder:
   ```bash
   cd "C:\Users\email\.gemini\antigravity\meddash-frontend"
   ```
3. Start the Node compilation engine:
   ```bash
   npm run dev
   ```
*Verification:* Wait ~5 to 10 seconds for the Next.js router to compile the CSS schemas. The terminal will output `Ready in ...ms` and bind to Port 3000.

---

## Step 3: Access the Meddash SaaS Control Center
1. Open Google Chrome or Microsoft Edge.
2. Navigate to: `http://localhost:3000`
3. You are now inside Meddash Version 2.0. 
   - Click the **Data Explorer** widget to pull live arrays out of Supabase (bridged entirely through Port 8000).
   - Click **Fetch Metrics** on the KOL Dashboard to witness the system autonomously shell out to `09_Scholar_Engine`, parse the API, write to the cloud, and update your React DOM instantly.
