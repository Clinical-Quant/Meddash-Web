"""
Central config — all paths, env vars, and SQL queries in one place.
Widgets import from here. Change a path or query → change it once.

v1.1 — Fixed table names and column names to match real Supabase schema.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env ────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

# Also load the Meddash backend .env (it has the real Supabase creds)
MEDDASH_ENV = BASE_DIR.parent.parent / "Meddash_organized_backend" / ".env"
if MEDDASH_ENV.exists():
    load_dotenv(MEDDASH_ENV, override=False)

# Also load the CQ .env
CQ_ENV = BASE_DIR.parent / "CQ_Team" / ".env"
if CQ_ENV.exists():
    load_dotenv(CQ_ENV, override=False)

# ── Supabase ─────────────────────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY", "")

# ── Database paths ───────────────────────────────────────────────────────────
MEDDASH_ROOT = BASE_DIR.parent.parent / "Meddash_organized_backend"
SQLITE_PATHS = {
    "kols":          MEDDASH_ROOT / "06_Shared_Datastores" / "meddash_kols.db",
    "trials":        MEDDASH_ROOT / "06_Shared_Datastores" / "ct_trials.db",
    "biocrawler":     MEDDASH_ROOT / "06_Shared_Datastores" / "biocrawler_leads.db",
}

# ── SQLite table name overrides ─────────────────────────────────────────────
# Supabase and SQLite use different table names in some cases
SQLITE_TABLE_MAP = {
    # sqlite_db: { "supabase_name": "sqlite_name" }
    "trials": { "display": "Clinical Trials", "sqlite_table": "trials" },
}

# ── Product folders ──────────────────────────────────────────────────────────
PRODUCT_PATHS = {
    "kol_briefs":     MEDDASH_ROOT / "04_Product_KOL_Briefs" / "kol_briefs",
    "ta_landscapes":  MEDDASH_ROOT / "05_Product_TA_Landscape",  # broader search
}

# ── Supabase table config ───────────────────────────────────────────────────
# Tables that DON'T have an 'id' column need different select columns
SB_TABLE_SELECT_COLUMNS = {
    "kols": "id",
    "kols_staging": "id",
    "kol_merge_candidates": "id",
    "kol_scholar_metrics": "kol_id",  # No 'id' column
    "biotech_leads": "company_name",   # No 'id' column
    "trials": "nct_id",               # Supabase table is 'trials' not 'ct_trials'
    "cq_regulatory_catalysts": "id",
}

# Known Supabase table names (some differ from what we expected)
SB_TABLES = [
    "kols",
    "kols_staging",
    "kol_merge_candidates",
    "kol_scholar_metrics",
    "biotech_leads",
    "trials",                       # NOT 'ct_trials'
    "cq_regulatory_catalysts",
]

# ── Refresh interval (seconds) ───────────────────────────────────────────────
REFRESH_SECONDS = 120  # 2 min auto-refresh