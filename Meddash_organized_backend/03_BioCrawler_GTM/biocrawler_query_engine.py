"""
biocrawler_query_engine.py — Granular BioCrawler Search Runner

Searches CT.gov for biotech company sponsors by TA profile, enriches with
SEC EDGAR financial data, ingests to Supabase, logs every run.

BioCrawler is LEAN: CT.gov sponsor extraction + SEC EDGAR only.
No hiring signals, no CRM, no website enrichment (decoupled in SEQ-0023).

Usage:
    python biocrawler_query_engine.py --profile glp1_metabolic
    python biocrawler_query_engine.py --custom "GLP-1" --phase PHASE3
    python biocrawler_query_engine.py --profile glp1_metabolic --dry-run
    python biocrawler_query_engine.py --list
"""

import os
import sys
import json
import time
import argparse
import logging
import urllib.request
import urllib.parse
import re
from datetime import datetime, timezone
from pathlib import Path

# ── Path setup ──
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "07_DevOps_Observability"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from supabase_writer import get_pg_engine, upsert_row
from biocrawler_search_profiles import (
    get_profile, list_profiles, build_ctgov_params, build_edgar_params,
    build_custom_params, build_ctgov_advanced_filter, resolve_date_range
)
from sqlalchemy import text

# ── Constants ──
CT_GOV_BASE = "https://clinicaltrials.gov/api/v2/studies"
EDGAR_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
EDGAR_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
EDGAR_TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json"
EDGAR_HEADERS = {"User-Agent": "Meddash-CQ research@meddash.ai"}
REQUEST_DELAY = 0.2

# ── Logging ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(str(Path(__file__).resolve().parent / "biocrawler_query_engine.log"), encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)


def fetch_ctgov_page(params: dict, page_token: str = None) -> dict:
    """Fetch a page from CT.gov API v2."""
    if page_token:
        params["pageToken"] = page_token
    query_string = urllib.parse.urlencode(params)
    url = f"{CT_GOV_BASE}?{query_string}"
    req = urllib.request.Request(url, headers={"User-Agent": "Meddash-CQ/2.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def generate_slug(company_name: str) -> str:
    """Standardize company name to slug for dedup."""
    slug = company_name.lower().strip()
    suffixes = [r'\binc\.?\b', r'\bllc\.?\b', r'\bcorp\.?\b', r'\bltd\.?\b', r'\bco\.?\b', r'\bcorporation\b', r'\blimited\b']
    for suffix in suffixes:
        slug = re.sub(suffix, '', slug)
    slug = re.sub(r'[^\w\s]', '', slug)
    return ' '.join(slug.split())


def extract_sponsors_from_ctgov(params: dict) -> list[dict]:
    """Extract unique sponsors from CT.gov trial results."""
    sponsors = []
    seen_slugs = set()
    page_token = None
    total_found = 0

    while True:
        data = fetch_ctgov_page(params, page_token)
        studies = data.get("studies", [])
        total_count = data.get("totalCount", 0)
        page_token = data.get("nextPageToken")

        for study in studies:
            ps = study.get("protocolSection", {})
            sponsor_mod = ps.get("sponsorCollaboratorsModule", {})
            lead_sponsor = sponsor_mod.get("leadSponsor", {})
            sponsor_name = lead_sponsor.get("name", "")
            sponsor_class = lead_sponsor.get("class", "")

            if not sponsor_name:
                continue

            slug = generate_slug(sponsor_name)
            if slug in seen_slugs:
                continue
            seen_slugs.add(slug)

            # Extract trial info
            id_mod = ps.get("identificationModule", {})
            nct_id = id_mod.get("nctId", "")
            conditions = ps.get("conditionsModule", {}).get("conditions", [])
            design = ps.get("designModule", {})
            phases = design.get("phases", [])
            status_mod = ps.get("statusModule", {})
            overall_status = status_mod.get("overallStatus", "")
            loc_mod = ps.get("contactsLocationsModule", {})
            locations = loc_mod.get("locations", [])
            country = locations[0].get("country", "") if locations else ""

            sponsors.append({
                "company_slug": slug,
                "company_name": sponsor_name,
                "primary_indication": conditions[0] if conditions else "",
                "trial_phases": ", ".join(phases) if phases else "",
                "trial_nct_id": nct_id,
                "country": country,
                "sponsor_class": sponsor_class,
                "recent_funding_signal": 0,
                "active_hiring_signal": 0,
                "tier": "C",
                "ticker": None,
            })

        if not page_token or len(sponsors) >= int(params.get("pageSize", 200)):
            break
        time.sleep(REQUEST_DELAY)

    log.info(f"  Extracted {len(sponsors)} unique sponsors from {total_count} trials")
    return sponsors, total_count


def fetch_edgar_filings(company_name: str, edgar_params: dict) -> dict:
    """Search SEC EDGAR for filings by company name."""
    params = edgar_params.copy()
    params["entityName"] = company_name
    # Remove empty params
    params = {k: v for k, v in params.items() if v}

    try:
        query_string = urllib.parse.urlencode(params)
        url = f"{EDGAR_SEARCH_URL}?{query_string}"
        req = urllib.request.Request(url, headers=EDGAR_HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            hits = data.get("hits", {}).get("hits", [])
            total = data.get("hits", {}).get("total", {}).get("value", 0)
            return {"found": total, "filings": hits[:5]}
    except Exception as e:
        log.warning(f"  EDGAR search failed for {company_name}: {e}")
        return {"found": 0, "filings": []}


def enrich_with_edgar(sponsors: list[dict], edgar_params: dict) -> int:
    """Enrich sponsors with SEC EDGAR filing data. Returns count enriched."""
    enriched = 0
    for sponsor in sponsors:
        edgar_result = fetch_edgar_filings(sponsor["company_name"], edgar_params)
        if edgar_result["found"] > 0:
            sponsor["recent_funding_signal"] = 1  # Has recent SEC filings
            sponsor["tier"] = "B"  # Upgrade tier if has filings
            enriched += 1
            log.info(f"  EDGAR: {sponsor['company_name']} — {edgar_result['found']} filings found")
        time.sleep(REQUEST_DELAY)

    # Reclassify tiers
    for sponsor in sponsors:
        if sponsor["recent_funding_signal"] == 1:
            sponsor["tier"] = "B" if sponsor["tier"] == "C" else sponsor["tier"]

    log.info(f"  EDGAR enrichment: {enriched}/{len(sponsors)} companies have recent filings")
    return enriched


def ingest_to_supabase(sponsors: list[dict]) -> dict:
    """Upsert sponsors to biotech_leads table in Supabase."""
    engine = get_pg_engine()
    conn = engine.connect()

    ingested = 0
    errors = 0

    for sponsor in sponsors:
        try:
            upsert_row(conn, "biotech_leads", {
                "company_slug": sponsor["company_slug"],
                "company_name": sponsor["company_name"],
                "primary_indication": sponsor["primary_indication"],
                "trial_phases": sponsor["trial_phases"],
                "trial_nct_id": sponsor["trial_nct_id"],
                "country": sponsor["country"],
                "website_url": None,
                "recent_funding_signal": sponsor["recent_funding_signal"],
                "active_hiring_signal": sponsor["active_hiring_signal"],
                "tier": sponsor["tier"],
                "ticker": sponsor.get("ticker"),
            }, pk="company_slug")
            ingested += 1
        except Exception as e:
            errors += 1
            conn.rollback()
            if errors <= 3:
                log.warning(f"  Failed to upsert {sponsor['company_name']}: {str(e)[:60]}")

    conn.commit()
    conn.close()

    return {"ingested": ingested, "errors": errors}


def log_run(pg_conn, profile_name: str, label: str, condition: str,
            ctgov_filter: str, edgar_query: str,
            companies_found: int, companies_ingested: int, edgar_filings: int,
            date_start: str, date_end: str, elapsed: float,
            status: str, error: str = ""):
    """Log a BioCrawler run to biocrawler_query_log table."""
    try:
        upsert_row(pg_conn, "biocrawler_query_log", {
            "profile_name": profile_name,
            "label": label,
            "condition_searched": condition,
            "ctgov_filter": ctgov_filter,
            "edgar_query": edgar_query,
            "companies_found": companies_found,
            "companies_ingested": companies_ingested,
            "edgar_filings_found": edgar_filings,
            "date_range_start": date_start,
            "date_range_end": date_end,
            "elapsed_seconds": round(elapsed, 1),
            "status": status,
            "error_message": error,
        }, pk="id")
        pg_conn.commit()
    except Exception:
        pass


def run_profile(profile_name: str, dry_run: bool = False):
    """Run a BioCrawler search profile."""
    profile = get_profile(profile_name)
    conditions = profile["ctgov_conditions"]
    label = profile["label"]

    if not conditions:
        log.error(f"Profile '{profile_name}' has no conditions")
        return

    condition = conditions[0]
    ct_params = build_ctgov_params(profile)
    edgar_params = build_edgar_params(profile)
    adv_filter = ct_params.get("filter.advanced", "")
    date_start, date_end = resolve_date_range(profile.get("ctgov_date_range", ""))

    log.info(f"=== BIOCRAWLER QUERY ENGINE ===")
    log.info(f"Profile: {profile_name} ({label})")
    log.info(f"Condition: {condition}")
    log.info(f"CT.gov filter: {adv_filter or '(none)'}")
    log.info(f"EDGAR query: {edgar_params.get('q', '(none)')}")

    if dry_run:
        print(f"\nProfile: {label}")
        print(f"\nCT.gov params: {json.dumps(ct_params, indent=2)}")
        print(f"\nEDGAR params: {json.dumps(edgar_params, indent=2)}")
        return

    start_time = time.time()
    engine = get_pg_engine()

    try:
        # Step 1: Extract sponsors from CT.gov
        log.info(f"\n--- Step 1: CT.gov Sponsor Extraction ---")
        sponsors, total_trials = extract_sponsors_from_ctgov(ct_params)

        if not sponsors:
            log.info("No sponsors found.")
            pg_conn = engine.connect()
            log_run(pg_conn, profile_name, label, condition, adv_filter,
                    edgar_params.get("q", ""), 0, 0, 0, date_start, date_end,
                    time.time() - start_time, "success", "No sponsors found")
            pg_conn.close()
            return {"profile": profile_name, "companies_found": 0, "status": "success"}

        # Step 2: Enrich with SEC EDGAR
        log.info(f"\n--- Step 2: SEC EDGAR Enrichment ---")
        edgar_count = enrich_with_edgar(sponsors, edgar_params)

        # Step 3: Ingest to Supabase
        log.info(f"\n--- Step 3: Supabase Ingestion ---")
        stats = ingest_to_supabase(sponsors)

        elapsed = time.time() - start_time
        log.info(f"\n=== COMPLETE: {len(sponsors)} companies found, {stats['ingested']} ingested, {edgar_count} EDGAR-enriched, {elapsed:.1f}s ===")

        # Log run
        pg_conn = engine.connect()
        log_run(pg_conn, profile_name, label, condition, adv_filter,
                edgar_params.get("q", ""), len(sponsors), stats["ingested"],
                edgar_count, date_start, date_end, elapsed, "success")
        pg_conn.close()

        return {
            "profile": profile_name,
            "companies_found": len(sponsors),
            "companies_ingested": stats["ingested"],
            "edgar_enriched": edgar_count,
            "errors": stats["errors"],
            "elapsed": elapsed,
            "status": "success",
        }

    except Exception as e:
        elapsed = time.time() - start_time
        log.error(f"BioCrawler query failed: {e}")
        try:
            pg_conn = engine.connect()
            log_run(pg_conn, profile_name, label, condition, adv_filter,
                    edgar_params.get("q", ""), 0, 0, 0, date_start, date_end,
                    elapsed, "error", str(e)[:500])
            pg_conn.close()
        except:
            pass
        return {"profile": profile_name, "companies_found": 0, "status": "error"}


def run_custom(condition: str, phase: list[str] = None, status: list[str] = None,
               sponsor_class: str = "INDUSTRY", study_type: str = "INTERVENTIONAL",
               ctgov_date_range: str = "last_90_days",
               edgar_filing_types: list[str] = None,
               edgar_date_range: str = "last_365_days",
               max_results: int = 200, dry_run: bool = False):
    """Run a custom ad-hoc BioCrawler search."""
    profile_name = "_custom"
    label = f"Custom: {condition}"

    result = build_custom_params(
        condition=condition, phase=phase, status=status,
        sponsor_class=sponsor_class, study_type=study_type,
        ctgov_date_range=ctgov_date_range,
        edgar_filing_types=edgar_filing_types,
        edgar_date_range=edgar_date_range,
        max_results=max_results,
    )

    ct_params = result["ctgov"]
    edgar_params = result["edgar"]
    profile = result["profile"]
    adv_filter = ct_params.get("filter.advanced", "")
    date_start, date_end = resolve_date_range(ctgov_date_range)

    log.info(f"=== CUSTOM BIOCRAWLER QUERY ===")
    log.info(f"Condition: {condition}")
    log.info(f"CT.gov filter: {adv_filter or '(none)'}")

    if dry_run:
        print(f"\nCT.gov params: {json.dumps(ct_params, indent=2)}")
        print(f"\nEDGAR params: {json.dumps(edgar_params, indent=2)}")
        return

    # Reuse run_profile logic with custom profile
    # Inject the custom profile into the profiles dict temporarily
    import biocrawler_search_profiles as bsp
    bsp.BIOCRAWLER_SEARCH_PROFILES["_custom"] = profile

    return run_profile("_custom", dry_run=False)


# ── CLI ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BioCrawler Query Engine")
    parser.add_argument("--profile", type=str, help="BioCrawler profile name")
    parser.add_argument("--custom", type=str, help="Custom condition search")
    parser.add_argument("--phase", nargs="*", help="Phase filter")
    parser.add_argument("--status", nargs="*", help="Status filter")
    parser.add_argument("--sponsor-class", type=str, default="INDUSTRY", help="Sponsor class (INDUSTRY, NIH, ACADEMIC)")
    parser.add_argument("--study-type", type=str, default="INTERVENTIONAL", help="Study type")
    parser.add_argument("--date-range", type=str, default="last_90_days", help="CT.gov date range")
    parser.add_argument("--edgar-filings", nargs="*", default=["8-K", "10-K"], help="EDGAR filing types")
    parser.add_argument("--edgar-date-range", type=str, default="last_365_days", help="EDGAR date range")
    parser.add_argument("--max-results", type=int, default=200, help="Max results")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be searched")
    parser.add_argument("--list", action="store_true", help="List available profiles")
    args = parser.parse_args()

    if args.list:
        print("Available BioCrawler Search Profiles:")
        for p in list_profiles():
            if p["name"] == "_custom":
                continue
            print(f"  {p['name']:30s} — {p['label']}")
        sys.exit(0)

    if args.profile:
        result = run_profile(args.profile, dry_run=args.dry_run)
        if result:
            print(f"\nResult: {result}")

    elif args.custom:
        result = run_custom(
            condition=args.custom,
            phase=args.phase,
            status=args.status,
            sponsor_class=args.sponsor_class,
            study_type=args.study_type,
            ctgov_date_range=args.date_range,
            edgar_filing_types=args.edgar_filings,
            edgar_date_range=args.edgar_date_range,
            max_results=args.max_results,
            dry_run=args.dry_run,
        )
        if result:
            print(f"\nResult: {result}")

    else:
        parser.print_help()