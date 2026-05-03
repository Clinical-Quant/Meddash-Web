#!/usr/bin/env python3
"""Compose CQ newsletter, tweet drafts, and approval packages from confirmed candidates."""
from __future__ import annotations

import argparse
import json
from typing import Any

from cq_automation_common import (
    CQ_AUTOMATION_ROOT,
    OBSIDIAN_NEWSLETTER_DIR,
    db_fetch_all,
    db_insert_returning,
    ensure_dirs,
    get_db_conn,
    log_run,
    make_content_id,
    utc_stamp,
    write_text_file,
)


def build_tweet_text(candidate: dict[str, Any], confirmation: dict[str, Any]) -> str:
    ticker = candidate.get("ticker") or "TICKER"
    event = candidate.get("event_type") or "catalyst signal"
    date = candidate.get("event_date") or "date not specified"
    source = "SEC 8-K" if candidate.get("source_table") == "cq_catalysts" else "SEC Form 4"
    return (
        f"${ticker} catalyst watch:\n\n"
        f"{candidate.get('company_name') or ticker} disclosed/confirmed: {event}.\n"
        f"Key date: {date}.\n"
        f"Source: {source}, accession {candidate.get('accession_number')}.\n\n"
        f"Verified by Clinical Quant. Not investment advice."
    )


def build_newsletter_section(candidate: dict[str, Any], confirmation: dict[str, Any]) -> str:
    facts = confirmation.get("confirmed_facts_json") or {}
    if isinstance(facts, str):
        try:
            facts = json.loads(facts)
        except Exception:
            facts = {}
    return "\n".join([
        f"### {candidate.get('ticker')} — {candidate.get('event_type')}",
        f"- Company: {candidate.get('company_name') or ''}",
        f"- Catalyst/signal: {candidate.get('event_type')}",
        f"- Date: {candidate.get('event_date') or facts.get('event_date') or 'Not specified'}",
        f"- Why it matters: {confirmation.get('research_summary') or 'Verified source signal.'}",
        f"- Source: {candidate.get('filing_url') or candidate.get('accession_number')}",
        f"- Verification: {confirmation.get('verification_status')}",
        "",
    ])


def render_newsletter(candidates: list[dict[str, Any]], confirmations: list[dict[str, Any]], timestamp: str) -> str:
    by_id = {c.get("candidate_id"): c for c in candidates}
    lines = [
        f"# Clinical Quant Daily Brief — {timestamp}",
        "",
        "## Executive Summary",
        f"- Verified items in this draft: {len(confirmations)}",
        "- All items are source-linked and approval-gated before external posting.",
        "- Not investment advice.",
        "",
        "## Verified Catalysts and Insider Signals",
        "",
    ]
    for conf in confirmations:
        cand = by_id.get(conf.get("candidate_id"), {})
        lines.append(build_newsletter_section(cand, conf))
    lines.extend(["## Sources", ""])
    for conf in confirmations:
        cand = by_id.get(conf.get("candidate_id"), {})
        lines.append(f"- {cand.get('ticker')}: {cand.get('filing_url') or cand.get('accession_number')}")
    return "\n".join(lines)


def render_tweet_drafts(candidates: list[dict[str, Any]], confirmations: list[dict[str, Any]]) -> str:
    by_id = {c.get("candidate_id"): c for c in candidates}
    lines = ["# CQ Tweet/X Drafts", "", "Status: PENDING DR. DON APPROVAL", ""]
    for idx, conf in enumerate(confirmations, start=1):
        cand = by_id.get(conf.get("candidate_id"), candidates[idx - 1] if idx - 1 < len(candidates) else {})
        lines.extend([f"## Draft {idx} — {cand.get('ticker')}", "```text", build_tweet_text(cand, conf), "```", ""])
    return "\n".join(lines)


def render_approval_package(candidates: list[dict[str, Any]], confirmations: list[dict[str, Any]], *, run_id: str, timestamp: str) -> str:
    by_id = {c.get("candidate_id"): c for c in candidates}
    lines = [
        f"# CQ Approval Package — {timestamp}",
        "",
        "Status: PENDING DR. DON APPROVAL",
        f"Run ID: {run_id}",
        f"Candidates reviewed: {len(candidates)}",
        f"Verified candidates: {len(confirmations)}",
        "",
        "---",
        "",
    ]
    for idx, conf in enumerate(confirmations, start=1):
        cand = by_id.get(conf.get("candidate_id"), candidates[idx - 1] if idx - 1 < len(candidates) else {})
        facts = conf.get("confirmed_facts_json") or {}
        if isinstance(facts, str):
            try:
                facts = json.loads(facts)
            except Exception:
                facts = {}
        lines.extend([
            f"## Candidate {idx} — {cand.get('ticker')} / {cand.get('company_name') or ''}",
            "",
            f"Event type: {cand.get('event_type')}",
            f"Verification status: {conf.get('verification_status')}",
            f"Primary source: {cand.get('filing_url') or cand.get('accession_number')}",
            "Secondary sources: see verification JSON / future enrichment",
            "",
            "### Verified Facts",
        ])
        for k, v in facts.items():
            lines.append(f"- {k}: {v}")
        lines.extend([
            "",
            "### Research Summary",
            conf.get("research_summary") or "Confirmed.",
            "",
            "### Newsletter Draft Snippet",
            build_newsletter_section(cand, conf),
            "### Tweet Draft",
            "```text",
            build_tweet_text(cand, conf),
            "```",
            "",
            "### Approval Options",
            "- APPROVE",
            "- REJECT",
            "- REVISE",
            "",
            "---",
            "",
        ])
    return "\n".join(lines)


def load_confirmed(conn, limit: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    confirmations = db_fetch_all(
        conn,
        """
        SELECT * FROM public.cq_research_confirmations
        WHERE verification_status = 'confirmed'
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (limit,),
    )
    ids = [c["candidate_id"] for c in confirmations]
    if not ids:
        return [], []
    candidates = db_fetch_all(
        conn,
        "SELECT * FROM public.cq_selected_candidates WHERE candidate_id = ANY(%s)",
        (ids,),
    )
    return candidates, confirmations


def insert_content_rows(conn, candidates: list[dict[str, Any]], confirmations: list[dict[str, Any]], paths: dict[str, str], dry_run: bool = False) -> int:
    count = 0
    by_id = {c.get("candidate_id"): c for c in candidates}
    for conf in confirmations:
        cand = by_id.get(conf.get("candidate_id"), {})
        for content_type in ("newsletter", "tweet", "approval_package"):
            row = {
                "content_id": make_content_id(conf.get("candidate_id"), content_type),
                "candidate_id": conf.get("candidate_id"),
                "content_type": content_type,
                "title": f"{cand.get('ticker')} — {cand.get('event_type')} ({content_type})",
                "draft_markdown": None,
                "tweet_text": build_tweet_text(cand, conf) if content_type == "tweet" else None,
                "approval_status": "pending_review",
                "posting_destination": "manual_export",
                "output_file_path": paths.get(content_type),
            }
            if not dry_run:
                db_insert_returning(conn, "cq_content_queue", row, conflict="content_id")
            count += 1
    return count


def run(args: argparse.Namespace) -> dict[str, Any]:
    ensure_dirs()
    conn = get_db_conn()
    run_id = f"cq-content-composer-{utc_stamp()}"
    timestamp = utc_stamp()
    candidates, confirmations = load_confirmed(conn, args.limit)
    newsletter = render_newsletter(candidates, confirmations, timestamp)
    tweets = render_tweet_drafts(candidates, confirmations)
    approval = render_approval_package(candidates, confirmations, run_id=run_id, timestamp=timestamp)

    newsletter_path = CQ_AUTOMATION_ROOT / "newsletter-drafts" / f"{timestamp}-cq-newsletter-draft.md"
    newsletter_obsidian = OBSIDIAN_NEWSLETTER_DIR / f"{timestamp}-cq-newsletter-draft.md"
    tweet_path = CQ_AUTOMATION_ROOT / "tweet-drafts" / f"{timestamp}-cq-tweets.md"
    approval_path = CQ_AUTOMATION_ROOT / "approval-packages" / f"{timestamp}-cq-approval-package.md"
    write_text_file(newsletter_path, newsletter)
    write_text_file(newsletter_obsidian, newsletter)
    write_text_file(tweet_path, tweets)
    write_text_file(approval_path, approval)
    paths = {"newsletter": str(newsletter_path), "tweet": str(tweet_path), "approval_package": str(approval_path)}
    content_rows = insert_content_rows(conn, candidates, confirmations, paths, dry_run=args.dry_run)
    details = {
        "confirmed_count": len(confirmations),
        "content_rows": content_rows,
        "dry_run": args.dry_run,
        "newsletter_path": str(newsletter_path),
        "newsletter_obsidian_path": str(newsletter_obsidian),
        "tweet_path": str(tweet_path),
        "approval_package_path": str(approval_path),
    }
    log_run("cq_content_composer", "success", f"Composed CQ content for {len(confirmations)} confirmed candidates", details=details, conn=conn, run_id=run_id)
    return details


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Compose CQ newsletter/tweet/approval drafts")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--dry-run", action="store_true")
    return p


def main() -> int:
    result = run(build_parser().parse_args())
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
