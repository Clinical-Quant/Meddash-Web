import argparse
import time
import json
import logging
import traceback
import os
import sys

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

def run_nightly_pipeline(target_diseases: list, pull_id: str = None, max_results: int = 50):
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
        
        logging.info("Phase 3: Running Disambiguation")
        run_disambiguation(pull_id=pull_id)
        
        logging.info("Phase 4: Computing Publication Weights")
        compute_all_weights()
        
        logging.info("Nightly pipeline completed structurally successfully.")
        
    except Exception as e:
        logging.error(f"Pipeline failed with error: {e}")
        logging.error(traceback.format_exc())

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--targets", nargs="+", required=True, help="List of diseases/targets")
    parser.add_argument("--pull_id", required=False, default=None, help="Campaign Sandbox Pull ID")
    parser.add_argument("--max_results", required=False, type=int, default=50, help="Number of publications to fetch")
    args = parser.parse_args()
    
    run_nightly_pipeline(args.targets, pull_id=args.pull_id, max_results=args.max_results)
