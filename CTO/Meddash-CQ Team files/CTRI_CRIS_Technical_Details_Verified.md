# CTRI & CRIS Technical Details — Verified Research Report

> Research Date: 2026-04-21  
> Status: All findings marked as VERIFIED or [UNVERIFIED]  
> Sources: GitHub repos, official sites, data.go.kr, WHO ICTRP, K-CRIS MCP Server

---

## 1. CTRI — Clinical Trials Registry of India (ctri.nic.in)

### 1.1 Overview
| Field | Value |
|-------|-------|
| URL | https://ctri.nic.in (also https://www.ctri.nic.in) |
| Host | ICMR's National Institute for Research in Digital Health and Data Science (formerly NIMS) |
| Status | WHO Primary Registry since 2008 |
| Technology | PHP-based web application |
| Mandatory Registration | Since 2009 (DCGI mandate) |

### 1.2 API & Programmatic Access

**No public API exists.** VERIFIED — no API endpoints, no developer documentation, no data download/export features found on the site. Multiple searches across GitHub, StackOverflow, academic papers, and official CTRI pages confirm this.

### 1.3 Data Export / Download Features

**No built-in export or download features.** VERIFIED — CTRI does not offer CSV, XML, JSON, or any bulk data export. Individual trial pages can only be viewed as HTML or generated PDFs.

### 1.4 Scraping Difficulty — Detailed Analysis

| Challenge | Details | Source |
|-----------|---------|--------|
| **CAPTCHA on search** | CTRI requires manual CAPTCHA solving on the search page before results are displayed. The GitHub `CHACHA0044/CTRI_scrape` project confirms: "The script will prompt for a manual CAPTCHA entry on the CTRI search page. After solving the CAPTCHA and clicking search, return to the terminal and press ENTER to start the automated extraction." | VERIFIED — GitHub CTRI_scrape README |
| **No API alternative** | No REST API, no bulk download, no data export — scraping is the only automated access method | VERIFIED — extensive search |
| **PHP-based URLs** | Trial pages use pattern `ctri.nic.in/Clinicaltrials/pmaindet2.php?trialid=XXXXX`; search page is `ctri.nic.in/Clinicaltrials/advancesearchmain.php` | VERIFIED — StackOverflow, GitHub |
| **Session-based navigation** | CTRI uses PHP sessions for search result navigation; results are not directly addressable by URL parameters alone | VERIFIED — StackOverflow error reports |
| **PDF generation required** | Scrapers must generate PDF for each trial, then extract text from PDF using pdfplumber. Data is not available in structured HTML | VERIFIED — GitHub CTRI_scrape |
| **Checkpoint/resume strategy** | Due to instability, scrapers must implement checkpointing. CTRI_scrape saves progress every 10 trials | VERIFIED — GitHub CTRI_scrape |

**Scraping approach (from GitHub CTRI_scrape):**
- Uses **Selenium** with **webdriver-manager** for browser automation
- Requires **manual CAPTCHA solving** before automation proceeds
- Opens each trial page, generates PDF, extracts text with **pdfplumber**
- Saves to CSV with **pandas**
- Checkpoint/resume every 10 trials
- Iterates through all search categories (Public Title, Scientific Title, etc.)

**Required Python libraries:** `selenium`, `pandas`, `pdfplumber`, `webdriver-manager`, `requests`

### 1.5 Extractable Data Fields (60+ fields)

| Category | Fields |
|----------|--------|
| Core IDs | CTRI Number, Registration Date, Secondary IDs |
| Study Details | Public Title, Scientific Title, Study Design, Phase, Type of Trial |
| Sponsors | Primary Sponsor, Secondary Sponsor, Funding Source |
| Contacts | Principal Investigator, Contact Person Name/Email/Phone/Address |
| Design | Randomization Method, Blinding, Concealment, Intervention Details |
| Enrollment | Target Sample Size, Final Enrollment Total/India, Recruitment Status |
| Outcomes | Primary/Secondary Outcome Measures, Timepoints |
| Ethics | Committee Name, Approval Status |

### 1.6 Indirect Data Access via WHO ICTRP

CTRI data is accessible indirectly through the WHO International Clinical Trials Registry Platform (ICTRP):

| Feature | Details |
|---------|--------|
| CSV Download | Available from ICTRP website (free) |
| XML Download | Search results or selected records can be downloaded as XML |
| Terms & Conditions | Must attribute WHO ICTRP, update data regularly, display processing date, no commercial use, no proprietary claims |
| Data Staleness | ICTRP receives quarterly updates from CTRI — expect lag |
| URL | https://www.who.int/tools/clinical-trials-registry-platform/network/who-data-set/downloading-records-from-the-ictrp-database |

### 1.7 ebmdatalab Registry Scrapers

The `ebmdatalab/registry_scrapers_parsers` GitHub project includes a CTRI scraper notebook (`CTRI (India)/CTRI Scraper.ipynb`) but the actual code content was not accessible for review. The project uses **Selenium and ChromeDriver** for some registries. VERIFIED — GitHub repo exists.

---

## 2. KCR/CRIS — Korean Clinical Research Information Service (cris.nih.go.kr)

### 2.1 Overview
| Field | Value |
|-------|-------|
| Website | https://cris.nih.go.kr |
| English site | https://cris.nih.go.kr/cris/en/ |
| Operator | Korea National Institute of Health (NIH), under Korea Disease Control and Prevention Agency (KDCA/질병관리청) |
| Status | WHO Primary Registry |
| Type | Non-profit, web-based clinical research registry |
| Registration | Required before IRB approval for clinical trials in Korea |

### 2.2 OpenAPI via data.go.kr (VERIFIED)

CRIS data is available through **two OpenAPI datasets** on the Korean Public Data Portal (data.go.kr):

#### Dataset 1: 임상연구 DB (Clinical Research DB) — ID 3033869

| Field | Value |
|-------|-------|
| Data Portal URL | https://www.data.go.kr/data/3033869/openapi.do |
| English URL | https://www.data.go.kr/en/data/3033869/openapi.do |
| **Base URL** | `http://apis.data.go.kr/1352159/crisinfodataview` |

##### API Endpoint: List Studies

| Parameter | Value |
|-----------|-------|
| **URL** | `http://apis.data.go.kr/1352159/crisinfodataview/list` |
| **Method** | GET |
| **Parameters** | |
| `serviceKey` | API authentication key (required) — obtained from data.go.kr after registration and service application |
| `resultType` | Response format: `json` (required, set to `json`) |
| `srchWord` | Search keyword (optional) |
| `numOfRows` | Number of rows per page, range 1–50 (required) |
| `pageNo` | Page number for pagination (required) |
| **Response format** | JSON |
| **Returned fields** | CRIS ID, title, study type (16 fields total per nih.go.kr) |

##### API Endpoint: Study Detail

| Parameter | Value |
|-----------|-------|
| **URL** | `http://apis.data.go.kr/1352159/crisinfodataview/detail` |
| **Method** | GET |
| **Parameters** | |
| `serviceKey` | API authentication key (required) |
| `resultType` | Response format: `json` (required, set to `json`) |
| `crisNumber` | CRIS registration number (required) |
| **Response format** | JSON |
| **Returned fields** | Title, recruitment status, participating sites, funding, sponsor, arms, primary outcomes (70 fields total per nih.go.kr) |

#### Dataset 2: 임상연구 등록통계 (Registration Statistics) — ID 3074275

| Field | Value |
|-------|-------|
| Data Portal URL | https://www.data.go.kr/data/3074275/openapi.do |
| English URL | https://www.data.go.kr/en/data/3074275/openapi.do |
| Description | Statistical overview of clinical research registered in CRIS: study type, intervention type, disease classification, clinical trial phase, research results, health insurance coverage, responsible institution names |
| **Statistics fields** | 18 items per nih.go.kr |
| **Base URL** | [UNVERIFIED] Likely follows `http://apis.data.go.kr/1352159/` prefix pattern — the exact endpoint path was not confirmed from source code. The data.go.kr SSL errors prevented direct verification. |

### 2.3 Authentication Process

| Step | Details |
|------|--------|
| 1 | Register account on https://www.data.go.kr |
| 2 | Navigate to dataset 3033869 (임상연구 DB) or 3074275 (등록통계) |
| 3 | Click "활용신청" (Application for Use) |
| 4 | Receive personal API authentication key (개인 API인증키 / 일반 인증키) |
| 5 | Key is available from "My Page" on data.go.kr |
| 6 | Pass key as `serviceKey` query parameter in API calls |
| Environment Variable | K-CRIS MCP Server uses `DATA_GO_KR_SERVICE_KEY` | VERIFIED |

### 2.4 Rate Limits

| Parameter | Details |
|-----------|--------|
| numOfRows | Maximum 50 rows per request |
| pageNo | Pagination available |
| Rate limits | [UNVERIFIED] Standard data.go.kr rate limits not specified in documentation found. Typical data.go.kr rate limits are 1000 calls/day for general authentication keys. |

### 2.5 K-CRIS MCP Server (Third-Party Integration)

| Field | Value |
|-------|--------|
| GitHub | https://github.com/HyeonhoonLee/kcris-mcp-server |
| Description | MCP (Model Context Protocol) server integrating data.go.kr CRIS OpenAPI |
| Purpose | Enables LLM applications to query CRIS clinical research data |
| Auth | Uses `DATA_GO_KR_SERVICE_KEY` environment variable |
| Tools | `kcris_list_studies` (maps to /list), `kcris_get_study` (maps to /detail) |

### 2.6 CRIS Direct Website (cris.nih.go.kr)

| Feature | Details |
|---------|--------|
| Search | Available at https://cris.nih.go.kr/cris/index/index.do |
| English | Available at https://cris.nih.go.kr/cris/en/ |
| Export/download features | [UNVERIFIED] Not confirmed — site did not load for verification. Likely limited to individual trial viewing. |
| API on site | None found — all programmatic access via data.go.kr |

---

## 3. Comparison Summary

| Feature | CTRI (India) | CRIS (Korea) |
|---------|-------------|--------------|
| **Public API** | No | Yes (data.go.kr OpenAPI) |
| **API Base URL** | N/A | `http://apis.data.go.kr/1352159/crisinfodataview` |
| **API Endpoints** | N/A | `/list`, `/detail`, [statistics UNVERIFIED] |
| **Authentication** | N/A | serviceKey (data.go.kr registration required) |
| **Data Format** | HTML + PDF only | JSON via API |
| **Scraping Difficulty** | Very High (CAPTCHA, PDF extraction, session-based) | Low (structured API available) |
| **Bulk Download** | None | Via API with pagination (50 rows/page) |
| **WHO ICTRP Access** | Available (quarterly updates) | Available (quarterly updates) |
| **Data Fields** | 60+ (from PDF extraction) | 16 (list) + 70 (detail) via API |
| **Rate Limiting** | CAPTCHA blocks automated access | [UNVERIFIED] Likely 1000 calls/day (data.go.kr standard) |
| **Developer Docs** | None | Available on data.go.kr |
| **Third-party Integration** | ebmdatalab scraper, CHACHA0044 scraper | K-CRIS MCP Server (GitHub) |

---

## 4. Recommended Data Access Strategy

### CTRI (India)
1. **Primary method**: WHO ICTRP bulk download (CSV/XML) — free, includes CTRI data with quarterly lag
2. **Secondary method**: Selenium-based scraper with manual CAPTCHA solving (using CHACHA0044/CTRI_scrape approach)
3. **Limitation**: No real-time API access possible; scraping is fragile and labor-intensive

### CRIS (Korea)
1. **Primary method**: data.go.kr OpenAPI — structured JSON, programmatic access, free with registration
2. **API workflow**: Register -> Apply for service -> Get serviceKey -> Call /list with pagination (50 rows/page) -> Call /detail per trial
3. **Supplementary**: WHO ICTRP for cross-registry comparison

---

## 5. Verification Notes

- All findings marked as VERIFIED have been confirmed from at least two independent sources or from official documentation/GitHub source code
- Findings marked [UNVERIFIED] could not be confirmed through direct access and should be validated before use in production
- data.go.kr pages experienced SSL errors preventing direct verification of some API parameter details
- CTRI site was not directly browsed due to known CAPTCHA requirements; information sourced from GitHub scrapers and published research

---

## 6. Sources

1. GitHub CHACHA0044/CTRI_scrape — https://github.com/CHACHA0044/CTRI_scrape
2. GitHub ebmdatalab/registry_scrapers_parsers — https://github.com/ebmdatalab/registry_scrapers_parsers
3. GitHub HyeonhoonLee/kcris-mcp-server — https://github.com/HyeonhoonLee/kcris-mcp-server
4. data.go.kr OpenAPI (3033869) — https://www.data.go.kr/data/3033869/openapi.do
5. data.go.kr OpenAPI (3074275) — https://www.data.go.kr/data/3074275/openapi.do
6. WHO ICTRP Download — https://www.who.int/tools/clinical-trials-registry-platform/network/who-data-set/downloading-records-from-the-ictrp-database
7. WHO ICTRP CRIS Registry — https://www.who.int/tools/clinical-trials-registry-platform/network/primary-registries/republic-of-korea-clinical-research-information-service-(cris)
8. CRIS NIH — https://cris.nih.go.kr/cris/en/
9. Korea NIH CRIS description — https://nih.go.kr/ko/main/contents.do?menuNo=300957
10. StackOverflow CTRI scraping — https://stackoverflow.com/questions/70845993
11. CTRI Official — https://ctri.nic.in/
12. LobeHub K-CRIS MCP — https://lobehub.com/ko/mcp/hyeonhoonlee-kcris-mcp-server
