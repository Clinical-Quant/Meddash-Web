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
    python edgar_catalyst_crawler.py --clean                  # Delete all rows

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
from datetime import datetime, date, timedelta, timezone
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
LOOKBACK_DAYS = 365  # Backfill 12 months

# ── Watchlist asset alias map (ticker → {alias: canonical_name}) ──
ASSET_ALIASES = {
    "BBIO": {"bbp-418": "ribitol", "ribitol": "ribitol", "bpb-418": "ribitol",
             "encaleret": "encaleret", "neladenoson": "neladenoson",
             "acdenoson": "acdenoson", "bmx-001": "bmx-001"},
    "CAPR": {"cap-1002": "deramiocel", "deramiocel": "deramiocel",
             "celdar": "celdar"},
    "INO": {"ino-3107": "INO-3107", "ino-4800": "INO-4800",
            "ino-4700": "INO-4700", "vgx-3100": "VGX-3100"},
    "COGT": {"cgt1145": "bezuclastinib", "bezuclastinib": "bezuclastinib",
             "cgt-1145": "bezuclastinib", "blu-281": "bezuclastinib"},
    "PRAX": {"prax-562": "relutrigine", "relutrigine": "relutrigine",
             "prax-628": "ulsacrine", "ulsacrine": "ulsacrine",
             "prax-114": "PRAX-114"},
    "PFE": {"elranatamab": "elranatamab", "zavegepant": "zavegepant",
             "tafamidis": "tafamidis", "vyndaqel": "tafamidis",
             "vypadca": "vypadca", "abrysvo": "abrysvo",
             "prevnar": "prevnar", "pomalyst": "pomalyst"},
    "MRK": {"pembrolizumab": "pembrolizumab", "keytruda": "pembrolizumab",
            "welireg": "belzutifan", "belzutifan": "belzutifan",
            "winrevair": "sotatercept", "sotatercept": "sotatercept",
            "capvaxive": "capvaxive", "v116": "capvaxive"},
    "VTRS": {"amlodipine": "amlodipine", "atorvastatin": "atorvastatin"},
}

# ── Regex patterns (case-insensitive, from spec) ──
RE_PDUFA = re.compile(
    r'PDUFA\s+(?:target\s+action\s+)?date\s+(?:of\s+)?([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})',
    re.IGNORECASE
)
RE_PDUFA_EXTENSION = re.compile(
    r'extend\w*?.{0,60}?PDUFA.{0,60}?from\s+([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})\s+to\s+([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})',
    re.IGNORECASE | re.DOTALL
)
# Broadened: catch "top-line data expected Q4 2026" AND "in the last quarter of 2026"
# AND "second half of 2026" AND quarter/half references tied to action dates
RE_READOUT_WINDOW = re.compile(
    r'(?:top-line|topline|top line|readout|data)\s+(?:data\s+)?(?:expected|anticipated|due|slated|planned).{0,60}?'
    r'(Q[1-4]\s+\d{4}|H[12]\s+\d{4}|'
    r'(?:first|second|third|fourth|last)\s+quarter\s+(?:of\s+)?\d{4}|'
    r'(?:first|second)\s+half\s+(?:of\s+)?\d{4})',
    re.IGNORECASE | re.DOTALL
)
# Also catch standalone "PDUFA ... in Q4 2026" / "approval in H2 2026"
RE_WINDOW_NEAR_PDUFA = re.compile(
    r'PDUFA.{0,100}?'
    r'(Q[1-4]\s+\d{4}|H[12]\s+\d{4}|'
    r'(?:first|second|third|fourth|last)\s+quarter\s+(?:of\s+)?\d{4}|'
    r'(?:first|second)\s+half\s+(?:of\s+)?\d{4})',
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

# ── Asset extraction patterns ──
# Drug code patterns: XXX-### or XXX#### (e.g., BBP-418, MK-8748, INO-3107)
RE_DRUG_CODE_DASH = re.compile(r'\b([A-Z]{2,5}-\d{3,5})\b')
RE_DRUG_CODE_NODASH = re.compile(r'\b([A-Z]{2,5}\d{3,5})\b')
# Known drug names (generic/brand) — used for proximity matching, not whole-doc
RE_DRUG_NAME = re.compile(
    r'\b(pembrolizumab|nivolumab|tofersen|ribitol|amiloride|lenmeldy|cobomarsen|'
    r'remdesivir|encaleret|belzutifan|welireg|sotatercept|winrevair|capvaxive|'
    r'keytruda|opdivo|deramiocel|relutrigine|bezuclastinib|elranatamab|'
    r'zavegepant|tafamidis|ulsacrine|neladenoson|acdenoson)\b',
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


def get_recent_8k_filings(cik: str, max_filings: int = 40,
                          lookback_days: int = LOOKBACK_DAYS) -> list[dict]:
    """Get 8-K filings for a CIK within the lookback window.

    Uses the submissions 'recent' block (covers ~1000 most recent filings).
    Filters by date to ensure 12-month coverage, not just last-N.
    """
    data = fetch_submissions(cik)
    recent = data.get("filings", {}).get("recent", {})

    forms = recent.get("form", [])
    accession_numbers = recent.get("accessionNumber", [])
    filing_dates = recent.get("filingDate", [])
    primary_docs = recent.get("primaryDocument", [])
    primary_desc = recent.get("primaryDocDescription", [])

    cutoff = (date.today() - timedelta(days=lookback_days)).isoformat()

    filings = []
    for i, form in enumerate(forms):
        if form != "8-K":
            continue
        fdate = filing_dates[i] if i < len(filing_dates) else ""
        if fdate < cutoff:
            continue
        accession = accession_numbers[i]
        filings.append({
            "accession_number": accession,
            "filing_date": fdate,
            "primary_document": primary_docs[i] if i < len(primary_docs) else "",
            "primary_doc_description": primary_desc[i] if i < len(primary_desc) else "",
            "cik": cik,
        })
        if len(filings) >= max_filings:
            break

    return filings


def search_edgar_fulltext(ticker: str, cik: str, terms: list[str],
                          lookback_days: int = LOOKBACK_DAYS) -> list[dict]:
    """Use EDGAR full-text search to find 8-K filings matching catalyst terms.

    This supplements the submissions-based lookback by searching across
    filing history for specific terms like 'PDUFA', 'complete response letter'.
    """
    filings = []
    cutoff = (date.today() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    for term in terms:
        try:
            params = {
                "q": f'"{term}"',
                "forms": "8-K",
                "dateRange": f"custom,{cutoff},{date.today().isoformat()}",
            }
            query_string = urllib.parse.urlencode(params)
            url = f"{EDGAR_SEARCH_URL}?{query_string}"
            req = urllib.request.Request(url, headers=EDGAR_HEADERS)
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            hits = data.get("hits", {}).get("hits", [])
            for hit in hits:
                source = hit.get("_source", {})
                hit_cik = source.get("entity_cik", "").zfill(10)
                if hit_cik != cik:
                    continue
                accession = source.get("accession_no", "")
                if accession:
                    filings.append({
                        "accession_number": accession,
                        "filing_date": source.get("file_date", ""),
                        "primary_document": source.get("primary_doc", ""),
                        "primary_doc_description": "",
                        "cik": cik,
                        "_source": "fulltext_search",
                    })
            time.sleep(REQUEST_DELAY)
        except Exception as e:
            log.warning(f"  Full-text search failed for term '{term}': {str(e)[:60]}")

    return filings


def dedupe_filings(filings: list[dict]) -> list[dict]:
    """Deduplicate filings by accession_number, preferring submissions source."""
    seen = {}
    for f in filings:
        acc = f["accession_number"]
        if acc not in seen:
            seen[acc] = f
        elif "_source" in f and "_source" not in seen[acc]:
            # Keep the fulltext-found one if submissions didn't have it
            seen[acc] = f
    return list(seen.values())


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
    text = re.sub(r'&[a-z]+;', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_excerpt(full_text: str, match_start: int, match_end: int,
                    context_chars: int = 400) -> str:
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
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%B %d %Y", "%b %d %Y"):
        try:
            dt = datetime.strptime(date_str.strip().rstrip(','), fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return date_str.strip()


def normalize_window(window_str: str) -> str:
    """Normalize window strings to consistent format."""
    s = window_str.strip()
    # "last quarter of 2026" → "Q4 2026"
    s = re.sub(r'(?:fourth|last)\s+quarter\s+(?:of\s+)?(\d{4})', r'Q4 \1', s, flags=re.IGNORECASE)
    s = re.sub(r'first\s+quarter\s+(?:of\s+)?(\d{4})', r'Q1 \1', s, flags=re.IGNORECASE)
    s = re.sub(r'second\s+quarter\s+(?:of\s+)?(\d{4})', r'Q2 \1', s, flags=re.IGNORECASE)
    s = re.sub(r'third\s+quarter\s+(?:of\s+)?(\d{4})', r'Q3 \1', s, flags=re.IGNORECASE)
    s = re.sub(r'first\s+half\s+(?:of\s+)?(\d{4})', r'H1 \1', s, flags=re.IGNORECASE)
    s = re.sub(r'second\s+half\s+(?:of\s+)?(\d{4})', r'H2 \1', s, flags=re.IGNORECASE)
    return s


def is_date_in_past(date_str: str) -> bool:
    """Check if a date or window string is before today.

    Handles:
    - Exact dates: '2026-11-27'
    - Window dates: 'Q1 2026', 'H1 2027', 'Q4 2025'
    """
    # Try exact date first
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        return d < date.today()
    except ValueError:
        pass

    # Window dates — parse quarter/half and year
    m = re.match(r'Q([1-4])\s+(\d{4})', date_str)
    if m:
        q, yr = int(m.group(1)), int(m.group(2))
        # Q1 ends Mar 31, Q2 ends Jun 30, Q3 ends Sep 30, Q4 ends Dec 31
        end_dates = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}
        mo, day = end_dates[q]
        quarter_end = date(yr, mo, day)
        return quarter_end < date.today()

    m = re.match(r'H([12])\s+(\d{4})', date_str)
    if m:
        h, yr = int(m.group(1)), int(m.group(2))
        # H1 ends Jun 30, H2 ends Dec 31
        mo, day = (6, 30) if h == 1 else (12, 31)
        half_end = date(yr, mo, day)
        return half_end < date.today()

    # Unknown format — assume upcoming (safe default)
    return False


# ═══════════════════════════════════════════════════════════════════════
# Asset Extraction — proximity-based (fix #2, #4)
# ═══════════════════════════════════════════════════════════════════════

def _extract_asset_near(doc_text: str, match_start: int, match_end: int,
                        ticker: str, company: str) -> str:
    """Extract drug/asset name from the text NEAR a date hit, not whole-document.

    Strategy:
    1. Check alias map for ticker-specific known assets first (highest priority)
    2. Search within ±500 chars of the match for drug names in the alias map
    3. Search within ±500 chars for drug code patterns (XXX-###, XXX####)
    4. Fall back to UNKNOWN

    Note: We do NOT use a global drug-name regex — that caused Merck's
    pembrolizumab to appear on Pfizer rows. Only ticker-specific alias
    entries are checked.
    """
    context_start = max(0, match_start - 500)
    context_end = min(len(doc_text), match_end + 500)
    context = doc_text[context_start:context_end]
    context_lower = context.lower()

    # Step 1: Check ticker-specific alias map
    aliases = ASSET_ALIASES.get(ticker.upper(), {})
    for alias, canonical in aliases.items():
        if alias.lower() in context_lower:
            return canonical

    # Step 2: Skip global drug name search — ticker-specific aliases only
    # (This prevents cross-company misattribution)

    # Step 3: Search for drug code patterns in the context window
    for m in RE_DRUG_CODE_DASH.finditer(context):
        candidate = m.group(1).upper()
        # Skip exhibit references (EX-99)
        if candidate.startswith("EX") and "99" in candidate:
            continue
        if candidate in ("HTTP", "HTTPS", "HTML"):
            continue
        # Skip SEC filing-like codes (too many digits)
        if len(candidate) > 10:
            continue
        return candidate

    for m in RE_DRUG_CODE_NODASH.finditer(context):
        candidate = m.group(1).upper()
        if candidate.startswith("EX") and "99" in candidate:
            continue
        if candidate in ("HTTP", "HTTPS", "HTML"):
            continue
        if len(candidate) > 10:
            continue
        return candidate

    return "UNKNOWN"


def _extract_indication_near(doc_text: str, match_start: int, match_end: int) -> str:
    """Extract indication from text NEAR a date hit."""
    context_start = max(0, match_start - 400)
    context_end = min(len(doc_text), match_end + 400)
    context = doc_text[context_start:context_end]

    contexts = [
        re.compile(r'(?:treatment\s+of|for\s+the\s+treatment\s+of)\s+([a-zA-Z][a-zA-Z\s]{3,40}?)(?:[.,;]|based|in\s+(?:the\s+)?U\.S|Phase)', re.IGNORECASE),
        re.compile(r'patients?\s+(?:with|suffering\s+from)\s+([a-zA-Z][a-zA-Z\s]{3,40}?)(?:[.,;]|based|Phase|who)', re.IGNORECASE),
        re.compile(r'(?:for|in)\s+(?:adults?\s+(?:with|suffering\s+from)\s+)?([a-zA-Z][a-zA-Z\s]{3,40}?)(?:[.,;]|based|Phase)', re.IGNORECASE),
    ]
    for ctx in contexts:
        m = ctx.search(context)
        if m:
            indication = m.group(1).strip()
            lower = indication.lower()
            if any(bad in lower for bad in ["the company", "this", "its", "total second",
                                             "oncology and animal", "news release", "the treatment"]):
                continue
            if len(indication) > 5:
                return indication
    return None


# ═══════════════════════════════════════════════════════════════════════
# Catalyst Extraction
# ═══════════════════════════════════════════════════════════════════════

def extract_catalysts_from_text(
    doc_text: str, ticker: str, cik: str, company: str,
    accession_number: str, filing_date: str, filing_index_url: str
) -> list[dict]:
    """Extract catalyst events from filing document text using regex patterns.

    Asset and indication are extracted from the context NEAR each date hit,
    not from the whole document. This prevents Merck's drug from appearing
    on Pfizer rows.
    """
    catalysts = []

    def make_event(event_type: str, date_or_window: str, date_precision: str,
                   excerpt: str, match_start: int, match_end: int,
                   priority_review: bool = False) -> dict:
        asset = _extract_asset_near(doc_text, match_start, match_end, ticker, company)
        indication = _extract_indication_near(doc_text, match_start, match_end)
        return {
            "company": company,
            "ticker": ticker,
            "cik": cik,
            "asset": asset,
            "indication": indication,
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
        catalysts.append(make_event("PDUFA", new_date, "exact", excerpt, m.start(), m.end()))
        log.info(f"    PDUFA EXTENSION: {old_date} → {new_date}")

    # PDUFA date (skip if already found via extension)
    pdufa_found = any(c["event_type"] == "PDUFA" for c in catalysts)
    if not pdufa_found:
        for m in RE_PDUFA.finditer(doc_text):
            parsed = parse_date_string(m.group(1))
            excerpt = extract_excerpt(doc_text, m.start(), m.end())
            nearby = doc_text[max(0, m.start()-300):m.end()+300]
            priority = "priority review" in nearby.lower()
            catalysts.append(make_event("PDUFA", parsed, "exact", excerpt, m.start(), m.end(), priority))
            log.info(f"    PDUFA date: {parsed}")

    # Readout window — broadened to catch quarter/half references
    for m in RE_READOUT_WINDOW.finditer(doc_text):
        raw_window = m.group(1).strip()
        window = normalize_window(raw_window)
        excerpt = extract_excerpt(doc_text, m.start(), m.end())
        catalysts.append(make_event("readout_window", window, "window", excerpt, m.start(), m.end()))
        log.info(f"    Readout window: {window}")

    # Also catch "PDUFA ... in Q4 2026" style (window near PDUFA mention)
    for m in RE_WINDOW_NEAR_PDUFA.finditer(doc_text):
        raw_window = m.group(1).strip()
        window = normalize_window(raw_window)
        # Only add if not already captured as exact PDUFA date
        if not any(c["event_type"] == "PDUFA" for c in catalysts):
            excerpt = extract_excerpt(doc_text, m.start(), m.end())
            catalysts.append(make_event("PDUFA", window, "window", excerpt, m.start(), m.end()))
            log.info(f"    PDUFA window: {window}")

    # AdCom
    for m in RE_ADCOM.finditer(doc_text):
        parsed = parse_date_string(m.group(1))
        excerpt = extract_excerpt(doc_text, m.start(), m.end())
        catalysts.append(make_event("AdCom", parsed, "exact", excerpt, m.start(), m.end()))
        log.info(f"    AdCom date: {parsed}")

    # Approval — only capture once per filing
    approval_found = False
    for m in RE_APPROVAL.finditer(doc_text):
        if not approval_found:
            excerpt = extract_excerpt(doc_text, m.start(), m.end())
            catalysts.append(make_event("approval", filing_date, "exact", excerpt, m.start(), m.end()))
            log.info(f"    FDA approval mention on {filing_date}")
            approval_found = True

    # CRL — only capture once per filing
    crl_found = False
    for m in RE_CRL.finditer(doc_text):
        if not crl_found:
            excerpt = extract_excerpt(doc_text, m.start(), m.end())
            catalysts.append(make_event("CRL", filing_date, "exact", excerpt, m.start(), m.end()))
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
        index_data = fetch_filing_index(cik, accession)
        items = index_data.get("directory", {}).get("item", [])

        # Collect HTM documents to parse (primary 8-K body + EX-99 exhibits)
        docs_to_parse = []
        for item in items:
            name = item.get("name", "")
            if name.endswith(".htm") or name.endswith(".html"):
                if "index" in name.lower():
                    continue
                name_lower = name.lower()
                is_primary = (name == filing.get("primary_document"))
                is_exhibit = ("ex-99" in name_lower or "ex99" in name_lower or
                              "_ex-99" in name_lower or "_ex99" in name_lower)
                if is_primary or is_exhibit:
                    doc_url = f"{filing_index_url}{name}"
                    docs_to_parse.append((name, doc_url))

        if not docs_to_parse:
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


def clean_table():
    """Delete all rows from catalyst_events (for re-ingestion after fixes)."""
    engine = get_pg_engine()
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM catalyst_events"))
        conn.commit()
    log.info("Cleaned all rows from catalyst_events")


def ingest_to_supabase(catalysts: list[dict]) -> dict:
    """Upsert catalyst events to Supabase catalyst_events table.

    Fix #3: When a new row has asset=UNKNOWN but an existing row with the same
    (ticker, event_type, date_or_window) already has a resolved asset, skip the
    UNKNOWN row instead of creating a duplicate with a different composite key.
    """
    if not catalysts:
        return {"ingested": 0, "errors": 0, "skipped_unknown": 0}

    engine = get_pg_engine()
    conn = engine.connect()

    # Fetch existing rows to check for UNKNOWN merge (fix #3)
    existing_rows = {}
    try:
        r = conn.execute(text(
            "SELECT ticker, asset, event_type, date_or_window FROM catalyst_events"
        ))
        for row in r.fetchall():
            key = (row[0], row[2], row[3])  # (ticker, event_type, date_or_window)
            existing_rows[key] = row[1]  # asset
    except Exception:
        pass  # Table might be empty

    ingested = 0
    errors = 0
    skipped_unknown = 0

    for catalyst in catalysts:
        try:
            # Fix #3: Skip UNKNOWN rows when a resolved asset already exists
            # for the same (ticker, event_type, date_or_window)
            merge_key = (catalyst["ticker"], catalyst["event_type"], catalyst["date_or_window"])
            if catalyst["asset"] == "UNKNOWN" and merge_key in existing_rows:
                existing_asset = existing_rows[merge_key]
                if existing_asset and existing_asset != "UNKNOWN":
                    log.info(f"  Skip UNKNOWN {catalyst['ticker']} {catalyst['event_type']} — "
                             f"existing asset: {existing_asset}")
                    skipped_unknown += 1
                    continue

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
                "verification_status": catalyst.get("verification_status", "unverified"),
                "verification_note": catalyst.get("verification_note"),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
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
            # Update the in-memory existing map
            existing_rows[(catalyst["ticker"], catalyst["event_type"],
                          catalyst["date_or_window"])] = catalyst["asset"]
        except Exception as e:
            errors += 1
            conn.rollback()
            if errors <= 5:
                log.warning(f"  Failed to upsert {catalyst['ticker']} {catalyst['event_type']}: {str(e)[:80]}")

    conn.commit()
    conn.close()

    return {"ingested": ingested, "errors": errors, "skipped_unknown": skipped_unknown}


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

def run_crawl(tickers: list[str], dry_run: bool = False, max_filings: int = 40,
              use_fulltext: bool = True, verify: bool = False) -> dict:
    """Run the EDGAR catalyst crawl for a list of tickers.

    Args:
        tickers: List of ticker symbols
        dry_run: If True, don't write to Supabase
        max_filings: Max 8-K filings to scan per ticker
        use_fulltext: If True, also use EDGAR full-text search to find filings
        verify: If True, run LLM verification gate on candidates before ingest
    """
    log.info("=" * 60)
    log.info("EDGAR CATALYST CRAWLER — Engine 04")
    log.info(f"Tickers: {', '.join(tickers)}")
    log.info(f"Dry run: {dry_run}")
    log.info(f"Max filings per ticker: {max_filings}")
    log.info(f"Lookback: {LOOKBACK_DAYS} days")
    log.info(f"Full-text search: {use_fulltext}")
    log.info("=" * 60)

    start_time = time.time()
    all_catalysts = []
    total_filings_scanned = 0
    errors = []

    # Catalyst search terms for full-text search
    fts_terms = ["PDUFA", "complete response letter", "advisory committee",
                 "FDA approved", "top-line data"]

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

        # Step 1: Get 8-K filings from submissions (lookback-filtered)
        try:
            filings = get_recent_8k_filings(cik, max_filings=max_filings)
        except Exception as e:
            log.warning(f"  Failed to fetch submissions for {ticker}: {str(e)[:80]}")
            errors.append(f"{ticker}: submissions fetch failed — {str(e)[:60]}")
            continue

        log.info(f"  Submissions: {len(filings)} 8-K filings in {LOOKBACK_DAYS}d lookback")

        # Step 2: Supplement with EDGAR full-text search (fix #1)
        if use_fulltext:
            time.sleep(REQUEST_DELAY)
            fts_filings = search_edgar_fulltext(ticker, cik, fts_terms)
            if fts_filings:
                log.info(f"  Full-text search: {len(fts_filings)} additional filings found")
                # Merge and dedupe
                all_filings = dedupe_filings(filings + fts_filings)
            else:
                all_filings = filings
        else:
            all_filings = filings

        log.info(f"  Total unique filings to scan: {len(all_filings)}")
        total_filings_scanned += len(all_filings)

        if not all_filings:
            continue

        # Process each filing
        for filing in all_filings:
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

    # Fix #3 pre-ingest: suppress UNKNOWN rows when resolved asset exists
    # Group by (ticker, event_type, date_or_window) and prefer resolved assets
    asset_resolved = {}
    for c in all_catalysts:
        key = (c["ticker"], c["event_type"], c["date_or_window"])
        if c["asset"] != "UNKNOWN":
            asset_resolved[key] = c["asset"]

    # Also build a ticker+event_type → dominant asset map
    # If all resolved assets for a (ticker, event_type) pair are the same,
    # use that to fill UNKNOWN rows of the same pair
    ticker_event_assets = {}
    for c in all_catalysts:
        if c["asset"] != "UNKNOWN":
            key = (c["ticker"], c["event_type"])
            if key not in ticker_event_assets:
                ticker_event_assets[key] = set()
            ticker_event_assets[key].add(c["asset"])

    ticker_event_dominant = {}
    for key, assets in ticker_event_assets.items():
        if len(assets) == 1:
            ticker_event_dominant[key] = assets.pop()

    if asset_resolved or ticker_event_dominant:
        filtered = []
        suppressed = 0
        for c in all_catalysts:
            key_exact = (c["ticker"], c["event_type"], c["date_or_window"])
            key_event = (c["ticker"], c["event_type"])

            if c["asset"] == "UNKNOWN":
                # Exact match on (ticker, event_type, date_or_window)
                if key_exact in asset_resolved:
                    log.info(f"  Suppress UNKNOWN {c['ticker']} {c['event_type']} "
                             f"{c['date_or_window']} — resolved asset: {asset_resolved[key_exact]}")
                    suppressed += 1
                    continue
                # Dominant asset for (ticker, event_type)
                if key_event in ticker_event_dominant:
                    dominant = ticker_event_dominant[key_event]
                    log.info(f"  Fill UNKNOWN {c['ticker']} {c['event_type']} "
                             f"{c['date_or_window']} — dominant asset: {dominant}")
                    c["asset"] = dominant
            filtered.append(c)
        all_catalysts = filtered
        if suppressed:
            log.info(f"  Suppressed {suppressed} UNKNOWN rows in favor of resolved assets")

    total_found = len(all_catalysts)

    # ── Stage 2: LLM Verification Gate ──
    verify_passed = 0
    verify_failed = 0
    if verify and all_catalysts:
        try:
            from edgar_llm_verifier import verify_candidates
            log.info(f"\n--- Stage 2: LLM Verification Gate ({len(all_catalysts)} candidates) ---")
            verified_results = verify_candidates(all_catalysts)

            # Split into verified and rejected
            verified_rows = [r for r in verified_results if r["verification_status"] == "verified"]
            rejected_rows = [r for r in verified_results if r["verification_status"] == "rejected"]
            error_rows = [r for r in verified_results if r["verification_status"] == "error"]

            verify_passed = len(verified_rows)
            verify_failed = len(rejected_rows)

            # Keep verified + error rows (errors are unverified, not rejected)
            # Rejected rows are still ingested but flagged for audit
            all_catalysts = verified_rows + error_rows + rejected_rows

            log.info(f"  Verified: {verify_passed}")
            log.info(f"  Rejected: {verify_failed}")
            log.info(f"  Errors (kept as unverified): {len(error_rows)}")

            # Update total_found after verification
            total_found = len(all_catalysts)

        except ImportError:
            log.warning("  edgar_llm_verifier not available — skipping verification")
        except Exception as e:
            log.warning(f"  LLM verification failed: {str(e)[:80]} — keeping unverified")

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
        if not dry_run:
            log_run(result["tickers_searched"], total_filings_scanned, total_found, 0,
                    result["status"], "; ".join(errors) if errors else "")
        return result

    # Write to Supabase
    log.info(f"\n--- Supabase Ingestion ---")
    ingest_stats = ingest_to_supabase(all_catalysts)

    log.info(f"  Ingested: {ingest_stats['ingested']}")
    log.info(f"  Skipped UNKNOWN (merged): {ingest_stats.get('skipped_unknown', 0)}")
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
        "verified": verify_passed,
        "rejected": verify_failed,
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
        "--clean", action="store_true",
        help="Delete all rows from catalyst_events before running"
    )
    parser.add_argument(
        "--max-filings", type=int, default=40,
        help="Max 8-K filings to scan per ticker (default: 40)"
    )
    parser.add_argument(
        "--no-fulltext", action="store_true",
        help="Disable EDGAR full-text search (submissions only)"
    )
    parser.add_argument(
        "--verify", action="store_true",
        help="Run LLM verification gate on candidates (Stage 2, requires Ollama)"
    )

    args = parser.parse_args()

    # Schema creation mode
    if args.create_schema:
        log.info("Creating Supabase schema...")
        create_schema()
        log.info("Schema creation complete.")
        return

    # Clean mode
    if args.clean:
        log.info("Cleaning catalyst_events table...")
        clean_table()

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

    result = run_crawl(tickers, dry_run=dry_run, max_filings=args.max_filings,
                       use_fulltext=not args.no_fulltext, verify=args.verify)

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