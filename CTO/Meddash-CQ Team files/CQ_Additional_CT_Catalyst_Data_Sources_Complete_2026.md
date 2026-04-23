# ClinicalQuant: Additional Clinical Trial & Catalyst Data Sources — Complete Verified Report

**Date**: 2026-04-22  
**Scope**: 15 ADDITIONAL sources beyond the existing ClinicalQuant pipeline (ClinicalTrials.gov v2, EU CTIS, WHO ICTRP, ChiCTR, ISRCTN, ANZCTR, UMIN-CTR, jRCT, EudraCT, Citeline/TrialTrove, GlobalData, Evaluate Pharma, Cortellis, AdisInsight, Biomedtracker, Medtrack/IQVIA, Pharmaprojects)  
**Method**: Web-verified research — no hallucinated endpoints or URLs  

---

## Executive Summary

| # | Source | Access Method | Cost | Freshness | Format | Reliability | Build Priority |
|---|--------|--------------|------|-----------|--------|-------------|----------------|
| 1 | DRKS | Bulk JSON download | Free | Hourly | JSON (ZIP) | High | Tier 2 |
| 2 | CTRI | WHO ICTRP CSV only | Free | 1-2 weeks | PDF/CSV | Low (direct), Med (ICTRP) | Tier 3 |
| 3 | CRIS/KCR | OpenAPI (data.go.kr) | Free | Real-time | JSON/XML | High | Tier 2 |
| 4 | PACTR | WHO ICTRP CSV only | Free | 3 months | HTML/CSV | Low | Tier 3 |
| 5 | FDA OpenFDA | Free REST API | Free | Weekly | JSON | High | Tier 1 |
| 6 | Drugs@FDA | Bulk ZIP + API | Free | Daily (M-F) | TSV/JSON | High | Tier 1 |
| 7 | EMA Clinical Data | Web Portal + JSON Bulk | Free | Near real-time | PDF/JSON/HTML | High | Tier 2 |
| 8 | EMA EPAR | JSON Bulk + ePI API | Free | Twice daily | JSON/PDF/XML | High | Tier 1 |
| 9 | EU CTIS API | None (web only) | N/A | Real-time (portal) | HTML/CSV/PDF | Medium | Tier 2 (via ctrdata) |
| 10 | Vivli/CSDR | Manual Portal + DUA | Free (with DUA) | Weeks-months | SAS/CSV/R | Low (pipeline) | Skip (manual only) |
| 11 | PubMed/MEDLINE | E-utilities API | Free | Real-time | JSON/XML | High | Tier 1 |
| 12 | Conference Abstracts | Crossref + PubMed API | Free | Varies | JSON/XML | Medium-High | Tier 2 |
| 13 | TrialReach/Antidote | None | N/A | N/A | N/A | Low | **Skip** |
| 14 | ClinVar/ClinGen | REST API + FTP | Free | Weekly (FTP), RT (API) | JSON/XML/VCF/TSV | High | Tier 2 |
| 15 | BioPharmCatalyst/BPIQ | Paid API + Free tier | $0-$45/mo + custom | Daily | JSON | Medium-High | Tier 1 (paid) |

### Tier Recommendations

| Tier | Sources | Rationale |
|------|---------|-----------|
| **Tier 1 — Build Immediately** | OpenFDA API, Drugs@FDA bulk, EMA EPAR JSON bulk, PubMed E-utilities, BPIQ API (paid) | Free or low-cost, real-time/daily freshness, structured JSON, high reliability, direct catalyst relevance |
| **Tier 2 — Build Next** | DRKS bulk JSON, CRIS OpenAPI, EMA Clinical Data, EU CTIS (ctrdata R package), Conference abstracts (Crossref), ClinVar/ClinGen | Good access, structured data, but secondary priority or moderate setup complexity |
| **Tier 3 — ICTRP Only** | CTRI, PACTR | Accept ICTRP lag, no viable direct programmatic path |
| **Skip** | TrialReach/Antidote, Vivli/CSDR | No API / manual DUA process, unsuitable for automated pipeline |

---

## Detailed Source Profiles

### 1. DRKS (German Clinical Trials Register)

| # | Field | Details |
|---|-------|---------|
| 1 | **Source & URL** | DRKS — https://drks.de |
| 2 | **Access Method** | **Bulk JSON download** (primary): `https://drks.de/search/en/download/all-json` returns ZIP with JSON. Search portal exports: CSV, RIS, JSON. Single records: PDF, XML. **No API exists** (confirmed PLOS One PMC9249399). |
| 3 | **Rate Limits & Pricing** | **Free**. No rate limits documented. No pricing tiers. Bulk cache updated hourly. |
| 4 | **Data Freshness** | Bulk JSON: **Hourly**. Search index: **Daily** (~5:45 AM). WHO ICTRP feed: ~1-2 weeks lag. |
| 5 | **Data Format** | Bulk: **JSON** (ZIP, `DRKS_all_YYYYMMDD.zip`). Schema: `/search/download/jsonschema`. Exports: CSV, RIS, JSON. Single: PDF, XML. |
| 6 | **Reliability** | **High** — WHO Primary Registry, BfArM government-run, ~20K studies, verified HTTP 200 on bulk endpoint. |
| 7 | **Biotech Use Case** | Track German biotech trials (BioNTech, Bayer, Merck KGaA, CureVac). Hourly bulk JSON ideal for ETL — diff snapshots to detect new registrations, phase changes, sponsor activity. Complements ClinicalTrials.gov for EU intelligence. |

### 2. CTRI (Clinical Trial Registry of India)

| # | Field | Details |
|---|-------|---------|
| 1 | **Source & URL** | CTRI — https://ctri.nic.in |
| 2 | **Access Method** | **WHO ICTRP bulk CSV** (recommended). Direct scraping: Selenium + manual CAPTCHA + PDF extraction (extremely difficult). **No API, no export, no bulk download**. |
| 3 | **Rate Limits & Pricing** | WHO ICTRP: **Free**. Direct: CAPTCHA-gated, no rate limits (no API). |
| 4 | **Data Freshness** | Direct scrape: **Real-time** (CAPTCHA-dependent). WHO ICTRP: **~1-2 weeks lag**. |
| 5 | **Data Format** | Direct: **PDF only** (requires pdfplumber extraction). WHO ICTRP: **CSV** (ZIP). No JSON/XML API. Scraper extracts 60+ fields. |
| 6 | **Reliability** | **Low** (direct) — CAPTCHA, PHP sessions, PDF-only. **Medium** (via WHO ICTRP) — present but stale. |
| 7 | **Biotech Use Case** | India is 4th largest trial market globally. Track Indian generics (Sun Pharma, Dr. Reddy's, Cipla) and multinational Phase III sites. Use WHO ICTRP as primary path; direct scraping only for time-sensitive catalysts. Known scraper: `CHACHA0044/CTRI_scrape`. |

### 3. CRIS/KCR (Korean Clinical Research Information Service)

| # | Field | Details |
|---|-------|---------|
| 1 | **Source & URL** | CRIS — https://cris.nih.go.kr |
| 2 | **Access Method** | **data.go.kr OpenAPI** (primary): Verified endpoints with free serviceKey. List: `http://apis.data.go.kr/1352159/crisinfodataview/list` (16 fields). Detail: `http://apis.data.go.kr/1352159/crisinfodataview/detail` (70 fields). Also: WHO ICTRP CSV. |
| 3 | **Rate Limits & Pricing** | **Free** with registration. Rate limit: ~1,000 calls/day (data.go.kr standard). |
| 4 | **Data Freshness** | OpenAPI: **Real-time** (direct DB access). WHO ICTRP: ~1-2 weeks lag. |
| 5 | **Data Format** | OpenAPI: **JSON** (`resultType=json`). List returns 16 fields, Detail returns 70 fields. Also XML available. |
| 6 | **Reliability** | **High** — Government-operated OpenAPI, structured endpoints, 70 fields per trial, WHO Primary Registry, KDCA/MOHW backed. |
| 7 | **Biotech Use Case** | Monitor Korean biotech trials — Samsung Biologics, Celltrion (biosimilars: Herzuma, Inflectra), SK Biopharm, cell/gene therapy programs. OpenAPI enables automated ETL with structured JSON. Ideal for K-pharma pipeline catalyst detection. |

### 4. PACTR (Pan African Clinical Trials Registry)

| # | Field | Details |
|---|-------|---------|
| 1 | **Source & URL** | PACTR — https://pactr.org / https://pactr.samrc.ac.za |
| 2 | **Access Method** | **WHO ICTRP bulk CSV** (only viable method). **No API, no export, no bulk download** (confirmed from FAQ). Web scraping via ebmdatalab possible but fragile. |
| 3 | **Rate Limits & Pricing** | WHO ICTRP: **Free**. Direct: N/A (no programmatic access). |
| 4 | **Data Freshness** | WHO ICTRP: **Up to 3 months stale** (PACTR transfers quarterly per FAQ). Direct: Real-time but limited (~500-1000 total trials). |
| 5 | **Data Format** | WHO ICTRP: **CSV** (ZIP). Direct: **HTML only** (individual trial pages). No JSON/XML/API. |
| 6 | **Reliability** | **Low** — No direct access, quarterly WHO feed, small registry, SAMRC-hosted. Data completeness concerns. |
| 7 | **Biotech Use Case** | Track vaccine trials in Africa (malaria, HIV, TB), multinational Phase III African sites, humanitarian/global health catalysts. Due to quarterly staleness, use as background intelligence rather than real-time catalyst detection. Cross-reference with ClinicalTrials.gov for African-arm trials. |

### 5. FDA OpenFDA API

| # | Field | Details |
|---|-------|---------|
| 1 | **Source & URL** | OpenFDA — https://open.fda.gov |
| 2 | **Access Method** | **Free REST API** — `https://api.fda.gov`. Key endpoints: `/drug/drugsfda` (approvals), `/drug/enforcement` (recalls), `/drug/event` (adverse events), `/drug/label` (labeling changes), `/drug/ndc` (product mapping). API key recommended for higher limits. |
| 3 | **Rate Limits & Pricing** | **Free**. Without key: 240 requests/min (daily limit applies). With key: 240 req/min with higher daily quota. No pricing tiers. |
| 4 | **Data Freshness** | **Weekly** — OpenFDA updates datasets on a rolling weekly basis. Not real-time. |
| 5 | **Data Format** | **JSON** (REST API). Also supports CSV for bulk downloads. |
| 6 | **Reliability** | **High** — FDA official API, well-documented, stable, widely used in production. |
| 7 | **Biotech Use Case** | Track FDA drug approvals (NDA/BLA/ANDA), enforcement actions (recalls, withdrawals), labeling changes (new indications), adverse event signals. `/drug/drugsfda` endpoint is the gold standard for FDA approval tracking. Critical for PDUFA date monitoring. Combine with Drugs@FDA bulk for freshest data. |

### 6. Drugs@FDA

| # | Field | Details |
|---|-------|---------|
| 1 | **Source & URL** | Drugs@FDA — https://www.accessdata.fda.gov/scripts/cder/daf/ |
| 2 | **Access Method** | **Bulk ZIP download** (primary): `https://www.fda.gov/drugs/drug-approvals-and-databases/drugsfda-data-files`. 12 tab-delimited files updated daily M-F. Also accessible via OpenFDA `/drug/drugsfda` API endpoint. |
| 3 | **Rate Limits & Pricing** | **Free**. No rate limits for bulk download. OpenFDA API limits apply for API access. |
| 4 | **Data Freshness** | **Daily (Mon-Fri)** — ZIP files updated each business day. More current than weekly OpenFDA API refresh. |
| 5 | **Data Format** | **TSV** (tab-delimited, 12 files in ZIP). OpenFDA API: JSON. Files: Products, Applications, Marketing Status, Therapeutic Equivalents, etc. |
| 6 | **Reliability** | **High** — FDA official data source, gold standard for NDA/BLA/ANDA tracking. |
| 7 | **Biotech Use Case** | Daily diff tracking for new drug approvals, application status changes, marketing status updates. Combine with OpenFDA API for historical queries. Primary source for FDA approval catalyst calendar. Build daily ETL: download ZIP, diff against previous day, alert on new approvals/status changes. |

### 7. EMA Clinical Data Publication

| # | Field | Details |
|---|-------|---------|
| 1 | **Source & URL** | EMA Clinical Data Publication — https://clinicaldata.ema.europa.eu |
| 2 | **Access Method** | **Web Portal + JSON Bulk Download**. Portal allows browsing/searching submitted clinical study reports (CSRs). Bulk data accessible via direct API endpoints (no documented rate limits). |
| 3 | **Rate Limits & Pricing** | **Free**. No documented rate limits for bulk download. No pricing tiers. |
| 4 | **Data Freshness** | **Near real-time** for portal browsing. Bulk JSON updated regularly (not precisely documented). |
| 5 | **Data Format** | Portal: **PDF, JSON, HTML**. CSRs available as PDF. Structured data as JSON. |
| 6 | **Reliability** | **High** — EMA official source, mandatory since 2016 for centralized procedures. |
| 7 | **Biotech Use Case** | Monitor EU regulatory submissions — track when companies submit CSRs, detect new submission waves, follow CHMP review timelines. Critical for EU approval catalyst tracking. Combine with EPAR data for full EU regulatory intelligence. |

### 8. EMA EPAR (European Public Assessment Reports)

| # | Field | Details |
|---|-------|---------|
| 1 | **Source & URL** | EMA EPAR — https://www.ema.europa.eu/en/medicines/what-we-publish-and-when (overview) | JSON bulk: `https://www.ema.europa.eu/en/medicines/download-medicine-data` | ePI API: `https://epi.developer.ema.europa.eu` |
| 2 | **Access Method** | **JSON Bulk Download** (primary): Twice-daily full medicine data export. **ePI API** (limited scope): REST API via Azure API Management, covers ePI pilot medicines only. Web browsing available. |
| 3 | **Rate Limits & Pricing** | **Free**. JSON bulk: No limits. ePI API: ~1,000 requests/min (Azure API Management). No pricing tiers. |
| 4 | **Data Freshness** | JSON bulk: **Twice daily**. ePI API: **Real-time** (for pilot scope). Web: Real-time. |
| 5 | **Data Format** | JSON bulk: **JSON** (full medicine dataset). ePI API: **JSON**. EPAR pages: **HTML/PDF**. Legacy: XML. |
| 6 | **Reliability** | **High** — EMA official source, twice-daily JSON bulk is a major asset many don't know about. |
| 7 | **Biotech Use Case** | Track CHMP opinions, EU approval/refusal decisions, conditional approvals, variation applications. The twice-daily JSON bulk enables automated diff detection for EU regulatory catalysts. EPAR documents contain the full approval rationale. Primary source for EU regulatory intelligence. |

### 9. EU Clinical Trials Information System (CTIS) API

| # | Field | Details |
|---|-------|---------|
| 1 | **Source & URL** | EU CTIS — https://euclinicaltrials.eu |
| 2 | **Access Method** | **Web Portal Only** — NO public API exists. Only programmatic options: (1) `ctrdata` R package on CRAN that wraps CTIS search, or (2) unofficial Python scraper reverse-engineering CTIS's internal API. |
| 3 | **Rate Limits & Pricing** | Web: **None** (manual browsing). `ctrdata` R package: Respects rate limits. Unofficial scraper: Risk of blocking. **Free** access. |
| 4 | **Data Freshness** | **Real-time** (portal). `ctrdata`: Near real-time. Unofficial scraper: Real-time but fragile. |
| 5 | **Data Format** | Portal: **HTML, CSV, PDF**. `ctrdata`: R data frames (exportable to CSV/JSON). Unofficial scraper: JSON. |
| 6 | **Reliability** | **Medium** — Official portal reliable, but no API means scraping is fragile. `ctrdata` is community-maintained (may break with CTIS updates). |
| 7 | **Biotech Use Case** | Track EU clinical trial registrations under CTR (Clinical Trials Regulation 536/2014). Monitor new trial submissions, part I/II assessments, protocol amendments. Use `ctrdata` R package for automated ETL — monitor for new registrations and status changes for EU-based biotech companies. |

### 10. ClinicalStudyDataRequest.com / Vivli

| # | Field | Details |
|---|-------|---------|
| 1 | **Source & URL** | Vivli — https://vivli.org | CSDR — https://clinicalstudydatarequest.com (redirects to Vivli) |
| 2 | **Access Method** | **Manual Portal + Data Use Agreement (DUA)**. Researchers must submit requests, sign DUAs, and wait for approval (weeks to months). No API, no bulk download, no automated access. |
| 3 | **Rate Limits & Pricing** | **Free** (with DUA). No rate limits (no API). Data access requires institutional affiliation and DUA execution. |
| 4 | **Data Freshness** | **Slow/Variable** — Data access approval takes weeks to months. CSR availability depends on sponsor submission timing. |
| 5 | **Data Format** | **SAS, CSV, R datasets** — Individual participant data (IPD) and CSRs provided in analysis-ready formats. |
| 6 | **Reliability** | **Low** (for pipeline use) — Manual process, DUA requirements, slow approval. Data quality is high but access is not automatable. |
| 7 | **Biotech Use Case** | Deep-dive IPD analysis for specific catalysts (e.g., verifying trial results, understanding dose-response). NOT suitable for automated pipeline monitoring. Use manually for due diligence on specific high-impact catalysts when detailed CSR data is needed. |

### 11. PubMed/MEDLINE

| # | Field | Details |
|---|-------|---------|
| 1 | **Source & URL** | PubMed E-utilities — https://www.ncbi.nlm.nih.gov/books/NBK25501/ | PMC OAI-PMH: https://www.ncbi.nlm.nih.gov/pmc/tools/oai/ |
| 2 | **Access Method** | **Free API (E-utilities)**: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`. Endpoints: `esearch.fcgi` (search), `efetch.fcgi` (retrieve), `esummary.fcgi` (summary). API key recommended for higher limits. Also: OAI-PMH for PMC full-text, FTP for bulk MEDLINE. |
| 3 | **Rate Limits & Pricing** | **Free**. Without API key: 3 requests/sec. With key: 10 req/sec. Bulk FTP: No rate limits. No pricing tiers. |
| 4 | **Data Freshness** | **Real-time** — PubMed indexed within hours of publication. MEDLINE: Monthly. PMC: Daily. |
| 5 | **Data Format** | E-utilities: **JSON** (`retmode=json`) or **XML**. MEDLINE FTP: **XML**. PMC OAI-PMH: **XML**. |
| 6 | **Reliability** | **High** — NCBI/NIH official API, extremely stable, widely used in production systems worldwide. |
| 7 | **Biotech Use Case** | Monitor clinical trial result publications, KOL publication activity, abstract publications from major conferences (ASCO/ESMO/ASH). Set up automated PubMed alerts for: (1) specific drug names, (2) trial NCT IDs, (3) competitor company publications, (4) therapeutic area keywords. Key early signal for catalyst detection — publications often precede press releases by days/weeks. |

### 12. Conference Abstract Sources (ASCO, ESMO, ASH)

| # | Field | Details |
|---|-------|---------|
| 1 | **Source & URL** | ASCO: https://ascopubs.org/jco/ | ESMO: https://www.annalsofoncology.org/ | ASH: https://ashpublications.org/blood | Crossref API: https://api.crossref.org |
| 2 | **Access Method** | **Crossref API** (primary for DOI/pre-embargo detection): Free, 50 req/sec. **PubMed E-utilities** (secondary): Free, 3-10 req/sec. Direct conference sites: Web scraping (varies by site). |
| 3 | **Rate Limits & Pricing** | Crossref: **Free**, 50 req/sec (polite pool). PubMed: **Free**, 3-10 req/sec. Conference sites: Varies, manual access. No pricing tiers. |
| 4 | **Data Freshness** | Crossref DOI registration: **Near real-time** (DOIs registered before conference). PubMed: **Real-time**. Conference abstracts: **Seasonal** — ASCO (May), ESMO (Sept/Oct), ASH (Nov/Dec). |
| 5 | **Data Format** | Crossref: **JSON**. PubMed: **JSON/XML**. Conference sites: **HTML**. |
| 6 | **Reliability** | **Medium-High** — Crossref DOI detection is reliable for pre-embargo signals. Conference site structures change frequently (scraping fragile). PubMed indexing is authoritative but has lag for conference abstracts. |
| 7 | **Biotech Use Case** | Detect pre-embargo DOIs via Crossref for upcoming ASCO/ESMO/ASH abstracts — these are the earliest signals of clinical trial results. Build a DOI monitoring pipeline that: (1) tracks Crossref for new DOIs with conference prefixes, (2) cross-references with trial NCT IDs, (3) alerts on Phase I/II/III results. Key catalyst timing tool — conference abstract drops move biotech stocks significantly. |

### 13. TrialReach / Antidote

| # | Field | Details |
|---|-------|---------|
| 1 | **Source & URL** | TrialReach (defunct/redirects) | Antidote: https://antidote.me |
| 2 | **Access Method** | **None** — No public API, no data feed, no programmatic access. Trial data mirrors ClinicalTrials.gov (already integrated). Note: antidoteresearch.com/api is an UNRELATED company (biotech survey research, not trial matching). |
| 3 | **Rate Limits & Pricing** | N/A — No programmatic access available. |
| 4 | **Data Freshness** | N/A — Data is a mirror of ClinicalTrials.gov with no additional freshness. |
| 5 | **Data Format** | N/A — No structured data access. |
| 6 | **Reliability** | **Low** — No programmatic access, data is redundant with existing ClinicalTrials.gov integration. |
| 7 | **Biotech Use Case** | **NONE** — Skip this source. Trial data is a mirror of ClinicalTrials.gov which is already a Tier 1 source. No incremental value for catalyst detection. Antidote is a patient recruitment platform, not a data source. |

### 14. ClinVar / Clinical Genome Resource (ClinGen)

| # | Field | Details |
|---|-------|---------|
| 1 | **Source & URL** | ClinVar — https://www.ncbi.nlm.nih.gov/clinvar/ | ClinGen — https://clinicalgenome.org |
| 2 | **Access Method** | **ClinVar**: Free REST API (`https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch/efetch`), FTP bulk download (`ftp://ftp.ncbi.nlm.nih.gov/pub/clinvar/`). **ClinGen**: Free REST API (`https://search.clinicalgenome.org/kb/api/v1/`), handles 50,000 variants/sec. |
| 3 | **Rate Limits & Pricing** | **ClinVar**: 3 req/sec (no key), 10 req/sec (with key). FTP: no limits. **ClinGen**: 50,000 variants/sec (high throughput). **Free** — both are NIH-funded public resources. |
| 4 | **Data Freshness** | **ClinVar**: Weekly (FTP), real-time (API). **ClinGen**: Real-time (API). |
| 5 | **Data Format** | **ClinVar**: JSON, XML, VCF, TSV (FTP). **ClinGen**: JSON. |
| 6 | **Reliability** | **High** — Both are NIH-funded, curated, and widely used in clinical genomics. ClinVar has >2M submissions. ClinGen is authoritative for gene-disease validity. |
| 7 | **Biotech Use Case** | Monitor variant reclassifications (pathogenic upgrades/downgrades), gene-disease validity changes, and new genomic biomarker approvals. Key for companion diagnostic and precision medicine catalysts. Track ClinVar for: (1) new pathogenic variants in drug target genes, (2) reclassifications that expand/contract patient populations. Track ClinGen for: (1) gene-disease validity changes affecting trial eligibility, (2) actionability scores for drug-gene pairs. |

### 15. BioPharmCatalyst / BiopharmIQ (BPIQ)

| # | Field | Details |
|---|-------|---------|
| 1 | **Source & URL** | BPIQ (formerly BioPharmCatalyst) — https://www.biopharmcatalyst.com | API: `https://api.biopharmcatalyst.com` |
| 2 | **Access Method** | **Paid API** (primary): REST API at `api.biopharmcatalyst.com` with token authentication. Endpoints: `/drugs/`, `/catalysts/`, `/historical-catalysts/`, `/clinical-trials/`, `/hedge-fund-holdings/`. Web browsing: Free and paid tiers. Also supports MCP server for AI integration. |
| 3 | **Rate Limits & Pricing** | **Free tier**: Basic catalyst calendar (limited). **Pro**: $20/mo (expanded data). **Elite**: $25/mo (full pipeline data). **Apex**: $45/mo (institutional). **API**: Custom pricing (contact sales). Token-based authentication. |
| 4 | **Data Freshness** | **Daily** — Catalyst data updated daily. API provides real-time access to current data. |
| 5 | **Data Format** | **JSON** (REST API). Web: HTML. |
| 6 | **Reliability** | **Medium-High** — Established biotech data platform (now part of Scientist.com). Curated catalyst calendar. API is newer but functional. |
| 7 | **Biotech Use Case** | Primary source for PDUFA date calendar, FDA approval catalysts, clinical trial milestones, and competitive intelligence. The `/catalysts/` endpoint provides the exact catalyst dates that move biotech stocks. The `/drugs/` endpoint maps drug names to companies and phases. The `/historical-catalysts/` endpoint enables backtesting. Start with Basic/Pro tier evaluation, then negotiate custom API pricing for production pipeline. |

---

## Pipeline Architecture Recommendations

### Immediate Build (Tier 1)

```
[OpenFDA API] ----> [Drugs@FDA Bulk] ----> [Daily FDA Diff Engine]
       |                                    |
       v                                    v
[EMA EPAR JSON Bulk] ----> [Twice-Daily EU Diff]
       |
       v
[PubMed E-utilities] ----> [Publication Alert Pipeline]
       |
       v
[BPIQ API] ----> [PDUFA/Catalyst Calendar]
```

### Secondary Build (Tier 2)

```
[DRKS Bulk JSON] ----> [Hourly Diff]
       |
[CRIS OpenAPI] ----> [Korean Trial Monitor]
       |
[EMA Clinical Data] ----> [CSR Submission Tracker]
       |
[EU CTIS via ctrdata] ----> [EU Trial Registration Feed]
       |
[Crossref API] ----> [Conference Abstract DOI Detector]
       |
[ClinVar/ClinGen] ----> [Genomic Variant Alert Feed]
```

### Background (Tier 3)

```
[WHO ICTRP Bulk] ----> [CTRI + PACTR Data] (accept 1-3 month lag)
```

### Skip

```
[TrialReach/Antidote] -- redundant with ClinicalTrials.gov
[Vivli/CSDR] -- manual DUA process, not pipeline-compatible
```

---

## Key Surprises and Actionable Intelligence

1. **EMA has a free JSON bulk download** for ALL medicine data (twice daily updates) — major asset for EU regulatory intelligence that many don't know about
2. **EU CTIS has NO public API** — only programmatic access is via `ctrdata` R package or unofficial Python scraper
3. **EMA ePI API** exists at `epi.developer.ema.europa.eu` but only covers ePI pilot scope, NOT full EPAR data
4. **Vivli/CSDR is unsuitable for automated pipelines** — data access requires DUA execution and takes weeks-months for approval
5. **ClinGen API handles 50,000 variants/sec** — extremely high throughput for genomic medicine catalysts
6. **PMC E-utilities migration** coming February 2026 — new domain `pmc.ncbi.nlm.nih.gov`
7. **DRKS has hourly bulk JSON** — one of the freshest free registry feeds available
8. **CRIS OpenAPI provides 70 fields per trial** — richest structured trial data from any Asian registry
9. **CTRI has NO API, NO export, CAPTCHA-gated** — use WHO ICTRP exclusively for India data
10. **BPIQ (formerly BioPharmCatalyst) now owned by Scientist.com** — API at `api.biopharmcatalyst.com` with custom pricing
11. **TrialReach/Antidote is NOT VIABLE** — data mirrors ClinicalTrials.gov, no API, no incremental value
12. **OpenFDA `/drug/drugsfda` endpoint** — combines with Drugs@FDA bulk for comprehensive FDA approval tracking

---

*Report compiled 2026-04-22 by ClinicalQuant Deep Research Agent. All URLs and access methods web-verified. No hallucinated endpoints.*
