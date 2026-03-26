"""
ct_kol_bridge.py — Meddash CT.gov Investigator → KOL Database Bridge
=====================================================================
Links trial_investigators in ct_trials.db to KOL IDs in meddash_kols.db
using a 3-signal probabilistic matching engine.

Matching signals (total weight = 1.0):
    Signal 1 — Name fuzzy match     (weight: 0.40)
    Signal 2 — Institution match    (weight: 0.35)
    Signal 3 — MeSH topic overlap   (weight: 0.25)

Thresholds:
    score >= 0.70  → Confirmed match  (writes kol_id to trial_investigators)
    score 0.45-0.69 → Review queue    (adds to kol_merge_candidates for human review)
    score < 0.45   → No match

Also:
    - Populates ct_kol_summary (trial counts per matched KOL)
    - Handles name normalization (strips titles, handles "LastName F" format)

Usage:
    python ct_kol_bridge.py                   # Match all unlinked investigators
    python ct_kol_bridge.py --stats           # Show bridge coverage stats
    python ct_kol_bridge.py --limit 100       # Process first 100 investigators
    python ct_kol_bridge.py --threshold 0.65  # Adjust auto-confirm threshold
"""

import argparse
import difflib
import logging
import re
import sqlite3
from datetime import datetime, timezone

CT_DB   = r"C:\Users\email\.gemini\antigravity\Meddash_organized_backend\06_Shared_Datastores\ct_trials.db"
KOL_DB  = r"C:\Users\email\.gemini\antigravity\Meddash_organized_backend\06_Shared_Datastores\meddash_kols.db"

AUTO_MATCH_THRESHOLD = 0.70   # ≥ this → write kol_id
REVIEW_THRESHOLD     = 0.45   # ≥ this but < auto_match → human review queue

# Signal weights — must sum to 1.0
W_NAME        = 0.40
W_INSTITUTION = 0.35
W_MESH        = 0.25

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("ct_kol_bridge.log", encoding="utf-8"),
    ]
)
log = logging.getLogger(__name__)

# Titles to strip from investigator name strings
TITLE_PATTERN = re.compile(
    r"\b(Dr\.?|Prof\.?|MD|PhD|MPH|MS|BSc|FRCS|FACP|FACS|MRCP|DPhil)\b\.?,?\s*",
    re.IGNORECASE
)


# ── Name normalization ─────────────────────────────────────────────────────────

def normalize_name(raw: str) -> tuple[str, str]:
    """
    Normalize a name string to (last_name, first_initial).
    Handles formats:
        "Dr. Pasi A. Janne"  → ("janne", "p")
        "Janne PA"           → ("janne", "p")
        "J. Smith"           → ("smith", "j")
        "Smith, John"        → ("smith", "j")
    Returns lowercase (last, first_initial).
    """
    name = TITLE_PATTERN.sub("", raw).strip()

    # Handle "LastName, FirstName" format
    if "," in name:
        parts  = [p.strip() for p in name.split(",", 1)]
        last   = parts[0].lower()
        first  = parts[1][0].lower() if len(parts) > 1 and parts[1] else ""
        return last, first

    tokens = name.split()
    if not tokens:
        return "", ""

    if len(tokens) == 1:
        return tokens[0].lower(), ""

    # "Janne PA" or "Smith JA" — last token is initials
    last_tok = tokens[-1]
    if last_tok.isupper() and len(last_tok) <= 3:
        return tokens[0].lower(), last_tok[0].lower()

    # Standard "First [Middle] Last"
    last  = tokens[-1].lower()
    first = tokens[0][0].lower() if tokens[0] else ""
    return last, first


def name_score(inv_name: str, kol_first: str, kol_last: str) -> float:
    """
    Fuzzy name similarity between a raw investigator string and a KOL's
    first/last name. Returns 0.0–1.0.
    """
    inv_last, inv_init = normalize_name(inv_name)
    kol_last_n = kol_last.lower().strip() if kol_last else ""
    kol_init   = kol_first[0].lower() if kol_first else ""

    if not inv_last or not kol_last_n:
        return 0.0

    # Last name fuzzy match (primary)
    last_sim = difflib.SequenceMatcher(None, inv_last, kol_last_n).ratio()

    # First initial bonus: exact match = +0.15, no initial = neutral
    if inv_init and kol_init:
        first_bonus = 0.15 if inv_init == kol_init else -0.15
    else:
        first_bonus = 0.0

    return min(1.0, max(0.0, last_sim + first_bonus))


# ── Institution match ─────────────────────────────────────────────────────────

def institution_score(inv_affil: str | None, kol_institution: str | None) -> float:
    """
    Fuzzy institution similarity. Returns 0.0–1.0.
    Returns 0.0 if either is missing (no penalty — just no signal).
    """
    if not inv_affil or not kol_institution:
        return 0.0

    a = inv_affil.lower().strip()
    b = kol_institution.lower().strip()

    # Exact domain check (Mayo Clinic variants)
    if a == b:
        return 1.0

    # Token overlap — both contain at least 3 chars of same word
    a_tokens = set(w for w in re.split(r'\W+', a) if len(w) >= 4)
    b_tokens = set(w for w in re.split(r'\W+', b) if len(w) >= 4)
    if a_tokens and b_tokens:
        overlap = len(a_tokens & b_tokens) / max(len(a_tokens), len(b_tokens))
        if overlap >= 0.5:
            return overlap

    return difflib.SequenceMatcher(None, a, b).ratio()


# ── MeSH overlap ──────────────────────────────────────────────────────────────

def mesh_overlap_score(trial_mesh_ids: set[str], kol_mesh_ids: set[str]) -> float:
    """
    Jaccard-style overlap between trial MeSH IDs and KOL's research MeSH IDs.
    Returns 0.0 if either set is empty.
    """
    if not trial_mesh_ids or not kol_mesh_ids:
        return 0.0
    intersection = trial_mesh_ids & kol_mesh_ids
    union        = trial_mesh_ids | kol_mesh_ids
    return len(intersection) / len(union)


# ── Data loaders ──────────────────────────────────────────────────────────────

def load_kol_index(kol_db_path: str) -> list[dict]:
    """
    Load all KOLs from meddash_kols.db into memory with their:
    - id, first_name, last_name, institution
    - set of MeSH IDs from their publications
    """
    conn = sqlite3.connect(kol_db_path)
    cur  = conn.cursor()

    cur.execute("SELECT id, first_name, last_name, institution FROM kols")
    kols = []
    for row in cur.fetchall():
        kol_id, first, last, inst = row
        kols.append({
            "id":          kol_id,
            "first_name":  first or "",
            "last_name":   last or "",
            "institution": inst or "",
            "mesh_ids":    set(),
        })

    # Build KOL → MeSH ID lookup via kol_authorships + publication_mesh
    kol_map = {k["id"]: k for k in kols}

    # Try publication_mesh table (may be named differently)
    try:
        cur.execute("""
            SELECT ka.kol_id, pm.mesh_id
            FROM kol_authorships ka
            JOIN publications p ON ka.publication_id = p.id
            JOIN publication_mesh_map pm ON p.pmid = pm.pmid
            WHERE pm.mesh_id IS NOT NULL
        """)
        for kol_id, mesh_id in cur.fetchall():
            if kol_id in kol_map:
                kol_map[kol_id]["mesh_ids"].add(mesh_id)
    except sqlite3.OperationalError as e:
        log.warning(f"Could not load KOL MeSH data: {e} — MeSH signal disabled")

    conn.close()
    log.info(f"Loaded {len(kols):,} KOLs from meddash_kols.db into memory")
    kols_with_mesh = sum(1 for k in kols if k["mesh_ids"])
    log.info(f"KOLs with MeSH data: {kols_with_mesh:,}")
    return kols


def get_unmapped_investigators(ct_conn: sqlite3.Connection,
                                limit: int = 0) -> list[dict]:
    """Return trial investigators with no kol_id yet."""
    query = """
        SELECT
            ti.id,
            ti.nct_id,
            ti.investigator_name,
            ti.role,
            ti.affiliation,
            GROUP_CONCAT(DISTINCT tc.mesh_id) as trial_mesh_ids
        FROM trial_investigators ti
        LEFT JOIN trial_conditions tc ON ti.nct_id = tc.nct_id
        WHERE ti.kol_id IS NULL
          AND ti.investigator_name IS NOT NULL
        GROUP BY ti.id
    """
    if limit:
        query += f" LIMIT {limit}"
    cur = ct_conn.cursor()
    cur.execute(query)
    rows = []
    for r in cur.fetchall():
        mesh_raw = r[5] or ""
        rows.append({
            "inv_id":       r[0],
            "nct_id":       r[1],
            "name":         r[2],
            "role":         r[3],
            "affiliation":  r[4],
            "trial_mesh":   set(m for m in mesh_raw.split(",") if m and m.startswith("D")),
        })
    return rows


# ── Match engine ──────────────────────────────────────────────────────────────

def match_investigator(inv: dict, kol_index: list[dict]) -> tuple[dict | None, float]:
    """
    Find the best KOL match for an investigator using 3-signal scoring.
    Returns (best_kol_dict, combined_score) or (None, 0.0).
    """
    best_kol   = None
    best_score = 0.0

    for kol in kol_index:
        # ── Signal 1: Name fuzzy match ─────────────────────────────────
        n_score = name_score(inv["name"], kol["first_name"], kol["last_name"])

        # Early prune: if name similarity < 0.50, no match possible
        if n_score < 0.50:
            continue

        # ── Signal 2: Institution match ────────────────────────────────
        i_score = institution_score(inv["affiliation"], kol["institution"])

        # ── Signal 3: MeSH overlap ────────────────────────────────────
        m_score = mesh_overlap_score(inv["trial_mesh"], kol["mesh_ids"])

        # If no institution data on either side, redistribute weight to name
        if not inv["affiliation"] or not kol["institution"]:
            combined = (
                n_score * (W_NAME + W_INSTITUTION * 0.5) +
                m_score * (W_MESH + W_INSTITUTION * 0.5)
            )
        else:
            combined = (
                n_score * W_NAME +
                i_score * W_INSTITUTION +
                m_score * W_MESH
            )

        if combined > best_score:
            best_score = combined
            best_kol   = kol

    return best_kol, best_score


# ── Writers ───────────────────────────────────────────────────────────────────

def write_match(cur: sqlite3.Cursor, inv_id: int, kol_id: int,
                score: float, method: str) -> None:
    cur.execute("""
        UPDATE trial_investigators
        SET kol_id = ?, bridge_confidence = ?, bridge_method = ?
        WHERE id = ?
    """, (kol_id, round(score, 4), method, inv_id))


def queue_for_review(ct_cur: sqlite3.Cursor, inv: dict,
                     kol: dict, score: float) -> None:
    """Add ambiguous match to kol_merge_candidates in meddash_kols.db for review."""
    # We write to a separate review file instead to avoid cross-DB write complexity
    with open("ct_bridge_review.tsv", "a", encoding="utf-8") as f:
        f.write(
            f"{inv['nct_id']}\t{inv['name']}\t{inv['affiliation'] or ''}\t"
            f"{kol['first_name']} {kol['last_name']}\t{kol['institution']}\t"
            f"{score:.3f}\n"
        )


# ── KOL Summary recompute ─────────────────────────────────────────────────────

def recompute_kol_summary(ct_conn: sqlite3.Connection) -> int:
    """
    Recompute ct_kol_summary for all KOLs that have matched investigators.
    Returns number of KOL summary rows updated.
    """
    cur = ct_conn.cursor()

    # Get all distinct kol_ids that have matches
    cur.execute("SELECT DISTINCT kol_id FROM trial_investigators WHERE kol_id IS NOT NULL")
    kol_ids = [r[0] for r in cur.fetchall()]

    if not kol_ids:
        return 0

    for kol_id in kol_ids:
        cur.execute("""
            SELECT
                COUNT(DISTINCT ti.nct_id)                                      as trials_total,
                COUNT(DISTINCT CASE WHEN ti.role LIKE '%PRINCIPAL%' THEN ti.nct_id END) as trials_as_pi,
                COUNT(DISTINCT CASE WHEN ts.sponsor_class = 'INDUSTRY'
                                    THEN ti.nct_id END)                        as industry_trials,
                COUNT(DISTINCT CASE WHEN t.phase LIKE '%1%' THEN ti.nct_id END) as phase1,
                COUNT(DISTINCT CASE WHEN t.phase LIKE '%2%' THEN ti.nct_id END) as phase2,
                COUNT(DISTINCT CASE WHEN t.phase LIKE '%3%' THEN ti.nct_id END) as phase3,
                COUNT(DISTINCT CASE WHEN t.phase LIKE '%4%' THEN ti.nct_id END) as phase4,
                COUNT(DISTINCT CASE WHEN t.overall_status IN ('RECRUITING','ACTIVE_NOT_RECRUITING')
                                    THEN ti.nct_id END)                        as active,
                COUNT(DISTINCT CASE WHEN t.overall_status = 'COMPLETED'
                                    THEN ti.nct_id END)                        as completed,
                COUNT(DISTINCT CASE WHEN t.overall_status = 'TERMINATED'
                                    THEN ti.nct_id END)                        as terminated,
                COUNT(DISTINCT ts.sponsor_name)                                as unique_sponsors,
                COUNT(DISTINCT tc.condition)                                   as unique_conditions,
                COUNT(DISTINCT tsi.facility_name)                              as unique_sites
            FROM trial_investigators ti
            JOIN trials t ON ti.nct_id = t.nct_id
            LEFT JOIN trial_sponsors ts ON ti.nct_id = ts.nct_id
            LEFT JOIN trial_conditions tc ON ti.nct_id = tc.nct_id
            LEFT JOIN trial_sites tsi ON ti.nct_id = tsi.nct_id
            WHERE ti.kol_id = ?
        """, (kol_id,))

        row = cur.fetchone()
        if row:
            cur.execute("""
                INSERT OR REPLACE INTO ct_kol_summary (
                    kol_id, trials_total, trials_as_pi, industry_trials,
                    phase1_trials, phase2_trials, phase3_trials, phase4_trials,
                    active_trials, completed_trials, terminated_trials,
                    unique_sponsors, unique_conditions, unique_sites, last_computed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (kol_id, *row, datetime.now(timezone.utc).isoformat()))

    ct_conn.commit()
    return len(kol_ids)


# ── Main bridge loop ──────────────────────────────────────────────────────────

def run_bridge(ct_db: str = CT_DB, kol_db: str = KOL_DB,
               limit: int = 0, threshold: float = AUTO_MATCH_THRESHOLD) -> dict:

    kol_index = load_kol_index(kol_db)
    if not kol_index:
        log.error("No KOLs found in meddash_kols.db — aborting")
        return {}

    ct_conn = sqlite3.connect(ct_db)
    ct_cur  = ct_conn.cursor()

    investigators = get_unmapped_investigators(ct_conn, limit)
    total = len(investigators)
    log.info(f"Investigators to match: {total:,}")

    matched  = 0
    reviewed = 0
    unmatched = 0

    for i, inv in enumerate(investigators, start=1):
        best_kol, score = match_investigator(inv, kol_index)

        if best_kol and score >= threshold:
            write_match(ct_cur, inv["inv_id"], best_kol["id"], score,
                        method="name_fuzzy_affil_mesh")
            matched += 1
            log.debug(
                f"MATCH: '{inv['name']}' → "
                f"{best_kol['first_name']} {best_kol['last_name']} "
                f"(score={score:.3f})"
            )

        elif best_kol and score >= REVIEW_THRESHOLD:
            queue_for_review(ct_cur, inv, best_kol, score)
            reviewed += 1
            log.debug(
                f"REVIEW: '{inv['name']}' → "
                f"{best_kol['first_name']} {best_kol['last_name']} "
                f"(score={score:.3f})"
            )
        else:
            unmatched += 1

        if i % 100 == 0:
            ct_conn.commit()
            log.info(
                f"  Progress {i}/{total} | Matched: {matched} | "
                f"Review: {reviewed} | Unmatched: {unmatched}"
            )

    ct_conn.commit()

    # Recompute summary for all matched KOLs
    summary_updated = recompute_kol_summary(ct_conn)
    log.info(f"ct_kol_summary updated for {summary_updated} KOLs")

    ct_conn.close()
    return {
        "total":           total,
        "matched":         matched,
        "review_queue":    reviewed,
        "unmatched":       unmatched,
        "summary_updated": summary_updated,
    }


def print_stats(ct_db: str = CT_DB) -> None:
    conn = sqlite3.connect(ct_db)
    cur  = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM trial_investigators")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM trial_investigators WHERE kol_id IS NOT NULL")
    matched = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM ct_kol_summary WHERE trials_total > 0")
    kols_with_trials = cur.fetchone()[0]

    cur.execute("""
        SELECT kol_id, trials_total, trials_as_pi, phase3_trials, industry_trials
        FROM ct_kol_summary
        WHERE trials_total > 0
        ORDER BY trials_as_pi DESC
        LIMIT 10
    """)
    top = cur.fetchall()
    conn.close()

    pct = 100 * matched / total if total else 0
    print(f"\n  KOL Bridge Coverage")
    print("  " + "─" * 44)
    print(f"  Total investigators:   {total:>8,}")
    print(f"  Matched to KOL:        {matched:>8,}  ({pct:.1f}%)")
    print(f"  KOLs with CT data:     {kols_with_trials:>8,}")
    if top:
        print(f"\n  Top KOLs by trial PI count (kol_id, total, as_PI, Ph3, industry):")
        for row in top:
            print(f"    {row}")
    print()


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Meddash CT Investigator → KOL Bridge"
    )
    parser.add_argument("--ct-db",    default=CT_DB,  help="ct_trials.db path")
    parser.add_argument("--kol-db",   default=KOL_DB, help="meddash_kols.db path")
    parser.add_argument("--limit",    type=int, default=0)
    parser.add_argument("--threshold",type=float, default=AUTO_MATCH_THRESHOLD,
                        help=f"Auto-confirm score threshold (default: {AUTO_MATCH_THRESHOLD})")
    parser.add_argument("--stats",    action="store_true")
    args = parser.parse_args()

    if args.stats:
        print_stats(args.ct_db)
        return

    print(f"\n  Meddash — CT KOL Bridge")
    print(f"  CT DB:   {args.ct_db}")
    print(f"  KOL DB:  {args.kol_db}")
    print(f"  Weights: Name={W_NAME} / Institution={W_INSTITUTION} / MeSH={W_MESH}")
    print(f"  Auto-confirm threshold: {args.threshold}")
    print("  " + "─" * 56)

    result = run_bridge(args.ct_db, args.kol_db, args.limit, args.threshold)

    if result:
        match_rate = 100 * result["matched"] / result["total"] if result["total"] else 0
        print(f"\n  ✅ Bridge complete!")
        print(f"  Total investigators:   {result['total']:,}")
        print(f"  Confirmed matches:     {result['matched']:,}  ({match_rate:.1f}%)")
        print(f"  Queued for review:     {result['review_queue']:,}")
        print(f"  Unmatched:             {result['unmatched']:,}")
        print(f"  ct_kol_summary rows:   {result['summary_updated']:,}")
        if result["review_queue"] > 0:
            print(f"\n  ⚠  Review candidates written to: ct_bridge_review.tsv")
        print(f"\n  Next step: python ct_results_parser.py\n")

    print_stats(args.ct_db)


if __name__ == "__main__":
    main()
