"""
Meddash Scholar Sync Engine - 4-Tier Disambiguation
Target: Google Scholar via SerpApi
Execution: On-Demand via Next.js UI (Rate-Limited to once per 7 days per KOL)

Tier 1: ORCID Match              → Auto-Accept
Tier 2: ≥3 Publication Titles    → Auto-Accept
Tier 3: Institution + Specialty   → Auto-Accept
Tier 4: None of above             → scholar_review_queue
"""
import os
import argparse
import logging
import re
import requests
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(base_dir, '.env')
load_dotenv(env_path)

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
SUPABASE_URI = os.getenv("SUPABASE_URI")

if not SERPAPI_KEY or not SUPABASE_URI:
    print("FATAL: Missing SERPAPI_KEY or SUPABASE_URI in .env")
    exit(1)

pg_engine = create_engine(SUPABASE_URI)
module_logger = logging.getLogger(__name__)


def ensure_scholar_columns(conn, table_name: str):
    """Ensures the required scholar enrichment columns exist on the target table."""
    if table_name not in ("kols_staging", "kols"):
        raise ValueError(f"Unsupported scholar table: {table_name}")
    conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS scholar_status TEXT DEFAULT 'pending'"))
    conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS scholar_id TEXT"))
    conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS scholar_profile_url TEXT"))


def ensure_kols_identity(conn):
    """Backfills missing ids on final kols rows and restores an insert default sequence."""
    conn.execute(text("CREATE SEQUENCE IF NOT EXISTS kols_id_seq"))
    conn.execute(text("""
        SELECT setval(
            'kols_id_seq',
            COALESCE((SELECT MAX(id) FROM kols WHERE id IS NOT NULL), 0) + 1,
            false
        )
    """))
    conn.execute(text("UPDATE kols SET id = nextval('kols_id_seq') WHERE id IS NULL"))
    conn.execute(text("ALTER TABLE kols ALTER COLUMN id SET DEFAULT nextval('kols_id_seq')"))

def build_scholar_queries(name: str, institution: str = ""):
    """Builds fallback Scholar profile queries to improve recall."""
    queries = []
    normalized_name = (name or "").strip()
    normalized_institution = (institution or "").strip()

    if normalized_name:
        queries.append(normalized_name)
        parts = [part for part in normalized_name.split() if part]
        if len(parts) >= 2:
            first_name = " ".join(parts[:-1])
            last_name = parts[-1]
            queries.append(f"{parts[0][0]} {last_name}")
            queries.append(f"{last_name}, {first_name}")

    if normalized_name and normalized_institution:
        institution_terms = [term.strip(",.") for term in normalized_institution.split() if len(term.strip(",.")) > 3]
        institution_hint = " ".join(institution_terms[:4])
        if institution_hint:
            queries.append(f"{normalized_name} {institution_hint}")

    deduped = []
    seen = set()
    for query in queries:
        query_key = query.lower()
        if query and query_key not in seen:
            deduped.append(query)
            seen.add(query_key)
    return deduped


def search_scholar_candidates(name: str, institution: str = ""):
    """Returns top Scholar profile candidates for a KOL using fallback query variants."""
    profiles = []
    seen_ids = set()

    for query in build_scholar_queries(name, institution):
        print(f"Searching SerpApi for Scholar candidates: {query}")
        module_logger.info(f"Scholar profile query: {query}")
        params = {
            "engine": "google_scholar_profiles",
            "mauthors": query,
            "hl": "en",
            "api_key": SERPAPI_KEY
        }
        try:
            res = requests.get("https://serpapi.com/search", params=params, timeout=30).json()
            candidates = res.get("profiles", [])
            module_logger.info(f"Profile query returned {len(candidates)} candidates.")
            for candidate in candidates:
                author_id = candidate.get("author_id")
                if author_id and author_id not in seen_ids:
                    profiles.append(candidate)
                    seen_ids.add(author_id)
            if profiles:
                return profiles[:5]
        except Exception as e:
            print(f"SerpApi Error during profile search: {e}")
            module_logger.warning(f"SerpApi profile search failed for query '{query}': {e}")

    return profiles[:5]


def fetch_scholar_author_data(scholar_id: str):
    """Fetches full author profile including articles, affiliations, and metrics."""
    print(f"Fetching full Scholar profile for: {scholar_id}")
    params = {
        "engine": "google_scholar_author",
        "hl": "en",
        "author_id": scholar_id,
        "api_key": SERPAPI_KEY
    }
    try:
        res = requests.get("https://serpapi.com/search", params=params, timeout=30).json()
        if res.get("error"):
            module_logger.warning(f"Scholar author API error for {scholar_id}: {res.get('error')}")
        if res.get("search_metadata", {}).get("status") == "Error":
            module_logger.warning(f"Scholar author API returned Error status for {scholar_id}.")
        return res
    except Exception as e:
        print(f"SerpApi Error during author fetch: {e}")
        module_logger.warning(f"SerpApi author fetch exception for {scholar_id}: {e}")
    return {}


def extract_scholar_id(value: str):
    """Extracts the Google Scholar user ID from either a full URL or a raw ID."""
    raw_value = (value or "").strip()
    if not raw_value:
        return None

    match = re.search(r"[?&]user=([A-Za-z0-9_-]+)", raw_value)
    if match:
        return match.group(1)

    if re.fullmatch(r"[A-Za-z0-9_-]+", raw_value):
        return raw_value

    return None


def extract_metrics(author_data: dict):
    """Parses the cited_by table from SerpApi response."""
    table = author_data.get("cited_by", {}).get("table", [])
    metrics = {"total_citations": 0, "h_index": 0, "i10_index": 0}
    for row in table:
        if "citations" in row:
            metrics["total_citations"] = row["citations"].get("all", 0)
        elif "h_index" in row:
            metrics["h_index"] = row["h_index"].get("all", 0)
        elif "i10_index" in row:
            metrics["i10_index"] = row["i10_index"].get("all", 0)
    return metrics


def fuzzy_match(a: str, b: str, threshold: int = 60) -> bool:
    """Simple character-level overlap match. Returns True if similarity >= threshold%."""
    if not a or not b:
        return False
    a, b = a.lower().strip(), b.lower().strip()
    # Count common words
    words_a = set(a.split())
    words_b = set(b.split())
    if not words_a or not words_b:
        return False
    overlap = len(words_a & words_b) / max(len(words_a), len(words_b)) * 100
    return overlap >= threshold


def disambiguate(kol_id: str, kol_name: str, kol_orcid: str,
                 kol_institution: str, kol_specialty: str,
                 kol_pub_titles: list, candidates: list):
    """
    4-Tier Identity Verification.
    Returns (scholar_id, tier_passed) or (None, 'FAILED')
    """

    for candidate in candidates:
        c_id = candidate.get("author_id", "")
        c_name = candidate.get("name", "")
        c_affil = candidate.get("affiliations", "")
        c_interests = " ".join([i.get("title", "") for i in candidate.get("interests", [])])

        # Fetch full profile to get article titles
        author_data = fetch_scholar_author_data(c_id)
        c_articles = [a.get("title", "") for a in author_data.get("articles", [])[:10]]

        # ── TIER 1: ORCID ──────────────────────────────────────────────
        if kol_orcid:
            # Check if ORCID appears in Scholar profile description/about
            about = str(author_data.get("author", {}).get("description", ""))
            if kol_orcid in about:
                print(f"TIER 1 PASS (ORCID): {c_name}")
                return c_id, "TIER_1_ORCID", extract_metrics(author_data)

        # ── TIER 2: Publication Title Overlap (≥3 matches) ─────────────
        if kol_pub_titles and c_articles:
            matches = sum(
                1 for pub in kol_pub_titles
                for art in c_articles
                if fuzzy_match(pub, art, threshold=70)
            )
            if matches >= 3:
                print(f"TIER 2 PASS ({matches} pub matches): {c_name}")
                return c_id, "TIER_2_PUBLICATIONS", extract_metrics(author_data)

        # ── TIER 3: Institution + Specialty (both must match) ──────────
        institution_match = fuzzy_match(kol_institution or "", c_affil, threshold=50)
        specialty_match = fuzzy_match(kol_specialty or "", c_interests, threshold=50)
        if institution_match and specialty_match:
            print(f"TIER 3 PASS (Institution+Specialty): {c_name}")
            return c_id, "TIER_3_AFFIL_SPECIALTY", extract_metrics(author_data)

    # ── TIER 4: No match — route to manual review ──────────────────
    return None, "TIER_4_MANUAL_REVIEW", None


def write_review_queue(conn, kol_id, kol_name, candidates):
    """Writes all failed candidates to the scholar_review_queue for human review."""
    for candidate in candidates[:3]:
        c_id = candidate.get("author_id", "")
        c_name = candidate.get("name", "")
        c_affil = candidate.get("affiliations", "")
        c_interests = " ".join([i.get("title", "") for i in candidate.get("interests", [])])

        conn.execute(text("""
            INSERT INTO scholar_review_queue
              (kol_id, kol_name, candidate_scholar_id, candidate_name,
               candidate_affiliation, candidate_interests, disambiguation_tier_failed)
            VALUES (:kid, :kname, :cid, :cname, :caffil, :cint, :tier)
            ON CONFLICT DO NOTHING
        """), {
            "kid": str(kol_id), "kname": kol_name, "cid": c_id,
            "cname": c_name, "caffil": c_affil, "cint": c_interests,
            "tier": "TIER_4_MANUAL_REVIEW"
        })
    conn.commit()
    print(f"-> Written {min(len(candidates), 3)} candidates to scholar_review_queue for manual verification.")


def upsert_metrics(conn, kol_id, scholar_id, metrics):
    conn.execute(text("""
        INSERT INTO kol_scholar_metrics
          (kol_id, scholar_id, total_citations, h_index, i10_index, last_updated_date)
        VALUES (:k, :sid, :t, :h, :i10, CURRENT_TIMESTAMP)
        ON CONFLICT (kol_id) DO UPDATE SET
            scholar_id = EXCLUDED.scholar_id,
            total_citations = EXCLUDED.total_citations,
            h_index = EXCLUDED.h_index,
            i10_index = EXCLUDED.i10_index,
            last_updated_date = CURRENT_TIMESTAMP;
    """), {
        "k": str(kol_id), "sid": scholar_id,
        "t": metrics["total_citations"],
        "h": metrics["h_index"],
        "i10": metrics["i10_index"]
    })
    conn.commit()


def sync_manual_scholar_targets(table_name: str, pull_id: str, targets: list, log_prefix: str):
    """Processes manually supplied Scholar profile URLs/IDs for either staging or final KOLs."""
    log_dir = os.path.join(base_dir, "07_DevOps_Observability")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"{log_prefix}_{pull_id}.log")

    file_handler = logging.FileHandler(log_path, mode='w', encoding='utf-8')
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger = logging.getLogger(f"{log_prefix}_{pull_id}")
    logger.handlers.clear()
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    logger.info(
        f"=== Manual Scholar Sync Starting for table={table_name} pull_id={pull_id} ({len(targets)} targets) ==="
    )

    results = []

    with pg_engine.connect() as conn:
        try:
            if table_name == "kols":
                ensure_kols_identity(conn)
            ensure_scholar_columns(conn, table_name)
            conn.commit()
        except Exception:
            conn.rollback()

        for idx, target in enumerate(targets):
            kol_id = int(target["kol_id"])
            scholar_value = (target.get("scholar_url") or "").strip()
            logger.info(f"[{idx+1}/{len(targets)}] Processing KOL ID: {kol_id}")

            scholar_id = extract_scholar_id(scholar_value)
            if not scholar_id:
                logger.warning(f"  Invalid Scholar URL or ID supplied: {scholar_value}")
                results.append({"kol_id": kol_id, "status": "invalid_input", "reason": "invalid_url"})
                continue

            author_data = fetch_scholar_author_data(scholar_id)
            if not author_data or not author_data.get("author"):
                logger.warning(f"  Scholar author fetch failed for scholar_id={scholar_id}")
                conn.execute(
                    text("""
                        UPDATE {table_name}
                        SET scholar_status = 'scholar_failed',
                            scholar_profile_url = :url
                        WHERE id = :id
                    """.replace("{table_name}", table_name)),
                    {"id": kol_id, "url": scholar_value}
                )
                conn.commit()
                results.append({"kol_id": kol_id, "status": "scholar_failed", "reason": "fetch_failed"})
                continue

            metrics = extract_metrics(author_data)
            upsert_metrics(conn, kol_id, scholar_id, metrics)
            conn.execute(
                text("""
                    UPDATE {table_name}
                    SET scholar_status = 'scholar_verified',
                        scholar_id = :sid,
                        scholar_profile_url = :url
                    WHERE id = :id
                """.replace("{table_name}", table_name)),
                {"id": kol_id, "sid": scholar_id, "url": scholar_value}
            )
            conn.commit()

            logger.info(
                f"  Scholar verified: scholar_id={scholar_id}, citations={metrics['total_citations']}, "
                f"h_index={metrics['h_index']}, i10_index={metrics['i10_index']}"
            )
            results.append({"kol_id": kol_id, "status": "scholar_verified", "scholar_id": scholar_id, **metrics})

    logger.info(
        f"=== Manual Scholar Sync Complete: "
        f"{sum(1 for r in results if r.get('status') == 'scholar_verified')} verified, "
        f"{sum(1 for r in results if r.get('status') == 'scholar_failed')} failed, "
        f"{sum(1 for r in results if r.get('status') == 'invalid_input')} invalid input ==="
    )
    return results


def sync_manual_scholar_entries(pull_id: str, targets: list):
    """
    Processes manually supplied Scholar profile URLs/IDs for selected sandbox KOLs.
    This bypasses name-based Scholar discovery and pulls metrics directly.
    """
    return sync_manual_scholar_targets("kols_staging", pull_id, targets, "scholar_sync")


def sync_manual_final_scholar_entries(pull_id: str, targets: list):
    """Processes manually supplied Scholar profile URLs/IDs for final KOL rows."""
    return sync_manual_scholar_targets("kols", pull_id, targets, "scholar_final")


def sync_single_kol(kol_id: str):
    print(f"\nInitiating On-Demand Scholar Sync for KOL: {kol_id}...")

    with pg_engine.connect() as conn:
        # Check if already mapped
        existing = conn.execute(
            text("SELECT scholar_id FROM kol_scholar_metrics WHERE kol_id::text = :k LIMIT 1"),
            {"k": str(kol_id)}
        ).fetchone()

        if existing:
            scholar_id = existing[0]
            print(f"Existing scholar_id found: {scholar_id}. Refreshing metrics...")
            author_data = fetch_scholar_author_data(scholar_id)
            metrics = extract_metrics(author_data)
            upsert_metrics(conn, kol_id, scholar_id, metrics)
            print("Sync Complete (Refresh).")
            return

        # Pull KOL data for disambiguation
        kol_row = conn.execute(text("""
            SELECT
                first_name || ' ' || last_name AS name,
                orcid,
                institution,
                specialty
            FROM kols WHERE id::text = :k LIMIT 1
        """), {"k": str(kol_id)}).fetchone()

        if not kol_row:
            print(f"ERROR: KOL {kol_id} not found in database.")
            return

        kol_name, kol_orcid, kol_institution, kol_specialty = kol_row

        # Pull known publication titles from the publications table (if exists)
        try:
            pub_rows = conn.execute(text("""
                SELECT title FROM publications
                WHERE kol_id::text = :k AND title IS NOT NULL
                LIMIT 15
            """), {"k": str(kol_id)}).fetchall()
            kol_pub_titles = [r[0] for r in pub_rows]
        except Exception:
            kol_pub_titles = []

        print(f"KOL: {kol_name} | ORCID: {kol_orcid} | Institution: {kol_institution} | {len(kol_pub_titles)} publications loaded.")

        # Search Scholar for candidates
        candidates = search_scholar_candidates(kol_name, kol_institution)
        if not candidates:
            print(f"ERROR: No Scholar profiles found for '{kol_name}'.")
            return

        # Run disambiguation
        scholar_id, tier_passed, metrics = disambiguate(
            kol_id, kol_name, kol_orcid, kol_institution, kol_specialty,
            kol_pub_titles, candidates
        )

        if scholar_id and metrics:
            print(f"-> Disambiguation passed via {tier_passed}. Upserting to Supabase...")
            upsert_metrics(conn, kol_id, scholar_id, metrics)
            print("Sync Complete.")
        else:
            print(f"-> Disambiguation FAILED all tiers. Routing to scholar_review_queue...")
            write_review_queue(conn, kol_id, kol_name, candidates)
            print("Manual review entry written.")


def sync_sandbox_selected(pull_id: str, kol_ids: list):
    """
    Process selected KOLs from kols_staging through the 4-tier Scholar disambiguation.
    Updates scholar_status and scholar_id columns on kols_staging.
    Writes to scholar_sync_{pull_id}.log for System Health streaming.
    """
    import logging
    log_dir = os.path.join(base_dir, "07_DevOps_Observability")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"scholar_sync_{pull_id}.log")
    
    file_handler = logging.FileHandler(log_path, mode='a', encoding='utf-8')
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger = logging.getLogger(f"scholar_{pull_id}")
    logger.handlers.clear()
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    module_logger.handlers.clear()
    module_logger.addHandler(file_handler)
    module_logger.setLevel(logging.INFO)
    module_logger.propagate = False
    
    logger.info(f"=== Scholar Sync Starting for pull_id: {pull_id} ({len(kol_ids)} KOLs selected) ===")
    
    results = []
    
    with pg_engine.connect() as conn:
        # Ensure scholar columns exist on kols_staging
        try:
            conn.execute(text("ALTER TABLE kols_staging ADD COLUMN IF NOT EXISTS scholar_status TEXT DEFAULT 'pending'"))
            conn.execute(text("ALTER TABLE kols_staging ADD COLUMN IF NOT EXISTS scholar_id TEXT"))
            conn.commit()
        except Exception:
            conn.rollback()
        
        for idx, kol_id in enumerate(kol_ids):
            logger.info(f"[{idx+1}/{len(kol_ids)}] Processing KOL ID: {kol_id}")
            
            # Check if already mapped in kol_scholar_metrics
            existing = conn.execute(
                text("SELECT scholar_id FROM kol_scholar_metrics WHERE kol_id::text = :k LIMIT 1"),
                {"k": str(kol_id)}
            ).fetchone()
            
            if existing:
                scholar_id = existing[0]
                logger.info(f"  Existing scholar_id found: {scholar_id}. Refreshing metrics...")
                author_data = fetch_scholar_author_data(scholar_id)
                metrics = extract_metrics(author_data)
                upsert_metrics(conn, kol_id, scholar_id, metrics)
                conn.execute(text("UPDATE kols_staging SET scholar_status = 'scholar_verified', scholar_id = :sid WHERE id = :id"),
                             {"sid": scholar_id, "id": kol_id})
                conn.commit()
                results.append({"kol_id": kol_id, "status": "scholar_verified", "scholar_id": scholar_id, "tier": "CACHED", **metrics})
                logger.info(f"  ✅ Scholar metrics refreshed. Citations: {metrics['total_citations']}, h-index: {metrics['h_index']}")
                continue
            
            # Pull KOL data from staging table
            kol_row = conn.execute(text("""
                SELECT first_name || ' ' || last_name AS name, orcid, institution, specialty
                FROM kols_staging WHERE id = :k LIMIT 1
            """), {"k": kol_id}).fetchone()
            
            if not kol_row:
                logger.warning(f"  KOL {kol_id} not found in kols_staging.")
                results.append({"kol_id": kol_id, "status": "not_found"})
                continue
            
            kol_name, kol_orcid, kol_institution, kol_specialty = kol_row
            logger.info(f"  KOL: {kol_name} | ORCID: {kol_orcid} | Institution: {kol_institution}")
            
            # Pull publication titles for Tier 2 matching
            try:
                pub_rows = conn.execute(text("""
                    SELECT p.title FROM kol_authorships ka
                    JOIN publications p ON ka.publication_id = p.id
                    WHERE ka.kol_id = :k AND p.title IS NOT NULL LIMIT 15
                """), {"k": kol_id}).fetchall()
                kol_pub_titles = [r[0] for r in pub_rows]
            except Exception:
                kol_pub_titles = []
            
            # Search Scholar for candidates
            candidates = search_scholar_candidates(kol_name, kol_institution)
            if not candidates:
                logger.warning(f"  No Scholar profiles found for '{kol_name}'.")
                conn.execute(text("UPDATE kols_staging SET scholar_status = 'scholar_failed' WHERE id = :id"), {"id": kol_id})
                conn.commit()
                results.append({"kol_id": kol_id, "status": "scholar_failed", "reason": "no_candidates"})
                continue
            
            # Run 4-tier disambiguation
            scholar_id, tier_passed, metrics = disambiguate(
                kol_id, kol_name, kol_orcid, kol_institution, kol_specialty,
                kol_pub_titles, candidates
            )
            
            if scholar_id and metrics:
                logger.info(f"  ✅ {tier_passed}: scholar_id={scholar_id}, Citations={metrics['total_citations']}, h={metrics['h_index']}")
                upsert_metrics(conn, kol_id, scholar_id, metrics)
                conn.execute(text("UPDATE kols_staging SET scholar_status = 'scholar_verified', scholar_id = :sid WHERE id = :id"),
                             {"sid": scholar_id, "id": kol_id})
                conn.commit()
                results.append({"kol_id": kol_id, "status": "scholar_verified", "scholar_id": scholar_id, "tier": tier_passed, **metrics})
            else:
                logger.info(f"  🔍 TIER_4_MANUAL_REVIEW: Writing to scholar_review_queue...")
                write_review_queue(conn, kol_id, kol_name, candidates)
                conn.execute(text("UPDATE kols_staging SET scholar_status = 'scholar_review' WHERE id = :id"), {"id": kol_id})
                conn.commit()
                results.append({"kol_id": kol_id, "status": "scholar_review", "tier": "TIER_4_MANUAL_REVIEW"})
    
    logger.info(f"=== Scholar Sync Complete: {sum(1 for r in results if r.get('status') == 'scholar_verified')} verified, "
                f"{sum(1 for r in results if r.get('status') == 'scholar_review')} pending review, "
                f"{sum(1 for r in results if r.get('status') == 'scholar_failed')} failed ===")
    
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync Scholar metrics for KOLs.")
    parser.add_argument("--kol_id", help="ID of a single KOL to sync (global kols table)")
    parser.add_argument("--pull_id", help="Pull ID for sandbox batch sync")
    parser.add_argument("--kol_ids", help="Comma-separated KOL IDs to sync from staging", default="")
    args = parser.parse_args()
    
    if args.pull_id and args.kol_ids:
        ids = [int(x.strip()) for x in args.kol_ids.split(",") if x.strip()]
        sync_sandbox_selected(args.pull_id, ids)
    elif args.kol_id:
        sync_single_kol(args.kol_id)
    else:
        print("Usage: --kol_id <id> OR --pull_id <pid> --kol_ids <id1,id2,id3>")
