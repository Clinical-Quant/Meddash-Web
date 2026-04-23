# Biotech Data Sources Research Report: Sources C & D
## ClinicalQuant Newsletter — Verified Data Source Analysis

**Research Date:** 2026-04-22
**Analyst:** Agent Zero Deep Research
**Status:** Web-verified facts only — no hallucinated data

---

## SOURCE C: Conference Abstract Sources (ASCO, ESMO, ASH)

### 1. Source Name and URL

| Conference | Primary URL | Abstract Access URL |
|---|---|---|
| ASCO | https://www.asco.org | https://ascopubs.org/jco/meeting |
| ESMO | https://www.esmo.org | https://www.annalsofoncology.org (supplements) |
| ASH | https://www.hematology.org | https://ashpublications.org/blood (supplements) |

**Crossref API (meta-level access):** https://api.crossref.org
**PubMed E-utilities (meta-level access):** https://eutils.ncbi.nlm.nih.gov/entrez/eutils/

### 2. Access Method

**Primary: Free API (Crossref, PubMed) + RSS + Web Scraping**

- **ASCO:** RSS feeds available at https://ascopubs.org/about/rss for JCO journals including meeting abstracts. No direct public API for abstract search. Meeting abstracts are published as a special section in JCO. Abstracts become publicly available at a specific embargo lift time (e.g., May 21, 2026 at 5:00 PM ET for ASCO 2026).
- **ESMO:** Abstracts published as supplements to Annals of Oncology on ScienceDirect (Elsevier). No direct API; access requires ScienceDirect subscription or free abstract viewing. ESMO Congress abstracts are also available at https://www.esmo.org/meeting-calendar/esmo-congress-2025/abstracts with open access per ESMO policy.
- **ASH:** Abstracts published as supplements to Blood journal (ashpublications.org/blood) and on ScienceDirect. ASH 2025 accepted 8,200+ abstracts. Abstracts searchable at https://apps.hematology.org/annual-meeting/ (search by title, abstract, author, institution, or topic number).
- **Crossref REST API:** Free, no signup required. Covers ASCO (26,796 registered records per Crossref participation report), ESMO, and ASH conference proceedings with DOIs. Provides metadata including abstracts where deposited by publishers. Access via https://api.crossref.org/works with query filters.
- **PubMed E-utilities:** Free API (https://eutils.ncbi.nlm.nih.gov/entrez/eutils/). ASCO, ESMO, and ASH abstracts are indexed in MEDLINE/PubMed and searchable by conference name, journal supplement, or DOI. Confirmed: 2025 ASCO abstracts appear in PubMed search results.

### 3. Rate Limits and Pricing Tiers

| Access Method | Rate Limit | Pricing |
|---|---|---|
| Crossref REST API (public pool) | 50 req/sec (updated Dec 1, 2025) | Free — no signup required |
| Crossref REST API (polite pool) | Higher throughput with mailto parameter | Free — provide email in mailto param |
| Crossref Plus (authenticated) | Premium rate limits, SLA | Paid subscription required |
| PubMed E-utilities | 3 req/sec without API key; 10 req/sec with API key | Free (API key available at no cost) |
| ScienceDirect (ESMO/ASH supplements) | Varies — Elsevier API rate limits | Institutional subscription or pay-per-view for full text; abstracts often free |
| ASH abstracts search | No published rate limit (interactive web search) | Free |
| ASCO RSS feeds | Standard RSS — no documented rate limit | Free |

### 4. Data Freshness

| Source | Freshness | Notes |
|---|---|---|
| ASCO abstracts | **Annual** (May/June) | Published at embargo lift during annual meeting; late-breaking abstracts released during meeting |
| ESMO abstracts | **Annual** (September/October) | Published as Annals of Oncology supplement before congress |
| ASH abstracts | **Annual** (November/December) | Published as Blood supplement; 2025 abstracts available Nov 3, 2025 |
| Crossref metadata | **Near real-time** (hours to days after registration) | Depends on publisher deposit timing |
| PubMed indexing | **Days to weeks** after publication | Lag varies by journal deposit schedule |

### 5. Data Format

| Access Method | Format |
|---|---|
| Crossref REST API | JSON (default), XML also available |
| PubMed E-utilities | XML, JSON, ASN.1 |
| ASCO RSS feeds | RSS/XML |
| ScienceDirect (ESMO/ASH) | HTML (web), XML (API), PDF (full text) |
| ASH abstracts search | HTML (web scraping) |

### 6. Reliability Rating: **Medium-High**

**Justification:**
- Crossref API is well-maintained, has 1B+ hits/month, and is a standard scholarly infrastructure service
- PubMed E-utilities are a stable, NIH-funded service running for decades
- Conference abstracts ARE reliably indexed but with a lag (days to weeks after publication)
- Abstract content availability varies: Crossref has abstracts only when publishers deposit them (not all do)
- PubMed may not include full abstract text for all conference proceedings
- Direct conference websites (ASCO.org, ESMO.org, hematology.org) are reliable but require web scraping
- Risk: Embargo policies may delay access to late-breaking abstracts

### 7. Specific Use Case for Biotech Catalyst Newsletter

**Primary Use Case: Detecting practice-changing clinical trial results presented at major oncology/hematology conferences**

- **Pre-conference catalyst identification:** Monitor Crossref/PubMed for newly registered conference abstract DOIs to identify companies with upcoming presentations before the meeting. This provides a 1-4 week lead time.
- **Embargo lift monitoring:** ASCO, ESMO, and ASH all publish abstracts at specific embargo lift times. Automated monitoring of these events can provide near-real-time alerts when pivotal trial results become public.
- **Late-breaking abstract tracking:** Late-breaking abstracts (LBA) are released during the meeting itself and often contain the most market-moving data (e.g., LBA8008 at ASCO 2025 on SCLC treatment).
- **Pipeline signal extraction:** Search Crossref by sponsor/institution names to track abstract publication patterns as early signals of clinical program activity.
- **Recommended implementation strategy:**
  1. Use PubMed E-utilities to search for conference abstracts by meeting name (e.g., "ASCO Annual Meeting", "ESMO Congress") and filter by date
  2. Supplement with Crossref API queries by DOI prefix or member ID (ASCO = member 233, verified 26,796 records)
  3. Set up RSS feed monitoring for JCO meeting abstracts (ascopubs.org/about/rss)
  4. Web-scrape ASH abstract search (apps.hematology.org) for structured trial result data
  5. Cross-reference with ClinicalTrials.gov NCT IDs mentioned in abstracts for trial status correlation

---

## SOURCE D: TrialReach / Antidote (Patient Recruitment Platform)

### 1. Source Name and URL

- **Name:** Antidote (formerly TrialReach)
- **URL:** https://www.antidote.me
- **Clinical Trial Search:** https://www.antidote.me/clinical-trial-search
- **Partner Program:** https://www.antidote.me/partners

**Important clarification:** antidoteresearch.com (API at https://antidoteresearch.com/api) is a **DIFFERENT, UNRELATED company** that provides drug information and nutrient depletion data. It is NOT connected to Antidote.me/TrialReach.

### 2. Access Method: **Web Scraping (limited) + Manual**

- **No public API available.** Antidote does not offer a developer API, public data feed, or RSS feed for clinical trial data.
- **Partner integrations** are available but require a formal partnership agreement. Antidote partners with 300+ organizations (patient advocacy groups, health nonprofits, patient technology companies, publishers) who can embed the Antidote Match search widget.
- **Antidote Match widget** is a free clinical trial search tool provided to partners that can be embedded on partner websites. However, this is a JavaScript widget — not an API or data feed.
- **Clinical trial search page** (antidote.me/clinical-trial-search) is interactive and requires user input (diagnosis, location) to display results. Not amenable to bulk data extraction.
- **Web scraping** of public-facing trial listings is technically possible but:
  - Results are personalized and query-dependent (no complete listing)
  - Terms of service likely prohibit scraping
  - Data is presentation-layer HTML with no structured data format
  - Anti-bot protections may be in place

### 3. Rate Limits and Pricing Tiers

| Access Method | Rate Limit | Pricing |
|---|---|---|
| Antidote Match widget (partner) | Undocumented (JavaScript widget) | Free for partners (requires partnership agreement) |
| Antidote clinical trial search (web) | Interactive use only | Free (consumer-facing) |
| Antidote Sponsors (pharma side) | Contact for details | Paid enterprise recruitment services |
| Web scraping (unofficial) | N/A — not authorized | Free (but ToS violation risk) |

### 4. Data Freshness

| Data Type | Freshness | Notes |
|---|---|---|
| Clinical trial listings | **Near real-time** | Antidote pulls from ClinicalTrials.gov and other registries; updates when source registries update |
| Patient recruitment activity | **Not publicly available** | Recruitment metrics (enrollment numbers, site activation) are shared only with sponsors |
| Trial status changes | **Dependent on source registry** | Antidote mirrors ClinicalTrials.gov data; no independent faster update cycle detected |

### 5. Data Format

| Access Method | Format |
|---|---|
| Antidote Match widget | JavaScript-rendered HTML (no structured data export) |
| Antidote clinical trial search | Interactive HTML (requires user input, no bulk access) |
| No API | N/A — no JSON, XML, RSS, or CSV output available |

### 6. Reliability Rating: **Low**

**Justification:**
- No public API or data feed exists for programmatic access
- Data shown on the website is query-dependent and interactive — no way to bulk-extract trial listings
- Recruitment activity data (the most valuable signal for early trial status changes) is not publicly available — it is shared only with paying sponsors
- Antidote's trial data ultimately comes from ClinicalTrials.gov and other registries, which are already accessible directly
- The company rebranded from TrialReach to Antidote, which is a minor concern for data source stability
- No RSS feeds, webhooks, or notification systems for trial status changes
- Web scraping is technically possible but likely violates Terms of Service and provides no advantage over direct ClinicalTrials.gov API access

### 7. Specific Use Case for Biotech Catalyst Newsletter

**Primary Use Case: Limited — patient recruitment activity as an early signal of trial status changes**

- **Original intent:** Use patient recruitment activity (e.g., trial listing changes, enrollment milestones) as early signals of trial status changes that could indicate upcoming catalyst events.
- **Reality:** Antidote does NOT expose recruitment metrics, enrollment numbers, or site activation data publicly. This data is only available to paying sponsors through Antidote's enterprise recruitment services.
- **What IS accessible:** Antidote's clinical trial search mirrors ClinicalTrials.gov data. There is no additional or faster data available through Antidote that is not already available directly from ClinicalTrials.gov API v2.
- **Verdict:** Antidote/TrialReach is NOT a viable independent data source for the ClinicalQuant newsletter. The trial listing data is a subset of what ClinicalTrials.gov already provides, and the valuable recruitment intelligence is locked behind enterprise contracts.

**Recommended Alternative Approach:**
1. Continue using ClinicalTrials.gov API v2 (already a verified Tier 1 source) for trial status monitoring
2. Monitor ClinicalTrials.gov for trial status changes (recruiting -> active/not recruiting -> completed) as catalyst signals
3. Supplement with FDA trial listing requirements (clinicaltrials.gov results reporting mandates) to track when companies are preparing to disclose results
4. Consider FDA AdCom meeting calendars and PDUFA date tracking as higher-value catalyst signals

---

## Summary Comparison

| Field | Source C (Conference Abstracts) | Source D (Antidote/TrialReach) |
|---|---|---|
| **Name/URL** | ASCO, ESMO, ASH via Crossref/PubMed | Antidote (antidote.me, formerly TrialReach) |
| **Access Method** | Free API (Crossref, PubMed) + RSS + Scraping | Web Scraping (limited, ToS risk) |
| **Rate Limits/Pricing** | 50 req/sec free (Crossref); 3-10 req/sec free (PubMed) | No API; partner-only widget; paid enterprise services |
| **Data Freshness** | Annual (conferences) + near real-time (Crossref) | Mirrors ClinicalTrials.gov — no advantage |
| **Data Format** | JSON (Crossref), XML/JSON (PubMed), RSS (ASCO) | HTML only — no structured output |
| **Reliability** | Medium-High | Low |
| **Use Case** | Pre-conference catalyst detection, embargo-lift alerts, pipeline signals | NOT viable — no unique data beyond ClinicalTrials.gov |

**Source C is RECOMMENDED for integration. Source D is NOT RECOMMENDED — ClinicalTrials.gov API v2 already provides superior trial data access.**
