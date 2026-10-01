"""
biocrawler_search_profiles.py — TA Search Profiles for BioCrawler

Defines structured search profiles for biotech company intelligence.
Each profile specifies CT.gov conditions (for sponsor extraction) + SEC EDGAR
SIC codes and filing types (for financial enrichment).

BioCrawler is LEAN: CT.gov sponsor extraction + SEC EDGAR only.
No hiring signals, no CRM, no website enrichment (decoupled in SEQ-0023).

Usage:
    from biocrawler_search_profiles import get_profile, list_profiles, build_ctgov_params, build_edgar_params

    profile = get_profile("glp1_metabolic")
    ct_params = build_ctgov_params(profile)
    edgar_params = build_edgar_params(profile)
"""

from datetime import datetime, timezone, timedelta
from typing import Optional


# ── Date Range Helper ─────────────────────────────────────────────────────

def resolve_date_range(range_str: str) -> tuple[str, str]:
    """Resolve date range to (start, end) in YYYY-MM-DD format."""
    if not range_str:
        return "", ""

    now = datetime.now(timezone.utc)
    presets = {
        "last_7_days": 7, "last_30_days": 30, "last_90_days": 90,
        "last_180_days": 180, "last_365_days": 365,
    }

    if range_str in presets:
        start = (now - timedelta(days=presets[range_str])).strftime("%Y-%m-%d")
        end = now.strftime("%Y-%m-%d")
        return start, end

    if "," in range_str:
        parts = range_str.split(",")
        return parts[0].strip(), parts[1].strip()

    return "", ""


# ── SEC EDGAR SIC Codes (biotech-relevant) ────────────────────────────────

SIC_CODES = {
    "biological_products": "2834",
    "pharmaceutical_preparations": "2834",
    "in_vitro_diagnostic_substances": "2835",
    "pharma_diagnostics": "2835",
    "biotech_laboratory": "3841",
    "surgical_medical_instruments": "3841",
    "dental_equipment": "3843",
    "electromedical_equipment": "3845",
    "health_services": "8000",
    "offices_clinics_medical": "8011",
}


# ── BioCrawler Search Profiles ────────────────────────────────────────────

BIOCRAWLER_SEARCH_PROFILES = {
    # ── Metabolic / GLP-1 ──
    "glp1_metabolic": {
        "label": "GLP-1 / Metabolic Disease — Company Intelligence",
        "ctgov_conditions": ["GLP-1", "Glucagon-Like Peptide-1", "Obesity", "Type 2 Diabetes", "Semaglutide", "Tirzepatide"],
        "ctgov_phase": ["PHASE2", "PHASE3"],
        "ctgov_status": ["RECRUITING", "ACTIVE_NOT_RECRUITING", "COMPLETED"],
        "ctgov_study_type": "INTERVENTIONAL",
        "ctgov_sponsor_class": "INDUSTRY",
        "ctgov_date_range": "last_90_days",
        "edgar_sic_codes": ["2834", "2835"],
        "edgar_filing_types": ["8-K", "10-K", "10-Q"],
        "edgar_date_range": "last_365_days",
        "edgar_fulltext_query": '"clinical trial" "GLP-1"',
        "max_results": 200,
    },

    # ── Oncology — NSCLC ──
    "nsclc_targeted": {
        "label": "NSCLC — Targeted Therapies Company Intelligence",
        "ctgov_conditions": ["Non-Small Cell Lung Cancer", "NSCLC", "EGFR", "KRAS", "ALK"],
        "ctgov_phase": ["PHASE2", "PHASE3"],
        "ctgov_status": ["RECRUITING", "ACTIVE_NOT_RECRUITING"],
        "ctgov_study_type": "INTERVENTIONAL",
        "ctgov_sponsor_class": "INDUSTRY",
        "ctgov_date_range": "last_90_days",
        "edgar_sic_codes": ["2834", "2835"],
        "edgar_filing_types": ["8-K", "10-K", "10-Q"],
        "edgar_date_range": "last_365_days",
        "edgar_fulltext_query": '"clinical trial" "lung cancer"',
        "max_results": 200,
    },

    # ── Aesthetic Medicine — All ──
    "aesthetic_all": {
        "label": "Aesthetic Medicine — Company Intelligence",
        "ctgov_conditions": ["Botulinum Toxin", "Hyaluronic Acid", "Laser Resurfacing", "Microneedling", "Dermal Fillers"],
        "ctgov_phase": [],
        "ctgov_status": ["COMPLETED", "RECRUITING"],
        "ctgov_study_type": "INTERVENTIONAL",
        "ctgov_sponsor_class": "",
        "ctgov_date_range": "last_180_days",
        "edgar_sic_codes": ["2834", "3841"],
        "edgar_filing_types": ["8-K", "10-K"],
        "edgar_date_range": "last_365_days",
        "edgar_fulltext_query": '"aesthetic" "cosmetic"',
        "max_results": 100,
    },

    # ── Immunology ──
    "immunology": {
        "label": "Immunology — Company Intelligence",
        "ctgov_conditions": ["Rheumatoid Arthritis", "Lupus", "Psoriasis", "Inflammatory Bowel Disease", "Asthma"],
        "ctgov_phase": ["PHASE2", "PHASE3"],
        "ctgov_status": ["RECRUITING", "ACTIVE_NOT_RECRUITING"],
        "ctgov_study_type": "INTERVENTIONAL",
        "ctgov_sponsor_class": "INDUSTRY",
        "ctgov_date_range": "last_90_days",
        "edgar_sic_codes": ["2834", "2835"],
        "edgar_filing_types": ["8-K", "10-K", "10-Q"],
        "edgar_date_range": "last_365_days",
        "edgar_fulltext_query": '"clinical trial" "immunology"',
        "max_results": 200,
    },

    # ── Neurology ──
    "neurology": {
        "label": "Neurology — Company Intelligence",
        "ctgov_conditions": ["Alzheimer Disease", "Parkinson Disease", "Multiple Sclerosis", "Epilepsy"],
        "ctgov_phase": ["PHASE2", "PHASE3"],
        "ctgov_status": ["RECRUITING", "ACTIVE_NOT_RECRUITING"],
        "ctgov_study_type": "INTERVENTIONAL",
        "ctgov_sponsor_class": "INDUSTRY",
        "ctgov_date_range": "last_90_days",
        "edgar_sic_codes": ["2834", "2835"],
        "edgar_filing_types": ["8-K", "10-K", "10-Q"],
        "edgar_date_range": "last_365_days",
        "edgar_fulltext_query": '"clinical trial" "neurology"',
        "max_results": 200,
    },

    # ── Custom ──
    "_custom": {
        "label": "Custom BioCrawler Search",
        "ctgov_conditions": [],
        "ctgov_phase": [],
        "ctgov_status": [],
        "ctgov_study_type": "",
        "ctgov_sponsor_class": "",
        "ctgov_date_range": "",
        "edgar_sic_codes": [],
        "edgar_filing_types": [],
        "edgar_date_range": "",
        "edgar_fulltext_query": "",
        "max_results": 200,
    },
}


# ── Profile Access ─────────────────────────────────────────────────────────

def get_profile(name: str) -> dict:
    if name not in BIOCRAWLER_SEARCH_PROFILES:
        raise ValueError(f"Unknown profile: '{name}'. Available: {list(BIOCRAWLER_SEARCH_PROFILES.keys())}")
    return BIOCRAWLER_SEARCH_PROFILES[name]


def list_profiles() -> list[dict]:
    return [
        {"name": k, "label": v["label"], "conditions": v["ctgov_conditions"]}
        for k, v in BIOCRAWLER_SEARCH_PROFILES.items()
    ]


def build_ctgov_advanced_filter(profile: dict) -> str:
    """Build filter.advanced AREA string for CT.gov sponsor search."""
    parts = []

    if profile.get("ctgov_phase"):
        phase_str = " OR ".join([f"AREA[Phase]{p}" for p in profile["ctgov_phase"]])
        parts.append(f"({phase_str})" if len(profile["ctgov_phase"]) > 1 else phase_str)

    if profile.get("ctgov_status"):
        status_str = " OR ".join([f"AREA[OverallStatus]{s}" for s in profile["ctgov_status"]])
        parts.append(f"({status_str})" if len(profile["ctgov_status"]) > 1 else status_str)

    if profile.get("ctgov_study_type"):
        parts.append(f"AREA[StudyType]{profile['ctgov_study_type']}")

    if profile.get("ctgov_sponsor_class"):
        parts.append(f"AREA[LeadSponsorClass]{profile['ctgov_sponsor_class']}")

    if profile.get("ctgov_date_range"):
        start, end = resolve_date_range(profile["ctgov_date_range"])
        if start and end:
            parts.append(f"AREA[LastUpdatePostDate]RANGE[{start},{end}]")

    return " AND ".join(parts)


def build_ctgov_params(profile: dict, condition_override: str = None) -> dict:
    """Build CT.gov API v2 query parameters for sponsor extraction."""
    condition = condition_override or (profile["ctgov_conditions"][0] if profile["ctgov_conditions"] else "")
    adv_filter = build_ctgov_advanced_filter(profile)

    params = {
        "query.cond": condition,
        "pageSize": str(profile.get("max_results", 200)),
        "countTotal": "true",
        "format": "json",
    }

    if adv_filter:
        params["filter.advanced"] = adv_filter

    return params


def build_edgar_params(profile: dict) -> dict:
    """Build SEC EDGAR full-text search parameters."""
    start, end = resolve_date_range(profile.get("edgar_date_range", ""))

    params = {
        "q": profile.get("edgar_fulltext_query", ""),
        "forms": ",".join(profile.get("edgar_filing_types", [])),
        "dateRange": "custom" if start else "",
    }

    if start:
        params["startdt"] = start
    if end:
        params["enddt"] = end

    return params


def build_custom_params(
    condition: str,
    phase: list[str] = None,
    status: list[str] = None,
    sponsor_class: str = "INDUSTRY",
    study_type: str = "INTERVENTIONAL",
    ctgov_date_range: str = "last_90_days",
    edgar_sic_codes: list[str] = None,
    edgar_filing_types: list[str] = None,
    edgar_date_range: str = "last_365_days",
    edgar_fulltext_query: str = "",
    max_results: int = 200,
) -> dict:
    """Build params for custom ad-hoc BioCrawler search."""
    profile = BIOCRAWLER_SEARCH_PROFILES["_custom"].copy()
    profile["ctgov_conditions"] = [condition]
    profile["ctgov_phase"] = phase or []
    profile["ctgov_status"] = status or []
    profile["ctgov_sponsor_class"] = sponsor_class
    profile["ctgov_study_type"] = study_type
    profile["ctgov_date_range"] = ctgov_date_range
    profile["edgar_sic_codes"] = edgar_sic_codes or ["2834", "2835"]
    profile["edgar_filing_types"] = edgar_filing_types or ["8-K", "10-K"]
    profile["edgar_date_range"] = edgar_date_range
    profile["edgar_fulltext_query"] = edgar_fulltext_query or f'"clinical trial" "{condition}"'
    profile["max_results"] = max_results

    return {
        "ctgov": build_ctgov_params(profile, condition_override=condition),
        "edgar": build_edgar_params(profile),
        "profile": profile,
    }


# ── CLI ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse, json

    parser = argparse.ArgumentParser(description="BioCrawler Search Profiles")
    parser.add_argument("--list", action="store_true", help="List all profiles")
    parser.add_argument("--show", type=str, help="Show a specific profile")
    parser.add_argument("--dry-run", type=str, help="Show query params for a profile")
    args = parser.parse_args()

    if args.list:
        print("Available BioCrawler Search Profiles:")
        for p in list_profiles():
            if p["name"] == "_custom":
                continue
            print(f"  {p['name']:30s} — {p['label']}")

    if args.show:
        profile = get_profile(args.show)
        print(json.dumps(profile, indent=2))

    if args.dry_run:
        profile = get_profile(args.dry_run)
        ct_params = build_ctgov_params(profile)
        edgar_params = build_edgar_params(profile)
        print(f"\nProfile: {profile['label']}")
        print(f"\nCT.gov params:")
        for k, v in ct_params.items():
            print(f"  {k}: {v}")
        print(f"\nSEC EDGAR params:")
        for k, v in edgar_params.items():
            print(f"  {k}: {v}")