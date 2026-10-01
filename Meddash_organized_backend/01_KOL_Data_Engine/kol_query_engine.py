"""
kol_query_engine.py — Granular PubMed Search Runner with KOL Profiles

Runs targeted PubMed E-utilities searches using KOL search profiles.
Fetches publications, ingests to Supabase, logs every run.

Usage:
    # Run a predefined profile
    python kol_query_engine.py --profile glp1_metabolic

    # Run custom search (natural language from Meddash Manager)
    python kol_query_engine.py --custom "GLP-1" --pub-types rct meta_analysis --date-range last_90_days

    # Dry run (show what would be searched)
    python kol_query_engine.py --profile glp1_metabolic --dry-run

    # List available profiles
    python kol_query_engine.py --list
"""

import os
import sys
import json
import time
import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

# ── Path setup ──
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "07_DevOps_Observability"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from supabase_writer import get_pg_engine, upsert_row
from kol_search_profiles import (
    get_profile, list_profiles, build_pubmed_query, build_custom_query,
    resolve_date_range, PUB_TYPES
)
from sqlalchemy import text

# ── PubMed (Bio.Entrez) ──
from Bio import Entrez
Entrez.email = "meddash_developer@example.com"
# Set socket timeout to prevent hanging
import socket
socket.setdefaulttimeout(30)

# ── Logging ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(str(Path(__file__).resolve().parent / "kol_query_engine.log"), encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)


def search_pubmed(query: str, max_results: int = 50, sort: str = "date") -> List[str]:
    """Search PubMed for PMIDs matching the query string."""
    log.info(f"PubMed esearch: {query[:80]}...")
    search_handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results, sort=sort)
    search_results = Entrez.read(search_handle)
    search_handle.close()
    id_list = search_results.get("IdList", [])
    total_count = int(search_results.get("Count", 0))
    log.info(f"  Found {total_count} total, fetching {len(id_list)}")
    return id_list, total_count


def fetch_publications(pmids: List[str]) -> List[Dict[str, Any]]:
    """Fetch full publication metadata for a list of PMIDs."""
    if not pmids:
        return []

    publications = []
    # Fetch in batches to respect rate limits
    batch_size = 10
    for i in range(0, len(pmids), batch_size):
        batch = pmids[i:i + batch_size]
        log.info(f"  Fetching batch {i//batch_size + 1}/{(len(pmids)-1)//batch_size + 1} ({len(batch)} PMIDs)")

        try:
            fetch_handle = Entrez.efetch(db="pubmed", id=",".join(batch), retmode="xml")
            records = Entrez.read(fetch_handle)
            fetch_handle.close()

            for article in records.get("PubmedArticle", []):
                pub = parse_pubmed_article(article)
                if pub:
                    publications.append(pub)

        except Exception as e:
            log.error(f"  Batch fetch failed: {e}")

        # Rate limit: 3 req/s without API key
        time.sleep(0.34)

    return publications


def parse_pubmed_article(article: dict) -> Dict[str, Any]:
    """Parse a PubMed article record into a structured dict."""
    try:
        medline = article.get("MedlineCitation", {})
        article_data = medline.get("Article", {})

        # PMID
        pmid = str(medline.get("PMID", ""))

        # Title
        title = str(article_data.get("ArticleTitle", ""))

        # Journal
        journal_info = article_data.get("Journal", {})
        journal_name = str(journal_info.get("Title", ""))
        journal_abbrev = str(journal_info.get("ISOAbbreviation", ""))
        issn = str(journal_info.get("ISSN", ""))

        # Date
        pub_date = journal_info.get("JournalIssue", {}).get("PubDate", {})
        year = str(pub_date.get("Year", ""))
        month = str(pub_date.get("Month", ""))
        day = str(pub_date.get("Day", ""))
        published_date = f"{year}-{month}-{day}" if year else ""

        # DOI
        doi = ""
        for eloc in article_data.get("ELocationID", []):
            if str(eloc.attributes.get("EIdType", "")) == "doi":
                doi = str(eloc)
                break

        # Abstract
        abstract_parts = article_data.get("Abstract", {}).get("AbstractText", [])
        abstract = " ".join([str(p) for p in abstract_parts]) if abstract_parts else ""

        # Publication type
        pub_types = article_data.get("PublicationTypeList", [])
        pub_type = "; ".join([str(pt) for pt in pub_types[:3]]) if pub_types else ""

        # URL
        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""

        # Authors
        authors_list = article_data.get("AuthorList", [])
        parsed_authors = []
        for author in authors_list:
            if "CollectiveName" in author:
                continue
            last_name = str(author.get("LastName", ""))
            fore_name = str(author.get("ForeName", ""))
            full_name = f"{fore_name} {last_name}".strip()
            orcid = ""
            for id_obj in author.get("Identifier", []):
                if str(id_obj.attributes.get("Source", "")) == "ORCID":
                    orcid = str(id_obj).replace("https://orcid.org/", "").strip()
            affiliation = ""
            affs = author.get("AffiliationInfo", [])
            if affs:
                affiliation = str(affs[0].get("Affiliation", ""))
            parsed_authors.append({
                "name": full_name,
                "last_name": last_name,
                "fore_name": fore_name,
                "orcid": orcid,
                "affiliation": affiliation,
            })

        # MeSH terms
        mesh_terms = []
        for descriptor in medline.get("MeshHeadingList", []):
            mesh_term = str(descriptor.get("DescriptorName", ""))
            if mesh_term:
                mesh_terms.append(mesh_term)

        return {
            "pmid": pmid,
            "title": title,
            "doi": doi,
            "journal_name": journal_name,
            "published_date": published_date,
            "abstract": abstract,
            "publication_type": pub_type,
            "url": url,
            "issn": issn,
            "authors": parsed_authors,
            "mesh_terms": mesh_terms,
        }
    except Exception as e:
        log.warning(f"Failed to parse article: {e}")
        return None


def ingest_to_supabase(publications: List[Dict[str, Any]], pull_id: str = None) -> dict:
    """Ingest publications and authors into Supabase."""
    engine = get_pg_engine()
    conn = engine.connect()

    pubs_ingested = 0
    kols_ingested = 0
    authorships = 0
    errors = 0

    for pub in publications:
        try:
            # Upsert publication
            pub_row = {
                "title": pub["title"],
                "doi": pub["doi"] or None,
                "pmid": pub["pmid"],
                "journal_name": pub["journal_name"],
                "published_date": pub["published_date"],
                "abstract": pub["abstract"],
                "publication_type": pub["publication_type"],
                "url": pub["url"],
                "issn": pub["issn"] or None,
            }

            # Check if publication exists
            existing = conn.execute(
                text("SELECT id FROM publications WHERE pmid = :pmid"),
                {"pmid": pub["pmid"]}
            ).fetchone()

            if existing:
                # Update
                conn.execute(text("""
                    UPDATE publications SET
                        title = :title, doi = :doi, journal_name = :journal_name,
                        published_date = :published_date, abstract = :abstract,
                        publication_type = :publication_type, url = :url, issn = :issn
                    WHERE pmid = :pmid
                """), pub_row)
                pub_id = existing[0]
            else:
                # Insert
                result = conn.execute(text("""
                    INSERT INTO publications (title, doi, pmid, journal_name, published_date, abstract, publication_type, url, issn)
                    VALUES (:title, :doi, :pmid, :journal_name, :published_date, :abstract, :publication_type, :url, :issn)
                    RETURNING id
                """), pub_row)
                pub_id = result.fetchone()[0]

            pubs_ingested += 1

            # Upsert authors as KOLs
            for i, author in enumerate(pub["authors"]):
                if not author["last_name"]:
                    continue

                # Check if KOL exists by name
                existing_kol = conn.execute(
                    text("SELECT id FROM kols WHERE first_name = :fn AND last_name = :ln LIMIT 1"),
                    {"fn": author["fore_name"], "ln": author["last_name"]}
                ).fetchone()

                if existing_kol:
                    kol_id = existing_kol[0]
                    # Update ORCID/institution if we have new info
                    if author["orcid"]:
                        conn.execute(text("UPDATE kols SET orcid = :o WHERE id = :id AND orcid IS NULL"),
                                    {"o": author["orcid"], "id": kol_id})
                    if author["affiliation"]:
                        conn.execute(text("UPDATE kols SET institution = :i WHERE id = :id AND (institution IS NULL OR institution = '')"),
                                    {"i": author["affiliation"], "id": kol_id})
                else:
                    # Insert new KOL
                    target_table = "kols_staging" if pull_id else "kols"
                    result = conn.execute(text(f"""
                        INSERT INTO {target_table} (first_name, last_name, orcid, institution, pull_id)
                        VALUES (:fn, :ln, :o, :i, :p)
                        RETURNING id
                    """), {
                        "fn": author["fore_name"],
                        "ln": author["last_name"],
                        "o": author["orcid"] or None,
                        "i": author["affiliation"] or None,
                        "p": pull_id,
                    })
                    kol_id = result.fetchone()[0]

                kols_ingested += 1

                # Upsert authorship
                existing_auth = conn.execute(
                    text("SELECT 1 FROM kol_authorships WHERE kol_id = :kid AND publication_id = :pid"),
                    {"kid": kol_id, "pid": pub_id}
                ).fetchone()

                if not existing_auth:
                    conn.execute(text("""
                        INSERT INTO kol_authorships (kol_id, publication_id, is_primary_author, author_position)
                        VALUES (:kid, :pid, :pa, :ap)
                    """), {
                        "kid": kol_id,
                        "pid": pub_id,
                        "pa": 1 if i == 0 else 0,
                        "ap": str(i + 1),
                    })
                    authorships += 1

            # Upsert MeSH terms
            for mesh_term in pub["mesh_terms"]:
                # Check if mesh term exists in ontology
                mesh_existing = conn.execute(
                    text("SELECT mesh_id FROM mesh_ontology WHERE mesh_term = :mt LIMIT 1"),
                    {"mt": mesh_term}
                ).fetchone()

                if not mesh_existing:
                    # Insert mesh term
                    conn.execute(text("""
                        INSERT INTO mesh_ontology (mesh_id, mesh_term)
                        VALUES (:mid, :mt)
                        ON CONFLICT (mesh_id) DO NOTHING
                    """), {"mid": mesh_term, "mt": mesh_term})

                # Insert publication_mesh_map
                conn.execute(text("""
                    INSERT INTO publication_mesh_map (pmid, mesh_id, is_major_topic)
                    VALUES (:pmid, :mid, 0)
                    ON CONFLICT (pmid, mesh_id) DO NOTHING
                """), {"pmid": pub["pmid"], "mid": mesh_term})

        except Exception as e:
            log.error(f"Failed to ingest publication {pub.get('pmid', '?')}: {str(e)[:80]}")
            errors += 1
            conn.rollback()

    conn.commit()
    conn.close()

    return {
        "publications": pubs_ingested,
        "kols": kols_ingested,
        "authorships": authorships,
        "errors": errors,
    }


def log_run(pg_conn, profile_name: str, label: str, condition: str,
            search_query: str, total_found: int, total_ingested: int,
            date_start: str, date_end: str, elapsed: float,
            status: str, error: str = ""):
    """Log a query run to kol_query_log table in Supabase."""
    try:
        upsert_row(pg_conn, "kol_query_log", {
            "profile_name": profile_name,
            "label": label,
            "condition_searched": condition,
            "search_query": search_query,
            "total_found": total_found,
            "total_ingested": total_ingested,
            "date_range_start": date_start,
            "date_range_end": date_end,
            "elapsed_seconds": round(elapsed, 1),
            "status": status,
            "error_message": error,
        }, pk="id")
        pg_conn.commit()
    except Exception:
        pass  # Table might not exist yet — created in SEQ-0019


def run_profile(profile_name: str, dry_run: bool = False):
    """Run a KOL search profile."""
    global _current_raw_dir

    profile = get_profile(profile_name)
    conditions = profile["conditions"]
    label = profile["label"]

    if not conditions:
        log.error(f"Profile '{profile_name}' has no conditions defined")
        return

    condition = conditions[0]
    query = build_pubmed_query(profile)
    date_start, date_end = resolve_date_range(profile.get("date_range", ""))

    log.info(f"=== KOL QUERY ENGINE ===")
    log.info(f"Profile: {profile_name} ({label})")
    log.info(f"Condition: {condition}")
    log.info(f"Query: {query[:100]}...")
    log.info(f"Date range: {date_start} to {date_end}" if date_start else "Date range: (none)")

    if dry_run:
        print(f"\nProfile: {label}")
        print(f"PubMed query: {query}")
        print(f"Max results: {profile['max_results']}")
        print(f"Sort: {profile['sort']}")
        return

    start_time = time.time()
    engine = get_pg_engine()

    try:
        # Search PubMed
        pmids, total_found = search_pubmed(query, profile["max_results"], profile["sort"])

        if not pmids:
            log.info("No publications found.")
            pg_conn = engine.connect()
            log_run(pg_conn, profile_name, label, condition, query, 0, 0,
                    date_start, date_end, time.time() - start_time, "success", "No results")
            pg_conn.close()
            return {"profile": profile_name, "total_found": 0, "total_ingested": 0, "status": "success"}

        # Fetch full metadata
        publications = fetch_publications(pmids)
        log.info(f"Fetched {len(publications)} publications with full metadata")

        # Ingest to Supabase
        log.info("Ingesting to Supabase...")
        stats = ingest_to_supabase(publications)
        elapsed = time.time() - start_time

        log.info(f"\n=== COMPLETE: {total_found} found, {stats['publications']} pubs ingested, {stats['kols']} KOLs, {elapsed:.1f}s ===")

        # Log run
        pg_conn = engine.connect()
        log_run(pg_conn, profile_name, label, condition, query, total_found,
                stats["publications"], date_start, date_end, elapsed, "success")
        pg_conn.close()

        return {
            "profile": profile_name,
            "total_found": total_found,
            "publications": stats["publications"],
            "kols": stats["kols"],
            "authorships": stats["authorships"],
            "errors": stats["errors"],
            "elapsed": elapsed,
            "status": "success",
        }

    except Exception as e:
        elapsed = time.time() - start_time
        log.error(f"KOL query failed: {e}")
        try:
            pg_conn = engine.connect()
            log_run(pg_conn, profile_name, label, condition, query, 0, 0,
                    date_start, date_end, elapsed, "error", str(e)[:500])
            pg_conn.close()
        except:
            pass
        return {"profile": profile_name, "total_found": 0, "total_ingested": 0, "status": "error"}


def run_custom(condition: str, pub_types: list[str] = None,
               date_range: str = "", language: str = "English",
               max_results: int = 50, dry_run: bool = False):
    """Run a custom ad-hoc PubMed search. Entry point for natural language queries."""
    profile_name = "_custom"
    label = f"Custom: {condition}"

    result = build_custom_query(
        condition=condition,
        pub_types=pub_types,
        date_range=date_range,
        language=language,
        max_results=max_results,
    )

    query = result["query"]
    profile = result["profile"]
    date_start, date_end = resolve_date_range(date_range)

    log.info(f"=== CUSTOM KOL QUERY ===")
    log.info(f"Condition: {condition}")
    log.info(f"Query: {query[:100]}...")
    log.info(f"Date range: {date_start} to {date_end}" if date_start else "Date range: (none)")

    if dry_run:
        print(f"\nCustom PubMed query: {query}")
        print(f"Max results: {max_results}")
        return

    start_time = time.time()
    engine = get_pg_engine()

    try:
        pmids, total_found = search_pubmed(query, max_results, "date")

        if not pmids:
            log.info("No publications found.")
            pg_conn = engine.connect()
            log_run(pg_conn, profile_name, label, condition, query, 0, 0,
                    date_start, date_end, time.time() - start_time, "success", "No results")
            pg_conn.close()
            return {"condition": condition, "total_found": 0, "total_ingested": 0, "status": "success"}

        publications = fetch_publications(pmids)
        log.info(f"Fetched {len(publications)} publications")

        log.info("Ingesting to Supabase...")
        stats = ingest_to_supabase(publications)
        elapsed = time.time() - start_time

        log.info(f"\n=== COMPLETE: {total_found} found, {stats['publications']} pubs, {stats['kols']} KOLs, {elapsed:.1f}s ===")

        pg_conn = engine.connect()
        log_run(pg_conn, profile_name, label, condition, query, total_found,
                stats["publications"], date_start, date_end, elapsed, "success")
        pg_conn.close()

        return {
            "condition": condition,
            "total_found": total_found,
            "publications": stats["publications"],
            "kols": stats["kols"],
            "authorships": stats["authorships"],
            "errors": stats["errors"],
            "elapsed": elapsed,
            "status": "success",
        }

    except Exception as e:
        elapsed = time.time() - start_time
        log.error(f"Custom KOL query failed: {e}")
        try:
            pg_conn = engine.connect()
            log_run(pg_conn, profile_name, label, condition, query, 0, 0,
                    date_start, date_end, elapsed, "error", str(e)[:500])
            pg_conn.close()
        except:
            pass
        return {"condition": condition, "total_found": 0, "total_ingested": 0, "status": "error"}


# ── CLI ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KOL Query Engine with PubMed Profiles")
    parser.add_argument("--profile", type=str, help="KOL profile name to run")
    parser.add_argument("--custom", type=str, help="Custom condition search")
    parser.add_argument("--pub-types", nargs="*", help="Publication types (rct, meta_analysis, clinical_trial, review)")
    parser.add_argument("--date-range", type=str, default="", help="Date range (last_90_days or YYYY-MM-DD,YYYY-MM-DD)")
    parser.add_argument("--language", type=str, default="English", help="Language filter")
    parser.add_argument("--max-results", type=int, default=50, help="Max results")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be searched")
    parser.add_argument("--list", action="store_true", help="List available profiles")
    args = parser.parse_args()

    if args.list:
        print("Available KOL Search Profiles:")
        for p in list_profiles():
            if p["name"] == "_custom":
                continue
            print(f"  {p['name']:30s} - {p['label']}")
            if p["conditions"]:
                print(f"    Conditions: {', '.join(p['conditions'][:4])}")
        sys.exit(0)

    if args.profile:
        result = run_profile(args.profile, dry_run=args.dry_run)
        if result:
            print(f"\nResult: {result}")

    elif args.custom:
        result = run_custom(
            condition=args.custom,
            pub_types=args.pub_types,
            date_range=args.date_range,
            language=args.language,
            max_results=args.max_results,
            dry_run=args.dry_run,
        )
        if result:
            print(f"\nResult: {result}")

    else:
        parser.print_help()