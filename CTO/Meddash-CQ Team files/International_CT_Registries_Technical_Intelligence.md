# International Clinical Trial Registries — Technical Intelligence Report

**Date**: 2026-04-21  
**Purpose**: Biotech market intelligence newsletter — verified programmatic access details  
**Status**: All findings verified via web research; unverified items marked [UNVERIFIED]

---

## A) DRKS — German Clinical Trials Register
**URL**: https://drks.de  
**WHO Status**: Primary Registry  
**Study Count**: ~20K, ~2K added/year

### API / Developer Access
- **NO API EXISTS** — Confirmed by PLOS One (PMC9249399): *"DRKS.de does not provide an API at all"* and Zenodo (7590083)
- No developer documentation of any kind

### Bulk Data Download (URLs VERIFIED via HTTP HEAD)

| URL | Returns | Status |
|-----|---------|--------|
| `https://drks.de/search/en/download/all-json` | `DRKS_all_YYYYMMDD.zip` (ZIP containing JSON) | HTTP 200 confirmed |
| `https://drks.de/search/download/jsonschema` | `DRKS_Schema-2.0.19.json` (28,996 bytes) | HTTP 200 confirmed |

### Search Result Export Formats
- **Bulk**: JSON, CSV, RIS (via download button on search results page)
- **Single records only**: PDF, XML (reduced dataset designed for WHO ICTRP transfer)

### Data Freshness
- Search index: Daily at ~5:45 AM (new studies appear next day)
- Bulk download cache: **Hourly** (includes newly registered studies)

### Limitations
- Max records per export: **NOT SPECIFIED** in documentation
- Rate limits: **NOT MENTIONED**
- Historical/version data: **NOT AVAILABLE** — web scraping required

### Access Strategy
| Priority | Method | Freshness | Difficulty |
|----------|--------|-----------|------------|
| 1 | Bulk JSON download (`/search/en/download/all-json`) | Hourly | Low |
| 2 | Search portal CSV export | Daily | Low |
| 3 | WHO ICTRP bulk CSV | ~1-2 weeks | Low |
| 4 | Selenium scraper (historical data) | Real-time | High |

---

## B) CTRI — Clinical Trial Registry of India
**URL**: https://ctri.nic.in  
**WHO Status**: Primary Registry  
**Host**: ICMR's National Institute for Research in Digital Health and Data Science

### API / Developer Access
- **NO API, NO export, NO bulk download** — VERIFIED across multiple sources
- No developer documentation

### Scraping Difficulty: VERY HIGH
- **CAPTCHA** on search page — manual solving required before any search
- **PHP session-based navigation** — results not directly addressable by URL
- **PDF extraction required** — data only available via generated PDFs, must use pdfplumber
- Trial page URL pattern: `ctri.nic.in/Clinicaltrials/pmaindet2.php?trialid=XXXXX`

### Known Scraper
- GitHub: `CHACHA0044/CTRI_scrape`
- Approach: Selenium + manual CAPTCHA + pdfplumber
- 60+ fields extractable including CTRI Number, Registration Date, Titles, Study Design, Phase, Sponsors, Contacts, Outcomes
- Checkpoint/resume automatic (saves every 10 trials)

### Access Strategy
| Priority | Method | Freshness | Difficulty |
|----------|--------|-----------|------------|
| 1 | WHO ICTRP bulk CSV download | ~1-2 weeks | Low |
| 2 | Selenium + CAPTCHA + pdfplumber scraper | Real-time | Very High |
| 3 | ebmdatalab URL enumeration scraper | Real-time | High (BROKEN) |

---

## C) KCR/CRIS — Korean Clinical Research Information Service
**URL**: https://cris.nih.go.kr  
**WHO Status**: Primary Registry (non-profit)

### data.go.kr OpenAPI — VERIFIED
Two datasets available:

#### Dataset 1: 임상연구 DB (Clinical Research DB) — ID 3033869
- **List endpoint**: `http://apis.data.go.kr/1352159/crisinfodataview/list`
  - Method: GET
  - Params: `serviceKey` (required), `resultType=json`, `srchWord`, `numOfRows` (1-50), `pageNo`
  - Returns: List of clinical research records (16 fields)

- **Detail endpoint**: `http://apis.data.go.kr/1352159/crisinfodataview/detail`
  - Method: GET
  - Params: `serviceKey` (required), `resultType=json`, `crisNumber` (required)
  - Returns: Detailed record (70 fields)

#### Dataset 2: 등록통계 (Registration Statistics) — ID 3074275
- **Statistics API endpoint**: [UNVERIFIED] — exact path not confirmed, data.go.kr SSL errors prevented verification
- 18 statistical fields

### Authentication
- Free `serviceKey` from data.go.kr registration (Korean government portal)
- Rate limit: [UNVERIFIED] Likely 1000 calls/day (data.go.kr standard)

### Third-Party Integration
- **K-CRIS MCP Server** (GitHub) — provides LLM integration for CRIS data

### Access Strategy
| Priority | Method | Freshness | Difficulty |
|----------|--------|-----------|------------|
| 1 | data.go.kr OpenAPI (list + detail endpoints) | Real-time | Low |
| 2 | WHO ICTRP bulk CSV | ~1-2 weeks | Low |
| 3 | ebmdatalab Scrapy + XML scraper | Real-time | Medium |

---

## D) PACTR — Pan African Clinical Trials Registry
**URL**: https://pactr.org / https://pactr.samrc.ac.za  
**WHO Status**: Primary Registry for Africa

### API / Developer Access
- **NO API, NO export, NO bulk download** — Confirmed from PACTR FAQ and exhaustive search
- No developer documentation
- No programmatic access alternatives
- Individual trial URL: `https://pactr.samrc.ac.za/TrialDisplay.aspx?TrialID=XXXXX`

### WHO ICTRP Integration
- PACTR FAQ: *"transfers all trial information to the WHO International Clinical Trials Search Portal on a quarterly basis"*
- Data staleness: **Up to 3 months** in WHO ICTRP

### Access Strategy
| Priority | Method | Freshness | Difficulty |
|----------|--------|-----------|------------|
| 1 | WHO ICTRP bulk CSV (quarterly) | Up to 3 months | Low |
| 2 | Web scraping (ebmdatalab scraper) | Real-time | Medium |
| 3 | Manual web search | Real-time | Very High |

---

## E) GitHub: ebmdatalab/registry_scrapers_parsers
**URL**: https://github.com/ebmdatalab/registry_scrapers_parsers

### Coverage of Target Registries

| Registry | Strategy | Status |
|----------|----------|--------|
| **DRKS** | Selenium grabs initial listings then visits each trial page individually | Active |
| **CTRI** | Brute-force URL enumeration of all possible trial page URLs, scraping HTML | **BROKEN** — lighter version in development |
| **CRiS** | Dual: XML download+parse for protocols, Scrapy HTML scraper for results | Active |
| **PACTR** | Gets URL suffixes then visits each trial page to extract data | Active |

### Tools Used
- **Selenium + ChromeDriver**: DRKS, Rebec
- **Scrapy**: EUCTR Protocols, CRiS (results)
- **Jupyter Notebooks/Jupytext**: Prototyping/development
- `requests`/`urllib` + `BeautifulSoup`: Inferred for most other registries

### Anti-Scraping Notes
- **No rate limiting** built into the scrapers
- **No CAPTCHA handling** — CTRI has CAPTCHA on search but scraper bypasses via URL enumeration
- Selenium/ChromeDriver requires discrete path, not env PATH
- **Repo is stale (~6+ years old)**, CTRI scraper confirmed broken

---

## F) WHO ICTRP Integration

### Registry Data Feed Status
All 4 target registries are confirmed WHO Primary Registries:

| Registry | WHO Feed Frequency | Lag in ICTRP |
|----------|-------------------|---------------|
| DRKS | Regular (weekly estimated) [UNVERIFIED exact frequency] | ~1-2 weeks |
| CTRI | Regular (weekly estimated) [UNVERIFIED exact frequency] | ~1-2 weeks |
| CRiS | Regular (weekly estimated) [UNVERIFIED exact frequency] | ~1-2 weeks |
| PACTR | **Quarterly** (confirmed from FAQ) | **Up to 3 months** |

### Data Access Methods

| Method | Cost | Format | Freshness | Notes |
|--------|------|--------|-----------|-------|
| **Bulk CSV Download** | **Free** | CSV (ZIP) | Monthly generation | Covers all 17+ registries; primary recommended method |
| trialsearch.who.int Search | Free | XML | Real-time | Manual/semi-automated; not for bulk |
| Web Service API | **Paid** (cost recovery) | XML | Weekly | Requires WHO partnership agreement |
| Crawling Service | **Unavailable** | — | — | Offline since 2025; survey available for future |

### Key URLs
- Search Portal: https://trialsearch.who.int/
- Bulk Download: https://www.who.int/tools/clinical-trials-registry-platform/network/who-data-set/downloading-records-from-the-ictrp-database
- Primary Registries: https://www.who.int/tools/clinical-trials-registry-platform/network/primary-registries

---

## G) Consolidated Access Strategy Matrix

| Registry | Best Direct Access | Direct Difficulty | Best Alternative | Alt Freshness |
|----------|-------------------|-------------------|-----------------|--------------|
| **DRKS** | Bulk JSON download | Low | WHO ICTRP CSV | ~1-2 weeks |
| **CTRI** | Selenium+CAPTCHA scraper | Very High | WHO ICTRP CSV | ~1-2 weeks |
| **CRIS** | data.go.kr OpenAPI | Low | WHO ICTRP CSV | ~1-2 weeks |
| **PACTR** | None exists | N/A | WHO ICTRP CSV | Up to 3 months |

### Pipeline Tier Classification
- **Tier 1** (Build Now): ClinicalTrials.gov v2 API + WHO ICTRP bulk CSV
- **Tier 2**: DRKS bulk JSON + CRIS OpenAPI + ISRCTN API + UMIN-CTR CSV
- **Tier 3** (ICTRP-only): CTRI + PACTR (no viable direct programmatic access)

---

## H) Sources and Verification Notes
- DRKS: PLOS One PMC9249399, Zenodo 7590083, BfArM manual, HTTP HEAD verification of download URLs
- CTRI: GitHub CHACHA0044/CTRI_scrape, direct site inspection
- CRIS: data.go.kr portal (verified endpoints), K-CRIS MCP Server GitHub
- PACTR: Official FAQ, exhaustive web search
- WHO ICTRP: Official WHO pages, ebmdatalab documentation
- GitHub repo: ebmdatalab/registry_scrapers_parsers README and code inspection

Items marked [UNVERIFIED] could not be confirmed through primary sources and require further investigation.
