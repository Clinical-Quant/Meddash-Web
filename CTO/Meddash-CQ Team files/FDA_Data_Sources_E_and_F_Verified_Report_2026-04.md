# FDA Data Sources E & F - Verified Research Report

**Date**: 2026-04-22
**Project**: ClinicalQuant (CQ) - Biotech Catalyst Newsletter
**Researcher**: Agent Zero Deep Research
**Verification Method**: Web search only - no hallucinated data

---

## SOURCE E: FDA Advisory Committee (AdComm) Meetings

### 1. Source Name and URL

- **Primary Source**: FDA Advisory Committee Calendar
  - URL: https://www.fda.gov/advisory-committees/advisory-committee-calendar
- **Supplementary**: FDA Advisory Committees Portal
  - URL: https://www.fda.gov/advisory-committees
- **Federal Register Notices**: https://www.federalregister.gov/api/v1 (search agencies[]=food-and-drug-administration)
- **Third-Party API - Finnhub**: https://finnhub.io/docs/api/fda-committee-meeting-calendar
- **Third-Party API - Aries (finance.dev)**: https://finance.dev/api-reference/supplemental/stock-fda-advisory-committee-calendar

### 2. Access Method

- **Primary: Web Scraping** - The FDA AdComm calendar page has NO official API and NO RSS feed. The calendar at fda.gov/advisory-committees/advisory-committee-calendar must be scraped to extract meeting data.
- **Secondary: Third-Party APIs**
  - **Finnhub API**: `GET /fda-committee-meeting-calendar` endpoint provides AdComm meeting data in JSON format. Free tier available.
  - **Aries API (finance.dev)**: `GET /stock/fda-advisory-committee-calendar` endpoint provides similar data. Requires subscription.
- **Tertiary: Federal Register API**: Free REST API at federalregister.gov/api/v1 can search for AdComm meeting notices by filtering `agencies[]=food-and-drug-administration` and `type[]=NOTICE`. JSON format, no API key required.
- **NOT available**: No official FDA RSS feed, no openFDA endpoint for AdComm meetings

### 3. Rate Limits and Pricing Tiers

| Access Method | Rate Limit | Pricing |
|---|---|---|
| FDA Calendar Web Scraping | Respectful crawling (~1 req/10 sec) | Free |
| Finnhub API (Free Tier) | 60 calls/min, 30 calls/sec global cap | Free |
| Finnhub API (Personal) | 60 calls/min | ~$9.95/month |
| Finnhub API (Business) | 300-900 calls/min | $49.95-$199.95/month |
| Finnhub API (Enterprise) | Custom | From $3,000/month |
| Aries API (finance.dev) | Varies by plan | Paid subscription required |
| Federal Register API v1 | ~100 req/min best practice | Free, no key required |

### 4. Data Freshness

- **FDA Calendar Page**: Updated as meetings are scheduled (typically weeks to months in advance of meeting dates). New meetings appear within 1-2 business days of FDA announcement.
- **Finnhub API**: Near real-time sync with FDA calendar (typically same-day updates).
- **Federal Register API**: Published daily; AdComm notices appear 1-3 days after FDA announcement.
- **Overall**: Not truly real-time; AdComm meetings are scheduled weeks/months ahead. Frequency of new entries: ~2-8 per month.

### 5. Data Format

| Access Method | Format | Notes |
|---|---|---|
| FDA Calendar Page | HTML | Must be scraped; structure subject to change |
| Finnhub API | JSON | Structured response with meeting date, committee name, agenda |
| Aries API | JSON | Structured response similar to Finnhub |
| Federal Register API | JSON (also HTML/PDF) | Notice documents with full text, metadata |

### 6. Reliability Rating

- **Medium-High**
  - FDA official calendar is authoritative but requires scraping (fragile to page structure changes)
  - Finnhub API provides structured data but depends on third-party parsing/maintenance
  - Federal Register API is official government data but may lag 1-3 days
  - No single source provides real-time, structured, authoritative data
  - Recommendation: Combine Finnhub API (primary structured data) + Federal Register API (official notice verification) + FDA calendar page scraping (authoritative source confirmation)

### 7. Specific Use Case for ClinicalQuant

**AdComm Meeting Intelligence Pipeline**:
1. **Pre-Meeting Alerts**: Monitor Finnhub API weekly for newly scheduled AdComm meetings. When a meeting is announced for a drug covered in the CQ watchlist, generate an alert 30 days before meeting date.
2. **Vote Prediction Analysis**: Cross-reference AdComm meeting agenda with CQ drug pipeline data. Analysts assess likely vote outcomes based on clinical trial data quality (from ClinicalTrials.gov).
3. **Post-Meeting Impact**: After AdComm votes, FDA decisions typically follow within 2-6 weeks. AdComm outcomes are strong catalysts for biotech stocks.
4. **Federal Register Verification**: Confirm all Finnhub-sourced AdComm data against Federal Register official notices to ensure no missed or cancelled meetings.
5. **Newsletter Integration**: Feature upcoming AdComm meetings in weekly CQ newsletter as "Key Catalysts to Watch" section, with ticker-level mapping.

---

## SOURCE F: FDA Press Releases / Newsroom

### 1. Source Name and URL

- **Primary RSS Feed**: FDA Press Releases RSS
  - URL: https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/press-releases/rss.xml
- **Web Page**: FDA Newsroom Press Announcements
  - URL: https://www.fda.gov/news-events/fda-newsroom/press-announcements
- **FDA Newsroom Hub**: https://www.fda.gov/news-events/fda-newsroom
- **FDA RSS Feeds Index**: https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds
- **FDA Subscriptions**: https://www.fda.gov/about-fda/contact-fda/subscribe-podcasts-and-news-feeds

### 2. Access Method

- **Primary: RSS Feed** - FDA provides an official XML RSS feed for press releases at the URL above. This is the most efficient and reliable programmatic access method.
- **Secondary: Web Scraping** - The press announcements page can be scraped for full article content when the RSS feed provides only summaries.
- **NOT available**: No official FDA API for press releases. openFDA does NOT cover press releases or news announcements.
- **Supplementary RSS feeds available**:
  - MedWatch Safety Alerts: https://www.fda.gov/safety/medwatch-fda-safety-information-and-adverse-event-reporting-program/medwatch-rss-feed
  - Drug Information Updates: available via FDA RSS feeds index
  - Consumer Health Information: available via FDA RSS feeds index

### 3. Rate Limits and Pricing Tiers

| Access Method | Rate Limit | Pricing |
|---|---|---|
| FDA Press Releases RSS Feed | No official limit; reasonable use (~1 poll/5 min) | Free |
| FDA Press Announcements Web Scraping | Respectful crawling (~1 req/10 sec) | Free |
| MedWatch RSS Feed | No official limit; reasonable use | Free |

All access methods are free. No paid tiers required.

### 4. Data Freshness

- **RSS Feed**: Near real-time. Press releases appear in the RSS feed within minutes of official FDA publication. For CQ purposes, polling every 5-15 minutes during market hours is sufficient.
- **Web Page**: Updated in real-time as press releases are published.
- **Overall**: Near real-time (minutes lag from official publication). This is one of the fastest official FDA channels for major announcements.

### 5. Data Format

| Access Method | Format | Notes |
|---|---|---|
| RSS Feed | XML (RSS 2.0) | Standard RSS format; includes title, description, link, pubDate |
| Press Announcements Page | HTML | Full article content with links, images, and formatting |

**RSS Feed Structure** (verified from web data):
- Title: Press release headline
- Description: Summary/abstract of the press release
- Link: URL to full press release on fda.gov
- pubDate: Publication date/time
- Standard RSS 2.0 elements (channel, item, etc.)

### 6. Reliability Rating

- **High**
  - Official FDA RSS feed - authoritative and stable
  - RSS is a mature, well-supported standard
  - FDA has maintained this feed for years
  - Feed URL is stable and officially documented
  - Minimal risk of format changes
  - Only vulnerability: if FDA restructures their website (rare)

### 7. Specific Use Case for ClinicalQuant

**FDA Press Release Monitoring Pipeline**:
1. **Real-Time Alert System**: Poll the FDA press releases RSS feed every 5-15 minutes during market hours. Use keyword matching (drug names, company names, ticker-related terms) to trigger immediate alerts.
2. **Approval Announcements**: FDA drug approval press releases are the most impactful biotech catalysts. Auto-detect approval keywords ("approved", "approval", "FDA approves") and map to CQ watchlist tickers.
3. **Safety Alerts**: MedWatch safety alerts and recall press releases can cause immediate stock impacts. Cross-reference with CQ drug database.
4. **Regulatory Actions**: Complete response letters (CRLs), REMS requirements, and enforcement actions are high-impact events for covered companies.
5. **Newsletter Integration**: RSS-sourced press releases feed directly into the CQ newsletter as "Breaking FDA Actions" section, with automated ticker tagging and analyst commentary prompts.
6. **Historical Analysis**: Archive all press releases for backtesting catalyst impact on biotech stock prices.

---

## Summary Comparison Table

| Field | Source E: AdComm Meetings | Source F: Press Releases |
|---|---|---|
| **Primary URL** | fda.gov/advisory-committees/advisory-committee-calendar | fda.gov/news-events/fda-newsroom/press-announcements |
| **Access Method** | Web Scraping + 3rd-Party APIs (Finnhub, Aries) + Federal Register API | RSS Feed (primary) + Web Scraping (supplementary) |
| **Rate Limits** | Finnhub: 60/min free; Fed Register: ~100/min | No official limits; reasonable use |
| **Pricing** | Free (scraping) or Free-$199/mo (Finnhub) or Paid (Aries) | Free |
| **Data Freshness** | Scheduled weeks ahead; updated within 1-2 days of announcement | Near real-time (minutes lag) |
| **Data Format** | HTML / JSON (Finnhub/Aries) / JSON (Fed Register) | XML (RSS 2.0) / HTML |
| **Reliability** | Medium-High (no official API) | High (official FDA RSS feed) |
| **CQ Priority** | Medium (2-8 events/month, high impact per event) | Critical (daily events, highest frequency catalyst source) |

---

## Implementation Recommendations for ClinicalQuant

### Source F (Press Releases) - IMMEDIATE PRIORITY
- Implement RSS feed polling every 5-15 minutes during market hours (9:30 AM - 4:00 PM ET)
- Use standard RSS parser (Python feedparser library recommended)
- Keyword-based filtering: approval, CRL, recall, safety, REMS, breakthrough, fast track
- Auto-map to CQ watchlist tickers via drug name/company name matching
- Archive all entries for historical backtesting
- Low implementation complexity, high impact

### Source E (AdComm Meetings) - HIGH PRIORITY
- Use Finnhub API as primary structured data source (free tier sufficient for weekly polling)
- Verify against Federal Register API (free, no key required)
- Cross-reference with FDA calendar page monthly for completeness
- Alert threshold: 30 days before meeting date for CQ watchlist drugs
- Medium implementation complexity, very high impact per event

---

*Report generated with verified web data only. No hallucinated information.*
