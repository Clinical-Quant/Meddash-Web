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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync Scholar metrics for a single KOL.")
    parser.add_argument("--kol_id", required=True, help="ID of the KOL to sync")
    args = parser.parse_args()
    sync_single_kol(args.kol_id)
