# Commercial Clinical Trial Data Sources Research Report

**Date**: 2026-04-21  
**Prepared for**: ClinicalQuant Newsletter (Biotech Catalyst Intelligence)  
**Author**: Agent Zero Deep Research  
**Classification**: PAID/COMMERCIAL Sources Only  

---

## Executive Summary

This report evaluates 10 commercial clinical trial intelligence platforms for their suitability as paid data sources for the ClinicalQuant biotech catalyst newsletter. Key findings:

- **Most platforms operate on enterprise licensing** ($10K-$100K+/year) with no public pricing
- **API access is available** from Citeline, Cortellis (Clarivate), GlobalData, AdisInsight (Springer Nature), and IQVIA
- **Biomedtracker is the most directly relevant** for biotech catalyst/event tracking (FDA PDUFA dates, trial readouts, approval decisions)
- **PharmaSpect does not exist as a standalone platform** - this appears to be an error in the source list
- **TrialScope is a Citeline regulatory compliance product**, not a clinical trial intelligence source
- **All platforms require contact-sales pricing**, typical of enterprise B2B SaaS in life sciences

---

## Source 1: Citeline / TrialTrove

| Field | Detail |
|-------|--------|
| **Source Name & URL** | Citeline Trialtrove — https://www.citeline.com/en/products-services/clinical/trialtrove |
| **Access Method** | Paid API (Citeline Informatics Solutions), Dashboard, Bulk Data Export |
| **Rate Limits & Pricing** | Enterprise licensing only (no public pricing). Estimated $30K-$100K+/year for full Trialtrove access. API access requires separate Informatics Solutions agreement. |
| **Data Freshness** | Real-time / daily — Powered by 60,000+ trusted sources with continuous curation. Trialtrove+ (launched Feb 2025) adds enhanced real-time analytics. |
| **Data Format** | API (JSON), Dashboard (web), Bulk export (CSV/structured data) |
| **Reliability** | **High** — Industry gold standard for clinical trial intelligence. Curated data from 60K+ sources. Used by major pharma companies worldwide. |
| **Use Case for CQ** | **PRIMARY CANDIDATE** — Trialtrove covers trial design, enrollment timelines, patient populations, endpoints, outcomes, geographic trends. API enables automated pipeline integration for catalyst detection (trial status changes, enrollment milestones, endpoint results). Trialtrove+ adds benchmarking and trend analytics. Citeline Informatics API ecosystem includes Drug Development API (from Pharmaprojects), Events API (from Biomedtracker), and Clinical Trial API. |

### Key Notes
- Trialtrove captured 10,503 Phase I–III trials initiated in 2024 (9.4% YoY growth)
- API ecosystem: https://www.citeline.com/en/products-services/custom-solutions/informatics-solutions
- Trialtrove+ and Sitetrove+ launched Feb 2025 with enhanced features
- Annual Clinical Trials Roundup reports provide free summary data

---

## Source 2: GlobalData Clinical Trials Database

| Field | Detail |
|-------|--------|
| **Source Name & URL** | GlobalData Pharma Clinical Trials Database — https://www.globaldata.com/product/pharma-clinical-trials-database/ |
| **Access Method** | Paid API, FTP, Cloud delivery; Dashboard access via Pharma Intelligence Centre |
| **Rate Limits & Pricing** | Enterprise licensing (no public pricing). Stanford & academic institutions license via Jisc. Vendr reports enterprise pricing varies significantly by module. Estimated $15K-$50K/year for clinical trials module. |
| **Data Freshness** | Daily updates with continuous curation from government registries, non-government registries, research publications, and conferences |
| **Data Format** | API (JSON), FTP (bulk), Cloud delivery, Dashboard (web) |
| **Reliability** | **High** — Comprehensive global coverage from multiple registry sources. Used by major pharma and academic institutions. |
| **Use Case for CQ** | **SECONDARY CANDIDATE** — GlobalData provides broad clinical trial coverage supplemented by market analysis, drug pricing, and competitive intelligence. The API/FTP/Cloud delivery options enable flexible data pipeline integration. Particularly useful for cross-referencing trial data with market context. The marketplace dataset (https://www.globaldata.com/marketplace/dataset/pharma-clinical-trials/) offers a potential lower-cost entry point for specific data slices. |

### Key Notes
- Academic access available via Jisc subscriptions (UK institutions)
- Marketplace offers individual dataset purchases (may be more accessible for startup budget)
- API documentation available via GlobalData developer portal
- Multiple delivery methods (API, FTP, Cloud) suit different integration approaches

---

## Source 3: PharmaIntelligence (Informa)

| Field | Detail |
|-------|--------|
| **Source Name & URL** | Informa Pharma Intelligence — https://pages.pharmaintelligence.informa.com/ (Note: now part of Citeline brand after 2022 rebrand) |
| **Access Method** | Paid API, Dashboard, Data Feeds |
| **Rate Limits & Pricing** | Enterprise licensing only (no public pricing). API brochure available for download at https://pages.pharmaintelligence.informa.com/apis-brochure-download. Estimated $20K-$80K+/year depending on modules selected. |
| **Data Freshness** | Real-time / daily — Continuous curation with real-time API updates available |
| **Data Format** | API (JSON), Dashboard (web), Data Feeds (structured export) |
| **Reliability** | **High** — Decades of pharmaceutical intelligence curation. Now operating under Citeline brand with enhanced AI capabilities. |
| **Use Case for CQ** | **REDUNDANT WITH CITELINE** — PharmaIntelligence was rebranded as Citeline in 2022. The products (Trialtrove, Sitetrove, Pharmaprojects, Biomedtracker) are now sold under the Citeline brand. The API solutions formerly marketed as "Informa Pharma Intelligence APIs" are now Citeline Informatics Solutions. This source should be treated as part of Citeline, not a separate vendor. |

### Key Notes
- **CRITICAL**: PharmaIntelligence was rebranded to Citeline in 2022. All products now under Citeline umbrella.
- API brochure still accessible at the old domain but products are Citeline-branded
- If approaching as a buyer, go directly to Citeline.com for current product offerings
- Separate entity "Pharma Intelligence" (pharmaintelligence.org) is a scientific publisher, NOT the same as Informa Pharma Intelligence

---

## Source 4: Evaluate Pharma

| Field | Detail |
|-------|--------|
| **Source Name & URL** | Evaluate (formerly EvaluatePharma) — https://www.evaluate.com/ |
| **Access Method** | Dashboard, Data Feeds (off-the-shelf or custom); No public API documented |
| **Rate Limits & Pricing** | Enterprise licensing only (no public pricing). Data Feeds available as add-on or standalone. Reddit discussions suggest individual subscriptions may run $10K-$30K+/year for basic access. |
| **Data Freshness** | Daily / weekly — Data feeds provide seamless flow of forecast, trial, and key event data into internal systems |
| **Data Format** | Data Feeds (structured export), Dashboard (web). No documented public API format. |
| **Reliability** | **High** — Evaluate is a trusted source for consensus forecasts, sales projections, and pharma commercial intelligence. Used by major pharma BD&L and strategy teams. |
| **Use Case for CQ** | **NICHE CANDIDATE** — Evaluate's strength is in commercial forecasting and consensus sales estimates rather than real-time clinical trial intelligence. Their data feeds (https://www.evaluate.com/solutions/data-feeds/) could complement free trial data with commercial context (sales forecasts, pipeline valuations). However, for the core CQ use case of catalyst event tracking, Evaluate is less directly relevant than Biomedtracker or Citeline's trial data. Best used as a supplementary source for market impact estimation. |

### Key Notes
- Biomedtracker is now part of Evaluate/Citeline (https://www.evaluate.com/solutions/biomedtracker/)
- Data Feeds: off-the-shelf or custom feeds for forecast, trial, and key event data
- Focus on consensus forecasts and commercial intelligence rather than trial-level detail
- Also offers Meddevicetracker for medical device catalyst events

---

## Source 5: Cortellis / Cortellis Clinical Trials Intelligence (Clarivate)

| Field | Detail |
|-------|--------|
| **Source Name & URL** | Cortellis Clinical Trials Intelligence (Clarivate) — https://clarivate.com/life-sciences-healthcare/research-development/discovery-development/cortellis-clinical-trials-intelligence/ |
| **Access Method** | Paid API (Cortellis Labs / Developer Portal), Dashboard, Bulk Data Export |
| **Rate Limits & Pricing** | Enterprise licensing only (no public pricing). Cortellis Labs offers sandbox API access for evaluation. Developer portal at https://developer.clarivate.com/apis/cortellis-api-collection. Estimated $20K-$75K+/year per module. |
| **Data Freshness** | Daily — Curated from 24 major trial registries, press releases (1987-present), conference abstracts (2007-present) |
| **Data Format** | API (JSON/XML via Cortellis Labs), Dashboard (web), Data Feeds |
| **Reliability** | **High** — Manually curated data from 24 registries with historical depth (press releases from 1987). Clarivate's Cortellis is widely used by pharma R&D teams. AI assistant and Claude MCP integration launched 2025. |
| **Use Case for CQ** | **PRIMARY CANDIDATE** — Cortellis Clinical Trials Intelligence offers the most API-friendly access among major platforms. The Cortellis Labs sandbox (https://cortellislabs.com/api/clinical/) allows evaluation before committing to enterprise licensing. The Clinical API provides curated trial data including endpoints, eligibility criteria, and reported outcomes — directly relevant for catalyst detection. The unified Cortellis suite also includes Drugs, Deals, Regulatory, and Patent intelligence for comprehensive pipeline tracking. |

### Key Notes
- Cortellis Labs sandbox: https://cortellislabs.com/api/clinical/ — requires professional email registration
- Developer portal: https://developer.clarivate.com/apis/cortellis-api-collection
- AI assistant launched 2025 with Claude MCP integration
- Potential divestiture of Clarivate's life sciences division reported in 2026 — could affect product roadmap
- Clinical API covers drugs, biologics, devices, and biomarkers from 24 registries
- Historical press release data from 1987 and conference abstracts from 2007 provide deep context

---

## Source 6: AdisInsight (Springer Nature)

| Field | Detail |
|-------|--------|
| **Source Name & URL** | AdisInsight (Springer Nature) — https://adisinsight.springer.com/ |
| **Access Method** | Paid API, Dashboard, Institutional Licensing |
| **Rate Limits & Pricing** | Institutional licensing (no public per-seat pricing). API access available at https://adisinsight.springer.com/apis. Springer Nature offers flexible licensing models (https://www.springernature.com/gp/rd/pricing/databases). Academic institutions can license via library subscriptions. Estimated $10K-$40K/year for commercial access. |
| **Data Freshness** | Daily — Continuously updated with curated scientific data on drugs, trials, deals, patents, and safety |
| **Data Format** | API (JSON — Drugs API, Trials API), Dashboard (web), PDF exports, Institutional database access |
| **Reliability** | **High** — Springer Nature's Adis has 50+ years of drug-focused publishing expertise. Scientifically rigorous, curated content with clear referencing and links to original sources across publishers. |
| **Use Case for CQ** | **MODERATE CANDIDATE** — AdisInsight's API provides structured access to drug development programs and clinical trials. The Trials API delivers trial profiles with progress tracking from planning to completion, including key efficacy and safety results — directly useful for tracking trial milestones. The Drugs API covers the full drug lifecycle. However, AdisInsight's primary focus is scientific R&D rather than market-moving catalyst events, making it better suited as a supplementary source for trial detail enrichment rather than primary catalyst detection. |

### Key Notes
- API documentation: https://adisinsight.springer.com/apis
- Two main APIs: Drugs API (drug development profiles) and Trials API (clinical trial profiles)
- Free preview version available for initial exploration
- Licensing page: https://www.springernature.com/gp/rd/pricing/databases
- API subscription models detailed at https://dev.springernature.com/subscription/
- Strong scientific rigor — authored summaries rather than just registry aggregation

---

## Source 7: Biomedtracker (Citeline)

| Field | Detail |
|-------|--------|
| **Source Name & URL** | Biomedtracker (Citeline) — https://www.biomedtracker.com/ and https://www.evaluate.com/solutions/biomedtracker/ |
| **Access Method** | Dashboard, Reports, Alerts; API available via Citeline Informatics Solutions (Events API) |
| **Rate Limits & Pricing** | Enterprise/subscription licensing. Individual product access likely $8K-$25K/year. Additional subscriptions required for AdComm coverage and some report types. Categorized as premium but more accessible than full Trialtrove. |
| **Data Freshness** | Real-time / daily — Tracks market-moving events, catalysts, PDUFA dates, clinical trial readouts, approval decisions. Quarterly Outlook reports plus continuous event monitoring. |
| **Data Format** | Dashboard (web), PDF reports, API (via Citeline Informatics Events API), Alerts (email/web) |
| **Reliability** | **High** — Specifically designed for biotech catalyst tracking. Integrates with Pharmapremia (Likelihood of Approval scoring). Expert analyst coverage of FDA Advisory Committees, PDUFA dates, and clinical readouts. |
| **Use Case for CQ** | **BEST DIRECT FIT** — Biomedtracker is the most directly relevant commercial source for ClinicalQuant's biotech catalyst newsletter. It tracks exactly what CQ needs: FDA PDUFA dates, clinical trial readouts, approval decisions, AdComm outcomes, and deal announcements. The Likelihood of Approval (LOA) scoring from Pharmapremia adds quantitative prediction to catalyst analysis. Quarterly Outlook reports provide forward-looking catalyst calendars. The Events API enables automated pipeline integration. This is the single most relevant commercial data source for CQ's use case. |

### Key Notes
- Quarterly Outlook Reports: Key Industry Drugs reports with catalyst calendars
- Key Potential Drug Launches in 2025/2026 reports
- Pharmapremia LOA (Likelihood of Approval) scoring integrated
- AdComm coverage available (additional subscription)
- Now part of both Citeline AND Evaluate brands
- Events API available via Citeline Informatics for automated catalyst detection
- Direct competitor to free sources like FDA Tracker (fdatracker.com) and BiopharmWatch

---

## Source 8: PharmaSpect / TrialScope

| Field | Detail |
|-------|--------|
| **Source Name & URL** | TrialScope Intelligence (Citeline) — https://www.citeline.com/en/products-services/regulatory-and-compliance/trialscope-intelligence/ |
| **Access Method** | Dashboard (TrialScope Disclose for compliance; TrialScope Intelligence for disclosure intelligence) |
| **Rate Limits & Pricing** | Enterprise licensing only (no public pricing). Estimated $10K-$30K/year. |
| **Data Freshness** | Daily — Continuous monitoring of clinical trial disclosure requirements and compliance status |
| **Data Format** | Dashboard (web), Alerts (email), Professional analyst support (Ask-the-Analyst service) |
| **Reliability** | **Medium-High** — Industry's most widely used platform for clinical trial disclosure management. However, it is focused on REGULATORY COMPLIANCE, not clinical trial intelligence. |
| **Use Case for CQ** | **LOW RELEVANCE** — TrialScope is designed for clinical trial disclosure compliance (making trial results public per FDA/EMA requirements), NOT for tracking clinical trial milestones or catalyst events. It is a regulatory compliance tool for pharma sponsors. **PharmaSpect does not appear to exist as a standalone platform** — extensive web searches found no commercial clinical trial intelligence product by this name. A "TrialScope AI" streamlit app exists (trialscope-ai.streamlit.app) but appears to be an experimental/hobby project, not a commercial enterprise platform. |

### Key Notes
- **PharmaSpect**: No evidence of existence as a commercial platform. Likely confusion with another product or a defunct/renamed service.
- **TrialScope**: Now a Citeline product focused on regulatory disclosure compliance, not trial intelligence
- TrialScope EXTRA 2025 event covered transparency trends and benchmarking
- TrialScope Intelligence provides: country-specific disclosure requirements, alerts for changing requirements, Ask-the-Analyst professional support
- **Not recommended for CQ catalyst tracking use case**

---

## Source 9: Medtrack (IQVIA)

| Field | Detail |
|-------|--------|
| **Source Name & URL** | IQVIA (includes Medtrack lineage) — https://www.iqvia.com/ | Developer Hub: https://developer.iqvia.com/ |
| **Access Method** | Dashboard, API (IQVIA Developer Hub), Data Export, Custom Data Feeds, Consulting Services |
| **Rate Limits & Pricing** | Enterprise licensing only (no public pricing). IQVIA pricing is among the highest in the industry — estimated $30K-$150K+/year depending on modules. ITQlick reports base plans offer core functionalities with premium plans including advanced analytics, predictive modeling, and dedicated support. |
| **Data Freshness** | Daily — IQVIA processes 100M+ transactions daily across their data ecosystem. Clinical trial data updated continuously from their proprietary data collection infrastructure. |
| **Data Format** | API (via IQVIA Developer Hub), Dashboard (web), Data Export (multiple formats), Custom Feeds, FTP delivery for bulk data. Health Data Research Platform available for research institutions. |
| **Reliability** | **High** — IQVIA is the largest pharmaceutical data company globally. Medtrack (now integrated into IQVIA's broader data ecosystem) has decades of pharmaceutical intelligence history. The IQVIA Institute publishes widely-cited industry reports. |
| **Use Case for CQ** | **NICHE CANDIDATE** — IQVIA's data is comprehensive but primarily oriented toward commercial analytics, market sizing, and real-world evidence rather than real-time catalyst event tracking. The IQVIA Developer Hub (https://developer.iqvia.com/) offers API access but requires enterprise engagement. The IQVIA Institute publishes free reports (Global Use of Medicines, R&D Trends) that provide valuable industry context. For CQ's specific use case of biotech catalyst tracking, IQVIA is overkill and too expensive relative to more focused alternatives like Biomedtracker. Best used for accessing IQVIA Institute free reports for market context. |

### Key Notes
- Medtrack brand has been absorbed into IQVIA's broader product suite
- IQVIA Developer Hub: https://developer.iqvia.com/ — requires enterprise architecture engagement
- IQVIA Institute free reports: https://www.iqvia.com/insights/the-iqvia-institute/reports-and-publications
- Health Data Access fact sheet: https://www.iqvia.com/-/media/iqvia/pdfs/library/fact-sheets/iqvia-health-data-access.pdf
- UK G-Cloud listing for Health Data Research Platform indicates institutional data access products
- Most expensive option among all reviewed platforms

---

## Source 10: Pharmaprojects (Citeline)

| Field | Detail |
|-------|--------|
| **Source Name & URL** | Pharmaprojects (Citeline) — https://www.citeline.com/en/products-services/clinical/pharmaprojects |
| **Access Method** | Dashboard, API (via Citeline Informatics Drug Development API), Bulk Data Export |
| **Rate Limits & Pricing** | Enterprise licensing only (no public pricing). Part of Citeline suite — likely bundled with Trialtrove access. Estimated $15K-$50K+/year as standalone module. |
| **Data Freshness** | Daily — Continuously curated with 90,000+ drug profiles including 20,000+ in active development |
| **Data Format** | API (Drug Development API via Citeline Informatics), Dashboard (web), Data Export |
| **Reliability** | **High** — 40+ years of drug pipeline tracking history. Industry standard for global R&D pipeline monitoring. Recently upgraded to Pharmaprojects+ (launched June 30, 2025) with enhanced features. |
| **Use Case for CQ** | **HIGHLY RELEVANT** — Pharmaprojects tracks the complete drug development lifecycle from early discovery through launch, making it ideal for CQ's pipeline catalyst tracking. The Drug Development API provides programmatic access to drug development pipeline intelligence and global trends — exactly what CQ needs for detecting pipeline status changes, phase transitions, and development milestones. Combined with the Events API (Biomedtracker data) and Clinical Trial API (Trialtrove data), this forms a complete Citeline data stack for biotech catalyst intelligence. |

### Key Notes
- Pharmaprojects+ launched June 30, 2025 with next-generation features
- 90,000+ drug profiles with 20,000+ in active development
- API access via Citeline Informatics Drug Development API
- Integrated with Pharmapremia for Likelihood of Approval scoring
- Part of Citeline suite — potential bundling with Trialtrove and Biomedtracker

---

## Comparative Analysis: Relevance for ClinicalQuant Newsletter

| Source | CQ Relevance | API Available | Est. Annual Cost | Data Freshness | Priority |
|--------|-------------|----------------|-------------------|----------------|----------|
| **Biomedtracker** | Highest | Yes (Events API) | $8K-$25K | Real-time | **#1** |
| **Cortellis Clinical** | Very High | Yes (Labs sandbox) | $20K-$75K | Daily | **#2** |
| **Pharmaprojects** | Very High | Yes (Drug Dev API) | $15K-$50K | Daily | **#3** |
| **Trialtrove** | High | Yes (Clinical API) | $30K-$100K | Real-time | **#4** |
| **AdisInsight** | Moderate | Yes (Drugs/Trials) | $10K-$40K | Daily | **#5** |
| **Evaluate Pharma** | Moderate | No (Data Feeds) | $10K-$30K | Daily/Weekly | **#6** |
| **GlobalData** | Moderate | Yes (API/FTP/Cloud) | $15K-$50K | Daily | **#7** |
| **Medtrack/IQVIA** | Low | Yes (Developer Hub) | $30K-$150K | Daily | **#8** |
| **PharmaIntelligence** | N/A | (Merged into Citeline) | N/A | N/A | N/A |
| **TrialScope/PharmaSpect** | None | No | N/A | N/A | N/A |

---

## Strategic Recommendations for ClinicalQuant

### Tier 1: Immediate Priority (Best ROI for Catalyst Newsletter)

1. **Biomedtracker** — The single most relevant commercial source. Tracks FDA PDUFA dates, clinical readouts, approval decisions, and market-moving events. Events API enables automated pipeline integration. Likelihood of Approval (LOA) scoring from Pharmapremia adds quantitative prediction.

2. **Cortellis Clinical Trials Intelligence** — Best API accessibility via Cortellis Labs sandbox. Free evaluation before enterprise commitment. Curated data from 24 registries with historical depth. Most developer-friendly of all platforms reviewed.

### Tier 2: Growth Phase (When Budget Allows)

3. **Citeline Informatics API Suite** (Trialtrove + Pharmaprojects + Events) — Bundle all three Citeline APIs for comprehensive coverage: trial data (Trialtrove), pipeline tracking (Pharmaprojects), and catalyst events (Biomedtracker Events API). Negotiate enterprise bundle pricing.

4. **AdisInsight API** — Supplementary source for scientific trial detail enrichment. Springer Nature's licensing may be more accessible for smaller organizations.

### Tier 3: Not Recommended for CQ Use Case

5. **Evaluate Pharma** — Better suited for commercial forecasting than catalyst tracking. Consider only if CQ expands into revenue/sales forecast analysis.

6. **IQVIA/Medtrack** — Overkill for CQ's current needs. Too expensive. Best used for their free Institute reports.

7. **TrialScope** — Regulatory compliance tool, not relevant for catalyst tracking.

8. **PharmaSpect** — Does not exist as a commercial platform.

---

## Free Alternatives to Consider Alongside Paid Sources

| Source | URL | Data Type | Relevance |
|--------|-----|-----------|----------|
| ClinicalTrials.gov API v2 | https://clinicaltrials.gov/api/v2 | Free trial registry data | Core free source |
| FDA OpenFDA API | https://api.fda.gov | Drug approval data | PDUFA date tracking |
| SEC EDGAR API | https://www.sec.gov/edgar | 8-K filings | Catalyst event detection |
| PubMed API | https://www.ncbi.nlm.nih.gov/pmc/tools/oai/ | Publication data | KOL/trial publications |
| FDA Tracker | https://www.fdatracker.com | Free PDUFA calendar | Supplementary catalyst tracking |
| BiopharmWatch | https://www.biopharmawatch.com | Free catalyst tracker | Supplementary biotech tracking |
| Syfrah | https://www.syfrah.com | 570K+ trials from CT.gov/WHO ICTRP | Free trial search |

---

## API Access Summary Table

| Platform | API Available | API Documentation URL | Sandbox/Eval Access |
|----------|--------------|----------------------|-------------------|
| Citeline Informatics | Yes | https://www.citeline.com/en/products-services/custom-solutions/informatics-solutions | Contact sales |
| Cortellis Labs | Yes | https://cortellislabs.com/api/clinical/ | Yes (professional email required) |
| Clarivate Developer | Yes | https://developer.clarivate.com/apis/cortellis-api-collection | Contact sales |
| AdisInsight API | Yes | https://adisinsight.springer.com/apis | Limited preview |
| GlobalData | Yes | https://www.globaldata.com/marketplace/dataset/pharma-clinical-trials/ | Contact sales |
| IQVIA Developer Hub | Yes | https://developer.iqvia.com/ | Enterprise engagement required |
| Evaluate Pharma | No | Data Feeds only | Contact sales |
| Biomedtracker | Via Citeline | Events API via Citeline Informatics | Contact sales |
| TrialScope | No | Dashboard only | Contact sales |
| Pharmaprojects | Via Citeline | Drug Dev API via Citeline Informatics | Contact sales |

---

## Appendix: Research Methodology

- **Search Date**: 2026-04-21
- **Sources Verified**: Official product websites, API documentation pages, developer portals, Reddit discussions, software review sites (Capterra, SoftwareSuggest), industry analyses (IntuitionLabs)
- **Pricing**: All platforms use enterprise "contact sales" pricing. Estimates based on Reddit discussions, software review sites, and industry benchmarks. Actual pricing requires direct vendor engagement.
- **PharmaSpect Status**: No commercial platform found under this name after extensive web searches. Likely a confusion with another product or a defunct service.
- **PharmaIntelligence Note**: Rebranded to Citeline in 2022. All products now under Citeline brand.

---

*Report generated by Agent Zero Deep Research | ClinicalQuant Team*
