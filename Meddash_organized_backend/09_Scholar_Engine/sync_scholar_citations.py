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


def search_scholar_candidates(name: str):
    """Returns top 3 Scholar profile candidates for a given name."""
    print(f"Searching SerpApi for Scholar candidates: {name}")
    params = {
        "engine": "google_scholar_profiles",
        "mauthors": name,
        "hl": "en",
        "api_key": SERPAPI_KEY
    }
    try:
        res = requests.get("https://serpapi.com/search", params=params).json()
        return res.get("profiles", [])[:3]
    except Exception as e:
        print(f"SerpApi Error during profile search: {e}")
    return []


def fetch_scholar_author_data(scholar_id: str):
    """Fetches full author profile including articles, affiliations, and metrics."""
    print(f"Fetching full Scholar profile for: {scholar_id}")
    params = {
        "engine": "google_scholar_author",
        "hl": "en",
        "user": scholar_id,
        "api_key": SERPAPI_KEY
    }
    try:
        res = requests.get("https://serpapi.com/search", params=params).json()
        return res
    except Exception as e:
        print(f"SerpApi Error during author fetch: {e}")
    return {}


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
        candidates = search_scholar_candidates(kol_name)
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
    
    file_handler = logging.FileHandler(log_path, mode='w')
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger = logging.getLogger(f"scholar_{pull_id}")
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)
    
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
            candidates = search_scholar_candidates(kol_name)
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

