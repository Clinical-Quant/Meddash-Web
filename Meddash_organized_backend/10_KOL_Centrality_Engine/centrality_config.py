"""Configuration for Meddash authorship centrality v1."""

METHOD_VERSION = "authorship_centrality_v1.0"
GRAPH_SCOPE = "global_authorship"
RUNS_TABLE = "kol_centrality_runs"
SCORES_TABLE = "kol_centrality_scores"

SCORE_WEIGHTS = {
    "weighted_degree_percentile": 0.30,
    "pagerank_percentile": 0.30,
    "betweenness_percentile": 0.20,
    "eigenvector_percentile": 0.10,
    "component_size_percentile": 0.10,
}

FALLBACK_SCORE_WEIGHTS = {
    "weighted_degree_percentile": 0.35,
    "pagerank_percentile": 0.35,
    "betweenness_percentile": 0.20,
    "component_size_percentile": 0.10,
}

DEFAULT_THRESHOLDS = {
    "min_publications": 2,
    "min_coauthors": 1,
    "min_join_rate": 0.80,
    "min_reliability_for_dashboard": 40,
}

TIER_CUTOFFS = [
    (85, "Tier 1 — Network Anchor"),
    (70, "Tier 2 — Strong Connector"),
    (50, "Tier 3 — Established Node"),
    (30, "Tier 4 — Peripheral/Mapped"),
    (1, "Emerging/Peripheral"),
    (0, "Insufficient Data"),
]


def validate_config():
    for label, weights in {"score": SCORE_WEIGHTS, "fallback": FALLBACK_SCORE_WEIGHTS}.items():
        total = round(sum(weights.values()), 6)
        if total != 1.0:
            raise ValueError(f"{label} weights must sum to 1.0, got {total}")
    return True
