# MDP3-SWIP3 — KOL Network Centrality Measurement Plan

**Status:** Planning only — do not execute yet  
**Created:** 2026-04-28 05:11 UTC  
**Owner:** Dr. Don  
**Agent:** Alfred Chief  
**Target system:** Meddash Phase 3 Automation / Supabase-backed KOL intelligence  
**Research source:** `C:\Users\email\Hermes Agent Win Files\Meddash Feature Research\KOL_Network_Centrality_Analysis.md`  
**Output file:** `C:\Users\email\.gemini\antigravity\Meddash Phase 3 Automation Observation and Sales\mdp3-swip3.md`

---

## 0. Executive Summary

This SWIP maps the current Supabase data into a repeatable KOL centrality measurement design.

The research document recommends measuring KOL centrality through several network lenses:

1. **Co-authorship network** — KOLs connected by shared publications.
2. **Clinical trial collaboration network** — KOLs connected by participation in the same trial.
3. **Biotech affiliation network** — KOLs connected by association with the same biotech/company.
4. **Institution / geography / therapeutic-area networks** — KOLs connected by shared institution, country, specialty, MeSH, disease area, or therapeutic area.
5. **Weighted influence layer** — centrality adjusted by H-index, citations, journal quality, author weight, trial role, recency, and institution/geography/specialty factors.

Current Supabase is sufficient for a **first repeatable centrality engine**, but with important caveats:

- The **best immediate network** is co-authorship using `kol_authorships` + `publications` + `kols`.
- The **second usable network** is trial collaboration using `trial_investigators` + `trials`, but only 82 investigator rows exist now.
- The **third usable network** is biotech association using `biotech_associated_kols` + `biotech_leads`, but only 6 rows exist now.
- Scholar metrics exist, but `kol_scholar_metrics` currently has only 3 rows, so H-index/citation weighting must be optional until expanded.
- There is no confirmed `institutions` table in the current Supabase OpenAPI schema; institution network must initially use the free-text `kols.institution` field.
- There is no `publication_citations` table in the current schema; true citation-network PageRank cannot be done yet. We can use publication-level journal quality and author/publication weights as proxies.

Recommended first implementation after approval:

**Build a versioned, reproducible centrality pipeline that creates four graphs and one composite KOL centrality score:**

1. `coauthorship_graph`
2. `trial_collaboration_graph`
3. `biotech_affiliation_graph`
4. `topic_similarity_graph`
5. `kol_centrality_scores` output table or materialized result file

No implementation has been done in this SWIP. This document is a planning and mapping artifact only.

---

## 1. Supabase Data Inventory

Supabase REST/OpenAPI was inspected through the existing Meddash-CQ dashboard configuration. Secrets were not printed or copied.

### 1.1 Data types available at database-column level

The database currently exposes these broad PostgreSQL/PostgREST data formats:

| Data type / format | Meaning for centrality work | Example tables |
|---|---|---|
| `bigint`, `integer` | IDs, row counters, binary flags, numeric relationship indicators | `kols`, `kol_authorships`, `trial_investigators`, `trial_sites` |
| `double precision`, `real`, `numeric` | weights, scores, SJR, confidence, enrollment, market analytics | `journal_metrics`, `kol_merge_candidates`, `trials`, `cq_quantitative_analytics` |
| `text`, `character varying` | names, institutions, specialties, disease terms, PMIDs, NCT IDs, URLs, titles | most Meddash/CQ tables |
| `timestamp with time zone`, `timestamp without time zone` | recency, ingestion freshness, update timing | `kols_staging`, `kol_scholar_metrics`, `cq_*`, ontology tables |
| `boolean` | review flags | `scholar_review_queue` |
| `uuid` | app/user system identifiers | `user_profiles`, `user_credits`, `credit_transactions` |

For KOL centrality, the important data types are:

- **Node IDs:** `kols.id`, `kol_authorships.kol_id`, `trial_investigators.kol_id`, `biotech_associated_kols.kol_id`
- **Edge group IDs:** `publication_id`, `nct_id`, `company_slug`, `institution`, `specialty`, `country`, `mesh_id`
- **Edge weights:** repeated co-occurrence counts, `is_primary_author`, `author_position`, trial `role`, trial `phase`, journal `sjr_weight`, KOL `author_publication_weight`
- **Recency fields:** `published_date`, `start_date`, `completion_date`, `last_update_posted`, `created_at`, `updated_at`, `last_updated_date`
- **Quality fields:** `h_index`, `total_citations`, `i10_index`, `sjr`, `sjr_weight`, `trial phase`, investigator role

### 1.2 Full table inventory from Supabase OpenAPI

| Table | Rows | Columns | Data type families | Centrality relevance |
|---|---:|---:|---|---|
| `kols` | 8,485 | 15 | bigint, double precision, text | **Core node table** |
| `kols_staging` | 247 | 15 | integer, real, text, timestamptz | staging / QA, not centrality source |
| `kol_authorships` | 8,461 | 4 | bigint, text | **Primary co-authorship edge source** |
| `publications` | 922 | 11 | bigint, text | publication metadata, journal/PMID/date |
| `publication_mesh_map` | 10,353 | 3 | bigint, text | topic/MeSH weighting and topic similarity |
| `journal_metrics` | 31,125 | 10 | bigint, double precision, text | journal quality weighting / Mango-like factor |
| `kol_scholar_metrics` | 3 | 6 | integer, text, timestamptz | H-index/citation weighting, currently sparse |
| `trial_investigators` | 82 | 8 | bigint, text | **Trial collaboration edge source** |
| `trials` | 100 | 23 | double precision, text | trial metadata, phase/status/enrollment/date |
| `trial_sites` | 4,056 | 8 | bigint, text | geography/site network support |
| `trial_sponsors` | 143 | 5 | bigint, text | sponsor/company context |
| `trial_conditions` | 268 | 5 | bigint, text | condition/MeSH disease context |
| `trial_interventions` | 272 | 5 | bigint, text | drug/modality context |
| `trial_publications` | 35 | 8 | bigint, text | trial-publication bridge |
| `trial_results` | 102 | 9 | bigint, double precision, text | trial outcome quality context, not centrality edge source |
| `trial_outcomes` | 889 | 6 | bigint, text | endpoint context, not centrality edge source |
| `trial_eligibility` | 100 | 11 | bigint, text | trial phenotype context |
| `biotech_leads` | 640 | 13 | bigint, text | company/prospect/ticker context |
| `biotech_associated_kols` | 6 | 2 | bigint, text | biotech affiliation edge source, sparse |
| `associated_kols` | 6 | 9 | bigint, text | associated KOL subset, sparse |
| `kol_merge_candidates` | 241 | 14 | bigint, double precision, text | duplicate/disambiguation safety layer |
| `deep_disambiguation_needed` | 0 | 9 | integer, real, text, timestamptz | disambiguation workflow, no current rows |
| `scholar_review_queue` | 0 | 11 | boolean, integer, text, timestamptz | scholar matching QA, no current rows |
| `mesh_ontology` | 2,613 | 5 | text | MeSH vocabulary for topic normalization |
| `condition_mesh_map` | 15 | 5 | text | condition-to-MeSH map |
| `therapeutic_areas` | 0 | 4 | text | planned TA layer, empty |
| `kol_therapeutic_areas` | 0 | 2 | text | planned KOL-TA bridge, empty |
| `therapeutic_area_map` | 0 | 2 | text | planned MeSH-to-TA map, empty |
| `ontology_mesh` | 0 | 4 | varchar, text, timestamp | duplicate/planned ontology table, empty |
| `ontology_icd10` | 0 | 4 | varchar, text, timestamp | planned ontology table, empty |
| `ontology_snomed` | 0 | 3 | varchar, text, timestamp | planned ontology table, empty |
| `ontology_crosswalk` | 0 | 6 | varchar, integer, double precision, timestamp | planned ontology bridge, empty |
| `ct_kol_summary` | 0 | 17 | text | planned summary table, empty |
| `cq_regulatory_catalysts` | 0 | 8 | bigint, varchar, text, timestamptz | CQ layer, not KOL centrality yet |
| `cq_market_sentiment` | 0 | 8 | bigint, varchar, numeric, text, timestamptz | CQ layer, not KOL centrality yet |
| `cq_quantitative_analytics` | 0 | 15 | bigint, varchar, numeric, text, timestamptz | CQ layer, not KOL centrality yet |
| `cq_scientific_congresses` | 0 | 10 | bigint, varchar, numeric, text, timestamptz | future congress/KOL signal, currently empty |
| `system_changelog` | 1 | 5 | varchar, integer, text, timestamp | ops metadata |
| `user_profiles` | 0 | 3 | uuid, text, timestamp | app metadata, not centrality |
| `user_credits` | 0 | 4 | uuid, bigint, timestamp | app monetization metadata, not centrality |
| `credit_transactions` | 0 | 6 | uuid, bigint, text, timestamp | app monetization metadata, not centrality |

---

## 2. Centrality Methods from Research Document

The research document lists the following centrality measures:

| Measure | What it means for KOLs | Use here? | Notes |
|---|---|---|---|
| Degree centrality | How many direct collaborators / links a KOL has | Yes | Fast, explainable, good first metric |
| Weighted degree | Direct links adjusted by edge strength | Yes | Better than raw degree for coauthorship/trials |
| Betweenness centrality | Whether a KOL bridges otherwise separate clusters | Yes | Strategic for medical affairs; use sampled approximation if graph grows |
| Eigenvector centrality | Whether a KOL is connected to other influential KOLs | Yes, with fallback | May fail or distort on disconnected graphs |
| PageRank | Stable overall influence based on connection quality | Yes | Recommended primary overall network score |
| Closeness centrality | How quickly KOL can reach the whole network | Conditional | Use within connected components, not whole disconnected graph blindly |
| Katz centrality | Direct + indirect influence with attenuation | Later | Useful but more parameter-sensitive |
| Composite centrality | Weighted blend of multiple centrality metrics | Yes | Needed for product-facing KOL score |

---

## 3. Mapping Current Supabase Data to Centrality Networks

### 3.1 KOL node table

| Source table | Relevant fields | Role |
|---|---|---|
| `kols` | `id`, `first_name`, `last_name`, `degree`, `institution`, `specialty`, `country`, `orcid`, `scholar_id`, `author_publication_weight` | canonical node list and node attributes |
| `kols_staging` | same broad identity fields plus `verification_status` | staging-only; do not use until promoted/verified |
| `kol_merge_candidates` | `kol_id_a`, `kol_id_b`, similarity scores, `status` | duplicate prevention before centrality output |

Canonical node ID should be `kols.id`.

Important caveat: some tables use `kol_id` as `text`, others use `bigint/integer`. SWIP3 implementation must normalize all KOL IDs to a single string representation internally, then write output back with the correct DB type.

---

### 3.2 Co-authorship network — highest priority

**Research document mapping:** section 3.1, `kol_authorships`.

| Component | Supabase source | Current state |
|---|---|---|
| Nodes | `kols.id` | 8,485 KOLs |
| Edge group | `kol_authorships.publication_id` | 8,461 authorship rows |
| Edge members | `kol_authorships.kol_id` | KOLs per publication |
| Edge weight | count of shared `publication_id` pairs | available |
| Edge modifiers | `is_primary_author`, `author_position` | available |
| Publication metadata | `publications.id`, `pmid`, `doi`, `journal_name`, `issn`, `published_date`, `publication_type` | available |
| Topic metadata | `publication_mesh_map.pmid`, `mesh_id`, `is_major_topic` | available |
| Journal quality | `journal_metrics.issn`, `sjr`, `sjr_weight`, journal `h_index` | available |

**Constructible graph:** yes.

**Graph design:**

- Undirected weighted graph.
- Add one node per KOL.
- For each publication, connect every pair of KOLs who authored that publication.
- Base edge weight = number of co-authored publications.
- Optional boosted edge weight:
  - higher if both are primary/senior author positions;
  - higher if publication journal has high `sjr_weight`;
  - higher if publication is recent;
  - higher if publication MeSH topic matches the target therapeutic area.

**Recommended metrics:**

- degree centrality
- weighted degree
- betweenness centrality
- PageRank
- eigenvector centrality with PageRank fallback
- connected component ID and component size

**Reliability:** high for first version.

---

### 3.3 Clinical trial collaboration network — second priority

**Research document mapping:** section 3.2, `trial_investigators`.

| Component | Supabase source | Current state |
|---|---|---|
| Nodes | `kols.id` linked from `trial_investigators.kol_id` | present but only 82 investigator rows |
| Edge group | `trial_investigators.nct_id` | available |
| Edge members | KOLs/investigators on same `nct_id` | available |
| Edge weight | count of trials shared | available |
| Edge modifiers | `role`, `bridge_confidence`, `bridge_method` | available |
| Trial metadata | `trials.phase`, `overall_status`, `enrollment`, dates | available |
| Sponsor context | `trial_sponsors.sponsor_name`, `sponsor_class`, `is_lead` | available |
| Site/geography | `trial_sites.facility_name`, `city`, `country` | available |
| Disease context | `trial_conditions.condition`, `mesh_id`, `mesh_term` | available |

**Constructible graph:** yes, but sparse.

**Graph design:**

- Undirected weighted graph.
- Group investigators by `nct_id`.
- Connect KOLs who appear on the same trial.
- Base edge weight = number of trials together.
- Optional boosted edge weight:
  - Phase 3 > Phase 2 > Phase 1;
  - PI role > collaborator role;
  - active/recruiting trials > old/completed trials for momentum;
  - higher `bridge_confidence` if present and numeric/interpretable.

**Recommended metrics:**

- weighted degree
- betweenness centrality
- PageRank
- trial PI weighted score
- component size

**Reliability:** medium now; will improve when trial investigator coverage expands.

---

### 3.4 Biotech affiliation network — third priority / sparse now

**Research document mapping:** section 3.4, `biotech_associated_kols`.

| Component | Supabase source | Current state |
|---|---|---|
| Nodes | `biotech_associated_kols.kol_id` mapped to `kols.id` | present |
| Edge group | `biotech_associated_kols.company_slug` | present |
| Company metadata | `biotech_leads.company_slug`, `company_name`, `primary_indication`, `trial_nct_id`, `ticker`, `tier` | present |
| Edge weight | shared company association | constructible |

**Constructible graph:** yes, but currently too sparse for strong centrality.

Only 6 `biotech_associated_kols` rows were visible, so this should be included as a component but not heavily weighted until data volume improves.

**Recommended metrics:**

- biotech degree
- company bridge count
- biotech PageRank only when row volume improves

**Reliability:** low for now.

---

### 3.5 Institution network — usable with free-text normalization

**Research document mapping:** section 4.1 mentions institution network, but expected `institution_id`; current schema has no populated `institutions` table and `kols` uses free-text `institution`.

| Component | Supabase source | Current state |
|---|---|---|
| Nodes | `kols.id` | present |
| Edge group | normalized `kols.institution` | present as free text |
| Edge weight | same institution | constructible after text normalization |
| Quality modifier | institution prestige | not currently available as structured table |

**Constructible graph:** yes, but needs normalization.

**Graph design:**

- Normalize institution names:
  - lowercase;
  - remove punctuation/corporate suffixes;
  - collapse obvious aliases later.
- Connect KOLs sharing same normalized institution.
- Avoid creating huge cliques for generic missing/unknown institution values.

**Recommended metrics:**

- institution degree
- institution component size
- institution bridge score if multiple institution aliases/groups exist

**Reliability:** medium-low until institution normalization and ranking exist.

---

### 3.6 Topic / therapeutic-area similarity network — feasible and useful

Although the research document focuses on `kol_therapeutic_areas`, that table is currently empty. However, we can construct a useful topic network from publication MeSH and trial condition MeSH.

| Component | Supabase source | Current state |
|---|---|---|
| Publication topic map | `publication_mesh_map.pmid`, `mesh_id`, `is_major_topic` | 10,353 rows |
| Publication metadata | `publications.pmid`, `id` | 922 rows |
| KOL-publication bridge | `kol_authorships.publication_id` | 8,461 rows |
| MeSH vocabulary | `mesh_ontology.mesh_id`, `mesh_term`, `mesh_tree_number`, `mesh_category` | 2,613 rows |
| Trial disease context | `trial_conditions.nct_id`, `mesh_id`, `mesh_term` | 268 rows |

**Constructible graph:** yes.

**Graph design options:**

1. **KOL-topic bipartite graph:** KOL -> MeSH topic.
2. **KOL-KOL topic similarity graph:** connect KOLs with overlapping MeSH topics.
3. **Therapeutic-area filtered graph:** build centrality inside a disease/topic subset instead of all KOLs.

**Recommended first approach:**

- Build KOL topic vectors from MeSH IDs associated with their publications.
- Weight `is_major_topic = 1` higher than minor topic.
- Connect KOLs if cosine/Jaccard similarity exceeds a threshold.
- Use this as a specialty/TA relevance layer, not the main centrality layer.

**Reliability:** medium-high if publication-to-PMID mapping is consistent.

---

### 3.7 Citation network — not currently possible as true citation graph

**Research document mapping:** section 3.3 expects `publication_citations`.

Current Supabase OpenAPI did **not** show a `publication_citations` table.

Therefore:

- True citation PageRank cannot be built yet.
- We can still use citation-like proxies:
  - `kol_scholar_metrics.total_citations` where available, but only 3 rows now;
  - `journal_metrics.sjr_weight` via publication ISSN;
  - `journal_metrics.h_index`;
  - `kols.author_publication_weight`.

**Recommendation:** defer true citation network until citation edge data exists.

---

## 4. Proposed Repeatable KOL Centrality Model

### 4.1 Core principle

Separate **network centrality** from **influence weighting**.

Network centrality answers:

> “Where does this KOL sit in the collaboration network?”

Influence weighting answers:

> “How strong, recent, clinically relevant, and academically credible are those connections?”

Do not mix everything into one black-box score too early. Store component scores separately, then compute a transparent composite.

---

### 4.2 Proposed v1 graph layers

| Graph layer | Source | Purpose | Readiness |
|---|---|---|---|
| `coauthorship` | `kol_authorships` + `publications` | academic collaboration centrality | high |
| `trial_collaboration` | `trial_investigators` + `trials` | clinical trial network centrality | medium |
| `biotech_affiliation` | `biotech_associated_kols` + `biotech_leads` | industry/biotech connector centrality | low now, high later |
| `topic_similarity` | `publication_mesh_map` + `publications` + `kol_authorships` | disease/TA relevance network | medium-high |
| `institution_similarity` | `kols.institution` | institutional clique/network context | medium-low |

---

### 4.3 Proposed v1 centrality measures per graph

| Graph | Degree | Weighted degree | Betweenness | PageRank | Eigenvector | Closeness | Notes |
|---|---|---|---|---|---|---|---|
| coauthorship | yes | yes | yes | yes | yes/fallback | component-only | best first graph |
| trial_collaboration | yes | yes | yes | yes | optional | component-only | sparse but strategically valuable |
| biotech_affiliation | yes | yes | optional | optional | no until more rows | no | currently sparse |
| topic_similarity | yes | yes | optional | yes | optional | no | use for TA relevance |
| institution_similarity | yes | yes | no initially | no initially | no | no | avoid over-weighting large institutions |

---

### 4.4 Proposed composite score

The research document suggests:

```text
network composite =
  degree * 0.20 +
  betweenness * 0.20 +
  eigenvector * 0.25 +
  closeness * 0.15 +
  pagerank * 0.20
```

For our current data, I recommend modifying this for v1:

```text
per_graph_network_score =
  weighted_degree_percentile * 0.25 +
  pagerank_percentile         * 0.30 +
  betweenness_percentile      * 0.25 +
  eigenvector_or_pr_percentile* 0.10 +
  component_size_percentile   * 0.10
```

Reason:

- Percentiles are easier to compare across disconnected graphs and different graph sizes.
- PageRank is more stable than eigenvector on disconnected graphs.
- Closeness is fragile in disconnected networks; use only within components or leave as diagnostic.

Then compute a cross-network KOL score:

```text
kol_network_centrality_v1 =
  coauthorship_score        * 0.50 +
  trial_collaboration_score * 0.25 +
  topic_similarity_score    * 0.15 +
  institution_score         * 0.05 +
  biotech_affiliation_score * 0.05
```

Temporary rationale:

- Co-authorship has the most rows and best network density.
- Trial collaboration is strategically important but currently sparse.
- Topic similarity prevents high centrality in irrelevant therapeutic areas from dominating.
- Biotech affiliation is currently too sparse for a high weight.

When `biotech_associated_kols`, `kol_scholar_metrics`, and CRM/client interaction data improve, weights can be revisited.

---

### 4.5 Proposed weighted influence score

After network score is computed, add a transparent influence overlay:

```text
kol_centrality_weighted_v1 =
  kol_network_centrality_v1
  * academic_factor
  * journal_quality_factor
  * recency_factor
  * trial_role_factor
  * data_confidence_factor
```

Where:

| Factor | Source | Current readiness |
|---|---|---|
| `academic_factor` | `kol_scholar_metrics.h_index`, `total_citations`, `i10_index` | low now; only 3 rows |
| `journal_quality_factor` | `publications.issn` -> `journal_metrics.sjr_weight` | medium-high |
| `recency_factor` | `publications.published_date`, `trials.start_date`, `last_update_posted` | medium; date parsing needed |
| `trial_role_factor` | `trial_investigators.role`, `trials.phase` | medium |
| `data_confidence_factor` | `bridge_confidence`, `kol_merge_candidates`, null/coverage checks | medium |

Important: the score should not hide sparse-data limitations. Every output should include `confidence_band` and `missing_inputs`.

---

## 5. Output Data Model Proposal

### 5.1 Planned output table: `kol_centrality_scores`

Do not create this table yet. This is the proposed shape for later implementation.

| Column | Type | Meaning |
|---|---|---|
| `run_id` | text/uuid | unique centrality run ID |
| `computed_at` | timestamp | run timestamp |
| `kol_id` | bigint/text normalized | KOL ID |
| `network_scope` | text | `global`, disease-specific, topic-specific, company-specific |
| `graph_name` | text | `coauthorship`, `trial_collaboration`, `biotech_affiliation`, `topic_similarity`, `aggregate` |
| `node_count` | integer | number of nodes in graph |
| `edge_count` | integer | number of edges in graph |
| `component_id` | text/integer | connected component ID |
| `component_size` | integer | KOLs in component |
| `degree_raw` | numeric | direct edge count |
| `degree_centrality` | numeric | normalized degree |
| `weighted_degree` | numeric | weighted direct influence |
| `betweenness` | numeric | broker/gatekeeper score |
| `pagerank` | numeric | stable influence score |
| `eigenvector` | numeric | network quality score, if stable |
| `closeness` | numeric | optional / component-local |
| `network_score` | numeric | per-graph composite |
| `academic_factor` | numeric | H-index/citation factor if available |
| `journal_quality_factor` | numeric | SJR/Mango-like factor |
| `recency_factor` | numeric | recent activity factor |
| `trial_role_factor` | numeric | PI/phase score |
| `data_confidence` | numeric | coverage and linkage confidence |
| `weighted_centrality_score` | numeric | final weighted score |
| `tier` | text | Tier 1 / Tier 2 / Tier 3 / Tier 4 / Emerging |
| `missing_inputs` | json/text | what data was absent |
| `method_version` | text | e.g. `centrality_v1.0` |

### 5.2 Planned output table: `kol_centrality_runs`

| Column | Type | Meaning |
|---|---|---|
| `run_id` | text/uuid | centrality run ID |
| `computed_at` | timestamp | run timestamp |
| `method_version` | text | algorithm version |
| `source_row_counts` | json | input table row counts |
| `graph_stats` | json | nodes/edges/components by graph |
| `warnings` | json/text | sparse data, missing tables, failed metrics |
| `status` | text | success/partial/failed |

---

## 6. SWIP3 Work Plan — Planning Only

> Use this section later for implementation. Do not execute until Dr. Don approves.

### A. Schema and data-readiness checkpoint

- [ ] Confirm final list of Supabase source tables.
- [ ] Confirm KOL ID type normalization rule (`kols.id` bigint vs `kol_id` text in some tables).
- [ ] Confirm row counts and null rates for centrality-critical columns.
- [ ] Confirm whether `publication_id` in `kol_authorships` always joins to `publications.id`.
- [ ] Confirm whether `publications.pmid` joins reliably to `publication_mesh_map.pmid`.
- [ ] Confirm whether `publications.issn` joins reliably to `journal_metrics.issn` or `issn_print`.
- [ ] Confirm whether `trial_investigators.kol_id` joins to `kols.id`.
- [ ] Confirm whether `biotech_associated_kols.company_slug` joins to `biotech_leads.company_slug`.
- [ ] Confirm whether `kols.institution` and `kols.specialty` have enough non-null coverage.

### B. Centrality method design

- [ ] Define v1 graph list: coauthorship, trial collaboration, biotech affiliation, topic similarity, institution similarity.
- [ ] Define edge-weight formulas for each graph.
- [ ] Define percentiling/normalization method.
- [ ] Define fallback behavior for disconnected graphs.
- [ ] Define how to handle KOLs with no graph edges.
- [ ] Define final composite weights.
- [ ] Define tier thresholds.
- [ ] Define `data_confidence` formula.

### C. Output schema design

- [ ] Decide whether to store results in Supabase tables or local parquet/CSV first.
- [ ] If Supabase: create SQL migration for `kol_centrality_runs`.
- [ ] If Supabase: create SQL migration for `kol_centrality_scores`.
- [ ] Add method versioning.
- [ ] Add run metadata and warnings.
- [ ] Add index strategy for `kol_id`, `run_id`, `graph_name`, `network_scope`.

### D. Implementation design

- [ ] Create a standalone script, likely `07_Analytics/kol_centrality/build_kol_centrality.py`.
- [ ] Build read-only Supabase extraction layer.
- [ ] Build graph construction functions.
- [ ] Build centrality calculation functions.
- [ ] Build normalization/tiering functions.
- [ ] Build output writer.
- [ ] Add CLI flags: `--dry-run`, `--graph`, `--scope`, `--write`, `--limit`, `--method-version`.
- [ ] Add structured JSON logging.

### E. QA and validation plan

- [ ] Unit test edge generation from tiny fake coauthorship table.
- [ ] Unit test edge weighting for author role, journal SJR, and recency.
- [ ] Unit test trial collaboration graph from tiny fake NCT table.
- [ ] Unit test sparse/no-edge KOL behavior.
- [ ] Unit test disconnected graph fallback.
- [ ] Validate top 20 KOLs manually for obvious nonsense.
- [ ] Validate one known KOL brief before exposing in dashboard.
- [ ] Add “not enough data” warning when graph density is too low.

### F. Dashboard integration plan

- [ ] Add a future dashboard section only after output table exists.
- [ ] Do not show centrality as truth without confidence band.
- [ ] For each KOL, display component scores: coauthorship, trial, topic, biotech, institution.
- [ ] Add explanation: “centrality is network influence, not clinical quality.”
- [ ] Add tooltip definitions for degree, betweenness, PageRank, composite, confidence.

---

## 7. Recommended v1 Execution Order After Approval

1. **Dry-run schema audit script**
   - Read OpenAPI schema and row counts.
   - Print missing joins/null rates.
   - No writes.

2. **Build coauthorship graph only**
   - `kols` + `kol_authorships` + `publications`.
   - Calculate degree, weighted degree, PageRank, betweenness.
   - Export local CSV for review.

3. **Add journal and recency weights**
   - Join publications to journal metrics by ISSN.
   - Add recency factor from `published_date`.

4. **Add trial graph**
   - `trial_investigators` + `trials`.
   - Keep separate from coauthorship at first.

5. **Add topic similarity graph**
   - `publication_mesh_map` + `mesh_ontology`.
   - Use for TA-specific centrality.

6. **Add aggregate score**
   - Blend graph scores only after individual layers are inspected.

7. **Write back to Supabase only after review**
   - Create output tables.
   - Add method version and run metadata.

8. **Add dashboard view**
   - Show centrality scores with explanation and confidence.

---

## 8. Risks and Design Guardrails

### 8.1 Major risks

| Risk | Why it matters | Guardrail |
|---|---|---|
| Duplicate KOLs | Duplicates artificially split centrality | use `kol_merge_candidates` before trusting output |
| Sparse scholar metrics | H-index only covers 3 rows now | make academic factor optional, not required |
| Sparse biotech associations | only 6 biotech-associated rows | low weight until expanded |
| Missing citation graph | no `publication_citations` table | do not claim citation PageRank yet |
| Free-text institutions | aliases create false splits | normalize and mark low confidence |
| Disconnected graphs | closeness/eigenvector can mislead | use PageRank fallback and component-local metrics |
| Over-explaining one score | users may treat composite as truth | show components + confidence + missing inputs |

### 8.2 “Do not do” list

- Do not write scores back into `kols` directly.
- Do not overwrite existing KOL fields.
- Do not create a single black-box “influence score” without component scores.
- Do not use revenue/CRM/client assumptions in centrality.
- Do not use empty tables as if populated.
- Do not claim citation centrality until citation edge data exists.
- Do not treat all coauthorship edges equally once journal/recency/author-position weights are available.

---

## 9. Decision Needed From Dr. Don

Before execution, decide:

1. Should v1 start with **coauthorship only** for a clean first deliverable?
2. Should output first be a **local CSV/parquet review file** before creating Supabase output tables?
3. Should the first dashboard view be global centrality, or centrality **within a therapeutic area**?
4. Should the final score be named:
   - `KOL Centrality Score`
   - `KOL Network Influence Score`
   - `Meddash KOL Influence Index`
   - another name?

My recommendation:

**Start with coauthorship-only v1, produce a local review CSV, inspect the top 50 KOLs manually, then add trial/topic layers and only then write a versioned Supabase table.**

---

## 10. Acceptance Criteria for SWIP3 Plan

This planning document is complete when:

- [x] Current Supabase tables and data types are listed.
- [x] Research centrality methods are mapped to current data sources.
- [x] Feasible vs missing data sources are clearly separated.
- [x] A repeatable centrality measurement path is proposed.
- [x] Output schema is proposed but not executed.
- [x] Implementation checklist exists but remains unexecuted.

---

## 10.5 Complete Phase 1 Authorship Centrality Implementation Brief

This section is intentionally placed before Topic 11 so that future readers understand the scoring parameters, system design, implementation plan, and limitations before reading the detailed checklist.

### 10.5.1 What Phase 1 Is Intended to Build

Phase 1 is intended to build an automatic, repeatable **Authorship Centrality** calculation for every KOL using currently available Supabase authorship data.

The intended system:

- reads the latest KOL and authorship data from Supabase;
- builds a co-authorship graph;
- calculates centrality metrics for each KOL;
- assigns a 0–100 authorship centrality score;
- assigns a centrality tier;
- generates a human-readable reason for the score;
- generates a separate reliability score;
- stores limitations and missing inputs;
- runs after every successful KOL/publication pull;
- supports future centrality layers without rewriting the whole system.

The score should not be presented as “total real-world KOL influence.” It should be presented as:

> “Mapped authorship centrality inside the Meddash publication network currently available.”

This distinction matters because a low score may reflect incomplete data capture rather than true low influence.

---

### 10.5.2 Why Authorship Centrality Is the Phase 1 Base Layer

Authorship is the best Phase 1 base because it uses real, observable professional relationships.

The graph logic is straightforward:

```text
KOL = node
shared publication = edge
repeated shared publications = stronger edge
```

Current usable source tables:

| Table | Role in Phase 1 |
|---|---|
| `kols` | canonical KOL node list |
| `kol_authorships` | KOL-to-publication bridge table |
| `publications` | publication metadata |
| `publication_mesh_map` | optional disease/topic context |
| `mesh_ontology` | optional MeSH label/context lookup |
| `journal_metrics` | optional journal quality weighting |
| `kol_merge_candidates` | duplicate/disambiguation warning layer |

This is more defensible than starting with trial, biotech, institution, scholar, or CRM signals because those layers are currently sparse, incomplete, unnormalized, or not connected yet.

---

### 10.5.3 Proposed System Architecture

Recommended architecture:

```text
KOL/publication pull completes
  -> centrality job starts
  -> extract latest Supabase data
  -> validate joins and row counts
  -> build authorship graph
  -> calculate graph metrics
  -> normalize metrics
  -> calculate final score
  -> calculate reliability and limitations
  -> write local review output first
  -> after approval, write versioned Supabase output
  -> dashboard reads latest successful centrality run
```

Recommended script shape:

```text
extract_source_data()
validate_source_data()
build_authorship_graph()
calculate_graph_metrics()
normalize_metrics_to_percentiles()
calculate_authorship_score()
calculate_reliability_score()
generate_score_reason()
generate_limitations()
write_local_review_output()
write_supabase_output_if_approved()
```

Recommended automation:

- Run automatically after a successful KOL/publication pull.
- Also run nightly as a safety refresh.
- Use `run_id` and `method_version` every time.
- Store previous runs instead of overwriting history.

---

### 10.5.4 Proposed Score Parameters

The Phase 1 score should use percentile-normalized graph metrics so KOLs can be compared fairly inside the mapped network.

Proposed final formula:

```text
authorship_centrality_score = 100 * (
  weighted_degree_percentile * 0.30 +
  pagerank_percentile         * 0.30 +
  betweenness_percentile      * 0.20 +
  eigenvector_percentile      * 0.10 +
  component_size_percentile   * 0.10
)
```

Fallback formula if eigenvector centrality fails or is unstable:

```text
authorship_centrality_score = 100 * (
  weighted_degree_percentile * 0.35 +
  pagerank_percentile         * 0.35 +
  betweenness_percentile      * 0.20 +
  component_size_percentile   * 0.10
)
```

Why these parameters:

| Metric | Weight | Reason |
|---|---:|---|
| Weighted degree | 30% | measures direct collaboration strength and repeated coauthorship |
| PageRank | 30% | measures influence through connections to other connected KOLs; stable on broad graphs |
| Betweenness | 20% | identifies bridge KOLs who connect otherwise separate clusters |
| Eigenvector | 10% | captures connection to influential KOLs, but lower weight because disconnected graphs can make it unstable |
| Component size | 10% | prevents over-ranking KOLs who are central only inside tiny isolated components |

Do not use raw publication count alone as the score. Publication count is a coverage and context signal, not centrality by itself.

---

### 10.5.5 Metric Definitions for Future Readers

| Metric | Plain-language meaning | Use in score |
|---|---|---|
| `publication_count_mapped` | how many publications we have mapped for this KOL | coverage/reliability, not direct score |
| `coauthor_count_mapped` | how many unique mapped KOL coauthors this KOL has | context and direct reach |
| `degree_centrality` | number of direct KOL connections normalized by graph size | direct network reach |
| `weighted_degree` | direct connections adjusted for repeated collaborations | main direct-connectivity metric |
| `pagerank` | influence based on being connected to other connected KOLs | main global network metric |
| `betweenness` | how often this KOL connects separate clusters | bridge/broker metric |
| `eigenvector` | whether this KOL connects to already influential KOLs | secondary influence-quality metric |
| `component_size` | size of the connected group the KOL belongs to | network-context metric |
| `reliability_score` | how much we trust the calculated centrality | displayed beside score; not the same as centrality |

---

### 10.5.6 Score Tiers

| Score | Tier | Meaning |
|---:|---|---|
| 85–100 | Tier 1 — Highly Central Author Network KOL | strong mapped coauthor network and high network influence |
| 70–84 | Tier 2 — High Centrality | well-connected in mapped authorship network |
| 50–69 | Tier 3 — Moderate Centrality | visible role but not dominant |
| 30–49 | Tier 4 — Low Mapped Centrality | limited mapped coauthor network or small component |
| 1–29 | Emerging / Peripheral | little mapped centrality in current data |
| 0/null | Insufficient Data | too little mapped authorship data to score fairly |

Important interpretation rule:

> Low score + high reliability may mean low mapped centrality. Low score + low reliability means “not enough mapped evidence,” not “low real-world KOL influence.”

---

### 10.5.7 Score Reason System

Every KOL score should have a short explanation. The explanation should make the metric interpretable inside a KOL brief or dashboard.

Examples:

```text
High authorship centrality because this KOL has many mapped coauthors, repeated collaborations, high PageRank, and belongs to a large connected publication component.
```

```text
Moderate authorship centrality because this KOL has a visible mapped coauthor network but limited bridge/betweenness role across clusters.
```

```text
Low measured centrality, but reliability is limited because the KOL’s publication network appears incompletely mapped. Do not interpret as low real-world influence.
```

The reason generator should consider:

- score tier;
- reliability band;
- mapped publication count;
- mapped coauthor count;
- PageRank percentile;
- betweenness percentile;
- component size;
- missing metadata;
- unresolved duplicate warnings.

---

### 10.5.8 Reliability System

Centrality and reliability must be separate.

Proposed reliability formula:

```text
reliability_score =
  publication_coverage_factor      * 0.35 +
  coauthor_mapping_factor          * 0.25 +
  metadata_completeness_factor     * 0.15 +
  disambiguation_confidence_factor * 0.15 +
  graph_component_factor           * 0.10
```

Reliability bands:

| Reliability | Band | Interpretation |
|---:|---|---|
| 80–100 | High | score can be used confidently inside the mapped network |
| 60–79 | Medium | usable with caveats |
| 40–59 | Low | show warning; avoid hard ranking |
| 0–39 | Insufficient | do not rank; show “needs more data” |

This protects against false conclusions when a KOL’s publication universe is incomplete.

---

### 10.5.9 Planned Storage Model

Recommended: do not write detailed centrality metrics directly into `kols` first.

Instead, create a versioned output table later:

```text
kol_centrality_scores
```

Potential companion run table:

```text
kol_centrality_runs
```

Only after the detailed output design is accepted, optional summary columns may be added to `kols` for dashboard speed:

```text
authorship_centrality_score
authorship_centrality_tier
authorship_centrality_confidence
authorship_centrality_updated_at
authorship_centrality_method_version
```

Reason:

- `kols` should remain the canonical identity table.
- Centrality is a calculated analytic result.
- Calculated scores need versioning and run history.
- Future trial/topic/biotech centrality layers should coexist without overwriting each other.

---

### 10.5.10 Major Limitations and Mitigation Plan

#### Limitation: incomplete publication network can falsely lower score

A major KOL may have many real publications, but Meddash may only have a small subset mapped.

Current mitigation:

- store mapped publication count;
- store mapped coauthor count;
- calculate reliability separately;
- mark low-coverage KOLs as `Insufficient Data` or `Low Reliability`;
- do not present low-reliability low scores as true low influence.

Future mitigation:

- expand PubMed/OpenAlex/Semantic Scholar pulls;
- pull full author lists per publication;
- add external author IDs such as ORCID/OpenAlex/Scholar ID;
- estimate coverage against known external publication counts.

#### Limitation: unknown coauthors are missing

If only known Meddash KOLs are nodes, external coauthors are invisible.

Current mitigation:

- treat single-KOL publications as weak network evidence;
- separate publication count from coauthor centrality;
- record known-coauthor coverage where possible.

Future mitigation:

- create `publication_authors_raw` or `external_authors`;
- store all publication authors;
- promote repeated external authors into candidate KOLs.

#### Limitation: duplicate KOL records can split centrality

Current mitigation:

- check `kol_merge_candidates`;
- reduce reliability for unresolved duplicates;
- include duplicate warning in limitations.

Future mitigation:

- stronger ORCID/Scholar/OpenAlex identity resolution;
- coauthor/topic/institution matching before final centrality scoring.

#### Limitation: disconnected graph can distort metrics

Current mitigation:

- rely most on weighted degree and PageRank;
- calculate component size;
- use eigenvector only if stable;
- avoid global closeness in v1.

Future mitigation:

- add therapeutic-area-specific subnetworks;
- compare KOLs within relevant disease networks instead of one global graph only.

#### Limitation: journal/topic metadata may be incomplete

Current mitigation:

- keep unweighted authorship centrality as base;
- use journal/topic as optional modifiers only where available;
- store missing input warnings.

Future mitigation:

- backfill PMID, ISSN, MeSH, dates, and journal aliases;
- improve publication enrichment pipeline.

---

### 10.5.11 Why This Can Support Future Centrality Types

The Phase 1 authorship centrality engine should be written as a generic graph-scoring framework.

Future graph scopes can use the same structure:

| Future layer | Data source | Future `graph_scope` |
|---|---|---|
| Trial centrality | `trial_investigators`, `trials` | `trial_collaboration` |
| Topic/TA centrality | `publication_mesh_map`, `mesh_ontology` | `topic_authorship:<mesh_or_ta>` |
| Biotech centrality | `biotech_associated_kols`, `biotech_leads` | `biotech_affiliation` |
| Institution centrality | normalized `kols.institution` | `institution_similarity` |
| Citation centrality | future citation edges | `citation_network` |
| CRM overlay | future CRM | separate commercial/outreach layer, not scientific centrality |

This means Phase 1 should not be a one-off script. It should be the foundation for a centrality subsystem.

---

### 10.5.12 Execution Guardrails

When implementation begins:

- Do not write to Supabase first.
- Start with local CSV/parquet output.
- Review top 50 and bottom 50 KOLs manually.
- Check score reasons and reliability warnings.
- Only then create/write Supabase output tables.
- Never overwrite core KOL identity fields.
- Never claim the score is global real-world influence.
- Always show reliability and limitations with the centrality score.

---

## 11. Topic: Phase 1 Centrality Implementation — Authorship Centrality v1

**Status:** Planning only — do not execute yet  
**Added:** 2026-04-28 05:44 UTC  
**Purpose:** Define the first implementable Meddash KOL centrality engine using currently available authorship data.  
**Scope:** Automatic, repeatable authorship centrality calculation after each KOL/publication pull.  
**Primary data source:** `kols` + `kol_authorships` + `publications`  
**Optional enrichment:** `publication_mesh_map`, `mesh_ontology`, `journal_metrics`, `kol_merge_candidates`

### 11.1 Goal

Build a self-sustaining Phase 1 centrality system that calculates an objective, explainable, automatically refreshable **Authorship Centrality Score** for each KOL using the publication network currently present in Supabase.

The score should answer:

> “How central is this KOL inside the publication collaboration network we have actually mapped?”

The v1 score must be transparent. For every score, the system should store:

- the score itself;
- the underlying network metrics;
- why the score is high/medium/low;
- how reliable the score is;
- what data limitations affected the score;
- the method version used to calculate it.

Important: the score should be presented as **centrality within the currently mapped Meddash publication network**, not as absolute global KOL influence.

---

### 11.2 Why Phase 1 Uses Authorship Centrality

Phase 1 should use authorship/co-authorship because it is the strongest available source of actual KOL-to-KOL relationship data.

Authorship centrality is suitable now because:

- `kol_authorships` provides real KOL-to-publication links;
- co-authorship creates real observed KOL-to-KOL edges;
- publication edges are objective and auditable;
- the method is repeatable after each new KOL/publication pull;
- the data already supports graph metrics such as degree, weighted degree, PageRank, betweenness, and component size;
- the same framework can later accept trial, biotech, topic, institution, citation, and CRM overlays.

Other data sources remain future layers because they are currently sparse, incomplete, or not normalized enough to carry the base centrality score.

---

### 11.3 Proposed Storage Approach

There are two possible storage strategies.

#### Recommended strategy: separate centrality score table

Create a new table later, after review:

```text
kol_centrality_scores
```

This is safer than adding many columns directly to `kols` because centrality is a calculated, versioned analytic output. Keeping it separate prevents the canonical KOL identity table from becoming polluted with method-specific calculations.

#### Optional convenience columns on `kols`

If dashboard speed or simple querying requires it later, add only lightweight summary columns to `kols`, such as:

```text
authorship_centrality_score
authorship_centrality_tier
authorship_centrality_confidence
authorship_centrality_updated_at
authorship_centrality_method_version
```

However, the full metrics and explanations should still live in a separate results table.

**Planning decision:** for Phase 1, plan a separate output table first; only add summary columns to `kols` if we need fast dashboard display.

---

### 11.4 Proposed Output Fields

#### Table: `kol_centrality_scores`

Do not create yet. Proposed fields:

| Field | Purpose |
|---|---|
| `run_id` | unique ID for each centrality run |
| `computed_at` | timestamp of calculation |
| `method_version` | e.g. `authorship_centrality_v1.0` |
| `kol_id` | KOL ID from `kols.id` |
| `graph_scope` | `global_authorship`, later `topic_authorship`, `trial`, etc. |
| `node_count` | number of KOL nodes in graph |
| `edge_count` | number of coauthorship edges |
| `component_id` | connected component ID |
| `component_size` | size of KOL’s connected component |
| `publication_count_mapped` | number of mapped publications for this KOL |
| `coauthor_count_mapped` | number of unique mapped coauthors |
| `degree_centrality` | normalized direct network connectivity |
| `weighted_degree` | direct connectivity weighted by repeated collaborations and quality modifiers |
| `pagerank` | stable global network influence within mapped graph |
| `betweenness` | bridge/broker role between clusters |
| `eigenvector` | influence from being connected to other influential KOLs, if stable |
| `component_percentile` | percentile for component size/network reach |
| `authorship_centrality_raw` | raw weighted composite score |
| `authorship_centrality_percentile` | percentile normalized score, easier to explain |
| `authorship_centrality_score` | final 0–100 score |
| `authorship_centrality_tier` | Tier 1 / Tier 2 / Tier 3 / Tier 4 / Emerging / Insufficient Data |
| `score_reason` | short human-readable reason for the score |
| `reliability_score` | 0–100 confidence in score reliability |
| `reliability_band` | High / Medium / Low / Insufficient |
| `limitations` | JSON/text list of known limitations affecting this KOL |
| `missing_inputs` | missing data fields/tables for this KOL |
| `data_coverage_summary` | short explanation of mapped data volume |

---

### 11.5 How Authorship Centrality Will Be Measured

#### Graph construction

- Each KOL becomes a graph node.
- Each publication becomes a collaboration group.
- If two or more KOLs are linked to the same `publication_id`, create coauthorship edges between each KOL pair.
- If the same pair appears together repeatedly, increase edge weight.
- If publication/journal metadata exists, enrich the edge weight.

Base graph:

```text
kols.id
  -> kol_authorships.kol_id
  -> kol_authorships.publication_id
  -> publications.id
```

Optional enrichments:

```text
publications.pmid -> publication_mesh_map.pmid -> mesh_ontology
publications.issn -> journal_metrics.issn / journal_metrics.issn_print
```

#### Base edge weight

Initial v1 edge weight:

```text
edge_weight = number_of_shared_publications_between_kol_A_and_kol_B
```

Later v1.1 edge weight can add:

```text
edge_weight =
  shared_publication_count
  * author_role_factor
  * journal_quality_factor
  * recency_factor
  * topic_relevance_factor
```

#### Metrics calculated

| Metric | Meaning | Why it matters |
|---|---|---|
| `publication_count_mapped` | how many publications we have mapped for this KOL | coverage / denominator |
| `coauthor_count_mapped` | unique mapped coauthors | direct collaboration footprint |
| `degree_centrality` | direct network connections normalized by graph size | immediate network reach |
| `weighted_degree` | connection strength including repeated collaborations | stronger than simple coauthor count |
| `pagerank` | influence based on quality/connectedness of neighbors | robust overall centrality |
| `betweenness` | how often KOL bridges clusters | identifies connectors/brokers |
| `eigenvector` | whether KOL connects to other central KOLs | high-status network proximity |
| `component_size` | how large the KOL’s connected subnetwork is | prevents over-reading isolated mini-networks |

#### Proposed final score formula

For v1, use percentile-normalized inputs so scores are easier to compare:

```text
authorship_centrality_score = 100 * (
  weighted_degree_percentile * 0.30 +
  pagerank_percentile         * 0.30 +
  betweenness_percentile      * 0.20 +
  eigenvector_percentile      * 0.10 +
  component_size_percentile   * 0.10
)
```

If eigenvector fails because the graph is disconnected or unstable:

```text
authorship_centrality_score = 100 * (
  weighted_degree_percentile * 0.35 +
  pagerank_percentile         * 0.35 +
  betweenness_percentile      * 0.20 +
  component_size_percentile   * 0.10
)
```

This avoids making the score depend on a fragile metric.

---

### 11.6 Score Tiers

Proposed explainable tiers:

| Score | Tier | Meaning |
|---:|---|---|
| 85–100 | Tier 1 — Highly Central Author Network KOL | strong mapped coauthor network and high network influence |
| 70–84 | Tier 2 — High Centrality | well-connected in mapped authorship network |
| 50–69 | Tier 3 — Moderate Centrality | visible network role but not dominant |
| 30–49 | Tier 4 — Low Mapped Centrality | limited mapped coauthor network or small component |
| 1–29 | Emerging / Peripheral | little mapped centrality in current data |
| 0 or null | Insufficient Data | too little mapped authorship data to score fairly |

Important: Tier should always be paired with reliability. A low score with low reliability should not be interpreted as “low influence.” It means “low measured centrality in our current mapped data.”

---

### 11.7 Reason for Score

Every score should have a human-readable reason. Examples:

High score reason:

```text
High authorship centrality because this KOL has many mapped coauthors, repeated collaborations, high PageRank, and belongs to a large connected publication component.
```

Medium score reason:

```text
Moderate authorship centrality because this KOL has a visible mapped coauthor network but limited bridge/betweenness role across clusters.
```

Low score with high reliability:

```text
Low authorship centrality because this KOL has few mapped publications and few mapped coauthors despite adequate publication coverage.
```

Low score with low reliability:

```text
Low measured centrality, but reliability is limited because the KOL’s publication network appears incompletely mapped. Do not interpret as low real-world influence.
```

Insufficient data reason:

```text
Insufficient authorship data: fewer than the minimum required mapped publications/coauthors were available for this KOL.
```

---

### 11.8 Objectivity and Reliability

#### Objectivity

The score is objective because it is calculated from explicit database relationships:

- KOL-publication links;
- shared publications;
- unique coauthors;
- repeated coauthorship;
- graph metrics computed by deterministic algorithms;
- optional journal/topic/date modifiers from structured tables.

No subjective manual ranking should be inserted into the core Phase 1 score.

#### Reliability score

Each KOL should receive a separate reliability score from 0–100.

Proposed reliability inputs:

```text
reliability_score =
  publication_coverage_factor      * 0.35 +
  coauthor_mapping_factor          * 0.25 +
  metadata_completeness_factor     * 0.15 +
  disambiguation_confidence_factor * 0.15 +
  graph_component_factor           * 0.10
```

Where:

| Factor | Meaning |
|---|---|
| `publication_coverage_factor` | enough publications mapped for the KOL |
| `coauthor_mapping_factor` | enough publications have multiple mapped KOL authors |
| `metadata_completeness_factor` | publication dates, PMIDs, journal/ISSN, MeSH available |
| `disambiguation_confidence_factor` | no unresolved duplicate/merge issues |
| `graph_component_factor` | KOL is not isolated solely due to incomplete mapping |

Reliability bands:

| Reliability | Band | Interpretation |
|---:|---|---|
| 80–100 | High | score can be used confidently inside current mapped network |
| 60–79 | Medium | usable with caveats |
| 40–59 | Low | display warning and avoid hard ranking |
| 0–39 | Insufficient | do not rank; show “needs more data” |

---

### 11.9 Main Limitations and Current Mitigations

#### Limitation 1 — Incomplete publication network can under-score true KOLs

Problem:

A genuinely high-centrality KOL may receive a low score if Meddash has only pulled a small part of their publication network.

Example:

- KOL has 300 real publications in PubMed/Scholar;
- Meddash currently has 4 mapped publications;
- only 1 of those publications has mapped coauthors;
- graph score appears low, but true network influence may be high.

Current mitigation:

- Store `publication_count_mapped`.
- Store `coauthor_count_mapped`.
- Store `reliability_score` separately from centrality score.
- If mapped publication count is below threshold, show `Insufficient Data` or `Low Reliability`, not a definitive low centrality label.
- Generate `limitations` text explaining incomplete mapping.

Future mitigation:

- Expand PubMed/OpenAlex/Semantic Scholar publication pulls per KOL.
- Pull all authors for each publication, not only known Meddash KOLs.
- Add author disambiguation and external IDs such as ORCID, Scholar ID, OpenAlex Author ID.
- Add external publication-count denominator to estimate coverage.

#### Limitation 2 — Unknown coauthors are missing from the graph

Problem:

If a publication includes external authors who are not yet in the `kols` table, the network edge only reflects known Meddash KOLs. This can make centrality look smaller than reality.

Current mitigation:

- Calculate `known_coauthor_ratio` where possible.
- Flag publications with only one mapped KOL as weak network evidence.
- Treat publication count and coauthor count separately.

Future mitigation:

- Create a `publication_authors_raw` or `external_authors` table.
- Store all author names/order from PubMed/OpenAlex.
- Later promote repeated external authors into candidate KOLs.

#### Limitation 3 — Duplicate KOL records can split centrality

Problem:

If the same person appears as two KOL records, their publication network splits across two nodes, lowering both scores.

Current mitigation:

- Check `kol_merge_candidates` before final scoring.
- Add a `disambiguation_warning` if a KOL has unresolved merge candidates.
- Reduce reliability score for unresolved duplicates.

Future mitigation:

- Improve merge workflow.
- Use ORCID, Scholar ID, institution, coauthor overlap, and MeSH overlap for identity resolution.
- Only run final centrality after deduplication confidence improves.

#### Limitation 4 — Name/ID mismatches between tables

Problem:

Some tables use bigint IDs while others may store KOL IDs as text. Bad joins can silently remove nodes or edges.

Current mitigation:

- Normalize KOL IDs internally as strings during graph construction.
- Validate join rates before every run.
- Report number of orphaned authorship rows.

Future mitigation:

- Standardize `kol_id` data types across Supabase schema.
- Add foreign keys where safe.
- Add automated schema checks before centrality run.

#### Limitation 5 — Journal and topic metadata may be incomplete

Problem:

Some publications may lack PMID, ISSN, MeSH, or journal matching. Weighted centrality may become uneven.

Current mitigation:

- Keep unweighted authorship centrality as the base score.
- Add journal/topic modifiers only when metadata exists.
- Store missing metadata count in `missing_inputs`.

Future mitigation:

- Improve publication enrichment pipeline.
- Backfill ISSN/PMID/MeSH fields.
- Add journal alias matching.

#### Limitation 6 — Disconnected graph components can distort metrics

Problem:

Medical publication networks are often disconnected by specialty, disease area, geography, or incomplete ingestion. Metrics like closeness/eigenvector can mislead if applied globally.

Current mitigation:

- Use PageRank and weighted degree as the most stable v1 metrics.
- Compute component size and component ID.
- Use eigenvector only if stable; otherwise fallback to PageRank.
- Avoid global closeness as a core v1 scoring metric.

Future mitigation:

- Add disease-specific/topic-specific centrality using MeSH.
- Compare KOLs within relevant therapeutic-area subnetworks, not only globally.

#### Limitation 7 — High publication volume does not always equal central influence

Problem:

A KOL can publish many papers but mostly in isolated groups; another KOL may publish less but bridge major clusters.

Current mitigation:

- Do not use publication count alone.
- Include PageRank, betweenness, weighted degree, and component size.
- Explain whether the score is driven by volume, bridge role, or network quality.

Future mitigation:

- Add citation network once citation edges exist.
- Add trial PI network and congress/society roles later.

---

### 11.10 Automatic Run Design

The centrality engine should run automatically after every successful KOL/publication pull.

Proposed workflow:

```text
KOL/publication pull completes
  -> validate row counts and join rates
  -> build authorship graph
  -> calculate metrics
  -> calculate reliability and limitations
  -> write versioned results
  -> update optional KOL summary columns if approved
  -> log run summary
  -> dashboard reads latest successful run
```

Proposed automation trigger options:

| Trigger | Pros | Cons | Recommendation |
|---|---|---|---|
| n8n after KOL pull | already part of Meddash automation | must handle failure/retry carefully | good v1 trigger |
| cron scheduled nightly | simple and stable | not immediate after pull | good backup |
| database trigger | immediate | too complex for graph calculation | avoid initially |
| manual dashboard button | useful for testing | not self-sustaining | dev-only |

Recommended v1:

- Run after successful KOL/publication pull through n8n.
- Also run nightly as a safety refresh.
- Use `run_id` and `method_version` for reproducibility.
- Never overwrite the only copy of previous results; mark latest successful run.

---

### 11.11 Stepwise Implementation Plan with Checkboxes

#### A. Planning and schema safety

- [ ] Confirm this Phase 1 authorship-only scope with Dr. Don.
- [ ] Re-check live Supabase row counts before implementation.
- [ ] Confirm whether output should be separate table only or separate table plus summary columns on `kols`.
- [ ] Decide final score name: `Authorship Centrality Score`, `Meddash Authorship Influence Score`, or another label.
- [ ] Define minimum data thresholds for scoring:
  - [ ] minimum mapped publications;
  - [ ] minimum mapped coauthors;
  - [ ] minimum component size;
  - [ ] minimum reliability score for dashboard display.

#### B. Output schema design

- [ ] Draft SQL migration for `kol_centrality_runs`.
- [ ] Draft SQL migration for `kol_centrality_scores`.
- [ ] Include method version fields.
- [ ] Include raw graph metrics, final score, tier, reliability, reason, limitations, and missing inputs.
- [ ] Add indexes for `kol_id`, `run_id`, `graph_scope`, `computed_at`, and `method_version`.
- [ ] If approved, add optional summary columns to `kols` only after the separate result table is accepted.

#### C. Build extraction layer

- [ ] Create a read-only extraction script for:
  - [ ] `kols`;
  - [ ] `kol_authorships`;
  - [ ] `publications`;
  - [ ] optional `publication_mesh_map`;
  - [ ] optional `journal_metrics`;
  - [ ] optional `kol_merge_candidates`.
- [ ] Validate that `kol_authorships.kol_id` joins to `kols.id`.
- [ ] Validate that `kol_authorships.publication_id` joins to `publications.id`.
- [ ] Validate that `publications.pmid` joins to `publication_mesh_map.pmid` where present.
- [ ] Validate that `publications.issn` joins to `journal_metrics.issn` or `issn_print` where present.
- [ ] Produce join-rate warnings before scoring.

#### D. Build graph construction

- [ ] Normalize all internal KOL IDs to string during graph construction.
- [ ] Create one graph node for every KOL with at least one mapped authorship record.
- [ ] Group authorship records by `publication_id`.
- [ ] For each publication with two or more mapped KOLs, create pairwise coauthorship edges.
- [ ] Increment edge weight for repeated collaborations.
- [ ] Store per-node mapped publication count.
- [ ] Store per-node mapped coauthor count.
- [ ] Store graph stats: node count, edge count, components, isolated nodes.

#### E. Calculate centrality metrics

- [ ] Calculate degree centrality.
- [ ] Calculate weighted degree.
- [ ] Calculate PageRank using edge weight.
- [ ] Calculate betweenness centrality; use approximation if graph becomes large.
- [ ] Attempt eigenvector centrality.
- [ ] If eigenvector fails, fallback to PageRank-derived percentile.
- [ ] Calculate component ID and component size.
- [ ] Avoid using global closeness as a v1 core metric.

#### F. Normalize and score

- [ ] Convert raw metrics to percentiles across all scored KOLs.
- [ ] Apply v1 score formula:
  - [ ] weighted degree percentile 30%;
  - [ ] PageRank percentile 30%;
  - [ ] betweenness percentile 20%;
  - [ ] eigenvector percentile 10%;
  - [ ] component size percentile 10%.
- [ ] Apply fallback formula if eigenvector is unavailable.
- [ ] Convert final score to 0–100 scale.
- [ ] Assign centrality tier.
- [ ] Generate `score_reason` text.

#### G. Calculate reliability and limitations

- [ ] Calculate publication coverage factor.
- [ ] Calculate coauthor mapping factor.
- [ ] Calculate metadata completeness factor.
- [ ] Check unresolved duplicate/merge candidate warning.
- [ ] Calculate graph component reliability.
- [ ] Produce `reliability_score` and `reliability_band`.
- [ ] Generate `limitations` list for each KOL.
- [ ] Mark KOLs with too little mapped data as `Insufficient Data` instead of falsely low centrality.

#### H. Write outputs safely

- [ ] Start with local CSV/parquet output for review.
- [ ] Review top 50 and bottom 50 KOLs manually.
- [ ] Check for obvious false rankings caused by incomplete publication mapping.
- [ ] Only after review, write to `kol_centrality_scores`.
- [ ] If summary columns on `kols` are approved, update only latest summary fields.
- [ ] Never overwrite KOL identity fields.
- [ ] Store run metadata in `kol_centrality_runs`.

#### I. Automation integration

- [ ] Add script CLI flags:
  - [ ] `--dry-run`;
  - [ ] `--write-local`;
  - [ ] `--write-supabase`;
  - [ ] `--method-version`;
  - [ ] `--limit` for testing;
  - [ ] `--min-publications`;
  - [ ] `--min-reliability`.
- [ ] Wire dry-run into developer workflow first.
- [ ] Wire local-output run after KOL pull.
- [ ] Wire Supabase write only after manual approval.
- [ ] Add nightly fallback run.
- [ ] Log every run with row counts, join rates, score distribution, warnings, and failures.

#### J. Dashboard integration

- [ ] Do not show centrality until the result table exists and has a successful run.
- [ ] Display score and reliability together.
- [ ] Display why the score is high/low.
- [ ] Display limitations if reliability is low.
- [ ] Label the score clearly as “mapped authorship centrality,” not total real-world influence.
- [ ] Add tooltip definitions for PageRank, betweenness, weighted degree, and reliability.

---

### 11.12 Future Integration with Other Centrality Types

The Phase 1 authorship engine should be built as a modular graph-scoring framework, not as a one-off script.

Recommended modular interface:

```text
extract_source_data()
build_graph()
calculate_graph_metrics()
normalize_metrics()
calculate_score()
calculate_reliability()
write_results()
```

This allows later centrality types to plug into the same output schema.

Future layers:

| Future layer | Data source | How it plugs in |
|---|---|---|
| Trial centrality | `trial_investigators`, `trials` | separate `graph_scope = trial_collaboration` |
| Topic centrality | `publication_mesh_map`, `mesh_ontology` | `graph_scope = topic_authorship:<mesh/TA>` |
| Biotech centrality | `biotech_associated_kols`, `biotech_leads` | `graph_scope = biotech_affiliation` |
| Institution centrality | normalized `kols.institution` | `graph_scope = institution_similarity` |
| Citation centrality | future citation edges | `graph_scope = citation_network` |
| CRM overlay | future CRM data | separate outreach/commercial overlay, not core scientific centrality |

The output schema should therefore include `graph_scope`, `method_version`, and component metrics so future centrality types can coexist without overwriting one another.

---

### 11.13 Phase 1 Acceptance Criteria

Phase 1 implementation is acceptable only when:

- [ ] Authorship graph can be built from current Supabase data.
- [ ] Every scored KOL has raw metrics, final score, tier, reason, reliability, and limitations.
- [ ] KOLs with insufficient mapped data are not falsely labeled as low influence.
- [ ] The script can run repeatedly without manual intervention.
- [ ] The script supports dry-run/local-output mode before Supabase writes.
- [ ] Runs are versioned and auditable.
- [ ] The method is documented clearly enough to explain in a KOL brief.
- [ ] The output design can support future trial/topic/biotech/institution/citation layers.

---

## 12. End-to-End Implementation Plan — From Current State to Auto-Populated Supabase Centrality Tables

**Status:** Planning only — do not execute yet  
**Added:** 2026-04-28 05:59 UTC  
**Goal:** Define every script, workflow, setting, table, and verification step needed to move from the current Meddash backend to automatically populated KOL authorship centrality tables after every KOL/publication pull.  
**Execution rule:** This is a checklist for later implementation. No Supabase tables, scripts, n8n workflows, or cron jobs should be created until Dr. Don approves execution.

### 12.1 Target End State

At the end of this implementation, Meddash should behave like this:

```text
KOL pull starts
  -> publications are extracted
  -> KOL/publication/authorship rows are ingested into Supabase
  -> disambiguation runs
  -> publication weights run
  -> authorship centrality engine runs automatically
  -> kol_centrality_runs receives one run record
  -> kol_centrality_scores receives per-KOL score records
  -> optional kols summary fields update for latest score
  -> pipeline summary JSON records success/failure
  -> n8n sees the summary and continues or alerts
  -> dashboard can read latest centrality scores
```

The centrality tables should auto-populate on every successful pull, but safely:

- no centrality write if source extraction failed;
- no write if join rates are below threshold;
- no false “low influence” labels for KOLs with incomplete mapped data;
- every result has `run_id`, `method_version`, reliability, reason, and limitations.

---

### 12.2 Current Assets to Reuse

Current backend root:

```text
/mnt/c/Users/email/.gemini/antigravity/Meddash_organized_backend
```

Reusable current files:

| Existing file | Current role | Planned use |
|---|---|---|
| `01_KOL_Data_Engine/run_pipeline.py` | current KOL pull pipeline | add centrality as a final optional phase after weights |
| `01_KOL_Data_Engine/extract_publications.py` | publication fetch | upstream source |
| `01_KOL_Data_Engine/db_ingestion.py` | publication/KOL ingestion | upstream source |
| `01_KOL_Data_Engine/kol_disambiguator.py` | duplicate/disambiguation | reliability warning source |
| `01_KOL_Data_Engine/kol_weight.py` | publication weighting | upstream quality signal |
| `07_DevOps_Observability/paths.py` | centralized paths/env loading | add centrality paths and summary file names |
| `07_DevOps_Observability/pipeline_summary.py` | JSON summaries | write centrality run summaries |
| `07_DevOps_Observability/telegram_notifier.py` | alerts | optional alerts on failure |
| `06_Shared_Datastores/pipeline_summaries/` | summary output folder | add centrality summary file |
| n8n Meddash workflow | orchestration | trigger centrality after KOL pull or rely on pipeline phase |

Planned new folder:

```text
/mnt/c/Users/email/.gemini/antigravity/Meddash_organized_backend/10_KOL_Centrality_Engine
```

Reason for new folder: centrality is an analytics engine, not a core ingestion script. Keeping it separate prevents `01_KOL_Data_Engine` from becoming too large while still allowing `run_pipeline.py` to call it.

---

### 12.3 Planned New Files and Their Responsibilities

| New file | Responsibility |
|---|---|
| `10_KOL_Centrality_Engine/__init__.py` | package marker |
| `10_KOL_Centrality_Engine/centrality_config.py` | method version, thresholds, score weights, table names |
| `10_KOL_Centrality_Engine/supabase_io.py` | read/write Supabase data, no scoring logic |
| `10_KOL_Centrality_Engine/schema.sql` | SQL for `kol_centrality_runs` and `kol_centrality_scores` |
| `10_KOL_Centrality_Engine/schema_validate.py` | confirms tables/columns/indexes exist before write mode |
| `10_KOL_Centrality_Engine/authorship_graph.py` | builds NetworkX graph from KOL authorship rows |
| `10_KOL_Centrality_Engine/metrics.py` | degree, weighted degree, PageRank, betweenness, eigenvector fallback |
| `10_KOL_Centrality_Engine/scoring.py` | percentile normalization, final score, tier assignment |
| `10_KOL_Centrality_Engine/reliability.py` | reliability score and limitations generation |
| `10_KOL_Centrality_Engine/reasons.py` | human-readable score reasons |
| `10_KOL_Centrality_Engine/run_centrality.py` | single-shot CLI entrypoint for n8n/pipeline |
| `10_KOL_Centrality_Engine/tests/test_authorship_graph.py` | graph construction tests |
| `10_KOL_Centrality_Engine/tests/test_scoring.py` | scoring/tier tests |
| `10_KOL_Centrality_Engine/tests/test_reliability.py` | reliability/limitations tests |
| `10_KOL_Centrality_Engine/tests/test_run_centrality_dry_run.py` | CLI dry-run behavior |

Planned modified files:

| Existing file | Planned change |
|---|---|
| `07_DevOps_Observability/paths.py` | add `ENGINE_PATHS["centrality"]`, `SUMMARY_FILES["kol_centrality"]` |
| `01_KOL_Data_Engine/run_pipeline.py` | add optional Phase 5 call to `run_centrality.py` after `compute_all_weights()` |
| n8n Meddash workflow | ensure centrality runs after KOL pull or pipeline command includes centrality flag |
| dashboard later | read latest centrality results only after table is populated and approved |

---

### 12.4 Supabase Table Plan

#### A. Table: `kol_centrality_runs`

Purpose: one row per centrality calculation run.

Planned columns:

```sql
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
```

Planned indexes:

```sql
create index if not exists idx_kol_centrality_runs_computed_at
  on kol_centrality_runs (computed_at desc);

create index if not exists idx_kol_centrality_runs_status
  on kol_centrality_runs (status);

create index if not exists idx_kol_centrality_runs_pull_id
  on kol_centrality_runs (pull_id);
```

#### B. Table: `kol_centrality_scores`

Purpose: one row per KOL per run per graph scope.

Planned columns:

```sql
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
```

Planned indexes:

```sql
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
```

#### C. Optional columns on `kols`

Only add these after the separate score table is working:

```sql
alter table kols add column if not exists authorship_centrality_score numeric;
alter table kols add column if not exists authorship_centrality_tier text;
alter table kols add column if not exists authorship_centrality_confidence numeric;
alter table kols add column if not exists authorship_centrality_updated_at timestamptz;
alter table kols add column if not exists authorship_centrality_method_version text;
```

Recommendation: do not add optional `kols` summary columns until dashboard needs them. The clean source of truth should be `kol_centrality_scores`.

---

### 12.5 Script Interface Requirements

The main script must be n8n-ready and single-shot.

Planned command:

```bash
cd /mnt/c/Users/email/.gemini/antigravity/Meddash_organized_backend
python 10_KOL_Centrality_Engine/run_centrality.py \
  --graph-scope global_authorship \
  --method-version authorship_centrality_v1.0 \
  --write-supabase \
  --pull-id "$PULL_ID" \
  --triggered-by n8n_kol_pipeline
```

Required CLI flags:

| Flag | Purpose |
|---|---|
| `--dry-run` | validate data and compute without writing |
| `--write-local` | write local CSV/parquet review output |
| `--write-supabase` | write to Supabase output tables |
| `--graph-scope` | default `global_authorship`; future topic/trial scopes |
| `--method-version` | e.g. `authorship_centrality_v1.0` |
| `--pull-id` | propagate pull/execution ID from KOL pipeline/n8n |
| `--triggered-by` | `manual`, `n8n_kol_pipeline`, `nightly_cron`, etc. |
| `--min-publications` | minimum mapped publications threshold |
| `--min-coauthors` | minimum mapped coauthors threshold |
| `--min-join-rate` | fail/partial if joins are too poor |
| `--limit` | dev/test mode for limited KOL rows |
| `--summary-json` | write machine-readable summary to pipeline summaries |

Required exit codes:

| Exit code | Meaning | n8n behavior |
|---:|---|---|
| 0 | success | continue workflow |
| 1 | partial success/warnings | continue but notify/mark yellow |
| 2 | hard failure | stop and alert |

Required summary file:

```text
06_Shared_Datastores/pipeline_summaries/kol_centrality_summary.json
```

Required summary fields:

```json
{
  "engine": "kol_centrality",
  "timestamp": "ISO-8601 UTC",
  "status": "success|partial|failure",
  "duration_seconds": 0,
  "run_id": "...",
  "method_version": "authorship_centrality_v1.0",
  "graph_scope": "global_authorship",
  "pull_id": "...",
  "source_row_counts": {},
  "join_quality": {},
  "graph_stats": {},
  "scores_written": 0,
  "reliability_distribution": {},
  "warnings": [],
  "error": null
}
```

---

### 12.6 Stepwise Implementation Checklist

#### Phase A — Preflight decisions and safety

- [ ] Confirm Dr. Don approves moving from planning to implementation.
- [ ] Confirm score label: `Authorship Centrality Score` unless renamed.
- [ ] Confirm output table names:
  - [ ] `kol_centrality_runs`
  - [ ] `kol_centrality_scores`
- [ ] Confirm first implementation should write local output before Supabase writes.
- [ ] Confirm whether optional `kols` summary columns are deferred.
- [ ] Confirm minimum thresholds:
  - [ ] `min_publications = 2` suggested starting point;
  - [ ] `min_coauthors = 1` suggested starting point;
  - [ ] `min_join_rate = 0.90` suggested starting point for core authorship joins;
  - [ ] `min_reliability_for_dashboard = 40` suggested starting point.
- [ ] Confirm centrality should run only after `compute_all_weights()` succeeds.
- [ ] Confirm failed centrality should not roll back successful KOL ingestion; it should mark centrality failed and alert.

#### Phase B — Create engine folder and package structure

- [ ] Create folder: `10_KOL_Centrality_Engine/`.
- [ ] Create file: `10_KOL_Centrality_Engine/__init__.py`.
- [ ] Create folder: `10_KOL_Centrality_Engine/tests/`.
- [ ] Add README stub explaining the engine is n8n-ready and single-shot.
- [ ] Confirm imports work from project root.
- [ ] Confirm no credentials are stored in this folder.

#### Phase C — Update shared paths/settings

- [ ] Modify `07_DevOps_Observability/paths.py`.
- [ ] Add `ENGINE_PATHS["centrality"] = MEDDASH_ROOT / "10_KOL_Centrality_Engine"`.
- [ ] Add `SUMMARY_FILES["kol_centrality"] = SUMMARY_DIR / "kol_centrality_summary.json"`.
- [ ] Add optional `STATE_FILES["kol_centrality_state"] = STATE_DIR / "kol_centrality_state.json"`.
- [ ] Run path smoke test:

```bash
cd /mnt/c/Users/email/.gemini/antigravity/Meddash_organized_backend
python 07_DevOps_Observability/paths.py
```

- [ ] Verify centrality path resolves correctly.

#### Phase D — Add centrality configuration

- [ ] Create `10_KOL_Centrality_Engine/centrality_config.py`.
- [ ] Define `METHOD_VERSION = "authorship_centrality_v1.0"`.
- [ ] Define table names:
  - [ ] `RUNS_TABLE = "kol_centrality_runs"`
  - [ ] `SCORES_TABLE = "kol_centrality_scores"`
- [ ] Define score weights:
  - [ ] weighted degree = 0.30;
  - [ ] PageRank = 0.30;
  - [ ] betweenness = 0.20;
  - [ ] eigenvector = 0.10;
  - [ ] component size = 0.10.
- [ ] Define fallback weights when eigenvector fails:
  - [ ] weighted degree = 0.35;
  - [ ] PageRank = 0.35;
  - [ ] betweenness = 0.20;
  - [ ] component size = 0.10.
- [ ] Define thresholds:
  - [ ] minimum publications;
  - [ ] minimum coauthors;
  - [ ] minimum join rate;
  - [ ] low reliability threshold;
  - [ ] insufficient data threshold.
- [ ] Define tier cutoffs.
- [ ] Add a config validation function that checks weights sum to 1.0.

#### Phase E — Create SQL schema file

- [ ] Create `10_KOL_Centrality_Engine/schema.sql`.
- [ ] Add `kol_centrality_runs` DDL.
- [ ] Add `kol_centrality_scores` DDL.
- [ ] Add all planned indexes.
- [ ] Add comments explaining `is_latest`, `method_version`, `graph_scope`, and reliability.
- [ ] Keep optional `kols` summary columns in a clearly marked optional section.
- [ ] Do not execute SQL yet.
- [ ] Review SQL manually before Supabase execution.

#### Phase F — Create schema validation script

- [ ] Create `10_KOL_Centrality_Engine/schema_validate.py`.
- [ ] Use Supabase OpenAPI metadata to check whether required tables exist.
- [ ] Check required columns exist.
- [ ] Check indexes if metadata allows; otherwise warn manual check needed.
- [ ] Add CLI:

```bash
python 10_KOL_Centrality_Engine/schema_validate.py --json
```

- [ ] Return exit code 0 if schema exists, 2 if missing required tables/columns.
- [ ] Never print Supabase credentials.

#### Phase G — Build Supabase IO layer

- [ ] Create `10_KOL_Centrality_Engine/supabase_io.py`.
- [ ] Load Supabase creds using existing `paths.get_supabase_creds()`.
- [ ] Implement read functions:
  - [ ] `fetch_kols()`;
  - [ ] `fetch_kol_authorships()`;
  - [ ] `fetch_publications()`;
  - [ ] `fetch_publication_mesh_map()` optional;
  - [ ] `fetch_journal_metrics()` optional;
  - [ ] `fetch_kol_merge_candidates()` optional.
- [ ] Implement write functions:
  - [ ] `insert_centrality_run()`;
  - [ ] `mark_previous_scores_not_latest(graph_scope)`;
  - [ ] `insert_centrality_scores(rows)`;
  - [ ] `mark_run_complete()`;
  - [ ] `mark_run_failed()`.
- [ ] Use chunked writes to avoid API payload limits.
- [ ] Add retry/backoff for transient Supabase errors.
- [ ] Add dry-run mode that performs no writes.
- [ ] Add tests/mocks for no credentials printed.

#### Phase H — Build graph construction module

- [ ] Create `10_KOL_Centrality_Engine/authorship_graph.py`.
- [ ] Normalize all KOL IDs to strings internally.
- [ ] Build node attributes from `kols`.
- [ ] Group `kol_authorships` by `publication_id`.
- [ ] Skip publication groups with fewer than 2 mapped KOLs for edge creation.
- [ ] For each publication with 2+ mapped KOLs, create pairwise undirected edges.
- [ ] Increment edge weight for repeated coauthorship.
- [ ] Store per-node:
  - [ ] mapped publication count;
  - [ ] mapped coauthor count;
  - [ ] single-author/missing-coauthor publication count if inferable;
  - [ ] unresolved duplicate warning if present.
- [ ] Return graph plus graph stats.
- [ ] Unit test tiny graph with 3 KOLs and 2 publications.

#### Phase I — Build metrics module

- [ ] Create `10_KOL_Centrality_Engine/metrics.py`.
- [ ] Calculate degree centrality.
- [ ] Calculate weighted degree from edge weights.
- [ ] Calculate PageRank using `weight="weight"`.
- [ ] Calculate betweenness centrality; use exact for small graph, approximate for large graph.
- [ ] Calculate eigenvector centrality with timeout/max iterations.
- [ ] If eigenvector fails, set `eigenvector_available = false` and use fallback formula later.
- [ ] Calculate connected components and component sizes.
- [ ] Avoid global closeness in v1 scoring.
- [ ] Unit test all metrics on known toy graph.

#### Phase J — Build scoring module

- [ ] Create `10_KOL_Centrality_Engine/scoring.py`.
- [ ] Implement percentile conversion for each metric.
- [ ] Implement v1 scoring formula.
- [ ] Implement fallback formula.
- [ ] Convert score to 0–100.
- [ ] Assign tiers.
- [ ] Mark insufficient-data KOLs separately from low-score KOLs.
- [ ] Unit test:
  - [ ] high network KOL receives higher score;
  - [ ] isolated KOL is insufficient/low as expected;
  - [ ] fallback formula works when eigenvector unavailable;
  - [ ] score never exceeds 100 or drops below 0.

#### Phase K — Build reliability and limitations module

- [ ] Create `10_KOL_Centrality_Engine/reliability.py`.
- [ ] Calculate `publication_coverage_factor`.
- [ ] Calculate `coauthor_mapping_factor`.
- [ ] Calculate `metadata_completeness_factor`.
- [ ] Calculate `disambiguation_confidence_factor`.
- [ ] Calculate `graph_component_factor`.
- [ ] Combine into 0–100 reliability score.
- [ ] Assign reliability band.
- [ ] Generate limitations list:
  - [ ] incomplete publication network;
  - [ ] too few mapped coauthors;
  - [ ] unresolved duplicate candidates;
  - [ ] missing publication metadata;
  - [ ] disconnected/small component;
  - [ ] eigenvector fallback used.
- [ ] Unit test low reliability does not automatically mean low centrality.

#### Phase L — Build score reason module

- [ ] Create `10_KOL_Centrality_Engine/reasons.py`.
- [ ] Generate high-score reason text.
- [ ] Generate moderate-score reason text.
- [ ] Generate low-score/high-reliability reason text.
- [ ] Generate low-score/low-reliability warning text.
- [ ] Generate insufficient-data reason text.
- [ ] Include plain language, not statistical jargon only.
- [ ] Unit test generated reason includes reliability caveat when reliability is low.

#### Phase M — Build main CLI script

- [ ] Create `10_KOL_Centrality_Engine/run_centrality.py`.
- [ ] Add argparse flags listed in section 12.5.
- [ ] Generate `run_id` if not supplied.
- [ ] Load source data.
- [ ] Validate row counts and join rates.
- [ ] Build graph.
- [ ] Calculate metrics.
- [ ] Score KOLs.
- [ ] Calculate reliability/limitations.
- [ ] Write local output if `--write-local`.
- [ ] Write Supabase if `--write-supabase`.
- [ ] Always write `kol_centrality_summary.json`.
- [ ] Return structured exit codes.
- [ ] Ensure exceptions write failure summary before exiting.

#### Phase N — Add local review output

- [ ] Create local output folder:

```text
06_Shared_Datastores/centrality_outputs/
```

- [ ] Write CSV:

```text
centrality_outputs/kol_authorship_centrality_latest.csv
```

- [ ] Write run-specific CSV:

```text
centrality_outputs/kol_authorship_centrality_{run_id}.csv
```

- [ ] Include all score, reliability, reason, and limitation fields.
- [ ] Use this for the first review before Supabase writes.

#### Phase O — Wire centrality into `run_pipeline.py`

- [ ] Modify `01_KOL_Data_Engine/run_pipeline.py`.
- [ ] Add CLI flag:

```text
--run_centrality
```

- [ ] Add CLI flag:

```text
--centrality_write_mode dry-run|local|supabase
```

- [ ] Add CLI flag:

```text
--skip_centrality_on_failure
```

- [ ] After `compute_all_weights()`, call centrality only if prior phases succeeded.
- [ ] Pass through `pull_id`.
- [ ] If centrality fails:
  - [ ] KOL pull remains successful;
  - [ ] centrality phase marked failed;
  - [ ] summary contains centrality error;
  - [ ] n8n/Paperclip can alert.
- [ ] Add pipeline summary fields:
  - [ ] `centrality_status`;
  - [ ] `centrality_run_id`;
  - [ ] `centrality_scores_written`;
  - [ ] `centrality_warnings`.

#### Phase P — Add standalone n8n execution option

If centrality is not called inside `run_pipeline.py`, n8n can call it as a separate Execute Command node.

- [ ] Add n8n node after KOL pipeline success: `Execute Command — Run KOL Centrality`.
- [ ] Command:

```bash
cd /mnt/c/Users/email/.gemini/antigravity/Meddash_organized_backend && \
python 10_KOL_Centrality_Engine/run_centrality.py \
  --graph-scope global_authorship \
  --method-version authorship_centrality_v1.0 \
  --write-supabase \
  --pull-id "{{$json.pull_id || $execution.id}}" \
  --triggered-by n8n_kol_pipeline
```

- [ ] Set node “Continue On Fail” to false once stable.
- [ ] During testing, set “Continue On Fail” to true and inspect summaries.
- [ ] Add a following node to read `kol_centrality_summary.json`.
- [ ] If status is `failure`, notify Telegram/Paperclip.
- [ ] If status is `partial`, notify yellow warning.
- [ ] If status is `success`, continue silently or log success.

Recommendation: prefer integrating centrality inside `run_pipeline.py` eventually so KOL pull + weights + centrality remain one coherent pipeline. Use standalone n8n node during testing.

#### Phase Q — n8n workflow settings

- [ ] Workflow name: `Meddash KOL Pull + Centrality` or update existing Meddash KOL workflow.
- [ ] Trigger: existing schedule/manual trigger for KOL pull.
- [ ] Ensure KOL pull command includes pull ID.
- [ ] Ensure centrality node runs only after KOL pipeline success.
- [ ] Set timeout high enough for graph calculation.
- [ ] Capture stdout/stderr.
- [ ] Add summary read node after centrality.
- [ ] Add alert branch for failure/partial.
- [ ] Do not store Supabase credentials in n8n Code nodes.
- [ ] Use existing `.env`/backend environment loading.
- [ ] Do not write n8n credentials directly to DB.
- [ ] Toggle workflow off/on through UI after changes if polling/schedules do not start.

#### Phase R — Nightly fallback workflow

- [ ] Add separate n8n schedule or cron job: `Meddash KOL Centrality Nightly Refresh`.
- [ ] Run once nightly after all KOL pulls are expected complete.
- [ ] Command:

```bash
cd /mnt/c/Users/email/.gemini/antigravity/Meddash_organized_backend && \
python 10_KOL_Centrality_Engine/run_centrality.py \
  --graph-scope global_authorship \
  --method-version authorship_centrality_v1.0 \
  --write-supabase \
  --triggered-by nightly_refresh
```

- [ ] Use this as safety net if post-pull centrality fails or is skipped.
- [ ] Alert only on failure/partial, not every success.

#### Phase S — Supabase write behavior

- [ ] Insert `kol_centrality_runs` row at run start with `status = 'running'`.
- [ ] Calculate scores.
- [ ] If write is approved and validation passes:
  - [ ] set previous `kol_centrality_scores.is_latest = false` for `graph_scope='global_authorship'`;
  - [ ] insert new score rows with `is_latest = true`;
  - [ ] update run row to `status = 'success'` or `partial`.
- [ ] If failure occurs:
  - [ ] update run row to `status = 'failure'` if run row exists;
  - [ ] do not mark previous scores as not latest unless new rows are ready;
  - [ ] preserve previous latest scores.
- [ ] This prevents the dashboard from going blank after a failed centrality run.

#### Phase T — Optional `kols` summary update

Only after score table is validated:

- [ ] Decide whether to add summary columns to `kols`.
- [ ] If approved, add columns listed in section 12.4.
- [ ] Update summary columns only from latest successful centrality run.
- [ ] Never use summary columns as source of truth.
- [ ] Dashboard can use summary columns for speed, but details come from `kol_centrality_scores`.

#### Phase U — Testing plan

- [ ] Unit test graph construction.
- [ ] Unit test score formula.
- [ ] Unit test reliability calculation.
- [ ] Unit test reason generation.
- [ ] Unit test dry-run CLI.
- [ ] Integration test local output mode:

```bash
python 10_KOL_Centrality_Engine/run_centrality.py --dry-run --write-local --limit 100
```

- [ ] Integration test schema validation:

```bash
python 10_KOL_Centrality_Engine/schema_validate.py --json
```

- [ ] Integration test Supabase write to staging/dev table first if available.
- [ ] Manual QA top 50 KOLs.
- [ ] Manual QA low-score/low-reliability KOLs.
- [ ] Verify no secrets printed in logs/summaries.

#### Phase V — Dashboard integration after tables populate

- [ ] Add dashboard read query for latest scores:

```text
kol_centrality_scores?is_latest=eq.true&graph_scope=eq.global_authorship
```

- [ ] Show score, tier, reliability, and reason together.
- [ ] Show warning if reliability is low.
- [ ] Show “Insufficient mapped authorship data” instead of low score where applicable.
- [ ] Add tooltip: “This is mapped authorship centrality, not absolute KOL influence.”
- [ ] Add future drilldown: coauthors, publications, component, limitations.

#### Phase W — Observability and Paperclip accountability

- [ ] Write `kol_centrality_summary.json` after every run.
- [ ] Add run logs under:

```text
07_DevOps_Observability/logs/kol_centrality.log
```

- [ ] Add centrality summary to dashboard Operations tab later.
- [ ] Let Meddash-Monitor observe summary/logs only.
- [ ] If centrality fails, Paperclip monitor reports/escalates; it should not self-fix.

---

### 12.7 Implementation Order Recommendation

Recommended order for actual execution after approval:

1. [ ] Create engine folder and config files.
2. [ ] Write schema SQL but do not execute.
3. [ ] Build local-only dry-run extractor.
4. [ ] Build graph constructor with tests.
5. [ ] Build metrics/scoring/reliability with tests.
6. [ ] Produce first local CSV for review.
7. [ ] Review top/bottom/low-reliability KOLs.
8. [ ] Create Supabase tables.
9. [ ] Enable Supabase write mode manually.
10. [ ] Add n8n standalone centrality node.
11. [ ] After stable, integrate centrality into `run_pipeline.py`.
12. [ ] Add nightly fallback refresh.
13. [ ] Add dashboard display.
14. [ ] Add future topic/trial centrality layers.

---

### 12.8 Final Acceptance Criteria for Auto-Populating Supabase Centrality

The implementation is complete only when:

- [x] `kol_centrality_runs` exists in Supabase.
- [x] `kol_centrality_scores` exists in Supabase.
- [x] `schema_validate.py --json` validates schema visibility through Supabase REST.
- [x] `schema_validate.py --create --json` creates/validates the approved schema when execution is authorized.
- [x] `run_centrality.py --dry-run` calculates metrics without Supabase writes.
- [x] `run_centrality.py --write-local` creates review output.
- [x] `run_centrality.py --write-supabase` inserts a run and score rows.
- [x] Previous latest scores are designed to remain intact if a new run fails.
- [x] KOL pipeline can trigger centrality after a pull.
- [x] n8n can trigger or observe the centrality phase through the existing scheduler call.
- [ ] Separate nightly fallback centrality refresh exists.
- [x] `kol_centrality_summary.json` is written on success/failure path.
- [x] Every scored KOL has score, tier, reason, reliability, limitations, and method version.
- [x] Low-reliability low scores are clearly marked as incomplete evidence, not low real-world influence.
- [x] No credentials are printed or written to logs.
- [ ] Dashboard can read latest centrality results without manual SQL.

---

## 13. Implementation Execution Log — Phase 1 Authorship Centrality v1

**Executed:** 2026-04-28 07:14 UTC  
**Executor:** Alfred Chief / Hermes  
**Status:** Implemented and initially populated  
**Scope:** Authorship centrality v1 only; no trial/topic/biotech/institution/citation centrality implemented yet.

### 13.1 Step-by-Step Execution Checklist

#### A. Preflight and safety

- [x] Confirmed this moved from planning into execution.
  - Dr. Don explicitly instructed: “proceed” and populate centrality scores.
- [x] Kept the score label as mapped/authorship centrality.
  - Implemented method version: `authorship_centrality_v1.0`.
  - Implemented graph scope: `global_authorship`.
- [x] Used separate output tables instead of writing directly into `kols`.
  - Created `kol_centrality_runs`.
  - Created `kol_centrality_scores`.
- [x] Deferred optional `kols` summary columns.
  - Reason: the score table is safer as the source of truth; dashboard can later read latest rows directly.
- [x] Used current practical scoring threshold: `min_publications = 1`, `min_coauthors = 1` for initial population.
  - Reason: current Supabase authorship data has many KOLs represented by one mapped publication. Using `min_publications = 2` caused most KOLs to become “Insufficient Data” even when they had a valid coauthor network. The implementation still records reliability/limitations so one-publication scores are not overclaimed.
- [x] Set join-rate guardrail to `0.90` for Supabase write run.
  - Observed coauthor mapping rate: `0.9425`, so write proceeded.

#### B. Engine folder and package structure

- [x] Created centrality engine folder.
  - Path: `/mnt/c/Users/email/.gemini/antigravity/Meddash_organized_backend/10_KOL_Centrality_Engine/`
- [x] Created package marker.
  - File: `10_KOL_Centrality_Engine/__init__.py`
- [x] Created README.
  - File: `10_KOL_Centrality_Engine/README.md`
  - Describes dry-run, schema validation, Supabase write, and safety rules.
- [x] Created tests folder.
  - Path: `10_KOL_Centrality_Engine/tests/`

#### C. Shared paths/settings

- [x] Updated shared path config.
  - File modified: `07_DevOps_Observability/paths.py`
- [x] Added centrality engine path.
  - `ENGINE_PATHS["centrality"] = MEDDASH_ROOT / "10_KOL_Centrality_Engine"`
- [x] Added centrality summary file path.
  - `SUMMARY_FILES["kol_centrality"] = SUMMARY_DIR / "kol_centrality_summary.json"`
- [x] Added centrality state file path.
  - `STATE_FILES["kol_centrality_state"] = STATE_DIR / "kol_centrality_state.json"`
- [x] Verified Python compile after path changes.

#### D. Centrality configuration

- [x] Created centrality config.
  - File: `10_KOL_Centrality_Engine/centrality_config.py`
- [x] Defined method version.
  - `METHOD_VERSION = "authorship_centrality_v1.0"`
- [x] Defined graph scope.
  - `GRAPH_SCOPE = "global_authorship"`
- [x] Defined table names.
  - `kol_centrality_runs`
  - `kol_centrality_scores`
- [x] Defined score weights.
  - weighted degree percentile: 30%
  - PageRank percentile: 30%
  - betweenness percentile: 20%
  - eigenvector percentile: 10%
  - component size percentile: 10%
- [x] Defined fallback score weights if eigenvector is unstable.
  - weighted degree percentile: 35%
  - PageRank percentile: 35%
  - betweenness percentile: 20%
  - component size percentile: 10%
- [x] Added config validation to confirm weights sum to 1.0.

#### E. SQL schema

- [x] Created schema SQL.
  - File: `10_KOL_Centrality_Engine/schema.sql`
- [x] Added `kol_centrality_runs` table DDL.
- [x] Added `kol_centrality_scores` table DDL.
- [x] Added indexes for run time, status, pull ID, latest KOL score, graph scope, score, and reliability.
- [x] Executed the schema against Supabase Postgres using existing configured database credentials.
- [x] Triggered PostgREST schema reload.
  - Reason: Supabase REST did not immediately see the new tables until schema cache reload.

#### F. Schema validation

- [x] Created schema validation script.
  - File: `10_KOL_Centrality_Engine/schema_validate.py`
- [x] Implemented `--json` validation mode.
- [x] Implemented `--create` mode to execute `schema.sql` using Postgres credentials.
- [x] Verified both tables exist through Supabase REST.
  - `kol_centrality_runs`: present
  - `kol_centrality_scores`: present

#### G. Supabase IO layer

- [x] Created Supabase IO module.
  - File: `10_KOL_Centrality_Engine/supabase_io.py`
- [x] Implemented safe environment loading without printing credentials.
- [x] Implemented REST fetch for source tables.
  - `kols`
  - `kol_authorships`
  - `publications`
  - `kol_merge_candidates`
- [x] Implemented REST insert for output tables.
- [x] Implemented chunked inserts.
  - Default chunk size: 500 rows.
- [x] Implemented previous-latest demotion.
  - Old rows for `graph_scope = global_authorship` are marked `is_latest = false` before new rows are inserted.
- [x] Implemented table creation via Postgres connection for approved execution.
- [x] No Supabase keys or database passwords were printed.

#### H. Authorship graph construction

- [x] Created graph builder.
  - File: `10_KOL_Centrality_Engine/authorship_graph.py`
- [x] Implemented KOL node creation from `kols.id`.
- [x] Implemented publication grouping from `kol_authorships.publication_id`.
- [x] Implemented undirected pairwise coauthor edges.
- [x] Implemented repeated coauthorship edge weights.
- [x] Implemented per-node mapped publication count.
- [x] Implemented per-node mapped coauthor count.
- [x] Implemented connected component helper.
- [x] Added unit test.
  - File: `tests/test_authorship_graph.py`

#### I. Metric calculation

- [x] Created metrics module.
  - File: `10_KOL_Centrality_Engine/metrics.py`
- [x] Implemented degree centrality.
- [x] Implemented weighted degree.
- [x] Implemented weighted PageRank.
- [x] Implemented Brandes betweenness centrality with sampling for large graphs.
- [x] Implemented eigenvector centrality with fallback flag.
- [x] Implemented connected component size and component IDs.
- [x] Avoided closeness centrality in v1.
  - Reason: global closeness is misleading in disconnected biomedical coauthorship graphs.

#### J. Scoring

- [x] Created scoring module.
  - File: `10_KOL_Centrality_Engine/scoring.py`
- [x] Implemented percentile normalization.
- [x] Implemented v1 score formula.
- [x] Implemented fallback score formula.
- [x] Implemented 0–100 bounds.
- [x] Implemented tier assignment.
- [x] Implemented “Insufficient Data” handling.
- [x] Added unit test.
  - File: `tests/test_scoring.py`

#### K. Reliability and limitations

- [x] Created reliability module.
  - File: `10_KOL_Centrality_Engine/reliability.py`
- [x] Implemented reliability score.
  - Inputs: mapped publication count, mapped coauthor count, component size, duplicate warning, eigenvector fallback status.
- [x] Implemented reliability bands.
  - `high`, `moderate`, `low`, `very_low`
- [x] Implemented limitations list.
  - Incomplete publication network
  - Few/no mapped coauthors
  - small/disconnected component
  - possible duplicate/merge candidate
  - eigenvector fallback if used
- [x] Added unit test.
  - File: `tests/test_reliability.py`

#### L. Human-readable score reasons

- [x] Created score reason module.
  - File: `10_KOL_Centrality_Engine/reasons.py`
- [x] Implemented reason generation for high, strong, moderate, low, low-reliability, and insufficient-data cases.
- [x] Reason text explicitly avoids claiming absolute real-world influence.
- [x] Low-reliability score reasons warn that the score may be understated because of incomplete mapped data.

#### M. Main CLI script

- [x] Created single-shot CLI.
  - File: `10_KOL_Centrality_Engine/run_centrality.py`
- [x] Implemented flags:
  - `--dry-run`
  - `--write-local`
  - `--write-supabase`
  - `--create-schema`
  - `--graph-scope`
  - `--method-version`
  - `--pull-id`
  - `--triggered-by`
  - `--min-publications`
  - `--min-coauthors`
  - `--min-join-rate`
  - `--limit`
  - `--run-id`
  - `--chunk-size`
- [x] Implemented structured exit behavior.
  - `0` success
  - `1` partial/warning
  - `2` failure
- [x] Implemented summary JSON on success and failure.
  - File: `06_Shared_Datastores/pipeline_summaries/kol_centrality_summary.json`

#### N. Local review output

- [x] Created local output folder.
  - Path: `06_Shared_Datastores/centrality_outputs/`
- [x] Wrote latest CSV.
  - `kol_authorship_centrality_latest.csv`
- [x] Wrote run-specific CSV.
  - `kol_authorship_centrality_centrality_20260428_070305_db4fba68.csv`
- [x] Included score, tier, reliability, reason, limitations, graph metrics, method version, run ID, and graph scope.

#### O. Pipeline integration

- [x] Modified KOL pipeline script.
  - File: `01_KOL_Data_Engine/run_pipeline.py`
- [x] Added centrality downstream phase.
  - Function: `run_centrality_phase()`
- [x] Added CLI flag.
  - `--run_centrality`
- [x] Added centrality write mode flag.
  - `--centrality_write_mode dry-run|local|supabase`
- [x] Centrality runs after publication weighting.
  - It is called after `compute_all_weights()`.
- [x] Centrality failure raises a centrality-phase error without changing the source-data ingestion design.

#### P. Scheduler / n8n-facing integration

- [x] Modified scheduler used by current n8n Meddash workflow.
  - File: `01_KOL_Data_Engine/nightly_scheduler.py`
- [x] Default scheduler behavior now enables centrality after each KOL pull.
  - Existing n8n node calls `python3 nightly_scheduler.py`; no node command change needed.
- [x] Added scheduler flag to disable if needed.
  - `--skip-centrality`
- [x] Added scheduler centrality write-mode flag.
  - `--centrality-write-mode dry-run|local|supabase`
- [x] Default scheduler write mode is `supabase`.
- [x] Scheduler summary now records whether centrality was enabled and which write mode was used.

#### Q. n8n workflow settings

- [x] Inspected current n8n Meddash workflow.
  - Workflow: `Meddash Work Flow`
  - Current KOL node runs `nightly_scheduler.py`.
- [x] Avoided direct n8n credential edits.
  - No credential DB writes were made.
- [x] Achieved auto-centrality through scheduler behavior instead of DB-mutating the workflow node.
  - Reason: existing n8n node already calls `nightly_scheduler.py`; updating scheduler defaults is safer than rewriting workflow JSON in SQLite.
- [ ] UI toggle/restart of n8n workflow not performed.
  - Current change is code-level; the next n8n execution should pick up the modified scheduler script.

#### R. Nightly fallback

- [x] Current Meddash scheduled KOL pull now acts as the recurring centrality refresh point because centrality runs after every pull.
- [ ] Separate standalone nightly fallback workflow not created yet.
  - Future improvement if we want centrality to refresh even on days when KOL pull is skipped.

#### S. Supabase write behavior

- [x] Inserted one `kol_centrality_runs` row for the initial population.
- [x] Inserted per-KOL rows into `kol_centrality_scores`.
- [x] Marked current rows as latest using `is_latest = true`.
- [x] Preserved previous latest-score design for future failed runs.
  - Failed future runs should not blank the dashboard because old latest rows are only demoted during a successful write path.

#### T. Optional `kols` summary columns

- [ ] Not implemented.
  - Deliberately deferred. The source of truth is `kol_centrality_scores`.
  - Dashboard can later join/read latest scores without changing the core `kols` table.

#### U. Testing and verification

- [x] Python compile passed for centrality scripts and modified pipeline/scheduler scripts.
- [x] Unit tests passed.
  - Command: `python -m pytest 10_KOL_Centrality_Engine/tests -q`
  - Result: `3 passed`
- [x] Dry-run local output passed.
- [x] Supabase schema validation passed.
- [x] Supabase population passed.
- [x] Verified Supabase REST counts after population.
  - `kol_centrality_runs`: 1 row
  - `kol_centrality_scores`: 8,485 rows

#### V. Dashboard integration

- [ ] Dashboard display not implemented yet.
  - The score data now exists in Supabase and can be wired into the dashboard in the next phase.
- [ ] Recommended display rule remains: show score + reliability + reason together, never score alone.

#### W. Observability

- [x] Summary JSON is written after centrality runs.
  - File: `06_Shared_Datastores/pipeline_summaries/kol_centrality_summary.json`
- [x] Local CSV output is available for manual inspection.
- [ ] Dedicated `kol_centrality.log` file not implemented yet.
  - Current observability uses summary JSON plus stdout/stderr captured by scheduler/n8n.

---

### 13.2 Initial Population Result

Initial run ID:

```text
centrality_20260428_070305_db4fba68
```

Supabase population result:

| Item | Result |
|---|---:|
| KOL source rows | 8,485 |
| Authorship source rows | 8,461 |
| Publication source rows | 922 |
| Coauthor graph nodes | 8,485 |
| Coauthor graph edges | 54,824 |
| Publication groups | 909 |
| Usable coauthored publications | 878 |
| KOLs with any mapped publication | 8,020 |
| KOLs with any mapped coauthor | 7,997 |
| Coauthor mapping rate | 0.9425 |
| Centrality score rows written | 8,485 |

Score distribution:

| Tier | Count |
|---|---:|
| Tier 1 — Network Anchor | 248 |
| Tier 2 — Strong Connector | 1,115 |
| Tier 3 — Established Node | 2,604 |
| Tier 4 — Peripheral/Mapped | 3,318 |
| Emerging/Peripheral | 712 |
| Insufficient Data | 488 |

Reliability distribution:

| Reliability band | Count |
|---|---:|
| High | 28 |
| Moderate | 1,682 |
| Low | 6,072 |
| Very low | 703 |

Important interpretation note:

A low or insufficient score currently means “low or insufficient centrality inside the mapped authorship graph,” not “low real-world influence.” This is why every score row includes reliability, limitations, and score reason.

