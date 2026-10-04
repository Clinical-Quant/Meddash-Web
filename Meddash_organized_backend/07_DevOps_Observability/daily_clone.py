#!/usr/bin/env python3
"""
daily_clone.py — Supabase → SQLite Daily Backup Clone

Downloads all Supabase tables and writes them to fresh SQLite files
in the clones/ directory. Creates a complete local backup every run.

Schedule: 6:00 AM EST daily (after 2 AM pipeline completes)
Location: 07_DevOps_Observability/daily_clone.py

Usage:
    python daily_clone.py                    # Clone all tables
    python daily_clone.py --tables kols      # Clone specific table
    python daily_clone.py --report           # Print stats only, no write
"""

import os
import sys
import sqlite3
import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path

# ── Path setup ──
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "07_DevOps_Observability"))
sys.path.insert(0, str(BASE_DIR))

from supabase_writer import get_pg_engine
from sqlalchemy import text

# ── Output directory ──
CLONE_DIR = BASE_DIR / "06_Shared_Datastores" / "clones"
CLONE_DIR.mkdir(parents=True, exist_ok=True)

# ── Clone files (grouped by logical DB) ──
CLONE_FILES = {
    "meddash_kols_clone.db": [
        "kols", "kols_staging", "publications", "kol_authorships",
        "kol_merge_candidates", "kol_therapeutic_areas", "therapeutic_areas",
        "therapeutic_area_map", "publication_mesh_map", "mesh_ontology",
        "journal_metrics", "deep_disambiguation_needed", "kol_scholar_metrics",
        "scholar_review_queue", "kol_centrality_runs", "kol_centrality_scores",
    ],
    "ct_trials_clone.db": [
        "trials", "trial_conditions", "trial_interventions", "trial_sponsors",
        "trial_sites", "trial_investigators", "trial_outcomes", "trial_results",
        "trial_publications", "trial_eligibility", "condition_mesh_map",
        "ct_kol_summary",
    ],
    "biocrawler_leads_clone.db": [
        "biotech_leads", "associated_kols", "biotech_associated_kols",
        "crm_contacts", "biotech_tickers", "biotech_ticker_aliases",
        "biocrawler_ticker_matches",
    ],
    "cq_clone.db": [
        "cq_catalysts", "cq_content_queue", "cq_insider_trades",
        "cq_market_events", "cq_market_sentiment", "cq_price_bars",
        "cq_quantitative_analytics", "cq_regulatory_catalysts",
        "cq_research_confirmations", "cq_run_logs", "cq_scientific_congresses",
        "cq_selected_candidates", "cq_source_artifacts",
    ],
    "meddash_lite_clone.db": [
        "brief_requests", "user_profiles", "user_credits",
        "credit_transactions", "system_changelog",
    ],
    "literature_clone.db": [
        "literature_results", "literature_query_log",
    ],
    "ontology_clone.db": [
        "ontology_crosswalk", "ontology_icd10", "ontology_mesh", "ontology_snomed",
    ],
}

# ── Logging ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(str(BASE_DIR / "07_DevOps_Observability" / "logs" / "daily_clone.log")),
    ],
)
log = logging.getLogger(__name__)


def get_table_columns(pg_conn, table_name):
    """Get column names and types from Supabase."""
    r = pg_conn.execute(text(f"""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = '{table_name}' AND table_schema = 'public'
        ORDER BY ordinal_position
    """))
    return [(row[0], row[1]) for row in r.fetchall()]


def clone_table(pg_conn, table_name, sqlite_conn):
    """Download a Supabase table and write to SQLite."""
    # Get columns
    columns = get_table_columns(pg_conn, table_name)
    if not columns:
        log.warning(f"  {table_name}: no columns found — skipping")
        return 0

    col_names = [c[0] for c in columns]
    col_str = ", ".join([f'"{c}"' for c in col_names])

    # Create SQLite table with matching schema
    # Map Postgres types to SQLite types
    type_map = {
        "bigint": "INTEGER", "integer": "INTEGER", "text": "TEXT",
        "double precision": "REAL", "real": "REAL", "numeric": "REAL",
        "boolean": "INTEGER", "timestamp with time zone": "TEXT",
        "timestamp without time zone": "TEXT", "date": "TEXT",
        "time without time zone": "TEXT", "uuid": "TEXT",
        "jsonb": "TEXT", "character varying": "TEXT",
    }

    # Drop and recreate for fresh clone
    sqlite_conn.execute(f'DROP TABLE IF EXISTS "{table_name}"')

    col_defs = []
    for col_name, col_type in columns:
        sqlite_type = type_map.get(col_type, "TEXT")
        col_defs.append(f'"{col_name}" {sqlite_type}')
    create_sql = f'CREATE TABLE "{table_name}" ({", ".join(col_defs)})'
    sqlite_conn.execute(create_sql)

    # Download data from Supabase
    r = pg_conn.execute(text(f'SELECT {col_str} FROM "{table_name}"'))
    rows = r.fetchall()

    if not rows:
        log.info(f"  {table_name}: 0 rows")
        return 0

    # Insert into SQLite
    placeholders = ", ".join(["?"] * len(col_names))
    insert_sql = f'INSERT INTO "{table_name}" ({col_str}) VALUES ({placeholders})'

    for row in rows:
        # Convert row to tuple, handling None and special types
        row_values = []
        for val in row:
            if val is None:
                row_values.append(None)
            elif isinstance(val, (dict, list)):
                import json
                row_values.append(json.dumps(val))
            else:
                row_values.append(str(val) if not isinstance(val, (int, float, str, bool)) else val)
        sqlite_conn.execute(insert_sql, row_values)

    sqlite_conn.commit()
    log.info(f"  {table_name}: {len(rows):,} rows cloned")
    return len(rows)


def run_clone(tables_filter=None, report_only=False):
    """Run the full clone process."""
    start = datetime.now(timezone.utc)
    log.info(f"=== DAILY CLONE START: {start.strftime('%Y-%m-%d %H:%M:%S')} UTC ===")

    engine = get_pg_engine()
    pg_conn = engine.connect()

    total_rows = 0
    total_tables = 0
    summary = {}

    for clone_file, table_list in CLONE_FILES.items():
        if tables_filter and not any(t in tables_filter for t in table_list):
            continue

        clone_path = CLONE_DIR / clone_file

        if report_only:
            # Just report counts
            for table in table_list:
                r = pg_conn.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
                count = r.fetchone()[0]
                summary[table] = count
                total_rows += count
                total_tables += 1
                log.info(f"  {table}: {count:,} rows")
            continue

        # Delete old clone and create fresh
        if clone_path.exists():
            clone_path.unlink()

        sqlite_conn = sqlite3.connect(str(clone_path))
        sqlite_conn.execute("PRAGMA journal_mode=WAL")
        sqlite_conn.execute("PRAGMA synchronous=NORMAL")

        log.info(f"\n--- {clone_file} ---")
        file_rows = 0
        for table in table_list:
            try:
                count = clone_table(pg_conn, table, sqlite_conn)
                summary[table] = count
                file_rows += count
                total_tables += 1
            except Exception as e:
                log.error(f"  {table}: FAILED — {str(e)[:80]}")
                summary[table] = -1

        sqlite_conn.close()
        total_rows += file_rows
        log.info(f"  {clone_file}: {file_rows:,} total rows")

    pg_conn.close()

    elapsed = (datetime.now(timezone.utc) - start).total_seconds()
    log.info(f"\n=== CLONE COMPLETE: {total_tables} tables, {total_rows:,} rows, {elapsed:.1f}s ===")

    # Print summary
    print(f"\n{'Table':<35} {'Rows':>10}")
    print("-" * 47)
    for table, count in sorted(summary.items()):
        if count < 0:
            print(f"{table:<35} {'FAILED':>10}")
        else:
            print(f"{table:<35} {count:>10,}")

    print(f"\nTotal: {total_tables} tables, {total_rows:,} rows, {elapsed:.1f}s")
    print(f"Clones saved to: {CLONE_DIR}")

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Supabase → SQLite Daily Clone")
    parser.add_argument("--tables", nargs="*", help="Clone only specific tables")
    parser.add_argument("--report", action="store_true", help="Report counts only, no write")
    args = parser.parse_args()

    run_clone(tables_filter=args.tables, report_only=args.report)