#!/usr/bin/env python3
"""Select CQ raw extraction rows for verification/content automation."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, UTC
from typing import Any

from cq_automation_common import (
    update_pipeline_status,
    CQ_AUTOMATION_ROOT,
    db_execute,
    db_fetch_all,
    db_fetch_one,
    db_insert_returning,
    ensure_dirs,
    get_db_conn,
    json_safe,
    log_run,
    make_candidate_id,
    read_posted_events,
    utc_stamp,
    write_text_file,
)

EVENT_PRIORITY = {
    "PDUFA": 10,
    "FDA Approval": 12,
    "CRL": 15,
    "AdCom": 20,
    "Phase 3 Data": 25,
    "Interim Analysis": 30,
    "Phase 2 Data": 35,
    "M&A": 40,
    "Partnering": 45,
    "Form 4 Purchase": 55,
    "Phase 1 Data": 60,
    "Offering": 90,
    "Unknown": 99,
}


def rank_candidate(candidate: dict[str, Any]) -> tuple[int, str]:
    event = candidate.get("event_type") or "Unknown"
    # Lower score wins. Sort dates descending by putting inverse string in second element via caller reverse avoidance.
    date = str(candidate.get("event_date") or "0000-00-00")
    return (EVENT_PRIORITY.get(event, 80), date)


def row_to_candidate(row: dict[str, Any], source_table: str) -> dict[str, Any]:
    row = json_safe(row)
    accession = row.get("accession_number")
    if source_table == "cq_catalysts":
        event_type = row.get("event_type") or "Unknown"
        event_date = row.get("catalyst_date")
        reason = f"{event_type} catalyst extracted from 8-K"
    else:
        event_type = "Form 4 Purchase"
        event_date = row.get("transaction_date")
        reason = "Open-market insider purchase extracted from Form 4"
    return {
        "candidate_id": make_candidate_id(source_table, accession or row.get("id") or "unknown"),
        "source_table": source_table,
        "source_row_id": row.get("id"),
        "ticker": row.get("ticker"),
        "company_name": row.get("company_name"),
        "event_type": event_type,
        "event_date": event_date,
        "accession_number": accession,
        "filing_url": row.get("filing_url"),
        "selection_reason": reason,
        "selection_rank": 999,
        "status": "verification_pending",
        "details_json": row,
    }


def load_raw_candidates(conn, limit: int = 50) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    catalysts = db_fetch_all(conn, "SELECT * FROM public.cq_catalysts ORDER BY created_at DESC LIMIT %s", (limit,))
    trades = db_fetch_all(conn, "SELECT * FROM public.cq_insider_trades ORDER BY created_at DESC LIMIT %s", (limit,))
    rows.extend(row_to_candidate(r, "cq_catalysts") for r in catalysts)
    rows.extend(row_to_candidate(r, "cq_insider_trades") for r in trades)
    return rows


def candidate_exists(conn, candidate_id: str) -> bool:
    row = db_fetch_one(conn, "SELECT 1 FROM public.cq_selected_candidates WHERE candidate_id=%s LIMIT 1", (candidate_id,))
    return row is not None


def select_candidates(conn, *, limit: int = 10, dry_run: bool = False) -> list[dict[str, Any]]:
    posted = read_posted_events()
    raw = load_raw_candidates(conn, limit=max(limit * 5, 50))
    filtered: list[dict[str, Any]] = []
    for c in raw:
        acc = c.get("accession_number")
        cid = c.get("candidate_id")
        if not acc or acc in posted or cid in posted:
            continue
        if candidate_exists(conn, cid):
            continue
        filtered.append(c)
    # priority ascending; date descending within priority
    filtered.sort(key=lambda c: (rank_candidate(c)[0], str(c.get("event_date") or "")), reverse=False)
    selected = filtered[:limit]
    for idx, cand in enumerate(selected, start=1):
        cand["selection_rank"] = idx
        if not dry_run:
            db_insert_returning(conn, "cq_selected_candidates", cand, conflict="candidate_id")
    return selected


def render_candidate_summary(selected: list[dict[str, Any]], run_id: str) -> str:
    lines = [f"# CQ Candidate Selection — {run_id}", "", f"Selected candidates: {len(selected)}", ""]
    for c in selected:
        lines.extend([
            f"## {c.get('selection_rank')}. {c.get('ticker')} — {c.get('event_type')}",
            f"- Candidate ID: {c.get('candidate_id')}",
            f"- Company: {c.get('company_name')}",
            f"- Event date: {c.get('event_date')}",
            f"- Accession: {c.get('accession_number')}",
            f"- Source table: {c.get('source_table')}",
            f"- Reason: {c.get('selection_reason')}",
            "",
        ])
    return "\n".join(lines)


def run(args: argparse.Namespace) -> dict[str, Any]:
    ensure_dirs()
    conn = get_db_conn()
    run_id = f"cq-candidate-selector-{utc_stamp()}"
    selected = select_candidates(conn, limit=args.limit, dry_run=args.dry_run)
    summary_md = render_candidate_summary(selected, run_id)
    summary_path = CQ_AUTOMATION_ROOT / "candidates" / f"{utc_stamp()}-candidate-selection.md"
    write_text_file(summary_path, summary_md)
    details = {"selected_count": len(selected), "dry_run": args.dry_run, "summary_path": str(summary_path), "candidates": selected}
    log_run("cq_candidate_selector", "success", f"Selected {len(selected)} CQ candidates", details=details, conn=conn, run_id=run_id)
    return details


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Select CQ candidates from raw catalyst/trade tables")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--dry-run", action="store_true")
    return p


def main() -> int:
    result = run(build_parser().parse_args())
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
