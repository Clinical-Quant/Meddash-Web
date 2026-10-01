"""
supabase_writer.py — Shared Supabase connection helper for all MBD engines.
All engines import from here to write to Supabase (single source of truth).

Usage:
    from supabase_writer import get_pg_engine, upsert_row, insert_batch_pg

    engine = get_pg_engine()
    with engine.connect() as conn:
        upsert_row(conn, 'trials', row_dict, pk='nct_id')
        insert_batch_pg(conn, 'trial_conditions', rows, pk='id')
        conn.commit()
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from pathlib import Path

# Load .env from Meddash backend
_base = Path(__file__).resolve().parent.parent
_env = _base / ".env"
if _env.exists():
    load_dotenv(_env)

SUPABASE_URI = os.getenv("SUPABASE_URI")

if not SUPABASE_URI:
    raise RuntimeError("SUPABASE_URI not found in .env")

_engine = None

def get_pg_engine():
    """Get or create the shared SQLAlchemy engine."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            SUPABASE_URI,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            connect_args={"connect_timeout": 15}
        )
    return _engine


def upsert_row(conn, table: str, row: dict, pk: str) -> None:
    """Upsert a single row into a Supabase table.
    
    Args:
        conn: SQLAlchemy connection (from engine.connect())
        table: Table name
        row: Dict of column → value
        pk: Primary key column name for ON CONFLICT
    """
    cols = list(row.keys())
    col_names = ", ".join([f'"{c}"' for c in cols])
    placeholders = ", ".join([f":{c}" for c in cols])
    update_cols = [c for c in cols if c != pk]
    update_set = ", ".join([f'"{c}" = EXCLUDED."{c}"' for c in update_cols])
    
    sql = f'INSERT INTO "{table}" ({col_names}) VALUES ({placeholders}) ON CONFLICT ("{pk}") DO UPDATE SET {update_set}'
    conn.execute(text(sql), row)


def insert_batch_pg(conn, table: str, rows: list[dict], pk: str,
                    skip_on_conflict: bool = False) -> int:
    """Insert a batch of rows into Supabase with upsert or ignore on conflict.
    
    Args:
        conn: SQLAlchemy connection
        table: Table name
        rows: List of row dicts
        pk: Primary key column for ON CONFLICT
        skip_on_conflict: If True, use DO NOTHING instead of DO UPDATE
    
    Returns: Number of rows inserted
    """
    if not rows:
        return 0
    
    cols = list(rows[0].keys())
    col_names = ", ".join([f'"{c}"' for c in cols])
    placeholders = ", ".join([f":{c}" for c in cols])
    
    if skip_on_conflict:
        sql = f'INSERT INTO "{table}" ({col_names}) VALUES ({placeholders}) ON CONFLICT ("{pk}") DO NOTHING'
    else:
        update_cols = [c for c in cols if c != pk]
        update_set = ", ".join([f'"{c}" = EXCLUDED."{c}"' for c in update_cols])
        sql = f'INSERT INTO "{table}" ({col_names}) VALUES ({placeholders}) ON CONFLICT ("{pk}") DO UPDATE SET {update_set}'
    
    inserted = 0
    for row in rows:
        try:
            conn.execute(text(sql), row)
            inserted += 1
        except Exception:
            conn.rollback()
    return inserted