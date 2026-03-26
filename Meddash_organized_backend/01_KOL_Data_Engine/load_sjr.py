"""
load_sjr.py — SCImago Journal Rank (SJR) Downloader & Importer
===============================================================
This script:
1. Looks for a local SJR CSV file (manually downloaded from SCImago, or a cached copy).
2. If not found, attempts to download from SCImago (may be blocked by Cloudflare).
3. Cleans and normalizes the ISSN format to match PubMed's "XXXX-XXXX" convention.
4. Creates the `journal_metrics` table in meddash_kols.db (if it doesn't exist).
5. Imports all SJR records, using UPSERT logic to handle future annual re-runs.

HOW TO GET THE CSV FILE (if download is blocked):
    1. Go to: https://www.scimagojr.com/journalrank.php
    2. Click the "Download data" button (bottom of page, CSV icon).
    3. Save the file and rename it 'sjr_raw.csv'.
    4. Place 'sjr_raw.csv' in the same folder as this script:
       C:\\Users\\email\\.gemini\\antigravity\\scratch\\meddash\\
    5. Run: python load_sjr.py

Run once manually, then include in the annual cron refresh.
Usage: python load_sjr.py
"""

import sqlite3
import os
import re
import csv
import math
import logging
import urllib.request
from datetime import date

# ── Config ────────────────────────────────────────────────────────────────────
DB_FILE  = r"C:\Users\email\.gemini\antigravity\Meddash_organized_backend\06_Shared_Datastores\meddash_kols.db"
SJR_URL  = "https://www.scimagojr.com/journalrank.php?out=xls"   # Returns semicolon-delimited CSV
SJR_FILE = "sjr_raw.csv"
LOG_FILE = "load_sjr.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def normalize_issn(raw: str) -> str:
    """
    Converts SCImago ISSN formats to the PubMed standard: XXXX-XXXX.
    Input examples: '1234567X', '12345678', '1234-567X'
    Output: '1234-567X'
    """
    stripped = re.sub(r'[^0-9Xx]', '', raw).upper()
    if len(stripped) == 8:
        return f"{stripped[:4]}-{stripped[4:]}"
    return raw.strip()


def sjr_to_weight(sjr: float) -> float:
    """
    Converts a raw SJR score to the journal weight metric.
    Formula: log(1 + sjr * 10)  — scales to produce a meaningful spread.
    A top-tier journal (SJR ~20) yields a weight of ~5.9.
    A mid-tier journal  (SJR ~1)  yields a weight of ~2.4.
    A missing journal   (SJR=0)   fallback yields weight of 0.0 (log(1+0)=0).
    """
    return round(math.log(1 + sjr * 10), 4)


def ensure_journal_table(cursor: sqlite3.Cursor):
    """Creates the journal_metrics table if it doesn't already exist."""
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS journal_metrics (
            issn                VARCHAR(9) PRIMARY KEY,  -- e.g. '1546-170X' — joins to publications.issn
            issn_print          VARCHAR(9),              -- secondary ISSN where available
            journal_name        TEXT NOT NULL,
            sjr                 REAL DEFAULT 0.0,        -- raw SJR score from SCImago
            sjr_weight          REAL DEFAULT 0.0,        -- log(1 + sjr * 10), pre-computed for speed
            h_index             INTEGER DEFAULT 0,       -- H-index from SCImago
            total_docs          INTEGER DEFAULT 0,       -- Latest year doc count
            subject_area        TEXT,                    -- Broad subject area (e.g. 'Medicine')
            publisher           TEXT,
            last_updated        DATE
        );
        CREATE INDEX IF NOT EXISTS idx_journal_issn ON journal_metrics(issn);
    """)


# ── Download ──────────────────────────────────────────────────────────────────

def download_sjr(url: str, dest: str) -> bool:
    """
    Downloads SCImago CSV if not already present locally.
    Returns True if file is ready, False if manual download is required.
    """
    if os.path.exists(dest):
        logging.info(f"Using existing SJR file: {dest}")
        return True
    logging.info(f"Attempting to download SCImago dataset from {url} ...")
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; Meddash/1.0; research-tool)"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=60) as resp, open(dest, "wb") as f:
            f.write(resp.read())
        logging.info(f"Downloaded SJR data to: {dest}")
        return True
    except Exception as e:
        logging.warning(f"Automated download blocked ({e}).")
        logging.warning("="*60)
        logging.warning("MANUAL ACTION REQUIRED:")
        logging.warning("  1. Open: https://www.scimagojr.com/journalrank.php")
        logging.warning("  2. Click the 'Download data' CSV button (bottom of page)")
        logging.warning(f"  3. Rename the file to '{dest}' and save it in:")
        logging.warning(f"     {os.path.abspath(os.path.dirname(dest) or '.')}")
        logging.warning("  4. Run this script again.")
        logging.warning("="*60)
        return False


# ── Import ────────────────────────────────────────────────────────────────────

def import_sjr_to_db(csv_path: str, db_path: str):
    """Parses the SCImago CSV and upserts every journal into journal_metrics."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    ensure_journal_table(cursor)
    conn.commit()

    today = str(date.today())
    inserted = 0
    skipped = 0

    # SCImago uses semicolon delimiters and UTF-8-BOM encoding
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        
        # Normalise header names (SCImago headers can vary slightly by year)
        rows = list(reader)
        if not rows:
            logging.error("CSV appears empty. Check the download.")
            conn.close()
            return

        # Log the actual column names seen, helps debug yearly format changes
        logging.info(f"CSV columns detected: {list(rows[0].keys())}")
        
        for row in rows:
            # Robustly extract fields — SCImago column names are not always stable
            raw_issn   = row.get("Issn", row.get("ISSN", "")).strip()
            title      = row.get("Title", row.get("Journal name", "")).strip()
            sjr_raw    = row.get("SJR", row.get("SJR Best Quartile", "0")).strip().replace(",", ".")
            h_idx      = row.get("H index", "0").strip()
            total_docs = row.get("Total Docs. (2023)", row.get("Total Docs.", "0")).strip()
            area       = row.get("Areas", row.get("Subject Area", "")).strip()
            publisher  = row.get("Publisher", "").strip()

            if not raw_issn or not title:
                skipped += 1
                continue

            # SCImago often lists TWO ISSNs separated by comma: "1234-5678, 8765-4321"
            issn_parts = [normalize_issn(x) for x in raw_issn.split(",") if x.strip()]
            primary_issn = issn_parts[0] if issn_parts else ""
            secondary_issn = issn_parts[1] if len(issn_parts) > 1 else None

            if not primary_issn:
                skipped += 1
                continue

            # Parse numeric fields safely
            try:
                sjr_val = float(sjr_raw) if sjr_raw else 0.0
            except ValueError:
                sjr_val = 0.0

            try:
                h_val = int(float(h_idx)) if h_idx else 0
            except ValueError:
                h_val = 0

            try:
                docs_val = int(float(total_docs)) if total_docs else 0
            except ValueError:
                docs_val = 0

            weight = sjr_to_weight(sjr_val)

            cursor.execute("""
                INSERT INTO journal_metrics
                    (issn, issn_print, journal_name, sjr, sjr_weight, h_index, total_docs, subject_area, publisher, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(issn) DO UPDATE SET
                    journal_name = excluded.journal_name,
                    sjr          = excluded.sjr,
                    sjr_weight   = excluded.sjr_weight,
                    h_index      = excluded.h_index,
                    total_docs   = excluded.total_docs,
                    subject_area = excluded.subject_area,
                    publisher    = excluded.publisher,
                    last_updated = excluded.last_updated
            """, (primary_issn, secondary_issn, title, sjr_val, weight, h_val, docs_val, area, publisher, today))
            inserted += 1

    conn.commit()
    conn.close()
    logging.info(f"Import complete. Inserted/updated: {inserted:,}  |  Skipped: {skipped:,} rows.")


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.info("=== SCImago SJR Import Pipeline Starting ===")
    file_ready = download_sjr(SJR_URL, SJR_FILE)
    if not file_ready:
        logging.error("Cannot proceed: sjr_raw.csv not found. Follow the MANUAL ACTION instructions above.")
    else:
        import_sjr_to_db(SJR_FILE, DB_FILE)
        logging.info("=== SJR Import Pipeline Complete ===")
