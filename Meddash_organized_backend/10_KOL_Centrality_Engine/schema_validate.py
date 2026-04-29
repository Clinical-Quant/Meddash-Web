"""Validate or create centrality Supabase schema."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from supabase_io import table_exists, create_schema_via_postgres
from centrality_config import RUNS_TABLE, SCORES_TABLE


def validate():
    return {RUNS_TABLE: table_exists(RUNS_TABLE), SCORES_TABLE: table_exists(SCORES_TABLE)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--create", action="store_true", help="Execute schema.sql using Postgres credentials")
    args = parser.parse_args()
    if args.create:
        create_schema_via_postgres()
    result = validate()
    payload = {"status": "success" if all(result.values()) else "missing", "tables": result}
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(payload)
    return 0 if all(result.values()) else 2

if __name__ == "__main__":
    raise SystemExit(main())
