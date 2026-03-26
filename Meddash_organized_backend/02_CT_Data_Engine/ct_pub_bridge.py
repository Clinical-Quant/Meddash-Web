"""
ct_pub_bridge.py — Meddash CT Publications ↔ KOL Database Cross-Reference
===========================================================================
Matches trial_publications PMIDs (from CT.gov referencesModule) against
publications in meddash_kols.db to link trial evidence back to KOLs.

What it produces:
    1. trial_publications.kol_pub_id      — foreign key to meddash_kols.db pub id
    2. trial_publications.sjr_score       — SJR journal impact score (if available)
    3. trial_publications.journal_name    — journal name from meddash_kols.db
    4. Updates ct_kol_summary.pub_bridge_count per KOL (# matched trial pubs)
    5. Flags ct_kol_summary.high_evidence = 1 for KOLs with ≥3 matched trial pubs

Also adds the 3 new columns to trial_publications if not present (schema migration).

Usage:
    python ct_pub_bridge.py               # Cross-reference all PMIDs
    python ct_pub_bridge.py --stats       # Show bridge stats
"""

import argparse
import logging
import sqlite3

CT_DB  = r"C:\Users\email\.gemini\antigravity\Meddash_organized_backend\06_Shared_Datastores\ct_trials.db"
KOL_DB = r"C:\Users\email\.gemini\antigravity\Meddash_organized_backend\06_Shared_Datastores\meddash_kols.db"

HIGH_EVIDENCE_THRESHOLD = 3   # KOLs with this many+ matched trial pubs → high_evidence

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("ct_pub_bridge.log", encoding="utf-8"),
    ]
)
log = logging.getLogger(__name__)


# ── Schema migration ──────────────────────────────────────────────────────────

def ensure_columns(conn: sqlite3.Connection) -> None:
    """Add kol_pub_id, sjr_score, journal_name columns if not present."""
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(trial_publications)")
    existing = {r[1] for r in cur.fetchall()}

    migrations = [
        ("kol_pub_id",   "INTEGER"),     # FK to meddash_kols.db publications.id
        ("sjr_score",    "REAL"),         # SJR journal impact score
        ("journal_name", "VARCHAR(200)"), # Journal name from kols DB
    ]
    for col, dtype in migrations:
        if col not in existing:
            conn.execute(f"ALTER TABLE trial_publications ADD COLUMN {col} {dtype}")
            log.info(f"Added column: trial_publications.{col}")

    # Ensure ct_kol_summary has pub_bridge_count and high_evidence columns
    cur.execute("PRAGMA table_info(ct_kol_summary)")
    kol_cols = {r[1] for r in cur.fetchall()}
    kol_migrations = [
        ("pub_bridge_count", "INTEGER DEFAULT 0"),
        ("high_evidence",    "INTEGER DEFAULT 0"),
    ]
    for col, dtype in kol_migrations:
        if col not in kol_cols:
            conn.execute(f"ALTER TABLE ct_kol_summary ADD COLUMN {col} {dtype}")
            log.info(f"Added column: ct_kol_summary.{col}")

    conn.commit()


# ── KOL publication index ──────────────────────────────────────────────────────

def build_kol_pub_index(kol_conn: sqlite3.Connection) -> dict:
    """
    Build a dict: pmid (str) → {pub_id, journal_name, sjr_score, kol_ids: set}
    Loads all publications + their KOL authors + SJR scores in one pass.
    """
    cur = kol_conn.cursor()

    # Load all publications with PMID
    cur.execute("""
        SELECT p.id, p.pmid, p.journal_name
        FROM publications p
        WHERE p.pmid IS NOT NULL
    """)
    pubs = {}
    for pub_id, pmid, journal_name in cur.fetchall():
        pubs[str(pmid)] = {
            "pub_id":       pub_id,
            "journal_name": journal_name,
            "sjr_score":    None,
            "kol_ids":      set(),
        }

    log.info(f"Loaded {len(pubs):,} publications with PMIDs from meddash_kols.db")

    # Enrich with SJR scores via journal_metrics
    try:
        cur.execute("""
            SELECT p.pmid, jm.sjr
            FROM publications p
            JOIN journal_metrics jm ON (
                LOWER(p.journal_name) = LOWER(jm.journal_name)
                OR jm.issn = p.issn
            )
            WHERE p.pmid IS NOT NULL AND jm.sjr IS NOT NULL
        """)
        sjr_enriched = 0
        for pmid, sjr in cur.fetchall():
            pmid_str = str(pmid)
            if pmid_str in pubs:
                pubs[pmid_str]["sjr_score"] = sjr
                sjr_enriched += 1
        log.info(f"SJR scores enriched: {sjr_enriched:,}")
    except sqlite3.OperationalError as e:
        log.warning(f"SJR enrichment skipped (no issn column or journal mismatch): {e}")
        # Fallback: match by journal name only
        try:
            cur.execute("""
                SELECT p.pmid, jm.sjr
                FROM publications p
                JOIN journal_metrics jm ON LOWER(TRIM(p.journal_name)) = LOWER(TRIM(jm.journal_name))
                WHERE p.pmid IS NOT NULL AND jm.sjr IS NOT NULL
            """)
            for pmid, sjr in cur.fetchall():
                pmid_str = str(pmid)
                if pmid_str in pubs:
                    pubs[pmid_str]["sjr_score"] = sjr
        except sqlite3.OperationalError:
            pass

    # Load KOL authors per publication
    cur.execute("""
        SELECT ka.kol_id, p.pmid
        FROM kol_authorships ka
        JOIN publications p ON ka.publication_id = p.id
        WHERE p.pmid IS NOT NULL
    """)
    kol_author_count = 0
    for kol_id, pmid in cur.fetchall():
        pmid_str = str(pmid)
        if pmid_str in pubs:
            pubs[pmid_str]["kol_ids"].add(kol_id)
            kol_author_count += 1

    log.info(f"KOL-publication authorship links loaded: {kol_author_count:,}")
    return pubs


# ── Cross-reference loop ──────────────────────────────────────────────────────

def run_bridge(ct_db: str = CT_DB, kol_db: str = KOL_DB) -> dict:
    ct_conn  = sqlite3.connect(ct_db)
    kol_conn = sqlite3.connect(kol_db)

    ensure_columns(ct_conn)
    kol_index = build_kol_pub_index(kol_conn)
    kol_conn.close()

    ct_cur = ct_conn.cursor()

    # Fetch all trial PMIDs
    ct_cur.execute("""
        SELECT id, nct_id, pmid
        FROM trial_publications
        WHERE pmid IS NOT NULL
          AND kol_pub_id IS NULL
    """)
    trial_pubs = ct_cur.fetchall()
    log.info(f"Trial publications to process: {len(trial_pubs):,}")

    matched      = 0
    unmatched    = 0
    # kol_id → count of matched trial publications
    kol_bridge_counts: dict[int, int] = {}

    for row_id, nct_id, pmid in trial_pubs:
        pmid_str = str(pmid).strip()
        match    = kol_index.get(pmid_str)

        if match:
            ct_cur.execute("""
                UPDATE trial_publications
                SET kol_pub_id   = ?,
                    sjr_score    = ?,
                    journal_name = ?
                WHERE id = ?
            """, (match["pub_id"], match["sjr_score"], match["journal_name"], row_id))
            matched += 1
            log.info(
                f"MATCH: {nct_id} / PMID {pmid} → "
                f"pub_id {match['pub_id']} "
                f"(SJR: {match['sjr_score']}) "
                f"KOL authors: {len(match['kol_ids'])}"
            )
            # Increment bridge count per KOL author
            for kol_id in match["kol_ids"]:
                kol_bridge_counts[kol_id] = kol_bridge_counts.get(kol_id, 0) + 1
        else:
            unmatched += 1

    ct_conn.commit()

    # Update ct_kol_summary with bridge counts and high_evidence flag
    summary_updated = 0
    for kol_id, count in kol_bridge_counts.items():
        high_ev = 1 if count >= HIGH_EVIDENCE_THRESHOLD else 0
        # INSERT OR IGNORE to create row if not exists, then UPDATE
        ct_cur.execute("""
            INSERT OR IGNORE INTO ct_kol_summary (kol_id, trials_total,
                pub_bridge_count, high_evidence)
            VALUES (?, 0, ?, ?)
        """, (kol_id, count, high_ev))
        ct_cur.execute("""
            UPDATE ct_kol_summary
            SET pub_bridge_count = pub_bridge_count + ?,
                high_evidence    = CASE WHEN pub_bridge_count + ? >= ?
                                        THEN 1 ELSE high_evidence END
            WHERE kol_id = ?
        """, (count, count, HIGH_EVIDENCE_THRESHOLD, kol_id))
        summary_updated += 1

    ct_conn.commit()
    ct_conn.close()

    return {
        "total":          len(trial_pubs),
        "matched":        matched,
        "unmatched":      unmatched,
        "kols_updated":   summary_updated,
        "match_rate_pct": round(100 * matched / len(trial_pubs), 1) if trial_pubs else 0,
    }


def print_stats(ct_db: str = CT_DB) -> None:
    conn = sqlite3.connect(ct_db)
    cur  = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM trial_publications")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM trial_publications WHERE kol_pub_id IS NOT NULL")
    matched = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM trial_publications WHERE sjr_score IS NOT NULL")
    with_sjr = cur.fetchone()[0]

    # Top matched journals
    cur.execute("""
        SELECT journal_name, COUNT(*) as cnt, AVG(sjr_score)
        FROM trial_publications
        WHERE kol_pub_id IS NOT NULL AND journal_name IS NOT NULL
        GROUP BY journal_name
        ORDER BY cnt DESC
        LIMIT 8
    """)
    top_journals = cur.fetchall()

    # High-evidence KOLs
    try:
        cur.execute("""
            SELECT COUNT(*) FROM ct_kol_summary WHERE high_evidence = 1
        """)
        high_ev = cur.fetchone()[0]
    except sqlite3.OperationalError:
        high_ev = 0

    conn.close()
    pct = 100 * matched / total if total else 0

    print(f"\n  Publication Bridge Coverage")
    print("  " + "─" * 44)
    print(f"  Total trial publications:   {total:>6,}")
    print(f"  Matched to KOL pubs:        {matched:>6,}  ({pct:.1f}%)")
    print(f"  With SJR journal score:     {with_sjr:>6,}")
    print(f"  High-evidence KOLs:         {high_ev:>6,}  (≥{HIGH_EVIDENCE_THRESHOLD} matched pubs)")
    if top_journals:
        print(f"\n  Top journals in matched trial publications:")
        for jname, cnt, avg_sjr in top_journals:
            sjr_str = f"SJR {avg_sjr:.2f}" if avg_sjr else "no SJR"
            print(f"    {(jname or 'Unknown')[:42]:<44} {cnt:>3} pubs  {sjr_str}")
    print()


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Meddash CT Publications ↔ KOL Cross-Reference Bridge"
    )
    parser.add_argument("--ct-db",  default=CT_DB)
    parser.add_argument("--kol-db", default=KOL_DB)
    parser.add_argument("--stats",  action="store_true")
    args = parser.parse_args()

    if args.stats:
        print_stats(args.ct_db)
        return

    print(f"\n  Meddash — CT Publication Bridge")
    print(f"  CT DB:  {args.ct_db}  |  KOL DB: {args.kol_db}")
    print(f"  High-evidence threshold: {HIGH_EVIDENCE_THRESHOLD}+ matched publications")
    print("  " + "─" * 56)

    result = run_bridge(args.ct_db, args.kol_db)

    print(f"\n  ✅ Publication bridge complete!")
    print(f"  Trial publications processed: {result['total']:,}")
    print(f"  Matched to KOL DB:            {result['matched']:,}  ({result['match_rate_pct']}%)")
    print(f"  Unmatched:                    {result['unmatched']:,}")
    print(f"  KOL summaries updated:        {result['kols_updated']:,}")
    print(f"\n  Next step: python ct_eligibility_parser.py\n")

    print_stats(args.ct_db)


if __name__ == "__main__":
    main()
