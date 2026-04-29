"""Single-shot authorship centrality CLI for Meddash."""
import argparse
import csv
import json
import statistics
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parent
ROOT = ENGINE_DIR.parents[0]
DEVOPS = ROOT / "07_DevOps_Observability"
sys.path.insert(0, str(ENGINE_DIR))
sys.path.insert(0, str(DEVOPS))

from centrality_config import METHOD_VERSION, GRAPH_SCOPE, RUNS_TABLE, SCORES_TABLE, validate_config, DEFAULT_THRESHOLDS
from authorship_graph import build_authorship_graph
from metrics import calculate_metrics
from scoring import score_nodes
from reliability import apply_reliability
from reasons import apply_reasons
from supabase_io import fetch_source_data, insert_rows, patch_rows, mark_previous_not_latest, table_exists, create_schema_via_postgres

try:
    from pipeline_summary import write_summary
except Exception:
    def write_summary(engine, status, duration_seconds, **kwargs):
        out = ROOT / "06_Shared_Datastores" / "pipeline_summaries"
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{engine}_summary.json"
        path.write_text(json.dumps({"engine": engine, "status": status, "duration_seconds": duration_seconds, **kwargs}, indent=2, default=str))
        return path

OUTPUT_DIR = ROOT / "06_Shared_Datastores" / "centrality_outputs"
LOG_DIR = ROOT / "07_DevOps_Observability" / "logs"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def json_safe(value):
    return json.loads(json.dumps(value, default=str))


def duplicate_kol_ids(merge_rows):
    ids = set()
    for row in merge_rows:
        status = (row.get("status") or "").lower()
        if status in {"rejected", "resolved", "merged"}:
            continue
        for key in ["kol_id_a", "kol_id_b"]:
            if row.get(key) is not None:
                try:
                    ids.add(int(row[key]))
                except Exception:
                    pass
    return ids


def score_distribution(rows):
    scores = [float(r.get("authorship_centrality_score") or 0) for r in rows]
    if not scores:
        return {}
    return {
        "count": len(scores),
        "min": min(scores),
        "max": max(scores),
        "mean": round(statistics.mean(scores), 2),
        "median": round(statistics.median(scores), 2),
        "tier_counts": {tier: sum(1 for r in rows if r.get("authorship_centrality_tier") == tier) for tier in sorted({r.get("authorship_centrality_tier") for r in rows})},
    }


def reliability_distribution(rows):
    return {band: sum(1 for r in rows if r.get("reliability_band") == band) for band in sorted({r.get("reliability_band") for r in rows})}


def write_local(rows, run_id):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    latest = OUTPUT_DIR / "kol_authorship_centrality_latest.csv"
    specific = OUTPUT_DIR / f"kol_authorship_centrality_{run_id}.csv"
    fields = list(rows[0].keys()) if rows else []
    for path in [latest, specific]:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for row in rows:
                writer.writerow({k: json.dumps(v) if isinstance(v, (list, dict)) else v for k, v in row.items()})
    return [str(latest), str(specific)]


def prepare_score_rows(rows, run_id, method_version, graph_scope, graph_stats):
    prepared = []
    computed_at = now_iso()
    for r in rows:
        row = dict(r)
        row.update({
            "run_id": run_id,
            "computed_at": computed_at,
            "method_version": method_version,
            "graph_scope": graph_scope,
            "node_count": graph_stats.get("node_count"),
            "edge_count": graph_stats.get("edge_count"),
            "is_latest": True,
        })
        for key in ["limitations", "missing_inputs"]:
            row[key] = json_safe(row.get(key, []))
        prepared.append(row)
    return prepared


def run(args):
    start = time.time()
    validate_config()
    run_id = args.run_id or f"centrality_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    method_version = args.method_version or METHOD_VERSION
    graph_scope = args.graph_scope or GRAPH_SCOPE
    warnings = []
    status = "success"
    scores_written = 0
    local_paths = []
    try:
        if args.create_schema:
            create_schema_via_postgres()
        if args.write_supabase and (not table_exists(RUNS_TABLE) or not table_exists(SCORES_TABLE)):
            raise RuntimeError("Centrality Supabase tables are missing. Run schema_validate.py --create first or pass --create-schema.")

        data = fetch_source_data(limit=args.limit)
        source_counts = {k: len(v) for k, v in data.items()}
        graph, graph_stats, node_stats = build_authorship_graph(data["kols"], data["kol_authorships"])
        if graph_stats["edge_count"] == 0:
            raise RuntimeError("Authorship graph has zero edges; refusing to write misleading centrality scores.")
        metrics_by_node, eig_ok = calculate_metrics(graph)
        if not eig_ok:
            warnings.append("Eigenvector centrality unstable; fallback score formula used.")
        thresholds = dict(DEFAULT_THRESHOLDS)
        thresholds.update({"min_publications": args.min_publications, "min_coauthors": args.min_coauthors})
        rows = score_nodes(metrics_by_node, node_stats, eigenvector_available=eig_ok, thresholds=thresholds)
        rows = apply_reliability(rows, graph_stats=graph_stats, duplicate_kol_ids=duplicate_kol_ids(data.get("kol_merge_candidates", [])), eigenvector_available=eig_ok)
        rows = apply_reasons(rows)
        rows = sorted(rows, key=lambda r: (r.get("authorship_centrality_score") or 0, r.get("reliability_score") or 0), reverse=True)
        join_quality = {
            "kols_with_any_publication": sum(1 for s in node_stats.values() if s.get("publication_count_mapped", 0) > 0),
            "kols_with_any_coauthor": sum(1 for s in node_stats.values() if s.get("coauthor_count_mapped", 0) > 0),
            "source_kol_count": len(data["kols"]),
        }
        join_quality["coauthor_mapping_rate"] = round(join_quality["kols_with_any_coauthor"] / max(join_quality["source_kol_count"], 1), 4)
        if join_quality["coauthor_mapping_rate"] < args.min_join_rate:
            warnings.append(f"Coauthor mapping rate {join_quality['coauthor_mapping_rate']} is below requested threshold {args.min_join_rate}; status marked partial.")
            status = "partial"
        dist = score_distribution(rows)
        rel_dist = reliability_distribution(rows)
        prepared = prepare_score_rows(rows, run_id, method_version, graph_scope, graph_stats)
        if args.write_local or args.dry_run:
            local_paths = write_local(prepared, run_id)
        if args.write_supabase:
            run_row = {
                "run_id": run_id,
                "method_version": method_version,
                "graph_scope": graph_scope,
                "status": "running",
                "source_row_counts": source_counts,
                "join_quality": join_quality,
                "graph_stats": graph_stats,
                "score_distribution": dist,
                "warnings": warnings,
                "pull_id": args.pull_id,
                "triggered_by": args.triggered_by,
                "duration_seconds": round(time.time() - start, 2),
            }
            insert_rows(RUNS_TABLE, [run_row], chunk_size=1)
            mark_previous_not_latest(graph_scope)
            scores_written = insert_rows(SCORES_TABLE, prepared, chunk_size=args.chunk_size)
            patch_rows(RUNS_TABLE, f"run_id=eq.{run_id}", {"status": status, "duration_seconds": round(time.time() - start, 2)})
        summary = {
            "run_id": run_id,
            "method_version": method_version,
            "graph_scope": graph_scope,
            "pull_id": args.pull_id,
            "source_row_counts": source_counts,
            "join_quality": join_quality,
            "graph_stats": graph_stats,
            "score_distribution": dist,
            "reliability_distribution": rel_dist,
            "scores_calculated": len(rows),
            "scores_written": scores_written,
            "local_paths": local_paths,
            "warnings": warnings,
            "error": None,
        }
        write_summary("kol_centrality", status, time.time() - start, **summary)
        return 0 if status == "success" else 1
    except Exception as exc:
        write_summary("kol_centrality", "failure", time.time() - start, run_id=run_id, method_version=method_version, graph_scope=graph_scope, pull_id=args.pull_id, error=str(exc), warnings=warnings)
        if args.write_supabase:
            try:
                patch_rows(RUNS_TABLE, f"run_id=eq.{run_id}", {"status": "failure", "error": str(exc), "duration_seconds": round(time.time() - start, 2)})
            except Exception:
                pass
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


def main():
    parser = argparse.ArgumentParser(description="Meddash authorship centrality calculator")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--write-local", action="store_true")
    parser.add_argument("--write-supabase", action="store_true")
    parser.add_argument("--create-schema", action="store_true")
    parser.add_argument("--graph-scope", default=GRAPH_SCOPE)
    parser.add_argument("--method-version", default=METHOD_VERSION)
    parser.add_argument("--pull-id", default=None)
    parser.add_argument("--triggered-by", default="manual")
    parser.add_argument("--min-publications", type=int, default=2)
    parser.add_argument("--min-coauthors", type=int, default=1)
    parser.add_argument("--min-join-rate", type=float, default=0.0)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--chunk-size", type=int, default=500)
    return run(parser.parse_args())

if __name__ == "__main__":
    raise SystemExit(main())
