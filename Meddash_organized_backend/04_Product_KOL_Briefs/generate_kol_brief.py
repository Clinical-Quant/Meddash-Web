"""
generate_kol_brief.py — Meddash KOL Intelligence Landscape Brief Generator
===========================================================================
Phase 1 product output: synthesises all CT Engine pipeline data into a
structured, ranked KOL Intelligence Brief for a given indication.

Two data pathways (both used when available):
    CT-Pathway  — Trial activity from ct_trials.db (PI roles, phases, sponsors,
                  eligibility biomarkers, results)
    KOL-Pathway — Publication signal from meddash_kols.db (pub count, h-index,
                  SJR, therapeutic area) — requires ct_kol_bridge to have run

Scoring (0–100):
    Trial Activity Score (50%)
        - PI count on Phase 2/3 trials        (20 pts max)
        - Industry-sponsored trials             (15 pts max)
        - Active / recruiting trials            (10 pts max)
        - Unique sponsors                       (5 pts max)

    Publication Signal Score (30%)  — from meddash_kols.db if bridge matched
        - Publication count                     (15 pts max)
        - Avg SJR score                         (10 pts max)
        - High-evidence flag                    (5 pts)

    Indication Specificity Score (20%)
        - Biomarker overlap with query          (12 pts max)
        - Trial population stage match          (8 pts max)

Output:
    kol_brief_{slug}.md    — Human-readable Landscape Report
    kol_brief_{slug}.json  — Machine-readable for Meddash SaaS API

Usage:
    python generate_kol_brief.py --query "KRAS G12C lung cancer"
    python generate_kol_brief.py --query "HER2 breast cancer" --top 20
    python generate_kol_brief.py --query "EGFR NSCLC" --out ./briefs/
"""

import argparse
import json
import os
import re
import sqlite3
from datetime import datetime, timezone

CT_DB  = r"C:\Users\email\.gemini\antigravity\Meddash_organized_backend\06_Shared_Datastores\ct_trials.db"
KOL_DB = r"C:\Users\email\.gemini\antigravity\Meddash_organized_backend\06_Shared_Datastores\meddash_kols.db"


# ── Query keyword expander ─────────────────────────────────────────────────────

QUERY_EXPANSIONS: dict[str, list[str]] = {
    "kras":         ["kras", "kirsten", "ras", "k-ras"],
    "egfr":         ["egfr", "erlotinib", "gefitinib", "osimertinib"],
    "her2":         ["her2", "erbb2", "trastuzumab", "pertuzumab"],
    "braf":         ["braf", "vemurafenib", "dabrafenib"],
    "lung":         ["lung", "nsclc", "non-small cell", "non small cell", "pulmonary"],
    "breast":       ["breast", "mammary"],
    "colorectal":   ["colorectal", "colon", "rectal", "crc"],
    "pancreatic":   ["pancreatic", "pancreas"],
    "melanoma":     ["melanoma", "skin cancer"],
    "glioblastoma": ["glioblastoma", "gbm", "glioma", "brain tumor"],
}


def expand_query(query: str) -> list[str]:
    """Expand query keywords using known synonym mappings."""
    terms = set(query.lower().split())
    expanded = set(query.lower().split())
    for key, synonyms in QUERY_EXPANSIONS.items():
        if key in terms:
            expanded.update(synonyms)
    return list(expanded)


# ── Data fetchers ──────────────────────────────────────────────────────────────

def find_matching_trials(ct_conn: sqlite3.Connection,
                          query_terms: list[str],
                          limit: int = 2000) -> list[str]:
    """
    Find NCT IDs for trials matching the query.
    Searches: trial conditions, trial interventions, brief_title.
    """
    cur = ct_conn.cursor()
    nct_ids: set[str] = set()

    for term in query_terms[:6]:  # Limit to first 6 terms to avoid N+1
        like = f"%{term}%"
        cur.execute("""
            SELECT DISTINCT tc.nct_id FROM trial_conditions tc
            WHERE LOWER(tc.condition) LIKE ?
            LIMIT ?
        """, (like, limit))
        nct_ids.update(r[0] for r in cur.fetchall())

        cur.execute("""
            SELECT DISTINCT t.nct_id FROM trials t
            WHERE LOWER(t.brief_title) LIKE ?
            LIMIT ?
        """, (like, limit))
        nct_ids.update(r[0] for r in cur.fetchall())

    return list(nct_ids)


def fetch_investigator_profiles(ct_conn: sqlite3.Connection,
                                 nct_ids: list[str],
                                 top_n: int) -> list[dict]:
    """
    For matched trials, aggregate investigator activity statistics.
    Returns sorted list of investigator dicts (most active first).
    Works even when trial_investigators.kol_id is not yet populated.
    """
    if not nct_ids:
        return []

    placeholders = ",".join("?" * len(nct_ids))
    cur = ct_conn.cursor()

    cur.execute(f"""
        SELECT
            ti.investigator_name,
            ti.affiliation,
            ti.kol_id,
            ti.bridge_confidence,
            COUNT(DISTINCT ti.nct_id)                                          AS trials_total,
            COUNT(DISTINCT CASE WHEN ti.role LIKE '%PRINCIPAL%' OR
                                     ti.role = 'STUDY_CHAIR'
                               THEN ti.nct_id END)                             AS trials_as_pi,
            COUNT(DISTINCT CASE WHEN t.phase LIKE '%3%'
                               THEN ti.nct_id END)                             AS phase3_count,
            COUNT(DISTINCT CASE WHEN t.phase LIKE '%2%'
                               THEN ti.nct_id END)                             AS phase2_count,
            COUNT(DISTINCT CASE WHEN ts.sponsor_class = 'INDUSTRY'
                               THEN ti.nct_id END)                             AS industry_trials,
            COUNT(DISTINCT CASE WHEN t.overall_status IN
                               ('RECRUITING','ACTIVE_NOT_RECRUITING')
                               THEN ti.nct_id END)                             AS active_trials,
            COUNT(DISTINCT ts.sponsor_name)                                    AS unique_sponsors,
            GROUP_CONCAT(DISTINCT t.overall_status)                            AS statuses,
            GROUP_CONCAT(DISTINCT te.biomarkers_required)                      AS all_biomarkers,
            GROUP_CONCAT(DISTINCT te.disease_stage)                            AS all_stages,
            GROUP_CONCAT(DISTINCT te.prior_treatment_required)                 AS all_prior_tx,
            GROUP_CONCAT(DISTINCT t.phase)                                     AS phases
        FROM trial_investigators ti
        JOIN trials t ON ti.nct_id = t.nct_id
        LEFT JOIN trial_sponsors ts ON ti.nct_id = ts.nct_id AND ts.is_lead = 1
        LEFT JOIN trial_eligibility te ON ti.nct_id = te.nct_id
        WHERE ti.nct_id IN ({placeholders})
          AND ti.investigator_name IS NOT NULL
        GROUP BY ti.investigator_name, ti.affiliation
        ORDER BY trials_as_pi DESC, phase3_count DESC, trials_total DESC
        LIMIT ?
    """, (*nct_ids, top_n * 3))  # Over-fetch to allow scoring trim

    rows = cur.fetchall()
    profiles = []
    for row in rows:
        profiles.append({
            "investigator_name":    row[0],
            "affiliation":          row[1],
            "kol_id":               row[2],
            "bridge_confidence":    row[3],
            "trials_total":         row[4] or 0,
            "trials_as_pi":         row[5] or 0,
            "phase3_count":         row[6] or 0,
            "phase2_count":         row[7] or 0,
            "industry_trials":      row[8] or 0,
            "active_trials":        row[9] or 0,
            "unique_sponsors":      row[10] or 0,
            "statuses":             row[11] or "",
            "all_biomarkers":       row[12] or "",
            "all_stages":           row[13] or "",
            "all_prior_tx":         row[14] or "",
            "phases":               row[15] or "",
            # KOL pathway fields — filled in next step
            "pub_count":            0,
            "avg_sjr":              0.0,
            "h_index":              None,
            "high_evidence":        0,
            "therapeutic_areas":    "",
        })
    return profiles


def enrich_from_kol_db(profiles: list[dict], kol_db: str) -> None:
    """
    For profiles with a kol_id, pull publication signals from meddash_kols.db.
    Modifies profiles in-place.
    """
    kol_ids = [p["kol_id"] for p in profiles if p["kol_id"]]
    if not kol_ids:
        return

    conn = sqlite3.connect(kol_db)
    cur  = conn.cursor()
    placeholders = ",".join("?" * len(kol_ids))

    cur.execute(f"""
        SELECT k.id, COUNT(DISTINCT ka.publication_id),
               AVG(COALESCE(jm.sjr, 0)),
               GROUP_CONCAT(DISTINCT ta.name)
        FROM kols k
        LEFT JOIN kol_authorships ka ON k.id = ka.kol_id
        LEFT JOIN publications p ON ka.publication_id = p.id
        LEFT JOIN journal_metrics jm ON LOWER(TRIM(p.journal_name)) = LOWER(TRIM(jm.journal_name))
        LEFT JOIN kol_therapeutic_areas kta ON k.id = kta.kol_id
        LEFT JOIN therapeutic_areas ta ON kta.therapeutic_area_id = ta.id
        WHERE k.id IN ({placeholders})
        GROUP BY k.id
    """, kol_ids)

    kol_data = {r[0]: r for r in cur.fetchall()}
    conn.close()

    kol_id_to_profile = {p["kol_id"]: p for p in profiles if p["kol_id"]}
    for kol_id, row in kol_data.items():
        if kol_id in kol_id_to_profile:
            prof = kol_id_to_profile[kol_id]
            prof["pub_count"]       = row[1] or 0
            prof["avg_sjr"]         = round(row[2] or 0.0, 2)
            prof["therapeutic_areas"] = row[3] or ""


# ── Scoring ────────────────────────────────────────────────────────────────────

def score_profile(profile: dict, query_terms: list[str]) -> float:
    """
    Compute composite 0–100 score.

    Trial Activity Score (50 pts):
        PI count on Phase 2/3                 20 pts (capped at 10 trials = 20pts)
        Industry-sponsored trials             15 pts (capped at 10 = 15pts)
        Active / recruiting trials            10 pts (capped at 5 = 10pts)
        Unique sponsors                        5 pts (capped at 5 = 5pts)

    Publication Signal Score (30 pts):
        Publication count                     15 pts (capped at 50 pubs = 15pts)
        Avg SJR                               10 pts (SJR ≥ 2.0 = 10pts)
        High-evidence flag                     5 pts

    Indication Specificity Score (20 pts):
        Biomarker match to query              12 pts
        Stage coverage                         8 pts
    """
    score = 0.0

    # ── Trial Activity (50 pts) ──────────────────────────────────────────
    pi_score = min(20, (profile["trials_as_pi"] + profile["phase3_count"]) * 2)
    industry_score = min(15, profile["industry_trials"] * 1.5)
    active_score   = min(10, profile["active_trials"] * 2)
    sponsor_score  = min(5,  profile["unique_sponsors"])
    score += pi_score + industry_score + active_score + sponsor_score

    # ── Publication Signal (30 pts) ──────────────────────────────────────
    pub_score = min(15, profile["pub_count"] * 0.3)
    sjr_score = min(10, profile["avg_sjr"] * 5)
    ev_score  = 5 if profile["high_evidence"] else 0
    score += pub_score + sjr_score + ev_score

    # ── Indication Specificity (20 pts) ──────────────────────────────────
    biomarkers_text = (profile["all_biomarkers"] or "").lower()
    stages_text     = (profile["all_stages"] or "").lower()

    bio_matches = sum(1 for t in query_terms if t in biomarkers_text)
    stage_matches = sum(1 for t in query_terms if t in stages_text)

    bio_spec  = min(12, bio_matches * 4)
    stage_spec = min(8, stage_matches * 4)
    score += bio_spec + stage_spec

    return round(score, 1)


# ── Report formatters ─────────────────────────────────────────────────────────

def format_markdown_brief(query: str, profiles: list[dict],
                          matched_trials: int, generated_at: str) -> str:
    """Generate human-readable Markdown KOL Intelligence Brief."""
    lines = [
        f"# KOL Intelligence Landscape Brief",
        f"**Indication:** {query}",
        f"**Generated:** {generated_at}",
        f"**Matching Trials:** {matched_trials:,}  |  "
        f"**KOLs Profiled:** {len(profiles)}",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        f"This brief profiles the top {len(profiles)} Key Opinion Leaders for "
        f"**{query}** based on their clinical trial activity and publication record. "
        f"Rankings are based on trial leadership (PI roles), Phase 3 participation, "
        f"industry engagement, and active trial count.",
        "",
        "## KOL Rankings",
        "",
    ]

    for rank, prof in enumerate(profiles, start=1):
        score   = prof.get("_score", 0)
        kol_tag = "🔗 KOL DB linked" if prof["kol_id"] else "⚪ Investigator (unlinked)"
        ev_tag  = "  ⭐ High-Evidence" if prof["high_evidence"] else ""

        lines += [
            f"### {rank}. {prof['investigator_name']}",
            f"**Score:** {score:.0f}/100  |  {kol_tag}{ev_tag}",
            f"**Institution:** {prof['affiliation'] or 'Not specified'}",
            "",
        ]

        # Trial activity table
        lines += [
            "| Metric | Value |",
            "|--------|-------|",
            f"| Total trials (this indication) | {prof['trials_total']} |",
            f"| As Principal Investigator      | {prof['trials_as_pi']} |",
            f"| Phase 3 trials                 | {prof['phase3_count']} |",
            f"| Phase 2 trials                 | {prof['phase2_count']} |",
            f"| Industry-sponsored             | {prof['industry_trials']} |",
            f"| Currently active/recruiting    | {prof['active_trials']} |",
            f"| Unique sponsors                | {prof['unique_sponsors']} |",
        ]

        if prof["pub_count"]:
            lines += [
                f"| Publications (KOL DB)         | {prof['pub_count']} |",
                f"| Avg journal SJR               | {prof['avg_sjr']:.2f} |",
            ]

        lines.append("")

        # Indication specificity
        if prof["all_biomarkers"]:
            bio_preview = ", ".join(list(set(
                b.strip() for b in prof["all_biomarkers"].split(",")
                if b.strip()
            ))[:5])
            lines.append(f"**Biomarkers / Populations:** {bio_preview}")

        if prof["all_stages"]:
            stage_set = list(set(s.strip() for s in prof["all_stages"].split(",") if s.strip()))
            lines.append(f"**Disease Stages:** {', '.join(stage_set[:3])}")

        if prof["all_prior_tx"]:
            ptx_set = list(set(p.strip() for p in prof["all_prior_tx"].split(",") if p.strip()))
            lines.append(f"**Prior Treatment Required:** {', '.join(ptx_set[:2])}")

        if prof["therapeutic_areas"]:
            lines.append(f"**Therapeutic Areas (PubMed):** {prof['therapeutic_areas'][:100]}")

        lines += ["", "---", ""]

    # Appendix
    lines += [
        "## Methodology Notes",
        "",
        "- **Trial Activity** scored from `ct_trials.db` via CT.gov API v2 (all historical trials)",
        "- **Publication Signal** scored from `meddash_kols.db` via PubMed (where KOL bridge matched)",
        "- **Indication Specificity** based on eligibility criteria biomarker extraction (regex + Qwen 2.5 7B)",
        "- KOL bridge match threshold: 0.70 (name fuzzy + institution + MeSH overlap)",
        "- `⚪ Investigator (unlinked)` = CT.gov investigator not yet matched to KOL DB",
        "  → Run `python ct_kol_bridge.py` after full crawl to increase match rate",
        "",
        f"*Generated by Meddash CT Engine v1.0 — {generated_at}*",
    ]

    return "\n".join(lines)


def format_json_brief(query: str, profiles: list[dict],
                      matched_trials: int, generated_at: str) -> dict:
    """Generate machine-readable JSON brief for Meddash SaaS API."""
    return {
        "meta": {
            "query":          query,
            "generated_at":   generated_at,
            "engine_version": "ct_engine_v1.0",
            "matched_trials": matched_trials,
            "kols_profiled":  len(profiles),
        },
        "kols": [
            {
                "rank":                    i + 1,
                "score":                   prof.get("_score", 0),
                "investigator_name":       prof["investigator_name"],
                "affiliation":             prof["affiliation"],
                "kol_id":                  prof["kol_id"],
                "bridge_confidence":       prof["bridge_confidence"],
                "trials_total":            prof["trials_total"],
                "trials_as_pi":            prof["trials_as_pi"],
                "phase3_count":            prof["phase3_count"],
                "phase2_count":            prof["phase2_count"],
                "industry_trials":         prof["industry_trials"],
                "active_trials":           prof["active_trials"],
                "unique_sponsors":         prof["unique_sponsors"],
                "pub_count":               prof["pub_count"],
                "avg_sjr":                 prof["avg_sjr"],
                "high_evidence":           bool(prof["high_evidence"]),
                "biomarkers_required":     prof["all_biomarkers"],
                "disease_stages":          prof["all_stages"],
                "prior_treatment":         prof["all_prior_tx"],
                "therapeutic_areas":       prof["therapeutic_areas"],
            }
            for i, prof in enumerate(profiles)
        ]
    }


# ── Main ───────────────────────────────────────────────────────────────────────

def generate_brief(query: str, top_n: int = 20,
                   ct_db: str = CT_DB, kol_db: str = KOL_DB,
                   out_dir: str = ".") -> tuple[str, str]:
    """
    Generate KOL Intelligence Brief for a given indication query.
    Returns (markdown_path, json_path).
    """
    ct_conn = sqlite3.connect(ct_db)
    query_terms = expand_query(query)

    print(f"  Query terms: {', '.join(query_terms[:8])}")

    # 1. Find matching trials
    nct_ids = find_matching_trials(ct_conn, query_terms)
    print(f"  Matching trials found: {len(nct_ids):,}")

    # 2. Fetch investigator profiles
    profiles = fetch_investigator_profiles(ct_conn, nct_ids, top_n)
    ct_conn.close()
    print(f"  Unique investigators profiled: {len(profiles):,}")

    # 3. Enrich with KOL DB signals
    enrich_from_kol_db(profiles, kol_db)

    # 4. Score and rank
    for prof in profiles:
        prof["_score"] = score_profile(prof, query_terms)

    profiles.sort(key=lambda p: p["_score"], reverse=True)
    profiles = profiles[:top_n]

    # 5. Generate outputs
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    slug = re.sub(r"[^\w]+", "_", query.lower()).strip("_")[:40]

    os.makedirs(out_dir, exist_ok=True)
    md_path   = os.path.join(out_dir, f"kol_brief_{slug}.md")
    json_path = os.path.join(out_dir, f"kol_brief_{slug}.json")

    md_content   = format_markdown_brief(query, profiles, len(nct_ids), generated_at)
    json_content = format_json_brief(query, profiles, len(nct_ids), generated_at)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_content, f, indent=2)

    return md_path, json_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Meddash KOL Intelligence Brief Generator"
    )
    parser.add_argument("--query",  required=True,
                        help="Indication/biomarker query (e.g. 'KRAS G12C lung cancer')")
    parser.add_argument("--top",    type=int, default=20,
                        help="Top N KOLs to include (default: 20)")
    parser.add_argument("--ct-db",  default=CT_DB)
    parser.add_argument("--kol-db", default=KOL_DB)
    parser.add_argument("--out",    default=".", help="Output directory")
    args = parser.parse_args()

    print(f"\n  Meddash — KOL Intelligence Brief Generator")
    print(f"  Query: \"{args.query}\"")
    print(f"  Top: {args.top} KOLs")
    print("  " + "─" * 56)

    md_path, json_path = generate_brief(
        args.query, args.top, args.ct_db, args.kol_db, args.out
    )

    print(f"\n  ✅ Brief generated!")
    print(f"  Markdown: {md_path}")
    print(f"  JSON:     {json_path}")
    print(f"\n  Open {md_path} to review the landscape brief.\n")


if __name__ == "__main__":
    main()
