create table if not exists kol_centrality_runs (
  run_id text primary key,
  computed_at timestamptz not null default now(),
  method_version text not null,
  graph_scope text not null default 'global_authorship',
  status text not null,
  source_row_counts jsonb,
  join_quality jsonb,
  graph_stats jsonb,
  score_distribution jsonb,
  warnings jsonb,
  error text,
  pull_id text,
  triggered_by text,
  duration_seconds numeric
);

create index if not exists idx_kol_centrality_runs_computed_at
  on kol_centrality_runs (computed_at desc);
create index if not exists idx_kol_centrality_runs_status
  on kol_centrality_runs (status);
create index if not exists idx_kol_centrality_runs_pull_id
  on kol_centrality_runs (pull_id);

create table if not exists kol_centrality_scores (
  id bigserial primary key,
  run_id text not null references kol_centrality_runs(run_id) on delete cascade,
  computed_at timestamptz not null default now(),
  method_version text not null,
  graph_scope text not null default 'global_authorship',
  kol_id bigint not null,
  node_count integer,
  edge_count integer,
  component_id text,
  component_size integer,
  publication_count_mapped integer,
  coauthor_count_mapped integer,
  degree_centrality numeric,
  weighted_degree numeric,
  weighted_degree_percentile numeric,
  pagerank numeric,
  pagerank_percentile numeric,
  betweenness numeric,
  betweenness_percentile numeric,
  eigenvector numeric,
  eigenvector_percentile numeric,
  component_size_percentile numeric,
  authorship_centrality_raw numeric,
  authorship_centrality_percentile numeric,
  authorship_centrality_score numeric,
  authorship_centrality_tier text,
  reliability_score numeric,
  reliability_band text,
  score_reason text,
  limitations jsonb,
  missing_inputs jsonb,
  data_coverage_summary text,
  is_latest boolean not null default false,
  created_at timestamptz not null default now()
);

create index if not exists idx_kol_centrality_scores_kol_latest
  on kol_centrality_scores (kol_id, is_latest);
create index if not exists idx_kol_centrality_scores_run_id
  on kol_centrality_scores (run_id);
create index if not exists idx_kol_centrality_scores_graph_scope
  on kol_centrality_scores (graph_scope);
create index if not exists idx_kol_centrality_scores_score
  on kol_centrality_scores (authorship_centrality_score desc);
create index if not exists idx_kol_centrality_scores_reliability
  on kol_centrality_scores (reliability_score desc);
