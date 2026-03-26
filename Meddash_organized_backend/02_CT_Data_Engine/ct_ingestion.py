"""
ct_ingestion.py — Meddash ClinicalTrials.gov JSON → SQL Ingestion Engine
=========================================================================
Reads raw JSON files from ct_raw_json/ (produced by ct_crawler.py) and
populates all 11 tables in ct_trials.db.

Features:
    - Upsert logic (INSERT OR REPLACE) — safe to re-run after delta crawls
    - Batch commits every 500 trials for speed and crash-safety
    - Null-safe parsing — missing modules never crash the parser
    - Privacy: contact email used only to derive institution domain, then discarded
    - Progress reporting with ETA

Usage:
    python ct_ingestion.py                     # Process all new/updated files
    python ct_ingestion.py --dir ct_raw_json   # Custom JSON directory
    python ct_ingestion.py --limit 500         # Process first N files (for testing)

Tables populated (in one pass per trial):
    trials, trial_conditions, trial_interventions, trial_sponsors,
    trial_sites, trial_investigators, trial_outcomes,
    trial_publications, trial_eligibility
    (trial_results populated here from resultsSection)
    (ct_kol_summary populated by Step 5 — ct_kol_bridge.py)
"""

import json
import logging
import os
import sqlite3
import sys
import time
import argparse
from datetime import datetime, timezone

from ct_initializer import initialize_ct_db, get_ct_db_stats

DB_FILE  = r"C:\Users\email\.gemini\antigravity\Meddash_organized_backend\06_Shared_Datastores\ct_trials.db"
RAW_DIR  = "ct_raw_json"
BATCH_SIZE = 500   # Commit every N trials

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("ct_ingestion.log", encoding="utf-8"),
    ]
)
log = logging.getLogger(__name__)


# ── Privacy: email → institution domain lookup ────────────────────────────────
# Used ONLY in-memory. Email is never written to the database.

DOMAIN_TO_INSTITUTION = {
    "mayo.edu":           "Mayo Clinic",
    "mskcc.org":          "Memorial Sloan Kettering Cancer Center",
    "mdanderson.org":     "MD Anderson Cancer Center",
    "dana-farber.org":    "Dana-Farber Cancer Institute",
    "stanford.edu":       "Stanford University",
    "harvard.edu":        "Harvard University",
    "jhmi.edu":           "Johns Hopkins University",
    "ucsf.edu":           "University of California San Francisco",
    "nih.gov":            "National Institutes of Health",
    "uchicago.edu":       "University of Chicago",
    "pennmedicine.upenn.edu": "University of Pennsylvania",
    "yale.edu":           "Yale University",
    "columbia.edu":       "Columbia University",
    "duke.edu":           "Duke University",
    "vanderbilt.edu":     "Vanderbilt University",
    "bwh.harvard.edu":    "Brigham and Women's Hospital",
    "mgh.harvard.edu":    "Massachusetts General Hospital",
    "nyulangone.org":     "NYU Langone Health",
    "mountsinai.org":     "Mount Sinai",
    "clevelandclinic.org":"Cleveland Clinic",
}


def email_to_institution(email: str) -> str | None:
    """
    Derive institution name from email domain.
    Returns None if domain is not in our lookup (don't guess).
    Email string is never stored — used only as input here, discarded after.
    """
    if not email or "@" not in email:
        return None
    domain = email.split("@")[-1].lower().strip()
    return DOMAIN_TO_INSTITUTION.get(domain)


# ── Safe getters ──────────────────────────────────────────────────────────────

def _s(obj: dict, *keys, default=None):
    """Safe nested dict getter. Returns default if any key is missing."""
    for k in keys:
        if not isinstance(obj, dict):
            return default
        obj = obj.get(k, {}) if k != keys[-1] else obj.get(k, default)
    return obj


def _date(date_struct: dict | None) -> str | None:
    """Extract date string from CT.gov's {date, type} struct."""
    if not date_struct or not isinstance(date_struct, dict):
        return None
    return date_struct.get("date") or date_struct.get("dateStruct", {}).get("date")


# ── Module parsers ────────────────────────────────────────────────────────────

def parse_trial(nct_id: str, ps: dict, json_path: str) -> dict:
    """Parse core trial fields from protocolSection."""
    id_mod     = ps.get("identificationModule", {})
    status_mod = ps.get("statusModule", {})
    design_mod = ps.get("designModule", {})
    desc_mod   = ps.get("descriptionModule", {})

    enroll     = design_mod.get("enrollmentInfo", {})
    design_inf = design_mod.get("designInfo", {})

    return {
        "nct_id":                  nct_id,
        "brief_title":             id_mod.get("briefTitle"),
        "official_title":          id_mod.get("officialTitle"),
        "brief_summary":           desc_mod.get("briefSummary"),
        "study_type":              design_mod.get("studyType"),
        "overall_status":          status_mod.get("overallStatus"),
        "why_stopped":             status_mod.get("whyStopped"),
        "why_stopped_category":    None,  # Filled by Qwen in Step 8
        "phase":                   ", ".join(design_mod.get("phases", [])) or None,
        "start_date":              _date(status_mod.get("startDateStruct")),
        "completion_date":         _date(status_mod.get("completionDateStruct")),
        "primary_completion_date": _date(status_mod.get("primaryCompletionDateStruct")),
        "first_posted_date":       _date(status_mod.get("firstPostDateStruct")),
        "last_update_posted":      _date(status_mod.get("lastUpdatePostDateStruct")),
        "enrollment":              enroll.get("count"),
        "enrollment_type":         enroll.get("type"),
        "allocation":              design_inf.get("allocation"),
        "intervention_model":      design_inf.get("interventionModel"),
        "primary_purpose":         design_inf.get("primaryPurpose"),
        "trial_url":               f"https://clinicaltrials.gov/study/{nct_id}",
        "raw_json_path":           json_path,
        "updated_at":              datetime.now(timezone.utc).isoformat(),
    }


def parse_conditions(nct_id: str, ps: dict) -> list[dict]:
    cond_mod = ps.get("conditionsModule", {})
    rows = []
    for cond in cond_mod.get("conditions", []):
        if cond:
            rows.append({"nct_id": nct_id, "condition": cond,
                         "mesh_id": None, "mesh_term": None})
    return rows


def parse_interventions(nct_id: str, ps: dict) -> list[dict]:
    arms_mod = ps.get("armsInterventionsModule", {})
    rows = []
    for interv in arms_mod.get("interventions", []):
        rows.append({
            "nct_id":                   nct_id,
            "intervention_name":        interv.get("name"),
            "intervention_type":        interv.get("type"),
            "intervention_description": interv.get("description"),
        })
    return rows


def parse_sponsors(nct_id: str, ps: dict) -> list[dict]:
    spon_mod = ps.get("sponsorCollaboratorsModule", {})
    rows = []
    lead = spon_mod.get("leadSponsor", {})
    if lead.get("name"):
        rows.append({
            "nct_id":       nct_id,
            "sponsor_name": lead.get("name"),
            "sponsor_class":lead.get("class"),
            "is_lead":      1,
        })
    for collab in spon_mod.get("collaborators", []):
        if collab.get("name"):
            rows.append({
                "nct_id":       nct_id,
                "sponsor_name": collab.get("name"),
                "sponsor_class":collab.get("class"),
                "is_lead":      0,
            })
    return rows


def parse_sites_and_investigators(nct_id: str, ps: dict) -> tuple[list, list]:
    """
    Returns (sites_rows, investigators_rows).
    PRIVACY: Contact email extracted in-memory for domain lookup only — never stored.
    """
    loc_mod = ps.get("contactsLocationsModule", {})
    sites, investigators = [], []

    for loc in loc_mod.get("locations", []):
        facility = loc.get("facility")
        city     = loc.get("city")
        country  = loc.get("country")
        if facility or city or country:
            sites.append({
                "nct_id":        nct_id,
                "facility_name": facility,
                "city":          city,
                "state":         loc.get("state"),
                "country":       country,
                "zip_code":      loc.get("zip"),
                "site_status":   loc.get("status"),
            })

    for official in loc_mod.get("overallOfficials", []):
        name = official.get("name")
        if not name:
            continue

        affiliation = official.get("affiliation")

        # PRIVACY: Check if we can derive institution from email domain
        # centralContacts is a separate list — match by name
        if not affiliation:
            for contact in loc_mod.get("centralContacts", []):
                # Email used in-memory only to derive domain — never stored
                email_raw: str = str(contact.get("email") or "")
                derived = email_to_institution(email_raw)
                if derived:
                    affiliation = derived
                # email_raw goes out of scope here — never written to DB

        investigators.append({
            "nct_id":            nct_id,
            "investigator_name": name,
            "role":              official.get("role"),
            "affiliation":       affiliation,
            "kol_id":            None,   # Populated by Step 5
            "bridge_confidence": None,
            "bridge_method":     None,
        })

    return sites, investigators


def parse_outcomes(nct_id: str, ps: dict) -> list[dict]:
    outcomes_mod = ps.get("outcomesModule", {})
    rows = []
    for o in outcomes_mod.get("primaryOutcomes", []):
        rows.append({"nct_id": nct_id, "outcome_type": "PRIMARY",
                     "measure": o.get("measure"), "time_frame": o.get("timeFrame"),
                     "description": o.get("description")})
    for o in outcomes_mod.get("secondaryOutcomes", []):
        rows.append({"nct_id": nct_id, "outcome_type": "SECONDARY",
                     "measure": o.get("measure"), "time_frame": o.get("timeFrame"),
                     "description": o.get("description")})
    return rows


def parse_publications(nct_id: str, ps: dict) -> list[dict]:
    ref_mod = ps.get("referencesModule", {})
    rows = []
    for ref in ref_mod.get("references", []):
        pmid = ref.get("pmid")
        if pmid:
            rows.append({
                "nct_id":   nct_id,
                "pmid":     str(pmid),
                "ref_type": ref.get("type"),
                "citation": ref.get("citation"),
            })
    return rows


def parse_eligibility(nct_id: str, ps: dict) -> dict | None:
    elig_mod = ps.get("eligibilityModule", {})
    raw_criteria = elig_mod.get("eligibilityCriteria")
    if not raw_criteria and not elig_mod:
        return None
    return {
        "nct_id":                   nct_id,
        "raw_criteria":             raw_criteria,
        "min_age":                  elig_mod.get("minimumAge"),
        "max_age":                  elig_mod.get("maximumAge"),
        "sex":                      elig_mod.get("sex"),
        "healthy_volunteers":       elig_mod.get("healthyVolunteers"),
        "biomarkers_required":      None,  # Filled by Qwen (Step 8)
        "prior_treatment_required": None,
        "disease_stage":            None,
        "llm_processed":            0,
    }


def parse_results(nct_id: str, study: dict) -> list[dict]:
    """Parse resultsSection for efficacy outcomes and adverse events."""
    rs = study.get("resultsSection", {})
    rows = []

    # Outcome measures
    for om in rs.get("outcomeMeasuresModule", {}).get("outcomeMeasures", []):
        title = om.get("title", "")[:200]
        if not title:
            continue
        rows.append({
            "nct_id":           nct_id,
            "outcome_title":    title,
            "outcome_type":     om.get("type"),
            "measure":          om.get("title"),
            "reported_value":   None,
            "p_value":          None,
            "serious_ae_count": None,
            "deaths_reported":  None,
        })

    # Adverse events summary (serious AEs + deaths)
    ae_mod = rs.get("adverseEventsModule", {})
    if ae_mod:
        serious_ae = ae_mod.get("seriousEvents", [])
        deaths = ae_mod.get("otherEvents", [])
        total_serious = sum(
            e.get("stats", [{}])[0].get("numAffected", 0) or 0
            for e in serious_ae if e.get("stats")
        )
        # Add as a summary row if we have any adverse event data
        if total_serious > 0 or "seriousNumAffected" in str(ae_mod):
            rows.append({
                "nct_id":           nct_id,
                "outcome_title":    "ADVERSE_EVENTS_SUMMARY",
                "outcome_type":     "SAFETY",
                "measure":          "Serious Adverse Events",
                "reported_value":   str(total_serious) if total_serious else None,
                "p_value":          None,
                "serious_ae_count": total_serious,
                "deaths_reported":  ae_mod.get("deathsNumAffected"),
            })

    return rows


# ── SQL writers ───────────────────────────────────────────────────────────────

def upsert_trial(cur: sqlite3.Cursor, row: dict) -> None:
    cur.execute("""
        INSERT OR REPLACE INTO trials (
            nct_id, brief_title, official_title, brief_summary,
            study_type, overall_status, why_stopped, why_stopped_category,
            phase, start_date, completion_date, primary_completion_date,
            first_posted_date, last_update_posted,
            enrollment, enrollment_type, allocation, intervention_model,
            primary_purpose, trial_url, raw_json_path, updated_at
        ) VALUES (
            :nct_id, :brief_title, :official_title, :brief_summary,
            :study_type, :overall_status, :why_stopped, :why_stopped_category,
            :phase, :start_date, :completion_date, :primary_completion_date,
            :first_posted_date, :last_update_posted,
            :enrollment, :enrollment_type, :allocation, :intervention_model,
            :primary_purpose, :trial_url, :raw_json_path, :updated_at
        )
    """, row)


def insert_batch(cur: sqlite3.Cursor, table: str, rows: list[dict],
                 unique_cols: list[str]) -> None:
    """INSERT OR IGNORE a list of row dicts into a table."""
    if not rows:
        return
    cols = list(rows[0].keys())
    placeholders = ", ".join(f":{c}" for c in cols)
    col_list = ", ".join(cols)
    cur.executemany(
        f"INSERT OR IGNORE INTO {table} ({col_list}) VALUES ({placeholders})",
        rows
    )


# ── Main ingestion loop ───────────────────────────────────────────────────────

def ingest_all(raw_dir: str = RAW_DIR, db_path: str = DB_FILE,
               limit: int = 0) -> dict:
    """
    Main ingestion loop. Reads all JSON files in raw_dir and writes to db_path.
    Returns summary statistics.

    Args:
        raw_dir:  Path to directory of {nct_id}.json files
        db_path:  Path to ct_trials.db
        limit:    Process only this many files (0 = all)
    """
    if not os.path.isdir(raw_dir):
        log.error(f"Raw JSON directory not found: {raw_dir}")
        return {}

    # Ensure DB exists
    initialize_ct_db(db_path)

    files = [f for f in os.listdir(raw_dir) if f.endswith(".json")]
    total  = min(len(files), limit) if limit else len(files)
    log.info(f"Found {len(files):,} JSON files. Processing {total:,}.")

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    cur  = conn.cursor()

    processed = 0
    errors    = 0
    start     = time.time()

    for i, filename in enumerate(files[:total], start=1):
        path = os.path.join(raw_dir, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                study = json.load(f)

            ps     = study.get("protocolSection", {})
            id_mod = ps.get("identificationModule", {})
            nct_id = id_mod.get("nctId")

            if not nct_id:
                log.warning(f"No nctId in {filename} — skipping")
                errors += 1
                continue

            # ── Parse all modules ──────────────────────────────────────────
            trial_row   = parse_trial(nct_id, ps, path)
            conditions  = parse_conditions(nct_id, ps)
            interventions = parse_interventions(nct_id, ps)
            sponsors    = parse_sponsors(nct_id, ps)
            sites, investigators = parse_sites_and_investigators(nct_id, ps)
            outcomes    = parse_outcomes(nct_id, ps)
            publications = parse_publications(nct_id, ps)
            elig_row    = parse_eligibility(nct_id, ps)
            results     = parse_results(nct_id, study)

            # ── Write to DB ────────────────────────────────────────────────
            upsert_trial(cur, trial_row)

            insert_batch(cur, "trial_conditions",    conditions,    ["nct_id", "condition"])
            insert_batch(cur, "trial_interventions",  interventions, ["nct_id", "intervention_name"])
            insert_batch(cur, "trial_sponsors",       sponsors,      ["nct_id", "sponsor_name", "is_lead"])
            insert_batch(cur, "trial_sites",          sites,         ["nct_id", "facility_name", "city", "country"])
            insert_batch(cur, "trial_investigators",  investigators, ["nct_id", "investigator_name", "role"])
            insert_batch(cur, "trial_outcomes",       outcomes,      ["nct_id", "outcome_type", "measure"])
            insert_batch(cur, "trial_publications",   publications,  ["nct_id", "pmid"])
            insert_batch(cur, "trial_results",        results,       ["nct_id", "outcome_title"])

            if elig_row:
                cur.execute("""
                    INSERT OR IGNORE INTO trial_eligibility (
                        nct_id, raw_criteria, min_age, max_age, sex,
                        healthy_volunteers, biomarkers_required,
                        prior_treatment_required, disease_stage, llm_processed
                    ) VALUES (
                        :nct_id, :raw_criteria, :min_age, :max_age, :sex,
                        :healthy_volunteers, :biomarkers_required,
                        :prior_treatment_required, :disease_stage, :llm_processed
                    )
                """, elig_row)

            processed += 1

            # Batch commit
            if processed % BATCH_SIZE == 0:
                conn.commit()
                elapsed = time.time() - start
                rate    = processed / elapsed
                eta_s   = (total - processed) / rate if rate > 0 else 0
                eta_m, eta_s2 = divmod(int(eta_s), 60)
                log.info(
                    f"  Progress: {processed:,}/{total:,} "
                    f"({100*processed/total:.1f}%) | "
                    f"Rate: {rate:.0f}/s | ETA: {eta_m}m {eta_s2}s"
                )

        except json.JSONDecodeError as e:
            log.error(f"JSON parse error in {filename}: {e}")
            errors += 1
        except Exception as e:
            log.error(f"Unexpected error processing {filename}: {e}")
            errors += 1

    conn.commit()
    conn.close()

    elapsed = time.time() - start
    return {
        "processed": processed,
        "errors":    errors,
        "total":     total,
        "elapsed_s": round(elapsed, 1),
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Meddash CT JSON → SQL Ingestion Engine"
    )
    parser.add_argument("--dir",   default=RAW_DIR, help="Raw JSON directory")
    parser.add_argument("--db",    default=DB_FILE,  help="Target SQLite database")
    parser.add_argument("--limit", type=int, default=0,
                        help="Max trials to process (0 = all)")
    args = parser.parse_args()

    print(f"\n  Meddash — CT Ingestion Engine")
    print(f"  Source: {os.path.abspath(args.dir)}")
    print(f"  Target: {os.path.abspath(args.db)}")
    print("  " + "─" * 56)

    result = ingest_all(args.dir, args.db, args.limit)

    if result:
        stats = get_ct_db_stats(args.db)
        print(f"\n  {'Table':<30} {'Rows':>8}")
        print("  " + "─" * 40)
        for table, count in stats.items():
            print(f"  {table:<30} {count:>8,}")

        print(f"\n  ✅ Ingestion complete!")
        print(f"  Processed: {result['processed']:,} trials")
        print(f"  Errors:    {result['errors']:,}")
        print(f"  Time:      {result['elapsed_s']}s")
        print(f"\n  Next step: python ct_mesh_mapper.py\n")


if __name__ == "__main__":
    main()
