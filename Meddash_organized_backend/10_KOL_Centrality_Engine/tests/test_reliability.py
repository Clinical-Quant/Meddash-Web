from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from importlib import import_module


def test_low_coverage_generates_limitation_not_false_low_influence():
    reliability = import_module('10_KOL_Centrality_Engine.reliability')
    row = {'kol_id': 10, 'publication_count_mapped': 1, 'coauthor_count_mapped': 0, 'component_size': 1}
    rel = reliability.calculate_reliability(row, graph_stats={'node_count': 100, 'edge_count': 50})
    assert rel['reliability_score'] < 40
    assert any('incomplete' in item.lower() or 'few' in item.lower() for item in rel['limitations'])
    assert rel['reliability_band'] in {'low', 'very_low'}
