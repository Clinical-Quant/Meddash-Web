"""
ct_results_parser.py — Meddash CT Results & Safety Data Enrichment
===================================================================
Enriches trial_results and trials tables with structured quantitative data
extracted from the resultsSection of each trial's raw JSON file.

Also classifies why_stopped free-text into categories using regex patterns
(no LLM required for most cases — Qwen handles edge cases in Step 8).

What it adds:
    trial_results:
        reported_value  — numeric outcome (e.g. "37.1" for ORR 37.1%)
        p_value         — statistical p-value string (e.g. "0.0001")
        serious_ae_count — total serious adverse events
        deaths_reported  — deaths count from AE module

    trials:
        why_stopped_category — SPONSOR_DECISION | SAFETY | EFFICACY |
                               ENROLLMENT | FUNDING | COVID_PANDEMIC | OTHER

Usage:
    python ct_results_parser.py                  # Process all unprocessed trials
    python ct_results_parser.py --limit 50       # Process first 50
    python ct_results_parser.py --stats          # Coverage report
    python ct_results_parser.py --dir ct_raw_json --db ct_trials.db
"""

import argparse
import json
import logging
import os
import re
import sqlite3

DB_FILE  = r"C:\Users\email\.gemini\antigravity\Meddash_organized_backend\06_Shared_Datastores\ct_trials.db"
RAW_DIR  = "ct_raw_json"
BATCH_SIZE = 200

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("ct_results_parser.log", encoding="utf-8"),
    ]
)
log = logging.getLogger(__name__)


# ── Why-stopped category classifier ──────────────────────────────────────────

WHY_STOPPED_PATTERNS: list[tuple[str, list[str]]] = [
    ("SAFETY", [
        r"safety", r"adverse\s+event", r"toxicit", r"side\s+effect",
        r"death", r"serious\s+AE", r"harm", r"risk\s+benefit",
    ]),
    ("EFFICACY", [
        r"efficac", r"futility", r"lack\s+of\s+(efficacy|benefit|response)",
        r"not\s+(effective|efficacious)", r"interim\s+analysis",
        r"surpass(ed)?\s+endpoint", r"early\s+(stopping|stop)",
    ]),
    ("ENROLLMENT", [
        r"enroll", r"accrual", r"recruit", r"insufficient\s+patient",
        r"slow\s+(accrual|enroll|recruit)", r"unable\s+to\s+accrue",
        r"patient\s+number", r"sample\s+size",
    ]),
    ("FUNDING", [
        r"fund", r"financ", r"budget", r"resource", r"sponsor\s+withdraw",
        r"no\s+longer\s+fund", r"grant",
    ]),
    ("COVID_PANDEMIC", [
        r"covid", r"pandemic", r"corona", r"sars-cov",
    ]),
    ("SPONSOR_DECISION", [
        r"sponsor\s+decision", r"business\s+decision", r"company\s+decision",
        r"portfolio", r"strategic", r"commercial", r"voluntary",
        r"sponsor\s+(choice|determin|halt|discontinu)",
    ]),
]

COMPILED_PATTERNS: list[tuple[str, list[re.Pattern]]] = [
    (cat, [re.compile(p, re.IGNORECASE) for p in patterns])
    for cat, patterns in WHY_STOPPED_PATTERNS
]


def classify_why_stopped(text: str | None) -> str | None:
    """
    Rule-based classification of why_stopped free text.
    Order matters — SAFETY is checked first as highest priority.
    Returns a category string or None if text is empty/null.
    """
    if not text or not text.strip():
        return None

    for category, patterns in COMPILED_PATTERNS:
        if any(p.search(text) for p in patterns):
            return category

    return "OTHER"


# ── Results section parsers ───────────────────────────────────────────────────

def extract_primary_outcome_value(outcome_measure: dict) -> str | None:
    """
    Extract the numeric result for a primary outcome measure.
    Navigates: outcomeMeasure → classes → categories → measurements → value
    Returns the first non-null measurement value, or None.
    """
    for cls in outcome_measure.get("classes", []):
        for cat in cls.get("categories", []):
            for meas in cat.get("measurements", []):
                val = meas.get("value")
                if val and val not in ("NA", "NE", "N/A", ""):
                    return str(val)
    return None


def extract_p_value(outcome_measure: dict) -> str | None:
    """
    Extract the p-value from the first statistical analysis.
    Returns the p-value string, or None.
    """
    for analysis in outcome_measure.get("analyses", []):
        pval = analysis.get("pValue")
        if pval:
            # Normalize "< 0.001" → "0.001", strip whitespace
            pval = re.sub(r"[<>≤≥~\s]", "", str(pval))
            if pval:
                return pval
    return None


def parse_ae_summary(ae_mod: dict) -> tuple[int | None, int | None]:
    """
    Parse adverse events module for serious AE count and deaths.
    Returns (serious_ae_total, deaths_count).
    """
    if not ae_mod:
        return None, None

    # Sum total numAffected across all serious event terms
    serious_total = 0
    for event in ae_mod.get("seriousEvents", []):
        for stat in event.get("stats", []):
            affected = stat.get("numAffected")
            if affected is not None:
                try:
                    serious_total += int(affected)
                except (ValueError, TypeError):
                    pass

    # Deaths — can be top-level or computed from serious events
    deaths = ae_mod.get("deathsNumAffected")
    if deaths is None:
        # Try to find from seriousEvents where term matches "death"
        for event in ae_mod.get("seriousEvents", []):
            term = (event.get("term") or "").lower()
            if "death" in term or "fatal" in term:
                for stat in event.get("stats", []):
                    affected = stat.get("numAffected")
                    if affected is not None:
                        deaths = affected
                        break

    return (serious_total if serious_total > 0 else None), deaths


# ── Main processing loop ──────────────────────────────────────────────────────

def run_parser(raw_dir: str = RAW_DIR, db_path: str = DB_FILE,
               limit: int = 0) -> dict:
    """
    Main loop: for each trial with a resultsSection, enrich trial_results rows
    and update trials.why_stopped_category.
    """
    if not os.path.isdir(raw_dir):
        log.error(f"Raw JSON directory not found: {raw_dir}")
        return {}

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    cur  = conn.cursor()

    # Get all nct_ids that have raw JSON accessible
    cur.execute("""
        SELECT nct_id, raw_json_path, why_stopped
        FROM trials
        ORDER BY nct_id
    """)
    all_trials = cur.fetchall()
    total = min(len(all_trials), limit) if limit else len(all_trials)
    log.info(f"Processing {total:,} trials for results enrichment")

    enriched_results  = 0
    why_stopped_classified = 0
    ae_enriched       = 0
    errors            = 0
    processed         = 0

    for nct_id, raw_json_path, why_stopped in all_trials[:total]:
        # Determine JSON file location
        json_path = raw_json_path or os.path.join(raw_dir, f"{nct_id}.json")
        if not os.path.exists(json_path):
            # Try raw_dir fallback
            json_path = os.path.join(raw_dir, f"{nct_id}.json")
        if not os.path.exists(json_path):
            continue

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                study = json.load(f)

            rs       = study.get("resultsSection", {})
            ae_mod   = rs.get("adverseEventsModule", {})
            om_mod   = rs.get("outcomeMeasuresModule", {})

            # ── Classify why_stopped ──────────────────────────────────────
            category = classify_why_stopped(why_stopped)
            if category:
                cur.execute("""
                    UPDATE trials SET why_stopped_category = ?
                    WHERE nct_id = ? AND why_stopped_category IS NULL
                """, (category, nct_id))
                why_stopped_classified += 1

            # ── Parse adverse events summary ──────────────────────────────
            serious_ae, deaths = parse_ae_summary(ae_mod)
            if serious_ae is not None or deaths is not None:
                # Update or insert AE summary row in trial_results
                cur.execute("""
                    UPDATE trial_results
                    SET serious_ae_count = ?,
                        deaths_reported  = ?
                    WHERE nct_id = ?
                      AND outcome_title  = 'ADVERSE_EVENTS_SUMMARY'
                """, (serious_ae, deaths, nct_id))

                if cur.rowcount == 0:
                    # Insert if Step 3 didn't capture it
                    cur.execute("""
                        INSERT OR IGNORE INTO trial_results
                            (nct_id, outcome_title, outcome_type, measure,
                             serious_ae_count, deaths_reported)
                        VALUES (?, 'ADVERSE_EVENTS_SUMMARY', 'SAFETY',
                                'Serious Adverse Events', ?, ?)
                    """, (nct_id, serious_ae, deaths))
                ae_enriched += 1

            # ── Enrich primary outcome measures ───────────────────────────
            for om in om_mod.get("outcomeMeasures", []):
                if om.get("type", "").upper() != "PRIMARY":
                    continue

                title      = (om.get("title") or "")[:200]
                rep_val    = extract_primary_outcome_value(om)
                p_val      = extract_p_value(om)

                if rep_val or p_val:
                    cur.execute("""
                        UPDATE trial_results
                        SET reported_value = COALESCE(reported_value, ?),
                            p_value        = COALESCE(p_value, ?)
                        WHERE nct_id = ?
                          AND outcome_type = 'PRIMARY'
                          AND (outcome_title = ? OR outcome_title LIKE ?)
                    """, (rep_val, p_val, nct_id, title, f"%{title[:40]}%"))
                    enriched_results += 1

            processed += 1

            if processed % BATCH_SIZE == 0:
                conn.commit()
                log.info(f"  Progress: {processed}/{total} | "
                         f"AE enriched: {ae_enriched} | "
                         f"Why-stopped classified: {why_stopped_classified}")

        except (json.JSONDecodeError, OSError) as e:
            log.warning(f"Error processing {nct_id}: {e}")
            errors += 1

    conn.commit()
    conn.close()

    return {
        "processed":              processed,
        "enriched_results":       enriched_results,
        "ae_enriched":            ae_enriched,
        "why_stopped_classified": why_stopped_classified,
        "errors":                 errors,
    }


def print_stats(db_path: str = DB_FILE) -> None:
    conn = sqlite3.connect(db_path)
    cur  = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM trial_results")
    total_results = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM trial_results WHERE serious_ae_count IS NOT NULL")
    with_ae = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM trial_results WHERE reported_value IS NOT NULL")
    with_val = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM trial_results WHERE p_value IS NOT NULL")
    with_pval = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM trials WHERE why_stopped IS NOT NULL")
    stopped = cur.fetchone()[0]

    cur.execute("""
        SELECT why_stopped_category, COUNT(*)
        FROM trials
        WHERE why_stopped_category IS NOT NULL
        GROUP BY why_stopped_category
        ORDER BY COUNT(*) DESC
    """)
    by_cat = cur.fetchall()

    conn.close()

    print(f"\n  Results Enrichment Coverage")
    print("  " + "─" * 44)
    print(f"  Total result rows:            {total_results:>6,}")
    print(f"  With serious_ae_count:        {with_ae:>6,}")
    print(f"  With reported outcome value:  {with_val:>6,}")
    print(f"  With p-value:                 {with_pval:>6,}")
    print(f"\n  Stopped trials:               {stopped:>6,}")
    if by_cat:
        print(f"  Why-stopped breakdown:")
        for cat, cnt in by_cat:
            print(f"    {(cat or 'NULL'):<25} {cnt:>4}")
    print()


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Meddash CT Results & Safety Enrichment Parser"
    )
    parser.add_argument("--dir",   default=RAW_DIR,  help="ct_raw_json directory")
    parser.add_argument("--db",    default=DB_FILE,   help="ct_trials.db path")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--stats", action="store_true")
    args = parser.parse_args()

    if args.stats:
        print_stats(args.db)
        return

    print(f"\n  Meddash — CT Results Parser")
    print(f"  DB: {args.db}  |  JSON dir: {args.dir}")
    print("  " + "─" * 56)

    result = run_parser(args.dir, args.db, args.limit)

    if result:
        print(f"\n  ✅ Enrichment complete!")
        print(f"  Trials processed:           {result['processed']:,}")
        print(f"  Outcome values extracted:   {result['enriched_results']:,}")
        print(f"  AE summaries enriched:      {result['ae_enriched']:,}")
        print(f"  Why-stopped classified:     {result['why_stopped_classified']:,}")
        print(f"  Errors:                     {result['errors']:,}")
        print(f"\n  Next step: python ct_pub_bridge.py\n")

    print_stats(args.db)


if __name__ == "__main__":
    main()
