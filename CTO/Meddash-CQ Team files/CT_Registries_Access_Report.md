# International Clinical Trial Registries — Programmatic Access Report

**Date**: 2026-04-22  
**Purpose**: Biotech catalyst newsletter — verified data source intelligence  
**Methodology**: Web research + primary source verification + GitHub scraper analysis  

---

## A) DRKS — German Clinical Trials Register

| # | Field | Details |
|---|-------|---------|
| 1 | **Source Name & URL** | DRKS (Deutsches Register Klinischer Studien) — https://drks.de |
| 2 | **Access Method** | **Bulk JSON download** (primary): `https://drks.de/search/en/download/all-json` returns ZIP containing JSON files. Search portal exports: CSV, RIS, JSON. Single records: PDF, XML. **No API exists** (confirmed by PLOS One PMC9249399). |
| 3 | **Rate Limits & Pricing** | **Free**. No rate limits documented. No pricing tiers (public/government registry). Max records per export: NOT SPECIFIED. Bulk download cache updated hourly. |
| 4 | **Data Freshness** | Bulk JSON: **Hourly** (includes newly registered studies). Search index: **Daily** (~5:45 AM). WHO ICTRP feed: ~1-2 weeks lag. |
| 5 | **Data Format** | Bulk: **JSON** (ZIP archive, `DRKS_all_YYYYMMDD.zip`). Schema available at `/search/download/jsonschema`. Search exports: **CSV, RIS, JSON**. Single record: **PDF, XML**. |
| 6 | **Reliability** | **High** — WHO Primary Registry, government-run (BfArM), ~20K studies, ~2K added/year, stable infrastructure, verified HTTP 200 on bulk endpoint. |
| 7 | **Biotech Newsletter Use Case** | German pharma/biotech trial tracking. Bulk JSON download ideal for ETL pipeline — download hourly, diff against previous snapshot to detect new registrations, phase changes, and sponsor activity for German-headquartered biotechs (BioNTech, Bayer, Merck KGaA, CureVac). Complement ClinicalTrials.gov for EU-based trial intelligence. |

### DRKS Access Tier Strategy
| Priority | Method | Freshness | Difficulty |
|----------|--------|-----------|------------|
| 1 | Bulk JSON download | Hourly | Low |
| 2 | Search portal CSV export | Daily | Low |
| 3 | WHO ICTRP bulk CSV | ~1-2 weeks | Low |
| 4 | Selenium scraper (historical) | Real-time | High |

---

## B) CTRI — Clinical Trial Registry of India

| # | Field | Details |
|---|-------|---------|
| 1 | **Source Name & URL** | CTRI (Clinical Trials Registry - India) — https://ctri.nic.in |
| 2 | **Access Method** | **WHO ICTRP bulk CSV** (recommended): Free monthly download covering all WHO registries. **Direct scraping**: Selenium + manual CAPTCHA solving + PDF extraction (extremely difficult). No API, no export, no bulk download exists. |
| 3 | **Rate Limits & Pricing** | WHO ICTRP: **Free** (bulk CSV). Direct scraping: Free but CAPTCHA-gated. No rate limits documented (because no API exists). Pricing: N/A (government registry, free access). |
| 4 | **Data Freshness** | Direct scrape: **Real-time** (if CAPTCHA solved). WHO ICTRP: **~1-2 weeks lag**. CTRI itself updates continuously but CAPTCHA blocks automated access. |
| 5 | **Data Format** | Direct: **PDF only** (must extract with pdfplumber). WHO ICTRP: **CSV** (ZIP archive). No JSON/XML API. 60+ fields extractable via scraper (CTRI Number, Registration Date, Titles, Phase, Sponsors, Outcomes). |
| 6 | **Reliability** | **Low** for direct access — CAPTCHA on search, PHP session-based navigation, no stable URLs for results, PDF-only data delivery. **Medium** via WHO ICTRP — data present but up to 2 weeks stale. |
| 7 | **Biotech Newsletter Use Case** | India is a major clinical trial hub (4th largest globally). Critical for tracking trials by Indian generics (Sun Pharma, Dr. Reddy's, Cipla) and multinational Phase III sites in India. WHO ICTRP is the pragmatic path — accept 1-2 week lag for comprehensive coverage. Direct scraping only for high-priority, time-sensitive catalysts (e.g., large Phase III results expected). |

### CTRI Access Tier Strategy
| Priority | Method | Freshness | Difficulty |
|----------|--------|-----------|------------|
| 1 | WHO ICTRP bulk CSV | ~1-2 weeks | Low |
| 2 | Selenium + CAPTCHA + pdfplumber | Real-time | Very High |
| 3 | ebmdatalab URL enumeration scraper | Real-time | High (BROKEN) |

### Known Scraper
- **CHACHA0044/CTRI_scrape** (GitHub): Selenium + manual CAPTCHA + pdfplumber, checkpoint/resume every 10 trials
- Trial URL pattern: `ctri.nic.in/Clinicaltrials/pmaindet2.php?trialid=XXXXX`
- **ebmdatalab scraper**: CONFIRMED BROKEN

---

## C) CRIS — Korean Clinical Research Information Service

| # | Field | Details |
|---|-------|---------|
| 1 | **Source Name & URL** | CRIS (Clinical Research Information Service) — https://cris.nih.go.kr / https://nih.go.kr/eng |
| 2 | **Access Method** | **data.go.kr OpenAPI** (primary): Two verified endpoints for clinical research data. Free serviceKey from Korean government portal registration. Also: WHO ICTRP bulk CSV (alternative). |
| 3 | **Rate Limits & Pricing** | data.go.kr OpenAPI: **Free** with registration. Rate limit: ~1,000 calls/day (data.go.kr standard, [UNVERIFIED for this specific dataset]). Pricing: N/A (government open data). |
| 4 | **Data Freshness** | OpenAPI: **Real-time** (direct database access). WHO ICTRP: ~1-2 weeks lag. |
| 5 | **Data Format** | OpenAPI: **JSON** (via `resultType=json` param). List endpoint returns 16 fields per record. Detail endpoint returns 70 fields per record. Response in JSON or XML. |
| 6 | **Reliability** | **High** — Government-operated OpenAPI with structured endpoints, 70 fields per trial detail, WHO Primary Registry, Korean government backing (KDCA/MOHW). |
| 7 | **Biotech Newsletter Use Case** | South Korea is a growing biotech hub (Samsung Biologics, Celltrion, SK Biopharm). CRIS OpenAPI enables real-time monitoring of Korean clinical trials, particularly biosimilar development (Celltrion's Herzuma, Inflectra), cell/gene therapy programs, and K-pharma pipeline catalysts. Ideal for automated ETL with structured JSON output. |

### CRIS OpenAPI Details (VERIFIED)

**Dataset 1 — Clinical Research DB (ID: 3033869)**:
- List: `http://apis.data.go.kr/1352159/crisinfodataview/list`
  - Method: GET
  - Params: `serviceKey` (required), `resultType=json`, `srchWord`, `numOfRows` (1-50), `pageNo`
  - Returns: 16 fields per record

- Detail: `http://apis.data.go.kr/1352159/crisinfodataview/detail`
  - Method: GET
  - Params: `serviceKey` (required), `resultType=json`, `crisNumber` (required)
  - Returns: 70 fields per record

**Dataset 2 — Registration Statistics (ID: 3074275)**:
- Statistics API: [UNVERIFIED exact endpoint] — 18 statistical fields

**Third-Party Integration**: K-CRIS MCP Server (GitHub: HyeonhoonLee/kcris-mcp-server) provides LLM-compatible access.

### CRIS Access Tier Strategy
| Priority | Method | Freshness | Difficulty |
|----------|--------|-----------|------------|
| 1 | data.go.kr OpenAPI | Real-time | Low |
| 2 | WHO ICTRP bulk CSV | ~1-2 weeks | Low |
| 3 | ebmdatalab Scrapy + XML scraper | Real-time | Medium |

---

## D) PACTR — Pan African Clinical Trials Registry

| # | Field | Details |
|---|-------|---------|
| 1 | **Source Name & URL** | PACTR (Pan African Clinical Trials Registry) — https://pactr.org / https://pactr.samrc.ac.za |
| 2 | **Access Method** | **WHO ICTRP bulk CSV** (only viable method): Free monthly download. **No API, no export, no bulk download** on PACTR directly (confirmed from FAQ). Web scraping via ebmdatalab (page-by-page extraction) possible but fragile. |
| 3 | **Rate Limits & Pricing** | WHO ICTRP: **Free** (bulk CSV). Direct PACTR: N/A (no programmatic access). Web scraping: No documented rate limits but site is fragile/low-traffic. |
| 4 | **Data Freshness** | WHO ICTRP: **Up to 3 months stale** (PACTR transfers data quarterly per FAQ). Direct scraping: Real-time but very limited coverage (~500-1000 trials total). |
| 5 | **Data Format** | WHO ICTRP: **CSV** (ZIP archive). Direct: **HTML only** (individual trial pages at `pactr.samrc.ac.za/TrialDisplay.aspx?TrialID=XXXXX`). No JSON/XML/API. |
| 6 | **Reliability** | **Low** for direct access — no API, no export, no bulk download, quarterly WHO feed. PACTR is SAMRC-hosted (South African Medical Research Council), small registry. Data quality and completeness concerns for African trials. |
| 7 | **Biotech Newsletter Use Case** | Africa is an emerging clinical trial market. PACTR data is relevant for tracking: (1) vaccine trials in Africa (malaria, HIV, TB), (2) multinational Phase III programs with African sites, (3) humanitarian/global health biotech catalysts. Due to quarterly data staleness, PACTR is best used as background intelligence rather than real-time catalyst detection. Cross-reference with ClinicalTrials.gov for African-arm trials. |

### PACTR Access Tier Strategy
| Priority | Method | Freshness | Difficulty |
|----------|--------|-----------|------------|
| 1 | WHO ICTRP bulk CSV | Up to 3 months | Low |
| 2 | Web scraping (ebmdatalab) | Real-time | Medium |
| 3 | Manual web search | Real-time | Very High |

---

## Cross-Registry Comparison Matrix

| Dimension | DRKS (DE) | CTRI (IN) | CRIS (KR) | PACTR (AF) |
|-----------|-----------|-----------|-----------|------------|
| **Best Access** | Bulk JSON | WHO ICTRP | OpenAPI | WHO ICTRP |
| **Access Difficulty** | Low | Very High | Low | N/A (indirect) |
| **Data Format** | JSON | PDF/CSV | JSON | HTML/CSV |
| **Freshness** | Hourly | 1-2 weeks | Real-time | 3 months |
| **Reliability** | High | Low (direct) / Med (ICTRP) | High | Low |
| **Cost** | Free | Free | Free | Free |
| **WHO ICTRP Lag** | ~1-2 weeks | ~1-2 weeks | ~1-2 weeks | **~3 months** |
| **Fields Available** | ~100+ | 60+ (via scrape) | 70 (API detail) | ~20 (WHO set) |

---

## Pipeline Integration Recommendations

### Tier 1 — Build Now (Universal Backbone)
1. **ClinicalTrials.gov API v2** — Primary data source (already in pipeline)
2. **WHO ICTRP Bulk CSV** — Monthly download, covers all 4 registries + 13 more

### Tier 2 — Direct Access (Structured APIs/Downloads)
3. **DRKS Bulk JSON** — Hourly download, diff for new/changed trials
4. **CRIS data.go.kr OpenAPI** — Real-time API with 70 fields, requires free registration

### Tier 3 — Indirect Access (WHO ICTRP Only)
5. **CTRI** — Accept 1-2 week lag via WHO ICTRP; direct scraping only for high-priority catalysts
6. **PACTR** — Accept quarterly lag via WHO ICTRP; supplement with ClinicalTrials.gov for African-arm trials

### Key URLs
| Resource | URL |
|----------|-----|
| DRKS Bulk JSON | https://drks.de/search/en/download/all-json |
| DRKS JSON Schema | https://drks.de/search/download/jsonschema |
| CRIS OpenAPI List | http://apis.data.go.kr/1352159/crisinfodataview/list |
| CRIS OpenAPI Detail | http://apis.data.go.kr/1352159/crisinfodataview/detail |
| CRIS data.go.kr | https://www.data.go.kr/data/3033869/openapi.do |
| WHO ICTRP Search | https://trialsearch.who.int/ |
| WHO ICTRP Download | https://www.who.int/tools/clinical-trials-registry-platform/network/who-data-set/downloading-records-from-the-ictrp-database |
| PACTR Search | https://pactr.samrc.ac.za/Search.aspx |
| CTRI Search | https://ctri.nic.in/Clinicaltrials/advancesearchmain.php |

---

*Report generated 2026-04-22 | All URLs verified via web research. Items marked [UNVERIFIED] could not be independently confirmed from primary sources.*
