"""
ct_crawler.py — Meddash ClinicalTrials.gov API v2 Crawler
==========================================================
Fetches trial records from the ClinicalTrials.gov REST API v2 and saves
each trial as a raw JSON file to ct_raw_json/{nct_id}.json for ingestion
by ct_ingestion.py (Step 3).

Modes:
    full   — First-time crawl of all ~480k trials. Run overnight.
    delta  — Nightly update: only trials updated in the last N hours.
    query  — Targeted crawl by keyword/condition (for focused KOL briefs).

Usage:
    python ct_crawler.py --mode full
    python ct_crawler.py --mode delta --hours 24
    python ct_crawler.py --mode query --query "KRAS lung cancer"
    python ct_crawler.py --mode query --query "HER2 breast cancer" --max 500

Resume:
    Crawl state is saved to ct_crawl_state.json after every page.
    If the process is interrupted, re-run the same command to resume.
    Use --no-resume to force a fresh crawl.

Rate limiting:
    100ms between requests by default.
    Automatic exponential backoff on HTTP 429/503 (up to 5 retries).
"""

import argparse
import json
import logging
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

# ── Path resolution via shared DevOps module ──────────────────────────────
DEVOPS_DIR = Path(__file__).resolve().parent.parent / "07_DevOps_Observability"
sys.path.insert(0, str(DEVOPS_DIR))
ENGINE_DIR = Path(__file__).resolve().parent  # For local imports

from paths import DB_PATHS, SUMMARY_DIR, STATE_DIR, ENGINE_PATHS
try:
    import telegram_notifier
except ImportError:
    telegram_notifier = None

# ── Configuration ─────────────────────────────────────────────────────────────

BASE_URL    = "https://clinicaltrials.gov/api/v2/studies"
RAW_DIR     = str(ENGINE_DIR / "ct_raw_json")  # MDP3-SWIP1: cross-platform path
STATE_FILE  = str(STATE_DIR / "ct_crawl_state.json")  # MDP3-SWIP1: shared state dir
PAGE_SIZE   = 100          # Max allowed by CT.gov API v2
REQUEST_DELAY_MS = 100     # Polite delay between requests (ms)
MAX_RETRIES = 5            # For 429/503 backoff

# Globals for Advanced Frontend UI Filtering
GLOBAL_PHASES = ""
GLOBAL_STATUSES = ""
GLOBAL_DATE_FROM = ""
GLOBAL_DATE_TO = ""

# Fields requested from the API — covers all 11 schema layers
# Full protocolSection + resultsSection overview
FIELDS = ",".join([
    "protocolSection.identificationModule",
    "protocolSection.statusModule",
    "protocolSection.sponsorCollaboratorsModule",
    "protocolSection.descriptionModule",
    "protocolSection.conditionsModule",
    "protocolSection.designModule",
    "protocolSection.armsInterventionsModule",
    "protocolSection.outcomesModule",
    "protocolSection.eligibilityModule",
    "protocolSection.contactsLocationsModule",
    "protocolSection.referencesModule",
    "resultsSection.outcomeMeasuresModule",
    "resultsSection.adverseEventsModule",
])

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(str(ENGINE_DIR / "ct_crawler.log"), encoding="utf-8"),
    ]
)
log = logging.getLogger(__name__)


# ── State management ──────────────────────────────────────────────────────────

def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_state(state: dict) -> None:
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


# ── HTTP fetch with retry ─────────────────────────────────────────────────────

def fetch_page(url: str) -> dict:
    """
    Fetch a single API page. Retries on 429/503 with exponential backoff.
    Returns parsed JSON dict.
    """
    delay = 2.0
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={"Accept": "application/json", "User-Agent": "Meddash/1.0"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                log.warning(f"HTTP {e.code} — retrying in {delay:.0f}s (attempt {attempt}/{MAX_RETRIES})")
                time.sleep(delay)
                delay *= 2
            else:
                raise
        except urllib.error.URLError as e:
            log.warning(f"Network error: {e.reason} — retrying in {delay:.0f}s")
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f"Failed to fetch {url} after {MAX_RETRIES} retries")


# ── Raw JSON storage ──────────────────────────────────────────────────────────

def save_trial_json(study: dict) -> str | None:
    """
    Save a single trial's raw JSON to ct_raw_json/{nct_id}.json.
    Returns the file path, or None if nct_id cannot be found.
    """
    try:
        nct_id = (
            study.get("protocolSection", {})
                 .get("identificationModule", {})
                 .get("nctId", "")
        )
        if not nct_id:
            return None
        path = os.path.join(RAW_DIR, f"{nct_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(study, f)
        return path
    except Exception as e:
        log.error(f"Failed to save trial JSON: {e}")
        return None


# ── URL builders ──────────────────────────────────────────────────────────────

def build_full_url(page_token: str | None = None) -> str:
    params: dict = {
        "pageSize": PAGE_SIZE,
        "fields": FIELDS,
        "format": "json",
    }
    if page_token:
        params["pageToken"] = page_token
    return f"{BASE_URL}?{urllib.parse.urlencode(params)}"


def build_delta_url(since_hours: int, page_token: str | None = None) -> str:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
    date_str = cutoff.strftime("%Y-%m-%d")
    params: dict = {
        "pageSize": PAGE_SIZE,
        "fields": FIELDS,
        "format": "json",
        "filter.advanced": f"AREA[LastUpdatePostDate]RANGE[{date_str},MAX]",
    }
    if page_token:
        params["pageToken"] = page_token
    return f"{BASE_URL}?{urllib.parse.urlencode(params)}"


def build_query_url(query: str, page_token: str | None = None) -> str:
    params: dict = {
        "pageSize": PAGE_SIZE,
        "fields": FIELDS,
        "format": "json",
    }
    
    if query:
        params["query.cond"] = query

    if GLOBAL_STATUSES:
        params["filter.overallStatus"] = GLOBAL_STATUSES
        
    adv_filters = []
    if GLOBAL_PHASES:
        phase_list = GLOBAL_PHASES.split(",")
        phase_str = " OR ".join([f"AREA[Phase]{p.strip()}" for p in phase_list if p.strip()])
        if phase_str:
            adv_filters.append(f"({phase_str})")
            
    if GLOBAL_DATE_FROM:
        d_to = GLOBAL_DATE_TO if GLOBAL_DATE_TO else "MAX"
        adv_filters.append(f"AREA[LastUpdatePostDate]RANGE[{GLOBAL_DATE_FROM},{d_to}]")
        
    if adv_filters:
        params["filter.advanced"] = " AND ".join(adv_filters)

    if page_token:
        params["pageToken"] = page_token
    return f"{BASE_URL}?{urllib.parse.urlencode(params)}"


# ── Core crawl loop ───────────────────────────────────────────────────────────

def crawl(
    url_builder,
    state_key: str,
    resume: bool = True,
    max_trials: int = 0,
) -> dict:
    """
    Generic paginated crawl loop.

    Args:
        url_builder: Callable(page_token) -> url str
        state_key:   Key name for persisting state in ct_crawl_state.json
        resume:      If True, resume from last saved page token
        max_trials:  Stop after this many trials (0 = no limit)

    Returns:
        Summary dict with counts.
    """
    os.makedirs(RAW_DIR, exist_ok=True)
    state = load_state() if resume else {}

    page_token: str | None = state.get(state_key)
    saved        = state.get(f"{state_key}_saved", 0)
    skipped      = state.get(f"{state_key}_skipped", 0)
    pages_done   = state.get(f"{state_key}_pages", 0)

    if page_token:
        log.info(f"Resuming {state_key} from page token (saved so far: {saved:,})")
    else:
        log.info(f"Starting fresh crawl: {state_key}")

    while True:
        url  = url_builder(page_token)
        data = fetch_page(url)

        studies = data.get("studies", [])
        if not studies:
            break

        for study in studies:
            path = save_trial_json(study)
            if path:
                saved += 1
            else:
                skipped += 1

        pages_done += 1
        page_token = data.get("nextPageToken")

        # Progress log every 10 pages
        if pages_done % 10 == 0:
            log.info(f"Pages: {pages_done:,} | Saved: {saved:,} | Skipped: {skipped}")

        # Save state after every page (crash-safe)
        state.update({
            state_key:                  page_token,
            f"{state_key}_saved":       saved,
            f"{state_key}_skipped":     skipped,
            f"{state_key}_pages":       pages_done,
            f"{state_key}_last_run":    datetime.now(timezone.utc).isoformat(),
        })
        save_state(state)

        if not page_token:
            log.info("Reached last page — crawl complete.")
            break

        if max_trials and saved >= max_trials:
            log.info(f"Reached --max {max_trials} trials. Stopping.")
            break

        time.sleep(REQUEST_DELAY_MS / 1000.0)

    # Clear the page token so next run starts fresh for this mode
    if not page_token:
        state[state_key] = None
        save_state(state)

    return {"saved": saved, "skipped": skipped, "pages": pages_done}


# ── CLI entry point ───────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Meddash ClinicalTrials.gov Crawler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--mode", choices=["full", "delta", "query"], required=True,
        help="Crawl mode: full (all trials), delta (updated since N hours), query (condition search)"
    )
    parser.add_argument(
        "--hours", type=int, default=24,
        help="For --mode delta: how many hours back to look (default: 24)"
    )
    parser.add_argument(
        "--query", type=str, default="",
        help="For --mode query: condition/keyword search string"
    )
    parser.add_argument(
        "--max", type=int, default=0,
        help="Stop after this many trials (0 = no limit)"
    )
    parser.add_argument(
        "--no-resume", action="store_true",
        help="Ignore saved crawl state and start from scratch"
    )
    
    # Advanced UI Target Parameters
    parser.add_argument("--phases", type=str, default="")
    parser.add_argument("--statuses", type=str, default="")
    parser.add_argument("--date_from", type=str, default="")
    parser.add_argument("--date_to", type=str, default="")
    # MDP3-SWIP1: Campaign tracking
    parser.add_argument("--pull-id", type=str, default=None,
        help="Campaign Sandbox Pull ID for tracking")
    
    args = parser.parse_args()

    # Inject into globals
    global GLOBAL_PHASES, GLOBAL_STATUSES, GLOBAL_DATE_FROM, GLOBAL_DATE_TO
    GLOBAL_PHASES = args.phases
    GLOBAL_STATUSES = args.statuses
    GLOBAL_DATE_FROM = args.date_from
    GLOBAL_DATE_TO = args.date_to

    resume = not args.no_resume
    start_time = time.time()

    print(f"\n  Meddash CT Crawler — mode: {args.mode}")
    print(f"  Raw JSON output: {os.path.abspath(RAW_DIR)}")
    print("  " + "─" * 56)

    if telegram_notifier:
        telegram_notifier.send_alert(f"CT Crawler Started%0A%0AMode: {args.mode.upper()}%0ATarget: ClinicalTrials.gov API v2", level="info")

    try:
        if args.mode == "full":
            result = crawl(
                url_builder=build_full_url,
                state_key="full",
                resume=resume,
                max_trials=args.max,
            )

        elif args.mode == "delta":
            log.info(f"Delta mode: fetching trials updated in last {args.hours}h")
            result = crawl(
                url_builder=lambda tok: build_delta_url(args.hours, tok),
                state_key=f"delta_{args.hours}h",
                resume=False,   # Delta always starts fresh (it's a date filter)
                max_trials=args.max,
            )

        elif args.mode == "query":
            if not args.query:
                parser.error("--mode query requires --query TEXT")
            log.info(f"Query mode: '{args.query}'")
            result = crawl(
                url_builder=lambda tok: build_query_url(args.query, tok),
                state_key=f"query_{args.query[:30].replace(' ', '_')}",
                resume=resume,
                max_trials=args.max,
            )
        else:
            parser.error(f"Unknown mode: {args.mode}")
            return

        elapsed = time.time() - start_time
        minutes, seconds = divmod(int(elapsed), 60)

        print(f"\n  ✅ Crawl complete in {minutes}m {seconds}s")
        print(f"  Trials saved: {result['saved']:,}")
        print(f"  Skipped:      {result['skipped']:,}")
        print(f"  Pages fetched:{result['pages']:,}")
        # ── MDP3-SWIP1: Write structured JSON summary ─────────────────────────
        SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
        summary = {
            "engine": "ct_data",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": args.mode,
            "query": args.query if args.mode == "query" else None,
            "hours": args.hours if args.mode == "delta" else None,
            "status": "success",
            "trials_saved": result["saved"],
            "trials_skipped": result["skipped"],
            "pages_fetched": result["pages"],
            "duration_seconds": round(elapsed, 2),
        }
        summary_path = SUMMARY_DIR / "ct_crawler_summary.json"
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)
        log.info(f"CT Crawler summary written to {summary_path}")

        print(f"\n  Next step: python ct_ingestion.py\n")

        if telegram_notifier:
            telegram_notifier.send_alert(f"CT Crawler Complete\n\nMode: {args.mode.upper()}\nSaved: {result['saved']:,} trials\nTime: {minutes}m {seconds}s", level="success")

    except Exception as e:
        log.error(f"CT Crawler crashed: {e}")
        # MDP3-SWIP1: Write failure summary JSON
        try:
            SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
            fail_summary = {
                "engine": "ct_data",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "mode": args.mode if hasattr(args, "mode") else "unknown",
                "status": "failure",
                "error": str(e),
            }
            with open(SUMMARY_DIR / "ct_crawler_summary.json", "w") as f:
                json.dump(fail_summary, f, indent=2)
        except Exception:
            pass
        if telegram_notifier:
            telegram_notifier.send_alert(f"CT CRAWLER CRASHED\n\nMode: {args.mode.upper()}\nError: {str(e)[:200]}", level="error")
        raise


if __name__ == "__main__":
    main()
