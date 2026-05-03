#!/usr/bin/env python3
"""Cleanup/archive expired CQ source artifacts indexed by cq_source_artifacts."""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

from cq_automation_common import db_execute, db_fetch_all, ensure_dirs, get_db_conn, log_run


def cleanup_artifacts(conn, *, dry_run: bool = False, limit: int = 100) -> list[dict]:
    rows = db_fetch_all(
        conn,
        """
        SELECT * FROM public.cq_source_artifacts
        WHERE retention_status = 'active' AND expires_at IS NOT NULL AND expires_at < now()
        ORDER BY expires_at ASC
        LIMIT %s
        """,
        (limit,),
    )
    results = []
    for row in rows:
        path = Path(row.get("local_file_path") or "")
        action = "missing"
        new_status = "deleted"
        output_path = None
        if path.exists():
            keep_archive = row.get("artifact_type") in {"verification_snapshot", "sec_8k_markdown", "form4_xml"}
            if keep_archive:
                gz = path.with_suffix(path.suffix + ".gz")
                if not dry_run:
                    with path.open("rb") as src, gzip.open(gz, "wb") as dst:
                        dst.write(src.read())
                    path.unlink(missing_ok=True)
                action = "archived"
                new_status = "archived"
                output_path = str(gz)
            else:
                if not dry_run:
                    path.unlink(missing_ok=True)
                action = "deleted"
                new_status = "deleted"
        if not dry_run:
            db_execute(
                conn,
                "UPDATE public.cq_source_artifacts SET retention_status=%s, updated_at=now() WHERE artifact_id=%s",
                (new_status, row.get("artifact_id")),
            )
        results.append({"artifact_id": row.get("artifact_id"), "action": action, "output_path": output_path})
    return results


def run(args: argparse.Namespace) -> dict:
    ensure_dirs()
    conn = get_db_conn()
    results = cleanup_artifacts(conn, dry_run=args.dry_run, limit=args.limit)
    details = {"processed": len(results), "dry_run": args.dry_run, "results": results}
    log_run("cq_artifact_cleanup", "success", f"Processed {len(results)} expired CQ artifacts", details=details, conn=conn)
    return details


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Archive/delete expired CQ artifacts")
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--dry-run", action="store_true")
    return p


def main() -> int:
    result = run(build_parser().parse_args())
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
