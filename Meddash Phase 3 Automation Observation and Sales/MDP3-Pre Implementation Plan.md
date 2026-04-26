# MDP3 — Meddash Phase 3: Pre-Implementation Plan

> **Author:** Hermes Alfred Chief  
> **Date:** 2026-04-26 22:15 UTC  
> **Status:** Pre-Implementation — Checklist for Phase 3 Build  
> **Scope:** Automation, Observability, Sales Enablement  

---

## 1. Current Architecture Overview (10 Engines)

| # | Engine | Path | Scripts | Trigger | LLM | Purpose |
|---|--------|------|---------|---------|-----|---------|
| 01 | KOL Data Engine | `Meddash_organized_backend/01_KOL_Data_Engine/` | 8 | Daily 2AM (nightly_scheduler.py) | Gemini Flash | PubMed/ORCID → disambiguate → weight → upsert KOLs |
| 02 | CT Data Engine | `Meddash_organized_backend/02_CT_Data_Engine/` | 8 | Manual/trigger | Gemini Flash | ClinicalTrials.gov API v2 → 11 tables → KOL bridge |
| 03 | BioCrawler GTM | `Meddash_organized_backend/03_BioCrawler_GTM/` | 5 | Daily 5PM (run_biocrawler.bat) | None | Company intelligence → leads → Google Sheets |
| 04 | Product KOL Briefs | `Meddash_organized_backend/04_Product_KOL_Briefs/` | 2 | On-demand | Gemini Pro | Generate KOL briefs from trial + publication signals |
| 05 | Product TA Landscape | `Meddash_organized_backend/05_Product_TA_Landscape/` | 4 | On-demand | Gemini 2.5 Pro | TA landscape reports with human-in-the-loop |
| 06 | Shared Datastores | `Meddash_organized_backend/06_Shared_Datastores/` | 0 | N/A | N/A | SQLite: meddash_kols.db, ct_trials.db, biocrawler_leads.db, journal_metrics.db |
| 07 | DevOps Observability | `Meddash_organized_backend/07_DevOps_Observability/` | 6 | Manual | N/A | Build dictionaries, file paths, QA, patches |
| 08 | MDM Ontology Engine | `Meddash_organized_backend/08_MDM_Ontology_Engine/` | 1 | On-demand | N/A | MeSH, ICD-10, SNOMED crosswalks |
| 09 | Scholar Engine | `Meddash_organized_backend/09_Scholar_Engine/` | 3 | On-demand | N/A | Google Scholar citations, review queue |
| 10 | CQ Newsletter Pipeline | `CTO/CQ_Team/scripts/phase1_regulatory/` | 3 | Daily 11AM (n8n cron) | None | SEC 8-K, FDA PDUFA, PR Wire → Supabase → Paperclip |

**Total: 37 scripts, 4 SQLite DBs, 1 Supabase instance (30+ tables)**

---

## 2. Current Workflow Map

```
BIOCRAWLER (03)  ──5PM──→  populates biotech_leads.primary_indication
                                    │
                                    ▼
KOL ENGINE (01) ──2AM──→  reads primary_indication → PubMed search → KOL profiles
                                    │
                                    ▼
CT ENGINE (02)  ──manual─→  ClinicalTrials.gov → 11 tables → KOL bridge
                                    │
                                    ▼
PRODUCT (04/05) ──on-demand─→  KOL Briefs + TA Landscapes
                                    │
                                    ▼
CQ NEWSLETTER (10) ──11AM──→  SEC/FDA/PR → Supabase → Paperclip agents → Obsidian draft
```

---

## 3. Issues Identified

### 3.1 Trigger & Scheduling Issues
- [ ] Engine 01 (nightly_scheduler.py) runs via Python `schedule` library — requires a terminal left open. Not resilient to restarts.
- [ ] Engine 02 (CT Crawler) has no automated trigger — purely manual execution.
- [ ] Engine 03 (BioCrawler) runs via Windows .bat file — no orchestration, no failure notification.
- [ ] No unified trigger system — each engine runs independently with no coordination or dependency management.
- [ ] No health monitoring or alerting for Engines 01-09 (only CQ Engine 10 has monitoring via CQ-Monitor agent).

### 3.2 Alerting Gaps
- [ ] Some scripts have hardcoded `telegram_notifier` imports (ct_crawler.py, run_pipeline.py) but the notifier is in DevOps and not consistently configured.
- [ ] No dedicated Meddash Telegram bot — CQ bot exists but Meddash needs its own.
- [ ] No pipeline health summaries — you don't know if last night's KOL pull succeeded until you manually check.

### 3.3 Data Scope Issues
- [ ] KOL search targets are semi-hardcoded — fallback to `["Non-Small Cell Lung Cancer"]`.
- [ ] CT Crawler `query` mode exists but no automated rotation of search areas.
- [ ] No MeSH-based systematic coverage — discovery is opportunistic, not comprehensive.
- [ ] Data moat is thin — only KOLs where companies already exist, not where they'll emerge.

---

## 4. Current KOL & Clinical Trial Search Criteria

### 4.1 KOL Data Engine (01) — How It Decides What to Pull

**Script:** `nightly_scheduler.py`

```
DEFAULT:         targets = ["Non-Small Cell Lung Cancer"]  ← Hardcoded fallback
DYNAMIC:         Reads biotech_leads.primary_indication from biocrawler_leads.db
OVERRIDE:        run_pipeline.py --targets "Disease A" "Disease B" --max_results 50
```

**The feedback loop:**
1. BioCrawler (03) discovers companies → populates `biotech_leads.primary_indication`
2. nightly_scheduler.py reads those indications → uses as PubMed search terms
3. `extract_publications.py` queries PubMed: `{therapeutic_area} AND medline[sb]`
4. Results are ingested → disambiguated → weighted → KOL profiles built

**Good:** It IS dynamic when BioCrawler has populated data.  
**Bad:** Falls back to NSCLC only when BioCrawler is empty. No systematic coverage beyond what leads exist.

### 4.2 CT Data Engine (02) — How It Decides What to Pull

**Script:** `ct_crawler.py`

```
FULL mode:       Pulled ALL ~480K trials — no disease filter
DELTA mode:      Only trials updated in last N hours — no disease filter
QUERY mode:      Targeted by condition/keyword — user-specified input
```

**Good:** Three-mode design is flexible. `query` mode supports on-demand briefs.  
**Bad:** No automated rotation of `query` mode. Full crawl is one-time. Delta doesn't expand coverage — only updates existing records.

### 4.3 BioCrawler GTM (03) — The Bright Spot

**This is the strongest part of the current architecture:**

- BioCrawler discovers biotech companies → extracts their `primary_indication`
- Those indications FEED BACK into the KOL engine's search targets
- This creates a GTM-aligned feedback loop: **where companies are buying → where we search for KOLs**
- BioCrawler also calculates SVS (Scientific Value Score) → bridges to advisory boards
- Push to Google Sheets → operational visibility for sales

**BioCrawler is the engine that makes the whole loop work.** Without it, KOL engine reverts to hardcoded NSCLC. With it, search targets auto-update based on real market activity.

---

## 5. Novel Solution: Three-Tier Search with Weekly MeSH Rotation

### 5.1 The Three Tiers

```
TIER 1: FEEDBACK LOOP (current — keep as-is)
  BioCrawler indications → KOL search targets
  GTM-aligned. Pulls KOLs where companies are buying.
  Zero additional cost — already works.

TIER 2: MeSH ROTATION (NEW — add to nightly_scheduler.py)
  Weekly rotation through MeSH top-level disease categories.
  Discovers KOLs BEFORE companies exist in that space.
  One extra PubMed query per night (~50 publications).
  Expands KOL universe ~15% per week.

TIER 3: CLIENT-DRIVEN (already designed — on-demand via dashboard)
  KOL Brief order for "HER2+ Breast Cancer"
  → triggers CT crawler --mode query --query "HER2 breast cancer"
  → triggers KOL pull for that MeSH
  → generates brief
  Revenue trigger — the customer pays, the engine runs.
```

### 5.2 MeSH Rotation Schedule

```python
MESH_ROTATION = [
    "Neoplasms",                    # C04 — Oncology
    "Musculoskeletal Diseases",     # C05 — Rheumatology/Orthopedics
    "Respiratory Tract Diseases",   # C08 — Pulmonology
    "Nervous System Diseases",      # C10 — Neurology
    "Cardiovascular Diseases",      # C14 — Cardiology
    "Digestive System Diseases",    # C06 — GI/Hepatology
    "Immune System Diseases",       # C20 — Immunology/Autoimmune
    "Eye Diseases",                 # C11 — Ophthalmology
    "Skin and Connective Tissue Diseases",  # C17 — Dermatology
    "Endocrine System Diseases",    # C19 — Endocrinology
    "Hemic and Lymphatic Diseases", # C15 — Hematology
    "Stomatognathic Diseases",      # C07 — Dental/Oral
]

# Weekly index based on ISO week number
week_index = datetime.now().isocalendar()[1] % len(MESH_ROTATION)
rotating_target = MESH_ROTATION[week_index]

# Merge all tiers: Tier 1 (leads) + Tier 2 (rotation) + deduplicate
targets = list(set(lead_targets + [rotating_target]))
```

### 5.3 Rotation Calendar (12-week cycle)

| Week | MeSH Category | MeSH Code | TA |
|------|---------------|-----------|-----|
| 1 | Neoplasms | C04 | Oncology |
| 2 | Musculoskeletal Diseases | C05 | Rheumatology/Orthopedics |
| 3 | Respiratory Tract Diseases | C08 | Pulmonology |
| 4 | Nervous System Diseases | C10 | Neurology |
| 5 | Cardiovascular Diseases | C14 | Cardiology |
| 6 | Digestive System Diseases | C06 | GI/Hepatology |
| 7 | Immune System Diseases | C20 | Immunology/Autoimmune |
| 8 | Eye Diseases | C11 | Ophthalmology |
| 9 | Skin and Connective Tissue Diseases | C17 | Dermatology |
| 10 | Endocrine System Diseases | C19 | Endocrinology |
| 11 | Hemic and Lymphatic Diseases | C15 | Hematology |
| 12 | Stomatognathic Diseases | C07 | Dental/Oral |

**Cycle repeats every 12 weeks. After 3 full cycles (36 weeks), every major TA has been covered 3 times with fresh publications.**

### 5.4 Database Growth Projection

| Metric | Current (Tier 1 Only) | After 12 Weeks (T1+T2) | After 36 Weeks (3 Cycles) |
|--------|----------------------|------------------------|---------------------------|
| PubMed queries/night | ~15 (from leads) | ~16 (+1 rotation) | ~16 |
| New publications/night | ~750 | ~800 | ~800 |
| Unique KOLs discovered | ~200/week | ~230/week | ~230/week |
| Total KOL universe | ~2,000 | ~4,760 | ~8,300+ |
| MeSH categories covered | 3-5 (opportunistic) | 12 (systematic) | 12 (deep coverage) |
| KOL Brief sellable TAs | 3-5 | 12 | 12 (with depth) |

**Cost: One extra PubMed query per night. Benefit: 4x KOL universe expansion in 9 months.**

### 5.5 Why BioCrawler + Rotation Is the Winning Combination

| Aspect | BioCrawler Only (Tier 1) | Rotation Only (Tier 2) | Both (T1+T2) |
|--------|--------------------------|------------------------|---------------|
| KOL discovery | Where companies buy | Systematic but unfocused | Systematic + GTM-aligned |
| Market relevance | High (buying signal) | Medium (broad coverage) | High + broad |
| Revenue potential | Limited to known TAs | Broad but shallow | Deep per TA + broad coverage |
| Data moat | Thin | Wide | Wide + Deep |
| Proactive capability | No | Yes | Yes |
| Advisory board mapping | Yes (SVS) | No | Yes (SVS + MeSH depth) |
| Client brief coverage | 3-5 TAs | 12 TAs | 12 TAs with GTM context |

**BioCrawler tells you WHERE the money is. Rotation tells you WHERE the money WILL BE. Together, you have both.**

---

## 6. Implementation Checklist — Phase 3

### 6.1 n8n Workflow: Meddash Pipeline

- [ ] **MDP3-01:** Create Meddash n8n workflow canvas (Dr. Don — done)
- [ ] **MDP3-02:** Add Schedule Trigger node — 2AM daily for KOL Data Engine
- [ ] **MDP3-03:** Add Code node — runs `run_pipeline.py --targets {dynamic_targets}` with Tier 1 + Tier 2 merged targets
- [ ] **MDP3-04:** Add MeSH rotation logic to nightly_scheduler.py (Tier 2 code change)
- [ ] **MDP3-05:** Add Schedule Trigger node — 5PM daily for BioCrawler GTM
- [ ] **MDP3-06:** Add Code node — runs biocrawler.py daily mode
- [ ] **MDP3-07:** Add Manual Trigger node — for on-demand CT Crawler (Engine 02) with `--mode query --query {input}`
- [ ] **MDP3-08:** Add Manual Trigger node — for on-demand KOL Brief generation (Engine 04)
- [ ] **MDP3-09:** Add Manual Trigger node — for on-demand TA Landscape report (Engine 05)
- [ ] **MDP3-10:** Add Manual Trigger node — for Scholar Sync (Engine 09)
- [ ] **MDP3-11:** Add Manual Trigger node — for Ontology Rebuild (Engine 08)

### 6.2 Alerting: Meddash Telegram Bot

- [ ] **MDP3-12:** Create Meddash Telegram bot via BotFather (Dr. Don)
- [ ] **MDP3-13:** Add Telegram credentials in n8n → Credentials → Telegram API
- [ ] **MDP3-14:** Add Telegram node after 2AM KOL trigger — "KOL Pipeline Started"
- [ ] **MDP3-15:** Add Telegram node after KOL scripts complete — "KOL Pipeline Complete — {X} publications, {Y} KOLs updated"
- [ ] **MDP3-16:** Add Telegram node after 5PM BioCrawler trigger — "BioCrawler Started"
- [ ] **MDP3-17:** Add Telegram node after BioCrawler complete — "BioCrawler Complete — {X} leads updated"
- [ ] **MDP3-18:** Add Telegram node on script failure — "PIPELINE FAILED: {engine} — {error}" with escalation

### 6.3 Monitoring: Meddash Agents in Paperclip

- [ ] **MDP3-19:** Create Meddash-Monitor agent (role: qa) — checks pipeline health + Supabase freshness + script execution logs
- [ ] **MDP3-20:** Add Wait node (15 min after 2AM) → POST to Paperclip → Meddash-Monitor issue
- [ ] **MDP3-21:** Add Wait node (15 min after 5PM) → POST to Paperclip → Meddash-Monitor issue
- [ ] **MDP3-22:** Add Telegram node after Monitor trigger — "Meddash health check starting"
- [ ] **MDP3-23:** Write Meddash-Monitor AGENTS.md — checks Supabase table counts, script exit codes, last run timestamps, data freshness
- [ ] **MDP3-24:** Add Meddash Supabase Health Monitor — dedicated check for Supabase connection, table row counts, recent inserts, API response times
- [ ] **MDP3-25:** Add escalation rule: healthy → report + sleep; issues found → URGENT issue to Meddash-CTO for fix + finalize report

### 6.4 MeSH Rotation Implementation

- [ ] **MDP3-26:** Patch `nightly_scheduler.py` — add MESH_ROTATION list and weekly index logic
- [ ] **MDP3-27:** Patch `run_pipeline.py` — accept `--rotation_target` parameter alongside `--targets`
- [ ] **MDP3-28:** Add rotation logging — record which MeSH category ran each night to `mesh_rotation_log.db`
- [ ] **MDP3-29:** Add rotation state file — `mesh_rotation_state.json` with current week, last completed category, cycle count
- [ ] **MDP3-30:** Add deduplication — ensure rotation target doesn't duplicate Tier 1 target if BioCrawler already has that indication
- [ ] **MDP3-31:** Test rotation logic — dry run with mock schedule to verify 12-week cycle
- [ ] **MDP3-32:** Add rotation metrics to Meddash-Monitor — report which TAs have been covered, KOLs per TA, coverage depth

### 6.5 Engine 04/05: On-Demand via Dashboard

- [ ] **MDP3-33:** Wire Streamlit dashboard (port 5090) KOL Brief tool to n8n manual trigger via webhook
- [ ] **MDP3-34:** Add n8n Webhook node — receives MeSH/condition from dashboard → triggers CT crawler query mode → triggers KOL pull → triggers brief generation
- [ ] **MDP3-35:** Add Telegram alert on brief request — "KOL Brief requested: {condition}"
- [ ] **MDP3-36:** Add Telegram alert on brief complete — "KOL Brief ready: {condition} → saved to {path}"

### 6.6 Cross-Product Synergy (CQ ↔ Meddash)

- [ ] **MDP3-37:** Ensure CQ scripts (SEC 8-K, FDA PDUFA, PR Wire) also populate Meddash-relevant Supabase tables (biotech_leads, trial timelines)
- [ ] **MDP3-38:** Add Meddash-COO coordination rule: CQ-Selector's daily catalyst selections feed Meddash GTM pipeline (which companies had catalysts → BioCrawler should track them)
- [ ] **MDP3-39:** Add shared posted-events mechanism — Meddash Monitor can read CQ posted-events-log to avoid duplicate alerting

---

## 7. Automation Backbone: n8n + Paperclip + Alfred (The Triarchy)

This entire Phase 3 implementation will be automated using the **Triarchy Architecture** — the same proven system that powers the CQ-Free Newsletter pipeline:

```
THE TRIARCHY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

n8n (THE HANDS)
  Clockwork. Triggers, schedules, script execution, HTTP calls.
  Time-based + manual triggers. No intelligence, just reliability.
  Meddash workflow: 2AM, 5PM cron + on-demand webhook buttons.
  
Paperclip (THE WORKERS)  
  Intelligence. Agents that think, verify, monitor, escalate.
  Meddash-COO: Business oversight, bug triage, cross-product coordination.
  Meddash-CTO: Technical executor, bug fixes, script maintenance.
  Meddash-Monitor: Daily health check, Supabase freshness, CTO escalation.
  5-minute heartbeat. Wakes on demand. Sleeps when done.

Hermes Alfred Chief (THE EYE + FIXER)
  Observability. Brain dumps, graph memory, wiki, cross-session recall.
  Sees everything. Remembers everything. Breaks glass when needed.
  Wiki: /mnt/c/Users/email/Hermes Agent Win Files/
  Graph memory: ~/.hermes/graph-memory/
  Brain dumps: Every 4 hours (00,04,08,12,16,20). No retention limit.
```

**What the Triarchy means for Meddash Phase 3:**

- **n8n** handles ALL triggers (2AM KOL, 5PM BioCrawler, on-demand briefs) — replaces fragile Python `schedule` library and Windows .bat files
- **Paperclip agents** handle ALL monitoring and LLM work — Meddash-Monitor checks health, Meddash-CTO fixes bugs, Meddash-COO coordinates
- **Alfred Chief** handles ALL knowledge persistence — pipeline runs, monitor reports, KOL universe metrics, and MeSH rotation state all compound into the wiki and graph memory
- **Three Telegram alert channels:** CQ bot (newsletter), Meddash bot (pipeline), Alfred (break-glass)

**No single point of failure.** If n8n misses a trigger, Meddash-Monitor catches it by 2:15 AM. If a script crashes, Meddash-CTO gets an URGENT issue. If Supabase goes down, the health check escalates. The system watches itself.

---

## 8. Success Criteria for Phase 3

| Metric | Current | Target (End of Phase 3) |
|--------|---------|------------------------|
| Automated triggers | 1 (CQ 11AM) | 4 (CQ 11AM + KOL 2AM + BioCrawler 5PM + on-demand) |
| Telegram alerts | 3 (CQ only) | 8+ (CQ + Meddash pipeline + health checks) |
| Paperclip agents | 7 | 8+ (add Meddash-Monitor) |
| MeSH coverage | 3-5 (opportunistic) | 12 (systematic rotation) |
| KOL universe size | ~2,000 | ~4,760 (after 12 weeks) |
| Pipeline health visibility | None | Full automated health reports twice daily |
| Supabase monitoring | None | Daily freshness + row count + API latency checks |
| On-demand brief triggers | Manual dashboard only | Dashboard → n8n webhook → full pipeline → Telegram alert |
| Self-healing | None | Meddash-CTO auto-fixes on escalation |

---

*End of Pre-Implementation Plan. Next step: Execute MDP3-01 through MDP3-39.*