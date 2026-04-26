"""
paths.py — Central path configuration for the Meddash backend.
===========================================================
Every script imports from this single module. Change a path → change it once.
Compatible with both Windows (C:\\Users\\email\\.gemini\\antigravity\\...) and WSL (/mnt/c/...).

Usage:
    from paths import MEDDASH_ROOT, DB_PATHS, SUMMARY_DIR, STATE_DIR

v1.0 — MDP3-SWIP1
"""

import os
import sys
from pathlib import Path

# ── Root Detection ────────────────────────────────────────────────────────
# Works from both Windows and WSL Python environments

def _detect_root() -> Path:
    """Detect Meddash root directory regardless of environment."""
    # Check environment variable first (set by n8n or systemd)
    env_root = os.getenv("MEDDASH_ROOT")
    if env_root:
        return Path(env_root)

    # Try common locations
    candidates = [
        Path(r"C:\Users\email\.gemini\antigravity\Meddash_organized_backend"),
        Path("/mnt/c/Users/email/.gemini/antigravity/Meddash_organized_backend"),
    ]

    # Also try relative to this file
    this_file = Path(__file__).resolve()
    if this_file.parent.name == "07_DevOps_Observability":
        candidates.insert(0, this_file.parent.parent)

    for candidate in candidates:
        if candidate.exists():
            return candidate

    # Fallback: try to find it by walking up from cwd
    cwd = Path.cwd()
    for parent in [cwd] + list(cwd.parents):
        if parent.name == "Meddash_organized_backend":
            return parent

    raise FileNotFoundError(
        f"Cannot find Meddash root. Set MEDDASH_ROOT env var or run from within the project. "
        f"Searched: {[str(c) for c in candidates]}"
    )


MEDDASH_ROOT = _detect_root()

# ── Engine Paths ──────────────────────────────────────────────────────────

ENGINE_PATHS = {
    "kol_data":       MEDDASH_ROOT / "01_KOL_Data_Engine",
    "ct_data":        MEDDASH_ROOT / "02_CT_Data_Engine",
    "biocrawler_gtm": MEDDASH_ROOT / "03_BioCrawler_GTM",
    "kol_briefs":     MEDDASH_ROOT / "04_Product_KOL_Briefs",
    "ta_landscape":   MEDDASH_ROOT / "05_Product_TA_Landscape",
    "shared_data":    MEDDASH_ROOT / "06_Shared_Datastores",
    "devops":         MEDDASH_ROOT / "07_DevOps_Observability",
    "mdm_ontology":   MEDDASH_ROOT / "08_MDM_Ontology_Engine",
    "scholar":        MEDDASH_ROOT / "09_Scholar_Engine",
    "cq_team":        MEDDASH_ROOT.parent / "CTO" / "CQ_Team",
}

# ── Database Paths ────────────────────────────────────────────────────────

DB_PATHS = {
    "kols":          ENGINE_PATHS["shared_data"] / "meddash_kols.db",
    "trials":        ENGINE_PATHS["shared_data"] / "ct_trials.db",
    "biocrawler":    ENGINE_PATHS["shared_data"] / "biocrawler_leads.db",
    "journal_metrics": ENGINE_PATHS["shared_data"] / "journal_metrics.db",
    "rotation_log":  ENGINE_PATHS["shared_data"] / "mesh_rotation_log.db",
}

# ── Directory Paths ───────────────────────────────────────────────────────

STATE_DIR     = ENGINE_PATHS["shared_data"] / "pipeline_state"
SUMMARY_DIR   = ENGINE_PATHS["shared_data"] / "pipeline_summaries"
LOG_DIR       = ENGINE_PATHS["devops"] / "logs"
CT_RAW_DIR    = ENGINE_PATHS["ct_data"] / "ct_raw_json"
CQ_SCRIPTS_DIR = ENGINE_PATHS["cq_team"] / "scripts" / "phase1_regulatory"

# ── Ensure directories exist ──────────────────────────────────────────────

for _dir in [STATE_DIR, SUMMARY_DIR, LOG_DIR, CT_RAW_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)

# ── State File Paths ──────────────────────────────────────────────────────

STATE_FILES = {
    "mesh_rotation":      STATE_DIR / "mesh_rotation_state.json",
    "ct_crawl_state":     ENGINE_PATHS["ct_data"] / "ct_crawl_state.json",
    "kol_pipeline_state":  STATE_DIR / "kol_pipeline_state.json",
    "biocrawler_state":   STATE_DIR / "biocrawler_state.json",
}

# ── Summary File Paths ────────────────────────────────────────────────────

SUMMARY_FILES = {
    "kol_pipeline":  SUMMARY_DIR / "kol_pipeline_summary.json",
    "ct_crawl":      SUMMARY_DIR / "ct_crawl_summary.json",
    "ct_ingestion":   SUMMARY_DIR / "ct_ingestion_summary.json",
    "biocrawler":    SUMMARY_DIR / "biocrawler_summary.json",
    "scholar_sync":  SUMMARY_DIR / "scholar_sync_summary.json",
}

# ── Environment ────────────────────────────────────────────────────────────

def _load_env():
    """Load .env files from multiple locations."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        # dotenv not available — env vars must be set externally
        return

    # Load from shared datastores first (has Supabase creds)
    shared_env = ENGINE_PATHS["shared_data"] / ".env"
    if shared_env.exists():
        load_dotenv(shared_env, override=False)

    # Load from engine-specific .env if exists
    for engine_path in ENGINE_PATHS.values():
        env_file = engine_path / ".env"
        if env_file.exists():
            load_dotenv(env_file, override=False)

    # Load from project root .env
    root_env = MEDDASH_ROOT.parent / ".env"
    if root_env.exists():
        load_dotenv(root_env, override=False)

    # Load CQ team .env
    cq_env = ENGINE_PATHS["cq_team"] / ".env"
    if cq_env.exists():
        load_dotenv(cq_env, override=False)

_load_env()

# ── Utility Functions ─────────────────────────────────────────────────────

def get_db_path(name: str) -> Path:
    """Get database path by name. Raises KeyError if not found."""
    if name not in DB_PATHS:
        raise KeyError(f"Unknown database: {name}. Available: {list(DB_PATHS.keys())}")
    return DB_PATHS[name]

def get_engine_path(name: str) -> Path:
    """Get engine path by name. Raises KeyError if not found."""
    if name not in ENGINE_PATHS:
        raise KeyError(f"Unknown engine: {name}. Available: {list(ENGINE_PATHS.keys())}")
    return ENGINE_PATHS[name]

def get_supabase_creds() -> dict:
    """Get Supabase credentials from environment."""
    return {
        "url": os.getenv("SUPABASE_URL", ""),
        "key": os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY", ""),
    }

def print_paths():
    """Print all resolved paths for debugging."""
    print(f"MEDDASH_ROOT: {MEDDASH_ROOT}")
    print(f"\nEngine Paths:")
    for name, path in ENGINE_PATHS.items():
        exists = "✓" if path.exists() else "✗"
        print(f"  {name}: {exists} {path}")
    print(f"\nDatabase Paths:")
    for name, path in DB_PATHS.items():
        exists = "✓" if path.exists() else "✗"
        print(f"  {name}: {exists} {path}")
    print(f"\nState Directory: {STATE_DIR}")
    print(f"Summary Directory: {SUMMARY_DIR}")


if __name__ == "__main__":
    print_paths()