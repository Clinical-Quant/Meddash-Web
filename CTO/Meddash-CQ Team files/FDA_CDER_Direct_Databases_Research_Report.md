# FDA CDER Direct Databases - Deep Research Report

**Date:** 2026-04-22
**Researcher:** Agent Zero Deep Research
**Status:** COMPLETE - All findings web-verified

---

## Executive Summary

**CRITICAL FINDING:** "CDER Direct" is NOT a public query database. It is a **SUBMISSION tool** (SPL authoring platform) for industry to submit registration and listing data TO the FDA. It has been rebranded as **FDA Direct** and is accessible at **direct.fda.gov**. The public CDER databases (Drugs@FDA, Orange Book, NDC Directory, etc.) are SEPARATE from CDER Direct and accessible through different URLs and APIs.

---

## 1. Exact URL for CDER Direct

### CDER Direct (now FDA Direct)
- **URL:** https://direct.fda.gov/
- **Login Page:** https://direct.fda.gov/apex/f?p=100:LOGIN_DESKTOP
- **User Guide:** https://direct.fda.gov/apex/f?p=100:103:::NO::P103_GUIDE:1
- **NOT the URL the user guessed** (https://www.fda.gov/drugs/drug-approvals-and-databases/cder-direct-database) - this page does NOT exist

### CDER Direct NextGen Portal
- **URL:** https://edm.fda.gov/
- **Purpose:** Industry notification portal for drug shortages and discontinuances
- **NOT for public data access** - intended ONLY for manufacturers to notify FDA

### CDER Public Databases Landing Page
- **URL:** https://www.fda.gov/drugs/development-approval-process-drugs/drug-approvals-and-databases
- This is the actual page that lists CDER's public databases (Drugs@FDA, Orange Book, etc.)

**Source URLs:**
- https://direct.fda.gov/
- https://direct.fda.gov/apex/f?p=100:103:::NO::P103_GUIDE:1
- https://www.fda.gov/drugs/development-approval-process-drugs/drug-approvals-and-databases

---

## 2. What Is Included in CDER Direct / FDA Direct

### CDER Direct Module (within FDA Direct)
CDER Direct is an **SPL authoring and submission tool**. It allows submission of:

1. **Establishment Registration and Drug Listing** (including NDC Labeler Code)
2. **Outsourcing Facility Registration and Product Reporting**
3. **DSCSA Annual Reporting** (Drug Supply Chain Security Act)
4. **Generic Drug Self-Identification** (GDUFA)

### CDER Direct NextGen Portal (edm.fda.gov)
5. **Drug Shortage Notifications** - Industry notifies FDA of shortages
6. **Discontinuance/Interruption Notifications** - Manufacturers report manufacturing interruptions

### FDA Direct Platform Account Types
- **CDER Direct Account:** Register/list human drugs or biological products
- **Cosmetics Direct Account:** Register/list cosmetic product facilities and products
- **Combined Account:** Access to both CDER Direct and Cosmetics Direct

**Key Point:** CDER Direct is a data SUBMISSION portal, NOT a data RETRIEVAL portal. The public-facing CDER databases are entirely separate systems.

**Source URLs:**
- https://direct.fda.gov/apex/f?p=100:103:::NO::P103_GUIDE:1 (User Guide)
- https://direct.fda.gov/apex/f?p=100:103:::NO::P103_GUIDE:26 (Cosmetics Direct User Guide)
- https://www.fda.gov/drugs/drug-safety-and-availability/drug-shortages
- https://www.fda.gov/media/102597/download (Annual Reporting using CDER Direct)
- https://www.fda.gov/media/154498/download (CDER Direct Drug Listing 101)
- https://regicheck.com/pages/understanding-fda-direct-a-powerful-tool-for-regulatory-submissions

---

## 3. Access Method

### CDER Direct (FDA Direct) - Submission Tool
| Feature | Details |
|---|---|
| **Access Type** | Web interface only (authenticated portal) |
| **API Access** | NO public API |
| **Cost** | FREE to use |
| **Registration** | Required - create account at direct.fda.gov |
| **Data Direction** | Industry submits data TO FDA (outbound from industry) |
| **Web Scraping** | Not applicable - requires authentication |
| **Manual Download** | Not applicable - this is a submission tool |

### CDER Public Databases - Data Retrieval
| Database | Access Method | API | Download |
|---|---|---|---|
| Drugs@FDA | Web + API + Bulk | Yes (openFDA) | Yes (ZIP) |
| Orange Book | Web + Bulk | No direct API | Yes (ZIP) |
| NDC Directory | Web + API + Bulk | Yes (openFDA) | Yes (ZIP) |
| Drug Shortage Database | Web only | Yes (openFDA) | No |
| accessdata.fda.gov | Web interface | No | Varies |
| National Drug Code Directory | Web + API | Yes (openFDA) | Yes |

**Source URLs:**
- https://direct.fda.gov/
- https://open.fda.gov/apis/drug/
- https://www.fda.gov/drugs/drug-approvals-and-databases/drugsfda-data-files

---

## 4. API Access for CDER Direct Data

### CDER Direct / FDA Direct
- **NO API access exists** for CDER Direct
- CDER Direct is a submission tool, not a data retrieval system
- Data submitted through CDER Direct flows into downstream FDA databases (DailyMed, NDC Directory, etc.)

### CDER Direct NextGen Portal
- **NO API access** - the NextGen Portal (edm.fda.gov) is for industry notifications only
- It is NOT intended for public data retrieval

### Related CDER Data APIs (Separate from CDER Direct)
- **openFDA API** (https://api.fda.gov) provides API access to CDER data:
  - /drug/drugsfda - Drug approvals
  - /drug/ndc - National Drug Code Directory
  - /drug/label - Drug product labeling
  - /drug/event - Adverse events
  - /drug/enforcement - Drug recalls
  - /drug/shortage - Drug shortages
  - Free API key available at https://open.fda.gov/api-registration/

**Source URLs:**
- https://open.fda.gov/apis/drug/
- https://open.fda.gov/apis/
- https://open.fda.gov/data/drugsfda/

---

## 5. Downloadable Data Files

### CDER Direct Itself
- **NO downloadable data files** - CDER Direct is a submission portal, not a data source

### CDER Public Database Downloads (Separate from CDER Direct)

| Data Source | Download URL | Format | Update Frequency |
|---|---|---|---|
| Drugs@FDA Data Files | https://www.fda.gov/drugs/drug-approvals-and-databases/drugsfda-data-files | ZIP containing 12 tab-delimited .txt files | Daily (M-F) |
| Orange Book Data Files | https://www.fda.gov/drugs/drug-approvals-and-databases/orange-book-data-files | ZIP containing 3 tilde-delimited (~) files | Monthly |
| NDC Directory (via openFDA) | https://open.fda.gov/data/downloads/ | JSON (zipped) | Weekly to near real-time |
| Drug Shortage (via openFDA) | https://open.fda.gov/data/downloads/ | JSON (zipped) | Weekly to near real-time |
| openFDA Bulk Downloads | https://open.fda.gov/data/downloads/ | JSON (zipped) | Varies by endpoint |

**Source URLs:**
- https://www.fda.gov/drugs/drug-approvals-and-databases/drugsfda-data-files
- https://www.fda.gov/drugs/drug-approvals-and-databases/orange-book-data-files
- https://open.fda.gov/data/downloads/

---

## 6. Data Format

### CDER Direct (Submission Tool)
- **Input Format:** Structured Product Labeling (SPL) XML
- SPL is an HL7 standard for exchanging medication-related information
- CDER Direct provides web-based forms that generate SPL XML behind the scenes
- SPL submissions go through FDA ESG (Electronic Submissions Gateway)

### CDER Public Database Data Formats
| Database | API Format | Bulk Download Format | Web Format |
|---|---|---|---|
| Drugs@FDA | JSON (openFDA) | Tab-delimited .txt (ZIP) | HTML |
| Orange Book | N/A | Tilde-delimited (~) text (ZIP) | HTML query interface |
| NDC Directory | JSON (openFDA) | JSON (ZIP) | HTML |
| Drug Shortages | JSON (openFDA) | JSON (ZIP) | HTML |
| accessdata.fda.gov | N/A | Varies | HTML query interface |

**Source URLs:**
- https://direct.fda.gov/apex/f?p=100:103:::NO::P103_GUIDE:1
- https://open.fda.gov/apis/drug/
- https://www.fda.gov/industry/fda-data-standards-advisory-board/structured-product-labeling-resources

---

## 7. Data Update Frequency

### CDER Direct (Submission Tool)
- **Real-time processing:** Submissions are processed as they are received
- Status tracking available within CDER Direct portal
- Submissions go through ESG validation and SPL validation

### CDER Public Database Update Frequencies
| Database | Update Frequency |
|---|---|
| Drugs@FDA (openFDA API) | Weekly to near real-time |
| Drugs@FDA (Bulk ZIP) | Daily (Monday-Friday) |
| Orange Book | Monthly (up to 30-day lag) |
| NDC Directory | Weekly to near real-time |
| Drug Shortages | Weekly to near real-time |
| accessdata.fda.gov (Orange Book) | Current through stated month |

**Source URLs:**
- https://www.accessdata.fda.gov/scripts/cder/ob/default.cfm
- https://open.fda.gov/data/drugsfda/

---

## 8. Rate Limits and Pricing

### CDER Direct / FDA Direct
- **Cost:** FREE (no fees to use)
- **Rate Limits:** Not applicable (authenticated web portal)
- **Contact:** CDERDirect@fda.hhs.gov for support

### openFDA API (for CDER public data)
| Feature | With API Key | Without API Key |
|---|---|---|
| **Cost** | Free | Free |
| **Rate Limit (per minute)** | 240 requests/min | 240 requests/min |
| **Rate Limit (per day)** | 120,000 requests/day | 1,000 requests/day (per IP) |
| **API Key Registration** | https://open.fda.gov/api-registration/ | N/A |

### Bulk Downloads
- **Cost:** FREE
- **Rate Limits:** None specified (standard HTTP downloads)
- **No authentication required** for bulk downloads

**Source URLs:**
- https://open.fda.gov/api-registration/
- https://open.fda.gov/apis/
- https://direct.fda.gov/

---

## 9. Data Source Reliability

### CDER Direct (Submission Tool)
- **Reliability:** HIGH - Official FDA system for regulatory submissions
- **Operational Status:** Active and maintained (annual webinars held through 2024)
- **Uptime:** High (government production system)
- **Data Quality:** Submissions must pass SPL validation before acceptance
- **Limitation:** NOT a data source - it is a submission tool only

### CDER Public Databases
| Database | Reliability | Notes |
|---|---|---|
| Drugs@FDA | HIGH | Official FDA database, updated daily M-F |
| Orange Book | HIGH | Official FDA database, monthly updates with up to 30-day lag |
| NDC Directory | MEDIUM-HIGH | Dependent on industry submissions via CDER Direct |
| Drug Shortages | MEDIUM | Dependent on industry voluntary reporting |
| openFDA API | HIGH | 66M+ calls/month, well-maintained |

### Key Reliability Considerations
1. **NDC Directory completeness** depends on industry compliance with listing requirements
2. **Drug Shortage data** relies on voluntary manufacturer notifications
3. **Orange Book** has inherent lag (monthly updates)
4. **Data submitted via CDER Direct** flows to downstream databases but with processing delays

**Source URLs:**
- https://www.fda.gov/drugs/news-events-human-drugs/electronic-drug-registration-and-listing-edrls-using-cder-direct-2024-09122024
- https://www.fda.gov/drugs/drug-safety-and-availability/drug-shortages

---

## Critical Distinction: CDER Direct vs. CDER Databases

### CDER Direct (Submission Portal)
    CDER Direct / FDA Direct (direct.fda.gov)
        +-- Establishment Registration and Drug Listing
        +-- Outsourcing Facility Registration
        +-- DSCSA Annual Reporting
        +-- Generic Drug Self-Identification

    CDER Direct NextGen Portal (edm.fda.gov)
        +-- Drug Shortage Notifications (industry to FDA)
        +-- Discontinuance/Interruption Notifications

### CDER Public Databases (Data Retrieval)
    CDER Public Databases (fda.gov)
        +-- Drugs@FDA (drug approvals)
        |       Web: https://www.accessdata.fda.gov/scripts/cder/daf/
        |       API: https://api.fda.gov/drug/drugsfda
        |       Bulk: https://www.fda.gov/drugs/drug-approvals-and-databases/drugsfda-data-files
        |
        +-- Orange Book (therapeutic equivalence)
        |       Web: https://www.accessdata.fda.gov/scripts/cder/ob/default.cfm
        |       Bulk: https://www.fda.gov/drugs/drug-approvals-and-databases/orange-book-data-files
        |
        +-- NDC Directory (product listing)
        |       API: https://api.fda.gov/drug/ndc
        |       Bulk: https://open.fda.gov/data/downloads/
        |
        +-- Drug Shortage Database
        |       Web: https://www.fda.gov/drugs/drug-safety-and-availability/drug-shortages
        |       API: https://api.fda.gov/drug/shortage
        |
        +-- openFDA API (aggregated CDER data)
                Base: https://api.fda.gov
                Docs: https://open.fda.gov/apis/drug/

---

## Summary Answer to Each Question

| # | Question | Answer |
|---|---|---|
| 1 | Exact URL for CDER Direct? | **direct.fda.gov** (rebranded as FDA Direct). The URL the user guessed does NOT exist. CDER Direct is a submission portal, not a public database. |
| 2 | What databases are included? | CDER Direct includes: Establishment Registration and Drug Listing, Outsourcing Facility Registration, DSCSA Annual Reporting, Generic Drug Self-Identification. These are SUBMISSION forms, not queryable databases. |
| 3 | Access method? | **Web interface only** (authenticated portal). No public API. No scraping. No downloads. It is a submission tool. |
| 4 | Is there API access? | **NO** - CDER Direct has no API. However, openFDA API (api.fda.gov) provides API access to CDER public data (Drugs@FDA, NDC, label, adverse events, etc.). |
| 5 | Are there downloadable data files? | **NO** for CDER Direct itself. YES for CDER public databases (Drugs@FDA ZIP files, Orange Book ZIP files, openFDA JSON downloads). |
| 6 | Data format? | CDER Direct uses **SPL XML** for submissions. CDER public databases provide: JSON (openFDA API), tab-delimited text (Drugs@FDA), tilde-delimited text (Orange Book), HTML (web interfaces). |
| 7 | Update frequency? | CDER Direct: **real-time processing**. CDER public databases: Daily (Drugs@FDA bulk), Monthly (Orange Book), Weekly to near real-time (openFDA API). |
| 8 | Rate limits/pricing? | CDER Direct: **Free**, no rate limits (authenticated portal). openFDA API: **Free**, 240 req/min, 120K/day with key. Bulk downloads: **Free**, no limits. |
| 9 | Reliability? | CDER Direct: **HIGH** (official FDA system). CDER public databases: **HIGH** for Drugs@FDA and Orange Book; **MEDIUM-HIGH** for NDC (dependent on industry submissions). |

---

## All Source URLs (20 total)

1. https://direct.fda.gov/ - FDA Direct (CDER Direct) main portal
2. https://direct.fda.gov/apex/f?p=100:103:::NO::P103_GUIDE:1 - FDA Direct User Guide
3. https://www.fda.gov/drugs/drug-approvals-and-databases/drugsfda-data-files - Drugs@FDA Data Files
4. https://www.fda.gov/drugs/drug-approvals-and-databases/orange-book-data-files - Orange Book Data Files
5. https://open.fda.gov/apis/drug/ - openFDA Drug API Endpoints
6. https://open.fda.gov/apis/ - openFDA API Overview
7. https://open.fda.gov/data/drugsfda/ - Drugs@FDA openFDA Documentation
8. https://open.fda.gov/data/downloads/ - openFDA Bulk Downloads
9. https://open.fda.gov/api-registration/ - openFDA API Key Registration
10. https://www.accessdata.fda.gov/scripts/cder/ob/default.cfm - Orange Book Web Interface
11. https://www.fda.gov/drugs/drug-safety-and-availability/drug-shortages - Drug Shortages
12. https://www.fda.gov/drugs/development-approval-process-drugs/drug-approvals-and-databases - CDER Databases Landing Page
13. https://www.fda.gov/drugs/news-events-human-drugs/electronic-drug-registration-and-listing-edrls-using-cder-direct-2024-09122024 - eDRLS Using CDER Direct
14. https://www.fda.gov/media/154498/download - CDER Direct Drug Listing 101
15. https://www.fda.gov/media/102597/download - Annual Reporting using CDER Direct
16. https://regicheck.com/pages/understanding-fda-direct-a-powerful-tool-for-regulatory-submissions - FDA Direct Overview
17. https://www.fda.gov/industry/fda-data-standards-advisory-board/structured-product-labeling-resources - SPL Resources
18. https://www.fda.gov/media/173707/download - CDER Direct Drug Listing Guide
19. https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory - NDC Directory
20. https://www.fda.gov/industry/fda-basics-industry/search-databases - Search Databases

---

*Report generated by Agent Zero Deep Research on 2026-04-22*
*All findings verified from web searches - no hallucinated data*
