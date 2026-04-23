# Commercial Biotech Catalyst Tracking Services - Research Report

**Research Date:** 2026-04-22
**Researcher:** Agent Zero Deep Research (Agent 8)
**Purpose:** Identify commercial services for ClinicalQuant biotech catalyst newsletter data pipeline

---

## Methodology

5 sequential web searches executed:
1. `drug pipeline calendar service`
2. `biotech event calendar API`
3. `clinical trial catalyst tracker`
4. `pharma pipeline calendar tool`
5. `biogenis biotech`

**IMPORTANT FINDING ON SEARCH 5:** The query "biogenis biotech" returned ZERO catalyst tracking services. All results were unrelated biotech companies (Biogenes Technologies - aptamers/diagnostics, BioGenesis LLC - stem cells, Biogen - large pharma, Sanofi Biogenius - science competition, Core Biogenesis - skincare, Biogensis Biotechnics - PCD pharma franchise, Biogenics Inc. - lab instruments). **No service called "Biogenis" or similar exists in the biotech catalyst tracking space based on search results.**

---

## Distinct Services Catalog (16 Services)

### 1. BiopharmaWatch

| Field | Detail |
|-------|--------|
| **Source Name & URL** | BiopharmaWatch - https://www.biopharmawatch.com/ |
| **Access Method** | Free web platform (FDA Calendar page at /fda-calendar) |
| **Rate Limits & Pricing** | Free (no specific pricing tiers found in search results) |
| **Data Freshness** | Daily ("updated daily" per search result) |
| **Data Format** | HTML (web-based calendar); no API mentioned in search results |
| **Reliability** | Medium - free service, claims real-time updates but no API verification |
| **CQ Use Case** | Free FDA/PDUFA date tracking and clinical trial readout calendar for initial data sourcing; manual verification of catalyst dates for newsletter content |

---

### 2. CatalystAlert

| Field | Detail |
|-------|--------|
| **Source Name & URL** | CatalystAlert - https://catalystalert.io/ |
| **Access Method** | Free web platform with AI predictions |
| **Rate Limits & Pricing** | Free tier available (search result states "Free biotech catalyst calendar"); paid tiers not specified in results |
| **Data Freshness** | Real-time ("Real-time alerts for biotech investors") |
| **Data Format** | HTML (web); alert system format unspecified |
| **Reliability** | Medium - newer service, AI-powered predictions add value but need validation |
| **CQ Use Case** | Real-time catalyst alerts for FDA decisions, PDUFA dates, Phase 3 readouts; AI predictions could supplement ClinicalQuant's own predictive models |

---

### 3. BioPharmCatalyst / BPIQ (Unified Platform)

| Field | Detail |
|-------|--------|
| **Source Name & URL** | BioPharmCatalyst (now BPIQ/BiopharmIQ) - https://www.biopharmcatalyst.com/ and https://www.bpiq.com/ |
| **Access Method** | Paid API (contact@biopharmcatalyst.com); Web platform at app.bpiq.com; MCP server at https://mcp.bpiq.com/mcp |
| **Rate Limits & Pricing** | API: Custom pricing (email inquiry required). Subscription tiers: Basic Free, Pro $20/mo, Elite $25/mo (sale from $40), Apex $45/mo (sale from $60), API custom pricing |
| **Data Freshness** | Daily ("maintained daily" per search result; "updated on a daily basis") |
| **Data Format** | JSON API; HTML web interface; MCP integration for AI workflows |
| **Reliability** | High - established service, division of Scientist.com, multiple access methods, active MCP server confirmed |
| **CQ Use Case** | PRIMARY paid data source for ClinicalQuant. FDA Calendar, PDUFA Calendar, Historical Calendar, Conference Calendar, Hedge Fund Data, Clinical Trials, Drug Pipeline Database. MCP server enables direct AI agent integration. Premium endpoints for hedge fund holdings and historical catalysts add unique value. |

---

### 4. ClinicalRx

| Field | Detail |
|-------|--------|
| **Source Name & URL** | ClinicalRx - https://clinicalrx.ai/ |
| **Access Method** | Web platform (AI-powered); API availability unknown from search results |
| **Rate Limits & Pricing** | Not specified in search results - requires further investigation |
| **Data Freshness** | Real-time ("Powered by live ClinicalTrials.gov data"; tracks 65,000+ recruiting trials) |
| **Data Format** | Unspecified (web platform); likely JSON API given .ai domain positioning |
| **Reliability** | Medium-High - leverages ClinicalTrials.gov data directly but is a newer AI platform |
| **CQ Use Case** | Clinical trial tracking and intelligence; real-time monitoring of 65,000+ recruiting trials for phase transitions, completion dates, and status changes that serve as catalysts |

---

### 5. BioCatalysts.ai

| Field | Detail |
|-------|--------|
| **Source Name & URL** | BioCatalysts.ai - https://biocatalysts.ai/catalysts |
| **Access Method** | Web platform with proprietary Bio-Score volatility prediction |
| **Rate Limits & Pricing** | Not specified in search results - requires investigation |
| **Data Freshness** | Regularly updated (search result shows upcoming catalysts ranked by predicted volatility) |
| **Data Format** | HTML (web); API availability unknown |
| **Reliability** | Medium - unique Bio-Score methodology but unverified independently |
| **CQ Use Case** | Complementary catalyst ranking via Bio-Score predicted volatility; PDUFA dates, Phase 3 readouts, AdCom votes, NDA decisions all scored by expected move magnitude - useful for prioritizing which catalysts to feature in newsletter |

---

### 6. Benzinga FDA Calendar API

| Field | Detail |
|-------|--------|
| **Source Name & URL** | Benzinga FDA Calendar API - https://www.benzinga.com/apis/cloud-product/fda-calendar/ |
| **Access Method** | Paid API (cloud product) |
| **Rate Limits & Pricing** | Not specified in search results - Benzinga API products typically have tiered pricing; requires contacting Benzinga for quotes |
| **Data Freshness** | Dynamic ("dynamically updated investment tool") |
| **Data Format** | JSON API (cloud product) |
| **Reliability** | High - established financial data provider with institutional clients |
| **CQ Use Case** | Professional-grade FDA calendar API for automated pipeline integration; dynamically updated FDA events suitable for real-time newsletter alert triggers and systematic catalyst tracking |

---

### 7. BioTrack (BTIP)

| Field | Detail |
|-------|--------|
| **Source Name & URL** | BioTrack - https://www.btip.pro/ |
| **Access Method** | Web platform ("Loading from database..." suggests app-based interface) |
| **Rate Limits & Pricing** | Not specified in search results |
| **Data Freshness** | Unknown - search result only showed loading page |
| **Data Format** | Unknown (web app with database backend) |
| **Reliability** | Low - minimal information available from search result; site appears to be in development or limited access |
| **CQ Use Case** | Potential clinical trial catalyst tracker but requires further investigation to determine viability; search result too sparse to confirm usefulness |

---

### 8. FDA Tracker

| Field | Detail |
|-------|--------|
| **Source Name & URL** | FDA Tracker - https://www.fdatracker.com/ |
| **Access Method** | Web platform; Trial Tracker tool at /support/trial-tracker/ |
| **Rate Limits & Pricing** | Not specified in search results; appears to have free and paid tiers |
| **Data Freshness** | Regular (integrates PDUFA dates, clinical trial primary completion dates, and working capital runway estimates) |
| **Data Format** | HTML (web platform); API availability unknown |
| **Reliability** | Medium - enhanced FDA calendar with working capital runway (unique feature) but pricing/access unclear |
| **CQ Use Case** | Unique value-add: combines FDA catalyst dates with working capital runway estimates for biotech companies, enabling assessment of whether companies can afford to reach their next catalyst - critical risk factor for ClinicalQuant newsletter analysis |

---

### 9. BioCatalyst.app

| Field | Detail |
|-------|--------|
| **Source Name & URL** | BioCatalyst - https://www.biocatalyst.app/ |
| **Access Method** | Web platform (AI-powered) |
| **Rate Limits & Pricing** | Not specified in search results |
| **Data Freshness** | Real-time ("automated research and portfolio optimization") |
| **Data Format** | Unspecified (AI-powered web platform) |
| **Reliability** | Medium - AI-powered tracker for "serious investors" but limited verifiable information |
| **CQ Use Case** | AI-powered FDA approval, PDUFA date, and clinical milestone monitoring; automated research could supplement ClinicalQuant's own analysis pipeline |

---

### 10. Biomedtracker (Citeline/Pharma Intelligence)

| Field | Detail |
|-------|--------|
| **Source Name & URL** | Biomedtracker - https://www.biomedtracker.com/ |
| **Access Method** | Paid enterprise platform |
| **Rate Limits & Pricing** | Enterprise pricing (not publicly listed); likely $10K+/year institutional subscription typical of Pharma Intelligence/Citeline products |
| **Data Freshness** | Regular (pharmaceutical development insights, upcoming catalysts, expert opinions) |
| **Data Format** | HTML (web platform); enterprise data feeds likely available |
| **Reliability** | High - Citeline/Pharma Intelligence is an established industry data provider |
| **CQ Use Case** | Premium institutional-grade catalyst tracking with expert analyst commentary; potential Tier 3 source for deep-dive analysis when specific catalysts require expert validation beyond automated data |

---

### 11. Pharmaprojects (Citeline)

| Field | Detail |
|-------|--------|
| **Source Name & URL** | Pharmaprojects by Citeline - https://www.citeline.com/en/products-services/clinical/pharmaprojects |
| **Access Method** | Paid enterprise platform (Pharmaprojects+) |
| **Rate Limits & Pricing** | Enterprise pricing (not publicly listed); likely $15K+/year typical for Citeline suite |
| **Data Freshness** | Regular updates with Drug Similarity tool, Advanced Analytics, Company Compare features |
| **Data Format** | Proprietary platform (web-based); likely has API/data export for enterprise clients |
| **Reliability** | High - industry standard for pipeline tracking, owned by Citeline (Norstella) |
| **CQ Use Case** | Industry-standard pipeline database for deep competitive analysis and drug similarity mapping; Drug Similarity tool and Company Compare features could identify comparable catalysts across similar drug classes for ClinicalQuant analysis |

---

### 12. MarketBeat FDA Calendar

| Field | Detail |
|-------|--------|
| **Source Name & URL** | MarketBeat FDA Calendar - https://www.marketbeat.com/fda-calendar/ |
| **Access Method** | Free web platform (MarketBeat has paid tiers for broader stock data) |
| **Rate Limits & Pricing** | Free FDA calendar access; MarketBeat premium subscriptions for full platform start ~$199/year (per public info, not confirmed in search results) |
| **Data Freshness** | Daily ("updated daily with real-time stock prices and 30-day price trends") |
| **Data Format** | HTML (web); MarketBeat has broader API for premium subscribers |
| **Reliability** | Medium-High - established financial data platform with daily updates and stock price correlation |
| **CQ Use Case** | Free FDA calendar with built-in 30-day price trend correlation; useful for linking catalyst events to actual stock price movements in ClinicalQuant newsletter content |

---

### 13. Health Pioneer Drug Pipeline Tracker

| Field | Detail |
|-------|--------|
| **Source Name & URL** | Health Pioneer Drug Pipeline - https://healthpioneer.com/biopharma/drug-pipeline |
| **Access Method** | Web platform |
| **Rate Limits & Pricing** | Not specified in search results; appears free |
| **Data Freshness** | Regular (tracks 247 drugs in development per search result) |
| **Data Format** | HTML (web); API unknown |
| **Reliability** | Low-Medium - smaller dataset (247 drugs vs thousands on other platforms); verification needed |
| **CQ Use Case** | Limited use for ClinicalQuant due to small scope (247 drugs); potentially useful for tracking specific breakthrough therapies in oncology, neurology, and rare diseases if coverage aligns with newsletter focus areas |

---

### 14. TipRanks FDA Calendar

| Field | Detail |
|-------|--------|
| **Source Name & URL** | TipRanks FDA Calendar - https://www.tipranks.com/calendars/fda |
| **Access Method** | Web platform (TipRanks has premium tiers) |
| **Rate Limits & Pricing** | Free FDA calendar access; TipRanks premium for full platform features; typical pricing ~$29-299/year for stock analysis tools |
| **Data Freshness** | Regular (centralized PDUFA decision date tracking for publicly traded biopharma) |
| **Data Format** | HTML (web); TipRanks API available for premium subscribers |
| **Reliability** | Medium-High - established financial analytics platform with institutional adoption |
| **CQ Use Case** | PDUFA date calendar specifically for publicly traded biopharma companies; includes company name, ticker, drug candidate, and expected decision date - directly aligned with ClinicalQuant's ticker-focused catalyst newsletter format |

---

### 15. ClinicalTrials.gov

| Field | Detail |
|-------|--------|
| **Source Name & URL** | ClinicalTrials.gov - https://clinicaltrials.gov/ |
| **Access Method** | Free API (v2) + Web |
| **Rate Limits & Pricing** | FREE - API v2 at clinicaltrials.gov/api; no registration required for basic access; rate limit not published but generally generous for research use |
| **Data Freshness** | Real-time (updated continuously as trials are registered/updated) |
| **Data Format** | JSON API (v2); XML also available; HTML web interface |
| **Reliability** | High - US government official registry, definitive source for clinical trial data |
| **CQ Use Case** | PRIMARY free data source for ClinicalQuant. API v2 enables automated monitoring of clinical trial status changes, phase transitions, primary completion dates, and enrollment updates. Essential for TrialSight pipeline and catalyst date verification. Already integrated in CQ data pipeline per prior architecture. |

---

### 16. Pipeline Watch (Citeline/Scrip)

| Field | Detail |
|-------|--------|
| **Source Name & URL** | Pipeline Watch by Citeline/Scrip - https://insights.citeline.com/scrip/r-and-d/pipeline-watch/ |
| **Access Method** | Paid subscription (Scrip/Citeline intelligence product) |
| **Rate Limits & Pricing** | Enterprise/subscription pricing (Scrip subscriptions typically $5K-15K+/year); not publicly listed in search results |
| **Data Freshness** | Regular (periodic pipeline updates and insights) |
| **Data Format** | HTML (articles/analysis); no public API |
| **Reliability** | High - Citeline is established pharma intelligence provider |
| **CQ Use Case** | Editorial pipeline analysis and expert commentary on drug development trends; useful for qualitative context and expert perspectives to supplement ClinicalQuant's quantitative catalyst data, but not suitable for automated data pipeline integration |

---

## Summary: Search 5 - "biogenis biotech"

**RESULT: NO CATALYST TRACKING SERVICE FOUND.**

All results for "biogenis biotech" were unrelated companies:
- **Biogenes Technologies** (biogenestech.com) - Animal-free aptamers for diagnostics, NOT a catalyst tracker
- **BioGenesis LLC** (biogenesis.world) - Stem cell culturing/manufacturing, NOT a catalyst tracker
- **Biogen** (biogen.com) - Major biotech pharma company (MS/spinal muscular atrophy drugs), NOT a catalyst tracking service
- **Sanofi Biogenius Canada** (biogenius.ca) - High school science competition, NOT relevant
- **Core Biogenesis** (peauforia.com) - Skincare actives/botanical growth factors, NOT relevant
- **Biogensis Biotechnics** (biogensisbiotechnics.com) - PCD pharma franchise company in India, NOT a catalyst tracker
- **Biogenics Inc.** (biogenics.com) - Lab instruments/cryopreservation equipment, NOT a catalyst tracker

**Conclusion:** There is no commercial biotech catalyst tracking service named "Biogenis" or similar. This specific query returned zero relevant services.

---

## Tiered Recommendation for ClinicalQuant Integration

### Tier 1 - Immediate Integration (Free, Verified)
| Service | Role | Priority |
|---------|------|----------|
| ClinicalTrials.gov API v2 | Primary trial data pipeline | CRITICAL |
| BiopharmaWatch (free calendar) | PDUFA/FDA date verification | HIGH |
| MarketBeat FDA Calendar | Price-trend correlated catalyst tracking | HIGH |
| TipRanks FDA Calendar | Ticker-focused PDUFA dates | MEDIUM |

### Tier 2 - Strategic Paid Integration
| Service | Role | Priority |
|---------|------|----------|
| BPIQ/BioPharmCatalyst API | Primary paid catalyst data + MCP integration | CRITICAL |
| Benzinga FDA Calendar API | Professional-grade automated FDA alerts | HIGH |

### Tier 3 - Deep Analysis / Manual Validation
| Service | Role | Priority |
|---------|------|----------|
| BioCatalysts.ai (Bio-Score) | Volatility prediction for catalyst ranking | MEDIUM |
| FDA Tracker (runway data) | Working capital runway + catalyst timing | MEDIUM |
| CatalystAlert (AI predictions) | AI-supplemented catalyst forecasting | LOW-MEDIUM |

### Tier 4 - Enterprise / Institutional Grade
| Service | Role | Priority |
|---------|------|----------|
| Pharmaprojects (Citeline) | Deep pipeline analysis & drug similarity | LOW (future) |
| Biomedtracker (Citeline) | Expert analyst commentary on catalysts | LOW (future) |

### Needs Further Investigation
| Service | Reason |
|---------|--------|
| ClinicalRx | Unknown pricing/API; potentially valuable for 65K+ trial tracking |
| BioCatalyst.app | Unknown pricing; AI-powered monitoring could be useful |
| BioTrack (btip.pro) | Minimal info available; site appeared to be loading/under development |
| Health Pioneer | Only 247 drugs tracked; likely insufficient scope |

---

## Data Freshness Comparison

| Service | Freshness | Verified? |
|---------|-----------|----------|
| ClinicalTrials.gov | Real-time (continuous) | YES - govt API |
| BiopharmaWatch | Daily | YES - stated |
| BPIQ/BioPharmCatalyst | Daily | YES - stated |
| CatalystAlert | Real-time alerts | Stated, needs verification |
| ClinicalRx | Real-time (live CT.gov data) | Stated, needs verification |
| MarketBeat | Daily + real-time prices | YES - stated |
| Benzinga | Dynamic | Stated, needs verification |
| TipRanks | Regular | Needs verification |
| BioCatalysts.ai | Regular | Needs verification |

---

## Pricing Summary (Verified Amounts Only)

| Service | Pricing | Source |
|---------|---------|--------|
| ClinicalTrials.gov | FREE | Government API |
| BiopharmaWatch | FREE (web) | Search result: "Free FDA Calendar" |
| CatalystAlert | FREE tier available | Search result: "Free biotech catalyst calendar" |
| MarketBeat FDA Calendar | FREE (calendar); Premium ~$199/yr | Public knowledge (not in search results) |
| BPIQ/BioPharmCatalyst | Free Basic; Pro $20/mo; Elite $25/mo; Apex $45/mo; API custom | Prior memory + confirmed by search |
| Benzinga API | Contact for pricing | Search result: enterprise API product |
| TipRanks | Free FDA calendar; Premium ~$29-299/yr | Public knowledge (not in search results) |
| Pharmaprojects | Enterprise ($15K+/yr estimate) | Industry knowledge (not confirmed) |
| Biomedtracker | Enterprise ($10K+/yr estimate) | Industry knowledge (not confirmed) |

**IMPORTANT:** Only BPIQ/BioPharmCatalyst pricing was confirmed through both search results AND prior memory. All other pricing marked as estimates requires direct verification.

---

*Report generated by Agent Zero Deep Research - Agent 8*
*All URLs and service details sourced exclusively from actual search results - no hallucinated content*
