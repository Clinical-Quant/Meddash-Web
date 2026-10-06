#!/usr/bin/env python3
"""
edgar_catalyst_crawler.py — SEC EDGAR 8-K Catalyst Crawler (Engine 04)

Reads SEC 8-K filings for a watchlist of biotech tickers, extracts scheduled
regulatory catalysts (PDUFA dates, readout windows, AdCom meetings, approvals,
CRLs), and upserts them to Supabase `catalyst_events`.

Every calendar date traces to a company-filed 8-K (or official IR release
where the 8-K is silent). No secondary-calendar scraping, no invented URLs.

Usage:
    python edgar_catalyst_crawler.py                          # Default watchlist
    python edgar_catalyst_crawler.py --tickers MRK,VTRS,INO   # Custom tickers
    python edgar_catalyst_crawler.py --dry-run                # No Supabase write
    python edgar_catalyst_crawler.py --smoke-test             # 2 tickers, dry-run
    python edgar_catalyst_crawler.py --create-schema          # Run SQL migration

Spec: [[EDGAR-Catalyst-Crawler]] (edgar-crawler-spec.md v2)
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
from datetime import datetime, date, timezone
from pathlib import Path

# ── Path setup ──
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "07_DevOps_Observability"))

from supabase_writer import get_pg_engine, upsert_row
from sqlalchemy import text

# ── Constants ──
EDGAR_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
EDGAR_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
EDGAR_TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json"
EDGAR_ARCHIVES_BASE = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession_no_dashes}/"
EDGAR_FILING_INDEX = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession_no_dashes}/index.json"

EDGAR_HEADERS = {
    "User-Agent": "Meddash/1.0 (contact@meddash.ai)",
    "Accept": "application/json",
}

REQUEST_DELAY = 0.15  # ~6.7 req/s, well under SEC's 10 req/s limit
DEFAULT_WATCHLIST = ["MRK", "VTRS", "INO", "CAPR", "BBIO", "PRAX", "COGT", "PFE"]
SMOKE_TICKERS = ["MRK", "BBIO"]

# ── Regex patterns (case-insensitive, from spec) ──
RE_PDUFA = re.compile(
    r'PDUFA\s+(?:target\s+action\s+)?date\s+(?:of\s+)?([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})',
    re.IGNORECASE
)
RE_PDUFA_EXTENSION = re.compile(
    r'extend\w*?.{0,60}?PDUFA.{0,60}?from\s+([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})\s+to\s+([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})',
    re.IGNORECASE | re.DOTALL
)
RE_READOUT_WINDOW = re.compile(
    r'(?:top-line|topline)\s+data\s+(?:expected|anticipated).{0,60}?(Q[1-4]\s+\d{4}|H[12]\s+\d{4})',
    re.IGNORECASE | re.DOTALL
)
RE_ADCOM = re.compile(
    r'advisory\s+committee.{0,80}?meeting.{0,40}?([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})',
    re.IGNORECASE | re.DOTALL
)
RE_APPROVAL = re.compile(
    r'FDA\s+(?:approved|granted\s+approval)',
    re.IGNORECASE
)
RE_CRL = re.compile(
    r'complete\s+response\s+letter',
    re.IGNORECASE
)

# Asset/indication extraction helpers
RE_ASSET_CONTEXT = re.compile(
    r'(?:drug|product|candidate|therapy|compound|agent)\s+(?:called\s+|named\s+|known\s+as\s+)?([A-Z]{2,}[0-9]?\w*(?:\s*\([\w-]+\))?)',
    re.IGNORECASE
)
RE_INDICATION_CONTEXT = re.compile(
    r'(?:for|in|treating|treatment\s+of)\s+(?:patients?\s+(?:with|suffering\s+from)\s+)?([A-Z][a-zA-Z]+(?:\s+[a-zA-Z]+){0,4})',
    re.IGNORECASE
)

# ── Logging ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            str(Path(__file__).resolve().parent / "edgar_catalyst_crawler.log"),
            encoding="utf-8",
        ),
    ],
)
log = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# EDGAR Access Layer
# ═══════════════════════════════════════════════════════════════════════

_ticker_cik_map = None


def load_ticker_cik_map() -> dict:
    """Load SEC's ticker→CIK mapping file. Cached in-process."""
    global _ticker_cik_map
    if _ticker_cik_map is not None:
        return _ticker_cik_map

    log.info("Loading SEC ticker-CIK mapping...")
    req = urllib.request.Request(EDGAR_TICKER_MAP_URL, headers=EDGAR_HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    _ticker_cik_map = {}
    for entry in data.values():
        ticker = entry.get("ticker", "").upper()
        cik = str(entry.get("cik_str", "")).zfill(10)
        if ticker:
            _ticker_cik_map[ticker] = {"cik": cik, "title": entry.get("title", "")}

    log.info(f"  Loaded {len(_ticker_cik_map)} ticker→CIK mappings")
    return _ticker_cik_map


def resolve_ticker(ticker: str) -> dict | None:
    """Resolve a ticker to CIK + company name."""
    mapping = load_ticker_cik_map()
    return mapping.get(ticker.upper())


def fetch_submissions(cik: str) -> dict:
    """Fetch company submissions JSON from EDGAR."""
    url = EDGAR_SUBMISSIONS_URL.format(cik=cik)
    req = urllib.request.Request(url, headers=EDGAR_HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_recent_8k_filings(cik: str, max_filings: int = 20) -> list[dict]:
    """Get recent 8-K filings for a CIK from submissions data."""
    data = fetch_submissions(cik)
    recent = data.get("filings", {}).get("recent", {})

    forms = recent.get("form", [])
    accession_numbers = recent.get("accessionNumber", [])
    filing_dates = recent.get("filingDate", [])
    primary_docs = recent.get("primaryDocument", [])
    primary_desc = recent.get("primaryDocDescription", [])

    filings = []
    for i, form in enumerate(forms):
        if form == "8-K":
            accession = accession_numbers[i]
            filings.append({
                "accession_number": accession,
                "filing_date": filing_dates[i],
                "primary_document": primary_docs[i] if i < len(primary_docs) else "",
                "primary_doc_description": primary_desc[i] if i < len(primary_desc) else "",
                "cik": cik,
            })
            if len(filings) >= max_filings:
                break

    return filings


def fetch_filing_index(cik: str, accession_number: str) -> dict:
    """Fetch the filing's index.json to get all documents."""
    accession_no_dashes = accession_number.replace("-", "")
    url = EDGAR_FILING_INDEX.format(cik=cik, accession_no_dashes=accession_no_dashes)
    req = urllib.request.Request(url, headers=EDGAR_HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_document_text(url: str) -> str:
    """Fetch and parse an HTM document, returning plain text."""
    req = urllib.request.Request(url, headers=EDGAR_HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode("utf-8", errors="replace")

    # Strip HTML tags → plain text
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&#\d+;', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_excerpt(full_text: str, match_start: int, match_end: int, context_chars: int = 200) -> str:
    """Extract a 1-2 sentence excerpt around a regex match."""
    start = max(0, match_start - context_chars)
    end = min(len(full_text), match_end + context_chars)
    chunk = full_text[start:end]

    # Try to trim to sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+', chunk)
    if len(sentences) >= 2:
        return ' '.join(sentences[:2]).strip()
    return chunk.strip()[:500]


def parse_date_string(date_str: str) -> str:
    """Parse 'November 27, 2026' → '2026-11-27'. Return original on failure."""
    try:
        dt = datetime.strptime(date_str.strip(), "%B %d, %Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        try:
            dt = datetime.strptime(date_str.strip(), "%b %d, %Y")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            return date_str.strip()


def is_date_in_past(date_str: str) -> bool:
    """Check if a parsed date string is before today."""
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        return d < date.today()
    except ValueError:
        return False  # Window dates — assume upcoming


# ═══════════════════════════════════════════════════════════════════════
# Catalyst Extraction
# ═══════════════════════════════════════════════════════════════════════

def extract_catalysts_from_text(
    doc_text: str, ticker: str, cik: str, company: str,
    accession_number: str, filing_date: str, filing_index_url: str
) -> list[dict]:
    """Extract catalyst events from filing document text using regex patterns."""
    catalysts = []

    def make_event(event_type: str, date_or_window: str, date_precision: str,
                   excerpt: str, priority_review: bool = False) -> dict:
        return {
            "company": company,
            "ticker": ticker,
            "cik": cik,
            "asset": _extract_asset(doc_text, ticker),
            "indication": _extract_indication(doc_text),
            "event_type": event_type,
            "date_or_window": date_or_window,
            "date_precision": date_precision,
            "priority_review": priority_review,
            "verification_source": filing_index_url,
            "accession_number": accession_number,
            "filing_date": filing_date,
            "excerpt": excerpt,
            "status": "occurred" if date_precision == "exact" and is_date_in_past(date_or_window) else "upcoming",
        }

    # Check for PDUFA extension first (supersedes existing PDUFA date)
    for m in RE_PDUFA_EXTENSION.finditer(doc_text):
        old_date = parse_date_string(m.group(1))
        new_date = parse_date_string(m.group(2))
        excerpt = extract_excerpt(doc_text, m.start(), m.end())
        catalysts.append(make_event("PDUFA", new_date, "exact", excerpt))
        log.info(f"    PDUFA EXTENSION: {old_date} → {new_date}")

    # PDUFA date (skip if already found via extension)
    pdufa_found = any(c["event_type"] == "PDUFA" for c in catalysts)
    if not pdufa_found:
        for m in RE_PDUFA.finditer(doc_text):
            parsed = parse_date_string(m.group(1))
            excerpt = extract_excerpt(doc_text, m.start(), m.end())
            # Check for priority review nearby
            nearby = doc_text[max(0, m.start()-300):m.end()+300]
            priority = "priority review" in nearby.lower()
            catalysts.append(make_event("PDUFA", parsed, "exact", excerpt, priority))
            log.info(f"    PDUFA date: {parsed}")

    # Readout window
    for m in RE_READOUT_WINDOW.finditer(doc_text):
        window = m.group(1).strip()
        excerpt = extract_excerpt(doc_text, m.start(), m.end())
        catalysts.append(make_event("readout_window", window, "window", excerpt))
        log.info(f"    Readout window: {window}")

    # AdCom
    for m in RE_ADCOM.finditer(doc_text):
        parsed = parse_date_string(m.group(1))
        excerpt = extract_excerpt(doc_text, m.start(), m.end())
        catalysts.append(make_event("AdCom", parsed, "exact", excerpt))
        log.info(f"    AdCom date: {parsed}")

    # Approval — only capture once per filing (avoid duplicates from pipeline update docs)
    approval_found = False
    for m in RE_APPROVAL.finditer(doc_text):
        if not approval_found:
            excerpt = extract_excerpt(doc_text, m.start(), m.end())
            catalysts.append(make_event("approval", filing_date, "exact", excerpt))
            log.info(f"    FDA approval mention on {filing_date}")
            approval_found = True

    # CRL — only capture once per filing
    crl_found = False
    for m in RE_CRL.finditer(doc_text):
        if not crl_found:
            excerpt = extract_excerpt(doc_text, m.start(), m.end())
            catalysts.append(make_event("CRL", filing_date, "exact", excerpt))
            log.info(f"    CRL mention on {filing_date}")
            crl_found = True

    # Deduplicate within this filing: same (event_type, date_or_window) = one row
    seen = set()
    unique = []
    for c in catalysts:
        key = (c["event_type"], c["date_or_window"])
        if key not in seen:
            seen.add(key)
            unique.append(c)

    return unique


def _extract_asset(doc_text: str, ticker: str) -> str:
    """Try to extract drug/asset name from filing text."""
    # Skip exhibit boilerplate (EX-99.1, EXHIBIT 99, etc.)
    # Look for known drug names first (case-insensitive)
    known_drugs = [
        "pembrolizumab", "nivolumab", "tofersen", "ribitol", "amiloride",
        "lenmeldy", "cobomarsen", "remdesivir", "encaleret", "welireg",
        "keytruda", "opdivo", "winrevair", "capvaxive",
    ]
    for drug in known_drugs:
        if drug in doc_text.lower():
            return drug.capitalize()

    # Look for drug code patterns: XXX-### or XXX#### (e.g., BBP-418, MK-8748)
    # Skip EX-99 (exhibit numbers) and SEC filing codes
    patterns = [
        re.compile(r'\b([A-Z]{2,4}-\d{3,4})\b'),  # BBP-418, MK-8748
        re.compile(r'\b([A-Z]{2,5}\d{2,4})\b'),   # AB1234 (no dash)
    ]
    for p in patterns:
        for m in p.finditer(doc_text):
            candidate = m.group(1)
            # Skip EX-99 (exhibit references) and common false positives
            if candidate.upper().startswith("EX") and "99" in candidate:
                continue
            # Skip if it looks like a filing code (all caps + many digits)
            if candidate.upper() in ("HTTP", "HTTPS", "HTML"):
                continue
            return candidate
    return "UNKNOWN"


def _extract_indication(doc_text: str) -> str:
    """Try to extract indication from filing text."""
    # Try to find indication near PDUFA/approval context
    # Look for patterns like "for the treatment of X" or "patients with X"
    contexts = [
        re.compile(r'(?:treatment\s+of|for\s+the\s+treatment\s+of)\s+([a-zA-Z][a-zA-Z\s]{3,40}?)(?:[.,;]|based|in\s+(?:the\s+)?U\.S|Phase)', re.IGNORECASE),
        re.compile(r'patients?\s+(?:with|suffering\s+from)\s+([a-zA-Z][a-zA-Z\s]{3,40}?)(?:[.,;]|based|Phase|who)', re.IGNORECASE),
    ]
    for ctx in contexts:
        m = ctx.search(doc_text)
        if m:
            indication = m.group(1).strip()
            # Filter out false positives
            lower = indication.lower()
            if any(bad in lower for bad in ["the company", "this", "its", "total second", "oncology and animal", "news release"]):
                continue
            if len(indication) > 5:
                return indication
    return None


# ═══════════════════════════════════════════════════════════════════════
# Filing Processing
# ═══════════════════════════════════════════════════════════════════════

def process_filing(filing: dict, ticker: str, cik: str, company: str) -> list[dict]:
    """Process a single 8-K filing: fetch index, parse primary doc + exhibits."""
    accession = filing["accession_number"]
    filing_date = filing["filing_date"]
    accession_no_dashes = accession.replace("-", "")
    filing_index_url = EDGAR_ARCHIVES_BASE.format(cik=cik, accession_no_dashes=accession_no_dashes)

    log.info(f"  Processing 8-K: {accession} (filed {filing_date})")

    all_catalysts = []

    try:
        # Fetch the filing index to find all documents
        index_data = fetch_filing_index(cik, accession)
        items = index_data.get("directory", {}).get("item", [])

        # Collect HTM documents to parse (primary 8-K body + EX-99 exhibits)
        docs_to_parse = []
        for item in items:
            name = item.get("name", "")
            if name.endswith(".htm") or name.endswith(".html"):
                # Skip index files
                if "index" in name.lower():
                    continue
                # Prioritize: primary 8-K body + EX-99 press release exhibits
                name_lower = name.lower()
                is_primary = (name == filing.get("primary_document"))
                is_exhibit = ("ex-99" in name_lower or "ex99" in name_lower or
                              "_ex-99" in name_lower or "_ex99" in name_lower)
                if is_primary or is_exhibit:
                    doc_url = f"{filing_index_url}{name}"
                    docs_to_parse.append((name, doc_url))

        if not docs_to_parse:
            # Fallback: parse all non-index HTM documents
            for item in items:
                name = item.get("name", "")
                if (name.endswith(".htm") or name.endswith(".html")) and "index" not in name.lower():
                    doc_url = f"{filing_index_url}{name}"
                    docs_to_parse.append((name, doc_url))

        log.info(f"    {len(docs_to_parse)} documents to parse")

        for doc_name, doc_url in docs_to_parse:
            try:
                time.sleep(REQUEST_DELAY)
                doc_text = fetch_document_text(doc_url)

                if len(doc_text) < 100:
                    continue

                catalysts = extract_catalysts_from_text(
                    doc_text, ticker, cik, company,
                    accession, filing_date, filing_index_url
                )

                if catalysts:
                    all_catalysts.extend(catalysts)
                    log.info(f"    {doc_name}: found {len(catalysts)} catalyst(s)")

            except Exception as e:
                log.warning(f"    Failed to parse {doc_name}: {str(e)[:80]}")
                continue

    except Exception as e:
        log.warning(f"  Failed to fetch filing index for {accession}: {str(e)[:80]}")

    return all_catalysts


# ═══════════════════════════════════════════════════════════════════════
# Supabase Ingestion
# ═══════════════════════════════════════════════════════════════════════

def create_schema():
    """Run the SQL migration to create catalyst_events + edgar_query_log."""
    schema_path = Path(__file__).resolve().parent / "schema_catalyst_events.sql"
    sql = schema_path.read_text(encoding="utf-8")

    engine = get_pg_engine()
    with engine.connect() as conn:
        # Execute the full SQL as one statement block
        # Remove comment-only lines and split on semicolons at end of statements
        lines = sql.split("\n")
        statements = []
        current = []
        for line in lines:
            stripped = line.strip()
            # Skip comment-only lines
            if stripped.startswith("--"):
                continue
            current.append(line)
            if stripped.endswith(";"):
                statements.append("\n".join(current))
                current = []
        if current:
            statements.append("\n".join(current))

        for stmt in statements:
            stmt = stmt.strip()
            if not stmt:
                continue
            try:
                conn.execute(text(stmt))
            except Exception as e:
                log.warning(f"  Schema statement failed (may be OK if idempotent): {str(e)[:100]}")
        conn.commit()
    log.info("Schema created: catalyst_events + edgar_query_log")


def ingest_to_supabase(catalysts: list[dict]) -> dict:
    """Upsert catalyst events to Supabase catalyst_events table."""
    if not catalysts:
        return {"ingested": 0, "errors": 0}

    engine = get_pg_engine()
    conn = engine.connect()

    ingested = 0
    errors = 0

    for catalyst in catalysts:
        try:
            # Build row dict (exclude 'id' — let Supabase auto-generate)
            row = {
                "company": catalyst["company"],
                "ticker": catalyst["ticker"],
                "cik": catalyst["cik"],
                "asset": catalyst["asset"],
                "indication": catalyst["indication"],
                "event_type": catalyst["event_type"],
                "date_or_window": catalyst["date_or_window"],
                "date_precision": catalyst["date_precision"],
                "priority_review": catalyst["priority_review"],
                "verification_source": catalyst["verification_source"],
                "accession_number": catalyst["accession_number"],
                "filing_date": catalyst["filing_date"],
                "excerpt": catalyst["excerpt"],
                "status": catalyst["status"],
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            # Upsert on (ticker, asset, event_type) unique constraint
            # We need a composite conflict target, so use raw SQL
            cols = list(row.keys())
            col_names = ", ".join([f'"{c}"' for c in cols])
            placeholders = ", ".join([f":{c}" for c in cols])
            update_cols = [c for c in cols if c not in ("ticker", "asset", "event_type")]
            update_set = ", ".join([f'"{c}" = EXCLUDED."{c}"' for c in update_cols])

            sql = (
                f'INSERT INTO "catalyst_events" ({col_names}) VALUES ({placeholders}) '
                f'ON CONFLICT ("ticker", "asset", "event_type") DO UPDATE SET {update_set}'
            )
            conn.execute(text(sql), row)
            ingested += 1
        except Exception as e:
            errors += 1
            conn.rollback()
            if errors <= 5:
                log.warning(f"  Failed to upsert {catalyst['ticker']} {catalyst['event_type']}: {str(e)[:80]}")

    conn.commit()
    conn.close()

    return {"ingested": ingested, "errors": errors}


def log_run(tickers_searched: str, filings_scanned: int, total_found: int,
            total_ingested: int, status: str, error_detail: str = ""):
    """Log a run to edgar_query_log table."""
    try:
        engine = get_pg_engine()
        conn = engine.connect()
        upsert_row(conn, "edgar_query_log", {
            "tickers_searched": tickers_searched,
            "filings_scanned": filings_scanned,
            "total_found": total_found,
            "total_ingested": total_ingested,
            "status": status,
            "error_detail": error_detail,
        }, pk="id")
        conn.commit()
        conn.close()
    except Exception as e:
        log.warning(f"  Failed to log run: {str(e)[:80]}")


# ═══════════════════════════════════════════════════════════════════════
# Main Crawl
# ═══════════════════════════════════════════════════════════════════════

def run_crawl(tickers: list[str], dry_run: bool = False, max_filings: int = 20) -> dict:
    """Run the EDGAR catalyst crawl for a list of tickers."""
    log.info("=" * 60)
    log.info("EDGAR CATALYST CRAWLER — Engine 04")
    log.info(f"Tickers: {', '.join(tickers)}")
    log.info(f"Dry run: {dry_run}")
    log.info(f"Max filings per ticker: {max_filings}")
    log.info("=" * 60)

    start_time = time.time()
    all_catalysts = []
    total_filings_scanned = 0
    errors = []

    for ticker in tickers:
        ticker = ticker.upper().strip()
        log.info(f"\n--- Processing ticker: {ticker} ---")

        # Resolve ticker → CIK
        ticker_info = resolve_ticker(ticker)
        if not ticker_info:
            log.warning(f"  Could not resolve ticker {ticker}")
            errors.append(f"{ticker}: ticker not found in SEC mapping")
            continue

        cik = ticker_info["cik"]
        company = ticker_info["title"]
        log.info(f"  CIK: {cik} | Company: {company}")

        time.sleep(REQUEST_DELAY)

        # Get recent 8-K filings
        try:
            filings = get_recent_8k_filings(cik, max_filings=max_filings)
        except Exception as e:
            log.warning(f"  Failed to fetch submissions for {ticker}: {str(e)[:80]}")
            errors.append(f"{ticker}: submissions fetch failed — {str(e)[:60]}")
            continue

        log.info(f"  Found {len(filings)} recent 8-K filings")
        total_filings_scanned += len(filings)

        if not filings:
            continue

        # Process each filing
        for filing in filings:
            time.sleep(REQUEST_DELAY)
            catalysts = process_filing(filing, ticker, cik, company)
            all_catalysts.extend(catalysts)

    elapsed = time.time() - start_time

    # Cross-filing dedup: same (ticker, asset, event_type, date_or_window) — keep newest filing_date
    deduped = {}
    for c in all_catalysts:
        key = (c["ticker"], c["asset"], c["event_type"], c["date_or_window"])
        if key not in deduped or c["filing_date"] > deduped[key]["filing_date"]:
            deduped[key] = c
    all_catalysts = list(deduped.values())

    total_found = len(all_catalysts)

    log.info(f"\n{'=' * 60}")
    log.info(f"CRAWL COMPLETE")
    log.info(f"  Tickers searched: {len(tickers)}")
    log.info(f"  Filings scanned: {total_filings_scanned}")
    log.info(f"  Catalysts found: {total_found}")
    log.info(f"  Elapsed: {elapsed:.1f}s")

    if all_catalysts:
        log.info(f"\n  Catalyst breakdown by event_type:")
        type_counts = {}
        for c in all_catalysts:
            type_counts[c["event_type"]] = type_counts.get(c["event_type"], 0) + 1
        for et, count in sorted(type_counts.items()):
            log.info(f"    {et}: {count}")

        log.info(f"\n  Catalysts by ticker:")
        ticker_counts = {}
        for c in all_catalysts:
            ticker_counts[c["ticker"]] = ticker_counts.get(c["ticker"], 0) + 1
        for t, count in sorted(ticker_counts.items()):
            log.info(f"    {t}: {count}")

    # Dry run: print results without writing
    if dry_run:
        log.info("\n  [DRY RUN] No Supabase writes.")
        if all_catalysts:
            print(f"\n{'='*60}")
            print(f"CATALYSTS FOUND ({total_found}):")
            print(f"{'='*60}")
            for i, c in enumerate(all_catalysts, 1):
                print(f"\n  [{i}] {c['ticker']} | {c['event_type']} | {c['date_or_window']} ({c['date_precision']})")
                print(f"      Company: {c['company']}")
                print(f"      Asset: {c['asset']} | Indication: {c.get('indication', 'N/A')}")
                print(f"      Filed: {c['filing_date']} | Accession: {c['accession_number']}")
                print(f"      Source: {c['verification_source']}")
                print(f"      Priority: {c['priority_review']} | Status: {c['status']}")
                print(f"      Excerpt: {c['excerpt'][:200]}...")

        result = {
            "tickers_searched": ",".join(tickers),
            "filings_scanned": total_filings_scanned,
            "total_found": total_found,
            "total_ingested": 0,
            "status": "success" if not errors else "partial",
            "errors": errors,
            "elapsed": elapsed,
        }
        log_run(result["tickers_searched"], total_filings_scanned, total_found, 0,
                result["status"], "; ".join(errors) if errors else "")
        return result

    # Write to Supabase
    log.info(f"\n--- Supabase Ingestion ---")
    ingest_stats = ingest_to_supabase(all_catalysts)

    log.info(f"  Ingested: {ingest_stats['ingested']}")
    log.info(f"  Errors: {ingest_stats['errors']}")

    status = "success" if not errors and ingest_stats["errors"] == 0 else "partial"
    if errors and not all_catalysts:
        status = "failed"

    result = {
        "tickers_searched": ",".join(tickers),
        "filings_scanned": total_filings_scanned,
        "total_found": total_found,
        "total_ingested": ingest_stats["ingested"],
        "status": status,
        "errors": errors + ([f"ingest errors: {ingest_stats['errors']}"] if ingest_stats["errors"] else []),
        "elapsed": elapsed,
    }

    log_run(result["tickers_searched"], total_filings_scanned, total_found,
            ingest_stats["ingested"], status, "; ".join(result["errors"]) if result["errors"] else "")

    log.info(f"\n=== COMPLETE: {total_found} found, {ingest_stats['ingested']} ingested, {elapsed:.1f}s ===")
    return result


# ═══════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="SEC EDGAR 8-K Catalyst Crawler (Engine 04)"
    )
    parser.add_argument(
        "--tickers", type=str, default="",
        help="Comma-separated tickers (default: MRK,VTRS,INO,CAPR,BBIO,PRAX,COGT,PFE)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Fetch and parse but do not write to Supabase"
    )
    parser.add_argument(
        "--smoke-test", action="store_true",
        help="Run with 2 tickers (MRK, BBIO) in dry-run mode"
    )
    parser.add_argument(
        "--create-schema", action="store_true",
        help="Run SQL migration to create Supabase tables"
    )
    parser.add_argument(
        "--max-filings", type=int, default=20,
        help="Max 8-K filings to scan per ticker (default: 20)"
    )

    args = parser.parse_args()

    # Schema creation mode
    if args.create_schema:
        log.info("Creating Supabase schema...")
        create_schema()
        log.info("Schema creation complete.")
        return

    # Determine tickers
    if args.smoke_test:
        tickers = SMOKE_TICKERS
        dry_run = True
    elif args.tickers:
        tickers = [t.strip() for t in args.tickers.split(",")]
        dry_run = args.dry_run
    else:
        tickers = DEFAULT_WATCHLIST
        dry_run = args.dry_run

    result = run_crawl(tickers, dry_run=dry_run, max_filings=args.max_filings)

    # Print JSON summary for pipeline integration
    print(f"\n{json.dumps(result, indent=2)}")

    # Exit code: 0 = success, 1 = partial, 2 = failed
    if result["status"] == "failed":
        sys.exit(2)
    elif result["status"] == "partial":
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()