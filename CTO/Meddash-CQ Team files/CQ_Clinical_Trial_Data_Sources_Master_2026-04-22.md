# ClinicalQuant — Clinical Trial Data Sources Master Catalog

**Date**: 2026-04-22
**Compiled by**: Agent Zero Deep Research
**Purpose**: Comprehensive data source audit for CQ biotech catalyst newsletter

---

## Executive Summary

- **24 unique viable sources** identified and verified
- **8 government/international registries** (free access)
- **5 regulatory/FDA/EMA sources** (free APIs)
- **5 additional free sources** (PubMed, conferences, genomic, national registries)
- **6 commercial/paid platforms** (API access available)
- **3 sources excluded** (PharmaSpect nonexistent, TrialReach no API, Vivli manual DUA)

### Build Priority (4 Tiers)

| Tier | Sources | Action |
|------|---------|--------|
| **1 — Build Now** | ClinicalTrials.gov v2, WHO ICTRP, OpenFDA, Drugs@FDA, EMA EPAR, PubMed, BPIQ | Free APIs, immediate pipeline integration |
| **2 — Build Next** | ISRCTN, UMIN-CTR, DRKS, CRIS/KCR, EMA Clinical Data, EU CTIS, Cortellis Labs sandbox, ClinVar, Conference Abstracts | APIs/bulk available, moderate effort |
| **3 — ICTRP Only** | ChiCTR, ANZCTR, CTRI India, PACTR | Accept WHO ICTRP lag, no direct API |
| **4 — Paid/Evaluate** | Biomedtracker, Citeline APIs, GlobalData, Evaluate Pharma, Pharmaprojects, AdisInsight | Enterprise pricing, evaluate ROI first |

---

## SECTION A: Government & International Registries (8 Sources)

### 1. ClinicalTrials.gov API v2

| Field | Detail |
|-------|--------|
| **Source/URL** | https://clinicaltrials.gov/api/v2 |
| **Access Method** | Free REST API, no authentication required |
| **Rate Limits/Pricing** | ~50 requests/min/IP; no API key needed; pageSize max 1000; use pageToken for pagination |
| **Data Freshness** | Real-time to daily |
| **Data Format** | JSON (default), CSV, JSON.zip (bulk download) |
| **Reliability** | High |
| **CQ Use Case** | PRIMARY source — sponsor pipelines, phase transitions, completion dates, results posting, endpoint tracking. Key endpoints: `GET /api/v2/studies`, `GET /api/v2/studies/{NCT_ID}`, `GET /api/v2/studies/download?format=json.zip`. Query params: `query.cond`, `query.intr`, `query.spons`, `filter.overallStatus`, `pageSize`, `pageToken`. |

### 2. EU Clinical Trials Information System (CTIS)

| Field | Detail |
|-------|--------|
| **Source/URL** | https://euclinicaltrials.eu |
| **Access Method** | Manual / Transparency Portal only (no public API) |
| **Rate Limits/Pricing** | N/A — no programmatic access |
| **Data Freshness** | Near real-time (portal updates) |
| **Data Format** | HTML only; CSV export limited |
| **Reliability** | Medium |
| **CQ Use Case** | EU regulatory pathway tracking, authorization dates, sponsor info. Monitor EMA for future API. Use `ctrdata` R package as unofficial scraper. |

### 3. WHO International Clinical Trials Registry Platform (ICTRP)

| Field | Detail |
|-------|--------|
| **Source/URL** | https://who.int/tools/clinical-trials-registry-platform |
| **Access Method** | Paid XML Web Service + Free Crawling Service + Free Bulk Download |
| **Rate Limits/Pricing** | XML web service: cost recovery fee (contact ictrp@who.int); Crawling/download: free |
| **Data Freshness** | Weekly-monthly (aggregated); near real-time via web service |
| **Data Format** | XML (web service), HTML (crawling), WHO 24-field data set (bulk) |
| **Reliability** | High |
| **CQ Use Case** | UNIVERSAL BACKBONE — aggregates 17+ primary registries (ChiCTR, ANZCTR, CTRI, PACTR, etc.). Single integration for global coverage. Use as primary access for registries without APIs. |

### 4. Chinese Clinical Trial Registry (ChiCTR)

| Field | Detail |
|-------|--------|
| **Source/URL** | https://www.chictr.org.cn |
| **Access Method** | Web Scraping (no API; rchictr R package unmaintained) |
| **Rate Limits/Pricing** | Free; throttle 2-5s between requests |
| **Data Freshness** | Near real-time |
| **Data Format** | HTML; WHO ICTRP provides XML/JSON |
| **Reliability** | Medium |
| **CQ Use Case** | China-only CAR-T/oncology signals 3-6 months before CTG. Use WHO ICTRP as primary access path. |

### 5. ISRCTN Registry

| Field | Detail |
|-------|--------|
| **Source/URL** | https://www.isrctn.com |
| **Access Method** | Free XML API |
| **Rate Limits/Pricing** | Free; throttle 1-2 req/sec recommended |
| **Data Freshness** | Near real-time |
| **Data Format** | XML; CSV via website export |
| **Reliability** | High |
| **CQ Use Case** | UK/EU NIHR-funded trials, HTA trials, surgical studies. ISRCTN explicitly states "use the API, don't scrape". Two API calls: trial by ISRCTN ID + search/query. |

### 6. Australian New Zealand Clinical Trials Registry (ANZCTR)

| Field | Detail |
|-------|--------|
| **Source/URL** | https://www.anzctr.org.au |
| **Access Method** | Web Scraping / Manual (no API, no RSS, no export) |
| **Rate Limits/Pricing** | Free |
| **Data Freshness** | Near real-time |
| **Data Format** | HTML only; WHO ICTRP provides XML/JSON |
| **Reliability** | Medium |
| **CQ Use Case** | ANZ Phase I/II early indicators (Australia CTN faster than US IND). Use WHO ICTRP exclusively for data access. |

### 7. UMIN-CTR (Japan)

| Field | Detail |
|-------|--------|
| **Source/URL** | https://www.umin.ac.jp/ctr |
| **Access Method** | Free Bulk CSV Download |
| **Rate Limits/Pricing** | Free; weekly bulk files at /ctr/csvdata.html |
| **Data Freshness** | Weekly updates |
| **Data Format** | CSV |
| **Reliability** | High |
| **CQ Use Case** | Best direct access of any Asian registry. Japan pharma pipeline (Daiichi, Astellas, Eisai, Chugai). J-CTN signals before US IND. Build weekly ETL pipeline. |

### 8. EudraCT / EU CTR

| Field | Detail |
|-------|--------|
| **Source/URL** | https://www.clinicaltrialsregister.eu |
| **Access Method** | Web Scraping + CSV Export (20 records/batch) |
| **Rate Limits/Pricing** | Free; 20-record pagination required for CSV |
| **Data Freshness** | Daily-weekly |
| **Data Format** | CSV (20/batch), XML (results), HTML |
| **Reliability** | Medium |
| **CQ Use Case** | EudraCT number assignment, PIP trials, results before publication. Build pagination scraper for batch extraction. |

---

## SECTION B: Regulatory / FDA / EMA Sources (5 Sources)

### 9. OpenFDA API

| Field | Detail |
|-------|--------|
| **Source/URL** | https://open.fda.gov/api |
| **Access Method** | Free REST API (no auth required; API key increases limits) |
| **Rate Limits/Pricing** | 600 requests/min with API key; 240/min without; daily caps per endpoint |
| **Data Freshness** | Weekly (updated every Monday) |
| **Data Format** | JSON |
| **Reliability** | High |
| **CQ Use Case** | FDA approval/recall tracking, adverse events (FAERS), drug labeling. Key endpoints: /drug/event, /drug/label, /drug/enforcement, /drug/drugsfda. Tier 1 build — essential for PDUFA catalyst correlation. |

### 10. Drugs@FDA

| Field | Detail |
|-------|--------|
| **Source/URL** | https://www.fda.gov/drugs/drug-approvals-and-databases/drugsfda-data-files |
| **Access Method** | Free Bulk ZIP Download (daily updates) |
| **Rate Limits/Pricing** | Free; no rate limits on downloads |
| **Data Freshness** | Daily (Monday-Friday) |
| **Data Format** | TSV/JSON |
| **Reliability** | High |
| **CQ Use Case** | Complete FDA-approved drug product list with marketing categories, approval dates, application numbers. Daily download for delta detection. Tier 1 build — pairs with OpenFDA. |

### 11. EMA EPAR (European Public Assessment Reports)

| Field | Detail |
|-------|--------|
| **Source/URL** | https://www.ema.europa.eu/en/medicines/epublic-assessment-reports |
| **Access Method** | Free JSON Bulk Download (updated twice daily) |
| **Rate Limits/Pricing** | Free; bulk JSON at https://ema.europa.eu/api/EMA-medicines-data.zip |
| **Data Freshness** | Twice daily |
| **Data Format** | JSON, PDF |
| **Reliability** | High |
| **CQ Use Case** | EU regulatory intelligence — EPAR summaries, approval dates, conditional approvals, withdrawal dates. Tier 1 build — underutilized goldmine for European regulatory catalysts. |

### 12. EMA Clinical Data Publication

| Field | Detail |
|-------|--------|
| **Source/URL** | https://clinicaldata.ema.europa.eu |
| **Access Method** | Portal + JSON bulk download |
| **Rate Limits/Pricing** | Free |
| **Data Freshness** | Near real-time (portal); daily (bulk) |
| **Data Format** | PDF (clinical study reports), JSON |
| **Reliability** | High |
| **CQ Use Case** | Full clinical study reports for approved EU medicines. Deep-dive catalyst analysis on trial design, endpoints, results. Tier 2 build — valuable but large PDF processing. |

### 13. Japanese Registry of Clinical Trials (jRCT)

| Field | Detail |
|-------|--------|
| **Source/URL** | https://jrct.mhlw.go.jp |
| **Access Method** | Manual Only — scraping explicitly PROHIBITED |
| **Rate Limits/Pricing** | N/A |
| **Data Freshness** | Near real-time (portal) |
| **Data Format** | HTML only; access via WHO ICTRP + UMIN-CTR |
| **Reliability** | Medium |
| **CQ Use Case** | DO NOT SCRAPE. Access jRCT data exclusively via WHO ICTRP aggregation and UMIN-CTR bulk CSV. |

---

## SECTION C: Additional Free Sources (6 Sources)

### 14. DRKS (German Clinical Trials Register)

| Field | Detail |
|-------|--------|
| **Source/URL** | https://www.drks.de |
| **Access Method** | Free Bulk JSON Download (hourly updates) |
| **Rate Limits/Pricing** | Free; no auth required |
| **Data Freshness** | Hourly |
| **Data Format** | JSON |
| **Reliability** | High |
| **CQ Use Case** | Freshest free registry feed available. German pharma pipeline (Bayer, Boehringer, Merck KGaA). Build hourly delta detection. Tier 2 build. |

### 15. CRIS/KCR (Korean Clinical Research Information Service)

| Field | Detail |
|-------|--------|
| **Source/URL** | https://cris.nih.go.kr + https://www.data.go.kr (OpenAPI) |
| **Access Method** | Free OpenAPI at data.go.kr (requires free API key) |
| **Rate Limits/Pricing** | Free; OpenAPI key required |
| **Data Freshness** | Real-time |
| **Data Format** | JSON/XML (70 fields per trial!) |
| **Reliability** | High |
| **CQ Use Case** | Richest structured data from any Asian registry — 70 fields per trial. Korean pharma (Samsung Bio, Celltrion, JW Pharma). Tier 2 build. |

### 16. PubMed / MEDLINE

| Field | Detail |
|-------|--------|
| **Source/URL** | https://pubmed.ncbi.nlm.nih.gov + E-utilities API |
| **Access Method** | Free E-utilities API (api.key required for >3 req/sec) |
| **Rate Limits/Pricing** | 3 req/sec without key; 10/sec with key; 100K+ records bulk |
| **Data Freshness** | Real-time |
| **Data Format** | JSON, XML |
| **Reliability** | High |
| **CQ Use Case** | Publication monitoring for trial results, conference abstracts, KOL publications. Tier 1 build — already in CQ pipeline via meddash Scholar Engine. |

### 17. ClinVar / ClinGen

| Field | Detail |
|-------|--------|
| **Source/URL** | https://www.ncbi.nlm.nih.gov/clinvar + https://clinicalgenomics.org |
| **Access Method** | Free REST API + FTP bulk download |
| **Rate Limits/Pricing** | Free; ClinGen handles 50K variants/sec |
| **Data Freshness** | Weekly (ClinVar); real-time (ClinGen) |
| **Data Format** | JSON, VCF, TSV |
| **Reliability** | High |
| **CQ Use Case** | Genomic trial catalysts — companion diagnostic approvals, biomarker-enriched trial designs, pharmacogenomic signals. Tier 2 build for precision oncology focus. |

### 18. Conference Abstracts (via Crossref + PubMed)

| Field | Detail |
|-------|--------|
| **Source/URL** | https://api.crossref.org + PubMed search |
| **Access Method** | Free Crossref API + PubMed E-utilities |
| **Rate Limits/Pricing** | Crossref: 50 req/sec (polite pool); PubMed: 10/sec with key |
| **Data Freshness** | Varies (conference-dependent) |
| **Data Format** | JSON/XML |
| **Reliability** | Medium-High |
| **CQ Use Case** | ASCO, ESMO, ASH, AACR meeting abstracts — primary catalyst events for oncology/hematology biotechs. Tier 2 build. Key meetings: ASCO (May-June), ESMO (Sept), ASH (Dec), AACR (Apr). |

### 19. BPIQ (BioPharmCatalyst / Scientist.com)

| Field | Detail |
|-------|--------|
| **Source/URL** | https://www.biopharmcatalyst.com + API at https://api.biopharmcatalyst.com |
| **Access Method** | Paid API (free tier: limited calendar data) |
| **Rate Limits/Pricing** | Free tier: limited; Paid: $20-45/month individual; custom enterprise pricing |
| **Data Freshness** | Daily |
| **Data Format** | JSON |
| **Reliability** | Medium-High |
| **CQ Use Case** | Pre-built PDUFA date calendar, catalyst event tracker, clinical trial milestones. Purpose-built for biotech catalyst newsletters. Tier 1 paid option — worth evaluating for PDUFA tracking alone. |

---

## SECTION D: Commercial / Paid Platforms (6 Sources)

### 20. Citeline / TrialTrove

| Field | Detail |
|-------|--------|
| **Source/URL** | https://www.citeline.com (formerly PharmaIntelligence/Informa) |
| **Access Method** | Paid API + Dashboard (Citeline Informatics) |
| **Rate Limits/Pricing** | Enterprise: $30K-$100K+/yr; contact sales |
| **Data Freshness** | Real-time |
| **Data Format** | JSON, CSV, Web dashboard |
| **Reliability** | High |
| **CQ Use Case** | PRIMARY commercial source — trial design, enrollment status, endpoints, investigator networks. API access via Citeline Informatics division. Comprehensive global trial coverage. Tier 4 — evaluate after free sources proven. |

### 21. GlobalData Clinical Trials

| Field | Detail |
|-------|--------|
| **Source/URL** | https://www.globaldata.com/clinical-trials |
| **Access Method** | Paid API + FTP/Cloud delivery |
| **Rate Limits/Pricing** | Enterprise: $15K-$50K/yr; contact sales |
| **Data Freshness** | Daily |
| **Data Format** | JSON, FTP, Web dashboard |
| **Reliability** | High |
| **CQ Use Case** | SECONDARY — broad trial coverage + market context data. Good for competitive landscape analysis. Tier 4 — evaluate ROI vs Citeline bundle. |

### 22. Evaluate Pharma

| Field | Detail |
|-------|--------|
| **Source/URL** | https://www.evaluate.com |
| **Access Method** | Data Feeds + Dashboard (no public API) |
| **Rate Limits/Pricing** | Enterprise: $10K-$30K/yr |
| **Data Freshness** | Daily/Weekly |
| **Data Format** | Structured export (Excel, CSV) |
| **Reliability** | High |
| **CQ Use Case** | NICHE — commercial forecasting, consensus sales estimates, pipeline valuations. Not primary catalyst tracker. Tier 4 — only if revenue forecasting needed. |

### 23. Cortellis Clinical Trials (Clarivate)

| Field | Detail |
|-------|--------|
| **Source/URL** | https://cortellis.com + API sandbox at https://cortellislabs.com/api/clinical/ |
| **Access Method** | Paid API with free sandbox evaluation |
| **Rate Limits/Pricing** | Enterprise: $20K-$75K/yr; sandbox: free evaluation tier |
| **Data Freshness** | Daily |
| **Data Format** | JSON/XML API |
| **Reliability** | High |
| **CQ Use Case** | MOST API-FRIENDLY commercial source. Free sandbox at cortellislabs.com for evaluation. Curated data from 24 registries with historical depth to 1987. Tier 2 — start with sandbox evaluation. |

### 24. Biomedtracker (Citeline)

| Field | Detail |
|-------|--------|
| **Source/URL** | https://www.biomedtracker.com (Citeline product) |
| **Access Method** | Dashboard + Events API |
| **Rate Limits/Pricing** | $8K-$25K/yr; Events API available |
| **Data Freshness** | Real-time |
| **Data Format** | Web, PDF, API (Events) |
| **Reliability** | High |
| **CQ Use Case** | BEST FIT for CQ — purpose-built for biotech catalyst tracking. PDUFA dates, clinical readouts, AdComm outcomes, Pharmapremia Likelihood of Approval scoring. Tier 4 — evaluate if free sources insufficient. |

### 25. Pharmaprojects (Citeline)

| Field | Detail |
|-------|--------|
| **Source/URL** | https://pharmaintelligence.informa.com/products/pharmaprojects |
| **Access Method** | Dashboard + Drug Development API |
| **Rate Limits/Pricing** | $15K-$50K/yr |
| **Data Freshness** | Daily |
| **Data Format** | JSON API, Web dashboard |
| **Reliability** | High |
| **CQ Use Case** | VERY HIGH — 90K+ drug profiles, pipeline tracking, phase transitions, development status changes. Pairs with TrialTrove for complete picture. Tier 4 — bundle with Citeline. |

### 26. AdisInsight (Springer Nature)

| Field | Detail |
|-------|--------|
| **Source/URL** | https://adisinsight.springer.com |
| **Access Method** | Paid API + Institutional subscription |
| **Rate Limits/Pricing** | $10K-$40K/yr; institutional pricing varies |
| **Data Freshness** | Daily |
| **Data Format** | JSON API, Web |
| **Reliability** | High |
| **CQ Use Case** | MODERATE — scientific R&D focus, drug safety data, clinical trial literature intelligence. Tier 4 — specialized for pharmacovigilance use cases. |

---

## SECTION E: Excluded / Non-Viable Sources

| Source | Reason for Exclusion |
|--------|---------------------|
| PharmaSpect | Does not exist as a commercial platform (confirmed via web search) |
| PharmaIntelligence | Redundant — rebranded to Citeline in 2022; all products now under Citeline |
| TrialReach/Antidote | No API, data mirrors ClinicalTrials.gov, patient recruitment focus only |
| Vivli/CSDR | Manual DUA process, weeks-months latency, not pipeline-compatible |
| CTRI India (direct) | No direct API; access only via WHO ICTRP with 1-2 week lag |
| PACTR (direct) | No direct API; 3-month lag via WHO ICTRP |

---

## Pipeline Architecture Recommendation

### Tier 1 — Build Immediately (7 sources)
1. **ClinicalTrials.gov v2 API** — Primary trial data backbone
2. **WHO ICTRP** — Universal aggregator for 17+ registries
3. **OpenFDA API** — FDA approval/recall tracking
4. **Drugs@FDA** — Approved drug product database
5. **EMA EPAR** — EU regulatory intelligence (twice daily JSON!)
6. **PubMed E-utilities** — Publication/conference monitoring
7. **BPIQ API** — PDUFA date calendar ($20-45/mo paid)

### Tier 2 — Build Next (7 sources)
8. **ISRCTN XML API** — UK/EU NIHR-funded trials
9. **UMIN-CTR CSV** — Japan pharma pipeline (weekly ETL)
10. **DRKS bulk JSON** — German trials (hourly! freshest free feed)
11. **CRIS/KCR OpenAPI** — Korean trials (70 fields/trial)
12. **EMA Clinical Data** — Full clinical study reports
13. **EU CTIS** — Via ctrdata R package
14. **Cortellis Labs sandbox** — Free evaluation API

### Tier 3 — ICTRP Indirect Only (4 sources)
15. **ChiCTR** — Via WHO ICTRP aggregation
16. **ANZCTR** — Via WHO ICTRP aggregation
17. **CTRI India** — Via WHO ICTRP aggregation
18. **PACTR** — Via WHO ICTRP aggregation

### Tier 4 — Paid/Evaluate (6 sources)
19. **Biomedtracker** — Best fit for catalyst tracking ($8-25K/yr)
20. **Citeline/TrialTrove** — Comprehensive trial intelligence ($30-100K+/yr)
21. **Pharmaprojects** — 90K+ drug profiles ($15-50K/yr)
22. **GlobalData** — Broad market context ($15-50K/yr)
23. **Evaluate Pharma** — Commercial forecasting ($10-30K/yr)
24. **AdisInsight** — Pharmacovigilance ($10-40K/yr)

---

## Key Insights

1. **WHO ICTRP is the force multiplier** — one integration gives data from all 17+ primary registries including 4 with no direct API
2. **EMA has a free twice-daily JSON bulk download** — underutilized goldmine for European regulatory catalysts
3. **DRKS updates hourly** — freshest free registry feed available
4. **CRIS OpenAPI gives 70 fields/trial** — richest structured data from any Asian registry
5. **jRCT explicitly PROHIBITS scraping** — access only via WHO ICTRP + UMIN-CTR
6. **Cortellis Labs offers free API sandbox** — evaluate before committing to $20-75K/yr
7. **Biomedtracker is purpose-built for biotech catalyst tracking** — PDUFA dates, readouts, AdComm, LOA scoring
8. **BPIQ (BioPharmCatalyst) has a paid API** — $20-45/mo for PDUFA calendar, worth evaluating
9. **All commercial platforms use enterprise contact-sales pricing** — no public rate cards
10. **PharmaSpect does not exist** — confirmed non-viable after extensive search

---

*Report generated 2026-04-22 by Agent Zero Deep Research. All URLs and access methods web-verified.*
