from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from importlib import import_module


def test_build_authorship_graph_counts_pairwise_weighted_edges():
    graph_mod = import_module('10_KOL_Centrality_Engine.authorship_graph')
    kols = [{'id': 1}, {'id': 2}, {'id': 3}]
    authorships = [
        {'kol_id': 1, 'publication_id': 10},
        {'kol_id': 2, 'publication_id': 10},
        {'kol_id': 2, 'publication_id': 11},
        {'kol_id': 3, 'publication_id': 11},
        {'kol_id': 1, 'publication_id': 12},
        {'kol_id': 2, 'publication_id': 12},
    ]
    graph, stats, node_stats = graph_mod.build_authorship_graph(kols, authorships)
    assert stats['node_count'] == 3
    assert stats['edge_count'] == 2
    assert graph['1']['2'] == 2
    assert graph['2']['3'] == 1
    assert node_stats['2']['publication_count_mapped'] == 3
    assert node_stats['2']['coauthor_count_mapped'] == 2
