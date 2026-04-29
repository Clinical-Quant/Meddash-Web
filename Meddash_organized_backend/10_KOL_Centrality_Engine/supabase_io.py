"""Supabase REST and Postgres IO for centrality engine. Never prints credentials."""
import json
import os
import time
from pathlib import Path
from urllib.parse import quote
import requests

ROOT = Path(__file__).resolve().parents[1]
DEVOPS = ROOT / "07_DevOps_Observability"
import sys
sys.path.insert(0, str(DEVOPS))
try:
    from paths import get_supabase_creds, MEDDASH_ROOT
except Exception:
    def get_supabase_creds():
        return {"url": os.getenv("SUPABASE_URL", ""), "key": os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY", "")}
    MEDDASH_ROOT = ROOT

try:
    from .centrality_config import RUNS_TABLE, SCORES_TABLE
except ImportError:
    from centrality_config import RUNS_TABLE, SCORES_TABLE


def load_env_files():
    for p in [ROOT / ".env", ROOT / "06_Shared_Datastores" / ".env", ROOT.parent / "CTO" / "Meddash-CQ_Dashboard" / ".env"]:
        if not p.exists():
            continue
        for line in p.read_text(errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k, v.strip().strip('"').strip("'"))


def creds():
    load_env_files()
    c = get_supabase_creds()
    if not c.get("url") or not c.get("key"):
        raise RuntimeError("Supabase URL/key not configured")
    return c


def headers(prefer=None):
    c = creds()
    h = {"apikey": c["key"], "Authorization": f"Bearer {c['key']}", "Content-Type": "application/json"}
    if prefer:
        h["Prefer"] = prefer
    return h


def rest_url(table):
    return creds()["url"].rstrip("/") + "/rest/v1/" + table


def fetch_table(table, select="*", order=None, limit=None):
    rows = []
    start = 0
    page = 1000
    while True:
        params = {"select": select}
        if order:
            params["order"] = order
        if limit is not None:
            remaining = limit - len(rows)
            if remaining <= 0:
                break
            current_page = min(page, remaining)
        else:
            current_page = page
        h = headers()
        h["Range"] = f"{start}-{start+current_page-1}"
        r = requests.get(rest_url(table), headers=h, params=params, timeout=60)
        if r.status_code >= 300:
            raise RuntimeError(f"Supabase fetch failed for {table}: HTTP {r.status_code} {r.text[:300]}")
        batch = r.json()
        rows.extend(batch)
        if len(batch) < current_page:
            break
        start += current_page
    return rows


def fetch_source_data(limit=None):
    return {
        "kols": fetch_table("kols", select="id,first_name,last_name,institution,specialty,country", order="id.asc", limit=limit),
        "kol_authorships": fetch_table("kol_authorships", select="kol_id,publication_id,is_primary_author,author_position"),
        "publications": fetch_table("publications", select="id,pmid,journal_name,published_date,issn"),
        "kol_merge_candidates": fetch_table("kol_merge_candidates", select="kol_id_a,kol_id_b,status,score_total"),
    }


def insert_rows(table, rows, chunk_size=500):
    if not rows:
        return 0
    total = 0
    for i in range(0, len(rows), chunk_size):
        chunk = rows[i:i+chunk_size]
        for attempt in range(3):
            r = requests.post(rest_url(table), headers=headers(prefer="return=minimal"), data=json.dumps(chunk, default=str), timeout=120)
            if r.status_code < 300:
                total += len(chunk)
                break
            if attempt == 2:
                raise RuntimeError(f"Supabase insert failed for {table}: HTTP {r.status_code} {r.text[:500]}")
            time.sleep(2 ** attempt)
    return total


def patch_rows(table, filter_query, values):
    url = rest_url(table) + "?" + filter_query
    r = requests.patch(url, headers=headers(prefer="return=minimal"), data=json.dumps(values, default=str), timeout=60)
    if r.status_code >= 300:
        raise RuntimeError(f"Supabase patch failed for {table}: HTTP {r.status_code} {r.text[:500]}")
    return True


def create_schema_via_postgres(schema_path=None):
    load_env_files()
    schema_path = schema_path or Path(__file__).with_name("schema.sql")
    sql = Path(schema_path).read_text()
    import psycopg2
    conn = psycopg2.connect(
        host=os.environ.get("DB_HOST"),
        dbname=os.environ.get("DB_NAME") or "postgres",
        user=os.environ.get("DB_USERNAME") or "postgres",
        password=os.environ.get("DB_PASSWORD"),
        port=os.environ.get("DB_PORT") or 5432,
        sslmode="require",
    )
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql)
    finally:
        conn.close()
    return True


def table_exists(table):
    r = requests.get(rest_url(table), headers={**headers(), "Range": "0-0"}, params={"select": "*"}, timeout=20)
    return r.status_code < 300


def mark_previous_not_latest(graph_scope):
    return patch_rows(SCORES_TABLE, f"graph_scope=eq.{quote(graph_scope)}&is_latest=eq.true", {"is_latest": False})
