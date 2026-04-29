from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from importlib import import_module


def test_score_rows_bounds_and_tiers():
    scoring = import_module('10_KOL_Centrality_Engine.scoring')
    metrics = {
        '1': {'weighted_degree': 10, 'pagerank': 0.5, 'betweenness': 0.2, 'eigenvector': 0.4, 'component_size': 3},
        '2': {'weighted_degree': 5, 'pagerank': 0.3, 'betweenness': 0.1, 'eigenvector': 0.2, 'component_size': 3},
        '3': {'weighted_degree': 0, 'pagerank': 0.2, 'betweenness': 0.0, 'eigenvector': 0.0, 'component_size': 1},
    }
    node_stats = {
        '1': {'publication_count_mapped': 5, 'coauthor_count_mapped': 2},
        '2': {'publication_count_mapped': 2, 'coauthor_count_mapped': 1},
        '3': {'publication_count_mapped': 1, 'coauthor_count_mapped': 0},
    }
    rows = scoring.score_nodes(metrics, node_stats, eigenvector_available=True)
    by_id = {r['kol_id']: r for r in rows}
    assert by_id[1]['authorship_centrality_score'] > by_id[2]['authorship_centrality_score']
    assert by_id[3]['authorship_centrality_tier'] == 'Insufficient Data'
    for row in rows:
        assert 0 <= row['authorship_centrality_score'] <= 100
