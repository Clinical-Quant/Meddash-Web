#!/usr/bin/env python3
"""Shared utilities for SWIP8 CQ automation scripts."""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timedelta, UTC
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT / ".env"
CQ_TEAM_ROOT = Path("/mnt/c/Users/email/.gemini/antigravity/CTO/CQ_Team")
CQ_AUTOMATION_ROOT = CQ_TEAM_ROOT / "CQ_Automation"
CQ_OBSERVABILITY_ROOT = CQ_TEAM_ROOT / "CQ_Observability"
OBSIDIAN_NEWSLETTER_DIR = Path("/mnt/c/Users/email/Hermes Agent Win Files/projects/clinical-quant/newsletter")
POSTED_EVENTS_LOG = Path("/mnt/c/Users/email/Hermes Agent Win Files/projects/clinical-quant/posted-events-log.md")
EDGAR_IDENTITY = "Clinical Quant contact@meddash.ai"

PIPELINE_REGISTRY_DB = ROOT / "06_Shared_Datastores" / "cq_pipeline_registry.db"


def update_pipeline_status(component_id: str, status: str, run_id: str = "", error: str = "") -> None:
    """UPSERT status into pipeline_registry.db for deterministic dashboard visualization."""
    import sqlite3
    try:
        conn = sqlite3.connect(str(PIPELINE_REGISTRY_DB))
        conn.execute("""
            INSERT INTO pipeline_registry (component_id, status, last_updated, run_id, error_message)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(component_id) DO UPDATE SET
                status=excluded.status,
                last_updated=excluded.last_updated,
                run_id=excluded.run_id,
                error_message=excluded.error_message
        """, (component_id, status, iso_now(), run_id, error))
        conn.commit()
        conn.close()
    except Exception:
        pass  # non-critical — dashboard works without it

AUTOMATION_SUBDIRS = [
    "candidates",
    "verification",
    "approval-packages",
    "newsletter-drafts",
    "tweet-drafts",
    "approved-posts",
    "rejected",
    "scripts",
    "sql",
    "source-artifacts/sec-atom-feeds",
    "source-artifacts/sec-8k-markdown",
    "source-artifacts/sec-8k-html",
    "source-artifacts/form4-xml",
    "source-artifacts/verification-snapshots",
    "source-artifacts/rejected-or-noncatalyst",
]


def utc_now() -> datetime:
    return datetime.now(UTC)


def utc_stamp(dt: datetime | None = None) -> str:
    dt = dt or utc_now()
    return dt.strftime("%Y-%m-%d_%H%M%SZ")


def iso_now() -> str:
    return utc_now().isoformat().replace("+00:00", "Z")


def ensure_dirs() -> None:
    for sub in AUTOMATION_SUBDIRS:
        (CQ_AUTOMATION_ROOT / sub).mkdir(parents=True, exist_ok=True)
    for sub in ["jsonl-run-logs", "daily-summaries", "error-logs"]:
        (CQ_OBSERVABILITY_ROOT / sub).mkdir(parents=True, exist_ok=True)
    OBSIDIAN_NEWSLETTER_DIR.mkdir(parents=True, exist_ok=True)
    POSTED_EVENTS_LOG.parent.mkdir(parents=True, exist_ok=True)
    if not POSTED_EVENTS_LOG.exists():
        POSTED_EVENTS_LOG.write_text("# Clinical Quant Posted Events Log\n\n", encoding="utf-8")


def load_env(path: Path = ENV_PATH) -> dict[str, str]:
    env = dict(os.environ)
    if path.exists():
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            raw = line.strip()
            if not raw or raw.startswith("#") or "=" not in raw:
                continue
            key, val = raw.split("=", 1)
            env[key.strip()] = val.strip().strip('"').strip("'")
    return env


def get_db_conn():
    import psycopg2
    import psycopg2.extras

    env = load_env()
    uri = env.get("SUPABASE_URI") or env.get("SUPABASE_DB_URL") or env.get("DATABASE_URL")
    if not uri:
        raise RuntimeError("Missing SUPABASE_URI/SUPABASE_DB_URL/DATABASE_URL in .env")
    conn = psycopg2.connect(uri)
    conn.autocommit = True
    return conn


def db_fetch_all(conn, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    import psycopg2.extras

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]


def db_fetch_one(conn, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    import psycopg2.extras

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None


def db_execute(conn, sql: str, params: tuple[Any, ...] = ()) -> None:
    with conn.cursor() as cur:
        cur.execute(sql, params)


def db_insert_returning(conn, table: str, row: dict[str, Any], conflict: str | None = None) -> dict[str, Any] | None:
    import psycopg2.extras

    keys = list(row.keys())
    cols = ", ".join(keys)
    vals = [json.dumps(row[k], default=str) if isinstance(row[k], (dict, list)) else row[k] for k in keys]
    placeholders = ", ".join(["%s"] * len(keys))
    update_clause = ""
    if conflict:
        updates = ", ".join([f"{k}=EXCLUDED.{k}" for k in keys if k != conflict])
        update_clause = f" ON CONFLICT ({conflict}) DO UPDATE SET {updates}"
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(f"INSERT INTO public.{table} ({cols}) VALUES ({placeholders}){update_clause} RETURNING *", vals)
        got = cur.fetchone()
        return dict(got) if got else None


def sanitize_slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", str(value)).strip("-") or "unknown"


def make_candidate_id(source_table: str, accession_number: str) -> str:
    prefix = "catalyst" if source_table == "cq_catalysts" else "trade" if source_table == "cq_insider_trades" else sanitize_slug(source_table)
    return f"cand-{prefix}-{sanitize_slug(accession_number)}"


def make_content_id(candidate_id: str, content_type: str) -> str:
    return f"content-{sanitize_slug(content_type)}-{sanitize_slug(candidate_id)}"


def make_artifact_id(candidate_id: str, artifact_type: str) -> str:
    return f"artifact-{sanitize_slug(artifact_type)}-{sanitize_slug(candidate_id)}-{utc_stamp()}"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_artifact_metadata(
    *,
    artifact_path: Path,
    artifact_type: str,
    candidate_id: str,
    ticker: str | None,
    accession_number: str | None,
    source_url: str | None,
    retention_days: int = 90,
) -> dict[str, Any]:
    artifact_path = Path(artifact_path)
    return {
        "artifact_id": make_artifact_id(candidate_id, artifact_type),
        "candidate_id": candidate_id,
        "ticker": ticker,
        "accession_number": accession_number,
        "artifact_type": artifact_type,
        "source_url": source_url,
        "local_file_path": str(artifact_path),
        "sha256_hash": sha256_file(artifact_path),
        "file_size_bytes": artifact_path.stat().st_size,
        "retention_status": "active",
        "expires_at": utc_now() + timedelta(days=retention_days),
    }


def write_text_file(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def read_posted_events() -> set[str]:
    if not POSTED_EVENTS_LOG.exists():
        return set()
    text = POSTED_EVENTS_LOG.read_text(encoding="utf-8", errors="ignore")
    return set(re.findall(r"\b\d{10}-\d{2}-\d{6}\b", text)) | set(re.findall(r"cand-[A-Za-z0-9._-]+", text))


def append_posted_event(candidate: dict[str, Any], content_id: str | None = None, action: str = "exported_for_manual_post") -> None:
    ensure_dirs()
    line = (
        f"- {iso_now()} | {action} | {candidate.get('ticker')} | "
        f"{candidate.get('event_type')} | {candidate.get('accession_number')} | "
        f"{candidate.get('candidate_id')} | {content_id or ''}\n"
    )
    with POSTED_EVENTS_LOG.open("a", encoding="utf-8") as f:
        f.write(line)


def log_run(component: str, status: str, summary: str, *, details: dict[str, Any] | None = None, conn=None, run_id: str | None = None) -> str:
    ensure_dirs()
    run_id = run_id or f"{component}-{utc_stamp()}"
    payload = {
        "run_id": run_id,
        "timestamp_utc": iso_now(),
        "component": component,
        "trigger_type": "manual_or_script",
        "status": status,
        "summary_text": summary,
        "details_json": details or {},
    }
    stamp = utc_stamp()
    jsonl = CQ_OBSERVABILITY_ROOT / "jsonl-run-logs" / f"{stamp}-{component}.jsonl"
    with jsonl.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, default=str) + "\n")
    md = CQ_OBSERVABILITY_ROOT / "daily-summaries" / f"{stamp}-{component}.md"
    write_text_file(md, f"# {component} — {stamp}\n\nStatus: {status}\n\n{summary}\n\n```json\n{json.dumps(details or {}, indent=2, default=str)}\n```\n")
    if conn is not None:
        try:
            db_execute(
                conn,
                """
                INSERT INTO public.cq_run_logs
                (run_id, component, trigger_type, status, summary_text, details_json)
                VALUES (%s,%s,%s,%s,%s,%s::jsonb)
                """,
                (run_id, component, "manual_or_script", status, summary, json.dumps(details or {})),
            )
        except Exception:
            pass
    return run_id


def json_safe(row: dict[str, Any]) -> dict[str, Any]:
    from decimal import Decimal
    out: dict[str, Any] = {}
    for k, v in row.items():
        if hasattr(v, "isoformat"):
            out[k] = v.isoformat()
        elif isinstance(v, Decimal):
            out[k] = float(v)
        else:
            out[k] = v
    return out
