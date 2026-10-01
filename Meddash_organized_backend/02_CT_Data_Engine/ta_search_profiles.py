"""
ta_search_profiles.py — Therapeutic Area Search Profiles for CT.gov API v2

Defines structured search profiles for targeted clinical trial queries.
Each profile specifies conditions, phases, statuses, sponsor class, date range,
and intervention keywords for precise CT.gov searches.

Usage:
    from ta_search_profiles import get_profile, list_profiles, build_query_params

    profile = get_profile("glp1_metabolic")
    params = build_query_params(profile)
    # → {'query.cond': 'GLP-1', 'filter.advanced': 'AREA[Phase]PHASE3 AND ...'}
"""

from datetime import datetime, timezone, timedelta
from typing import Optional


# ── Date Range Helper ─────────────────────────────────────────────────────

def resolve_date_range(range_str: str) -> tuple[str, str]:
    """Resolve a date range string to (start, end) in YYYY-MM-DD format.

    Supports:
    - 'last_7_days', 'last_30_days', 'last_90_days', 'last_180_days', 'last_365_days'
    - 'YYYY-MM-DD,YYYY-MM-DD' (explicit range)
    - '' or None (no date filter)
    """
    if not range_str:
        return "", ""

    now = datetime.now(timezone.utc)

    presets = {
        "last_7_days": 7,
        "last_30_days": 30,
        "last_90_days": 90,
        "last_180_days": 180,
        "last_365_days": 365,
    }

    if range_str in presets:
        start = (now - timedelta(days=presets[range_str])).strftime("%Y-%m-%d")
        end = now.strftime("%Y-%m-%d")
        return start, end

    # Explicit range
    if "," in range_str:
        parts = range_str.split(",")
        return parts[0].strip(), parts[1].strip()

    return "", ""


# ── TA Search Profiles ────────────────────────────────────────────────────

TA_SEARCH_PROFILES = {
    # ── Metabolic / GLP-1 ──
    "glp1_metabolic": {
        "label": "GLP-1 / Metabolic Disease",
        "conditions": ["GLP-1", "Glucagon-Like Peptide-1", "Semaglutide", "Tirzepatide", "Obesity", "Type 2 Diabetes"],
        "intervention_search": "",  # search by condition only
        "phase": ["PHASE3"],
        "status": ["RECRUITING", "ACTIVE_NOT_RECRUITING", "COMPLETED"],
        "sponsor_class": "",  # all sponsors
        "study_type": "INTERVENTIONAL",
        "date_range": "",  # no date filter — get all Phase 3 GLP-1 trials
        "max_results": 500,
    },

    # ── Oncology — NSCLC ──
    "nsclc_targeted": {
        "label": "NSCLC — Targeted Therapies",
        "conditions": ["Non-Small Cell Lung Cancer", "NSCLC", "EGFR", "KRAS", "ALK"],
        "intervention_search": "",
        "phase": ["PHASE2", "PHASE3"],
        "status": ["RECRUITING", "ACTIVE_NOT_RECRUITING"],
        "sponsor_class": "INDUSTRY",
        "study_type": "INTERVENTIONAL",
        "date_range": "last_90_days",
        "max_results": 500,
    },

    # ── Aesthetic Medicine — Botulinum Toxin ──
    "aesthetic_botox": {
        "label": "Aesthetic Medicine — Botulinum Toxin",
        "conditions": ["Botulinum Toxin", "Glabellar Lines", "Facial Wrinkles"],
        "intervention_search": "",
        "phase": [],  # all phases
        "status": ["COMPLETED", "RECRUITING"],
        "sponsor_class": "",
        "study_type": "INTERVENTIONAL",
        "date_range": "last_180_days",
        "max_results": 200,
    },

    # ── Aesthetic Medicine — Dermal Fillers ──
    "aesthetic_fillers": {
        "label": "Aesthetic Medicine — Dermal Fillers",
        "conditions": ["Hyaluronic Acid", "Dermal Fillers", "Nasolabial Fold"],
        "intervention_search": "",
        "phase": [],
        "status": ["COMPLETED", "RECRUITING"],
        "sponsor_class": "",
        "study_type": "INTERVENTIONAL",
        "date_range": "last_180_days",
        "max_results": 200,
    },

    # ── Aesthetic Medicine — Laser/Energy ──
    "aesthetic_laser": {
        "label": "Aesthetic Medicine — Laser & Energy-Based Devices",
        "conditions": ["Laser Resurfacing", "Radiofrequency", "Intense Pulsed Light"],
        "intervention_search": "",
        "phase": [],
        "status": ["COMPLETED", "RECRUITING"],
        "sponsor_class": "",
        "study_type": "INTERVENTIONAL",
        "date_range": "last_180_days",
        "max_results": 200,
    },

    # ── Aesthetic Medicine — Microneedling/PRP ──
    "aesthetic_microneedling": {
        "label": "Aesthetic Medicine — Microneedling & PRP",
        "conditions": ["Microneedling", "Platelet-Rich Plasma"],
        "intervention_search": "",
        "phase": [],
        "status": ["COMPLETED", "RECRUITING"],
        "sponsor_class": "",
        "study_type": "INTERVENTIONAL",
        "date_range": "last_180_days",
        "max_results": 200,
    },

    # ── Aesthetic Medicine — Skin Aging ──
    "aesthetic_skin_aging": {
        "label": "Aesthetic Medicine — Skin Aging & Photoaging",
        "conditions": ["Skin Aging", "Photoaging", "Wrinkles"],
        "intervention_search": "",
        "phase": [],
        "status": ["COMPLETED", "RECRUITING"],
        "sponsor_class": "",
        "study_type": "INTERVENTIONAL",
        "date_range": "last_180_days",
        "max_results": 200,
    },

    # ── Aesthetic Medicine — Pigmentation ──
    "aesthetic_pigmentation": {
        "label": "Aesthetic Medicine — Pigmentation & Rosacea",
        "conditions": ["Melasma", "Rosacea"],
        "intervention_search": "",
        "phase": [],
        "status": ["COMPLETED", "RECRUITING"],
        "sponsor_class": "",
        "study_type": "INTERVENTIONAL",
        "date_range": "last_180_days",
        "max_results": 200,
    },

    # ── Custom / Ad-hoc (for natural language search) ──
    "_custom": {
        "label": "Custom Search",
        "conditions": [],
        "intervention_search": "",
        "phase": [],
        "status": [],
        "sponsor_class": "",
        "study_type": "",
        "date_range": "",
        "max_results": 500,
    },
}


# ── Profile Access ─────────────────────────────────────────────────────────

def get_profile(name: str) -> dict:
    """Get a TA search profile by name."""
    if name not in TA_SEARCH_PROFILES:
        raise ValueError(f"Unknown profile: '{name}'. Available: {list(TA_SEARCH_PROFILES.keys())}")
    return TA_SEARCH_PROFILES[name]


def list_profiles() -> list[dict]:
    """List all available profiles with their labels."""
    return [
        {"name": k, "label": v["label"], "conditions": v["conditions"]}
        for k, v in TA_SEARCH_PROFILES.items()
    ]


def build_advanced_filter(profile: dict) -> str:
    """Build the filter.advanced AREA string from a profile.

    Combines phase, status, study type, sponsor class, and date range
    using AND/OR boolean operators per CT.gov API v2 syntax.
    """
    parts = []

    # Phase (OR within phases, AND with everything else)
    if profile.get("phase"):
        phase_str = " OR ".join([f"AREA[Phase]{p}" for p in profile["phase"]])
        if len(profile["phase"]) > 1:
            parts.append(f"({phase_str})")
        else:
            parts.append(phase_str)

    # Status (OR within statuses)
    if profile.get("status"):
        status_str = " OR ".join([f"AREA[OverallStatus]{s}" for s in profile["status"]])
        if len(profile["status"]) > 1:
            parts.append(f"({status_str})")
        else:
            parts.append(status_str)

    # Study type
    if profile.get("study_type"):
        parts.append(f"AREA[StudyType]{profile['study_type']}")

    # Sponsor class
    if profile.get("sponsor_class"):
        parts.append(f"AREA[LeadSponsorClass]{profile['sponsor_class']}")

    # Date range
    if profile.get("date_range"):
        start, end = resolve_date_range(profile["date_range"])
        if start and end:
            parts.append(f"AREA[LastUpdatePostDate]RANGE[{start},{end}]")

    return " AND ".join(parts)


def build_query_params(profile: dict, condition_override: str = None) -> dict:
    """Build CT.gov API v2 query parameters from a profile.

    Args:
        profile: TA search profile dict
        condition_override: Override the condition (for custom searches)

    Returns:
        Dict of query parameters for CT.gov API v2
    """
    condition = condition_override or profile["conditions"][0] if profile["conditions"] else ""
    adv_filter = build_advanced_filter(profile)

    params = {
        "query.cond": condition,
        "pageSize": str(profile.get("max_results", 500)),
        "countTotal": "true",
        "format": "json",
    }

    if adv_filter:
        params["filter.advanced"] = adv_filter

    return params


def build_custom_params(
    condition: str,
    phase: list[str] = None,
    status: list[str] = None,
    sponsor_class: str = "",
    study_type: str = "",
    date_range: str = "",
    intervention: str = "",
    max_results: int = 500,
) -> dict:
    """Build query params for a custom/ad-hoc search.

    This is the entry point for natural language search triggered by Meddash Manager.
    """
    profile = TA_SEARCH_PROFILES["_custom"].copy()
    profile["conditions"] = [condition]
    profile["phase"] = phase or []
    profile["status"] = status or []
    profile["sponsor_class"] = sponsor_class
    profile["study_type"] = study_type
    profile["date_range"] = date_range
    profile["intervention_search"] = intervention
    profile["max_results"] = max_results

    return build_query_params(profile, condition_override=condition)


# ── CLI ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="TA Search Profiles")
    parser.add_argument("--list", action="store_true", help="List all profiles")
    parser.add_argument("--show", type=str, help="Show a specific profile")
    parser.add_argument("--dry-run", type=str, help="Show query params for a profile")
    args = parser.parse_args()

    if args.list:
        print("Available TA Search Profiles:")
        for p in list_profiles():
            if p["name"] == "_custom":
                continue
            print(f"  {p['name']:30s} — {p['label']}")
            if p["conditions"]:
                print(f"    Conditions: {', '.join(p['conditions'][:3])}")

    if args.show:
        profile = get_profile(args.show)
        print(json.dumps(profile, indent=2))

    if args.dry_run:
        profile = get_profile(args.dry_run)
        params = build_query_params(profile)
        print(f"\nProfile: {profile['label']}")
        print(f"Query params:")
        for k, v in params.items():
            print(f"  {k}: {v}")