# Clinical Trial Registry API Access Research
## ClinicalQuant Biotech Catalyst Newsletter — Data Source Analysis
**Date**: 2026-04-21 | **Author**: Deep Research Agent | **Project**: MedDash-CQ

---

## Executive Summary

Of 8 government/international clinical trial registries researched, only **3 offer programmatic API access** (ClinicalTrials.gov v2, WHO ICTRP, ISRCTN). One offers bulk CSV download (UMIN-CTR). The remaining 4 require web scraping or manual access. **WHO ICTRP is the universal backbone** — it aggregates data from all other registries plus 12+ more, making it the single most valuable integration point.

| Source | Access | API? | Reliability | CQ Priority |
|--------|--------|------|-------------|-------------|
| ClinicalTrials.gov v2 | Free REST API | YES | High | Tier 1 |
| WHO ICTRP | Paid XML Web Service | YES | High | Tier 1 |
| ISRCTN | Free XML API | YES | High | Tier 2 |
| UMIN-CTR | Free Bulk CSV | PARTIAL | High | Tier 2 |
| EudraCT/EU CTR | Web Scraping + CSV | NO | Medium | Tier 2 |
| ChiCTR | Web Scraping | NO | Medium | Tier 3 |
| ANZCTR | Web Scraping/Manual | NO | Medium | Tier 3 |
| EU CTIS | Transparency Portal Only | NO | Medium | Indirect |
| jRCT | Manual (scraping prohibited) | NO | Medium-High | Indirect |

---

## 1. ClinicalTrials.gov API v2

### Source Name and URL
- **Name**: ClinicalTrials.gov Modern API v2
- **URL**: https://clinicaltrials.gov/data-api/api
- **Base URL**: `https://clinicaltrials.gov/api/v2`
- **OpenAPI Spec**: Available in YAML at the data-api page
- **Version**: 2.0.2 (as of 2025-08-26 data ingest modernization)

### Access Method
**Free REST API** — No authentication required, no API key needed

### Rate Limits and Pricing
- **Rate Limit**: ~50 requests per minute per IP address
- **Pricing**: Completely free (US government service via NLM/NIH)
- **Authentication**: None required
- **Pagination**: Token-based (`pageToken`), `pageSize` max 1000 results per page

### Data Freshness
- **Real-time to daily**: Studies appear within hours of sponsor submission
- **Bulk download**: Full dataset available via `/api/v2/studies/download?format=json.zip`
- **Update schedule**: Continuous ingestion; API reflects current database state

### Data Format
- **JSON** (default), **CSV** (via format parameter)
- Dates: ISO 8601 format
- Rich text fields: CommonMark Markdown
- Bulk download: JSON.zip archive

### Key API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v2/studies` | GET | Search studies with query/filter parameters |
| `/api/v2/studies/{NCT_ID}` | GET | Retrieve single study by NCT ID |
| `/api/v2/studies/download` | GET | Bulk download all studies (json.zip) |

### Key Query Parameters (Search Endpoint)

| Parameter | Description | Example |
|-----------|-------------|---------|
| `query.cond` | Disease/condition | `query.cond=cancer` |
| `query.intr` | Intervention/drug | `query.intr=pembrolizumab` |
| `query.locn` | Location | `query.locn=boston` |
| `query.spons` | Sponsor | `query.spons=merck` |
| `query.term` | Full-text search | `query.term=CAR-T` |
| `filter.overallStatus` | Status filter | `RECRUITING,COMPLETED` |
| `filter.ids` | NCT ID filter | `NCT04171719` |
| `filter.phase` | Phase filter | `PHASE2,PHASE3` |
| `sort` | Result ordering | `LastUpdatePostDate:desc` |
| `pageSize` | Results per page | Max 1000 |
| `pageToken` | Pagination token | From previous response |
| `format` | Response format | `json` or `csv` |

### Available Data Fields (Study Record Modules)

**protocolSection:**
- `identificationModule`: NCT ID, titles, organization, acronym
- `statusModule`: Overall status, start/completion dates, why stopped
- `sponsorCollaboratorsModule`: Sponsor, collaborators, responsible party
- `descriptionModule`: Brief summary, detailed description
- `conditionsModule`: Conditions, keywords
- `designModule`: Study type, phases, enrollment, time perspective
- `armsInterventionsModule`: Arms, interventions (drug names, dosing)
- `outcomesModule`: Primary/secondary outcome measures
- `eligibilityModule`: Inclusion/exclusion criteria, sex, age
- `contactsLocationsModule`: Sites, investigators, contacts
- `referencesModule`: Publications, PMIDs

**derivedSection:**
- `miscInfoModule`: Study creation/update timestamps
- `conditionBrowseModule`: MeSH condition terms
- `interventionBrowseModule`: MeSH intervention terms

**resultsSection** (when available):
- `participantFlowModule`: Participant flow
- `baselineCharacteristicsModule`: Baseline demographics
- `outcomeMeasuresModule`: Results data
- `adverseEventsModule`: Safety data
- Top-level: `hasResults` boolean

### Reliability Rating
**High** — US government service, SLA-backed, well-documented OpenAPI 3.0 spec, active development

### Specific Use Case for ClinicalQuant
- **PRIMARY DATA SOURCE** for US/global clinical trial pipeline tracking
- Phase transitions (Phase I to II to III) as catalyst signals
- Sponsor-specific pipeline monitoring (e.g., track all Merck oncology trials)
- Primary completion date tracking for FDA submission timeline estimation
- Results posting for pre-publication data extraction for newsletter content
- Enrollment status changes as recruitment milestones / sentiment signals
- Bulk download for offline analysis and ML model training

---

## 2. EU Clinical Trials Information System (CTIS)

### Source Name and URL
- **Name**: Clinical Trials Information System (CTIS)
- **URL**: https://euclinicaltrials.eu/
- **Transparency Portal**: https://euclinicaltrials.eu/ (public searchable interface)
- **Legacy Register**: https://www.clinicaltrialsregister.eu/ (EudraCT data, still operational)

### Access Method
**Manual / Transparency Portal Only** — No public API available

- CTIS provides a searchable web interface for public trial information
- As of Jan 31, 2023, all new EU clinical trial applications must be submitted via CTIS
- As of Jan 31, 2025, all EU clinical trials have transitioned to CTIS
- No REST API, no data export, no RSS feeds documented
- EMA provides training materials but no developer documentation

### Rate Limits and Pricing
- **Rate Limits**: Not applicable (no API)
- **Pricing**: Free to access transparency portal
- **Scraping Risk**: Unknown — EMA terms of use should be checked

### Data Freshness
- **Near real-time** for new trial applications (CTIS is the live system)
- Legacy EudraCT data: Daily-to-weekly updates

### Data Format
- **HTML** only (transparency portal)
- No structured export from CTIS itself

### Reliability Rating
**Medium** — High data quality (EU regulatory system), but zero programmatic access limits pipeline utility

### Specific Use Case for ClinicalQuant
- EU regulatory approval pathway tracking (CTIS authorization dates)
- Multi-country trial design visibility (which EU member states participating)
- Transparency rules (revised April 2026) may improve data availability
- Cross-reference with EudraCT/EU CTR for legacy trial data
- **Recommendation**: Monitor EMA developer page for future API releases; use WHO ICTRP or EU CTR scraping as interim

---

## 3. WHO International Clinical Trials Registry Platform (ICTRP)

### Source Name and URL
- **Name**: WHO ICTRP Search Portal
- **Search Portal**: https://www.who.int/tools/clinical-trials-registry-platform/the-ictrp-search-portal
- **Web Service Page**: https://www.who.int/tools/clinical-trials-registry-platform/the-ictrp-search-portal/ictrp-search-portal-web-service
- **Crawling Service**: https://www.who.int/tools/clinical-trials-registry-platform/the-ictrp-search-portal/ictrp-search-portal-crawling-service
- **Data Download**: https://www.who.int/tools/clinical-trials-registry-platform/network/who-data-set/downloading-records-from-the-ictrp-database
- **Data Providers**: https://www.who.int/tools/clinical-trials-registry-platform/network/data-providers

### Access Method
**Paid XML Web Service** (cost recovery) + **Free Crawling Service** + **Free Data Download**

Three programmatic access options:
1. **ICTRP Search Portal Web Service** — XML-based web service for real-time queries. Available to: public (research purposes), Primary Registries, government agencies, WHO units, research institutions. Cost recovery fee applies (contact ICTRP Secretariat for pricing).
2. **ICTRP Search Portal Crawling Service** — Allows real-time interrogation by crawling HTML pages. Free.
3. **Bulk Data Download** — Full ICTRP database downloadable. Free for research.

### Rate Limits and Pricing
- **Web Service**: Cost recovery fee (amount not publicly listed — contact ictrp@who.int)
- **Crawling Service**: Free, but respect robots.txt and throttle requests
- **Bulk Download**: Free
- **No hard rate limits published** for any access method

### Data Freshness
- **Weekly-to-monthly** for aggregated data (registries submit at varying intervals)
- **Near real-time** via web service queries
- 17+ primary registries feed into ICTRP as of Oct 2024

### Data Format
- **XML** (web service)
- **HTML** (crawling service)
- **WHO Trial Registration Data Set** (24-field minimum standard)
- Downloadable datasets available

### Available Fields (WHO Trial Registration Data Set — 24 fields)
1. Trial Registration Date
2. Primary Registry and Trial ID
3. Secondary IDs
4. Source(s) of Monetary or Material Support
5. Primary Sponsor
6. Secondary Sponsor(s)
7. Contact for Public Queries
8. Contact for Scientific Queries
9. Public Title
10. Scientific Title
11. Countries of Recruitment
12. Health Condition(s) or Problem(s)
13. Intervention(s)
14. Key Inclusion/Exclusion Criteria
15. Study Type
16. Date of First Enrolment
17. Target Sample Size
18. Recruitment Status
19. Primary Outcome(s)
20. Secondary Outcome(s)
21. Ethical Review Status
22. Completion Date
23. Summary Results
24. IPD Sharing Statement

### Reliability Rating
**High** — WHO-backed, aggregates 17+ primary registries globally, ICMJE-recognized

### Specific Use Case for ClinicalQuant
- **UNIVERSAL BACKBONE** — Single integration point for global trial data from ALL registries
- Cross-registry trial deduplication (same trial registered in multiple registries)
- Coverage gap identification (trials in ChiCTR, ANZCTR, UMIN-CTR not in ClinicalTrials.gov)
- Early signal detection from Asian/EU registries 3-6 months before US registration
- Pipeline: Use ICTRP as primary aggregator, then supplement with registry-specific access for richer data
- **Recommendation**: Contact ictrp@who.int for web service pricing; if cost is prohibitive, use free crawling service + bulk download

---

## 4. Chinese Clinical Trial Registry (ChiCTR)

### Source Name and URL
- **Name**: Chinese Clinical Trial Registry (ChiCTR)
- **URL**: https://www.chictr.org.cn
- **WHO Primary Registry**: Yes

### Access Method
**Web Scraping** — No official API exists
- Unmaintained R package `rchictr` exists (GitHub: serghiou/rchictr) but not production-ready
- WHO ICTRP aggregates ChiCTR data (recommended alternative)

### Rate Limits and Pricing
- **Pricing**: Free
- **No official rate limits** — recommend 2-5 second throttling between requests
- Site primarily in Chinese; English subset available

### Data Freshness
- **Near real-time** for registrations
- Results posting is sponsor-dependent

### Data Format
- **HTML** (website only)
- WHO ICTRP provides XML/JSON for ChiCTR records

### Reliability Rating
**Medium** — WHO Primary Registry (quality controlled), but Chinese-language primary interface and zero API access limit automated pipeline utility

### Specific Use Case for ClinicalQuant
- China-only oncology, CAR-T, gene therapy trials appearing 3-6 months before ClinicalTrials.gov
- China-innovation signals (domestic pharma: BeiGene, Legend Biotech, Innovent)
- Cross-reference with WHO ICTRP for English-normalized data
- **Recommendation**: Use WHO ICTRP as primary access; scrape ChiCTR directly only for China-specific intelligence that ICTRP does not capture

---

## 5. ISRCTN Registry

### Source Name and URL
- **Name**: ISRCTN Registry (International Standard Randomised Controlled Trial Number)
- **URL**: https://www.isrctn.com
- **API Documentation**: https://www.isrctn.com/editorial/retrieveFile/38def0ea-8330-4eab-b288-d21115c782f3/37855
- **Owned by**: ISRCTN company (non-profit), administered by BMC/Springer Nature

### Access Method
**Free XML API** — Two API calls available:
1. **Trial by ISRCTN**: Retrieve data for a specific trial by its ISRCTN identifier
2. **Search/Query**: Query available trials by criteria

ISRCTN explicitly states: "Please do not scrape this site — the API is a much more efficient way of getting trial data."

### Rate Limits and Pricing
- **Pricing**: Free
- **Rate Limits**: Not explicitly documented — recommend polite throttling (1-2 req/sec)
- **No authentication** required for basic queries

### Data Freshness
- **Near real-time** for registrations
- Results posting: varies by sponsor
- WHO ICTRP also aggregates ISRCTN data

### Data Format
- **XML** (API response)
- R package `ctrdata` transforms ISRCTN XML to ndjson format
- CSV export available via website (search with wide date range)

### Reliability Rating
**High** — WHO Primary Registry, ICMJE-recognized, Springer Nature-administered, content validation and curation

### Specific Use Case for ClinicalQuant
- UK/EU trial registration (especially NIHR-funded trials)
- Health technology assessment (HTA) trials requiring ISRCTN
- Surgical/interventional procedure trials common in ISRCTN
- Cross-reference with EudraCT for EU regulatory pathway
- ISRCTN assignment can indicate trial maturity/approval stage
- **Recommendation**: Build ISRCTN API integration as Tier 2 data source; use for UK/EU trial intelligence supplementing ClinicalTrials.gov

---

## 6. Australian New Zealand Clinical Trials Registry (ANZCTR)

### Source Name and URL
- **Name**: ANZCTR (Australian New Zealand Clinical Trials Registry)
- **URL**: https://www.anzctr.org.au
- **WHO Primary Registry**: Yes

### Access Method
**Web Scraping / Manual** — No API, no RSS, no structured export
- WHO ICTRP aggregates ANZCTR data (recommended alternative)
- Website search interface only

### Rate Limits and Pricing
- **Pricing**: Free
- **No API to rate-limit**
- Web scraping: respect robots.txt, throttle requests

### Data Freshness
- **Near real-time** for registrations
- Results: sponsor-dependent

### Data Format
- **HTML** only (individual trial pages)
- WHO ICTRP provides XML/JSON for ANZCTR records

### Reliability Rating
**Medium** — High data quality (WHO Primary Registry), but zero export options limit automated access

### Specific Use Case for ClinicalQuant
- ANZ trial site signals — Australia's CTN (Clinical Trial Notification) scheme enables faster trial initiation than US IND process
- Early indicator for international companies running first-in-human trials outside US
- Australia as a popular Phase I/II destination (regulatory arbitrage)
- **Recommendation**: Use WHO ICTRP as sole access method for ANZCTR data; do not invest in building ANZCTR-specific scraper

---

## 7. Japan Primary Registries Network (UMIN-CTR + jRCT)

### 7a. UMIN-CTR

#### Source Name and URL
- **Name**: UMIN Clinical Trials Registry (UMIN-CTR)
- **URL**: https://www.umin.ac.jp/ctr/
- **CSV Data**: https://www.umin.ac.jp/ctr/csvdata.html
- **WHO Primary Registry**: Yes

#### Access Method
**Free Bulk CSV Download** — Best programmatic access of all Asian registries
- Bulk CSV files available at `/ctr/csvdata.html`
- No REST API, but structured CSV download enables automated ETL

#### Rate Limits and Pricing
- **Pricing**: Free
- **No limits** on bulk CSV download
- No API to rate-limit

#### Data Freshness
- **Weekly-to-monthly** for bulk CSV updates
- **Near real-time** via WHO ICTRP aggregation

#### Data Format
- **CSV** (bulk download)
- HTML (individual trial pages)
- WHO ICTRP provides XML/JSON

#### Reliability Rating
**High** — Academic network (42 national university hospitals), WHO Primary Registry, ICMJE-recognized

#### Specific Use Case for ClinicalQuant
- Japan-origin trials for Daiichi Sankyo, Astellas, Eisai, Chugai, Takeda pipeline tracking
- J-CTN (Japan Clinical Trial Number) signals before US IND filing
- ADC (antibody-drug conjugate) and IO trial landscape in Japan
- **Recommendation**: Build weekly UMIN-CTR CSV download + ETL pipeline as Tier 2 source

### 7b. jRCT (Japan Registry of Clinical Trials)

#### Source Name and URL
- **Name**: jRCT (Japan Registry of Clinical Trials)
- **URL**: https://jrct.mhlw.go.jp (migrated from jrct.niph.go.jp in April 2025)
- **Backed by**: MHLW (Ministry of Health, Labour and Welfare)

#### Access Method
**Manual Only** — Explicitly prohibits automated downloads
- Terms of use on search page state: no automated/scraping access
- No API, no export, no bulk download
- Cross-searchable via JPRN Portal (Japan Primary Registries Network)

#### Rate Limits and Pricing
- **Automated downloads prohibited** by terms of use
- Manual browsing: free

#### Data Freshness
- **Near real-time** (government-maintained)
- Cross-searchable via WHO ICTRP

#### Data Format
- **HTML** only
- No export available
- WHO ICTRP provides XML/JSON for jRCT records

#### Reliability Rating
**Medium-High** — Government-backed (MHLW), high data quality, but access restrictions severely limit pipeline utility

#### Specific Use Case for ClinicalQuant
- Regulatory-mandated trials under Japan's Clinical Trials Act (2017+)
- These trials MUST be in jRCT by law — covers a subset UMIN-CTR misses
- **CRITICAL**: Do NOT scrape jRCT (prohibited by terms). Use WHO ICTRP + UMIN-CTR CSV for Japan coverage without violating terms

---

## 8. EudraCT / EU Clinical Trials Register

### Source Name and URL
- **Name**: EudraCT / EU Clinical Trials Register
- **URL**: https://www.clinicaltrialsregister.eu/
- **Search**: https://www.clinicaltrialsregister.eu/ctr-search/search
- **Note**: Being replaced by CTIS (euclinicaltrials.eu) for new trials as of Jan 31, 2023

### Access Method
**Web Scraping + CSV Export** (20 records per batch limit)
- No REST API
- CSV export available but limited to 20 records per batch (severely limits bulk collection)
- XML available for some results data
- Zipped full records available for some trials

### Rate Limits and Pricing
- **Pricing**: Free
- **20-record CSV export limit** per batch — requires pagination scraping
- No published rate limits for web access

### Data Freshness
- **Daily-to-weekly** for EudraCT data
- CTIS provides real-time for new-regime trials
- Legacy EudraCT data continues to be updated

### Data Format
- **CSV** (20 records/batch limit)
- **XML** (results data)
- **HTML** (individual trial pages)
- **Zipped** full records

### Reliability Rating
**Medium** — Well-maintained EU regulatory database, but 20-record CSV limit cripples bulk collection and CTIS migration splits the data landscape

### Specific Use Case for ClinicalQuant
- EU trial approvals and EudraCT number assignment (precedes authorization)
- Results posting before journal publication
- Paediatric Investigation Plan (PIP) trial requirements
- Cross-reference with CTIS for new-regime trials
- **Recommendation**: Build pagination scraper with 20-record batching + throttling for legacy EudraCT data; use CTIS transparency portal manually for new-regime trials until API becomes available

---

## Recommended Pipeline Architecture for ClinicalQuant

### Tier 1 — Build Now (Highest ROI)

1. **ClinicalTrials.gov API v2** — Primary data source
   - Real-time queries via `/api/v2/studies` with sponsor/condition/intervention filters
   - Weekly bulk download via `/api/v2/studies/download?format=json.zip`
   - No auth required, 50 req/min, JSON/CSV output
   - Covers: US + majority of global trials

2. **WHO ICTRP** — Universal backbone aggregator
   - Contact ictrp@who.int for web service pricing
   - Fallback: Use free crawling service or bulk data download
   - Covers: ALL 17+ primary registries in single integration
   - Use for: gap-filling (trials not in ClinicalTrials.gov)

### Tier 2 — Build Next (Incremental Value)

3. **UMIN-CTR CSV** — Japan-specific pipeline
   - Weekly automated CSV download + ETL pipeline
   - Best direct access of any Asian registry
   - Use for: Daiichi Sankyo, Astellas, Eisai, Chugai pipeline tracking

4. **ISRCTN XML API** — UK/EU trial intelligence
   - Two API calls (by ID + search)
   - Free, XML format
   - Use for: NIHR-funded trials, surgical/interventional studies

5. **EudraCT/EU CTR** — Legacy EU trial data
   - Pagination scraper with 20-record batching
   - Use for: EudraCT numbers, PIP trials, results before publication

### Tier 3 — Indirect Access Only (Via WHO ICTRP)

6. **ChiCTR** — Use WHO ICTRP for English-normalized data; direct scrape only for China-specific intelligence
7. **ANZCTR** — Use WHO ICTRP exclusively; no direct export exists
8. **jRCT** — DO NOT SCRAPE (prohibited); use WHO ICTRP + UMIN-CTR CSV instead
9. **EU CTIS** — Monitor for future API; use transparency portal manually until then

### Integration Strategy

~~~
ClinicalTrials.gov v2 (primary) ----\
                                     +---> Supabase cq_regulatory_catalysts
WHO ICTRP (gap-filler) -----------/         + trials tables
                                     |
UMIN-CTR CSV (weekly ETL) ---------+---> Enrichment Pipeline
ISRCTN API (UK/EU supplement) -----+     -> ClinicalQuant
EudraCT scraper (legacy EU) ------/        newsletter alerts
~~~

### Cron Schedule
- **ClinicalTrials.gov**: Every 4 hours (query for new/updated studies by sponsor list)
- **WHO ICTRP**: Daily (crawl for new registrations across all registries)
- **UMIN-CTR CSV**: Weekly (Sunday 5 AM UTC — bulk download + diff)
- **ISRCTN API**: Daily (query for new UK/EU trials)
- **EudraCT scraper**: Daily (paginated crawl with throttling)

---

## Appendix: AACT Database (Bonus Resource)

- **Name**: Aggregate Analysis of ClinicalTrials.gov (AACT)
- **URL**: https://aact.ctti-clinicaltrials.org/
- **Access**: Free PostgreSQL database (daily refresh from ClinicalTrials.gov)
- **Format**: SQL (PostgreSQL), CSV exports available
- **Use Case**: Offline analytical queries, historical trend analysis, ML training datasets
- **Limitation**: Same data as ClinicalTrials.gov API but in relational format; no additional registries
- **Recommendation**: Use for complex analytical queries that would require many API calls; supplement API v2, not replace it
