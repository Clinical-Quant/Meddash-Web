"""
kol_weight.py — KOL Author Publication Weight Calculator
=========================================================
Computes the Author Publication Weight (APW) for every KOL in meddash_kols.db.

Formula (as specified by the team):
    author_publication_weight = log(1 + sum(sjr_weight for each paper published))

Where sjr_weight per paper = log(1 + SJR * 10) from the journal_metrics table.
If no ISSN match is found, the fallback SJR is 0.0 (i.e., weight contribution = 0).

The result is stored in the `kols.author_publication_weight` column.

Run after load_sjr.py to populate weights.
Usage: python kol_weight.py
"""

import sqlite3
import math
import logging

DB_FILE = r"C:\Users\email\.gemini\antigravity\Meddash_organized_backend\06_Shared_Datastores\meddash_kols.db"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

FALLBACK_SJR_WEIGHT = math.log(1 + 1.0 * 10)  # fallback SJR=1.0 → weight ≈ 2.398


def ensure_apw_column(cursor: sqlite3.Cursor):
    """Add the author_publication_weight column to kols if it doesn't exist."""
    try:
        cursor.execute(
            "ALTER TABLE kols ADD COLUMN author_publication_weight REAL DEFAULT 0.0"
        )
        logging.info("Added 'author_publication_weight' column to kols table.")
    except sqlite3.OperationalError:
        pass  # Column already exists


def compute_all_weights(db_path: str):
    """
    For every KOL, sums the sjr_weight of each journal they published in,
    applies the outer log formula, and stores the result in kols.author_publication_weight.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    ensure_apw_column(cursor)
    conn.commit()

    # Fetch all KOL IDs
    cursor.execute("SELECT id, first_name, last_name FROM kols")
    kols = cursor.fetchall()

    logging.info(f"Computing publication weights for {len(kols)} KOLs...")

    updated = 0
    for (kol_id, first, last) in kols:
        # Pull all publications this KOL authored, joining to journal_metrics via ISSN
        cursor.execute("""
            SELECT 
                p.issn,
                COALESCE(jm.sjr_weight, 0.0) AS journal_weight
            FROM kol_authorships ka
            JOIN publications p ON ka.publication_id = p.id
            LEFT JOIN journal_metrics jm ON p.issn = jm.issn
            WHERE ka.kol_id = ?
        """, (kol_id,))
        rows = cursor.fetchall()

        if not rows:
            continue

        # Sum the SJR weights across all publications
        # If no ISSN match: use fallback weight
        cumulative_sjr_weight = 0.0
        for (issn, jw) in rows:
            if issn and jw and jw > 0.0:
                cumulative_sjr_weight += jw
            else:
                # Missing journal data — apply mentor's recommended fallback (SJR=1)
                cumulative_sjr_weight += FALLBACK_SJR_WEIGHT

        # Apply the outer formula: log(1 + cumulative sum)
        apw = round(math.log(1 + cumulative_sjr_weight), 4)

        cursor.execute(
            "UPDATE kols SET author_publication_weight = ? WHERE id = ?",
            (apw, kol_id)
        )
        updated += 1

    conn.commit()
    conn.close()
    logging.info(f"Author Publication Weight computed and stored for {updated} KOLs.")


def show_top_kols(db_path: str, n: int = 10):
    """Quick preview: print top N KOLs by publication weight."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT first_name, last_name, author_publication_weight,
               (SELECT COUNT(*) FROM kol_authorships WHERE kol_id = kols.id) AS pub_count
        FROM kols
        WHERE author_publication_weight > 0
        ORDER BY author_publication_weight DESC
        LIMIT ?
    """, (n,))
    rows = cursor.fetchall()
    conn.close()

    print(f"\n{'='*60}")
    print(f"  TOP {n} KOLs BY AUTHOR PUBLICATION WEIGHT")
    print(f"{'='*60}")
    print(f"{'Name':<30} {'APW Score':>10} {'# Papers':>10}")
    print(f"{'-'*60}")
    for (first, last, apw, count) in rows:
        print(f"{first} {last:<28} {apw:>10.4f} {count:>10}")
    print()


if __name__ == "__main__":
    logging.info("=== KOL Publication Weight Computation Starting ===")
    compute_all_weights(DB_FILE)
    show_top_kols(DB_FILE, n=10)
    logging.info("=== Weight Computation Complete ===")
