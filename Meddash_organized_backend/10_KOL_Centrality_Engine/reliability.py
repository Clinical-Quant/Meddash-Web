"""Reliability and limitation annotations for centrality scores."""


def _band(score):
    if score >= 80:
        return "high"
    if score >= 60:
        return "moderate"
    if score >= 40:
        return "low"
    return "very_low"


def calculate_reliability(row, graph_stats=None, duplicate_warning=False, eigenvector_available=True):
    graph_stats = graph_stats or {}
    pubs = int(row.get("publication_count_mapped", 0) or 0)
    coauthors = int(row.get("coauthor_count_mapped", 0) or 0)
    component_size = int(row.get("component_size", 1) or 1)
    node_count = max(int(graph_stats.get("node_count", 1) or 1), 1)

    publication_factor = min(1.0, pubs / 5.0)
    coauthor_factor = min(1.0, coauthors / 5.0)
    component_factor = min(1.0, component_size / max(10.0, node_count * 0.02))
    metadata_factor = 1.0  # v1 has no per-row metadata penalty yet; reserved for future MeSH/journal coverage.
    disambig_factor = 0.65 if duplicate_warning else 1.0
    eigen_factor = 1.0 if eigenvector_available else 0.9

    score = round(100.0 * (
        0.30 * publication_factor +
        0.30 * coauthor_factor +
        0.20 * component_factor +
        0.10 * metadata_factor +
        0.10 * disambig_factor
    ) * eigen_factor, 2)

    limitations = []
    missing = []
    if pubs < 2:
        limitations.append("Incomplete mapped publication network: fewer than 2 mapped publications for this KOL.")
        missing.append("additional_publications")
    if coauthors < 1:
        limitations.append("Few or no mapped coauthors; score may understate a real-world central KOL if their network has not been pulled.")
        missing.append("mapped_coauthors")
    if component_size < 3:
        limitations.append("Small/disconnected graph component; centrality is calculated only within currently mapped data.")
        missing.append("larger_component_mapping")
    if duplicate_warning:
        limitations.append("Possible duplicate/merge candidate exists; centrality may be split across records.")
        missing.append("duplicate_resolution")
    if not eigenvector_available:
        limitations.append("Eigenvector centrality was unstable; fallback score formula was used.")
        missing.append("stable_eigenvector")
    if not limitations:
        limitations.append("No major v1 data limitations detected; still limited to mapped authorship data, not total real-world influence.")

    return {
        "reliability_score": score,
        "reliability_band": _band(score),
        "limitations": limitations,
        "missing_inputs": missing,
        "data_coverage_summary": f"{pubs} mapped publications, {coauthors} mapped coauthors, component size {component_size}.",
    }


def apply_reliability(rows, graph_stats=None, duplicate_kol_ids=None, eigenvector_available=True):
    duplicate_kol_ids = duplicate_kol_ids or set()
    enriched = []
    for row in rows:
        rel = calculate_reliability(
            row,
            graph_stats=graph_stats,
            duplicate_warning=row.get("kol_id") in duplicate_kol_ids,
            eigenvector_available=eigenvector_available,
        )
        enriched.append({**row, **rel})
    return enriched
