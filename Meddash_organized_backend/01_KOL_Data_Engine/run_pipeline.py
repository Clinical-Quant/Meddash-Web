import argparse
import time
import json
import logging
import traceback
import os
import sys
import subprocess
from pathlib import Path

# Import the centralized DevOps notifier
sys.path.append(r"C:\Users\email\.gemini\antigravity\Meddash_organized_backend\07_DevOps_Observability")
try:
    import telegram_notifier
except ImportError:
    telegram_notifier = None

from extract_publications import fetch_recent_publications
from db_ingestion import initialize_database, ingest_publications_from_json
from kol_disambiguator import run_disambiguation
from kol_weight import compute_all_weights

# Configure logging
LOG_FILE = "meddash_pipeline.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

def run_centrality_phase(pull_id: str = None, write_mode: str = "local"):
    """Run authorship centrality as a single-shot downstream phase."""
    root = Path(__file__).resolve().parents[1]
    script = root / "10_KOL_Centrality_Engine" / "run_centrality.py"
    if write_mode == "dry-run":
        write_flag = "--dry-run"
    elif write_mode == "supabase":
        write_flag = "--write-supabase"
    else:
        write_flag = "--write-local"
    cmd = [
        sys.executable,
        str(script),
        write_flag,
        "--min-publications", "1",
        "--min-join-rate", "0.90",
        "--triggered-by", "kol_pipeline",
    ]
    if write_mode == "supabase":
        cmd.extend(["--write-local"])
    if pull_id:
        cmd.extend(["--pull-id", pull_id])
    logging.info("Phase 5: Running KOL authorship centrality (%s)", write_mode)
    result = subprocess.run(cmd, cwd=str(root), text=True, capture_output=True, timeout=600)
    if result.stdout:
        logging.info("Centrality stdout: %s", result.stdout[-2000:])
    if result.stderr:
        logging.warning("Centrality stderr: %s", result.stderr[-2000:])
    if result.returncode not in (0, 1):
        raise RuntimeError(f"Centrality phase failed with exit code {result.returncode}")
    return result.returncode


def run_nightly_pipeline(
    target_diseases: list,
    pull_id: str = None,
    max_results: int = 50,
    run_centrality: bool = False,
    centrality_write_mode: str = "local",
    run_disambiguation_phase: bool = True,
    run_weights_phase: bool = True,
):
    logging.info(f"Starting pipeline. Targets: {target_diseases}")
    if pull_id:
         logging.info(f"Using Campaign Sandbox mode with Pull ID: {pull_id}")
         
    if telegram_notifier:
        telegram_notifier.send_alert("Meddash Master Pipeline Started\n\nInitiating extraction.", level="info")
        
    try:
        initialize_database()
        
        for ta in target_diseases:
            logging.info(f"Extracting recent publications for: {ta}")
            
            # Phase 1: Fetch
            results = fetch_recent_publications(ta, max_results=max_results) 
            
            if not results:
                logging.warning(f"No results found for {ta}.")
                continue
                
            temp_json = f"temp_{ta.replace(' ','_').lower()}_data.json"
            with open(temp_json, 'w') as f:
                json.dump(results, f)
                
            logging.info(f"Successfully extracted {len(results)} records. Starting PostgreSQL ingestion.")
            
            # Phase 2: Ingest
            ingest_publications_from_json(temp_json, pull_id=pull_id)
            logging.info(f"Successfully ingested data for {ta}.")
            
            if os.path.exists(temp_json):
                os.remove(temp_json)
        
        if run_disambiguation_phase:
            logging.info("Phase 3: Running Disambiguation")
            run_disambiguation(pull_id=pull_id)
        else:
            logging.info("Phase 3: Skipping Disambiguation for bounded scheduled run")
        
        if run_weights_phase:
            logging.info("Phase 4: Computing Publication Weights")
            compute_all_weights()
        else:
            logging.info("Phase 4: Skipping Publication Weights for bounded scheduled run")
        
        if run_centrality:
            run_centrality_phase(pull_id=pull_id, write_mode=centrality_write_mode)
        
        logging.info("Nightly pipeline completed structurally successfully.")
        
    except Exception as e:
        logging.error(f"Pipeline failed with error: {e}")
        logging.error(traceback.format_exc())

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--targets", nargs="+", required=True, help="List of diseases/targets")
    parser.add_argument("--pull_id", required=False, default=None, help="Campaign Sandbox Pull ID")
    parser.add_argument("--max_results", required=False, type=int, default=50, help="Number of publications to fetch")
    parser.add_argument("--run_centrality", action="store_true", help="Run authorship centrality after publication weights")
    parser.add_argument("--centrality_write_mode", choices=["dry-run", "local", "supabase"], default="local", help="Centrality output mode")
    parser.add_argument("--skip_disambiguation", action="store_true", help="Skip full-DB KOL disambiguation for bounded scheduled runs")
    parser.add_argument("--skip_weights", action="store_true", help="Skip full-DB publication weight recomputation for bounded scheduled runs")
    args = parser.parse_args()
    
    run_nightly_pipeline(
        args.targets,
        pull_id=args.pull_id,
        max_results=args.max_results,
        run_centrality=args.run_centrality,
        centrality_write_mode=args.centrality_write_mode,
        run_disambiguation_phase=not args.skip_disambiguation,
        run_weights_phase=not args.skip_weights,
    )
