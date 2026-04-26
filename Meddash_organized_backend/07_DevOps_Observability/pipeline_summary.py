"""
pipeline_summary.py — Structured Output Convention for All Meddash Engines
==========================================================================
MDP3-SWIP1: Standardized JSON summary output for n8n/Paperclip monitoring.

Every engine writes a summary JSON to the shared summaries directory after
each run. n8n and Paperclip agents can read these summaries to determine
pipeline health, trigger downstream workflows, or escalate failures.

Convention:
  File: {engine}_summary.json
  Location: 06_Shared_Datastores/pipeline_summaries/
  
  Required fields:
    engine:      str   ("kol_data", "ct_data", "biocrawler", "kol_brief", "ta_landscape", "scholar", "ontology", "cq_newsletter")
    timestamp:   str   ISO 8601 UTC
    status:       str   "success" | "partial" | "failure"
    duration_seconds: float
    
  Optional fields (engine-specific):
    targets:         list  (KOL targets used)
    rotation:        dict  (MeSH rotation info)
    mode:            str   (full/delta/query for CT, api/deep/all for BioCrawler)
    trials_saved:    int   (CT crawler)
    trials_skipped:  int   (CT crawler)
    leads_added:     int   (BioCrawler)
    pull_id:         str   (Campaign Sandbox Pull ID)
    error:           str   (failure details)

Usage:
  from pipeline_summary import write_summary
  
  write_summary(
      engine="kol_data",
      status="success",
      duration_seconds=120.5,
      targets=["Breast Cancer", "Lung Cancer"],
      rotation={"category": "Neoplasms", "mesh_code": "C04"},
  )
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger(__name__)

# ── Path Resolution ────────────────────────────────────────────────────────
# Try to use paths.py, fall back to convention
try:
    from paths import SUMMARY_DIR
except ImportError:
    SUMMARY_DIR = Path(__file__).resolve().parent.parent / "06_Shared_Datastores" / "pipeline_summaries"


def write_summary(engine: str, status: str, duration_seconds: float, **kwargs) -> Path:
    """
    Write a standardized pipeline summary JSON.
    
    Args:
        engine:           Engine identifier (e.g. "kol_data", "ct_data")
        status:           "success", "partial", or "failure"
        duration_seconds: Duration of the pipeline run
        **kwargs:         Additional engine-specific fields
    
    Returns:
        Path to the written summary file
    """
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    
    summary = {
        "engine": engine,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "duration_seconds": round(duration_seconds, 2),
    }
    summary.update(kwargs)
    
    summary_path = SUMMARY_DIR / f"{engine}_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    
    log.info(f"[pipeline_summary] Written {summary_path} — status={status}")
    return summary_path


def read_summary(engine: str) -> dict:
    """
    Read the most recent summary for an engine.
    
    Args:
        engine: Engine identifier
    
    Returns:
        Summary dict, or empty dict if not found
    """
    summary_path = SUMMARY_DIR / f"{engine}_summary.json"
    if not summary_path.exists():
        return {}
    
    with open(summary_path, "r") as f:
        return json.load(f)


def read_all_summaries() -> dict:
    """
    Read all available summaries.
    
    Returns:
        Dict mapping engine names to their summary dicts
    """
    summaries = {}
    if not SUMMARY_DIR.exists():
        return summaries
    
    for path in SUMMARY_DIR.glob("*_summary.json"):
        engine = path.stem.replace("_summary", "")
        with open(path, "r") as f:
            summaries[engine] = json.load(f)
    
    return summaries


# ── CLI ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Pipeline Summary CLI")
    parser.add_argument("--read", type=str, help="Read summary for engine (e.g., kol_data)")
    parser.add_argument("--read-all", action="store_true", help="Read all available summaries")
    args = parser.parse_args()
    
    if args.read:
        summary = read_summary(args.read)
        print(json.dumps(summary, indent=2) if summary else f"No summary found for '{args.read}'")
    elif args.read_all:
        summaries = read_all_summaries()
        print(json.dumps(summaries, indent=2) if summaries else "No summaries found")
    else:
        print("Use --read <engine> or --read-all")