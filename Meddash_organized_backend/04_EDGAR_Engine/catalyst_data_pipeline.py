#!/usr/bin/env python3
"""
catalyst_data_pipeline.py — Meddash 4th Pillar: Biotech Hedge Fund Data Pipeline

Pulls daily insights from multiple P0 sources, resolves entities, and writes
append-only raw data to Supabase. Cloned daily to SQLite via daily_clone.py.

P0 Sources:
  - EDGAR: company_tickers.json diff, 8-K watcher, 10-Q/10-K XBRL, Form 4
  - CT.gov v2: daily delta for tracked assets
  - FDA: openFDA approvals, label revisions

Design: machines pull, intelligence verifies. Append-only — nothing updated
in place, corrections are new rows.

Usage:
    python catalyst_data_pipeline.py                    # Full P0 run
    python catalyst_data_pipeline.py --dry-run          # No Supabase writes
    python catalyst_data_pipeline.py --smoke-test       # 2 tickers, dry-run
    python catalyst_data_pipeline.py --create-schema    # Run SQL migration
    python catalyst_data_pipeline.py --source edgar     # Only EDGAR
    python catalyst_data_pipeline.py --source ctgov     # Only CT.gov
    python catalyst_data_pipeline.py --source fda       # Only FDA

Spec: [[EDGAR-Catalyst-Crawler]] (edgar-pipeline-amendment-prompt.md)
"""

import os
import sys
import json
import re
import time
import argparse
import logging
import urllib.request
import urllib.parse
from datetime import datetime, date, timedelta, timezone
from pathlib import Path

# ── Path setup ──
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "07_DevOps_Observability"))

from supabase_writer import get_pg_engine, upsert_row
from sqlalchemy import text

# ── Constants ──
EDGAR_TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json"
EDGAR_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
EDGAR_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
EDGAR_XBRL_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
EDGAR_ARCHIVES_BASE = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession_no_dashes}/"
EDGAR_FILING_INDEX = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession_no_dashes}/index.json"
EDGAR_HEADERS = {"User-Agent": "Meddash/1.0 (contact@meddash.ai)", "Accept": "application/json"}

CT_GOV_BASE = "https://clinicaltrials.gov/api/v2/studies"
FDA_OPENFDA_URL = "https://api.fda.gov/drug/drugsfda.json"

REQUEST_DELAY = 0.15
DEFAULT_WATCHLIST = ["MRK", "VTRS", "INO", "CAPR", "BBIO", "PRAX", "COGT", "PFE"]
SMOKE_TICKERS = ["MRK", "BBIO"]

# ── 8-K item classification ──
ITEM_CLASSIFICATIONS = {
    "1.01": "partnership",
    "1.02": "ma",
    "2.01": "ma",
    "2.02": "financing",
    "2.03": "financing",
    "2.04": "financing",
    "2.05": "financing",
    "3.01": "delisting",
    "3.02": "management_change",
    "3.03": "management_change",
    "4.01": "management_change",
    "5.01": "management_change",
    "5.02": "management_change",
    "5.03": "management_change",
    "7.01": "other",
    "8.01": "other",
    "9.01": "other",
}

# ── Logging ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            str(Path(__file__).resolve().parent / "catalyst_data_pipeline.log"),
            encoding="utf-8",
        ),
    ],
)
log = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════
# HTTP Helper
# ════════════════════════════════════════════════════════════════

def _fetch_json(url: str, headers: dict = None, timeout: int = 30) -> dict:
    """Fetch JSON from URL with optional headers."""
    hdrs = headers or EDGAR_HEADERS
    req = urllib.request.Request(url, headers=hdrs)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _fetch_text(url: str, headers: dict = None, timeout: int = 30) -> str:
    """Fetch text content from URL."""
    hdrs = headers or EDGAR_HEADERS
    req = urllib.request.Request(url, headers=hdrs)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


# ════════════════════════════════════════════════════════════════
# Entity Resolution (§5)
# ════════════════════════════════════════════════════════════════

_ticker_cik_map = None
_entity_cache = {}


def load_ticker_cik_map() -> dict:
    """Load SEC ticker→CIK mapping. Cached in-process."""
    global _ticker_cik_map
    if _ticker_cik_map is not None:
        return _ticker_cik_map
    log.info("Loading SEC ticker-CIK mapping...")
    data = _fetch_json(EDGAR_TICKER_MAP_URL)
    _ticker_cik_map = {}
    for entry in data.values():
        ticker = entry.get("ticker", "").upper()
        cik = str(entry.get("cik_str", "")).zfill(10)
        if ticker:
            _ticker_cik_map[ticker] = {"cik": cik, "title": entry.get("title", "")}
    log.info(f"  Loaded {len(_ticker_cik_map)} ticker→CIK mappings")
    return _ticker_cik_map


def resolve_or_create_entity(ticker: str, cik: str, company_name: str,
                              dry_run: bool = False) -> str | None:
    """Resolve a ticker/CIK to entity_id. Create if not exists.
    Returns entity_id (uuid string) or None on failure."""
    cache_key = cik or ticker
    if cache_key in _entity_cache:
        return _entity_cache[cache_key]

    if dry_run:
        _entity_cache[cache_key] = f"dry-run-{ticker}"
        return _entity_cache[cache_key]

    try:
        engine = get_pg_engine()
        with engine.connect() as conn:
            # Try by CIK first
            if cik:
                r = conn.execute(text(
                    "SELECT entity_id FROM entities WHERE cik = :cik"
                ), {"cik": cik})
                row = r.fetchone()
                if row:
                    _entity_cache[cache_key] = str(row[0])
                    return _entity_cache[cache_key]

            # Try by primary_name
            r = conn.execute(text(
                "SELECT entity_id FROM entities WHERE primary_name ILIKE :name LIMIT 1"
            ), {"name": company_name})
            row = r.fetchone()
            if row:
                _entity_cache[cache_key] = str(row[0])
                return _entity_cache[cache_key]

            # Create new entity
            conn.execute(text(
                "INSERT INTO entities (cik, primary_name, first_seen) VALUES (:cik, :name, now()) RETURNING entity_id"
            ), {"cik": cik, "name": company_name})
            r = conn.execute(text(
                "SELECT entity_id FROM entities WHERE cik = :cik"
            ), {"cik": cik})
            row = r.fetchone()
            if row:
                entity_id = str(row[0])
                # Also create ticker_history entry
                conn.execute(text(
                    "INSERT INTO ticker_history (entity_id, ticker, start_date, reason) "
                    "VALUES (:eid, :ticker, :today, 'seed')"
                ), {"eid": entity_id, "ticker": ticker, "today": date.today().isoformat()})
                conn.commit()
                _entity_cache[cache_key] = entity_id
                log.info(f"  Created entity: {company_name} ({ticker}) → {entity_id[:8]}...")
                return entity_id
            conn.commit()
    except Exception as e:
        log.warning(f"  Entity resolution failed for {ticker}: {str(e)[:80]}")
    return None


# ════════════════════════════════════════════════════════════════
# P0 Source 1: EDGAR Ticker Diff
# ════════════════════════════════════════════════════════════════

def run_ticker_diff(watchlist: list[str], dry_run: bool = False) -> dict:
    """Pull company_tickers.json, diff against last run, detect changes."""
    log.info("\n--- EDGAR Ticker Diff ---")
    mapping = load_ticker_cik_map()

    changes = []
    for ticker in watchlist:
        ticker = ticker.upper()
        current = mapping.get(ticker)
        if not current:
            continue

        cik = current["cik"]
        name = current["title"]

        if dry_run:
            changes.append({"ticker": ticker, "cik": cik, "name": name, "change": "seed_check"})
            continue

        try:
            engine = get_pg_engine()
            with engine.connect() as conn:
                # Check if we've seen this ticker before
                r = conn.execute(text(
                    "SELECT old_cik, new_cik, change_type FROM ticker_diff_state "
                    "WHERE ticker = :ticker ORDER BY checked_at DESC LIMIT 1"
                ), {"ticker": ticker})
                prev = r.fetchone()

                if prev is None:
                    # First time seeing this ticker
                    change_type = "new"
                    log.info(f"  {ticker}: first detection (CIK: {cik}, {name})")
                elif prev[1] != cik:
                    change_type = "cik_change"
                    log.info(f"  {ticker}: CIK CHANGED {prev[1]} → {cik}")
                else:
                    change_type = "same"

                # Log the diff state
                conn.execute(text(
                    "INSERT INTO ticker_diff_state (ticker, new_cik, new_name, change_type) "
                    "VALUES (:ticker, :cik, :name, :ctype)"
                ), {"ticker": ticker, "cik": cik, "name": name, "ctype": change_type})
                conn.commit()

                if change_type != "same":
                    changes.append({"ticker": ticker, "cik": cik, "name": name, "change": change_type})
        except Exception as e:
            log.warning(f"  Ticker diff failed for {ticker}: {str(e)[:80]}")

    log.info(f"  Ticker diff: {len(changes)} changes detected")
    return {"source": "edgar_ticker_diff", "changes": len(changes), "details": changes}


# ════════════════════════════════════════════════════════════════
# P0 Source 2: EDGAR 8-K Watcher
# ════════════════════════════════════════════════════════════════

def run_8k_watcher(watchlist: list[str], dry_run: bool = False,
                   lookback_days: int = 1) -> dict:
    """Watch for new 8-K filings via EDGAR full-text search."""
    log.info("\n--- EDGAR 8-K Watcher ---")
    mapping = load_ticker_cik_map()

    cutoff = (date.today() - timedelta(days=lookback_days)).isoformat()
    total_hits = 0
    all_detections = []

    for ticker in watchlist:
        ticker = ticker.upper()
        info = mapping.get(ticker)
        if not info:
            continue

        cik = info["cik"]
        company = info["title"]
        entity_id = resolve_or_create_entity(ticker, cik, company, dry_run)

        time.sleep(REQUEST_DELAY)

        # Search for recent 8-K filings for this CIK
        try:
            params = {
                "q": "*",
                "forms": "8-K",
                "dateRange": f"custom,{cutoff},{date.today().isoformat()}",
            }
            query_string = urllib.parse.urlencode(params)
            url = f"{EDGAR_SEARCH_URL}?{query_string}"
            data = _fetch_json(url)

            hits = data.get("hits", {}).get("hits", [])
            # Filter to this CIK
            ticker_hits = [h for h in hits
                           if h.get("_source", {}).get("entity_cik", "").zfill(10) == cik]

            for hit in ticker_hits:
                source = hit.get("_source", {})
                accession = source.get("accession_no", "")
                filed = source.get("file_date", "")
                items = source.get("form_items", "")

                # Classify based on item numbers
                catalyst_type = "other"
                if items:
                    for item_num in items.split(","):
                        item_num = item_num.strip()
                        if item_num in ITEM_CLASSIFICATIONS:
                            catalyst_type = ITEM_CLASSIFICATIONS[item_num]
                            break

                # Also check for catalyst keywords in the hit
                headline = source.get("headline", "") or ""
                if re.search(r'PDUFA|complete response letter|FDA approv|advisory committee',
                             headline, re.IGNORECASE):
                    catalyst_type = "readout"

                detection = {
                    "detected_at": datetime.now(timezone.utc).isoformat(),
                    "event_date": filed,
                    "entity_id": entity_id,
                    "ticker": ticker,
                    "catalyst_type": catalyst_type,
                    "source": "edgar_8k",
                    "source_url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=8-K&dateb=&owner=include&count=10",
                    "filed_at": filed,
                    "raw_text_ref": headline[:500],
                }
                all_detections.append(detection)
                total_hits += 1

                log.info(f"  {ticker}: 8-K filed {filed} — {catalyst_type} — {headline[:60]}")

        except Exception as e:
            log.warning(f"  8-K search failed for {ticker}: {str(e)[:80]}")

    # Write detections to Supabase
    if not dry_run and all_detections:
        _write_detections(all_detections)

    log.info(f"  8-K watcher: {total_hits} hits across {len(watchlist)} tickers")
    return {"source": "edgar_8k", "hits": total_hits}


# ════════════════════════════════════════════════════════════════
# P0 Source 3: EDGAR 10-Q/10-K XBRL Puller
# ════════════════════════════════════════════════════════════════

def run_xbrl_puller(watchlist: list[str], dry_run: bool = False) -> dict:
    """Pull latest 10-Q/10-K financials via companyfacts XBRL API."""
    log.info("\n--- EDGAR 10-Q/10-K XBRL Puller ---")
    mapping = load_ticker_cik_map()

    total_pulls = 0
    all_filings = []

    for ticker in watchlist:
        ticker = ticker.upper()
        info = mapping.get(ticker)
        if not info:
            continue

        cik = info["cik"]
        company = info["title"]
        entity_id = resolve_or_create_entity(ticker, cik, company, dry_run)

        time.sleep(REQUEST_DELAY)

        try:
            url = EDGAR_XBRL_URL.format(cik=cik)
            data = _fetch_json(url, timeout=45)

            # Extract key financials from XBRL facts
            facts = data.get("facts", {})
            us_gaap = facts.get("us-gaap", {})

            key_facts = {}

            # Revenue (TTM) — RevenuesFromContractWithCustomerExcludingAssessedTax
            rev_units = us_gaap.get("RevenuesFromContractWithCustomerExcludingAssessedTax", {}).get("units", {})
            rev_data = rev_units.get("USD", [])
            if rev_data:
                latest_rev = rev_data[-1]
                key_facts["revenue_ttm"] = latest_rev.get("val")
                key_facts["revenue_period"] = f"{latest_rev.get('fp','')} {latest_rev.get('fy','')}"

            # Cash and equivalents
            cash_units = us_gaap.get("CashAndCashEquivalentsAtCarryingValue", {}).get("units", {})
            cash_data = cash_units.get("USD", [])
            if cash_data:
                latest_cash = cash_data[-1]
                key_facts["cash_m"] = round(latest_cash.get("val", 0) / 1_000_000, 2)
                key_facts["cash_period"] = f"{latest_cash.get('fp','')} {latest_cash.get('fy','')}"

            # R&D expense (proxy for burn)
            rd_units = us_gaap.get("ResearchAndDevelopmentExpense", {}).get("units", {})
            rd_data = rd_units.get("USD", [])
            if rd_data:
                latest_rd = rd_data[-1]
                key_facts["burn_q"] = round(latest_rd.get("val", 0) / 1_000_000, 2)
                key_facts["burn_period"] = f"{latest_rd.get('fp','')} {latest_rd.get('fy','')}"

            if key_facts:
                filing = {
                    "detected_at": datetime.now(timezone.utc).isoformat(),
                    "entity_id": entity_id,
                    "cik": cik,
                    "ticker": ticker,
                    "form_type": "10-Q/10-K XBRL",
                    "accession_number": None,
                    "filing_date": key_facts.get("revenue_period", date.today().isoformat()),
                    "item_numbers": None,
                    "headline": f"{company} financial snapshot",
                    "key_facts": json.dumps(key_facts),
                    "source_url": url,
                    "raw_text": json.dumps(key_facts)[:2000],
                    "detected_items": ["financial_snapshot"],
                }
                all_filings.append(filing)
                total_pulls += 1
                log.info(f"  {ticker}: XBRL pulled — rev: {key_facts.get('revenue_ttm','N/A')}, "
                         f"cash: ${key_facts.get('cash_m','N/A')}M, burn: ${key_facts.get('burn_q','N/A')}M/qtr")

        except Exception as e:
            log.warning(f"  XBRL pull failed for {ticker}: {str(e)[:80]}")

    # Write to Supabase
    if not dry_run and all_filings:
        _write_raw_filings(all_filings)

    log.info(f"  XBRL puller: {total_pulls} entities processed")
    return {"source": "edgar_xbrl", "pulls": total_pulls}


# ════════════════════════════════════════════════════════════════
# P0 Source 4: CT.gov v2 Daily Delta
# ════════════════════════════════════════════════════════════════

def run_ctgov_delta(watchlist: list[str], dry_run: bool = False,
                     lookback_days: int = 1) -> dict:
    """Check CT.gov for trial status changes and results postings."""
    log.info("\n--- CT.gov v2 Daily Delta ---")
    mapping = load_ticker_cik_map()

    total_changes = 0
    all_trials = []

    # Search for trials by sponsor name for each tracked company
    for ticker in watchlist:
        ticker = ticker.upper()
        info = mapping.get(ticker)
        if not info:
            continue

        company = info["title"]
        cik = info["cik"]
        entity_id = resolve_or_create_entity(ticker, cik, company, dry_run)

        time.sleep(REQUEST_DELAY)

        try:
            # Search CT.gov for trials by this sponsor
            params = {
                "query.sponsor": company,
                "pageSize": "10",
                "countTotal": "true",
            }
            query_string = urllib.parse.urlencode(params)
            url = f"{CT_GOV_BASE}?{query_string}"
            data = _fetch_json(url, headers={"User-Agent": "Meddash-CQ/2.0"})

            studies = data.get("studies", [])
            total_count = data.get("totalCount", 0)

            for study in studies:
                ps = study.get("protocolSection", {})
                id_mod = ps.get("identificationModule", {})
                status_mod = ps.get("statusModule", {})
                nct_id = id_mod.get("nctId", "")
                title = id_mod.get("briefTitle", "")
                current_status = status_mod.get("overallStatus", "")
                results = ps.get("resultsSection", {})

                has_results = bool(results)
                results_date = status_mod.get("studyFirstPostDateStruct", {}).get("date", "")

                # For delta: we'd compare against last known status
                # For now, log all as potential changes
                trial = {
                    "detected_at": datetime.now(timezone.utc).isoformat(),
                    "entity_id": entity_id,
                    "nct_id": nct_id,
                    "trial_title": title,
                    "previous_status": None,  # Would be from last run
                    "new_status": current_status,
                    "status_change_date": date.today().isoformat(),
                    "has_results": has_results,
                    "results_posting_date": results_date if has_results else None,
                    "source_url": f"https://clinicaltrials.gov/study/{nct_id}",
                    "raw_data": json.dumps({"status": current_status, "has_results": has_results}),
                }
                all_trials.append(trial)
                total_changes += 1

                if has_results:
                    log.info(f"  {ticker}: RESULTS POSTED — {nct_id} — {title[:50]}")
                else:
                    log.info(f"  {ticker}: {current_status} — {nct_id}")

        except Exception as e:
            log.warning(f"  CT.gov search failed for {ticker}: {str(e)[:80]}")

    # Write to Supabase
    if not dry_run and all_trials:
        _write_raw_trials(all_trials)

    log.info(f"  CT.gov delta: {total_changes} trials checked across {len(watchlist)} tickers")
    return {"source": "ctgov", "trials_checked": total_changes}


# ════════════════════════════════════════════════════════════════
# P0 Source 5: FDA openFDA
# ════════════════════════════════════════════════════════════════

def run_fda_openfda(watchlist: list[str], dry_run: bool = False,
                     lookback_days: int = 7) -> dict:
    """Check openFDA for recent drug approvals and label revisions."""
    log.info("\n--- FDA openFDA ---")
    mapping = load_ticker_cik_map()

    total_actions = 0
    all_regulatory = []

    for ticker in watchlist:
        ticker = ticker.upper()
        info = mapping.get(ticker)
        if not info:
            continue

        company = info["title"]
        cik = info["cik"]
        entity_id = resolve_or_create_entity(ticker, cik, company, dry_run)

        time.sleep(REQUEST_DELAY)

        try:
            # Search openFDA for this company's drugs
            # openFDA doesn't have a great sponsor search, so we search by company name in submissions
            params = {
                "search": f'openfda.manufacturer_name:"{company}"',
                "limit": "10",
            }
            query_string = urllib.parse.urlencode(params)
            url = f"{FDA_OPENFDA_URL}?{query_string}"
            data = _fetch_json(url, headers={"User-Agent": "Meddash-CQ/2.0"})

            results = data.get("results", [])
            for result in results:
                openfda = result.get("openfda", {})
                drug_name = openfda.get("brand_name", ["Unknown"])[0] if openfda.get("brand_name") else "Unknown"
                submission_type = result.get("submission_type", "")
                submission_status = result.get("submission_status", "")

                if submission_status.upper() == "AP":
                    action_type = "approval"
                elif submission_type == "SUPPL":
                    action_type = "label_revision"
                else:
                    action_type = "other_regulatory"

                reg = {
                    "detected_at": datetime.now(timezone.utc).isoformat(),
                    "entity_id": entity_id,
                    "ticker": ticker,
                    "action_type": action_type,
                    "action_date": date.today().isoformat(),
                    "drug_name": drug_name,
                    "indication": openfda.get("generic_name", [None])[0] if openfda.get("generic_name") else None,
                    "source": "fda_drugsatfda",
                    "source_url": f"https://api.fda.gov/drug/drugsfda.json?search=openfda.manufacturer_name:\"{company}\"",
                    "raw_text": json.dumps(result)[:2000],
                }
                all_regulatory.append(reg)
                total_actions += 1
                log.info(f"  {ticker}: FDA {action_type} — {drug_name} ({submission_status})")

        except Exception as e:
            log.warning(f"  FDA search failed for {ticker}: {str(e)[:80]}")

    # Write to Supabase
    if not dry_run and all_regulatory:
        _write_raw_regulatory(all_regulatory)

    log.info(f"  FDA openFDA: {total_actions} actions found across {len(watchlist)} tickers")
    return {"source": "fda", "actions": total_actions}


# ════════════════════════════════════════════════════════════════
# Supabase Writers
# ════════════════════════════════════════════════════════════════

def _write_detections(detections: list[dict]):
    """Write detection rows to catalyst_detections (append-only)."""
    try:
        engine = get_pg_engine()
        with engine.connect() as conn:
            for d in detections:
                conn.execute(text(
                    "INSERT INTO catalyst_detections "
                    "(detected_at, event_date, entity_id, ticker, catalyst_type, source, source_url, filed_at, raw_text_ref) "
                    "VALUES (:detected_at, :event_date, :entity_id, :ticker, :catalyst_type, :source, :source_url, :filed_at, :raw_text_ref)"
                ), d)
            conn.commit()
        log.info(f"  Wrote {len(detections)} detection rows to Supabase")
    except Exception as e:
        log.warning(f"  Failed to write detections: {str(e)[:80]}")


def _write_raw_filings(filings: list[dict]):
    """Write raw filing rows to catalyst_raw_filings (append-only)."""
    try:
        engine = get_pg_engine()
        with engine.connect() as conn:
            for f in filings:
                conn.execute(text(
                    "INSERT INTO catalyst_raw_filings "
                    "(detected_at, entity_id, cik, ticker, form_type, accession_number, filing_date, "
                    "item_numbers, headline, key_facts, source_url, raw_text, detected_items) "
                    "VALUES (:detected_at, :entity_id, :cik, :ticker, :form_type, :accession_number, :filing_date, "
                    ":item_numbers, :headline, :key_facts, :source_url, :raw_text, :detected_items)"
                ), f)
            conn.commit()
        log.info(f"  Wrote {len(filings)} raw filing rows to Supabase")
    except Exception as e:
        log.warning(f"  Failed to write raw filings: {str(e)[:80]}")


def _write_raw_trials(trials: list[dict]):
    """Write raw trial rows to catalyst_raw_trials (append-only)."""
    try:
        engine = get_pg_engine()
        with engine.connect() as conn:
            for t in trials:
                conn.execute(text(
                    "INSERT INTO catalyst_raw_trials "
                    "(detected_at, entity_id, nct_id, trial_title, previous_status, new_status, "
                    "status_change_date, has_results, results_posting_date, source_url, raw_data) "
                    "VALUES (:detected_at, :entity_id, :nct_id, :trial_title, :previous_status, :new_status, "
                    ":status_change_date, :has_results, :results_posting_date, :source_url, :raw_data)"
                ), t)
            conn.commit()
        log.info(f"  Wrote {len(trials)} raw trial rows to Supabase")
    except Exception as e:
        log.warning(f"  Failed to write raw trials: {str(e)[:80]}")


def _write_raw_regulatory(regs: list[dict]):
    """Write raw regulatory rows to catalyst_raw_regulatory (append-only)."""
    try:
        engine = get_pg_engine()
        with engine.connect() as conn:
            for r in regs:
                conn.execute(text(
                    "INSERT INTO catalyst_raw_regulatory "
                    "(detected_at, entity_id, ticker, action_type, action_date, drug_name, indication, "
                    "source, source_url, raw_text) "
                    "VALUES (:detected_at, :entity_id, :ticker, :action_type, :action_date, :drug_name, :indication, "
                    ":source, :source_url, :raw_text)"
                ), r)
            conn.commit()
        log.info(f"  Wrote {len(regs)} raw regulatory rows to Supabase")
    except Exception as e:
        log.warning(f"  Failed to write raw regulatory: {str(e)[:80]}")


# ════════════════════════════════════════════════════════════════
# Schema Creation
# ════════════════════════════════════════════════════════════════

def create_schema():
    """Run the SQL migration to create all catalyst pipeline tables."""
    schema_path = Path(__file__).resolve().parent / "schema_catalyst_pipeline.sql"
    sql = schema_path.read_text(encoding="utf-8")

    engine = get_pg_engine()
    with engine.connect() as conn:
        lines = sql.split("\n")
        statements = []
        current = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("--"):
                continue
            current.append(line)
            if stripped.endswith(";"):
                statements.append("\n".join(current))
                current = []
        if current:
            statements.append("\n".join(current))

        success = 0
        for stmt in statements:
            stmt = stmt.strip()
            if not stmt:
                continue
            try:
                conn.execute(text(stmt))
                success += 1
            except Exception as e:
                log.warning(f"  Schema statement failed: {str(e)[:100]}")
        conn.commit()
    log.info(f"Schema migration complete: {success} statements executed")


# ════════════════════════════════════════════════════════════════
# Main Pipeline
# ════════════════════════════════════════════════════════════════

def run_pipeline(tickers: list[str], dry_run: bool = False,
                 sources: str = "all") -> dict:
    """Run the full P0 catalyst data pipeline."""
    log.info("=" * 60)
    log.info("CATALYST DATA PIPELINE — Meddash 4th Pillar")
    log.info(f"Tickers: {', '.join(tickers)}")
    log.info(f"Dry run: {dry_run}")
    log.info(f"Sources: {sources}")
    log.info("=" * 60)

    start_time = time.time()
    results = {}

    # Always run ticker diff first (seeds entities)
    if sources in ("all", "edgar"):
        results["ticker_diff"] = run_ticker_diff(tickers, dry_run)

    # EDGAR sources
    if sources in ("all", "edgar"):
        results["8k_watcher"] = run_8k_watcher(tickers, dry_run)
        results["xbrl_puller"] = run_xbrl_puller(tickers, dry_run)

    # CT.gov
    if sources in ("all", "ctgov"):
        results["ctgov_delta"] = run_ctgov_delta(tickers, dry_run)

    # FDA
    if sources in ("all", "fda"):
        results["fda_openfda"] = run_fda_openfda(tickers, dry_run)

    elapsed = time.time() - start_time

    log.info(f"\n{'=' * 60}")
    log.info(f"PIPELINE COMPLETE")
    log.info(f"  Sources run: {', '.join(results.keys())}")
    log.info(f"  Elapsed: {elapsed:.1f}s")

    for source, result in results.items():
        log.info(f"  {source}: {result}")

    log.info(f"\n=== COMPLETE: {elapsed:.1f}s ===")

    return {
        "tickers": ",".join(tickers),
        "sources": sources,
        "dry_run": dry_run,
        "results": results,
        "elapsed": elapsed,
        "status": "success",
    }


# ════════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Catalyst Data Pipeline — Meddash 4th Pillar"
    )
    parser.add_argument("--tickers", type=str, default="",
                        help="Comma-separated tickers")
    parser.add_argument("--dry-run", action="store_true",
                        help="No Supabase writes")
    parser.add_argument("--smoke-test", action="store_true",
                        help="2 tickers, dry-run")
    parser.add_argument("--create-schema", action="store_true",
                        help="Run SQL migration")
    parser.add_argument("--source", type=str, default="all",
                        choices=["all", "edgar", "ctgov", "fda"],
                        help="Which sources to run")

    args = parser.parse_args()

    if args.create_schema:
        log.info("Creating Supabase schema...")
        create_schema()
        return

    if args.smoke_test:
        tickers = SMOKE_TICKERS
        dry_run = True
    elif args.tickers:
        tickers = [t.strip() for t in args.tickers.split(",")]
        dry_run = args.dry_run
    else:
        tickers = DEFAULT_WATCHLIST
        dry_run = args.dry_run

    result = run_pipeline(tickers, dry_run=dry_run, sources=args.source)
    print(f"\n{json.dumps(result, indent=2, default=str)}")


if __name__ == "__main__":
    main()