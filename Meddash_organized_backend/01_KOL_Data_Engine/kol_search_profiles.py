"""
kol_search_profiles.py — Therapeutic Area Search Profiles for PubMed E-utilities

Defines structured search profiles for targeted PubMed publication queries.
Each profile specifies conditions, MeSH terms, publication types, date range,
and max results — enabling granular KOL discovery like the CT Query Engine.

Usage:
    from kol_search_profiles import get_profile, list_profiles, build_pubmed_query

    profile = get_profile("glp1_metabolic")
    query = build_pubmed_query(profile)
    # → '"GLP-1"[MH] AND ("Randomized Controlled Trial"[PT]) AND ("2025/01/01"[DP] : "2025/12/31"[DP]) AND medline[sb]'
"""

from datetime import datetime, timezone, timedelta
from typing import Optional


# ── Date Range Helper ─────────────────────────────────────────────────────

def resolve_date_range(range_str: str) -> tuple[str, str]:
    """Resolve a date range string to (start, end) in YYYY/MM/DD format (PubMed style).

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
        start = (now - timedelta(days=presets[range_str])).strftime("%Y/%m/%d")
        end = now.strftime("%Y/%m/%d")
        return start, end

    # Explicit range — convert YYYY-MM-DD to YYYY/MM/DD
    if "," in range_str:
        parts = range_str.split(",")
        start = parts[0].strip().replace("-", "/")
        end = parts[1].strip().replace("-", "/")
        return start, end

    return "", ""


# ── Publication Type Filters ──────────────────────────────────────────────

PUB_TYPES = {
    "rct": "Randomized Controlled Trial",
    "meta_analysis": "Meta-Analysis",
    "systematic_review": "Systematic Review",
    "clinical_trial": "Clinical Trial",
    "review": "Review",
    "case_report": "Case Reports",
    "observational": "Observational Study",
    "comparative": "Comparative Study",
    "validation": "Validation Study",
}


# ── KOL Search Profiles ───────────────────────────────────────────────────

KOL_SEARCH_PROFILES = {
    # ── Metabolic / GLP-1 ──
    "glp1_metabolic": {
        "label": "GLP-1 / Metabolic Disease",
        "conditions": ["GLP-1", "Glucagon-Like Peptide-1", "Semaglutide", "Tirzepatide"],
        "mesh_terms": ["Glucagon-Like Peptide-1", "Incretins", "Obesity", "Diabetes Mellitus, Type 2"],
        "publication_types": ["rct", "meta_analysis", "clinical_trial"],
        "date_range": "last_90_days",
        "max_results": 50,
        "sort": "date",
        "language": "English",
    },

    # ── Oncology — NSCLC ──
    "nsclc_targeted": {
        "label": "NSCLC — Targeted Therapies",
        "conditions": ["Non-Small Cell Lung Cancer", "NSCLC", "EGFR", "KRAS", "ALK"],
        "mesh_terms": ["Carcinoma, Non-Small-Cell Lung", "Lung Neoplasms", "Protein Kinase Inhibitors"],
        "publication_types": ["rct", "meta_analysis", "clinical_trial"],
        "date_range": "last_90_days",
        "max_results": 50,
        "sort": "date",
        "language": "English",
    },

    # ── Aesthetic Medicine — Botulinum Toxin ──
    "aesthetic_botox": {
        "label": "Aesthetic Medicine — Botulinum Toxin",
        "conditions": ["Botulinum Toxin Type A", "cosmetic"],
        "mesh_terms": ["Botulinum Toxins, Type A", "Cosmetic Techniques"],
        "publication_types": ["rct", "clinical_trial", "comparative"],
        "date_range": "last_180_days",
        "max_results": 30,
        "sort": "date",
        "language": "English",
    },

    # ── Aesthetic Medicine — Dermal Fillers ──
    "aesthetic_fillers": {
        "label": "Aesthetic Medicine — Dermal Fillers",
        "conditions": ["Dermal Fillers", "Hyaluronic Acid", "face"],
        "mesh_terms": ["Hyaluronic Acid", "Cosmetic Techniques", "Injections, Intradermal"],
        "publication_types": ["rct", "clinical_trial", "comparative"],
        "date_range": "last_180_days",
        "max_results": 30,
        "sort": "date",
        "language": "English",
    },

    # ── Aesthetic Medicine — Laser/Energy ──
    "aesthetic_laser": {
        "label": "Aesthetic Medicine — Laser & Energy-Based Devices",
        "conditions": ["Laser Resurfacing", "Radiofrequency", "Intense Pulsed Light", "skin"],
        "mesh_terms": ["Laser Therapy", "Radiofrequency Therapy", "Skin"],
        "publication_types": ["rct", "clinical_trial", "comparative"],
        "date_range": "last_180_days",
        "max_results": 30,
        "sort": "date",
        "language": "English",
    },

    # ── Aesthetic Medicine — Microneedling/PRP ──
    "aesthetic_microneedling": {
        "label": "Aesthetic Medicine — Microneedling & PRP",
        "conditions": ["Microneedling", "Platelet-Rich Plasma", "skin"],
        "mesh_terms": ["Platelet-Rich Plasma", "Skin", "Wound Healing"],
        "publication_types": ["rct", "clinical_trial", "comparative"],
        "date_range": "last_180_days",
        "max_results": 30,
        "sort": "date",
        "language": "English",
    },

    # ── Aesthetic Medicine — Skin Aging ──
    "aesthetic_skin_aging": {
        "label": "Aesthetic Medicine — Skin Aging & Photoaging",
        "conditions": ["Skin Aging", "Photoaging", "treatment"],
        "mesh_terms": ["Skin Aging", "Sunburn", "Wrinkles"],
        "publication_types": ["rct", "clinical_trial", "review"],
        "date_range": "last_180_days",
        "max_results": 30,
        "sort": "date",
        "language": "English",
    },

    # ── Aesthetic Medicine — Pigmentation ──
    "aesthetic_pigmentation": {
        "label": "Aesthetic Medicine — Pigmentation & Rosacea",
        "conditions": ["Melasma", "Rosacea", "treatment"],
        "mesh_terms": ["Melasma", "Rosacea", "Skin Pigmentation"],
        "publication_types": ["rct", "clinical_trial", "comparative"],
        "date_range": "last_180_days",
        "max_results": 30,
        "sort": "date",
        "language": "English",
    },

    # ── Custom / Ad-hoc (for natural language search) ──
    "_custom": {
        "label": "Custom PubMed Search",
        "conditions": [],
        "mesh_terms": [],
        "publication_types": [],
        "date_range": "",
        "max_results": 50,
        "sort": "date",
        "language": "English",
    },
}


# ── Profile Access ─────────────────────────────────────────────────────────

def get_profile(name: str) -> dict:
    """Get a KOL search profile by name."""
    if name not in KOL_SEARCH_PROFILES:
        raise ValueError(f"Unknown profile: '{name}'. Available: {list(KOL_SEARCH_PROFILES.keys())}")
    return KOL_SEARCH_PROFILES[name]


def list_profiles() -> list[dict]:
    """List all available profiles with their labels."""
    return [
        {"name": k, "label": v["label"], "conditions": v["conditions"]}
        for k, v in KOL_SEARCH_PROFILES.items()
    ]


def build_pubmed_query(profile: dict, condition_override: str = None) -> str:
    """Build a PubMed E-utilities search term string from a profile.

    Combines conditions, MeSH terms, publication types, date range, and language
    using PubMed boolean syntax with field tags.

    Args:
        profile: KOL search profile dict
        condition_override: Override the condition (for custom searches)

    Returns:
        PubMed search term string for Entrez.esearch(term=...)
    """
    parts = []

    # Condition (primary search term)
    condition = condition_override or (profile["conditions"][0] if profile["conditions"] else "")
    if condition:
        # Use condition as a title/abstract search
        parts.append(f'"{condition}"[TIAB]')

    # MeSH terms (OR within MeSH, AND with everything else)
    mesh_terms = profile.get("mesh_terms", [])
    if mesh_terms and not condition_override:
        mesh_parts = [f'"{m}"[MH]' for m in mesh_terms]
        if len(mesh_parts) > 1:
            parts.append(f'({" OR ".join(mesh_parts)})')
        else:
            parts.append(mesh_parts[0])

    # Publication types (OR within types)
    pub_types = profile.get("publication_types", [])
    if pub_types:
        type_parts = [f'"{PUB_TYPES.get(pt, pt)}"[PT]' for pt in pub_types]
        if len(type_parts) > 1:
            parts.append(f'({" OR ".join(type_parts)})')
        else:
            parts.append(type_parts[0])

    # Date range
    date_range = profile.get("date_range", "")
    if date_range:
        start, end = resolve_date_range(date_range)
        if start and end:
            parts.append(f'("{start}"[DP] : "{end}"[DP])')

    # Language
    lang = profile.get("language", "")
    if lang:
        parts.append(f'{lang}[LA]')

    # Always include medline subset
    parts.append("medline[sb]")

    return " AND ".join(parts)


def build_custom_query(
    condition: str,
    mesh_terms: list[str] = None,
    pub_types: list[str] = None,
    date_range: str = "",
    language: str = "English",
    max_results: int = 50,
    sort: str = "date",
) -> dict:
    """Build query params for a custom/ad-hoc PubMed search.

    Entry point for natural language search triggered by Meddash Manager.
    """
    profile = KOL_SEARCH_PROFILES["_custom"].copy()
    profile["conditions"] = [condition]
    profile["mesh_terms"] = mesh_terms or []
    profile["publication_types"] = pub_types or []
    profile["date_range"] = date_range
    profile["language"] = language
    profile["max_results"] = max_results
    profile["sort"] = sort

    query = build_pubmed_query(profile, condition_override=condition)

    return {
        "query": query,
        "max_results": max_results,
        "sort": sort,
        "profile": profile,
    }


# ── CLI ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="KOL Search Profiles for PubMed")
    parser.add_argument("--list", action="store_true", help="List all profiles")
    parser.add_argument("--show", type=str, help="Show a specific profile")
    parser.add_argument("--dry-run", type=str, help="Show PubMed query for a profile")
    args = parser.parse_args()

    if args.list:
        print("Available KOL Search Profiles:")
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
        query = build_pubmed_query(profile)
        print(f"\nProfile: {profile['label']}")
        print(f"PubMed query: {query}")
        print(f"Max results: {profile['max_results']}")
        print(f"Sort: {profile['sort']}")