# Evaluate, Biomedtracker, MMIT, Panalgo & Norstella — Data Source Profiles

**Research Date:** 2026-04-22  
**Project:** ClinicalQuant Biotech Catalyst Newsletter Data Pipeline  
**Purpose:** Evaluate commercial pharma intelligence platforms for CQ catalyst data integration

---

## Executive Summary

All five platforms operate under **enterprise licensing models** with no publicly listed pricing. Evaluate (now under Norstella) and Biomedtracker (under Citeline/Norstella) offer the most directly relevant data for ClinicalQuant's biotech catalyst newsletter — particularly Biomedtracker's real-time catalyst event tracking and Evaluate Pharma's consensus forecasts. MMIT provides payer/formulary data most relevant to market access rather than catalyst events. Panalgo provides real-world evidence analytics. NorstellaLinQ integrates data across all brands.

| Platform | Primary CQ Relevance | Access Method | Data Freshness | Estimated Reliability |
|----------|---------------------|---------------|----------------|----------------------|
| Evaluate Pharma | HIGH — consensus forecasts, pipeline data | Paid API / Data Feeds | Daily/Weekly | High |
| Evaluate Omnium | MEDIUM — ML pipeline risk scoring | Paid Data Feeds | Daily/Weekly | High |
| Evaluate Data Feeds | HIGH — programmatic pipeline data | Paid API / sFTP / S3 | Daily-Quarterly | High |
| Biomedtracker (Citeline) | HIGHEST — real-time catalyst events, LOA | Paid API (Citeline Informatics) | Real-time | High |
| MMIT API | LOW for CQ — payer/formulary data | Paid RESTful API | Bi-weekly | High |
| Panalgo IHD | LOW for CQ — RWE analytics | Paid Cloud Platform | Near real-time | High |
| NorstellaLinQ | MEDIUM — integrated RWD + pipeline | Paid Integration | Varies by source | High |

---

## 1. Evaluate Pharma

| Field | Detail |
|-------|--------|
| **Source Name & URL** | Evaluate Pharma — https://www.evaluate.com/solutions/evaluate-pharma/ |
| **Access Method** | Paid API / Data Feeds (programmatic access available). Off-the-shelf feeds via sFTP or Amazon S3. Custom feeds support JSON, Parquet, Avro formats. No free tier. |
| **Rate Limits & Pricing** | Enterprise licensing — no public pricing. Contact sales for quotes. Custom data feeds priced separately from off-the-shelf. |
| **Data Freshness** | Daily, weekly, monthly, or quarterly (varies by data feed type). Daily/weekly stock round-ups available. |
| **Data Format** | Off-the-shelf: CSV, XLS. Custom: JSON, Parquet, Avro. Delivery via sFTP, Amazon S3, or custom destination. |
| **Reliability Rating** | **High** — Established pharma intelligence platform, consensus forecast leader, Norstella-backed infrastructure. |
| **CQ Use Case** | **HIGH PRIORITY** — Consensus sales forecasts for biotech companies, pipeline asset tracking, deal monitoring, and patent tracking. Most valuable for CQ's pre-market catalyst analysis — provides the quantitative baseline (consensus estimates) against which actual clinical/regulatory outcomes are measured. Complements Biomedtracker's event data with financial/market context. |

---

## 2. Evaluate Omnium

| Field | Detail |
|-------|--------|
| **Source Name & URL** | Evaluate Omnium — https://www.evaluate.com/solutions/evaluate-pharma/ (part of Evaluate Pharma suite) |
| **Access Method** | Paid Data Feeds (same infrastructure as Evaluate Pharma). No free tier. |
| **Rate Limits & Pricing** | Enterprise licensing — bundled with Evaluate Pharma or separate enterprise license. No public pricing. |
| **Data Freshness** | Daily to weekly updates (machine learning models retrained periodically). |
| **Data Format** | Same as Evaluate Pharma: CSV/XLS (off-the-shelf), JSON/Parquet/Avro (custom). |
| **Reliability Rating** | **High** — ML-powered pipeline risk scoring with millions of data points across clinical development stages. |
| **CQ Use Case** | **MEDIUM PRIORITY** — Predictive risk-return scoring for clinical pipeline assets. Could enhance CQ's PDUFA outcome predictions with probabilistic risk assessments. However, the ML model is a black box and may not provide the explainability needed for newsletter analysis. More useful as an internal signal than a cited source. |

---

## 3. Evaluate Data Feeds

| Field | Detail |
|-------|--------|
| **Source Name & URL** | Evaluate Data Feeds — https://www.evaluate.com/solutions/data-feeds/ |
| **Access Method** | Paid API / Programmatic Access + sFTP / Amazon S3 delivery. Custom feeds available. No free tier. |
| **Rate Limits & Pricing** | Enterprise licensing — no public pricing. Scalable based on data volume and delivery frequency. Custom feeds priced based on format and destination requirements. |
| **Data Freshness** | Off-the-shelf: Daily, weekly, monthly, or quarterly. Custom: Configurable based on client needs. |
| **Data Format** | **Off-the-shelf:** CSV, XLS. **Custom:** JSON, Parquet, Avro. Delivery: sFTP, Amazon S3, or custom destinations. Programmatic access for direct integration into CRM, analytics dashboards, and applications. |
| **Reliability Rating** | **High** — Systematic data pipeline with established update schedules and programmatic delivery infrastructure. |
| **CQ Use Case** | **HIGH PRIORITY** — Primary programmatic access point for Evaluate data. Most relevant for CQ's automated pipeline: Product attributes, predictive metrics, clinical trial data, forecast/event data, and deal tracking. JSON/Parquet custom feeds ideal for CQ's data pipeline. Programmatic access enables seamless integration with CQ's monitoring systems. Specific data types of interest: Key event data (PDUFA dates, trial readouts), forecast data (consensus vs. actual), and deal/ownership data (M&A catalysts). |

---

## 4. Biomedtracker (Citeline)

| Field | Detail |
|-------|--------|
| **Source Name & URL** | Biomedtracker (Citeline) — https://www.biomedtracker.com/ |
| **Access Method** | **Paid API** via Citeline Informatics Solutions. RESTful/JSON API at docs.api.citeline.com. Two APIs: Drug Development API (Pharmaprojects pipeline data) and Events API (Biomedtracker catalysts). Web portal also available. No free tier. |
| **Rate Limits & Pricing** | Enterprise licensing — no public pricing. API access requires commercial agreement with Citeline. Tiered by data scope and call volume. |
| **Data Freshness** | **Real-time** — Catalysts and events tracked in real-time. Regulatory activities, trial data updates, and deal changes are monitored continuously. |
| **Data Format** | **API:** JSON (RESTful). **Portal:** Web-based interface with Advanced Catalyst Search, FDA AdComm search, KOL search, Trial Comparison search. |
| **Reliability Rating** | **High** — Industry-standard biopharma catalyst tracking. Part of Citeline/Norstella infrastructure. Widely cited by institutional investors and analysts. |
| **CQ Use Case** | **HIGHEST PRIORITY** — Directly aligns with CQ's core value proposition: real-time tracking of clinical trial data releases, regulatory events (PDUFA dates, AdComm meetings), and deal catalysts. The Events API provides structured catalyst events with expected date ranges, likelihood of approval predictions, and company/drug-specific filtering. This is the single most valuable commercial data source for CQ's biotech catalyst newsletter. Specific use cases: (1) PDUFA date tracking with outcome probabilities, (2) Clinical trial readout date predictions, (3) Regulatory filing catalysts, (4) M&A and deal event monitoring, (5) FDA Advisory Committee meeting tracking. |

---

## 5. MMIT API

| Field | Detail |
|-------|--------|
| **Source Name & URL** | MMIT API — https://api.mmitnetwork.com/ and https://www.mmitnetwork.com/api/ |
| **Access Method** | **Paid RESTful API** at api.mmitnetwork.com. Requires registration and commercial agreement. Quick Start guide available. Scalable API calls starting from a baseline. |
| **Rate Limits & Pricing** | Enterprise licensing — no public pricing. API usage is scalable to match business needs, starting with a baseline number of API calls. Implies tiered pricing based on call volume. |
| **Data Freshness** | Real-time to bi-weekly. Formulary and medical policy data updated continuously. Analytics Pro provides bi-weekly market snapshots. Covers 98%+ of covered lives with status and restriction changes monitored in real-time. |
| **Data Format** | RESTful JSON API. Returns raw formulary, coverage, restriction, medical policy, and Rx BIN/PCN/Group data. Decade of historical data across all drugs, channels, states, CBSAs, and counties. |
| **Reliability Rating** | **High** — Leading platform for pharma market access data. Covers 98%+ of covered lives. Norstella-backed infrastructure. RESTful API architecture ensures reliable programmatic access. |
| **CQ Use Case** | **LOW PRIORITY for CQ catalyst newsletter** — MMIT's core value is payer/formulary/coverage data, which is more relevant to market access teams than to catalyst event tracking. However, it has secondary value for: (1) Tracking formulary coverage changes post-FDA approval (a secondary catalyst type), (2) Identifying payer restriction changes that signal commercial readiness, (3) BIN/PCN/Group data for understanding drug availability at launch. Recommend considering MMIT only after Biomedtracker and Evaluate are integrated and revenue justifies the additional enterprise license. |

---

## 6. Panalgo (IHD Platform)

| Field | Detail |
|-------|--------|
| **Source Name & URL** | Panalgo — https://panalgo.com/ (part of Norstella) |
| **Access Method** | **Paid Cloud Platform** (IHD Cloud). Ella AI Gen AI assistant for cohort building. IHD Data Science for advanced analytics. No free tier. No public API documentation for data extraction — designed as an analytics platform, not a data pipe. |
| **Rate Limits & Pricing** | Enterprise licensing — no public pricing. Cloud platform subscription model. Separate licensing for IHD Cloud, IHD Data Science, and Ella AI. |
| **Data Freshness** | Near real-time to quarterly depending on data source. NorstellaLinQ RWD data includes trigger alerts for real-time notifications. Claims, lab, pathways, and EMR data sets with varying refresh cycles. |
| **Data Format** | Cloud analytics platform (IHD Cloud). No standard data export format documented. LinQ data supports structured and unstructured data analysis. Seamless integrations mentioned but no public API specs. |
| **Reliability Rating** | **High** — Established real-world evidence analytics platform. Norstella-backed. Used by major pharma companies. IHD platform has been operating for years. |
| **CQ Use Case** | **LOW PRIORITY for CQ** — Panalgo is an analytics/RWE platform, not a data source for catalyst events. Its value to CQ would be primarily through NorstellaLinQ's integrated data asset (which includes Evaluate and Citeline data). The Ella AI Gen AI assistant and IHD analytics could theoretically be used for post-market analysis of catalyst outcomes, but this is outside CQ's current scope. Only relevant if CQ expands into real-world outcome analysis. |

---

## 7. NorstellaLinQ

| Field | Detail |
|-------|--------|
| **Source Name & URL** | NorstellaLinQ — https://www.norstella.com/our-brands/ (integrated data asset across Norstella brands) |
| **Access Method** | **Paid Integration** — Unified data asset connecting Evaluate (forecasting), Citeline (clinical/regulatory), MMIT (payer), and Panalgo (analytics). Access via enterprise agreement with Norstella. Launched 2024. |
| **Rate Limits & Pricing** | Enterprise licensing — no public pricing. Likely premium pricing given it integrates all Norstella brands. Bundled or separate licensing unclear. |
| **Data Freshness** | Varies by source — real-time catalysts (Citeline), daily/weekly forecasts (Evaluate), bi-weekly formulary (MMIT), near real-time RWD (Panalgo). Over 1 billion data points. |
| **Data Format** | Integrated data asset — format depends on access method. Likely supports programmatic access given Evaluate Data Feeds infrastructure and MMIT API. No public format documentation for LinQ specifically. |
| **Reliability Rating** | **High** — Combines data from four established Norstella brands (Evaluate, Citeline, MMIT, Panalgo). Each brand has strong individual reliability. Integration quality untested given 2024 launch. |
| **CQ Use Case** | **MEDIUM PRIORITY** — NorstellaLinQ could theoretically provide a single integration point for all CQ data needs (catalysts from Citeline, forecasts from Evaluate, payer data from MMIT). However, as a newly launched (2024) product, integration maturity is uncertain. For CQ's immediate needs, direct API access to Biomedtracker (Citeline) and Evaluate Data Feeds would be more straightforward. Consider NorstellaLinQ as a future consolidation option once CQ revenue justifies enterprise licensing across multiple Norstella brands. |

---

## Integration Priority Recommendations for ClinicalQuant

### Tier 1: Immediate Priority (When Budget Available)
1. **Biomedtracker Events API (Citeline Informatics)** — Directly matches CQ's core use case of catalyst event tracking. RESTful JSON API enables automated pipeline integration.
2. **Evaluate Data Feeds** — Programmatic access to consensus forecasts, pipeline data, and key events. JSON/Parquet custom feeds ideal for CQ automation.

### Tier 2: Strategic (After Revenue Validates)
3. **Evaluate Pharma** — Full platform access for deeper analysis when CQ expands beyond catalyst-only content.
4. **NorstellaLinQ** — Single integration point for Evaluate + Citeline + MMIT + Panalgo data, if pricing makes sense.

### Tier 3: Low Priority for CQ
5. **MMIT API** — Payer/formulary data has secondary catalyst value only. Consider for market access content expansion.
6. **Panalgo IHD** — Analytics platform, not a data source. Only relevant if CQ moves into RWE/outcome analysis.
7. **Evaluate Omnium** — ML pipeline risk scoring is useful but black-box nature limits newsletter value.

---

## Key Findings & Gaps

### Confirmed Data Points
- All five platforms operate under **enterprise licensing** — no public pricing available
- Evaluate Data Feeds provides **programmatic access** via sFTP/S3 with JSON/Parquet/Avro custom formats
- MMIT has a **documented RESTful API** at api.mmitnetwork.com (contradicts GetApp listing)
- Biomedtracker (Citeline) has **Events API** at docs.api.citeline.com providing JSON catalyst data
- NorstellaLinQ (2024 launch) integrates all brand data but has no public API documentation
- Panalgo is an **analytics platform**, not a data extraction source

### Unverified / Needs Direct Inquiry
- Exact pricing for any platform — all require sales contact
- API rate limits and throttling policies — not publicly documented for any platform
- Evaluate Data Feeds API endpoint specifications (beyond sFTP/S3 delivery)
- MMIT API authentication mechanism and exact endpoint catalog
- NorstellaLinQ technical access specifications and data format details
- Panalgo data export capabilities beyond the IHD Cloud analytics interface

### Critical Note for CQ Pipeline
All commercial platforms should be treated as **Tier 2/3 paid sources** to be added after CQ establishes revenue. The free data sources (SEC EDGAR, FDA/OpenFDA, ClinicalTrials.gov, PubMed) documented in the CQ pipeline remain the foundation. Biomedtracker is the single most valuable commercial addition due to its direct catalyst event coverage, but enterprise pricing means it should be evaluated once CQ generates sufficient subscription revenue ($149+/month tier) to justify the cost.

---

*Report generated by Agent Zero Deep Research — 2026-04-22*
*Primary: /a0/CTO/Meddash-CQ Team files/Evaluate_Biomedtracker_MMIT_Panalgo_Norstella_Data_Source_Profiles.md*
*Backup: /a0/usr/ceo-files/Evaluate_Biomedtracker_MMIT_Panalgo_Norstella_Data_Source_Profiles.md*
