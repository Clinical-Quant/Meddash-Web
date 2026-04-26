"""
mesh_rotation.py — MeSH Category Rotation for Tier 2 KOL Discovery
=====================================================================
Implements weekly rotation through MeSH top-level disease categories
to systematically expand KOL universe beyond BioCrawler-driven targets.

12-week cycle. After 3 cycles (36 weeks), every major TA has been
covered 3 times with fresh publications.

Usage:
    from mesh_rotation import get_rotation_target, get_rotation_report

v1.0 — MDP3-SWIP1
"""

import json
import os
import sqlite3
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── Configuration ─────────────────────────────────────────────────────────

MESH_ROTATION = [
    {"category": "Neoplasms",                       "mesh_code": "C04", "ta": "Oncology"},
    {"category": "Musculoskeletal Diseases",         "mesh_code": "C05", "ta": "Rheumatology/Orthopedics"},
    {"category": "Respiratory Tract Diseases",       "mesh_code": "C08", "ta": "Pulmonology"},
    {"category": "Nervous System Diseases",          "mesh_code": "C10", "ta": "Neurology"},
    {"category": "Cardiovascular Diseases",          "mesh_code": "C14", "ta": "Cardiology"},
    {"category": "Digestive System Diseases",        "mesh_code": "C06", "ta": "GI/Hepatology"},
    {"category": "Immune System Diseases",           "mesh_code": "C20", "ta": "Immunology/Autoimmune"},
    {"category": "Eye Diseases",                     "mesh_code": "C11", "ta": "Ophthalmology"},
    {"category": "Skin and Connective Tissue Diseases", "mesh_code": "C17", "ta": "Dermatology"},
    {"category": "Endocrine System Diseases",        "mesh_code": "C19", "ta": "Endocrinology"},
    {"category": "Hemic and Lymphatic Diseases",     "mesh_code": "C15", "ta": "Hematology"},
    {"category": "Stomatognathic Diseases",          "mesh_code": "C07", "ta": "Dental/Oral"},
]

# Import paths
try:
    from paths import STATE_DIR, DB_PATHS, SUMMARY_DIR
    STATE_FILE = STATE_DIR / "mesh_rotation_state.json"
    ROTATION_DB = DB_PATHS["rotation_log"]
except ImportError:
    # Fallback if paths.py not available
    STATE_FILE = Path(__file__).parent.parent / "06_Shared_Datastores" / "pipeline_state" / "mesh_rotation_state.json"
    ROTATION_DB = Path(__file__).parent.parent / "06_Shared_Datastores" / "mesh_rotation_log.db"

log = logging.getLogger(__name__)


# ── Rotation Logic ────────────────────────────────────────────────────────

def get_week_index() -> int:
    """Get current rotation index based on ISO week number.
    
    12 categories × repeating = cycles through all TAs every 12 weeks.
    Uses UTC week to avoid timezone drift.
    """
    week_number = datetime.now(timezone.utc).isocalendar()[1]
    return week_number % len(MESH_ROTATION)


def get_current_category() -> dict:
    """Get the MeSH category for the current week.
    
    Returns dict with: category, mesh_code, ta
    """
    return MESH_ROTATION[get_week_index()]


def get_rotation_target(lead_targets: list, max_results: int = 50) -> list:
    """Merge Tier 1 (BioCrawler leads) + Tier 2 (MeSH rotation) targets.
    
    Deduplicates: if the rotation category already exists in lead_targets,
    the rotation category is skipped (avoid double-pulling the same TA).
    
    Args:
        lead_targets: List of disease/condition strings from BioCrawler leads.
        max_results: Max PubMed results per target (default 50).
    
    Returns:
        Deduplicated list of target strings for PubMed search.
    """
    rotation = get_current_category()
    rotation_target = rotation["category"]
    
    # Normalize for dedup: check if rotation category (or close match) is already in leads
    normalized_leads = [t.lower().strip() for t in lead_targets]
    rotation_normalized = rotation_target.lower().strip()
    
    # Check exact and partial matches
    already_covered = False
    for lead in normalized_leads:
        if rotation_normalized in lead or lead in rotation_normalized:
            already_covered = True
            log.info(f"Rotation target '{rotation_target}' already covered by lead target '{lead}' — skipping duplicate")
            break
    
    if already_covered:
        log.info(f"Tier 2 dedup: '{rotation_target}' already in Tier 1 targets. Using Tier 1 only.")
        targets = list(lead_targets)
    else:
        targets = list(lead_targets) + [rotation_target]
        log.info(f"Tier 1 + Tier 2 targets: {targets}")
    
    # Log the merge decision
    log.info(f"Rotation: Week {get_week_index()+1}/{len(MESH_ROTATION)} — "
             f"{rotation['mesh_code']} {rotation['category']} ({rotation['ta']}) — "
             f"Targets: {len(targets)} (Tier1: {len(lead_targets)}, Tier2: 1 if not deduped else 0)")
    
    return targets


def get_rotation_state() -> dict:
    """Load rotation state from JSON file.
    
    Returns default state if file doesn't exist.
    """
    default_state = {
        "current_week": get_week_index(),
        "current_category": get_current_category()["category"],
        "last_run_timestamp": None,
        "last_run_status": None,
        "cycle_count": 1,
        "categories_completed_this_cycle": [],
        "total_runs": 0,
    }
    
    if not STATE_FILE.exists():
        log.info(f"No rotation state file found. Creating default at {STATE_FILE}")
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        save_rotation_state(default_state)
        return default_state
    
    try:
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
        # Update current week/category if stale
        state["current_week"] = get_week_index()
        state["current_category"] = get_current_category()["category"]
        return state
    except (json.JSONDecodeError, KeyError) as e:
        log.warning(f"Corrupt rotation state file: {e}. Resetting to default.")
        save_rotation_state(default_state)
        return default_state


def save_rotation_state(state: dict) -> None:
    """Save rotation state to JSON file.
    
    Updates cycle_count when all 12 categories have been completed.
    """
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if cycle completed
    completed = state.get("categories_completed_this_cycle", [])
    if len(completed) >= len(MESH_ROTATION):
        state["cycle_count"] = state.get("cycle_count", 1) + 1
        state["categories_completed_this_cycle"] = []
        log.info(f"Rotation cycle {state['cycle_count']-1} complete! Starting cycle {state['cycle_count']}.")
    
    state["last_updated"] = datetime.now(timezone.utc).isoformat()
    
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)
    
    log.info(f"Rotation state saved: week {state['current_week']}, category {state.get('current_category')}")


def mark_category_completed(category: str) -> None:
    """Mark a MeSH category as completed in the current cycle.
    
    Called after a successful KOL pipeline run for the rotation target.
    """
    state = get_rotation_state()
    
    completed = state.get("categories_completed_this_cycle", [])
    if category not in completed:
        completed.append(category)
    
    state["categories_completed_this_cycle"] = completed
    state["total_runs"] = state.get("total_runs", 0) + 1
    state["last_run_timestamp"] = datetime.now(timezone.utc).isoformat()
    state["last_run_status"] = "success"
    
    save_rotation_state(state)
    log.info(f"Marked '{category}' as completed. Cycle progress: {len(completed)}/{len(MESH_ROTATION)}")


# ── Rotation Logging (SQLite) ─────────────────────────────────────────────

def _ensure_rotation_db():
    """Create rotation_log.db if it doesn't exist."""
    ROTATION_DB.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(ROTATION_DB))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rotation_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            category TEXT NOT NULL,
            mesh_code TEXT NOT NULL,
            publications_found INTEGER DEFAULT 0,
            kols_disambiguated INTEGER DEFAULT 0,
            kols_weighted INTEGER DEFAULT 0,
            cycle INTEGER DEFAULT 1,
            week_number INTEGER NOT NULL,
            tier1_targets INTEGER DEFAULT 0,
            tier2_target TEXT DEFAULT '',
            dedup_applied INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def log_rotation_result(
    category: str,
    mesh_code: str,
    publications_found: int = 0,
    kols_disambiguated: int = 0,
    kols_weighted: int = 0,
    cycle: int = 1,
    week_number: Optional[int] = None,
    tier1_targets: int = 0,
    tier2_target: str = "",
    dedup_applied: bool = False,
) -> int:
    """Log a rotation run result to SQLite.
    
    Returns the row ID of the inserted record.
    """
    _ensure_rotation_db()
    
    if week_number is None:
        week_number = get_week_index()
    
    conn = sqlite3.connect(str(ROTATION_DB))
    cursor = conn.execute("""
        INSERT INTO rotation_log (
            timestamp, category, mesh_code, publications_found,
            kols_disambiguated, kols_weighted, cycle, week_number,
            tier1_targets, tier2_target, dedup_applied
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now(timezone.utc).isoformat(),
        category,
        mesh_code,
        publications_found,
        kols_disambiguated,
        kols_weighted,
        cycle,
        week_number,
        tier1_targets,
        tier2_target,
        1 if dedup_applied else 0,
    ))
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    
    log.info(f"Rotation result logged: {category} ({mesh_code}) — {publications_found} pubs, {kols_disambiguated} KOLs disambiguated")
    return row_id


def get_rotation_report() -> dict:
    """Generate a growth report from rotation_log.db.
    
    Returns dict with:
        - categories_covered: number of unique MeSH categories with data
        - total_kols_per_category: dict of category -> total KOLs
        - current_cycle: which cycle we're on
        - total_runs: total number of rotation runs
        - estimated_total_12_weeks: projected KOL universe after 12 weeks
        - estimated_total_36_weeks: projected KOL universe after 36 weeks
    """
    _ensure_rotation_db()
    
    conn = sqlite3.connect(str(ROTATION_DB))
    conn.row_factory = sqlite3.Row
    
    try:
        # Total runs
        total_runs = conn.execute("SELECT COUNT(*) FROM rotation_log").fetchone()[0]
        
        # Categories covered
        categories = conn.execute(
            "SELECT DISTINCT category FROM rotation_log"
        ).fetchall()
        categories_covered = [row[0] for row in categories]
        
        # KOLs per category
        kol_per_cat = {}
        for row in conn.execute(
            "SELECT category, SUM(kols_weighted) as total_kols FROM rotation_log GROUP BY category"
        ).fetchall():
            kol_per_cat[row[0]] = row[1]
        
        # Current cycle
        state = get_rotation_state()
        current_cycle = state.get("cycle_count", 1)
        
        # Growth projection
        total_kols = sum(kol_per_cat.values()) if kol_per_cat else 0
        avg_kols_per_run = total_kols / max(total_runs, 1)
        
        # 12 weeks = 12 rotation runs (1 per week)
        estimated_12w = int(avg_kols_per_run * 12) + (total_kols * 2) if total_kols else 0
        # 36 weeks = 3 cycles
        estimated_36w = estimated_12w * 3 if estimated_12w else 0
        
    finally:
        conn.close()
    
    return {
        "categories_covered": len(categories_covered),
        "categories_list": categories_covered,
        "total_kols_per_category": kol_per_cat,
        "current_cycle": current_cycle,
        "total_runs": total_runs,
        "estimated_total_12_weeks": estimated_12w,
        "estimated_total_36_weeks": estimated_36w,
    }


# ── CLI Entry Point ──────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="MeSH Rotation Manager")
    parser.add_argument("--current", action="store_true", help="Show current rotation target")
    parser.add_argument("--state", action="store_true", help="Show rotation state")
    parser.add_argument("--report", action="store_true", help="Show rotation growth report")
    parser.add_argument("--dry-run", action="store_true", help="Show what targets would be used (no execution)")
    parser.add_argument("--mark-completed", type=str, help="Mark a category as completed")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    
    if args.current:
        cat = get_current_category()
        print(f"Week {get_week_index()+1}/{len(MESH_ROTATION)}")
        print(f"  Category: {cat['category']}")
        print(f"  MeSH Code: {cat['mesh_code']}")
        print(f"  TA: {cat['ta']}")
    
    if args.state:
        state = get_rotation_state()
        for key, value in state.items():
            print(f"  {key}: {value}")
    
    if args.report:
        report = get_rotation_report()
        for key, value in report.items():
            print(f"  {key}: {value}")
    
    if args.dry_run:
        # Simulate with mock BioCrawler targets
        mock_leads = ["Non-Small Cell Lung Cancer", "Breast Cancer", "Multiple Myeloma"]
        targets = get_rotation_target(mock_leads)
        cat = get_current_category()
        print(f"\n=== DRY RUN ===")
        print(f"Week: {get_week_index()+1}/{len(MESH_ROTATION)}")
        print(f"Rotation target: {cat['category']} ({cat['mesh_code']}) — {cat['ta']}")
        print(f"Tier 1 (BioCrawler leads): {mock_leads}")
        print(f"Merged targets: {targets}")
        print(f"Total targets: {len(targets)}")
    
    if args.mark_completed:
        mark_category_completed(args.mark_completed)
        print(f"Marked '{args.mark_completed}' as completed.")
    
    if not any([args.current, args.state, args.report, args.dry_run, args.mark_completed]):
        parser.print_help()