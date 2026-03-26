"""
ct_mesh_mapper.py — Meddash Condition → MeSH Ontology Bridge
=============================================================
Maps raw ClinicalTrials.gov condition strings to MeSH tree identifiers
so CT.gov trial data shares the same ontology as PubMed KOL data.

Two-pass strategy:
    Pass 1 — NLM MeSH Lookup API (free, deterministic, no tokens)
              https://id.nlm.nih.gov/mesh/lookup/descriptor
    Pass 2 — Gemini Flash API (OPTIONAL — for unresolved complex terms)
              Only runs if GEMINI_API_KEY is an environment variable.
              Activate with: --gemini

Results are cached in ct_trials.db → condition_mesh_map table.
All resolved terms are then written back to trial_conditions.mesh_id / mesh_term.

Usage:
    python ct_mesh_mapper.py                   # NLM API only
    python ct_mesh_mapper.py --gemini          # NLM + Gemini Flash fallback
    python ct_mesh_mapper.py --stats           # Show current mapping coverage
    python ct_mesh_mapper.py --limit 50        # Process only 50 unmapped conditions
"""

import argparse
import json
import logging
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
import os
from datetime import datetime
import google.generativeai as genai

DB_FILE   = r"C:\Users\email\.gemini\antigravity\Meddash_organized_backend\06_Shared_Datastores\ct_trials.db"
NLM_BASE  = "https://id.nlm.nih.gov/mesh/lookup/descriptor"
REQUEST_DELAY_MS = 150   # Polite delay between NLM API calls

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("ct_mesh_mapper.log", encoding="utf-8"),
    ]
)
log = logging.getLogger(__name__)


# ── NLM MeSH Lookup API ───────────────────────────────────────────────────────

def nlm_lookup(condition: str) -> tuple[str | None, str | None]:
    """
    Query NLM MeSH descriptor lookup API.
    """
    for match_type in ("exact", "contains"):
        params = urllib.parse.urlencode({
            "label": condition,
            "match": match_type,
            "limit": 1,
        })
        url = f"{NLM_BASE}?{params}"
        try:
            req = urllib.request.Request(
                url,
                headers={"Accept": "application/json", "User-Agent": "Meddash/1.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data and isinstance(data, list) and len(data) > 0:
                    result    = data[0]
                    resource  = result.get("resource", "")
                    mesh_term = result.get("label")
                    mesh_id   = resource.split("/")[-1] if resource else None
                    if mesh_id and mesh_id.startswith("D"):
                        return mesh_id, mesh_term
        except (urllib.error.URLError, json.JSONDecodeError, Exception):
            pass
        time.sleep(REQUEST_DELAY_MS / 1000.0)
    return None, None


# ── Gemini Flash Fallback ────────────────────────────────────────────

def is_gemini_available() -> bool:
    """Check if Gemini API key is configured in the environment."""
    return bool(os.environ.get("GEMINI_API_KEY"))


def gemini_mesh_lookup(condition: str) -> tuple[str | None, str | None]:
    """
    Use Gemini Flash API to map a condition to a MeSH ID.
    Returns (mesh_id, mesh_term) or (None, None).
    """
    if not is_gemini_available():
        return None, None

    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    
    generation_config = genai.GenerationConfig(
        response_mime_type="application/json",
        temperature=0.0
    )
    
    model = genai.GenerativeModel("gemini-1.5-flash", generation_config=generation_config)
    
    prompt = f"""You are a medical ontology expert. Map the following clinical trial condition to its OFFICIAL MeSH descriptor.

Condition: "{condition}"

Rules:
- Return ONLY valid, real MeSH descriptor IDs that start with D followed by 6 digits (e.g. D002289)
- If you are not certain of the exact MeSH ID, return null
- Do not invent MeSH IDs
- Return JSON only, no explanation

Format:
{{"mesh_id": "D002289", "mesh_term": "Carcinoma, Non-Small-Cell Lung"}}
or
{{"mesh_id": null, "mesh_term": null}}"""

    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()
        result = json.loads(raw)
        mesh_id   = result.get("mesh_id")
        mesh_term = result.get("mesh_term")
        if mesh_id and mesh_id.startswith("D") and mesh_id[1:].isdigit():
            return mesh_id, mesh_term
    except Exception as e:
        log.debug(f"Gemini lookup failed for '{condition}': {e}")
    return None, None


# ── Cache management ──────────────────────────────────────────────────────────

def get_unmapped_conditions(conn: sqlite3.Connection, limit: int = 0) -> list[str]:
    query = """
        SELECT DISTINCT tc.condition
        FROM trial_conditions tc
        LEFT JOIN condition_mesh_map cm ON tc.condition = cm.condition
        WHERE cm.condition IS NULL
        ORDER BY tc.condition
    """
    if limit:
        query += f" LIMIT {limit}"
    cur = conn.cursor()
    cur.execute(query)
    return [r[0] for r in cur.fetchall()]


def save_to_cache(conn: sqlite3.Connection, condition: str,
                  mesh_id: str | None, mesh_term: str | None, source: str) -> None:
    from datetime import timezone as tz
    conn.execute("""
        INSERT OR REPLACE INTO condition_mesh_map
            (condition, mesh_id, mesh_term, source, resolved_at)
        VALUES (?, ?, ?, ?, ?)
    """, (condition, mesh_id, mesh_term, source, datetime.now(tz.utc).isoformat()))


def apply_cache_to_conditions(conn: sqlite3.Connection) -> int:
    cur = conn.cursor()
    cur.execute("""
        UPDATE trial_conditions
        SET mesh_id   = cm.mesh_id,
            mesh_term = cm.mesh_term
        FROM condition_mesh_map cm
        WHERE trial_conditions.condition = cm.condition
          AND cm.mesh_id IS NOT NULL
          AND trial_conditions.mesh_id IS NULL
    """)
    conn.commit()
    return cur.rowcount


# ── Main mapping loop ─────────────────────────────────────────────────────────

def run_mapper(db_path: str = DB_FILE, use_gemini: bool = False,
               limit: int = 0) -> dict:
    conn = sqlite3.connect(db_path)

    unmapped = get_unmapped_conditions(conn, limit)
    total = len(unmapped)
    log.info(f"Unmapped conditions to process: {total:,}")

    if total == 0:
        log.info("All conditions already mapped — nothing to do.")
        conn.close()
        return {"total": 0, "nlm_resolved": 0, "gemini_resolved": 0, "unresolved": 0}

    gemini_available = use_gemini and is_gemini_available()
    if use_gemini and not gemini_available:
        log.warning("--gemini requested but GEMINI_API_KEY env variable is missing. Falling back to NLM-only mode.")

    nlm_resolved  = 0
    gemini_resolved = 0
    unresolved    = 0

    for i, condition in enumerate(unmapped, start=1):
        mesh_id, mesh_term = nlm_lookup(condition)

        if mesh_id:
            save_to_cache(conn, condition, mesh_id, mesh_term, "nlm_api")
            nlm_resolved += 1
            log.debug(f"NLM: '{condition}' → {mesh_id} ({mesh_term})")
        else:
            if gemini_available:
                mesh_id, mesh_term = gemini_mesh_lookup(condition)
                if mesh_id:
                    save_to_cache(conn, condition, mesh_id, mesh_term, "gemini_flash")
                    gemini_resolved += 1
                    log.debug(f"Gemini: '{condition}' → {mesh_id} ({mesh_term})")
                else:
                    save_to_cache(conn, condition, None, None, "unresolved")
                    unresolved += 1
            else:
                save_to_cache(conn, condition, None, None, "unresolved")
                unresolved += 1

        if i % 50 == 0:
            conn.commit()
            log.info(
                f"  Progress: {i}/{total} | NLM: {nlm_resolved} | "
                f"Gemini: {gemini_resolved} | Unresolved: {unresolved}"
            )

    conn.commit()
    updated = apply_cache_to_conditions(conn)
    log.info(f"Updated {updated:,} rows in trial_conditions with MeSH IDs")

    conn.close()
    return {
        "total":        total,
        "nlm_resolved": nlm_resolved,
        "gemini_resolved":gemini_resolved,
        "unresolved":   unresolved,
        "conditions_updated": updated,
    }


def print_stats(db_path: str = DB_FILE) -> None:
    conn = sqlite3.connect(db_path)
    cur  = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM trial_conditions")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM trial_conditions WHERE mesh_id IS NOT NULL")
    mapped = cur.fetchone()[0]

    cur.execute("SELECT source, COUNT(*) FROM condition_mesh_map GROUP BY source ORDER BY COUNT(*) DESC")
    by_source = cur.fetchall()

    cur.execute("""
        SELECT mesh_term, COUNT(*) as cnt
        FROM trial_conditions
        WHERE mesh_term IS NOT NULL
        GROUP BY mesh_term
        ORDER BY cnt DESC
        LIMIT 10
    """)
    top_terms = cur.fetchall()

    conn.close()

    pct = 100 * mapped / total if total else 0
    print(f"\n  MeSH Mapping Coverage")
    print("  " + "─" * 44)
    print(f"  Total conditions:   {total:>8,}")
    print(f"  Mapped to MeSH:     {mapped:>8,}  ({pct:.1f}%)")
    print(f"  Unmapped:           {total-mapped:>8,}")

    if by_source:
        print(f"\n  Resolution sources:")
        for src, cnt in by_source:
            print(f"    {src:<20} {cnt:>6,}")

    if top_terms:
        print(f"\n  Top 10 MeSH terms in ct_trials.db:")
        for term, cnt in top_terms:
            print(f"    {str(term)[:40]:<42} {cnt:>4} trials")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Meddash Condition → MeSH Ontology Bridge"
    )
    parser.add_argument("--db",    default=DB_FILE, help="SQLite database path")
    parser.add_argument("--gemini",  action="store_true",
                        help="Enable Gemini Flash fallback (requires GEMINI_API_KEY env var)")
    parser.add_argument("--limit", type=int, default=0,
                        help="Process only first N unmapped conditions (0 = all)")
    parser.add_argument("--stats", action="store_true",
                        help="Show mapping coverage stats and exit")
    args = parser.parse_args()

    if args.stats:
        print_stats(args.db)
        return

    print(f"\n  Meddash — Condition → MeSH Mapper")
    print(f"  Database: {args.db}")
    print(f"  Gemini Flash fallback: {'enabled' if args.gemini else 'disabled (--gemini to enable)'}")
    print("  " + "─" * 56)

    result = run_mapper(args.db, args.gemini, args.limit)

    if result.get("total", 0) > 0:
        print(f"\n  ✅ Mapping complete!")
        print(f"  NLM resolved:     {result['nlm_resolved']:,}")
        print(f"  Gemini resolved:  {result.get('gemini_resolved', 0):,}")
        print(f"  Unresolved:       {result['unresolved']:,}")
        print(f"  Rows updated:     {result['conditions_updated']:,}")
        print(f"\n  Run with --stats to see coverage breakdown.")
        print(f"  Next step: python ct_kol_bridge.py\n")

    print_stats(args.db)


if __name__ == "__main__":
    main()
