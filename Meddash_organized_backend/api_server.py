import os
import subprocess
import threading
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
import pandas as pd
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Optional

# Absolute path resolutions to mount the .env
base_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(base_dir, '.env'))
SUPABASE_URI = os.getenv("SUPABASE_URI")

app = FastAPI(
    title="Meddash Sidecar API",
    description="Bridge connecting the Meddash Next.js Frontend to the Python Backend and PostgreSQL databases.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global active process tracking
active_processes = {}


class ThreadProcessProxy:
    """Lightweight poll-compatible wrapper so thread-backed jobs appear in Health logs."""
    def __init__(self):
        self.running = True

    def mark_complete(self):
        self.running = False

    def poll(self):
        return None if self.running else 0

# ---------------------------------------------------------
# Database Engine Initialization
# ---------------------------------------------------------
try:
    pg_engine = create_engine(SUPABASE_URI, pool_pre_ping=True)
    print("PostgreSQL Pipeline: Connected!")
except Exception as e:
    pg_engine = None
    print(f"Error resolving PostgreSQL: {e}")

# ---------------------------------------------------------
# Phase 1: API Heartbeat Route
# ---------------------------------------------------------
@app.get("/")
def read_root():
    return {"status": "ok", "message": "Meddash API is online and cleanly bridged to Supabase."}

# ---------------------------------------------------------
# Phase 2: PostgreSQL Visualizer Routes
# Use Pandas logic to abstract standard SQL serialization arrays
# ---------------------------------------------------------
@app.get("/api/db/kols")
def get_kols(limit: int = 150, search: str = None):
    if not pg_engine:
        raise HTTPException(status_code=500, detail="Database Engine Offline.")
    
    query = """
    SELECT 
        k.id AS kol_id, 
        k.first_name || ' ' || k.last_name AS name, 
        k.specialty, 
        k.author_publication_weight AS weight,
        s.total_citations,
        s.h_index,
        s.last_updated_date
    FROM kols k
    LEFT JOIN kol_scholar_metrics s ON k.id::text = s.kol_id::text
    """
    if search:
        query += f" WHERE k.first_name ILIKE '%%{search}%%' OR k.last_name ILIKE '%%{search}%%'"
    query += f" ORDER BY k.author_publication_weight DESC NULLS LAST LIMIT {limit}"
    
    try:
        df = pd.read_sql(query, pg_engine)
        df = df.fillna(0)
        return {"data": df.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/db/trials")
def get_trials(limit: int = 150):
    if not pg_engine:
        raise HTTPException(status_code=500, detail="Database Engine Offline.")
    query = f"SELECT nct_id, brief_title, phase, overall_status FROM trials LIMIT {limit}"
    try:
        df = pd.read_sql(query, pg_engine)
        df = df.fillna("Unknown")
        return {"data": df.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/db/leads")
def get_leads(limit: int = 150):
    if not pg_engine:
        raise HTTPException(status_code=500, detail="Database Engine Offline.")
    query = f"SELECT company_name, primary_indication, trial_phases, tier, website_url FROM biotech_leads ORDER BY tier DESC NULLS LAST LIMIT {limit}"
    try:
        df = pd.read_sql(query, pg_engine)
        df = df.fillna(0)
        return {"data": df.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------
# Phase 3: System Health & Execution Control Routes
# ---------------------------------------------------------
@app.post("/api/system/run")
def run_system_script(script_name: str):
    """Executes a physical .py script securely in a background thread."""
    allowed = {
        "ct_crawler": "02_CT_Data_Engine/ct_crawler.py",
        "biocrawler": "03_BioCrawler_GTM/biocrawler.py",
        "ta_landscape": "05_Product_TA_Landscape/generate_ta_landscape_stepwise.py"
    }
    
    if script_name not in allowed:
        raise HTTPException(status_code=400, detail="Script not officially authorized for frontend remote execution.")
        
    script_path = os.path.join(base_dir, allowed[script_name])
    log_path = os.path.join(base_dir, "07_DevOps_Observability", f"{script_name}.log")
    
    # Ensure observablity directory exists
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    if script_name in active_processes and active_processes[script_name].poll() is None:
        raise HTTPException(status_code=429, detail="This exact script is already actively running!")
        
    def execute_and_log():
        with open(log_path, "w", encoding="utf-8") as out:
            # We must use proper env and executable
            proc = subprocess.Popen(["python", script_path], stdout=out, stderr=subprocess.STDOUT, cwd=base_dir)
            active_processes[script_name] = proc
            proc.wait()

    threading.Thread(target=execute_and_log, daemon=True).start()
    return {"status": "success", "message": f"Successfully initiated background execution shell for {script_name}."}

@app.get("/api/system/logs/{script_name}")
def get_script_logs(script_name: str):
    """Streams the tail logs of active processes back to the UI."""
    log_path = os.path.join(base_dir, "07_DevOps_Observability", f"{script_name}.log")
    
    is_running = script_name in active_processes and active_processes[script_name].poll() is None
    
    if not os.path.exists(log_path):
        return {"logs": "No execution history found yet. Ready for launch.", "running": is_running}
        
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            # Send back the last 100 lines for the physical terminal view
            lines = f.readlines()[-100:]
            return {"logs": "".join(lines) if lines else "Process initiated... yielding execution.", "running": is_running}
    except Exception as e:
        return {"logs": f"Error resolving logs: {str(e)}", "running": is_running}

class AdvancedPayload(BaseModel):
    engine: str
    disease_name: Optional[str] = ""
    mesh_id: Optional[str] = ""
    phases: List[str] = []
    statuses: List[str] = []
    date_from: Optional[str] = ""
    date_to: Optional[str] = ""
    pull_id: Optional[str] = ""
    max_results: Optional[int] = 50

@app.post("/api/system/run_advanced")
def run_advanced(payload: AdvancedPayload):
    allowed = {
        "kol_engine": "01_KOL_Data_Engine/run_pipeline.py",
        "ct_crawler": "02_CT_Data_Engine/ct_crawler.py",
        "biocrawler": "03_BioCrawler_GTM/biocrawler.py",
        "ta_landscape": "05_Product_TA_Landscape/generate_ta_landscape_stepwise.py",
        "sequential_ct_bio": "sequential_ct_bio"
    }
    
    if payload.engine not in allowed:
        raise HTTPException(status_code=400, detail="Invalid target engine.")
        
    log_name = payload.engine if payload.engine != "sequential_ct_bio" else "sequential_ct_bio"
    log_path = os.path.join(base_dir, "07_DevOps_Observability", f"{log_name}.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    if log_name in active_processes and active_processes[log_name].poll() is None:
        raise HTTPException(status_code=429, detail="Engine is already actively running!")
        
    def execute_advanced():
        with open(log_path, "w", encoding="utf-8") as out:
            
            def build_args(script_rel_path):
                cmd = ["python", os.path.join(base_dir, script_rel_path)]
                query_term = payload.mesh_id if payload.mesh_id else payload.disease_name
                
                if query_term:
                    if "run_pipeline" in script_rel_path:
                        cmd.extend(["--targets", query_term])
                        if payload.pull_id:
                            cmd.extend(["--pull_id", payload.pull_id])
                        if payload.max_results:
                            cmd.extend(["--max_results", str(payload.max_results)])
                    elif "ct_crawler" in script_rel_path:
                        cmd.extend(["--mode", "query", "--query", query_term])
                    elif "biocrawler" in script_rel_path:
                        cmd.extend(["--mode", "deep", "--mesh", query_term])
                        
                if payload.phases:
                    cmd.extend(["--phases", ",".join(payload.phases)])
                if payload.statuses:
                    cmd.extend(["--statuses", ",".join(payload.statuses)])
                if payload.date_from:
                    cmd.extend(["--date_from", payload.date_from])
                if payload.date_to:
                    cmd.extend(["--date_to", payload.date_to])
                return cmd

            if payload.engine == "sequential_ct_bio":
                out.write(">>> INITIATING SEQUENTIAL CRAWLER PIPELINE OVERRIDE <<<\n")
                out.flush()
                # Stage 1: CT Database Search
                cmd_ct = build_args(allowed["ct_crawler"])
                out.write(f"STAGE 1 | Executing: {' '.join(cmd_ct)}\n")
                out.flush()
                proc1 = subprocess.Popen(cmd_ct, stdout=out, stderr=subprocess.STDOUT, cwd=base_dir)
                active_processes[log_name] = proc1
                proc1.wait()
                
                if proc1.returncode == 0:
                    out.write("\n>>> LOCAL DATABASES UPDATED. LAUNCHING BIOCRAWLER GTM ENRICHMENT <<<\n")
                    out.flush()
                    # Stage 2: Biocrawler GTM Search
                    cmd_bio = build_args(allowed["biocrawler"])
                    out.write(f"STAGE 2 | Executing: {' '.join(cmd_bio)}\n")
                    out.flush()
                    proc2 = subprocess.Popen(cmd_bio, stdout=out, stderr=subprocess.STDOUT, cwd=base_dir)
                    active_processes[log_name] = proc2
                    proc2.wait()
                    out.write("\n>>> TOTAL SEQUENTIAL PIPELINE COMPLETE <<<\n")
                else:
                    out.write("\n>>> STAGE 1 FAILED. ABORTING PIPELINE <<<\n")
            else:
                script_path = allowed[payload.engine]
                cmd = build_args(script_path)
                out.write(f"Executing Single Engine: {' '.join(cmd)}\n")
                out.flush()
                proc = subprocess.Popen(cmd, stdout=out, stderr=subprocess.STDOUT, cwd=base_dir)
                active_processes[log_name] = proc
                proc.wait()

    threading.Thread(target=execute_advanced, daemon=True).start()
    return {"status": "success", "message": f"Successfully initiated JSON array injection background schema for {payload.engine}."}

class ScholarSyncPayload(BaseModel):
    kol_id: str

@app.post("/api/scholar/sync")
def sync_scholar(payload: ScholarSyncPayload):
    """
    Accepts a single KOL ID and triggers the SerpApi sync exactly once in a background process.
    """
    script_path = os.path.join(base_dir, "09_Scholar_Engine/sync_scholar_citations.py")
    log_name = f"scholar_sync_{payload.kol_id}"
    log_path = os.path.join(base_dir, "07_DevOps_Observability", f"{log_name}.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    if log_name in active_processes and active_processes[log_name].poll() is None:
        raise HTTPException(status_code=429, detail="A sync for this specific KOL is already actively running!")
        
    def execute_and_log():
        with open(log_path, "w", encoding="utf-8") as out:
            cmd = ["python", script_path, "--kol_id", payload.kol_id]
            out.write(f"Executing Scholar Sync: {' '.join(cmd)}\n")
            out.flush()
            proc = subprocess.Popen(cmd, stdout=out, stderr=subprocess.STDOUT, cwd=base_dir)
            active_processes[log_name] = proc
            proc.wait()

    threading.Thread(target=execute_and_log, daemon=True).start()
    return {"status": "success", "message": f"Successfully initiated background Scholar Sync for KOL {payload.kol_id}."}

# ---------------------------------------------------------
# Phase 4: Campaign Sandbox (Pull ID) Routes
# ---------------------------------------------------------

@app.get("/api/db/sandbox")
def get_sandbox_kols(pull_id: str):
    """Fetches KOLs currently held in the sandbox for a specific pull_id."""
    if not pg_engine:
        raise HTTPException(status_code=500, detail="Database Engine Offline.")
    if not pull_id:
        raise HTTPException(status_code=400, detail="pull_id is required.")
        
    query = f"""
    SELECT 
        id AS kol_id, 
        first_name || ' ' || last_name AS name, 
        specialty,
        institution,
        verification_status
    FROM kols_staging
    WHERE '{pull_id}' = ANY(string_to_array(pull_id, ','))
    """
    try:
        df = pd.read_sql(query, pg_engine)
        # Sanitize NaN/None values to prevent JSON serialization crashes
        df = df.fillna("")
        return {"data": df.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class SandboxActionPayload(BaseModel):
    pull_id: str

@app.post("/api/sandbox/run_disambiguation")
def run_sandbox_disambiguation(payload: SandboxActionPayload):
    """Triggers kol_disambiguator.py specifically for a pull_id sandbox."""
    script_path = os.path.join(base_dir, "01_KOL_Data_Engine/kol_disambiguator.py")
    log_name = f"sandbox_dedup_{payload.pull_id}"
    log_path = os.path.join(base_dir, "07_DevOps_Observability", f"{log_name}.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    if log_name in active_processes and active_processes[log_name].poll() is None:
        raise HTTPException(status_code=429, detail="Disambiguation is currently running for this Pull ID.")
        
    def execute_and_log():
        with open(log_path, "w", encoding="utf-8") as out:
            cmd = ["python", script_path, "--pull_id", payload.pull_id]
            out.write(f"Executing Sandbox Disambiguation: {' '.join(cmd)}\n")
            out.flush()
            proc = subprocess.Popen(cmd, stdout=out, stderr=subprocess.STDOUT, cwd=base_dir)
            active_processes[log_name] = proc
            proc.wait()

    threading.Thread(target=execute_and_log, daemon=True).start()
    return {"status": "success", "message": f"Sandbox Disambiguation initiated for {payload.pull_id}."}

@app.post("/api/sandbox/commit")
def commit_sandbox(payload: SandboxActionPayload):
    """Moves verified KOLs from kols_staging into the main kols, merging duplicates and transferring foreign keys."""
    if not pg_engine:
        raise HTTPException(status_code=500, detail="Database Engine Offline.")
        
    try:
        with pg_engine.connect() as conn:
            from sqlalchemy import text
            ensure_kols_identity_api(conn)
            conn.commit()
            
            # 1. Fetch all pending/verified records targeted for commit
            staging_records = conn.execute(text("""
                SELECT id, first_name, last_name, orcid, institution, specialty, degree, author_publication_weight
                FROM kols_staging
                WHERE :pull = ANY(string_to_array(pull_id, ',')) AND verification_status != 'rejected';
            """), {"pull": payload.pull_id}).fetchall()
            
            for stg in staging_records:
                # 2. Look for the KOL natively in the core 'kols' table
                kol_record = None
                if stg.orcid:
                    kol_record = conn.execute(text("SELECT id, pull_id FROM kols WHERE orcid = :o LIMIT 1"), {"o": stg.orcid}).fetchone()
                else:
                    kol_record = conn.execute(text("SELECT id, pull_id FROM kols WHERE first_name = :f AND last_name = :l LIMIT 1"), 
                        {"f": stg.first_name, "l": stg.last_name}).fetchone()

                if not kol_record:
                    # Insert fresh into kols
                    res = conn.execute(text("""
                        INSERT INTO kols (first_name, last_name, orcid, institution, specialty, degree, author_publication_weight, pull_id)
                        VALUES (:f, :l, :o, :i, :s, :d, :w, :pull) RETURNING id;
                    """), {
                        "f": stg.first_name, "l": stg.last_name, "o": stg.orcid, "i": stg.institution, 
                        "s": stg.specialty, "d": stg.degree, "w": stg.author_publication_weight, "pull": payload.pull_id
                    }).fetchone()
                    core_kol_id = res[0]
                else:
                    # Update existing core KOL
                    core_kol_id = kol_record[0]
                    existing_pulls = kol_record[1] if kol_record[1] else ""
                    if payload.pull_id not in existing_pulls.split(","):
                        new_pulls = f"{existing_pulls},{payload.pull_id}" if existing_pulls else payload.pull_id
                        conn.execute(text("UPDATE kols SET pull_id = :p WHERE id = :id"), {"p": new_pulls, "id": core_kol_id})
                    
                    # Update null demographic fields natively
                    if stg.orcid:
                        conn.execute(text("UPDATE kols SET orcid = :o WHERE id = :id AND orcid IS NULL"), {"o": stg.orcid, "id": core_kol_id})
                    if stg.institution:
                        conn.execute(text("UPDATE kols SET institution = :i WHERE id = :id AND (institution IS NULL OR institution = '')"), {"i": stg.institution, "id": core_kol_id})

                # 3. Transfer relationships from the staging ID to the Core ID
                conn.execute(text("UPDATE kol_authorships SET kol_id = :core WHERE kol_id = :stg"), {"core": core_kol_id, "stg": stg.id})
                # Add any future bridging table migrations here recursively
                
            # 4. Remove the pull_id from the staging CSV strings, and delete row if empty
            conn.execute(text("""
                UPDATE kols_staging 
                SET pull_id = array_to_string(array_remove(string_to_array(pull_id, ','), :pull), ',')
                WHERE :pull = ANY(string_to_array(pull_id, ','));
            """), {"pull": payload.pull_id})
            
            conn.execute(text("DELETE FROM kols_staging WHERE pull_id = '' OR pull_id IS NULL;"))
            conn.commit()
            
        return {"status": "success", "message": f"Verified KOLs for {payload.pull_id} successfully merged downstream to the global core database."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sandbox/export")
def export_sandbox(pull_id: str):
    """Generates a text report for the specific pull_id."""
    if not pg_engine:
        raise HTTPException(status_code=500, detail="Database Engine Offline.")
    
    query = f"""
    SELECT first_name, last_name, institution, specialty, verification_status
    FROM kols_staging
    WHERE '{pull_id}' = ANY(string_to_array(pull_id, ','))
    """
    try:
        df = pd.read_sql(query, pg_engine)
        report_text = f"=== CAMPAIGN SANDBOX EXPORT: {pull_id} ===\n\n"
        report_text += f"Total Records: {len(df)}\n\n"
        for _, row in df.iterrows():
            report_text += f"Name:   {row['first_name']} {row['last_name']}\n"
            report_text += f"Inst:   {row['institution']}\n"
            report_text += f"Spec:   {row['specialty']}\n"
            report_text += f"Status: {row['verification_status']}\n"
            report_text += "-" * 40 + "\n"
            
        export_dir = os.path.join(base_dir, "EXPORT CLIENT TEXT REPORTS")
        os.makedirs(export_dir, exist_ok=True)
        file_path = os.path.join(export_dir, f"export_{pull_id}.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(report_text)
            
        return {"status": "success", "file_path": file_path, "preview": report_text[:500]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sandbox/erase")
def erase_sandbox(payload: SandboxActionPayload):
    """Hard wipes the sandbox for a specific Pull ID."""
    if not pg_engine:
        raise HTTPException(status_code=500, detail="Database Engine Offline.")
    
    try:
        with pg_engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("""
                UPDATE kols_staging 
                SET pull_id = array_to_string(array_remove(string_to_array(pull_id, ','), :pull), ',')
                WHERE :pull = ANY(string_to_array(pull_id, ','));
            """), {"pull": payload.pull_id})
            
            conn.execute(text("DELETE FROM kols_staging WHERE pull_id = '' OR pull_id IS NULL;"))
            conn.commit()
        return {"status": "success", "message": f"Sandbox {payload.pull_id} successfully erased."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== TIER 2: HITL DISAMBIGUATION ROUTES =====

@app.get("/api/sandbox/pending_pairs")
def get_pending_pairs(pull_id: str):
    """Fetches all PENDING merge candidates for a pull_id, joined with full KOL profile data."""
    if not pg_engine:
        raise HTTPException(status_code=500, detail="Database Engine Offline.")
    
    try:
        with pg_engine.connect() as conn:
            from sqlalchemy import text
            rows = conn.execute(text("""
                SELECT 
                    mc.id AS candidate_id,
                    mc.kol_id_a, mc.kol_id_b,
                    mc.score_total, mc.score_coauthor, mc.score_mesh, mc.score_name, mc.score_temporal,
                    mc.merge_type, mc.notes,
                    a.first_name AS a_first, a.last_name AS a_last, a.institution AS a_institution, a.specialty AS a_specialty, a.orcid AS a_orcid,
                    b.first_name AS b_first, b.last_name AS b_last, b.institution AS b_institution, b.specialty AS b_specialty, b.orcid AS b_orcid
                FROM kol_merge_candidates mc
                JOIN kols_staging a ON mc.kol_id_a = a.id
                JOIN kols_staging b ON mc.kol_id_b = b.id
                WHERE mc.status = 'PENDING' AND mc.pull_id = :pull
                ORDER BY mc.score_total DESC
            """), {"pull": pull_id}).fetchall()
            
            pairs = []
            for r in rows:
                # Also fetch MeSH tags for each KOL
                mesh_a = [m.mesh_id for m in conn.execute(text("""
                    SELECT DISTINCT pmm.mesh_id FROM kol_authorships ka
                    JOIN publications p ON ka.publication_id = p.id
                    JOIN publication_mesh_map pmm ON p.pmid = pmm.pmid
                    WHERE ka.kol_id = :kid LIMIT 10
                """), {"kid": r.kol_id_a}).fetchall()]
                
                mesh_b = [m.mesh_id for m in conn.execute(text("""
                    SELECT DISTINCT pmm.mesh_id FROM kol_authorships ka
                    JOIN publications p ON ka.publication_id = p.id
                    JOIN publication_mesh_map pmm ON p.pmid = pmm.pmid
                    WHERE ka.kol_id = :kid LIMIT 10
                """), {"kid": r.kol_id_b}).fetchall()]
                
                pairs.append({
                    "candidate_id": r.candidate_id,
                    "kol_id_a": r.kol_id_a, "kol_id_b": r.kol_id_b,
                    "score_total": r.score_total, "score_coauthor": r.score_coauthor,
                    "score_mesh": r.score_mesh, "score_name": r.score_name, "score_temporal": r.score_temporal,
                    "merge_type": r.merge_type,
                    "kol_a": {"name": f"{r.a_first} {r.a_last}", "institution": r.a_institution or "", "specialty": r.a_specialty or "", "orcid": r.a_orcid or "", "mesh_tags": mesh_a},
                    "kol_b": {"name": f"{r.b_first} {r.b_last}", "institution": r.b_institution or "", "specialty": r.b_specialty or "", "orcid": r.b_orcid or "", "mesh_tags": mesh_b},
                })
            
            return {"data": pairs, "total": len(pairs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class GeminiReviewPayload(BaseModel):
    kol_id_a: int
    kol_id_b: int
    pull_id: str

@app.post("/api/sandbox/gemini_review")
def gemini_review(payload: GeminiReviewPayload):
    """Queries Gemini Flash 2.5 for contextual disambiguation reasoning on a KOL pair."""
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise HTTPException(status_code=503, detail="GOOGLE_API_KEY not configured in .env. Add it to enable Gemini Flash HITL review.")
    
    if not pg_engine:
        raise HTTPException(status_code=500, detail="Database Engine Offline.")
    
    try:
        with pg_engine.connect() as conn:
            from sqlalchemy import text
            kol_a = conn.execute(text("SELECT first_name, last_name, institution, specialty, orcid FROM kols_staging WHERE id = :id"), {"id": payload.kol_id_a}).fetchone()
            kol_b = conn.execute(text("SELECT first_name, last_name, institution, specialty, orcid FROM kols_staging WHERE id = :id"), {"id": payload.kol_id_b}).fetchone()
            
            if not kol_a or not kol_b:
                raise HTTPException(status_code=404, detail="One or both KOL IDs not found in staging.")
            
            # Fetch MeSH tags
            mesh_a = [m.mesh_id for m in conn.execute(text("""
                SELECT DISTINCT pmm.mesh_id FROM kol_authorships ka
                JOIN publications p ON ka.publication_id = p.id
                JOIN publication_mesh_map pmm ON p.pmid = pmm.pmid
                WHERE ka.kol_id = :kid LIMIT 15
            """), {"kid": payload.kol_id_a}).fetchall()]
            
            mesh_b = [m.mesh_id for m in conn.execute(text("""
                SELECT DISTINCT pmm.mesh_id FROM kol_authorships ka
                JOIN publications p ON ka.publication_id = p.id
                JOIN publication_mesh_map pmm ON p.pmid = pmm.pmid
                WHERE ka.kol_id = :kid LIMIT 15
            """), {"kid": payload.kol_id_b}).fetchall()]
            
            # Get merge candidate scores
            scores = conn.execute(text("""
                SELECT score_total, score_coauthor, score_mesh, score_name, score_temporal
                FROM kol_merge_candidates WHERE kol_id_a = :a AND kol_id_b = :b
            """), {"a": payload.kol_id_a, "b": payload.kol_id_b}).fetchone()
        
        prompt = f"""You are a medical research disambiguation advisor. Two KOL (Key Opinion Leader) profiles were found in a publication database and may be the same person or two different people. Analyze the evidence and provide your reasoning.

KOL A:
- Name: {kol_a.first_name} {kol_a.last_name}
- Institution: {kol_a.institution or 'Unknown'}
- Specialty: {kol_a.specialty or 'Unknown'}
- ORCID: {kol_a.orcid or 'None'}
- MeSH Research Tags: {', '.join(mesh_a) if mesh_a else 'None found'}

KOL B:
- Name: {kol_b.first_name} {kol_b.last_name}
- Institution: {kol_b.institution or 'Unknown'}
- Specialty: {kol_b.specialty or 'Unknown'}
- ORCID: {kol_b.orcid or 'None'}
- MeSH Research Tags: {', '.join(mesh_b) if mesh_b else 'None found'}

Disambiguation Scores:
- Name Similarity: {scores.score_name if scores else 'N/A'}
- Co-author Overlap: {scores.score_coauthor if scores else 'N/A'}
- MeSH Overlap: {scores.score_mesh if scores else 'N/A'}
- Temporal Proximity: {scores.score_temporal if scores else 'N/A'}
- Composite Score: {scores.score_total if scores else 'N/A'}

Provide a concise 2-3 sentence assessment: Are these likely the same person or two different individuals? Consider name commonality, specialty overlap, institutional proximity, and research topic alignment. End with your confidence level (High/Medium/Low)."""
        
        import google.generativeai as genai
        genai.configure(api_key=google_api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        
        return {"reasoning": response.text, "kol_id_a": payload.kol_id_a, "kol_id_b": payload.kol_id_b}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ResolvePairPayload(BaseModel):
    kol_id_a: int
    kol_id_b: int
    decision: str  # "same_person", "two_people", "escalate"
    pull_id: str
    gemini_reasoning: str = ""

@app.post("/api/sandbox/resolve_pair")
def resolve_pair(payload: ResolvePairPayload):
    """Resolves a pending merge candidate pair based on human decision."""
    if not pg_engine:
        raise HTTPException(status_code=500, detail="Database Engine Offline.")
    if payload.decision not in ("same_person", "two_people", "escalate"):
        raise HTTPException(status_code=400, detail="Decision must be: same_person, two_people, or escalate.")
    
    try:
        with pg_engine.connect() as conn:
            from sqlalchemy import text
            
            if payload.decision == "same_person":
                # Merge: transfer authorships from B to A, delete B, mark A as verified
                conn.execute(text("UPDATE kol_authorships SET kol_id = :a WHERE kol_id = :b"), {"a": payload.kol_id_a, "b": payload.kol_id_b})
                conn.execute(text("UPDATE kols_staging SET verification_status = 'verified' WHERE id = :id"), {"id": payload.kol_id_a})
                conn.execute(text("DELETE FROM kols_staging WHERE id = :id"), {"id": payload.kol_id_b})
                conn.execute(text("""
                    UPDATE kol_merge_candidates SET status = 'MERGED', reviewed_at = CURRENT_TIMESTAMP, notes = :notes
                    WHERE kol_id_a = :a AND kol_id_b = :b
                """), {"a": payload.kol_id_a, "b": payload.kol_id_b, "notes": f"HITL: Merged. {payload.gemini_reasoning[:200]}"})
                msg = f"KOL {payload.kol_id_b} merged into {payload.kol_id_a} and marked verified."
            
            elif payload.decision == "two_people":
                # Confirm distinct: mark both as verified, remove from merge candidates
                conn.execute(text("UPDATE kols_staging SET verification_status = 'verified' WHERE id IN (:a, :b)"), {"a": payload.kol_id_a, "b": payload.kol_id_b})
                conn.execute(text("""
                    UPDATE kol_merge_candidates SET status = 'REJECTED', reviewed_at = CURRENT_TIMESTAMP, notes = :notes
                    WHERE kol_id_a = :a AND kol_id_b = :b
                """), {"a": payload.kol_id_a, "b": payload.kol_id_b, "notes": f"HITL: Confirmed distinct. {payload.gemini_reasoning[:200]}"})
                msg = f"KOLs {payload.kol_id_a} and {payload.kol_id_b} confirmed as two distinct individuals."
            
            else:  # escalate
                # Move to deep_disambiguation_needed
                conn.execute(text("""
                    INSERT INTO deep_disambiguation_needed (kol_id_a, kol_id_b, score_total, pull_id, gemini_reasoning)
                    VALUES (:a, :b, 
                        (SELECT score_total FROM kol_merge_candidates WHERE kol_id_a = :a AND kol_id_b = :b),
                        :pull, :reason)
                    ON CONFLICT DO NOTHING
                """), {"a": payload.kol_id_a, "b": payload.kol_id_b, "pull": payload.pull_id, "reason": payload.gemini_reasoning})
                conn.execute(text("""
                    UPDATE kol_merge_candidates SET status = 'ESCALATED', reviewed_at = CURRENT_TIMESTAMP, notes = 'Escalated to deep disambiguation'
                    WHERE kol_id_a = :a AND kol_id_b = :b
                """), {"a": payload.kol_id_a, "b": payload.kol_id_b})
                msg = f"Pair ({payload.kol_id_a}, {payload.kol_id_b}) escalated to deep disambiguation queue."
            
            conn.commit()
        return {"status": "success", "message": msg}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== STEP 3: GOOGLE SCHOLAR CITATION PARSING ROUTES =====

class ScholarManualTarget(BaseModel):
    kol_id: int
    scholar_url: str


class ScholarSyncPayload(BaseModel):
    pull_id: str
    targets: List[ScholarManualTarget] = []


def ensure_scholar_columns_api(conn, table_name: str):
    if table_name not in ("kols_staging", "kols"):
        raise ValueError(f"Unsupported scholar table: {table_name}")
    conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS scholar_status TEXT DEFAULT 'pending'"))
    conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS scholar_id TEXT"))
    conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS scholar_profile_url TEXT"))


def ensure_kols_identity_api(conn):
    """Backfills missing ids on final kols rows and restores an insert default sequence."""
    conn.execute(text("CREATE SEQUENCE IF NOT EXISTS kols_id_seq"))
    conn.execute(text("""
        SELECT setval(
            'kols_id_seq',
            COALESCE((SELECT MAX(id) FROM kols WHERE id IS NOT NULL), 0) + 1,
            false
        )
    """))
    conn.execute(text("UPDATE kols SET id = nextval('kols_id_seq') WHERE id IS NULL"))
    conn.execute(text("ALTER TABLE kols ALTER COLUMN id SET DEFAULT nextval('kols_id_seq')"))

@app.post("/api/sandbox/run_scholar_sync")
def run_scholar_sync(payload: ScholarSyncPayload):
    """Launches optional manual Scholar sync for selected KOLs with direct Scholar URLs/IDs."""
    if not SERPAPI_KEY_PRESENT:
        raise HTTPException(status_code=503, detail="SERPAPI_KEY not configured in .env.")
    if not payload.targets:
        raise HTTPException(status_code=400, detail="No manual Scholar targets were provided.")

    process_name = f"scholar_sync_{payload.pull_id}"
    proxy = ThreadProcessProxy()
    active_processes[process_name] = proxy

    def run_in_bg():
        import sys
        script_dir = os.path.join(base_dir, "09_Scholar_Engine")
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)
        from sync_scholar_citations import sync_manual_scholar_entries
        try:
            sync_manual_scholar_entries(payload.pull_id, [target.model_dump() for target in payload.targets])
        finally:
            proxy.mark_complete()
    
    thread = threading.Thread(target=run_in_bg, daemon=True)
    thread.start()
    
    return {"status": "success", "message": f"Manual Scholar sync initiated for {len(payload.targets)} KOLs (pull_id: {payload.pull_id})."}


@app.get("/api/scholar/final_kols")
def get_final_kols_for_pull(pull_id: str):
    """Returns final KOL records for a pull_id for manual scholar enrichment."""
    if not pg_engine:
        raise HTTPException(status_code=500, detail="Database Engine Offline.")
    if not pull_id:
        raise HTTPException(status_code=400, detail="pull_id is required.")

    try:
        with pg_engine.connect() as conn:
            try:
                ensure_kols_identity_api(conn)
                ensure_scholar_columns_api(conn, "kols")
                conn.commit()
            except Exception:
                conn.rollback()

            rows = conn.execute(text("""
                SELECT
                    k.id,
                    k.first_name,
                    k.last_name,
                    k.institution,
                    k.specialty,
                    COALESCE(k.scholar_status, 'pending') AS scholar_status,
                    k.scholar_id,
                    k.scholar_profile_url,
                    m.total_citations,
                    m.h_index,
                    m.i10_index,
                    m.last_updated_date
                FROM kols k
                LEFT JOIN kol_scholar_metrics m ON k.id::text = m.kol_id::text
                WHERE :pull = ANY(string_to_array(k.pull_id, ','))
                ORDER BY k.last_name, k.first_name
            """), {"pull": pull_id}).fetchall()

            data = []
            for r in rows:
                data.append({
                    "id": r.id,
                    "name": f"{r.first_name} {r.last_name}",
                    "institution": r.institution or "",
                    "specialty": r.specialty or "",
                    "scholar_status": r.scholar_status or "pending",
                    "scholar_id": r.scholar_id or "",
                    "scholar_profile_url": r.scholar_profile_url or "",
                    "total_citations": r.total_citations if r.total_citations is not None else None,
                    "h_index": r.h_index if r.h_index is not None else None,
                    "i10_index": r.i10_index if r.i10_index is not None else None,
                    "last_synced": str(r.last_updated_date) if r.last_updated_date else None
                })

            return {"data": data, "total": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scholar/run_final_sync")
def run_final_scholar_sync(payload: ScholarSyncPayload):
    """Launches manual Scholar sync for final KOL rows selected by pull_id."""
    if not SERPAPI_KEY_PRESENT:
        raise HTTPException(status_code=503, detail="SERPAPI_KEY not configured in .env.")
    if not payload.targets:
        raise HTTPException(status_code=400, detail="No final Scholar targets were provided.")

    try:
        with pg_engine.connect() as conn:
            ensure_kols_identity_api(conn)
            ensure_scholar_columns_api(conn, "kols")
            conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to prepare final kols scholar schema: {e}")

    process_name = f"scholar_final_{payload.pull_id}"
    proxy = ThreadProcessProxy()
    active_processes[process_name] = proxy

    def run_in_bg():
        import sys
        script_dir = os.path.join(base_dir, "09_Scholar_Engine")
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)
        from sync_scholar_citations import sync_manual_final_scholar_entries
        try:
            sync_manual_final_scholar_entries(payload.pull_id, [target.model_dump() for target in payload.targets])
        finally:
            proxy.mark_complete()

    thread = threading.Thread(target=run_in_bg, daemon=True)
    thread.start()

    return {"status": "success", "message": f"Manual final Scholar sync initiated for {len(payload.targets)} KOLs (pull_id: {payload.pull_id})."}


@app.get("/api/sandbox/scholar_status")
def get_scholar_status(pull_id: str):
    """Returns per-KOL scholar sync status for the given pull_id."""
    if not pg_engine:
        raise HTTPException(status_code=500, detail="Database Engine Offline.")
    
    try:
        with pg_engine.connect() as conn:
            from sqlalchemy import text
            # Ensure columns exist
            try:
                conn.execute(text("ALTER TABLE kols_staging ADD COLUMN IF NOT EXISTS scholar_status TEXT DEFAULT 'pending'"))
                conn.execute(text("ALTER TABLE kols_staging ADD COLUMN IF NOT EXISTS scholar_id TEXT"))
                conn.execute(text("ALTER TABLE kols_staging ADD COLUMN IF NOT EXISTS scholar_profile_url TEXT"))
                conn.commit()
            except Exception:
                conn.rollback()
            
            rows = conn.execute(text("""
                SELECT s.id, s.first_name, s.last_name, s.institution, s.specialty,
                       COALESCE(s.scholar_status, 'pending') AS scholar_status, 
                       s.scholar_id,
                       s.scholar_profile_url,
                       m.total_citations, m.h_index, m.i10_index, m.last_updated_date
                FROM kols_staging s
                LEFT JOIN kol_scholar_metrics m ON s.id::text = m.kol_id::text
                WHERE :pull = ANY(string_to_array(s.pull_id, ','))
                ORDER BY s.last_name, s.first_name
            """), {"pull": pull_id}).fetchall()
            
            data = []
            for r in rows:
                data.append({
                    "id": r.id,
                    "name": f"{r.first_name} {r.last_name}",
                    "institution": r.institution or "",
                    "specialty": r.specialty or "",
                    "scholar_status": r.scholar_status or "pending",
                    "scholar_id": r.scholar_id or "",
                    "scholar_profile_url": r.scholar_profile_url or "",
                    "total_citations": r.total_citations if r.total_citations else None,
                    "h_index": r.h_index if r.h_index else None,
                    "i10_index": r.i10_index if r.i10_index else None,
                    "last_synced": str(r.last_updated_date) if r.last_updated_date else None
                })
            
            return {"data": data, "total": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sandbox/scholar_review_queue")
def get_scholar_review_queue(pull_id: str):
    """Returns Tier 4 scholar review candidates for KOLs in this pull_id."""
    if not pg_engine:
        raise HTTPException(status_code=500, detail="Database Engine Offline.")
    
    try:
        with pg_engine.connect() as conn:
            from sqlalchemy import text
            rows = conn.execute(text("""
                SELECT srq.id, srq.kol_id, srq.kol_name, 
                       srq.candidate_scholar_id, srq.candidate_name, 
                       srq.candidate_affiliation, srq.candidate_interests,
                       srq.disambiguation_tier_failed, srq.reviewed
                FROM scholar_review_queue srq
                JOIN kols_staging s ON srq.kol_id::text = s.id::text
                WHERE srq.reviewed = false AND :pull = ANY(string_to_array(s.pull_id, ','))
                ORDER BY srq.kol_name
            """), {"pull": pull_id}).fetchall()
            
            data = []
            for r in rows:
                data.append({
                    "queue_id": r.id,
                    "kol_id": r.kol_id,
                    "kol_name": r.kol_name,
                    "candidate_scholar_id": r.candidate_scholar_id,
                    "candidate_name": r.candidate_name or "",
                    "candidate_affiliation": r.candidate_affiliation or "",
                    "candidate_interests": r.candidate_interests or "",
                    "tier_failed": r.disambiguation_tier_failed,
                })
            return {"data": data, "total": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ResolveScholarPayload(BaseModel):
    queue_id: int
    kol_id: str
    candidate_scholar_id: str
    decision: str  # "accept" or "reject"

@app.post("/api/sandbox/resolve_scholar")
def resolve_scholar(payload: ResolveScholarPayload):
    """Human approves or rejects a Scholar candidate from the review queue."""
    if not pg_engine:
        raise HTTPException(status_code=500, detail="Database Engine Offline.")
    if payload.decision not in ("accept", "reject"):
        raise HTTPException(status_code=400, detail="Decision must be: accept or reject.")
    
    try:
        with pg_engine.connect() as conn:
            from sqlalchemy import text
            
            if payload.decision == "accept":
                # Inline: fetch author data, extract metrics, upsert
                script_dir = os.path.join(base_dir, "09_Scholar_Engine")
                import sys
                sys.path.insert(0, script_dir)
                from sync_scholar_citations import fetch_scholar_author_data, extract_metrics, upsert_metrics
                
                author_data = fetch_scholar_author_data(payload.candidate_scholar_id)
                metrics = extract_metrics(author_data)
                upsert_metrics(conn, payload.kol_id, payload.candidate_scholar_id, metrics)
                
                conn.execute(text("UPDATE kols_staging SET scholar_status = 'scholar_verified', scholar_id = :sid WHERE id::text = :kid"),
                             {"sid": payload.candidate_scholar_id, "kid": payload.kol_id})
                msg = f"Scholar {payload.candidate_scholar_id} accepted for KOL {payload.kol_id}. Citations: {metrics['total_citations']}"
            else:
                conn.execute(text("UPDATE kols_staging SET scholar_status = 'scholar_failed' WHERE id::text = :kid"),
                             {"kid": payload.kol_id})
                msg = f"Scholar candidate rejected for KOL {payload.kol_id}."
            
            # Mark reviewed in queue
            conn.execute(text("UPDATE scholar_review_queue SET reviewed = true WHERE id = :qid"), {"qid": payload.queue_id})
            conn.commit()
        
        return {"status": "success", "message": msg}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Check if SERPAPI_KEY is set (used by Scholar sync routes)
SERPAPI_KEY_PRESENT = bool(os.getenv("SERPAPI_KEY"))

if __name__ == "__main__":
    import uvicorn
    # Execution: uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
