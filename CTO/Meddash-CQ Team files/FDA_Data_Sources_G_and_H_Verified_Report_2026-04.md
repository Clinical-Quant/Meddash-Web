# FDA Data Sources G & H - Verified Research Report
**Date:** 2026-04-22  
**Project:** ClinicalQuant (MedDash-CQ)  
**Researcher:** Agent Zero Deep Research  
**Methodology:** Web-verified data only. No hallucination.

---

## Executive Summary

| Source | Access Method | Data Format | Freshness | Reliability | CQ Priority |
|--------|--------------|-------------|-----------|-------------|-------------|
| G: Drug Safety Communications | RSS + Web Scraping | RSS/XML, HTML | Near real-time (hours) | High | **High** - Direct catalyst source |
| H: CDER Direct Databases | N/A (Submission Tool) | N/A | N/A | N/A | **SKIP** - Not a data source |

**Critical Finding:** CDER Direct (Source H) is NOT a public query database. It is an industry submission portal rebranded as "FDA Direct" at direct.fda.gov. The actual CDER public databases are separate, accessible via openFDA API and bulk downloads (already covered in Sources A-C of our pipeline).

---

## SOURCE G: FDA Drug Safety Communications

### 1. Source Name and URL
- **Name:** FDA Drug Safety Communications
- **Main Page:** https://www.fda.gov/drugs/drug-safety-and-availability/drug-safety-communications
- **MedWatch Safety Alerts RSS:** https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/medwatch/rss.xml
- **Drug Safety Podcasts RSS:** https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/drug-safety-podcast/rss.xml
- **What's New: Drugs RSS:** https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/drugs/rss.xml
- **Email Alerts Subscription:** https://www.fda.gov/safety/medwatch-fda-safety-information-and-adverse-event-reporting-program/subscribe-medwatch-safety-alerts
- **openFDA Drug Enforcement (related):** https://api.fda.gov/drug/enforcement

### 2. Access Method
**RSS + Web Scraping + Email Alerts + Related API**

- **RSS Feeds (Primary):** Three relevant RSS feeds available:
  - MedWatch Safety Alerts RSS - covers all human medical product safety alerts including drug safety communications
  - Drug Safety Podcasts RSS - audio versions of Drug Safety Communications
  - What's New: Drugs RSS - broader drug-related updates
- **Web Scraping (Supplementary):** The Drug Safety Communications landing page lists all DSCs with titles and dates; structured HTML can be scraped for new additions
- **Email Alerts (Alternative):** MedWatch email subscription for push notifications of safety alerts
- **openFDA Drug Enforcement API (Related):** Covers drug recalls via the Recall Enterprise System, but does NOT include Drug Safety Communications specifically. Endpoint: `https://api.fda.gov/drug/enforcement`

### 3. Rate Limits and Pricing Tiers

| Access Method | Rate Limits | Pricing |
|--------------|-------------|----------|
| RSS Feeds | No limits (standard RSS polling) | Free |
| Web Scraping | Respect robots.txt; recommended 1 req/10-30 sec | Free |
| Email Alerts | No limits | Free |
| openFDA Drug Enforcement API | With key: 240 req/min, 120K/day; Without key: 240 req/min, 1K day/IP | Free (key at open.fda.gov/api-registration/) |

### 4. Data Freshness
- **MedWatch RSS:** Near real-time - updated within hours of FDA safety communication publication
- **Drug Safety Podcasts RSS:** Same-day - published alongside Drug Safety Communications
- **What's New: Drugs RSS:** Near real-time
- **Web Page:** Updated in real-time when new DSCs are posted
- **openFDA Drug Enforcement:** Updated weekly to near real-time

### 5. Data Format
- **RSS Feeds:** XML (RSS 2.0 format)
- **Drug Safety Communications Web Page:** HTML
- **openFDA Drug Enforcement API:** JSON
- **Email Alerts:** HTML email

### 6. Reliability Rating
**High**

- Official FDA source with consistent publication schedule
- RSS feeds are actively maintained (verified 2024-2026 content)
- MedWatch system is FDA's primary safety communication channel
- Drug Safety Communications follow a standardized format with consistent metadata
- Minor concern: RSS feeds may occasionally lag by hours (not days)

### 7. Specific Use Case for ClinicalQuant

**Primary Use Case: Drug Safety Communication Catalyst Alerts**

Drug Safety Communications are HIGH-IMPACT biotech catalysts because they:
1. **Signal Label Changes:** Boxed warnings, contraindications, warnings - directly affect commercial outlook
2. **REMS Actions:** New or modified Risk Evaluation and Mitigation Strategies - restrict market access
3. **Safety Signals:** Early warnings about adverse events - can crater stock prices (e.g., FDA DSC on Aduhelm safety concerns)
4. **Market Withdrawal Indicators:** Communication precedes actual market withdrawals

**ClinicalQuant Pipeline Integration:**

| Pipeline Stage | Implementation | Priority |
|---------------|----------------|----------|
| Ingestion | Poll MedWatch RSS every 15 minutes via cron job | P0 |
| Parsing | Extract drug names, safety issue, FDA action from RSS title/description | P0 |
| Ticker Mapping | Cross-reference drug names to tickers via NDC/Drugs@FDA | P1 |
| Alert Generation | Push notification for DSCs affecting portfolio tickers | P0 |
| Newsletter Content | Auto-generate DSC summary for affected tickers | P1 |
| Historical Analysis | Scrape full DSC archive for backtesting | P2 |

**Recommended Implementation:**
- **Primary:** Monitor MedWatch Safety Alerts RSS feed (broadest coverage, includes device/drug safety)
- **Secondary:** Scrape Drug Safety Communications page for DSC-specific content
- **Tertiary:** openFDA Drug Enforcement API for recall enforcement reports (complementary data)

---

## SOURCE H: FDA CDER Direct Databases

### 1. Source Name and URL
- **Name:** FDA CDER Direct (now FDA Direct)
- **FDA Direct Portal:** https://direct.fda.gov/
- **Login Page:** https://direct.fda.gov/apex/f?p=100:LOGIN_DESKTOP
- **CDER Public Databases Landing:** https://www.fda.gov/drugs/development-approval-process-drugs/drug-approvals-and-databases
- **NOTE:** The originally provided URL (https://www.fda.gov/drugs/drug-approvals-and-databases/cder-direct-database) does NOT exist

### 2. Access Method
**N/A - CDER Direct is NOT a public data source**

CDER Direct (now FDA Direct) is an **industry SUBMISSION portal**, not a query database. It is used by pharmaceutical companies to:
- Submit Establishment Registration and Drug Listing data (NDC Labeler Code)
- Submit Outsourcing Facility Registration and Product Reporting
- Submit DSCSA Annual Reporting
- Submit Generic Drug Self-Identification (GDUFA)
- Submit Drug Shortage Notifications (via NextGen Portal)
- Submit Discontinuance/Interruption Notifications

Access method: **Authenticated web interface only** (requires FDA account). No API. No public data access. No scraping.

### 3. Rate Limits and Pricing
**N/A** - Not a public data source. Registration required for industry submissions only.

### 4. Data Freshness
**N/A** - Submission tool, not a data source.

### 5. Data Format
**N/A** - Submission format is SPL XML, but this is for inbound submissions to FDA, not outbound data.

### 6. Reliability Rating
**N/A** - Not applicable as a data source. FDA Direct is a reliable submission system, but it does not provide public data.

### 7. Specific Use Case for ClinicalQuant

**SKIP - Not a viable data source for ClinicalQuant.**

CDER Direct/FDA Direct is an industry submission portal. It contains no publicly queryable data. However, the data submitted through CDER Direct flows into separate public databases that ARE relevant:

| Relevant CDER Database | Access Method | Already in CQ Pipeline? |
|----------------------|--------------|------------------------|
| Drugs@FDA | Bulk ZIP download + openFDA API | YES (Source A/B) |
| Orange Book | Bulk ZIP download | YES (Source C) |
| NDC Directory | openFDA API | YES (Source A) |
| Drug Shortages | openFDA API (`/drug/shortage`) | Partially |
| Adverse Events | openFDA API (`/drug/event`) | YES (Source A) |
| Drug Enforcement/Recalls | openFDA API (`/drug/enforcement`) | YES (Source A) |

**Action Item:** The only gap from CDER databases not yet in our pipeline is the **Drug Shortage API** (`/drug/shortage` on openFDA). This should be evaluated as a future addition.

---

## Comparison: Sources G vs H

| Dimension | Source G (Drug Safety Communications) | Source H (CDER Direct) |
|-----------|---------------------------------------|----------------------|
| **Data Type** | Safety alerts, label changes, boxed warnings | Industry submission portal (no public data) |
| **Access** | RSS + Web Scraping + Email + openFDA API | Authenticated web portal only |
| **Format** | XML (RSS), HTML, JSON (openFDA) | N/A |
| **Freshness** | Near real-time (hours) | N/A |
| **Reliability** | High | N/A (not a data source) |
| **CQ Priority** | **HIGH** - Direct catalyst source | **SKIP** - Not a data source |
| **Implementation Effort** | Low (RSS polling) | N/A |
| **Catalyst Impact** | Very High (box warnings, REMS, safety signals) | N/A |

---

## Implementation Recommendations

### Source G: Immediate Implementation (Priority P0)

1. **Set up MedWatch RSS polling** (cron every 15 minutes)
   ```bash
   # Poll MedWatch RSS feed
   curl -s "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/medwatch/rss.xml" | python3 parse_medwatch_rss.py
   ```

2. **Set up Drug Safety Communications page scraper** (daily)
   - Target: https://www.fda.gov/drugs/drug-safety-and-availability/drug-safety-communications
   - Extract: DSC title, date, drug names, safety issue, FDA action

3. **Integrate openFDA Drug Enforcement API** for recall enforcement reports
   - Endpoint: `https://api.fda.gov/drug/enforcement?api_key=YOUR_KEY&limit=100`
   - Complements DSCs with structured recall data

4. **Cross-reference drug names to tickers** via Drugs@FDA/NDC mapping

### Source H: Skip Entirely

CDER Direct is not a data source. All relevant CDER public databases are already covered by Sources A-C in our existing pipeline.

**One gap to consider:** `openFDA /drug/shortage` endpoint for drug shortage monitoring - evaluate as future addition.

---

## Verified Source URLs

| Resource | URL |
|----------|-----|
| Drug Safety Communications (main) | https://www.fda.gov/drugs/drug-safety-and-availability/drug-safety-communications |
| MedWatch Safety Alerts RSS | https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/medwatch/rss.xml |
| Drug Safety Podcasts RSS | https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/drug-safety-podcast/rss.xml |
| What's New: Drugs RSS | https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/drugs/rss.xml |
| MedWatch Email Subscription | https://www.fda.gov/safety/medwatch-fda-safety-information-and-adverse-event-reporting-program/subscribe-medwatch-safety-alerts |
| openFDA Drug Enforcement API | https://api.fda.gov/drug/enforcement |
| openFDA API Registration | https://open.fda.gov/api-registration/ |
| FDA Direct (formerly CDER Direct) | https://direct.fda.gov/ |
| CDER Public Databases | https://www.fda.gov/drugs/development-approval-process-drugs/drug-approvals-and-databases |
| Drugs@FDA Data Files | https://www.fda.gov/drugs/drug-approvals-and-databases/drugsfda-data-files |

---

*Report generated 2026-04-22 by Agent Zero Deep Research. All data web-verified.*
