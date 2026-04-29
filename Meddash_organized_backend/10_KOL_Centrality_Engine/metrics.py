"""Graph metrics for authorship centrality using pure Python/stdlib."""
from collections import deque
from math import sqrt
try:
    from .authorship_graph import connected_components
except ImportError:
    from authorship_graph import connected_components


def weighted_degree(graph):
    return {n: float(sum(neigh.values())) for n, neigh in graph.items()}


def degree_centrality(graph):
    n = len(graph)
    denom = max(n - 1, 1)
    return {node: len(neigh) / denom for node, neigh in graph.items()}


def pagerank(graph, damping=0.85, iterations=80, tolerance=1e-9):
    nodes = list(graph.keys())
    n = len(nodes)
    if n == 0:
        return {}
    rank = {node: 1.0 / n for node in nodes}
    out_weight = {node: float(sum(graph[node].values())) for node in nodes}
    base = (1.0 - damping) / n
    for _ in range(iterations):
        new = {node: base for node in nodes}
        dangling = sum(rank[node] for node in nodes if out_weight[node] == 0)
        dangling_share = damping * dangling / n
        for node in nodes:
            new[node] += dangling_share
        for src in nodes:
            if out_weight[src] == 0:
                continue
            for dst, weight in graph[src].items():
                new[dst] += damping * rank[src] * (weight / out_weight[src])
        delta = sum(abs(new[node] - rank[node]) for node in nodes)
        rank = new
        if delta < tolerance:
            break
    return rank


def betweenness_centrality(graph, max_sources=250):
    """Brandes betweenness, sampled for large graphs."""
    nodes = list(graph.keys())
    n = len(nodes)
    if n <= 2:
        return {v: 0.0 for v in nodes}
    sources = nodes if n <= max_sources else nodes[:max_sources]
    cb = {v: 0.0 for v in nodes}
    for s in sources:
        stack = []
        pred = {w: [] for w in nodes}
        sigma = dict.fromkeys(nodes, 0.0)
        dist = dict.fromkeys(nodes, -1)
        sigma[s] = 1.0
        dist[s] = 0
        q = deque([s])
        while q:
            v = q.popleft()
            stack.append(v)
            for w in graph[v]:
                if dist[w] < 0:
                    q.append(w)
                    dist[w] = dist[v] + 1
                if dist[w] == dist[v] + 1:
                    sigma[w] += sigma[v]
                    pred[w].append(v)
        delta = dict.fromkeys(nodes, 0.0)
        while stack:
            w = stack.pop()
            for v in pred[w]:
                if sigma[w]:
                    delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w])
            if w != s:
                cb[w] += delta[w]
    scale = 1.0 / ((n - 1) * (n - 2))
    if n > max_sources:
        scale *= n / len(sources)
    return {v: val * scale for v, val in cb.items()}


def eigenvector_centrality(graph, iterations=100, tolerance=1e-8):
    nodes = list(graph.keys())
    n = len(nodes)
    if n == 0:
        return {}, False
    x = {node: 1.0 / sqrt(n) for node in nodes}
    for _ in range(iterations):
        x_new = {node: 0.0 for node in nodes}
        for node in nodes:
            for neigh, weight in graph[node].items():
                x_new[neigh] += x[node] * weight
        norm = sqrt(sum(v*v for v in x_new.values()))
        if norm == 0:
            return {node: 0.0 for node in nodes}, False
        x_new = {node: val / norm for node, val in x_new.items()}
        delta = sum(abs(x_new[node] - x[node]) for node in nodes)
        x = x_new
        if delta < tolerance:
            return x, True
    return x, False


def calculate_metrics(graph):
    deg = degree_centrality(graph)
    wdeg = weighted_degree(graph)
    pr = pagerank(graph)
    btw = betweenness_centrality(graph)
    eig, eig_ok = eigenvector_centrality(graph)
    comp_sizes = {}
    comp_ids = {}
    for idx, comp in enumerate(connected_components(graph), start=1):
        for node in comp:
            comp_sizes[node] = len(comp)
            comp_ids[node] = f"component_{idx}"
    rows = {}
    for node in graph:
        rows[node] = {
            "degree_centrality": deg.get(node, 0.0),
            "weighted_degree": wdeg.get(node, 0.0),
            "pagerank": pr.get(node, 0.0),
            "betweenness": btw.get(node, 0.0),
            "eigenvector": eig.get(node, 0.0),
            "component_size": comp_sizes.get(node, 1),
            "component_id": comp_ids.get(node, "component_0"),
        }
    return rows, eig_ok
