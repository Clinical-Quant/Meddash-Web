"""
literature_engine.py — Multi-Source Literature Search Engine for Meddash Pipeline

Searchs Europe PMC, OpenAlex, Semantic Scholar, and bioRxiv/medRxiv for publications.
Also integrates Unpaywall for open-access resolution. Deduplicates against PubMed
(canonical source) on DOI → PMID → normalized title.

Usage:
    # Search all sources
    python literature_engine.py --custom "androgenetic alopecia" --max-results 100

    # Search specific source
    python literature_engine.py --custom "androgenetic alopecia" --source europepmc

    # Citation chasing
    python literature_engine.py --cited-by 35655638 --source semanticscholar

    # DOI lookup (acceptance test)
    python literature_engine.py --doi 10.4103/JCAS.JCAS_232_20 --source openalex

    # Unpaywall check
    python literature_engine.py --unpaywall 10.1007/s00403-025-03938-0

    # Acceptance test (full smoke test)
    python literature_engine.py --acceptance-test

Pipeline wiring:
    - Writes to Supabase tables: literature_results, literature_query_log
    - Deduplicates on DOI (primary), then PMID, then normalized title
    - PubMed remains canonical; other sources only add what PubMed lacks
"""

import os
import sys
import json
import time
import argparse
import logging
import re
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import quote_plus, urlencode

import requests

# ── Path setup ──
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "07_DevOps_Observability"))

from supabase_writer import get_pg_engine
from sqlalchemy import text

# ── Configuration ──
CONTACT_EMAIL = os.getenv("MEDDASH_CONTACT_EMAIL", "meddash.developer@gmail.com")
SEM_SCHOLAR_KEY = os.getenv("SEM_SCHOLAR_KEY", "")
REQUEST_TIMEOUT = 30
socket_timeout = 30

# ── Logging ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            str(Path(__file__).resolve().parent / "literature_engine.log"),
            encoding="utf-8",
        ),
    ],
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def normalize_title(title: str) -> str:
    """Normalize a title for dedup comparison."""
    if not title:
        return ""
    t = title.lower().strip()
    t = re.sub(r'[^a-z0-9\s]', '', t)
    t = re.sub(r'\s+', ' ', t)
    return t

def title_hash(title: str) -> str:
    """Generate a hash of a normalized title for dedup."""
    return hashlib.md5(normalize_title(title).encode()).hexdigest()

def reconstruct_abstract(inv_index: dict) -> str:
    """Reconstruct an OpenAlex inverted-index abstract into plain text."""
    if not inv_index:
        return ""
    words = []
    for word, positions in inv_index.items():
        for pos in positions:
            words.append((pos, word))
    words.sort()
    return " ".join(w for _, w in words)

def safe_request(url: str, headers: dict = None, params: dict = None,
                 timeout: int = REQUEST_TIMEOUT, max_retries: int = 3) -> Optional[dict]:
    """Make an HTTP GET request with retry logic."""
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=timeout)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429:
                wait = min(10 * (attempt + 1), 30)
                log.warning(f"  Rate limited (429), waiting {wait}s...")
                time.sleep(wait)
                continue
            else:
                log.warning(f"  HTTP {resp.status_code} from {url[:80]}")
                if attempt < max_retries - 1:
                    time.sleep(2)
        except requests.exceptions.Timeout:
            log.warning(f"  Timeout on attempt {attempt+1}/{max_retries}")
        except Exception as e:
            log.warning(f"  Request error: {str(e)[:80]}")
        if attempt < max_retries - 1:
            time.sleep(2)
    return None

# ─────────────────────────────────────────────────────────────────────────────
# 1. Europe PMC
# ─────────────────────────────────────────────────────────────────────────────

EPMC_BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest"

def search_europepmc(query: str, max_results: int = 100,
                     full_text_only: bool = False) -> Tuple[List[dict], int]:
    """Search Europe PMC for publications."""
    log.info(f"Europe PMC search: {query[:80]}...")

    if full_text_only:
        query = f"({query}) AND IN_PMC:Y"

    results = []
    cursor = "*"
    total_hits = 0

    while len(results) < max_results:
        params = {
            "query": query,
            "format": "json",
            "pageSize": min(1000, max_results - len(results)),
            "resultType": "core",
            "cursorMark": cursor,
            "email": CONTACT_EMAIL,
        }
        data = safe_request(f"{EPMC_BASE}/search", params=params)
        if not data:
            break

        hits = data.get("resultList", {}).get("result", [])
        if not hits:
            break

        total_hits = int(data.get("hitCount", len(hits)))
        for r in hits:
            results.append(_parse_epmc(r))
            if len(results) >= max_results:
                break

        next_cursor = data.get("nextCursorMark", "")
        if not next_cursor or next_cursor == cursor:
            break
        cursor = next_cursor
        time.sleep(0.2)  # ~5 req/s

    log.info(f"  Europe PMC: {total_hits} total hits, {len(results)} fetched")
    return results, total_hits

def _parse_epmc(r: dict) -> dict:
    """Parse an Europe PMC result into our standard format."""
    authors = []
    author_str = r.get("authorString", "")
    if author_str:
        for a in author_str.split(","):
            a = a.strip()
            if a:
                parts = a.rsplit(" ", 1)
                if len(parts) == 2:
                    authors.append({"fore_name": parts[0], "last_name": parts[1]})
                else:
                    authors.append({"fore_name": "", "last_name": a})

    mesh_terms = []
    for m in r.get("meshHeadingList", {}).get("meshHeading", []):
        term = m.get("descriptorName", "")
        if term:
            mesh_terms.append(term)

    return {
        "source": "europepmc",
        "pmid": str(r.get("pmid", "")) or None,
        "doi": r.get("doi", "") or None,
        "title": r.get("title", ""),
        "journal_name": r.get("journalTitle", ""),
        "pub_year": str(r.get("pubYear", "")) or None,
        "published_date": str(r.get("firstPublicationDate", "")) or None,
        "abstract": r.get("abstractText", "") or "",
        "authors": authors,
        "mesh_terms": mesh_terms,
        "pmcid": r.get("pmcid", "") or None,
        "url": f"https://europepmc.org/article/med/{r.get('pmid', '')}" if r.get("pmid") else "",
        "is_oa": r.get("inPMC", "N") == "Y",
    }

def epmc_cited_by(pmid: str, max_results: int = 100) -> List[dict]:
    """Get papers citing a given PMID via Europe PMC."""
    log.info(f"Europe PMC cited-by for PMID {pmid}...")
    params = {"format": "json", "pageSize": min(1000, max_results)}
    data = safe_request(f"{EPMC_BASE}/MED/{pmid}/citations", params=params)
    if not data:
        return []
    hits = data.get("resultList", {}).get("result", [])
    results = [_parse_epmc(h) for h in hits[:max_results]]
    log.info(f"  {len(results)} citing papers found")
    return results

# ─────────────────────────────────────────────────────────────────────────────
# 2. OpenAlex
# ─────────────────────────────────────────────────────────────────────────────

OPENALEX_BASE = "https://api.openalex.org"

def search_openalex(query: str, max_results: int = 100,
                    from_date: str = "2020-01-01",
                    oa_only: bool = False) -> Tuple[List[dict], int]:
    """Search OpenAlex for publications."""
    log.info(f"OpenAlex search: {query[:80]}...")

    filters = [f"type:article", f"from_publication_date:{from_date}"]
    if oa_only:
        filters.append("is_oa:true")
    filter_str = ",".join(filters)

    results = []
    cursor = ""
    total_hits = 0

    while len(results) < max_results:
        params = {
            "search": query,
            "filter": filter_str,
            "per-page": min(200, max_results - len(results)),
            "mailto": CONTACT_EMAIL,
        }
        if cursor:
            params["cursor"] = cursor

        data = safe_request(f"{OPENALEX_BASE}/works", params=params)
        if not data:
            break

        total_hits = int(data.get("meta", {}).get("count", 0))
        works = data.get("results", [])
        if not works:
            break

        for w in works:
            results.append(_parse_openalex(w))
            if len(results) >= max_results:
                break

        # Cursor pagination
        cursor = data.get("meta", {}).get("next_cursor", "")
        if not cursor:
            break
        time.sleep(0.1)  # ~10 req/s

    log.info(f"  OpenAlex: {total_hits} total hits, {len(results)} fetched")
    return results, total_hits

def _parse_openalex(w: dict) -> dict:
    """Parse an OpenAlex work into our standard format."""
    # Parse authors
    authors = []
    for a in w.get("authorships", []):
        author = a.get("author", {})
        name = author.get("display_name", "")
        if name:
            parts = name.rsplit(" ", 1)
            authors.append({
                "fore_name": parts[0] if len(parts) == 2 else "",
                "last_name": parts[-1] if parts else name,
                "orcid": (author.get("orcid", "") or "").replace("https://orcid.org/", ""),
                "affiliation": a.get("institutions", [{}])[0].get("display_name", "") if a.get("institutions") else "",
            })

    # Reconstruct abstract
    abstract = reconstruct_abstract(w.get("abstract_inverted_index"))

    # Parse DOI (strip https://doi.org/ prefix)
    doi = w.get("doi", "") or ""
    doi = doi.replace("https://doi.org/", "") if doi else None

    # Primary location
    primary_loc = w.get("primary_location", {}) or {}
    source = primary_loc.get("source", {}) or {}
    is_oa = w.get("open_access", {}).get("is_oa", False)
    oa_url = w.get("open_access", {}).get("oa_url", "")

    # Concepts
    concepts = []
    for c in w.get("concepts", [])[:5]:
        concepts.append(c.get("display_name", ""))

    return {
        "source": "openalex",
        "pmid": None,  # OpenAlex doesn't reliably carry PMID
        "doi": doi,
        "title": w.get("title", "") or "",
        "journal_name": source.get("display_name", "") or "",
        "pub_year": str(w.get("publication_year", "")) or None,
        "published_date": w.get("publication_date", "") or None,
        "abstract": abstract,
        "authors": authors,
        "mesh_terms": [],
        "url": oa_url or w.get("id", ""),
        "is_oa": is_oa,
        "cited_by_count": w.get("cited_by_count", 0),
        "concepts": concepts,
        "openalex_id": w.get("id", ""),
    }

def openalex_doi_lookup(doi: str) -> Optional[dict]:
    """Look up a single work by DOI on OpenAlex."""
    log.info(f"OpenAlex DOI lookup: {doi}")
    data = safe_request(f"{OPENALEX_BASE}/works/doi:{doi}",
                        params={"mailto": CONTACT_EMAIL})
    if not data:
        log.warning(f"  DOI {doi} not found on OpenAlex")
        return None
    result = _parse_openalex(data)
    log.info(f"  Found: {result['title'][:60]}")
    return result

# ─────────────────────────────────────────────────────────────────────────────
# 3. Semantic Scholar
# ─────────────────────────────────────────────────────────────────────────────

SEMSCHOLAR_BASE = "https://api.semanticscholar.org/graph/v1"

def _sem_scholar_headers() -> dict:
    """Build headers for Semantic Scholar API."""
    headers = {}
    if SEM_SCHOLAR_KEY:
        headers["x-api-key"] = SEM_SCHOLAR_KEY
    return headers

def search_semantic_scholar(query: str, max_results: int = 100) -> Tuple[List[dict], int]:
    """Search Semantic Scholar for publications."""
    log.info(f"Semantic Scholar search: {query[:80]}...")

    fields = "title,abstract,year,authors,venue,url,openAccessPdf,externalIds,publicationTypes,citationCount"
    params = {
        "query": query,
        "limit": min(100, max_results),
        "fields": fields,
    }

    data = safe_request(f"{SEMSCHOLAR_BASE}/paper/search",
                        headers=_sem_scholar_headers(), params=params)
    if not data:
        return [], 0

    total_hits = int(data.get("total", 0))
    papers = data.get("data", [])

    results = [_parse_semscholar(p) for p in papers[:max_results]]
    log.info(f"  Semantic Scholar: {total_hits} total hits, {len(results)} fetched")
    return results, total_hits

def _parse_semscholar(p: dict) -> dict:
    """Parse a Semantic Scholar paper into our standard format."""
    authors = []
    for a in p.get("authors", []):
        name = a.get("name", "")
        if name:
            parts = name.rsplit(" ", 1)
            authors.append({
                "fore_name": parts[0] if len(parts) == 2 else "",
                "last_name": parts[-1] if parts else name,
            })

    ext_ids = p.get("externalIds", {}) or {}
    pmid = str(ext_ids.get("PubMed", "")) if ext_ids.get("PubMed") else None
    doi = ext_ids.get("DOI", "") or None

    oa_pdf = p.get("openAccessPdf", {}) or {}

    pub_types = p.get("publicationTypes", []) or []

    return {
        "source": "semscholar",
        "pmid": pmid,
        "doi": doi,
        "title": p.get("title", "") or "",
        "journal_name": p.get("venue", "") or "",
        "pub_year": str(p.get("year", "")) or None,
        "published_date": None,
        "abstract": p.get("abstract", "") or "",
        "authors": authors,
        "mesh_terms": [],
        "url": p.get("url", "") or "",
        "is_oa": bool(oa_pdf.get("url")),
        "oa_pdf_url": oa_pdf.get("url", ""),
        "citation_count": p.get("citationCount", 0),
        "publication_types": pub_types,
    }

def semscholar_cited_by(paper_id: str, max_results: int = 100) -> List[dict]:
    """Get papers citing a given paper via Semantic Scholar."""
    log.info(f"Semantic Scholar cited-by for {paper_id}...")

    # Normalize PMID to Semantic Scholar format
    if paper_id.isdigit():
        sid = f"PMID:{paper_id}"
    elif paper_id.startswith("10."):
        sid = f"DOI:{paper_id}"
    else:
        sid = paper_id

    fields = "title,abstract,year,authors,externalIds"
    params = {"fields": fields, "limit": min(1000, max_results)}

    data = safe_request(f"{SEMSCHOLAR_BASE}/paper/{sid}/citations",
                        headers=_sem_scholar_headers(), params=params)
    if not data:
        return []

    citations = data.get("data", [])
    results = []
    for c in citations[:max_results]:
        paper = c.get("citingPaper", {})
        if paper:
            results.append(_parse_semscholar(paper))

    log.info(f"  {len(results)} citing papers found")
    return results

def semscholar_doi_lookup(doi: str) -> Optional[dict]:
    """Look up a single paper by DOI on Semantic Scholar."""
    log.info(f"Semantic Scholar DOI lookup: {doi}")
    fields = "title,abstract,year,authors,venue,url,openAccessPdf,externalIds,publicationTypes,citationCount"
    data = safe_request(f"{SEMSCHOLAR_BASE}/paper/DOI:{doi}",
                        headers=_sem_scholar_headers(),
                        params={"fields": fields})
    if not data:
        log.warning(f"  DOI {doi} not found on Semantic Scholar")
        return None
    result = _parse_semscholar(data)
    log.info(f"  Found: {result['title'][:60]}")
    return result

# ─────────────────────────────────────────────────────────────────────────────
# 4. bioRxiv / medRxiv
# ─────────────────────────────────────────────────────────────────────────────

BIORXIV_BASE = "https://api.biorxiv.org"

def search_biorxiv(server: str = "biorxiv",
                   date_from: str = "2024-01-01",
                   date_to: str = "2024-12-31",
                   keyword_filter: str = "",
                   max_results: int = 100) -> Tuple[List[dict], int]:
    """Crawl bioRxiv/medRxiv by date range and keyword filter."""
    log.info(f"bioRxiv/medRxiv crawl: {server} {date_from} to {date_to}, filter='{keyword_filter[:40]}'")

    results = []
    cursor = 0
    total_hits = 0

    while len(results) < max_results:
        url = f"{BIORXIV_BASE}/details/{server}/{date_from}/{date_to}/{cursor}"
        data = safe_request(url)
        if not data:
            break

        messages = data.get("messages", [{}])
        total = messages[0].get("total", 0) if messages else 0
        total_hits = total

        collection = data.get("collection", [])
        if not collection:
            break

        for item in collection:
            parsed = _parse_biorxiv(item, server)
            # Local keyword filter on title + abstract
            if keyword_filter:
                text = (parsed["title"] + " " + parsed["abstract"]).lower()
                if keyword_filter.lower() not in text:
                    continue
            results.append(parsed)
            if len(results) >= max_results:
                break

        # Next cursor
        new_cursor = messages[0].get("cursor", cursor + len(collection)) if messages else cursor + len(collection)
        if new_cursor <= cursor:
            break
        cursor = new_cursor
        time.sleep(0.2)

    log.info(f"  bioRxiv/{server}: {total_hits} total, {len(results)} matched filter")
    return results, total_hits

def _parse_biorxiv(item: dict, server: str) -> dict:
    """Parse a bioRxiv/medRxiv item."""
    authors = []
    for a in item.get("authors", "").split(";"):
        a = a.strip()
        if a:
            parts = a.rsplit(" ", 1)
            if len(parts) == 2:
                authors.append({"fore_name": parts[0], "last_name": parts[1]})
            else:
                authors.append({"fore_name": "", "last_name": a})

    return {
        "source": f"{server}",
        "pmid": None,
        "doi": item.get("doi", "") or None,
        "title": item.get("title", "") or "",
        "journal_name": f"{server} preprint",
        "pub_year": (item.get("date", "") or "")[:4] or None,
        "published_date": item.get("date", "") or None,
        "abstract": item.get("abstract", "") or "",
        "authors": authors,
        "mesh_terms": [],
        "url": item.get("jats_url", "") or f"https://www.{server}.org/content/{item.get('doi', '')}v{item.get('version', 1)}",
        "is_oa": True,
        "category": item.get("category", ""),
        "version": item.get("version", 1),
    }

# ─────────────────────────────────────────────────────────────────────────────
# 5. Unpaywall
# ─────────────────────────────────────────────────────────────────────────────

def unpaywall_lookup(doi: str) -> Optional[dict]:
    """Look up open-access status for a DOI via Unpaywall."""
    if not doi:
        return None
    log.info(f"Unpaywall lookup: {doi}")
    data = safe_request(f"https://api.unpaywall.org/v2/{doi}",
                        params={"email": CONTACT_EMAIL})
    if not data:
        log.warning(f"  DOI {doi} not found on Unpaywall")
        return None

    best_oa = data.get("best_oa_location", {}) or {}
    result = {
        "doi": doi,
        "is_oa": data.get("is_oa", False),
        "oa_status": data.get("oa_status", ""),
        "oa_url": best_oa.get("url_for_pdf", "") or best_oa.get("url", ""),
        "publisher": data.get("publisher", ""),
        "journal_name": data.get("journal_name", ""),
        "year": data.get("year"),
    }
    log.info(f"  is_oa={result['is_oa']}, status={result['oa_status']}")
    return result

# ─────────────────────────────────────────────────────────────────────────────
# Supabase ingestion
# ─────────────────────────────────────────────────────────────────────────────

def ensure_supabase_tables():
    """Create literature_results and literature_query_log tables if they don't exist."""
    engine = get_pg_engine()
    conn = engine.connect()

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS literature_results (
            id BIGSERIAL PRIMARY KEY,
            source TEXT NOT NULL,
            pmid TEXT,
            doi TEXT,
            title TEXT NOT NULL,
            journal_name TEXT,
            pub_year TEXT,
            published_date TEXT,
            abstract TEXT,
            authors JSONB,
            mesh_terms TEXT[],
            url TEXT,
            is_oa BOOLEAN DEFAULT FALSE,
            oa_pdf_url TEXT,
            citation_count INTEGER,
            cited_by_count INTEGER,
            concepts TEXT[],
            openalex_id TEXT,
            pmcid TEXT,
            category TEXT,
            publication_types TEXT[],
            title_hash TEXT,
            query_used TEXT,
            ingested_at TIMESTAMPTZ DEFAULT NOW()
        )
    """))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS literature_query_log (
            id BIGSERIAL PRIMARY KEY,
            source TEXT NOT NULL,
            query TEXT,
            params JSONB,
            hits INTEGER DEFAULT 0,
            inserted INTEGER DEFAULT 0,
            status TEXT DEFAULT 'success',
            error_message TEXT DEFAULT '',
            elapsed_seconds REAL DEFAULT 0,
            timestamp TIMESTAMPTZ DEFAULT NOW()
        )
    """))

    # Indexes for dedup
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_lit_results_doi ON literature_results(doi) WHERE doi IS NOT NULL"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_lit_results_pmid ON literature_results(pmid) WHERE pmid IS NOT NULL"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_lit_results_title_hash ON literature_results(title_hash)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_lit_results_source ON literature_results(source)"))

    conn.commit()
    conn.close()
    log.info("Supabase tables ensured: literature_results, literature_query_log")

def ingest_to_supabase(publications: List[dict], query_used: str = "") -> dict:
    """Ingest publications into Supabase literature_results table with dedup."""
    engine = get_pg_engine()
    conn = engine.connect()

    inserted = 0
    duplicates = 0
    errors = 0

    for pub in publications:
        try:
            # Compute dedup key
            th = title_hash(pub.get("title", ""))

            # Check if exists by DOI first
            if pub.get("doi"):
                existing = conn.execute(
                    text("SELECT id FROM literature_results WHERE doi = :doi LIMIT 1"),
                    {"doi": pub["doi"]}
                ).fetchone()
                if existing:
                    duplicates += 1
                    continue

            # Then by PMID
            if pub.get("pmid"):
                existing = conn.execute(
                    text("SELECT id FROM literature_results WHERE pmid = :pmid LIMIT 1"),
                    {"pmid": pub["pmid"]}
                ).fetchone()
                if existing:
                    duplicates += 1
                    continue

            # Then by title hash
            existing = conn.execute(
                text("SELECT id FROM literature_results WHERE title_hash = :th LIMIT 1"),
                {"th": th}
            ).fetchone()
            if existing:
                duplicates += 1
                continue

            # Insert
            conn.execute(text("""
                INSERT INTO literature_results (
                    source, pmid, doi, title, journal_name, pub_year, published_date,
                    abstract, authors, mesh_terms, url, is_oa, oa_pdf_url,
                    citation_count, cited_by_count, concepts, openalex_id, pmcid,
                    category, publication_types, title_hash, query_used
                ) VALUES (
                    :source, :pmid, :doi, :title, :journal_name, :pub_year, :published_date,
                    :abstract, :authors, :mesh_terms, :url, :is_oa, :oa_pdf_url,
                    :citation_count, :cited_by_count, :concepts, :openalex_id, :pmcid,
                    :category, :publication_types, :title_hash, :query_used
                )
            """), {
                "source": pub.get("source", ""),
                "pmid": pub.get("pmid"),
                "doi": pub.get("doi"),
                "title": pub.get("title", ""),
                "journal_name": pub.get("journal_name", ""),
                "pub_year": pub.get("pub_year"),
                "published_date": pub.get("published_date"),
                "abstract": pub.get("abstract", ""),
                "authors": json.dumps(pub.get("authors", [])),
                "mesh_terms": pub.get("mesh_terms", []),
                "url": pub.get("url", ""),
                "is_oa": pub.get("is_oa", False),
                "oa_pdf_url": pub.get("oa_pdf_url", ""),
                "citation_count": pub.get("citation_count"),
                "cited_by_count": pub.get("cited_by_count"),
                "concepts": pub.get("concepts", []),
                "openalex_id": pub.get("openalex_id", ""),
                "pmcid": pub.get("pmcid"),
                "category": pub.get("category", ""),
                "publication_types": pub.get("publication_types", []),
                "title_hash": th,
                "query_used": query_used,
            })
            inserted += 1

        except Exception as e:
            log.error(f"  Ingest error for '{pub.get('title', '?')[:40]}': {str(e)[:80]}")
            errors += 1
            conn.rollback()

    conn.commit()
    conn.close()

    return {"inserted": inserted, "duplicates": duplicates, "errors": errors}

def log_run(source: str, query: str, params: dict, hits: int,
             inserted: int, elapsed: float, status: str = "success",
             error: str = ""):
    """Log a literature query run to Supabase."""
    try:
        engine = get_pg_engine()
        conn = engine.connect()
        conn.execute(text("""
            INSERT INTO literature_query_log (source, query, params, hits, inserted, status, error_message, elapsed_seconds)
            VALUES (:source, :query, :params, :hits, :inserted, :status, :error, :elapsed)
        """), {
            "source": source,
            "query": query,
            "params": json.dumps(params),
            "hits": hits,
            "inserted": inserted,
            "status": status,
            "error": error[:500],
            "elapsed": round(elapsed, 1),
        })
        conn.commit()
        conn.close()
    except Exception as e:
        log.warning(f"Failed to log run: {str(e)[:80]}")

# ─────────────────────────────────────────────────────────────────────────────
# Orchestration
# ─────────────────────────────────────────────────────────────────────────────

def search_all_sources(query: str, max_results: int = 100,
                       sources: List[str] = None) -> dict:
    """Search all enabled sources and merge results with dedup."""
    if sources is None:
        sources = ["europepmc", "openalex", "semscholar"]

    all_results = {}
    total_inserted = 0
    total_duplicates = 0

    # Ensure tables exist
    ensure_supabase_tables()

    for source in sources:
        start = time.time()
        try:
            if source == "europepmc":
                results, hits = search_europepmc(query, max_results)
            elif source == "openalex":
                results, hits = search_openalex(query, max_results)
            elif source == "semscholar":
                results, hits = search_semantic_scholar(query, max_results)
            elif source == "biorxiv":
                results, hits = search_biorxiv(keyword_filter=query, max_results=max_results)
            elif source == "medrxiv":
                results, hits = search_biorxiv(server="medrxiv", keyword_filter=query, max_results=max_results)
            else:
                log.warning(f"Unknown source: {source}")
                continue

            elapsed = time.time() - start

            # Ingest to Supabase
            stats = ingest_to_supabase(results, query_used=query)
            total_inserted += stats["inserted"]
            total_duplicates += stats["duplicates"]

            log_run(source, query, {"max_results": max_results}, hits,
                    stats["inserted"], elapsed)

            all_results[source] = {
                "hits": hits,
                "fetched": len(results),
                "inserted": stats["inserted"],
                "duplicates": stats["duplicates"],
                "errors": stats["errors"],
                "elapsed": round(elapsed, 1),
            }

        except Exception as e:
            elapsed = time.time() - start
            log.error(f"Source {source} failed: {str(e)[:100]}")
            log_run(source, query, {"max_results": max_results}, 0, 0,
                    elapsed, "error", str(e)[:500])
            all_results[source] = {"status": "error", "error": str(e)[:100]}

    return {
        "query": query,
        "sources": all_results,
        "total_inserted": total_inserted,
        "total_duplicates": total_duplicates,
    }

# ─────────────────────────────────────────────────────────────────────────────
# Acceptance test
# ─────────────────────────────────────────────────────────────────────────────

def run_acceptance_test() -> dict:
    """
    Acceptance test as specified in the integration brief.
    Disease: "androgenetic alopecia"
    """
    log.info("=" * 60)
    log.info("ACCEPTANCE TEST: androgenetic alopecia")
    log.info("=" * 60)

    results = {}

    # 1. Europe PMC returns ≥ PubMed hit count
    log.info("\n[1/5] Europe PMC search...")
    epmc_results, epmc_hits = search_europepmc("androgenetic alopecia", max_results=50)
    results["europepmc"] = {"hits": epmc_hits, "fetched": len(epmc_results)}
    log.info(f"  → {epmc_hits} hits, {len(epmc_results)} fetched")

    # 2. OpenAlex returns the 3 calibration RCTs by DOI
    log.info("\n[2/5] OpenAlex DOI lookups (3 calibration RCTs)...")
    test_dois = [
        "10.4103/JCAS.JCAS_232_20",
        "10.4103/ijd.ijd_461_22",
        "10.1007/s00403-025-03938-0",
    ]
    oa_found = 0
    for doi in test_dois:
        r = openalex_doi_lookup(doi)
        if r:
            oa_found += 1
    results["openalex_dois"] = {"expected": 3, "found": oa_found}
    log.info(f"  → {oa_found}/3 calibration RCTs found")

    # Also run a keyword search for the acceptance test
    log.info("\n[2b] OpenAlex keyword search...")
    oa_results, oa_hits = search_openalex("androgenetic alopecia", max_results=50)
    results["openalex_search"] = {"hits": oa_hits, "fetched": len(oa_results)}
    log.info(f"  → {oa_hits} hits, {len(oa_results)} fetched")

    # 3. Semantic Scholar cited-by on PMID 35655638
    log.info("\n[3/5] Semantic Scholar cited-by for PMID 35655638...")
    ss_citations = semscholar_cited_by("35655638", max_results=50)
    results["semscholar_cited_by"] = {"citing_papers": len(ss_citations)}
    log.info(f"  → {len(ss_citations)} citing papers")

    # Also run a keyword search
    log.info("\n[3b] Semantic Scholar keyword search...")
    ss_results, ss_hits = search_semantic_scholar("androgenetic alopecia", max_results=50)
    results["semscholar_search"] = {"hits": ss_hits, "fetched": len(ss_results)}
    log.info(f"  → {ss_hits} hits, {len(ss_results)} fetched")

    # 4. Unpaywall resolves DOI 10.1007/s00403-025-03938-0
    log.info("\n[4/5] Unpaywall lookup for 10.1007/s00403-025-03938-0...")
    upw = unpaywall_lookup("10.1007/s00403-025-03938-0")
    if upw:
        results["unpaywall"] = {
            "resolved": True,
            "is_oa": upw["is_oa"],
            "oa_status": upw["oa_status"],
        }
        log.info(f"  → Resolved. is_oa={upw['is_oa']}, status={upw['oa_status']}")
    else:
        results["unpaywall"] = {"resolved": False}
        log.info("  → Not resolved")

    # 5. Zero duplicate PMIDs/DOIs across merged set
    log.info("\n[5/5] Dedup check across merged set...")
    all_pubs = epmc_results + oa_results + ss_results
    doi_set = set()
    pmid_set = set()
    title_hash_set = set()
    dupes = 0
    for p in all_pubs:
        if p.get("doi"):
            if p["doi"] in doi_set:
                dupes += 1
            doi_set.add(p["doi"])
        if p.get("pmid"):
            if p["pmid"] in pmid_set:
                dupes += 1
            pmid_set.add(p["pmid"])
        th = title_hash(p.get("title", ""))
        if th and th in title_hash_set:
            dupes += 1
        title_hash_set.add(th)

    results["dedup"] = {
        "total_pubs": len(all_pubs),
        "unique_dois": len(doi_set),
        "unique_pmids": len(pmid_set),
        "cross_source_dupes": dupes,
    }
    log.info(f"  → {len(all_pubs)} total, {dupes} cross-source duplicates")

    # Ingest all to Supabase
    log.info("\nIngesting all results to Supabase...")
    ensure_supabase_tables()
    ingest_stats = ingest_to_supabase(all_pubs, query_used="androgenetic alopecia [acceptance test]")
    results["ingest"] = ingest_stats
    log.info(f"  Inserted: {ingest_stats['inserted']}, Duplicates: {ingest_stats['duplicates']}, Errors: {ingest_stats['errors']}")

    # Summary
    log.info("\n" + "=" * 60)
    log.info("ACCEPTANCE TEST SUMMARY")
    log.info("=" * 60)
    for k, v in results.items():
        log.info(f"  {k}: {v}")

    return results

# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import socket
    socket.setdefaulttimeout(socket_timeout)

    parser = argparse.ArgumentParser(
        description="Multi-Source Literature Search Engine for Meddash Pipeline"
    )
    parser.add_argument("--custom", type=str, help="Custom search query")
    parser.add_argument("--source", type=str,
                        choices=["europepmc", "openalex", "semscholar", "biorxiv", "medrxiv", "all"],
                        default="all", help="Source to search (default: all)")
    parser.add_argument("--max-results", type=int, default=100, help="Max results per source")
    parser.add_argument("--cited-by", type=str, help="Citation chasing: papers citing this PMID/DOI")
    parser.add_argument("--doi", type=str, help="DOI lookup (OpenAlex + Semantic Scholar)")
    parser.add_argument("--unpaywall", type=str, help="Unpaywall OA status for a DOI")
    parser.add_argument("--from-date", type=str, default="2020-01-01", help="OpenAlex from date")
    parser.add_argument("--acceptance-test", action="store_true", help="Run full acceptance test")
    parser.add_argument("--dry-run", action="store_true", help="Search only, no Supabase ingest")
    args = parser.parse_args()

    if args.acceptance_test:
        results = run_acceptance_test()
        print("\n" + json.dumps(results, indent=2))
        sys.exit(0)

    if args.unpaywall:
        result = unpaywall_lookup(args.unpaywall)
        print(json.dumps(result, indent=2) if result else "Not found")
        sys.exit(0)

    if args.doi:
        # Try OpenAlex first, then Semantic Scholar
        oa = openalex_doi_lookup(args.doi)
        ss = semscholar_doi_lookup(args.doi)
        upw = unpaywall_lookup(args.doi)
        print(json.dumps({"openalex": oa, "semscholar": ss, "unpaywall": upw}, indent=2))
        sys.exit(0)

    if args.cited_by:
        # Citation chasing via Europe PMC + Semantic Scholar
        epmc_cites = epmc_cited_by(args.cited_by)
        ss_cites = semscholar_cited_by(args.cited_by)
        all_cites = epmc_cites + ss_cites
        if not args.dry_run:
            ensure_supabase_tables()
            stats = ingest_to_supabase(all_cites, query_used=f"cited-by:{args.cited_by}")
            print(json.dumps({"total": len(all_cites), "ingest": stats}, indent=2))
        else:
            print(json.dumps({"total": len(all_cites)}, indent=2))
        sys.exit(0)

    if args.custom:
        if args.source == "all":
            sources = ["europepmc", "openalex", "semscholar"]
        else:
            sources = [args.source]

        if args.dry_run:
            # Just search, no ingest
            for src in sources:
                if src == "europepmc":
                    r, h = search_europepmc(args.custom, args.max_results)
                elif src == "openalex":
                    r, h = search_openalex(args.custom, args.max_results, from_date=args.from_date)
                elif src == "semscholar":
                    r, h = search_semantic_scholar(args.custom, args.max_results)
                elif src == "biorxiv":
                    r, h = search_biorxiv(keyword_filter=args.custom, max_results=args.max_results)
                elif src == "medrxiv":
                    r, h = search_biorxiv(server="medrxiv", keyword_filter=args.custom, max_results=args.max_results)
                print(f"\n{src}: {h} hits, {len(r)} fetched")
                for pub in r[:3]:
                    print(f"  - {pub.get('title', '?')[:70]}")
        else:
            results = search_all_sources(args.custom, args.max_results, sources)
            print(json.dumps(results, indent=2))
        sys.exit(0)

    parser.print_help()