"""
ct_query_engine.py — Structured CT.gov Query Runner with TA Profiles

Runs targeted CT.gov API v2 searches using TA search profiles.
Crawls trials, saves raw JSON, ingests to Supabase, logs every run.

Usage:
    # Run a predefined profile
    python ct_query_engine.py --profile glp1_metabolic

    # Run custom search (natural language from Meddash Manager)
    python ct_query_engine.py --custom "GLP-1" --phase PHASE3

    # Run all conditions in a profile
    python ct_query_engine.py --profile glp1_metabolic --all-conditions

    # Dry run (show what would be searched)
    python ct_query_engine.py --profile glp1_metabolic --dry-run

    # List available profiles
    python ct_query_engine.py --list
"""

import os
import sys
import json
import time
import argparse
import logging
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

# ── Path setup ──
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "07_DevOps_Observability"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from supabase_writer import get_pg_engine, upsert_row
from ta_search_profiles import (
    get_profile, list_profiles, build_query_params, build_custom_params,
    build_advanced_filter, resolve_date_range
)
from sqlalchemy import text

# ── Constants ──
API_BASE = "https://clinicaltrials.gov/api/v2/studies"
RAW_DIR = Path(__file__).resolve().parent / "ct_raw_json"
RAW_DIR.mkdir(parents=True, exist_ok=True)
PAGE_SIZE = 100
REQUEST_DELAY = 0.1  # 100ms between requests

# ── Logging ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(str(Path(__file__).resolve().parent / "ct_query_engine.log"), encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)


def fetch_page(params: dict, page_token: str = None) -> dict:
    """Fetch a single page from CT.gov API v2."""
    if page_token:
        params["pageToken"] = page_token

    query_string = urllib.parse.urlencode(params)
    url = f"{API_BASE}?{query_string}"

    req = urllib.request.Request(url, headers={"User-Agent": "Meddash-CQ/2.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


# Run-specific subdirectory — set by run_profile/run_custom at the start of each run
_current_raw_dir = RAW_DIR


def save_trial_json(study: dict) -> str | None:
    """Save a trial JSON to the current run's raw dir. Returns the file path or None."""
    try:
        ps = study.get("protocolSection", {})
        ident = ps.get("identificationModule", {})
        nct_id = ident.get("nctId", "")
        if not nct_id:
            return None
        filepath = _current_raw_dir / f"{nct_id}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(study, f)
        return str(filepath)
    except Exception as e:
        log.warning(f"Failed to save JSON: {e}")
        return None


def crawl_query(params: dict, profile_name: str) -> dict:
    """Crawl all matching trials for a query. Returns stats."""
    total_found = 0
    saved = 0
    skipped = 0
    page_token = None
    pages = 0

    while True:
        data = fetch_page(params, page_token)
        studies = data.get("studies", [])
        total_count = data.get("totalCount", 0)
        page_token = data.get("nextPageToken")

        if pages == 0:
            log.info(f"  Total found: {total_count:,}")

        for study in studies:
            saved += 1 if save_trial_json(study) else 0
            skipped += 1 if not save_trial_json(study) else 0

        pages += 1
        log.info(f"  Page {pages}: {len(studies)} studies (saved: {saved:,}, total: {total_count:,})")

        if not page_token or saved >= int(params.get("pageSize", 500)):
            break

        time.sleep(REQUEST_DELAY)

    return {
        "total_found": total_count if total_count else saved,
        "saved": saved,
        "skipped": skipped,
        "pages": pages,
    }


def log_run(pg_conn, profile_name: str, label: str, condition: str,
            filter_advanced: str, total_found: int, total_ingested: int,
            date_start: str, date_end: str, elapsed: float,
            status: str, error: str = ""):
    """Log a query run to ct_query_log table in Supabase."""
    upsert_row(pg_conn, "ct_query_log", {
        "profile_name": profile_name,
        "label": label,
        "condition_searched": condition,
        "filter_advanced": filter_advanced,
        "total_found": total_found,
        "total_ingested": total_ingested,
        "date_range_start": date_start,
        "date_range_end": date_end,
        "elapsed_seconds": round(elapsed, 1),
        "status": status,
        "error_message": error,
    }, pk="id")
    pg_conn.commit()


def run_profile(profile_name: str, all_conditions: bool = False, dry_run: bool = False):
    """Run a TA search profile."""
    global _current_raw_dir
    
    profile = get_profile(profile_name)
    conditions = profile["conditions"]
    label = profile["label"]

    # Create run-specific raw directory
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    _current_raw_dir = RAW_DIR / run_id
    _current_raw_dir.mkdir(parents=True, exist_ok=True)

    if not conditions:
        log.error(f"Profile '{profile_name}' has no conditions defined")
        return

    # Determine which conditions to search
    search_conditions = conditions if all_conditions else [conditions[0]]

    adv_filter = build_advanced_filter(profile)
    date_start, date_end = resolve_date_range(profile.get("date_range", ""))

    log.info(f"=== CT QUERY ENGINE ===")
    log.info(f"Profile: {profile_name} ({label})")
    log.info(f"Conditions: {search_conditions}")
    log.info(f"Filter: {adv_filter or '(none)'}")
    log.info(f"Date range: {date_start} to {date_end}" if date_start else "Date range: (none)")

    if dry_run:
        for cond in search_conditions:
            params = build_query_params(profile, condition_override=cond)
            print(f"\nCondition: {cond}")
            for k, v in params.items():
                print(f"  {k}: {v}")
        return

    engine = get_pg_engine()
    pg_conn = engine.connect()

    grand_total = 0
    grand_ingested = 0
    start_time = time.time()
    overall_status = "success"

    for condition in search_conditions:
        log.info(f"\n--- Searching: {condition} ---")
        params = build_query_params(profile, condition_override=condition)

        try:
            stats = crawl_query(params, profile_name)
            grand_total += stats["total_found"]
            grand_ingested += stats["saved"]

            # Log this condition's run
            log_run(pg_conn, profile_name, label, condition,
                    adv_filter, stats["total_found"], stats["saved"],
                    date_start, date_end,
                    time.time() - start_time, "success")

        except Exception as e:
            log.error(f"Failed searching '{condition}': {e}")
            try:
                log_run(pg_conn, profile_name, label, condition,
                        adv_filter, 0, 0, date_start, date_end,
                        time.time() - start_time, "error", str(e)[:500])
            except Exception:
                pass
            overall_status = "partial"

    pg_conn.close()
    elapsed = time.time() - start_time

    log.info(f"\n=== COMPLETE: {grand_total:,} found, {grand_ingested:,} saved, {elapsed:.1f}s ===")

    # Run ingestion if any trials were saved
    if grand_ingested > 0:
        log.info("Running CT ingestion to Supabase (in-process)...")
        try:
            from ct_ingestion import ingest_all
            result = ingest_all(raw_dir=str(_current_raw_dir))
            log.info(f"Ingestion complete: {result.get('processed', 0)} processed, {result.get('errors', 0)} errors")
        except Exception as ingest_err:
            log.error(f"Ingestion failed: {str(ingest_err)[:200]}")

    return {
        "profile": profile_name,
        "total_found": grand_total,
        "total_ingested": grand_ingested,
        "elapsed": elapsed,
        "status": overall_status,
    }


def run_custom(condition: str, phase: list[str] = None, status: list[str] = None,
               sponsor_class: str = "", study_type: str = "",
               date_range: str = "", intervention: str = "",
               max_results: int = 500, dry_run: bool = False):
    """Run a custom ad-hoc search. Entry point for natural language queries."""
    global _current_raw_dir
    
    profile_name = "_custom"
    label = f"Custom: {condition}"

    # Create run-specific raw directory
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    _current_raw_dir = RAW_DIR / run_id
    _current_raw_dir.mkdir(parents=True, exist_ok=True)

    params = build_custom_params(
        condition=condition,
        phase=phase,
        status=status,
        sponsor_class=sponsor_class,
        study_type=study_type,
        date_range=date_range,
        intervention=intervention,
        max_results=max_results,
    )

    adv_filter = params.get("filter.advanced", "")
    date_start, date_end = resolve_date_range(date_range)

    log.info(f"=== CUSTOM CT QUERY ===")
    log.info(f"Condition: {condition}")
    log.info(f"Filter: {adv_filter or '(none)'}")
    log.info(f"Date range: {date_start} to {date_end}" if date_start else "Date range: (none)")

    if dry_run:
        print(f"\nCustom search params:")
        for k, v in params.items():
            print(f"  {k}: {v}")
        return

    engine = get_pg_engine()
    pg_conn = engine.connect()
    start_time = time.time()

    try:
        stats = crawl_query(params, profile_name)
        elapsed = time.time() - start_time

        log_run(pg_conn, profile_name, label, condition,
                adv_filter, stats["total_found"], stats["saved"],
                date_start, date_end, elapsed, "success")

        log.info(f"\n=== COMPLETE: {stats['total_found']:,} found, {stats['saved']:,} saved, {elapsed:.1f}s ===")

        if stats["saved"] > 0:
            log.info("Running CT ingestion to Supabase (in-process)...")
            try:
                from ct_ingestion import ingest_all
                result = ingest_all(raw_dir=str(_current_raw_dir))
                log.info(f"Ingestion complete: {result.get('processed', 0)} processed, {result.get('errors', 0)} errors, {result.get('elapsed_s', 0)}s")
            except Exception as ingest_err:
                log.error(f"Ingestion failed: {str(ingest_err)[:200]}")

        pg_conn.close()

        return {
            "condition": condition,
            "total_found": stats["total_found"],
            "total_ingested": stats["saved"],
            "elapsed": elapsed,
            "status": "success",
        }

    except Exception as e:
        elapsed = time.time() - start_time
        log.error(f"Custom search failed: {e}")
        try:
            log_run(pg_conn, profile_name, label, condition,
                    adv_filter, 0, 0, date_start, date_end, elapsed, "error", str(e)[:500])
        except Exception:
            pass  # Connection may already be closed
        try:
            pg_conn.close()
        except Exception:
            pass
        return {"condition": condition, "total_found": 0, "total_ingested": 0, "elapsed": elapsed, "status": "error"}


# ── CLI ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CT.gov Query Engine with TA Profiles")
    parser.add_argument("--profile", type=str, help="TA profile name to run")
    parser.add_argument("--custom", type=str, help="Custom condition search")
    parser.add_argument("--phase", nargs="*", help="Phase filter (PHASE1, PHASE2, PHASE3, PHASE4)")
    parser.add_argument("--status", nargs="*", help="Status filter (RECRUITING, COMPLETED, etc.)")
    parser.add_argument("--sponsor-class", type=str, default="", help="Sponsor class (INDUSTRY, NIH, ACADEMIC)")
    parser.add_argument("--study-type", type=str, default="", help="Study type (INTERVENTIONAL, OBSERVATIONAL)")
    parser.add_argument("--date-range", type=str, default="", help="Date range (last_90_days or YYYY-MM-DD,YYYY-MM-DD)")
    parser.add_argument("--intervention", type=str, default="", help="Intervention search term")
    parser.add_argument("--max-results", type=int, default=500, help="Max results")
    parser.add_argument("--all-conditions", action="store_true", help="Run all conditions in profile")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be searched")
    parser.add_argument("--list", action="store_true", help="List available profiles")
    args = parser.parse_args()

    if args.list:
        print("Available TA Search Profiles:")
        for p in list_profiles():
            if p["name"] == "_custom":
                continue
            print(f"  {p['name']:30s} - {p['label']}")
            if p["conditions"]:
                print(f"    Conditions: {', '.join(p['conditions'][:4])}")
        sys.exit(0)

    if args.profile:
        result = run_profile(args.profile, all_conditions=args.all_conditions, dry_run=args.dry_run)
        if result:
            print(f"\nResult: {result}")

    elif args.custom:
        result = run_custom(
            condition=args.custom,
            phase=args.phase,
            status=args.status,
            sponsor_class=args.sponsor_class,
            study_type=args.study_type,
            date_range=args.date_range,
            intervention=args.intervention,
            max_results=args.max_results,
            dry_run=args.dry_run,
        )
        if result:
            print(f"\nResult: {result}")

    else:
        parser.print_help()