-- ============================================================
-- ct_schema.sql — Meddash ClinicalTrials.gov Intelligence DB
-- Version: 1.0   Created: 2026-03-08
-- Database: ct_trials.db (separate from meddash_kols.db)
-- ============================================================
-- Privacy rule: investigator emails are NEVER stored.
--   Email is used only to derive institution name in-memory,
--   then discarded. Only the derived institution string is kept.
-- ============================================================

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;


-- ── 1. trials ─────────────────────────────────────────────
-- Core identity, status, dates, and phase for every trial.
-- trial_url is a derived field: https://clinicaltrials.gov/study/{nct_id}

CREATE TABLE IF NOT EXISTS trials (
    nct_id                   TEXT PRIMARY KEY,
    brief_title              TEXT,
    official_title           TEXT,
    brief_summary            TEXT,
    study_type               TEXT,              -- Interventional / Observational
    overall_status           TEXT,              -- Recruiting, Completed, Terminated, etc.
    why_stopped              TEXT,              -- Raw CT.gov termination reason
    why_stopped_category     TEXT,              -- Phi-3 derived: safety/efficacy/business/enrollment/regulatory
    phase                    TEXT,              -- Phase 1, 2, 3, 4, N/A
    start_date               TEXT,
    completion_date          TEXT,
    primary_completion_date  TEXT,
    first_posted_date        TEXT,
    last_update_posted       TEXT,              -- Used for delta-update filtering
    enrollment               INTEGER,
    enrollment_type          TEXT,              -- Anticipated / Actual
    allocation               TEXT,              -- Randomized / Non-Randomized
    intervention_model       TEXT,              -- Parallel / Crossover / etc.
    primary_purpose          TEXT,              -- Treatment / Prevention / Diagnostic / etc.
    trial_url                TEXT,              -- https://clinicaltrials.gov/study/{nct_id}
    raw_json_path            TEXT,              -- Path to raw JSON snapshot for reprocessing
    ingested_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at               TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_trials_status    ON trials(overall_status);
CREATE INDEX IF NOT EXISTS idx_trials_phase     ON trials(phase);
CREATE INDEX IF NOT EXISTS idx_trials_study_type ON trials(study_type);
CREATE INDEX IF NOT EXISTS idx_trials_updated   ON trials(last_update_posted);
CREATE INDEX IF NOT EXISTS idx_trials_start     ON trials(start_date);


-- ── 2. trial_conditions ──────────────────────────────────
-- Raw condition strings from CT.gov + MeSH mapping (populated by ct_mesh_mapper.py)

CREATE TABLE IF NOT EXISTS trial_conditions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nct_id      TEXT NOT NULL REFERENCES trials(nct_id) ON DELETE CASCADE,
    condition   TEXT NOT NULL,    -- Raw CT.gov free-text string
    mesh_id     TEXT,             -- Mapped by ct_mesh_mapper.py (NLM API / Phi-3 fallback)
    mesh_term   TEXT,             -- Human-readable MeSH term
    UNIQUE(nct_id, condition)
);

CREATE INDEX IF NOT EXISTS idx_cond_nct   ON trial_conditions(nct_id);
CREATE INDEX IF NOT EXISTS idx_cond_mesh  ON trial_conditions(mesh_id);


-- ── 3. trial_interventions ────────────────────────────────
-- Drug / biologic / device being studied

CREATE TABLE IF NOT EXISTS trial_interventions (
    id                        INTEGER PRIMARY KEY AUTOINCREMENT,
    nct_id                    TEXT NOT NULL REFERENCES trials(nct_id) ON DELETE CASCADE,
    intervention_name         TEXT,
    intervention_type         TEXT,             -- Drug / Biological / Device / Procedure / Other
    intervention_description  TEXT,
    UNIQUE(nct_id, intervention_name)
);

CREATE INDEX IF NOT EXISTS idx_interv_nct  ON trial_interventions(nct_id);
CREATE INDEX IF NOT EXISTS idx_interv_name ON trial_interventions(intervention_name);
CREATE INDEX IF NOT EXISTS idx_interv_type ON trial_interventions(intervention_type);


-- ── 4. trial_sponsors ─────────────────────────────────────
-- Lead sponsor + collaborators (is_lead = 1 for lead, 0 for collaborator)

CREATE TABLE IF NOT EXISTS trial_sponsors (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    nct_id         TEXT NOT NULL REFERENCES trials(nct_id) ON DELETE CASCADE,
    sponsor_name   TEXT NOT NULL,
    sponsor_class  TEXT,          -- INDUSTRY / NIH / FED / OTHER_GOV / INDIV / NETWORK / AMBIG / UNKNOWN / OTHER
    is_lead        INTEGER DEFAULT 1,  -- 1 = lead sponsor, 0 = collaborator
    UNIQUE(nct_id, sponsor_name, is_lead)
);

CREATE INDEX IF NOT EXISTS idx_spon_nct   ON trial_sponsors(nct_id);
CREATE INDEX IF NOT EXISTS idx_spon_name  ON trial_sponsors(sponsor_name);
CREATE INDEX IF NOT EXISTS idx_spon_class ON trial_sponsors(sponsor_class);
CREATE INDEX IF NOT EXISTS idx_spon_lead  ON trial_sponsors(is_lead);


-- ── 5. trial_sites ────────────────────────────────────────
-- Site-level geography and recruitment status (institution intelligence layer)

CREATE TABLE IF NOT EXISTS trial_sites (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    nct_id         TEXT NOT NULL REFERENCES trials(nct_id) ON DELETE CASCADE,
    facility_name  TEXT,
    city           TEXT,
    state          TEXT,
    country        TEXT,
    zip_code       TEXT,
    site_status    TEXT,          -- Recruiting / Not yet recruiting / Completed / etc.
    UNIQUE(nct_id, facility_name, city, country)
);

CREATE INDEX IF NOT EXISTS idx_sites_nct      ON trial_sites(nct_id);
CREATE INDEX IF NOT EXISTS idx_sites_facility ON trial_sites(facility_name);
CREATE INDEX IF NOT EXISTS idx_sites_country  ON trial_sites(country);
CREATE INDEX IF NOT EXISTS idx_sites_status   ON trial_sites(site_status);


-- ── 6. trial_investigators ────────────────────────────────
-- KOL linkage spine. kol_id references meddash_kols.db → kols.id
-- Populated by ct_kol_bridge.py (Step 5).
-- NOTE: email is NEVER stored. affiliation is derived from official record
--       or email domain in-memory, then email is discarded.

CREATE TABLE IF NOT EXISTS trial_investigators (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    nct_id              TEXT NOT NULL REFERENCES trials(nct_id) ON DELETE CASCADE,
    investigator_name   TEXT NOT NULL,
    role                TEXT,          -- PRINCIPAL_INVESTIGATOR / SUB_INVESTIGATOR / STUDY_DIRECTOR
    affiliation         TEXT,          -- Institution only (derived from record or email domain — email discarded)
    kol_id              INTEGER,       -- FK to meddash_kols.db kols.id (populated by Step 5)
    bridge_confidence   REAL,          -- 0.0–1.0 match score from ct_kol_bridge.py
    bridge_method       TEXT,          -- name_exact / name_fuzzy_affil / mesh_name / unmatched
    UNIQUE(nct_id, investigator_name, role)
);

CREATE INDEX IF NOT EXISTS idx_inv_nct    ON trial_investigators(nct_id);
CREATE INDEX IF NOT EXISTS idx_inv_kol    ON trial_investigators(kol_id);
CREATE INDEX IF NOT EXISTS idx_inv_name   ON trial_investigators(investigator_name);
CREATE INDEX IF NOT EXISTS idx_inv_role   ON trial_investigators(role);


-- ── 7. trial_outcomes ─────────────────────────────────────
-- Primary and secondary endpoint definitions (from protocol)

CREATE TABLE IF NOT EXISTS trial_outcomes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nct_id          TEXT NOT NULL REFERENCES trials(nct_id) ON DELETE CASCADE,
    outcome_type    TEXT NOT NULL,    -- PRIMARY / SECONDARY
    measure         TEXT,
    time_frame      TEXT,
    description     TEXT,
    UNIQUE(nct_id, outcome_type, measure)
);

CREATE INDEX IF NOT EXISTS idx_out_nct  ON trial_outcomes(nct_id);
CREATE INDEX IF NOT EXISTS idx_out_type ON trial_outcomes(outcome_type);


-- ── 8. trial_results ─────────────────────────────────────
-- Actual results from resultsSection (populated by ct_results_parser.py — Step 6)
-- Includes efficacy data and adverse event summaries.

CREATE TABLE IF NOT EXISTS trial_results (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    nct_id            TEXT NOT NULL REFERENCES trials(nct_id) ON DELETE CASCADE,
    outcome_title     TEXT,
    outcome_type      TEXT,           -- PRIMARY / SECONDARY
    measure           TEXT,
    reported_value    TEXT,
    p_value           TEXT,
    serious_ae_count  INTEGER,        -- Serious adverse events (from adverseEventsModule)
    deaths_reported   INTEGER,
    UNIQUE(nct_id, outcome_title)
);

CREATE INDEX IF NOT EXISTS idx_res_nct  ON trial_results(nct_id);


-- ── 9. trial_publications ────────────────────────────────
-- referencesModule PMID bridge (populated by ct_pub_bridge.py — Step 7)
-- Links trials directly to publications in meddash_kols.db

CREATE TABLE IF NOT EXISTS trial_publications (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nct_id      TEXT NOT NULL REFERENCES trials(nct_id) ON DELETE CASCADE,
    pmid        TEXT NOT NULL,        -- FK to meddash_kols.db publications.pmid
    ref_type    TEXT,                 -- RESULT / BACKGROUND / DERIVED
    citation    TEXT,
    UNIQUE(nct_id, pmid)
);

CREATE INDEX IF NOT EXISTS idx_pub_nct  ON trial_publications(nct_id);
CREATE INDEX IF NOT EXISTS idx_pub_pmid ON trial_publications(pmid);


-- ── 10. trial_eligibility ────────────────────────────────
-- Raw eligibility criteria text + Phi-3 Mini extracted structured fields
-- llm_processed flag = 0 until ct_eligibility_parser.py runs (Step 8)

CREATE TABLE IF NOT EXISTS trial_eligibility (
    nct_id                   TEXT PRIMARY KEY REFERENCES trials(nct_id) ON DELETE CASCADE,
    raw_criteria             TEXT,
    min_age                  TEXT,
    max_age                  TEXT,
    sex                      TEXT,
    healthy_volunteers       TEXT,
    biomarkers_required      TEXT,    -- Phi-3 extracted: e.g. "KRAS G12C positive"
    prior_treatment_required TEXT,    -- Phi-3 extracted: e.g. "≥2 prior therapies"
    disease_stage            TEXT,    -- Phi-3 extracted: e.g. "Stage III-IV"
    llm_processed            INTEGER DEFAULT 0,  -- 0=pending, 1=processed by Phi-3
    llm_processed_at         TIMESTAMP
);


-- ── 11. ct_kol_summary ────────────────────────────────────
-- Pre-computed analytical summary per KOL across all CT.gov trials.
-- Refreshed by ct_kol_bridge.py whenever new trials are ingested.
-- kol_id references meddash_kols.db → kols.id

CREATE TABLE IF NOT EXISTS ct_kol_summary (
    kol_id                  INTEGER PRIMARY KEY,  -- FK to meddash_kols.db kols.id
    trials_total            INTEGER DEFAULT 0,
    trials_as_pi            INTEGER DEFAULT 0,    -- Principal Investigator roles
    industry_trials         INTEGER DEFAULT 0,    -- sponsor_class = INDUSTRY
    phase1_trials           INTEGER DEFAULT 0,
    phase2_trials           INTEGER DEFAULT 0,
    phase3_trials           INTEGER DEFAULT 0,
    phase4_trials           INTEGER DEFAULT 0,
    active_trials           INTEGER DEFAULT 0,    -- status = Recruiting / Active not recruiting
    completed_trials        INTEGER DEFAULT 0,
    terminated_trials       INTEGER DEFAULT 0,
    unique_sponsors         INTEGER DEFAULT 0,
    unique_conditions       INTEGER DEFAULT 0,
    unique_sites            INTEGER DEFAULT 0,
    last_computed_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_kol_sum_pi       ON ct_kol_summary(trials_as_pi DESC);
CREATE INDEX IF NOT EXISTS idx_kol_sum_industry ON ct_kol_summary(industry_trials DESC);
CREATE INDEX IF NOT EXISTS idx_kol_sum_phase3   ON ct_kol_summary(phase3_trials DESC);
CREATE INDEX IF NOT EXISTS idx_kol_sum_total    ON ct_kol_summary(trials_total DESC);
