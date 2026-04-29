"""Build an undirected weighted KOL coauthorship graph from Supabase authorship rows."""
from collections import defaultdict
from itertools import combinations


def _sid(value):
    return str(value)


def build_authorship_graph(kols, authorships):
    """Return adjacency dict, graph stats, and per-node mapped authorship stats.

    Nodes are KOL ids as strings. Edges are undirected and weighted by repeated
    coauthorship across publications.
    """
    graph = defaultdict(dict)
    node_stats = defaultdict(lambda: {
        "publication_ids": set(),
        "coauthor_ids": set(),
        "publication_count_mapped": 0,
        "coauthor_count_mapped": 0,
    })

    valid_kols = {_sid(k.get("id")) for k in kols if k.get("id") is not None}
    for kid in valid_kols:
        graph[kid]  # ensure isolated nodes exist
        node_stats[kid]

    by_publication = defaultdict(list)
    for row in authorships:
        kid = row.get("kol_id")
        pid = row.get("publication_id")
        if kid is None or pid is None:
            continue
        kid = _sid(kid)
        if kid not in valid_kols:
            continue
        by_publication[_sid(pid)].append(kid)
        node_stats[kid]["publication_ids"].add(_sid(pid))

    usable_publications = 0
    skipped_single_author = 0
    for pid, raw_kids in by_publication.items():
        kids = sorted(set(raw_kids))
        if len(kids) < 2:
            skipped_single_author += 1
            continue
        usable_publications += 1
        for a, b in combinations(kids, 2):
            graph[a][b] = graph[a].get(b, 0) + 1
            graph[b][a] = graph[b].get(a, 0) + 1
            node_stats[a]["coauthor_ids"].add(b)
            node_stats[b]["coauthor_ids"].add(a)

    for kid, stats in node_stats.items():
        stats["publication_count_mapped"] = len(stats.pop("publication_ids"))
        stats["coauthor_count_mapped"] = len(stats.pop("coauthor_ids"))

    edge_count = sum(len(neigh) for neigh in graph.values()) // 2
    stats = {
        "node_count": len(graph),
        "edge_count": edge_count,
        "authorship_rows": len(authorships),
        "publication_groups": len(by_publication),
        "usable_coauthored_publications": usable_publications,
        "skipped_single_author_or_unmapped_publications": skipped_single_author,
    }
    return dict(graph), stats, dict(node_stats)


def connected_components(graph):
    seen = set()
    comps = []
    for node in graph:
        if node in seen:
            continue
        stack = [node]
        seen.add(node)
        comp = []
        while stack:
            cur = stack.pop()
            comp.append(cur)
            for nxt in graph.get(cur, {}):
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        comps.append(comp)
    return comps
