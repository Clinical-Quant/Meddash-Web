# Biotech Data Source Research Report: FDA Sources for ClinicalQuant Newsletter

**Date**: 2026-04-22  
**Researcher**: Agent Zero Deep Research  
**Project**: MedDash-CQ / ClinicalQuant Catalyst Newsletter  

---

## SOURCE A: FDA OpenFDA API

### 1. Source Name and URL
**FDA OpenFDA API**  
URL: https://open.fda.gov  
API Base: https://api.fda.gov  
GitHub: https://github.com/FDA/openfda  

### 2. Access Method
**Free API** (REST-based, Elasticsearch-backed)  
- API key required (free to obtain at https://open.fda.gov/apis/authentication/)  
- No paid tiers exist — completely free public API  
- No OAuth or complex authentication — just include `api_key=` parameter in requests  

### 3. Rate Limits and Pricing Tiers

| Tier | Requests/Minute | Requests/Day | Cost |
|------|----------------|--------------|------|
| **With API Key** | 240 | 120,000 | Free |
| **Without API Key** | 40 | 1,000 | Free |

- API key is free; just register email on the OpenFDA site  
- Rate limits are per IP address  
- No premium/paid tiers available  

### 4. Data Freshness
Varies by endpoint:  
- **Drug Adverse Events** (`/drug/event`): Weekly refresh (as of Aug 2025, FDA started publishing daily FAERS data, but API refresh is typically weekly)  
- **Drug Labeling** (`/drug/label`): Weekly  
- **Drug Enforcement/Recalls** (`/drug/enforcement`): Weekly  
- **Drug NDC Directory** (`/drug/ndc`): Daily  
- **Drugs@FDA** (`/drug/drugsfda`): Weekly (aligned with bulk data file updates)  

**Overall**: Primarily **weekly** for most drug endpoints, **daily** for NDC. Not real-time.  

### 5. Data Format
**JSON** (REST API returns JSON responses)  
- Supports query parameters: `search`, `limit`, `skip`, `count`, `date`  
- Supports `sort` and `count` aggregations  
- Max 1000 results per query (use `skip` for pagination)  
- Bulk downloads also available in JSON format at https://open.fda.gov/apis/downloads/  

### 6. Reliability Rating
**High**  
- Official FDA government API  
- Elasticsearch-backed, well-documented  
- Active maintenance (GitHub repo, regular updates page)  
- Uptime generally stable but occasional outages during data refreshes  
- Disclaimer: FDA states data may have reporting lags  

### 7. Specific Use Case for Biotech Catalyst Newsletter

| Endpoint | Use Case |
|----------|----------|
| `/drug/drugsfda` | **PRIMARY**: Track drug approvals (NDA, ANDA, BLA), approval dates, application numbers, sponsor names, product details |
| `/drug/event` | Monitor adverse event spikes for portfolio companies — potential catalysts (safety signals, boxed warning additions) |
| `/drug/enforcement` | Track drug recalls and enforcement actions — major negative catalysts for affected companies |
| `/drug/label` | Labeling changes (new indications, contraindications) — positive/negative catalysts |
| `/drug/ndc` | Product catalog lookups — map NDC codes to company tickers for automated tracking |

**Catalyst-specific workflow**: Query `/drug/drugsfda` for recent approvals by date range, cross-reference sponsor names with CQ ticker database, generate approval alerts for newsletter.  

---

## SOURCE B: Drugs@FDA

### 1. Source Name and URL
**Drugs@FDA (FDA-Approved Drugs)**  
Web URL: https://www.accessdata.fda.gov/scripts/cder/daf/  
Data Files URL: https://www.fda.gov/drugs/drug-approvals-and-databases/drugsfda-data-files  
OpenFDA Data Page: https://open.fda.gov/data/drugsfda/  
Data.gov Listing: https://catalog.data.gov/dataset/drugsfda-database  

### 2. Access Method
**Hybrid: Web Scraping + Bulk Download**  
- **No direct API** — the accessdata.fda.gov website has no programmatic API  
- **Bulk download**: Compressed ZIP file (`drugsatfda.zip`) containing 12 tab-delimited text tables  
- **Programmatic access via OpenFDA**: The `/drug/drugsfda` endpoint provides JSON API access to the same underlying data  
- **Web scraping possible** but the site uses dynamic forms (search by drug name, application number) — not ideal for automation  

### 3. Rate Limits and Pricing Tiers

| Access Method | Rate Limit | Cost |
|--------------|-----------|------|
| **Bulk ZIP download** | Unlimited (one-time download) | Free |
| **Web interface** | No stated limits (CAPTCHA likely for abuse) | Free |
| **OpenFDA API** (recommended) | 240 req/min with key | Free |

- No paid tiers exist  
- All access is free  

### 4. Data Freshness
- **Web interface (accessdata.fda.gov)**: Updated **daily**  
- **Bulk data file (drugsatfda.zip)**: Updated **each morning, Monday through Friday** (per current FDA.gov page; some older references cite weekly on Tue/Wed — FDA has moved to daily M-F updates)  
- **OpenFDA drugsfda endpoint**: Updated **weekly** (aligned with bulk data refresh cycle)  

**Overall**: Bulk file is **daily (M-F)**, API is **weekly**. For near-real-time, use the web interface or check daily downloads.  

### 5. Data Format

| Access Method | Format |
|--------------|--------|
| **Bulk ZIP download** | ZIP containing 12 tab-delimited text files (.txt) |
| **Web interface** | HTML (requires scraping) |
| **OpenFDA API** | JSON |

**Bulk file structure** (drugsatfda.zip unzips into 12 text tables):  
- Tab-delimited fields  
- Includes: Applications, Products, Marketing Status, Therapeutic Equivalence, Approval Letters, Reviews, etc.  
- Primary keys and field definitions documented on FDA data files page  
- Covers drug products approved since 1939 (complete data since 1998)  

### 6. Reliability Rating
**High**  
- Official FDA authoritative source for drug approval data  
- Gold standard for FDA-approved drug product information  
- Includes NDA, ANDA, BLA submissions with approval dates, sponsors, product details  
- Data sourced directly from FDA's Center for Drug Evaluation and Research (CDER)  
- Data.gov listing confirms dataset maintenance and metadata  
- Minor concern: Bulk file may lag 1 business day behind web interface  

### 7. Specific Use Case for Biotech Catalyst Newsletter

| Data Element | Catalyst Use Case |
|-------------|-------------------|
| **Approval dates** | Track NDA/BLA approvals by date — primary positive catalyst for biotech stocks |
| **Application numbers** | Cross-reference PDUFA date calendar with actual approval events |
| **Sponsor/applicant names** | Map approvals to company tickers for automated portfolio tracking |
| **Marketing status** | Detect new market entries, discontinuations, or regulatory status changes |
| **Therapeutic equivalence** | Identify generic approvals (ANDA) that may impact brand-name competitors |
| **Approval letters/reviews** | Extract key details (indications, conditions, REMS) for catalyst analysis |
| **BLA tracking** | Monitor biologics approvals — critical for cell/gene therapy and mAb companies |

**Recommended workflow**:  
1. Daily download of `drugsatfda.zip` for complete dataset refresh  
2. Diff against previous day's data to identify new approvals, status changes  
3. Cross-reference sponsor names with CQ ticker database  
4. Use OpenFDA `/drug/drugsfda` API for ad-hoc queries between bulk refreshes  
5. Generate approval alert content for newsletter publication  

---

## Comparative Summary

| Field | OpenFDA API | Drugs@FDA |
|-------|-------------|-----------|
| **URL** | https://open.fda.gov | https://www.accessdata.fda.gov/scripts/cder/daf/ |
| **Access** | Free API | Web + Bulk Download (ZIP) |
| **Rate Limits** | 240/min (w/ key), 40/min (no key) | None for bulk; web has no stated limits |
| **Pricing** | Free (all tiers) | Free |
| **Freshness** | Weekly (most endpoints); Daily (NDC) | Daily M-F (bulk); Weekly (API); Daily (web) |
| **Format** | JSON | Tab-delimited TXT (bulk); HTML (web); JSON (via OpenFDA) |
| **Reliability** | High | High |
| **Best For** | Real-time queries, adverse event monitoring, recall alerts | Complete approval dataset, sponsor mapping, approval date tracking |

### Recommended Integration Strategy
1. **Primary**: Use OpenFDA `/drug/drugsfda` API for automated daily queries tracking recent approvals  
2. **Secondary**: Daily bulk download of `drugsatfda.zip` for full dataset refresh and diff-based change detection  
3. **Tertiary**: OpenFDA `/drug/event` and `/drug/enforcement` for adverse event and recall catalysts  
4. **Tertiary**: OpenFDA `/drug/label` for labeling change catalysts (new indications, safety updates)  

Both sources are **complementary** — OpenFDA provides queryable JSON API access while Drugs@FDA bulk data provides the complete authoritative dataset for local analysis and diff detection.  

---

*Report generated by Agent Zero Deep Research — all facts verified via web search on 2026-04-22*
