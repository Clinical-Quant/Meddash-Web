"""
nightly_scheduler.py — Meddash KOL Pipeline Scheduler (v2.0)
=============================================================
MDP3-SWIP1 Refactored:
  - REMOVED: schedule library + while True loop (n8n handles cron)
  - REMOVED: hardcoded NSCLC fallback
  - ADDED: MeSH Tier 2 rotation via mesh_rotation module
  - ADDED: Tier 1 (BioCrawler leads) + Tier 2 (rotation) merge with dedup
  - ADDED: --dry-run, --targets-override, --json-summary flags
  - ADDED: Structured exit codes (0=success, 1=partial, 2=failure)
  - ADDED: paths.py for cross-platform DB resolution
  - ADDED: Telegram alert integration
  - ADDED: Rotation state tracking + logging

Usage:
  python nightly_scheduler.py                          # Normal run (T1 + T2 rotation)
  python nightly_scheduler.py --dry-run                # Show targets without executing
  python nightly_scheduler.py --targets-override "Disease A" "Disease B"  # Force specific targets
  python nightly_scheduler.py --max-results 100         # Override max PubMed results per target
"""

import argparse
import json
import logging
import os
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ── Path Resolution ────────────────────────────────────────────────────────
# Add DevOps Observability to path so we can import paths and telegram_notifier
DEVOPS_DIR = Path(__file__).resolve().parent.parent / "07_DevOps_Observability"
sys.path.insert(0, str(DEVOPS_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))  # For mesh_rotation

try:
    from paths import DB_PATHS, SUMMARY_DIR, ENGINE_PATHS
    from mesh_rotation import (
        get_rotation_target,
        get_current_category,
        get_rotation_state,
        save_rotation_state,
        mark_category_completed,
        log_rotation_result,
        get_week_index,
    )
except ImportError as e:
    print(f"FATAL: Cannot import required modules: {e}")
    print(f"Ensure paths.py and mesh_rotation.py are in {DEVOPS_DIR} or {Path(__file__).resolve().parent}")
    sys.exit(2)

try:
    import telegram_notifier
except ImportError:
    telegram_notifier = None

# ── Logging ────────────────────────────────────────────────────────────────

LOG_DIR = ENGINE_PATHS.get("devops", Path(__file__).resolve().parent.parent / "07_DevOps_Observability") / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "kol_scheduler.log"),
        logging.StreamHandler(),
    ]
)
log = logging.getLogger(__name__)


# ── Tier 1: BioCrawler Lead Targets ────────────────────────────────────────

def get_tier1_targets() -> list:
    """Read primary_indication from biocrawler_leads.db.
    
    Returns list of disease/condition strings from the leads database.
    These are GTM-aligned targets — where companies are buying.
    """
    db_path = DB_PATHS["biocrawler"]
    
    if not db_path.exists():
        log.warning(f"BioCrawler DB not found at {db_path}. No Tier 1 targets.")
        return []
    
    try:
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT DISTINCT primary_indication FROM biotech_leads "
                "WHERE primary_indication IS NOT NULL AND primary_indication != ''"
            )
            rows = cursor.fetchall()
            targets = [r[0] for r in rows]
            log.info(f"Tier 1: Found {len(targets)} targets from BioCrawler leads")
            return targets
    except Exception as e:
        log.error(f"Failed to fetch Tier 1 targets from DB: {e}")
        return []


# ── Pipeline Execution ────────────────────────────────────────────────────

def run_pipeline(targets: list, max_results: int = 50, pull_id: str = None, run_centrality: bool = True, centrality_write_mode: str = "supabase") -> dict:
    """Execute the KOL pipeline via run_pipeline.py.
    
    Returns dict with: exit_code, stdout, stderr, duration_seconds
    """
    pipeline_script = Path(__file__).resolve().parent / "run_pipeline.py"
    
    cmd = [sys.executable, str(pipeline_script), "--targets"] + targets
    cmd += ["--max_results", str(max_results)]
    if run_centrality:
        cmd += ["--run_centrality", "--centrality_write_mode", centrality_write_mode]
    if pull_id:
        cmd += ["--pull_id", pull_id]
    
    log.info(f"Executing pipeline: {' '.join(cmd)}")
    
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).resolve().parent),
            timeout=3600  # 1 hour timeout
        )
        duration = time.time() - start_time
        
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration_seconds": round(duration, 2),
        }
    except subprocess.TimeoutExpired:
        return {
            "exit_code": 2,
            "stdout": "",
            "stderr": "Pipeline timed out after 3600 seconds",
            "duration_seconds": 3600,
        }
    except Exception as e:
        return {
            "exit_code": 2,
            "stdout": "",
            "stderr": f"Pipeline execution error: {e}",
            "duration_seconds": 0,
        }


def write_summary(summary: dict) -> None:
    """Write pipeline summary JSON to shared summaries directory."""
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    summary_path = SUMMARY_DIR / "kol_pipeline_summary.json"
    
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    
    log.info(f"Pipeline summary written to {summary_path}")


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Meddash KOL Pipeline Scheduler (v2.0 - MDP3-SWIP1)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show targets and rotation without executing pipeline"
    )
    parser.add_argument(
        "--targets-override", nargs="+",
        help="Force specific targets (bypass BioCrawler + rotation)"
    )
    parser.add_argument(
        "--max-results", type=int, default=50,
        help="Max PubMed results per target (default: 50)"
    )
    parser.add_argument(
        "--pull-id", type=str, default=None,
        help="Campaign Sandbox Pull ID for tracking"
    )
    parser.add_argument(
        "--skip-rotation", action="store_true",
        help="Skip Tier 2 MeSH rotation (use only BioCrawler leads)"
    )
    parser.add_argument(
        "--json-summary", action="store_true",
        help="Write pipeline summary JSON to shared summaries directory"
    )
    parser.add_argument(
        "--skip-centrality", action="store_true",
        help="Skip automatic authorship centrality after KOL pull"
    )
    parser.add_argument(
        "--centrality-write-mode", choices=["dry-run", "local", "supabase"], default="supabase",
        help="Centrality output mode when automatic centrality is enabled"
    )
    
    args = parser.parse_args()
    
    # ── Resolve Targets ────────────────────────────────────────────────
    
    rotation_info = get_current_category()
    
    if args.targets_override:
        # Tier 0: Manual override — no T1, no T2, just what the user specified
        targets = args.targets_override
        source = "manual_override"
        dedup_applied = False
        log.info(f"Manual override targets: {targets}")
    
    elif args.skip_rotation:
        # Tier 1 only: BioCrawler leads, no MeSH rotation
        targets = get_tier1_targets()
        source = "tier1_only"
        dedup_applied = False
        if not targets:
            log.error("No BioCrawler targets found and rotation is skipped. Exiting.")
            if telegram_notifier:
                telegram_notifier.send_alert("KOL Pipeline ABORTED — No targets and rotation skipped", level="error")
            sys.exit(2)
    
    else:
        # Default: Tier 1 (BioCrawler) + Tier 2 (MeSH rotation) with dedup
        tier1 = get_tier1_targets()
        targets = get_rotation_target(tier1)
        source = "tier1_tier2_merged"
        dedup_applied = len(targets) == len(tier1)  # dedup applied if rotation was already covered
        log.info(f"T1+T2 targets: {targets} (source: {source}, dedup: {dedup_applied})")
    
    # ── Dry Run ────────────────────────────────────────────────────────
    
    if args.dry_run:
        print("\n=== KOL PIPELINE DRY RUN ===")
        print(f"Timestamp:        {datetime.now(timezone.utc).isoformat()}")
        print(f"Source:            {source}")
        print(f"Current rotation: {rotation_info['category']} ({rotation_info['mesh_code']}) — {rotation_info['ta']}")
        print(f"Week:             {get_week_index()+1}/{12}")
        print(f"Targets:          {targets}")
        print(f"Max results:      {args.max_results}")
        print(f"Tier1 count:      {len(get_tier1_targets())}")
        print(f"Dedup applied:    {dedup_applied}")
        print(f"Pull ID:          {args.pull_id or 'None'}")
        print(f"Centrality:       {'disabled' if args.skip_centrality else args.centrality_write_mode}")
        
        state = get_rotation_state()
        print(f"\nRotation state:")
        for key, value in state.items():
            print(f"  {key}: {value}")
        return 0
    
    # ── Execute Pipeline ───────────────────────────────────────────────
    
    log.info(f"Starting KOL pipeline with {len(targets)} targets (source: {source})")
    if telegram_notifier:
        telegram_notifier.send_alert(
            f"KOL Pipeline Started\n\n"
            f"Targets: {len(targets)}\n"
            f"Source: {source}\n"
            f"Rotation: {rotation_info['category']} ({rotation_info['mesh_code']})\n"
            f"Week: {get_week_index()+1}/12",
            level="info"
        )
    
    start_time = time.time()
    result = run_pipeline(
        targets,
        max_results=args.max_results,
        pull_id=args.pull_id,
        run_centrality=not args.skip_centrality,
        centrality_write_mode=args.centrality_write_mode,
    )
    duration = round(time.time() - start_time, 2)
    
    # ── Process Results ────────────────────────────────────────────────
    
    exit_code = result["exit_code"]
    
    # Determine status
    if exit_code == 0:
        status = "success"
    elif exit_code == 1:
        status = "partial"
    else:
        status = "failure"
    
    # Mark rotation as completed if successful
    if status != "failure" and source != "manual_override" and not args.skip_rotation:
        mark_category_completed(rotation_info["category"])
        log_rotation_result(
            category=rotation_info["category"],
            mesh_code=rotation_info["mesh_code"],
            cycle=get_rotation_state().get("cycle_count", 1),
            week_number=get_week_index(),
            tier1_targets=len(get_tier1_targets()),
            tier2_target=rotation_info["category"],
            dedup_applied=dedup_applied,
        )
    
    # Write summary JSON
    summary = {
        "engine": "kol_data",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "targets": targets,
        "rotation": rotation_info,
        "dedup_applied": dedup_applied,
        "status": status,
        "exit_code": exit_code,
        "duration_seconds": duration,
        "pull_id": args.pull_id,
        "stdout_last_line": result["stdout"].strip().split("\n")[-1] if result["stdout"] else "",
        "stderr_last_line": result["stderr"].strip().split("\n")[-1] if result["stderr"] else "",
        "centrality_enabled": not args.skip_centrality,
        "centrality_write_mode": args.centrality_write_mode if not args.skip_centrality else "disabled",
    }
    write_summary(summary)
    
    # ── Alert ───────────────────────────────────────────────────────────
    
    if telegram_notifier:
        if status == "success":
            telegram_notifier.send_alert(
                f"KOL Pipeline Complete\n\n"
                f"Targets: {len(targets)}\n"
                f"Rotation: {rotation_info['category']} ({rotation_info['mesh_code']})\n"
                f"Status: {status}\n"
                f"Duration: {duration}s",
                level="success"
            )
        elif status == "partial":
            telegram_notifier.send_alert(
                f"KOL Pipeline Partial Success\n\n"
                f"Targets: {len(targets)}\n"
                f"Status: {status}\n"
                f"Duration: {duration}s",
                level="warning"
            )
        else:
            telegram_notifier.send_alert(
                f"KOL Pipeline FAILED\n\n"
                f"Targets: {len(targets)}\n"
                f"Error: {result['stderr'][:200]}\n"
                f"Duration: {duration}s",
                level="error"
            )
    
    log.info(f"Pipeline completed: status={status}, duration={duration}s")
    
    # ── Exit ────────────────────────────────────────────────────────────
    
    if status == "success":
        return 0
    elif status == "partial":
        return 1
    else:
        return 2


if __name__ == "__main__":
    sys.exit(main())