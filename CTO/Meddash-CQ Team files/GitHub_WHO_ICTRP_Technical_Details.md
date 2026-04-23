# GitHub Registry Scrapers & WHO ICTRP Integration — Technical Details

> **Research Date**: 2026-04-21  
> **Status**: Verified from primary sources unless marked [UNVERIFIED]

---

## 1. GitHub Repo: `ebmdatalab/registry_scrapers_parsers`

**URL**: https://github.com/ebmdatalab/registry_scrapers_parsers  
**Branch**: `master`  
**Language**: Python, Jupyter Notebook  
**Maintainer**: Bennett Institute for Applied Data Science (EBM DataLab)

### 1.1 Registry Coverage — ALL 4 Target Registries Covered

The repo includes scrapers for **20 registries** total. The 4 target registries are confirmed present:

| # | Registry | Directory | Status |
|---|----------|-----------|--------|
| 1 | **DRKS** (German) | `/drks/` | Active |
| 2 | **CTRI** (India) | `/ctri/` | PARTIALLY BROKEN (brute-force approach no longer works; lighter version in development) |
| 3 | **CRiS** (Korea) | `/cris/` | Active |
| 4 | **PACTR** (Pan African) | `/pactr/` | Active |

**Other registries covered**: Rebec (Brazil), REPEC (Peru), ChiCTR (under development), ISRCTN, EUCTR Sponsor Country, EUCTR Protocols, EUCTR Results Pages, ANZCTR, ClinicalTrials.gov, IRCT (Iran), RPCEC (Cuba), LBCTR (Lebanon), TCTR (Thailand), NTR (Netherlands), JPRN (Japan), SLCTR (Sri Lanka)

### 1.2 Scraping Strategy per Target Registry

#### DRKS (German Clinical Trials Register)
- **Strategy**: Hybrid Selenium + page-by-page visitation
  1. Uses **Selenium** (with ChromeDriver) to grab initial information/trial listings
  2. Then visits each individual trial page to extract data
- **Libraries**: Selenium, ChromeDriver
- **Anti-scraping**: No explicit CAPTCHA handling documented. Selenium is used specifically for the initial data grab, not for bypassing protection.
- **Notes**: Requires Selenium and ChromeDriver set at a discrete path (not environmental PATH variable). Cross-platform compatibility not guaranteed.

#### CTRI (Clinical Trials Registry — India)
- **Strategy**: Brute-force URL enumeration
  1. Attempts to visit all possible CTRI trial URLs systematically (enumerating trial ID patterns)
  2. Scrapes HTML from each trial page
- **Current Status**: The brute-force approach **does not currently work**. The README states "a lighter footprint version of this scraper is potentially in the works."
- **Libraries**: Not explicitly documented; likely `requests` or similar for HTML fetching
- **Anti-scraping**: CTRI has **CAPTCHA on its search page** (confirmed from external sources: GitHub CHACHA0044/CTRI_scrape project). The brute-force approach bypasses search by directly enumerating trial page URLs.
- **Known Issue**: Brute-force enumeration is fragile — breaks when URL patterns change or rate-limiting is applied

#### CRiS / KCR (Clinical Research Information Service — South Korea)
- **Strategy**: Dual approach
  1. **Primary**: Scripts to automatically download and parse **XML** files from the CRiS website
  2. **Secondary**: Manual **HTML scraper** for results data (built with **Scrapy**)
- **Libraries**: Scrapy (for HTML scraping), XML parsers (standard library)
- **Anti-scraping**: No explicit measures documented. XML download approach is more resilient than HTML scraping.
- **Notes**: Two separate scrapers — one for protocols (XML-based) and one for results (HTML-based)

#### PACTR (Pan African Clinical Trials Registry)
- **Strategy**: URL suffix cycling + page extraction
  1. Gets trial URL suffixes from the registry
  2. Visits each trial page (`https://pactr.samrc.ac.za/TrialDisplay.aspx?TrialID=XXXXX`)
  3. Extracts data from each individual trial page
- **Libraries**: Not explicitly documented in README; likely `requests` + HTML parsing
- **Anti-scraping**: No explicit measures documented. PACTR has no CAPTCHA but also no API/export.
- **Notes**: PACTR has NO API, NO data export, and NO bulk download capability (confirmed from PACTR FAQ). This scraper is the only programmatic access method besides WHO ICTRP.

### 1.3 Tools & Libraries Summary

| Tool | Usage | Registries |
|------|-------|------------|
| **Selenium** + ChromeDriver | Browser automation for JavaScript-heavy pages | DRKS, Rebec |
| **Scrapy** | Structured HTML scraping framework | EUCTR Protocols, CRiS (results) |
| **Jupyter Notebooks** / Jupytext | Prototyping, development, testing | All (development) |
| Python (standard) | HTTP requests, XML parsing | Most registries |
| `requests` / `urllib` [INFERRED] | HTTP fetching | Most registries (not explicitly named in README) |
| `BeautifulSoup` [INFERRED] | HTML parsing | Likely used but not explicitly mentioned in README |

### 1.4 Anti-Scraping & Rate Limiting

| Aspect | Detail |
|--------|--------|
| **Rate limiting** | Not explicitly documented in repo. No built-in rate limiting code mentioned. |
| **CAPTCHA handling** | Not documented. CTRI has CAPTCHA on search but scraper bypasses via URL enumeration. |
| **Multiprocessing** | IRCT and EUCTR Results Pages have multiprocessing versions to "speed things up" — IRCT multiprocessing version described as "a little unfriendly." |
| **Cross-platform** | Not all scrapers work cross-platform. Selenium/ChromeDriver requires discrete path, not env PATH. |
| **robots.txt** | No explicit robots.txt compliance mentioned. |

### 1.5 Key Limitations

1. **CTRI scraper is broken** — brute-force URL enumeration approach no longer works; lighter version under development
2. **No rate limiting built in** — users must implement their own throttling
3. **Selenium dependency** — some scrapers require ChromeDriver at a specific path
4. **No CAPTCHA handling** — CTRI CAPTCHA is bypassed via URL enumeration, not solved
5. **Repo appears stale** — last significant updates appear to be ~6+ years ago (based on GitHub commit timestamps)
6. **Not all scrapers work cross-platform** — platform-specific issues noted

---

## 2. WHO ICTRP Integration

### 2.1 Registry Data Feeds to WHO ICTRP

**All 4 target registries are confirmed WHO Primary Registries** that feed data to WHO ICTRP:

| Registry | WHO Primary Registry | ICTRP Data Feed Frequency | Verified |
|----------|--------------------|-----------------------------|----------|
| **DRKS** (German) | Yes | Weekly (per ICTRP schedule) | Verified |
| **CTRI** (India) | Yes | Weekly (per ICTRP schedule) | Verified |
| **CRiS** (South Korea) | Yes | Weekly (per ICTRP schedule) | Verified |
| **PACTR** (Pan African) | Yes | Quarterly (per PACTR FAQ) | Verified |

**Important**: PACTR specifically transfers data quarterly, not weekly. This means PACTR data in WHO ICTRP can be up to **3 months stale**. All other registries feed weekly. [UNVERIFIED: exact lag per registry — only PACTR quarterly frequency is explicitly documented in PACTR FAQ]

**Complete list of WHO ICTRP Primary Registries** (confirmed from official WHO page):
- Thai Clinical Trials Registry (TCTR)
- Pan African Clinical Trial Registry (PACTR)
- Peruvian Clinical Trial Registry (REPEC)
- Sri Lanka Clinical Trials Registry (SLCTR)
- Clinical Research Information Service (CRiS) — Republic of Korea
- Clinical Trials Information System (CTIS)
- Clinical Trials Registry — India (CTRI)
- Cuban Public Registry of Clinical Trials (RPCEC)
- EU Clinical Trials Register (EU-CTR)
- German Clinical Trials Register (DRKS)
- Iranian Registry of Clinical Trials (IRCT)
- ISRCTN
- International Traditional Medicine Clinical Trial Registry (ITMCTR)
- Japan Registry of Clinical Trials (jRCT)
- Lebanese Clinical Trials Registry (LBCTR)
- Australian New Zealand Clinical Trials Registry (ANZCTR)
- Brazilian Clinical Trials Registry (ReBec)
- Chinese Clinical Trial Registry (ChiCTR)
- ClinicalTrials.gov (data provider)

### 2.2 WHO ICTRP Data Access Methods

#### Method 1: Free Bulk CSV Download (RECOMMENDED for bulk data)
- **URL**: https://www.who.int/tools/clinical-trials-registry-platform/network/who-data-set/downloading-records-from-the-ictrp-database
- **Format**: CSV (compressed in ZIP file)
- **Cost**: **Free** — publicly available to all requesters at no charge
- **Frequency**: File is generated **once per month**
- **Coverage**: All 17+ Primary Registries' data combined
- **Limitations**: Monthly generation means up to 1-month lag; CSV format only (no structured API)
- **Terms**: Subject to WHO ICTRP Terms and Conditions for Use of Data

#### Method 2: XML Search Results Export (Free, search-based)
- **URL**: https://trialsearch.who.int/
- **Format**: XML
- **Cost**: Free for search-based downloads
- **Process**: Use the search portal to query trials, then download results in XML
- **Limitations**: Requires manual or semi-automated search; not suitable for full bulk downloads

#### Method 3: ICTRP Search Portal Web Service (PAID)
- **URL**: https://www.who.int/tools/clinical-trials-registry-platform/the-ictrp-search-portal/ictrp-search-portal-web-service
- **Format**: XML web services
- **Cost**: **Paid** (cost recovery basis) — requires partnership agreement with WHO
- **Capability**: Real-time interrogation of ICTRP database; search and display results on partner websites
- **Process**: Requires agreement with WHO; allows embedding ICTRP search in external applications

#### Method 4: Crawling Service (CURRENTLY UNAVAILABLE as of 2025)
- **Status**: **Not available**. WHO website states: "The Crawling service is currently not available. If you wish to use this service in 2025 or when it is made available please fill this survey."
- **Format**: Presumably structured data export
- **Note**: This was previously available and may return in the future

### 2.3 WHO ICTRP Data Format Details

| Aspect | Detail |
|--------|--------|
| **Data standard** | WHO Trial Registration Data Set (Version 1.3.1 current; archives include v1.1, v1.2, v1.2.1, v1.3) |
| **Minimum fields** | 24-item WHO Trial Registration Data Set (trial ID, title, sponsor, status, phase, contact, etc.) |
| **Language** | English only in ICTRP Search Portal |
| **Update frequency** | ICTRP database updated **weekly** |
| **Bulk download frequency** | CSV file generated **monthly** |
| **Archive** | Previous data set versions available |
| **Terms** | Subject to WHO ICTRP Terms and Conditions; data not endorsed by WHO |

### 2.4 Data Lag Times per Registry

| Registry | Feed Frequency to ICTRP | Estimated Lag in ICTRP | Confidence |
|----------|-------------------------|------------------------|------------|
| DRKS | Weekly | ~1-2 weeks | [UNVERIFIED] — estimated from weekly schedule |
| CTRI | Weekly | ~1-2 weeks | [UNVERIFIED] — estimated from weekly schedule |
| CRiS | Weekly | ~1-2 weeks | [UNVERIFIED] — estimated from weekly schedule |
| PACTR | Quarterly | **Up to 3 months** | Verified from PACTR FAQ |
| ClinicalTrials.gov | Daily/Weekly | ~1 week | [UNVERIFIED] |

**Important**: The monthly CSV bulk download file has an additional lag of up to 1 month beyond the ICTRP update schedule.

### 2.5 Cost Summary

| Access Method | Cost | Notes |
|--------------|------|-------|
| Bulk CSV Download | **Free** | Monthly ZIP file |
| Search Portal (trialsearch.who.int) | **Free** | Manual/semi-automated searches |
| XML Export from searches | **Free** | Limited to search results |
| Web Service API | **Paid** | Cost recovery basis, requires agreement |
| Crawling Service | **Unavailable** | Was likely free; currently offline |

### 2.6 Key URLs

| Resource | URL |
|----------|-----|
| ICTRP Search Portal | https://trialsearch.who.int/ |
| ICTRP Main Page | https://who.int/tools/clinical-trials-registry-platform |
| Bulk Download Page | https://www.who.int/tools/clinical-trials-registry-platform/network/who-data-set/downloading-records-from-the-ictrp-database |
| Web Service Info | https://www.who.int/tools/clinical-trials-registry-platform/the-ictrp-search-portal/ictrp-search-portal-web-service |
| Primary Registries List | https://www.who.int/tools/clinical-trials-registry-platform/network/primary-registries |
| Data Set Standard | https://www.who.int/tools/clinical-trials-registry-platform/network/who-data-set |

---

## 3. Strategic Recommendations for ClinicalQuant/MedDash Pipeline

### Tier 1 — Primary Data Sources (Build First)
1. **ClinicalTrials.gov v2 API** — Free REST API, no auth, JSON/CSV bulk download
2. **WHO ICTRP Bulk CSV** — Free monthly ZIP, covers all 17+ registries including DRKS, CTRI, CRiS, PACTR

### Tier 2 — Direct Registry Access (Where Beneficial)
1. **CRiS (Korea)** — XML download available; supplement ICTRP for real-time Korean trial data
2. **DRKS (Germany)** — Selenium scraper from ebmdatalab repo; supplement ICTRP for real-time German trial data

### Tier 3 — Scraping Only (No Better Alternative)
1. **PACTR** — No API, no export, no bulk download. Use WHO ICTRP for bulk data + ebmdatalab scraper for real-time data (note quarterly ICTRP lag)
2. **CTRI (India)** — CAPTCHA on search, no API. Use WHO ICTRP for bulk data. Direct scraping requires CAPTCHA solving (ebmdatalab brute-force approach is broken)

### Key Risk: ebmdatalab Repo Staleness
- The repo appears to have last significant updates ~6+ years ago
- CTRI scraper is confirmed broken
- Scrapers may need updating for current registry website changes
- Recommend forking and maintaining if using in production

---

## 4. Verification Status Legend

| Marker | Meaning |
|--------|----------|
| Verified | Confirmed from primary source (official website, README, WHO pages) |
| [UNVERIFIED] | Not confirmed from primary source; estimated or inferred |

---

*Primary path: `/a0/CTO/Meddash-CQ Team files/GitHub_WHO_ICTRP_Technical_Details.md`*
*Backup: `/a0/usr/ceo-files/GitHub_WHO_ICTRP_Technical_Details.md`*
