"""
ct_eligibility_parser.py — Meddash Eligibility Criteria Structured Extractor
==============================================================================
Reads trial_eligibility.raw_criteria free-text and extracts 3 structured fields
that power trial population profiling in the KOL Intelligence Brief.

Two-pass strategy:
    Pass 1 — Regex fast-pass     (handles ~40% of cases, zero tokens)
    Pass 2 — Gemini Flash API    (remaining complex criteria)
              Activate with: --gemini
              Requires: GEMINI_API_KEY environment variable

Fields extracted:
    biomarkers_required      — e.g. "KRAS G12C, PD-L1 ≥1%"
    prior_treatment_required — e.g. "≥1 prior platinum-based chemotherapy"
    disease_stage            — e.g. "metastatic / stage IV"

Sets llm_processed = 1 on each row after processing.
Safe to re-run — skips already-processed rows by default.

Usage:
    python ct_eligibility_parser.py            # Regex only (fast, no LLM)
    python ct_eligibility_parser.py --gemini   # Regex + Gemini Flash API fallback
    python ct_eligibility_parser.py --stats    # Coverage report
    python ct_eligibility_parser.py --limit 50 # Process first 50 rows
    python ct_eligibility_parser.py --reprocess # Re-run all (including processed)
"""

import argparse
import json
import logging
import re
import sqlite3
import time
import os
import google.generativeai as genai

DB_FILE    = "ct_trials.db"
BATCH_SIZE = 100

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("ct_eligibility_parser.log", encoding="utf-8"),
    ]
)
log = logging.getLogger(__name__)


# ── Regex pattern library ─────────────────────────────────────────────────────
# Order matters — more specific patterns first within each group.

BIOMARKER_PATTERNS: list[tuple[str, str]] = [
    (r"KRAS\s*G12[CDVARSW]",              "KRAS G12C/mutant"),
    (r"\bKRAS\b.{0,10}(mutant|mutation)", "KRAS mutant"),
    (r"EGFR\s*(exon\s*(?:19|21|20)|activating\s+mutation|L858R|T790M)", "EGFR mutation"),
    (r"\bEGFR\b.{0,15}(positive|amplif|overexpress)",                   "EGFR+"),
    (r"BRAF\s*V600[EK]?",                 "BRAF V600E/K"),
    (r"\bBRAF\b.{0,10}(mutant|mutation)", "BRAF mutant"),
    (r"PD.?L1\s*(expression|TPS|CPS|score)?\s*[≥>]\s*(\d+%?)",        "PD-L1+"),
    (r"\bPD.?L1\b.{0,20}(positive|express|high)",                      "PD-L1+"),
    (r"HER2\s*(amplif|overexpress|3\+|2\+|IHC|FISH|positive)",         "HER2+"),
    (r"\bHER2\b.{0,20}(mutant|mutation)",                               "HER2 mutant"),
    (r"\bALK\b.{0,20}(rearrangement|fusion|positive|translocation)",   "ALK+"),
    (r"\bROS1\b.{0,20}(rearrangement|fusion|positive)",                "ROS1+"),
    (r"\bMET\b.{0,20}(amplif|exon\s*14|overexpress|high\s*copy)",      "MET alt"),
    (r"\bNTRK[123]?\b.{0,20}(fusion|rearrangement)",                   "NTRK fusion"),
    (r"\bBRCA[12]?\b.{0,15}(mutant|mutation|variant|germline|somatic)","BRCA mutant"),
    (r"\bBRCA[12]?\b",                                                  "BRCA"),
    (r"RET.{0,15}(fusion|rearrangement|mutant)",                       "RET fusion"),
    (r"\bFGFR[1234]?\b.{0,15}(amplif|mutant|fusion|alter)",            "FGFR alt"),
    (r"IDH[12]\b.{0,10}(mutant|mutation|R132|R172)",                   "IDH1/2 mutant"),
    (r"\bMMR.{0,10}(deficient|defic)|dMMR|MSI.?H|microsatellite\s+instab","MSI-H/dMMR"),
    (r"TMB\s*[≥>]\s*\d+",                                             "TMB-high"),
    (r"\bSTK11\b.{0,15}(mutant|mutation|loss)",                        "STK11 mutant"),
    (r"\bKEAP1\b.{0,15}(mutant|mutation)",                             "KEAP1 mutant"),
    (r"ECOG\s*(?:PS|performance\s+status)?\s*[≤<]\s*(\d)",             "ECOG PS≤N"),
    (r"Karnofsky\s*[≥>]\s*(\d+)",                                      "Karnofsky≥N"),
]

PRIOR_TREATMENT_PATTERNS: list[tuple[str, str]] = [
    (r"[≥≤<>]?\s*(\d+)\s*(prior|previous)\s*(line|course|regimen)s?\s*(of\s+(therapy|treatment|chemo\w*))?",
     "≥N prior lines"),
    (r"(at\s+least|minimum|no\s+more\s+than)\s+(\d+)\s*(prior|previous)",
     "prior line count"),
    (r"prior\s+(?:\w+\s+)?platinum.{0,40}(based|conta|doublet|chemotherapy)",
     "prior platinum-based chemotherapy"),
    (r"prior\s+(immunotherapy|checkpoint\s+inhibitor|anti.?PD.?[L1]|anti.?CTLA)",
     "prior immunotherapy"),
    (r"prior\s+(targeted\s+therapy|TKI|tyrosine\s+kinase)",
     "prior targeted therapy"),
    (r"treatment.?na[iï]ve|chemotherapy.?na[iï]ve|treatment\s+na[iï]ve",
     "treatment-naive (no prior therapy)"),
    (r"(first.?line|1st\s+line|frontline)",
     "first-line setting"),
    (r"(second.?line|2nd\s+line|previously\s+treated|relapsed|refractory)",
     "≥2nd line / relapsed-refractory"),
]

DISEASE_STAGE_PATTERNS: list[tuple[str, str]] = [
    (r"(stage\s+IV|stage\s+4\b|metastatic)",           "metastatic / stage IV"),
    (r"(stage\s+III[ABC]?|locally\s+advanced)",         "locally advanced / stage III"),
    (r"(stage\s+II[AB]?)",                              "stage II"),
    (r"(stage\s+I[AB]?(?!II|V))",                       "stage I"),
    (r"(recurrent|relapsed\s+and\s+refractory|R/R)",    "recurrent / R&R"),
    (r"(refractory\b)",                                  "refractory"),
    (r"(unresectable|irresectable)",                    "unresectable"),
    (r"(newly\s+diagnosed)",                            "newly diagnosed"),
    (r"(early\s+stage|localized)",                      "early stage / localized"),
]


def compile_patterns(patterns: list[tuple[str, str]]) -> list[tuple[re.Pattern, str]]:
    return [(re.compile(p, re.IGNORECASE), label) for p, label in patterns]


BIOMARKER_RE  = compile_patterns(BIOMARKER_PATTERNS)
PRIOR_TX_RE   = compile_patterns(PRIOR_TREATMENT_PATTERNS)
STAGE_RE      = compile_patterns(DISEASE_STAGE_PATTERNS)


def extract_section(text: str, header_pattern: str) -> str:
    match = re.search(header_pattern, text, re.IGNORECASE)
    if not match:
        return text
    start = match.end()
    next_header = re.search(
        r'\n\s*(?:Exclusion|Inclusion|Key)\s+Criteria\s*:',
        text[start:], re.IGNORECASE
    )
    end = start + next_header.start() if next_header else len(text)
    return text[start:end]


def apply_patterns(text: str, patterns: list[tuple[re.Pattern, str]]) -> list[str]:
    found = []
    seen  = set()
    for pat, label in patterns:
        m = pat.search(text)
        if m:
            groups = [g for g in m.groups() if g]
            if groups and any(c.isdigit() for c in groups[0]):
                key = f"{label.split('≥')[0].strip()} {groups[0]}"
            else:
                key = label
            if key not in seen:
                found.append(key)
                seen.add(key)
    return found


def regex_extract(raw_criteria: str) -> tuple[str | None, str | None, str | None]:
    if not raw_criteria:
        return None, None, None

    incl_text = extract_section(raw_criteria, r'Inclusion\s+Criteria\s*:')

    biomarkers = apply_patterns(incl_text, BIOMARKER_RE)
    prior_tx   = apply_patterns(incl_text, PRIOR_TX_RE)
    stage      = apply_patterns(incl_text, STAGE_RE)

    return (
        ", ".join(biomarkers)[:500] if biomarkers else None,
        ", ".join(prior_tx)[:500]   if prior_tx   else None,
        ", ".join(stage)[:200]       if stage       else None,
    )


# ── Gemini Flash API structured extraction ────────────────────────────────────────

def is_gemini_available() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY"))


def gemini_extract(raw_criteria: str) -> tuple[str | None, str | None, str | None]:
    """
    Use Gemini Flash API to extract 3 fields from eligibility criteria.
    Temperature=0 for deterministic output. Validates JSON before accepting.
    """
    criteria_snippet = raw_criteria[:2000].strip()

    prompt = f"""Extract structured information from these clinical trial eligibility criteria.

ELIGIBILITY CRITERIA:
{criteria_snippet}

Extract ONLY from the INCLUSION criteria (ignore exclusion).

Return a JSON object with exactly these keys:
{{
  "biomarkers_required": "comma-separated list of required biomarkers, mutations, or performance status (e.g. 'KRAS G12C, ECOG PS≤2') or null",
  "prior_treatment_required": "description of required prior treatment lines or classes (e.g. '≥1 prior platinum-based chemotherapy') or null if treatment-naive or not specified",
  "disease_stage": "disease stage(s) accepted (e.g. 'metastatic / stage IV') or null"
}}

Rules:
- null means not specified or not required
- Be concise, max 200 chars per field
- Return valid JSON ONLY, no explanation"""

    if not is_gemini_available():
        return None, None, None

    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    generation_config = genai.GenerationConfig(
        response_mime_type="application/json",
        temperature=0.0
    )
    model = genai.GenerativeModel("gemini-1.5-flash", generation_config=generation_config)

    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()
        result = json.loads(raw)
        return (
            str(result.get("biomarkers_required") or "")[:500] or None,
            str(result.get("prior_treatment_required") or "")[:500] or None,
            str(result.get("disease_stage") or "")[:200] or None,
        )
    except Exception as e:
        log.debug(f"Gemini extraction failed: {e}")
        return None, None, None


# ── Main parsing loop ─────────────────────────────────────────────────────────

def run_parser(db_path: str = DB_FILE, use_gemini: bool = False,
               limit: int = 0, reprocess: bool = False) -> dict:

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    cur  = conn.cursor()

    where_clause = "" if reprocess else "WHERE llm_processed = 0 OR llm_processed IS NULL"
    query = f"""
        SELECT id, nct_id, raw_criteria
        FROM trial_eligibility
        {where_clause}
        ORDER BY nct_id
    """
    if limit:
        query += f" LIMIT {limit}"

    cur.execute(query)
    rows  = cur.fetchall()
    total = len(rows)
    log.info(f"Eligibility rows to process: {total:,}")

    gemini_available = use_gemini and is_gemini_available()
    if use_gemini and not gemini_available:
        log.warning("--gemini requested but GEMINI_API_KEY is missing.")

    regex_hits   = 0
    gemini_hits  = 0
    total_filled = 0

    for i, (row_id, nct_id, raw_criteria) in enumerate(rows, start=1):
        if not raw_criteria:
            cur.execute("UPDATE trial_eligibility SET llm_processed = 1 WHERE id = ?", (row_id,))
            continue

        bio, prior_tx, stage = regex_extract(raw_criteria)
        method = "regex"

        if gemini_available:
            needs_gemini = not bio or not prior_tx or not stage
            if needs_gemini:
                q_bio, q_prior, q_stage = gemini_extract(raw_criteria)
                bio      = bio      or q_bio
                prior_tx = prior_tx or q_prior
                stage    = stage    or q_stage
                if any([q_bio, q_prior, q_stage]):
                    gemini_hits += 1
                    method = "gemini_flash"
                    time.sleep(0.05)

        if any([bio, prior_tx, stage]):
            cur.execute("""
                UPDATE trial_eligibility
                SET biomarkers_required      = COALESCE(biomarkers_required, ?),
                    prior_treatment_required = COALESCE(prior_treatment_required, ?),
                    disease_stage            = COALESCE(disease_stage, ?),
                    llm_processed            = 1
                WHERE id = ?
            """, (bio, prior_tx, stage, row_id))
            total_filled += 1
            if method == "regex":
                regex_hits += 1
        else:
            cur.execute("UPDATE trial_eligibility SET llm_processed = 1 WHERE id = ?", (row_id,))

        if i % BATCH_SIZE == 0:
            conn.commit()
            log.info(
                f"  Progress: {i}/{total} | Regex: {regex_hits} | "
                f"Gemini: {gemini_hits} | Filled: {total_filled}"
            )

    conn.commit()
    conn.close()
    return {
        "total":       total,
        "regex_hits":  regex_hits,
        "gemini_hits": gemini_hits,
        "filled":      total_filled,
        "empty":       total - total_filled,
    }


def print_stats(db_path: str = DB_FILE) -> None:
    conn = sqlite3.connect(db_path)
    cur  = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM trial_eligibility")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM trial_eligibility WHERE llm_processed = 1")
    processed = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM trial_eligibility WHERE biomarkers_required IS NOT NULL")
    with_bio = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM trial_eligibility WHERE prior_treatment_required IS NOT NULL")
    with_prior = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM trial_eligibility WHERE disease_stage IS NOT NULL")
    with_stage = cur.fetchone()[0]

    cur.execute("""
        SELECT disease_stage, COUNT(*) FROM trial_eligibility
        WHERE disease_stage IS NOT NULL
        GROUP BY disease_stage ORDER BY COUNT(*) DESC LIMIT 8
    """)
    stage_dist = cur.fetchall()

    cur.execute("""
        SELECT biomarkers_required FROM trial_eligibility
        WHERE biomarkers_required IS NOT NULL
        LIMIT 5
    """)
    sample_bio = [r[0] for r in cur.fetchall()]

    conn.close()

    pct = 100 * processed / total if total else 0
    print(f"\n  Eligibility Parser Coverage")
    print("  " + "─" * 44)
    print(f"  Total eligibility rows:       {total:>6,}")
    print(f"  Processed:                    {processed:>6,}  ({pct:.1f}%)")
    print(f"  With biomarkers_required:     {with_bio:>6,}")
    print(f"  With prior_tx required:       {with_prior:>6,}")
    print(f"  With disease_stage:           {with_stage:>6,}")

    if stage_dist:
        print(f"\n  Disease stage breakdown:")
        for stage, cnt in stage_dist:
            print(f"    {str(stage)[:40]:<42} {cnt:>3}")

    if sample_bio:
        print(f"\n  Sample biomarkers_required:")
        for b in sample_bio[:3]:
            print(f"    {str(b)[:70]}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Meddash CT Eligibility Criteria Structured Extractor"
    )
    parser.add_argument("--db",        default=DB_FILE)
    parser.add_argument("--gemini",    action="store_true",
                        help="Enable Gemini Flash API fallback (Requires GEMINI_API_KEY)")
    parser.add_argument("--limit",     type=int, default=0)
    parser.add_argument("--stats",     action="store_true")
    parser.add_argument("--reprocess", action="store_true",
                        help="Re-process already-processed rows")
    args = parser.parse_args()

    if args.stats:
        print_stats(args.db)
        return

    print(f"\n  Meddash — Eligibility Parser")
    print(f"  DB: {args.db}")
    print(f"  Mode: {'Regex + Gemini Flash' if args.gemini else 'Regex only (--gemini to enable Gemini)'}")
    print("  " + "─" * 56)

    result = run_parser(args.db, args.gemini, args.limit, args.reprocess)

    print(f"\n  ✅ Parsing complete!")
    print(f"  Rows processed:     {result['total']:,}")
    print(f"  Regex extracted:    {result['regex_hits']:,}")
    print(f"  Gemini extracted:   {result['gemini_hits']:,}")
    print(f"  Total filled:       {result['filled']:,}")
    print(f"  Still empty:        {result['empty']:,}")
    print(f"\n  Next step: python generate_kol_brief.py\n")

    print_stats(args.db)


if __name__ == "__main__":
    main()
