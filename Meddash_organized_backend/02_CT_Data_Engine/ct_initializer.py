"""
ct_initializer.py — Meddash CT Trials Database Initializer
===========================================================
Creates ct_trials.db and applies ct_schema.sql.
Safe to re-run — uses CREATE TABLE IF NOT EXISTS throughout.

Run:
    python ct_initializer.py

Also called by ct_ingestion.py on first run to guarantee DB exists.
"""

import sqlite3
import os
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger(__name__)

DB_FILE     = "ct_trials.db"
SCHEMA_FILE = "ct_schema.sql"


def initialize_ct_db(db_path: str = DB_FILE, schema_path: str = SCHEMA_FILE) -> bool:
    """
    Create or verify ct_trials.db from ct_schema.sql.
    Returns True on success.
    """
    if not os.path.exists(schema_path):
        log.error(f"Schema file not found: {schema_path}")
        return False

    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(schema_sql)
        conn.commit()
        log.info(f"Database initialized: {db_path}")

        # Verify all 11 tables exist
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [r[0] for r in cur.fetchall()]
        expected = [
            "ct_kol_summary", "trial_conditions", "trial_eligibility",
            "trial_interventions", "trial_investigators", "trial_outcomes",
            "trial_publications", "trial_results", "trial_sites",
            "trial_sponsors", "trials"
        ]
        missing = [t for t in expected if t not in tables]
        if missing:
            log.error(f"Missing tables after init: {missing}")
            return False

        log.info(f"All {len(expected)} tables verified: {', '.join(tables)}")

        # Count indexes
        cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
        idx_count = cur.fetchone()[0]
        log.info(f"Indexes created: {idx_count}")

        return True

    except Exception as e:
        log.error(f"Schema initialization failed: {e}")
        return False
    finally:
        conn.close()


def get_ct_db_stats(db_path: str = DB_FILE) -> dict:
    """Return row counts for all CT tables — useful for monitoring."""
    if not os.path.exists(db_path):
        return {}
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in cur.fetchall()]
    stats = {}
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        stats[t] = cur.fetchone()[0]
    conn.close()
    return stats


if __name__ == "__main__":
    print("\n  Meddash — ClinicalTrials.gov DB Initializer")
    print("  " + "─" * 48)

    success = initialize_ct_db()

    if success:
        stats = get_ct_db_stats()
        print(f"\n  {'Table':<30} {'Rows':>8}")
        print("  " + "─" * 40)
        for table, count in stats.items():
            print(f"  {table:<30} {count:>8}")
        print(f"\n  ✅ ct_trials.db ready.\n")
    else:
        print("\n  ❌ Initialization failed — check logs above.\n")
