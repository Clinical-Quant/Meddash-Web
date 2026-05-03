#!/usr/bin/env python3
"""Approval status updater for CQ content queue."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from cq_automation_common import CQ_AUTOMATION_ROOT, db_execute, db_fetch_all, ensure_dirs, get_db_conn, json_safe, log_run, utc_stamp, write_text_file

VALID_ACTIONS = {"approve": "approved", "reject": "rejected", "revise": "needs_revision"}


def update_approval(conn, *, action: str, content_id: str | None = None, candidate_id: str | None = None, reason: str = "") -> dict:
    if action not in VALID_ACTIONS:
        raise ValueError(f"action must be one of {sorted(VALID_ACTIONS)}")
    if not content_id and not candidate_id:
        raise ValueError("content_id or candidate_id is required")
    status = VALID_ACTIONS[action]
    if content_id:
        where = "content_id=%s"
        params = (status, reason, status, content_id)
    else:
        where = "candidate_id=%s"
        params = (status, reason, status, candidate_id)
    db_execute(
        conn,
        f"UPDATE public.cq_content_queue SET approval_status=%s, approval_notes=%s, approved_by='Dr. Don', approved_at=CASE WHEN %s='approved' THEN now() ELSE approved_at END, updated_at=now() WHERE {where}",
        params,
    )
    rows = db_fetch_all(conn, f"SELECT * FROM public.cq_content_queue WHERE {where}", params[-1:])
    return {"updated_count": len(rows), "status": status, "rows": [json_safe(r) for r in rows]}


def copy_approved_outputs(rows: list[dict]) -> list[str]:
    copied = []
    for row in rows:
        src = row.get("output_file_path")
        if not src or not Path(src).exists():
            continue
        dest = CQ_AUTOMATION_ROOT / "approved-posts" / f"{utc_stamp()}-{Path(src).name}"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        copied.append(str(dest))
    return copied


def write_rejection_note(rows: list[dict], reason: str) -> str:
    path = CQ_AUTOMATION_ROOT / "rejected" / f"{utc_stamp()}-rejection-note.md"
    body = "# CQ Rejection / Revision Note\n\n" + f"Reason: {reason}\n\n" + json.dumps(rows, indent=2, default=str)
    write_text_file(path, body)
    return str(path)


def run(args: argparse.Namespace) -> dict:
    ensure_dirs()
    conn = get_db_conn()
    result = update_approval(conn, action=args.action, content_id=args.content_id, candidate_id=args.candidate_id, reason=args.reason or "")
    extra = {}
    if result["status"] == "approved":
        extra["copied_outputs"] = copy_approved_outputs(result["rows"])
    elif result["status"] in {"rejected", "needs_revision"}:
        extra["note_path"] = write_rejection_note(result["rows"], args.reason or result["status"])
    details = {**result, **extra}
    log_run("cq_approval_updater", "success", f"Updated approval status to {result['status']}", details=details, conn=conn)
    return details


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Update CQ approval status")
    p.add_argument("action", choices=sorted(VALID_ACTIONS))
    p.add_argument("--content-id")
    p.add_argument("--candidate-id")
    p.add_argument("--reason", default="")
    return p


def main() -> int:
    result = run(build_parser().parse_args())
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
