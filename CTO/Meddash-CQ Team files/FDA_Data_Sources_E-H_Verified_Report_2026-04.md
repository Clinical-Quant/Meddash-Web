# FDA Data Sources E-H — Verified Research Report
**Date:** 2026-04-22
**Project:** ClinicalQuant Biotech Catalyst Newsletter
**Status:** Web-verified, no hallucination

---

## SOURCE E: FDA Advisory Committee (AdComm) Meetings

### 1. Source Name and URL
- FDA Advisory Committee Calendar: https://www.fda.gov/advisory-committees/advisory-committee-calendar
- FDA Advisory Committees Portal: https://www.fda.gov/advisory-committees
- Third-Party API (Finnhub): https://finnhub.io/docs/api/fda-committee-meeting-calendar
- Third-Party API (Aries/finance.dev): https://finance.dev/api-reference/supplemental/stock-fda-advisory-committee-calendar
- Federal Register API: https://www.federalregister.gov/api/v1

### 2. Access Method
- **Primary: Web Scraping** — NO official FDA API or RSS feed for AdComm meetings
- **Secondary: Third-Party APIs** — Finnhub (GET /fda-committee-meeting-calendar, JSON, free tier) and Aries API (paid)
- **Tertiary: Federal Register API** — Free REST API, filter agencies[]=food-and-drug-administration + type[]=NOTICE, no key required
- **NOT available**: No FDA RSS feed, no openFDA endpoint for AdComm data

### 3. Rate Limits and Pricing
| Method | Rate Limit | Price |
|---|---|---|
| FDA Calendar Scraping | ~1 req/10 sec (respectful) | Free |
| Finnhub Free Tier | 60 calls/min, 30/sec cap | Free |
| Finnhub Personal | 60 calls/min | ~$9.95/mo |
| Finnhub Business | 300-900 calls/min | $49.95-$199.95/mo |
| Aries API | Varies | Paid subscription |
| Federal Register API v1 | ~100 req/min | Free, no key |

### 4. Data Freshness
- FDA Calendar: Updated within 1-2 business days of announcement; meetings scheduled weeks/months in advance
- Finnhub: Same-day sync with FDA calendar
- Federal Register: 1-3 day lag after FDA announcement
- New entries: ~2-8 per month

### 5. Data Format
- FDA Calendar: HTML (scraping required)
- Finnhub: JSON (meeting date, committee name, agenda)
- Aries: JSON (similar to Finnhub)
- Federal Register: JSON (+ HTML/PDF)

### 6. Reliability Rating: Medium-High
- No single authoritative structured source exists
- Finnhub is reliable but third-party-dependent
- Federal Register is official but lags 1-3 days
- **Recommendation**: Combine Finnhub (primary structured) + Federal Register (verification) + FDA scraping (confirmation)

### 7. ClinicalQuant Use Case
- Weekly Finnhub API polling for new AdComm meetings on CQ watchlist drugs
- 30-day pre-meeting alerts mapped to tickers
- Post-meeting impact analysis (FDA decisions follow 2-6 weeks after AdComm votes)
- Federal Register verification to catch missed/cancelled meetings
- Newsletter "Key Catalysts to Watch" section

---

## SOURCE F: FDA Press Releases / Newsroom

### 1. Source Name and URL
- RSS Feed: https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/press-releases/rss.xml
- Web Page: https://www.fda.gov/news-events/fda-newsroom/press-announcements
- RSS Feeds Index: https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds
- Subscriptions: https://www.fda.gov/about-fda/contact-fda/subscribe-podcasts-and-news-feeds
- Supplementary: MedWatch Safety Alerts RSS

### 2. Access Method
- **Primary: RSS Feed** — Official FDA XML RSS feed (most efficient programmatic access)
- **Secondary: Web Scraping** — For full article content when RSS provides only summaries
- **NOT available**: No FDA API for press releases; openFDA does NOT cover press releases
- **Supplementary RSS feeds**: MedWatch Safety Alerts, Drug Information Updates, Consumer Health Information

### 3. Rate Limits and Pricing
| Method | Rate Limit | Price |
|---|---|---|
| Press Releases RSS | No official limit; ~1 poll/5 min | Free |
| Web Scraping | ~1 req/10 sec | Free |
| MedWatch RSS | Reasonable use | Free |

All access methods are entirely **free**.

### 4. Data Freshness
- **Near real-time** — Press releases appear in RSS within minutes of FDA publication
- Sufficient polling: every 5-15 minutes during market hours

### 5. Data Format
- RSS Feed: XML (RSS 2.0) — title, description, link, pubDate
- Web Page: HTML (full article content)

### 6. Reliability Rating: High
- Official FDA RSS feed — authoritative and stable
- RSS 2.0 is a mature, well-supported standard
- FDA has maintained this feed for years
- Minimal risk of format changes or feed disruption

### 7. ClinicalQuant Use Case
- **Real-time alert system**: Poll RSS every 5-15 min during market hours; keyword-match (approval, CRL, recall, safety, REMS, breakthrough, fast track) against CQ watchlist
- **Approval detection**: Auto-flag FDA drug approvals and map to tickers
- **Safety alerts**: MedWatch cross-reference for immediate stock impact
- **Newsletter integration**: "Breaking FDA Actions" section with automated ticker tagging
- **Historical archive**: Backtesting catalyst impact on biotech stock prices

---

## SOURCE G: FDA Drug Safety Communications

### 1. Source Name and URL
- **Name:** FDA Drug Safety Communications
- **Main Page:** https://www.fda.gov/drugs/drug-safety-and-availability/drug-safety-communications
- **MedWatch Safety Alerts RSS:** https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/medwatch/rss.xml
- **Drug Safety Podcasts RSS:** https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/drug-safety-podcast/rss.xml
- **What's New: Drugs RSS:** https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/drugs/rss.xml
- **Email Alerts:** https://www.fda.gov/safety/medwatch-fda-safety-information-and-adverse-event-reporting-program/subscribe-medwatch-safety-alerts
- **Related API:** openFDA Drug Enforcement: https://api.fda.gov/drug/enforcement (covers recalls only, NOT DSCs specifically)

### 2. Access Method
- **Primary: RSS Feeds** — 3 feeds: MedWatch Safety Alerts (broadest, includes DSCs), Drug Safety Podcasts (audio of DSCs), What's New: Drugs
- **Secondary: Web Scraping** — DSC landing page has structured HTML with titles/dates
- **Tertiary: Email Alerts** — MedWatch push email subscription
- **Related: openFDA Drug Enforcement API** — Covers drug recalls but NOT safety communications directly

### 3. Rate Limits and Pricing
| Method | Rate Limits | Pricing |
|--------|------------|--------|
| RSS Feeds | No limits (standard RSS polling) | Free |
| Web Scraping | Respect robots.txt; ~1 req/10-30sec | Free |
| Email Alerts | No limits | Free |
| openFDA Enforcement API | With key: 240 req/min, 120K/day; Without key: 240 req/min, 1K/day/IP | Free (key at open.fda.gov/api-registration/) |

### 4. Data Freshness
- **Near real-time (hours)** — MedWatch RSS updated within hours of FDA safety communication publication
- Drug Safety Podcasts same-day
- Web page real-time

### 5. Data Format
- RSS Feeds: XML (RSS 2.0)
- DSC Web Page: HTML
- openFDA Drug Enforcement API: JSON
- Email Alerts: HTML email

### 6. Reliability Rating: High
- Official FDA source, actively maintained (verified 2024-2026 content)
- MedWatch is FDA's primary safety communication channel
- Standardized DSC format

### 7. ClinicalQuant Use Case
- **HIGH-PRIORITY catalyst source.** Drug Safety Communications are among the most impactful biotech catalysts:
  - Boxed warnings / label changes -> direct commercial impact
  - REMS actions -> restrict market access
  - Safety signals -> can crater stock prices
  - Precede actual market withdrawals
- **Implementation:** Poll MedWatch RSS every 15 min (P0), scrape DSC page daily (P1), cross-reference drug names to tickers via Drugs@FDA/NDC mapping, auto-generate DSC alerts for portfolio tickers

---

## SOURCE H: FDA CDER Direct Databases

### 1. Source Name and URL
- **Name:** FDA CDER Direct (now FDA Direct)
- **Portal:** https://direct.fda.gov/
- **Login:** https://direct.fda.gov/apex/f?p=100:LOGIN_DESKTOP
- **NOTE:** The commonly referenced URL (https://www.fda.gov/drugs/drug-approvals-and-databases/cder-direct-database) does NOT exist as a public data source

### 2. Access Method
**N/A — Not a public data source.** CDER Direct is an industry SUBMISSION portal for pharma companies to submit registration/listing data to FDA. Requires authenticated FDA account. No API. No public data access. No scraping.

### 3. Rate Limits and Pricing
**N/A** — Not a public data source.

### 4. Data Freshness
**N/A** — Submission tool, not a data source.

### 5. Data Format
**N/A** — Inbound submission format is SPL XML only.

### 6. Reliability Rating
**N/A** — Not applicable as a data source for ClinicalQuant.

### 7. ClinicalQuant Use Case
**SKIP entirely.** CDER Direct/FDA Direct contains no publicly queryable data. However, data submitted through it flows into separate public CDER databases that ARE relevant — and most are already in our pipeline:

| CDER Database | Access | Already in Pipeline? |
|--------------|--------|---------------------|
| Drugs@FDA | openFDA API + bulk ZIP | YES |
| Orange Book | Bulk ZIP | YES |
| NDC Directory | openFDA API | YES |
| Drug Shortages | openFDA /drug/shortage | **Partially — GAP** |
| Adverse Events | openFDA /drug/event | YES |
| Drug Recalls | openFDA /drug/enforcement | YES |

**Action Item:** Evaluate openFDA /drug/shortage endpoint as a pipeline addition — it's the only CDER database gap.

---

## Consolidated Summary

| Field | Source E (AdComm) | Source F (Press Releases) | Source G (Drug Safety) | Source H (CDER Direct) |
|-------|-------------------|--------------------------|------------------------|----------------------|
| Access | Web Scraping + 3rd Party API | RSS Feed | RSS + Scraping + API | N/A (submission portal) |
| Rate Limits | Varies (free to $200/mo) | Free, unlimited | Free, unlimited | N/A |
| Freshness | 1-3 days | Near real-time | Near real-time (hours) | N/A |
| Format | HTML, JSON | XML (RSS 2.0) | XML, HTML, JSON | N/A |
| Reliability | Medium-High | High | High | N/A |
| CQ Priority | HIGH | IMMEDIATE | HIGH (P0) | SKIP |

## Implementation Priority
1. **Source F (Press Releases) — IMMEDIATE**: Free RSS feed, low complexity, highest-frequency catalyst source. Use Python feedparser.
2. **Source G (Drug Safety Comms) — HIGH (P0)**: Free MedWatch RSS, high stock impact (boxed warnings, REMS). Poll every 15 min.
3. **Source E (AdComm Meetings) — HIGH**: Finnhub free tier + Federal Register API. Weekly polling sufficient. Very high impact per event.
4. **Source H (CDER Direct) — SKIP**: Not a data source. Evaluate openFDA /drug/shortage as gap fill.
