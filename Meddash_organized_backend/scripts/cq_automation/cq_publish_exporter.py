#!/usr/bin/env python3
"""Export approved CQ content for manual posting and update dedup log."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from cq_automation_common import CQ_AUTOMATION_ROOT, append_posted_event, db_execute, db_fetch_all, db_fetch_one, ensure_dirs, get_db_conn, log_run, utc_stamp


def load_approved_content(conn, limit: int) -> list[dict]:
    return db_fetch_all(
        conn,
        """
        SELECT q.*, c.ticker, c.event_type, c.accession_number
        FROM public.cq_content_queue q
        LEFT JOIN public.cq_selected_candidates c ON q.candidate_id = c.candidate_id
        WHERE q.approval_status = 'approved'
        ORDER BY q.approved_at DESC NULLS LAST, q.created_at DESC
        LIMIT %s
        """,
        (limit,),
    )


def export_rows(conn, rows: list[dict], dry_run: bool = False) -> list[dict]:
    out = []
    export_dir = CQ_AUTOMATION_ROOT / "approved-posts" / f"{utc_stamp()}-manual-export"
    export_dir.mkdir(parents=True, exist_ok=True)
    for row in rows:
        src = row.get("output_file_path")
        exported_path = None
        if src and Path(src).exists():
            dest = export_dir / Path(src).name
            shutil.copy2(src, dest)
            exported_path = str(dest)
        candidate = {
            "candidate_id": row.get("candidate_id"),
            "ticker": row.get("ticker"),
            "event_type": row.get("event_type"),
            "accession_number": row.get("accession_number"),
        }
        if not dry_run:
            append_posted_event(candidate, content_id=row.get("content_id"), action="exported_for_manual_post")
            db_execute(
                conn,
                "UPDATE public.cq_content_queue SET approval_status='exported_for_manual_post', posted_at=now(), updated_at=now() WHERE content_id=%s",
                (row.get("content_id"),),
            )
        out.append({"content_id": row.get("content_id"), "candidate_id": row.get("candidate_id"), "exported_path": exported_path})
    return out


def run(args: argparse.Namespace) -> dict:
    ensure_dirs()
    conn = get_db_conn()
    rows = load_approved_content(conn, args.limit)
    exported = export_rows(conn, rows, dry_run=args.dry_run)
    details = {"approved_rows": len(rows), "exported": exported, "dry_run": args.dry_run}
    log_run("cq_publish_exporter", "success", f"Exported {len(exported)} approved CQ content rows", details=details, conn=conn)
    return details


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Export approved CQ content for manual posting")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--dry-run", action="store_true")
    return p


def main() -> int:
    result = run(build_parser().parse_args())
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
