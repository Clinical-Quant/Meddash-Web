"""Scoring and tiering for authorship centrality."""
try:
    from .centrality_config import SCORE_WEIGHTS, FALLBACK_SCORE_WEIGHTS, TIER_CUTOFFS, DEFAULT_THRESHOLDS
except ImportError:
    from centrality_config import SCORE_WEIGHTS, FALLBACK_SCORE_WEIGHTS, TIER_CUTOFFS, DEFAULT_THRESHOLDS


def percentile_map(values):
    if not values:
        return {}
    sorted_items = sorted(values.items(), key=lambda kv: (kv[1], kv[0]))
    n = len(sorted_items)
    if n == 1:
        return {sorted_items[0][0]: 100.0}
    result = {}
    for rank, (key, value) in enumerate(sorted_items, start=1):
        result[key] = round(100.0 * (rank - 1) / (n - 1), 4)
    return result


def assign_tier(score, insufficient=False):
    if insufficient:
        return "Insufficient Data"
    for cutoff, label in TIER_CUTOFFS:
        if score >= cutoff:
            return label
    return "Insufficient Data"


def score_nodes(metrics_by_node, node_stats, eigenvector_available=True, thresholds=None):
    thresholds = thresholds or DEFAULT_THRESHOLDS
    metric_keys = ["weighted_degree", "pagerank", "betweenness", "eigenvector", "component_size"]
    percentiles = {}
    for key in metric_keys:
        percentiles[key] = percentile_map({node: vals.get(key, 0.0) for node, vals in metrics_by_node.items()})
    weights = SCORE_WEIGHTS if eigenvector_available else FALLBACK_SCORE_WEIGHTS
    rows = []
    for node, vals in metrics_by_node.items():
        stats = node_stats.get(node, {})
        pubs = int(stats.get("publication_count_mapped", 0) or 0)
        coauthors = int(stats.get("coauthor_count_mapped", 0) or 0)
        insufficient = pubs < thresholds.get("min_publications", 2) or coauthors < thresholds.get("min_coauthors", 1)
        score_parts = {
            "weighted_degree_percentile": percentiles["weighted_degree"].get(node, 0.0),
            "pagerank_percentile": percentiles["pagerank"].get(node, 0.0),
            "betweenness_percentile": percentiles["betweenness"].get(node, 0.0),
            "eigenvector_percentile": percentiles["eigenvector"].get(node, 0.0) if eigenvector_available else None,
            "component_size_percentile": percentiles["component_size"].get(node, 0.0),
        }
        raw = 0.0
        for key, weight in weights.items():
            raw += (score_parts.get(key) or 0.0) * weight
        score = 0.0 if insufficient else max(0.0, min(100.0, round(raw, 2)))
        row = {
            "kol_id": int(node),
            "degree_centrality": vals.get("degree_centrality", 0.0),
            "weighted_degree": vals.get("weighted_degree", 0.0),
            "pagerank": vals.get("pagerank", 0.0),
            "betweenness": vals.get("betweenness", 0.0),
            "eigenvector": vals.get("eigenvector", 0.0) if eigenvector_available else None,
            "component_id": vals.get("component_id"),
            "component_size": vals.get("component_size", 1),
            "publication_count_mapped": pubs,
            "coauthor_count_mapped": coauthors,
            "authorship_centrality_raw": round(raw, 4),
            "authorship_centrality_percentile": score,
            "authorship_centrality_score": score,
            "authorship_centrality_tier": assign_tier(score, insufficient),
            **score_parts,
        }
        rows.append(row)
    return rows
