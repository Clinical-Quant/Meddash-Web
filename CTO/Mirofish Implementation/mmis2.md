# MMIS2: Mirofish-MedDash Integration Phase 1
## Operational Execution Handbook - KOL Briefs Predictive Enhancement

**Document:** MMIS2 - Mirofish-MedDash Implementation Phase 1  
**Version:** 1.0  
**Date:** April 16, 2026  
**Classification:** Operational Execution Guide  
**Previous Document:** MMIS1 (Technical Blueprint)  
**Location:** `/a0/usr/ceo-files/`  

---

## Executive Overview

This document provides the **operational execution roadmap** for Phase 1 of the Mirofish-MedDash integration. Built on the technical specifications from MMIS1, this handbook translates strategic planning into day-by-day actionable tasks, ownership assignments, and success criteria.

**Goal:** Deploy predictive analytics-enhanced KOL Briefs within 10 weeks, delivering measurable client value that replaces expensive consultant engagements.

---

## Table of Contents

1. [Phase 1 Architecture Overview](#1-phase-1-architecture-overview)
2. [10-Week Implementation Timeline](#2-10-week-implementation-timeline)
3. [Immediate Actions (Week 1)](#3-immediate-actions-week-1)
4. [Stages 1-5 Detailed Execution](#4-stages-1-5-detailed-execution)
5. [Data Architecture & Dependencies](#5-data-architecture--dependencies)
6. [Quality Gates & Success Criteria](#6-quality-gates--success-criteria)
7. [Risk Management](#7-risk-management)
8. [Team & Resource Assignment](#8-team--resource-assignment)
9. [Client Pilot Program](#9-client-pilot-program)
10. [Appendices](#10-appendices)

---

## 1. Phase 1 Architecture Overview

### Decision-First Implementation Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PHASE 1 ARCHITECTURE (10 Weeks)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WEEKS 1-2: INFRASTRUCTURE FOUNDATION        (Stage 1)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                      │
│  │ Mirofish │ │ Supabase │ │   API    │ │  Queue   │                      │
│  │ Deploy   │ │  Bridge  │ │  Layer   │ │  System  │                      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘                      │
│                                                                             │
│  WEEKS 3-4: QUANTIFICATION ENGINE            (Stage 2)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                      │
│  │   EPS    │ │  RWPS    │ │ Network  │ │ Temporal │                      │
│  │ Calculator│ │  Engine  │ │Centrality│ │ Tracking │                      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘                      │
│                                                                             │
│  WEEKS 5-6: SIMULATION CONTEXT               (Stage 3)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                      │
│  │  Seed    │ │ Scenario │ │Competitor│ │  Market  │                      │
│  │Document  │ │ Templates│ │ Context  │ │ Context  │                      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘                      │
│                                                                             │
│  WEEKS 7-8: DECISION INTERPRETATION          (Stage 4)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                      │
│  │ Translation │ Failure │ │ Feedback │ │Visualize─│                      │
│  │   Engine    │  Modes  │ │   Loop   │ │   ion    │                      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘                      │
│                                                                             │
│  WEEKS 9-10: OUTPUT INTEGRATION              (Stage 5)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                      │
│  │ Enhanced │ │   MSL    │ │   API    │ │  Pricing │                      │
│  │   PDF    │ │  Widgets │ │ Response │ │  Update  │                      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Core Value Flow

| Stage | Input | Output | Client Value |
|-------|-------|--------|--------------|
| 1 | Raw Supabase data | Connected infrastructure | Platform ready |
| 2 | Publication/trial records | EPS 0.00-1.00 scores | Prioritization clarity |
| 3 | KOL profile + context | Mirofish-ready seed documents | Context-rich predictions |
| 4 | Raw Mirofish verdicts (73% confidence) | "High Priority - deploy within 5 days" | Actionable intelligence |
| 5 | Interpreted predictions | Enhanced KOL Brief ($4,500) | Consultant replacement |

---

## 2. 10-Week Implementation Timeline

### Master Timeline View

```
Week:    1    2    3    4    5    6    7    8    9   10
         |────|────|────|────|────|────|────|────|────|
         
Stage 1: [Infrastructure]
         ████████████████████
         
Stage 2:           [Quantification]
                    ████████████████████
                    
Stage 3:                       [Simulation Context]
                                ████████████████████
                                
Stage 4:                                           [Decision Layer]
                                                    ████████████████████
                                                    
Stage 5:                                                               [Output]
                                                                      ████████████████████
                                                                      
Gates:        G1               G2               G3               G4               G5
              ↓                ↓                ↓                ↓                ↓
         Infra Ready     EPS Valid        Seeds Ready     Decisions Clear   Product Live
```

### Weekly Milestones

| Week | Stage | Theme | Key Deliverable | Go/No-Go Gate |
|------|-------|-------|-----------------|---------------|
| **1** | 1 | Deploy | Cloud infrastructure provisioned | G1: Mirofish accessible |
| **2** | 1 | Connect | Supabase → Mirofish bridge working | G1: End-to-end test passed |
| **3** | 2 | Calculate | EPS calculator functional | - |
| **4** | 2 | Validate | Quantified scores make business sense | G2: EPS accuracy baseline |
| **5** | 3 | Build | Seed document templates created | - |
| **6** | 3 | Enrich | Competitive + market context integrated | G3: Full context seeds |
| **7** | 4 | Translate | Raw predictions → decision language | - |
| **8** | 4 | Optimize | Failure modes + feedback loop built | G4: Non-tech user validated |
| **9** | 5 | Generate | Enhanced PDF template complete | - |
| **10** | 5 | Launch | Product live with pilot clients | G5: Revenue tracking active |

---

## 3. Immediate Actions (Week 1)

### Day 1-3: Pre-Flight Checklist

| Priority | Action | Owner | Success Criteria | Time |
|----------|--------|-------|------------------|------|
| **P0** | Confirm budget sign-off | Executive / CEO | Approved resource allocation documented | Hour 1 |
| **P0** | Assign technical lead | CTO | Lead named, 75%+ allocation confirmed | Hour 2 |
| **P0** | Schedule kickoff meeting | Project Manager | Meeting invite sent, all stakeholders confirmed | Hour 3 |
| **P1** | Provision cloud infrastructure | DevOps | AWS/GCP account ready, IAM permissions set | Day 1 PM |
| **P1** | Clone Mirofish repo | Backend Engineer | `git clone https://github.com/amadad/mirofish-cli` | Day 1 PM |
| **P1** | Test manual Mirofish run | Backend Engineer | CLI returns `verdict.json` without errors | Day 1 EOD |
| **P2** | Generate data audit report | Data Lead | Report on 10 sample KOLs, completeness percentages | Day 2 AM |
| **P2** | Validate Supabase field availability | Data Lead | All MMIS1 Section 2.1 fields confirmed available | Day 2 AM |
| **P2** | Get Claude API access | Engineering Lead | API key generated, billing configured | Day 2 PM |
| **P3** | Identify 5 pilot clients | Sales Lead | Client list with contact info, incentive offer ready | Day 3 AM |
| **P3** | Set up project tracking | Project Manager | GitHub Projects or Linear configured | Day 3 PM |
| **P3** | Schedule weekly check-in ritual | Project Manager | Recurring meeting, standing agenda template | Day 3 PM |

### Day 1-3 Decision Gates

| Gate | Question | Pass Criteria | Owner |
|------|----------|---------------|-------|
| **DG-1** | Are critical resources allocated? | Technical lead assigned, budget approved | Executive |
| **DG-2** | Is data quality acceptable? | >95% field completeness for required fields | Data Lead |
| **DG-3** | Is Mirofish technically viable? | Manual test produces valid output | Engineering |

**If any gate FAILS:** Pause and resolve before Day 4. Do not proceed to Week 1 development.

---

## 4. Stages 1-5 Detailed Execution

### STAGE 1: Infrastructure Foundation (Weeks 1-2)

#### Week 1: Deployment

| Day | Task | Technical Spec | Owner | Validation |
|-----|------|----------------|-------|------------|
| Mon | Provision compute resources | AWS ECS or GCP Cloud Run, 4 vCPU, 16GB RAM | DevOps | Console shows RUNNING status |
| Mon-Tue | Create Dockerfile | Python 3.11, poetry/pip dependencies | Backend | `docker build` succeeds |
| Tue | Configure storage | S3 bucket `mirofish-artifacts-prod` | DevOps | Bucket created, IAM policy applied |
| Tue-Wed | Deploy Redis queue | ElastiCache or Cloud Memorystore | DevOps | `redis-cli ping` returns PONG |
| Wed-Thu | Configure Celery workers | 2 worker nodes, task routing | Backend | Tasks enqueue and process |
| Thu-Fri | Deploy Mirofish container | ECS service, load balancer | DevOps | Health check endpoint returns 200 |
| Fri | **Week 1 Gate** | Infrastructure accessible | Team Lead | `curl /health` returns 200 |

#### Week 2: Connectivity

| Day | Task | Technical Spec | Owner | Validation |
|-----|------|----------------|-------|------------|
| Mon | Design `KOLPredictiveEngine` class | See MMIS1 Section 1.2.2 | Backend | Interface defined, imports work |
| Mon-Tue | Build Supabase client | `supabase-py`, connection pooling | Backend | 100 concurrent connections test |
| Tue-Wed | Implement data fetcher | Query `kols`, `kol_authorships`, `trial_investigators` | Backend | Returns structured KOL object |
| Wed-Thu | Build seed document generator | JSON schema per MMIS1 | Backend | Schema validates, content complete |
| Thu | Integrate Mirofish API call | POST to internal Mirofish, timeout handling | Backend | Returns prediction object |
| Fri | End-to-end test | Sample KOL ID → full prediction → output | Team | Console log shows full pipeline |
| Fri | **Stage 1 Complete** | Infrastructure + bridge operational | Team Lead | Demo successful |

**Stage 1 Success Criteria:**
- Mirofish API accessible at `mirofish.internal.meddash.ai`
- Supabase → Mirofish data flow working
- Sample KOL produces prediction end-to-end

---

### STAGE 2: Quantification Engine (Weeks 3-4)

#### Week 3: Calculator Implementation

| Component | Implementation Task | Formula Reference | Owner |
|-----------|----------------------|-------------------|-------|
| **EPS** | Build 5-component calculator | MMIS1 Section 2.4.1 | Backend |
| **RWPS** | Exponential decay for publications | `Σ(pubs × e^(-days/365))` | Backend |
| **Network Centrality** | Graph analysis with NetworkX | Betweenness centrality | Backend |
| **Recency Factor** | 90d/365d activity ratio | Timestamp calculation | Backend |
| **COI Scoring** | Conflict flag calculations | `biotech_associated_kols` | Backend |

#### Week 4: Validation & Tuning

| Activity | Method | Success Criteria |
|----------|--------|------------------|
| Calculate EPS for 100 KOLs | Batch script | All scores 0.00-1.00, no NaN |
| Business sense check | Human review top/bottom 10 | Scores align with intuition |
| Manual verification | Spot check 5 calculations | Formula implementation correct |
| Temporal table setup | Create `metrics_timeseries` | Daily automated updates working |
| Transparency layer | Component breakdown display | Hover shows 5 factor contributions |

**Stage 2 Success Criteria:**
- EPS calculated on 100+ KOLs
- Scores make business sense (validated by medical affairs advisor)
- Temporal tracking shows trends (↑, →, ↘)
- Component-level transparency operational

---

### STAGE 3: Simulation Context Builder (Weeks 5-6)

#### Week 5: Templates & Scenarios

| Scenario Template | Variables | Mirofish Output |
|-------------------|-----------|-----------------|
| **Advisory Board Recruitment** | Budget, format, timing, competitors | Likelihood + approach |
| **Message Testing** | Message text, target audience, timing | Resonance score |
| **Publication Planning** | Journal, authorship, competition | Acceptance probability |
| **Congress Engagement** | Congress, session type, commitments | Availability |
| **Crisis Management** | Event type, sentiment baseline | Reaction prediction |

#### Week 6: Context Enrichment

| Data Source | Integration Method | Update Frequency |
|-------------|-------------------|------------------|
| Competitive landscape | LinkedIn scraping + manual research | Daily |
| TA sentiment | PubMed trend analysis | Weekly |
| Congress cycles | Database of oncology conferences | Static + annual update |
| Funding climate | Crunchbase/TechCrunch API | Monthly |

**Stage 3 Success Criteria:**
- 5 scenario templates operational
- Seed documents include competitive context
- Market context automatically enriched
- Mirofish generates predictions with full context

---

### STAGE 4: Decision Interpretation Layer (Weeks 7-8)

#### Week 7: Translation Engine

| Raw Mirofish Output | Decision Translation | Display |
|---------------------|----------------------|---------|
| "73% confidence, 4 signals" | "High Priority - Deploy senior MSL within 5 days" | Priority badge |
| "Peak receptivity: Day 12-14" | "Optimal outreach: Week of May 18" | Calendar highlight |
| "Academic appeal signal strong" | "Emphasize publication opportunity" | Recommended approach |
| "Competitor engagement detected" | "Urgency escalation - Competitor X active" | Alert banner |

#### Week 8: Failure Modes & Optimization

| Prediction Type | If Fails (Negative Outcome) | Likely Cause | Adjustment |
|-----------------|---------------------------|--------------|------------|
| Engagement Likely (75%) | KOL non-responsive | Undisclosed COI, competitive lock-in | Update COI monitoring, check exclusives |
| Message Resonance (68%) | Poor reception | Message-framing mismatch | A/B test alternatives |
| Trial Enrollment (82%) | Under-enrollment | Site staffing, competing trials | Real-time monitoring, alert at 80% |

**Optimization Loop:**
```
Prediction → MSL Feedback (1-click: success/failure + reason) → 
  ↓
Weight Adjustment (weekly auto-backtest) → 
  ↓
Accuracy Recalculation → Client Notification
```

**Stage 4 Success Criteria:**
- Non-technical user (sales/operations) interprets prediction without guidance
- Failure mode framework documents 5 common scenarios
- Feedback collection widget in MSL dashboard
- Historical accuracy visible ("Similar predictions: 12/14 correct")

---

### STAGE 5: Output Integration (Weeks 9-10)

#### Week 9: Product Generation

| Deliverable | Specification | Owner |
|-------------|-------------|-------|
| Enhanced PDF Template | 7 sections (See MMIS1 1.6.1) | Product Design |
| MSL Dashboard Priority Queue | EPS × Urgency ranking | Frontend |
| Accuracy Tracker Widget | Prediction vs. outcome graph | Frontend |
| Cascade Simulator | Interactive network graph (D3.js) | Frontend |
| API Documentation | OpenAPI spec for `/v2/kol-briefs/predictive` | Backend |

#### Week 10: Launch

| Activity | Details | Owner |
|----------|---------|-------|
| Pilot client outreach | 5 pre-identified clients | Sales Lead |
| Brief generation | Generate 5 enhanced briefs | Sales + Engineering |
| Feedback collection | Structured interview questions | Product Manager |
| Pricing update | Website: $4,500 tier, sales materials | Marketing |
| Announcement | "Predictive Intelligence Beta" | Communications |

**Stage 5 Success Criteria:**
- Enhanced PDF generates automatically for any KOL
- MSL dashboard widgets populated with real data
- 5 pilot clients using briefs
- Revenue tracking active, first $4,500 invoice sent

---

## 5. Data Architecture & Dependencies

### Required Data Sources (Priority Order)

| Priority | Source | Current Status | Implementation | Week |
|----------|--------|---------------|------------------|------|
| **P0** | Supabase `kols` table | ✅ Available | Direct query | 1-2 |
| **P0** | Supabase `kol_authorships` | ✅ Available | Join query | 1-2 |
| **P0** | Supabase `trial_investigators` | ✅ Available | Join query | 1-2 |
| **P1** | Twitter/X Academic API | ❌ Missing | API integration | 2-3 |
| **P1** | Conference abstract scraper | ⚠️ Manual | Selenium/scrapy | 4-5 |
| **P2** | MSL CRM outcomes | ⚠️ Partial | Salesforce API | 6-8 |
| **P2** | LinkedIn activity | ❌ Missing | Scraping (compliance check) | 8-10 |

### Data Quality Checkpoints

| Checkpoint | Frequency | Action if Failed |
|------------|-----------|------------------|
| Completeness | Daily | Alert if <95% required fields |
| Validity | Weekly | Manual review of outliers |
| Consistency | Weekly | Cross-reference with external sources |
| Timeliness | Daily | Flag data >30 days stale |

### Dependency Map

```
Mirofish API ──┐
               ├──→ KOLPredictiveEngine ──→ Enhanced Brief
Supabase ──────┤             ↑
               │      Quantification Engine
Twitter ───────┤    (EPS, RWPS, Centrality)
               │             ↑
Conference ────┴──────────────┘
 abstracts
```

---

## 6. Quality Gates & Success Criteria

### Phase 1 Quality Gates

| Gate | Location | Criteria | Pass Indicator |
|------|----------|----------|----------------|
| **G1** | End Week 2 | Infrastructure operational | `curl /health` = 200 |
| **G2** | End Week 4 | EPS validated | 100 KOLs scored, business sense confirmed |
| **G3** | End Week 6 | Seeds complete | 5 scenarios with full context |
| **G4** | End Week 8 | Decisions clear | Non-tech user validates |
| **G5** | End Week 10 | Product live | 5 pilot clients active |

### Success Metrics Dashboard

| Metric | Target | Measurement | Frequency |
|--------|--------|-------------|-----------|
| **Prediction Accuracy** | >65% | MSL feedback vs. prediction | Weekly |
| **Client Decision Confidence** | NPS >80 | Post-brief survey | Monthly |
| **Time-to-Decision** | -30% | Compare to baseline | Monthly |
| **Generation Time** | <5 min | Timer per brief | Per generation |
| **System Uptime** | >99% | Monitoring | Continuous |
| **SaaS Conversion** | 40% | Brief buyers → platform | Quarterly |
| **Revenue per Brief** | $4,500 | Pricing adherence | Monthly |
| **MSL Feedback Rate** | >50% | Outcome reporting | Weekly |

### Risk Flags

| Flag | Condition | Response |
|------|-----------|----------|
| **YELLOW** | Accuracy 55-60% | Review weights, add training data |
| **RED** | Accuracy <55% | Pause predictions, investigate failure modes |
| **YELLOW** | Feedback rate 30-50% | Add incentives, simplify reporting |
| **RED** | Feedback rate <30% | Mandatory outcome reporting |

---

## 7. Risk Management

### Risk Register

| Risk ID | Risk | Likelihood | Impact | Mitigation | Owner |
|---------|------|------------|--------|------------|-------|
| **R1** | Mirofish API instability | Medium | High | Fallback rule-based EPS | Backend |
| **R2** | Claude API rate limiting | Medium | High | Batch requests, retry logic | Backend |
| **R3** | Data quality issues | Medium | High | Validation rules, manual review queue | Data |
| **R4** | Client over-Expectation | High | Medium | Clear disclaimers, "informs not replaces" | Product |
| **R5** | Technical lead unavailable | Low | Critical | Cross-train backup, documentation | CTO |
| **R6** | Competitor launches similar | Medium | Medium | Speed-to-market, data moat | Executive |
| **R7** | Pilot client churn | Medium | High | Close CS partnership, iterate fast | Sales |

### Contingency Plans

**If Mirofish fails:**
- Activation: Week 2 if instability persists
- Fallback: Rule-based EPS using weighted formula (MMIS1 2.4.1) without simulation
- Impact: Reduced accuracy target to 55-60%, still defensible vs competitors

**If data quality insufficient:**
- Activation: Week 1-2 if audit shows <90% completeness
- Fallback: Manual data enrichment for pilot clients
- Impact: Increased cost, delayed launch by 1-2 weeks

**If pilot clients reject pricing ($4,500):**
- Activation: Week 9 after pricing validation
- Fallback: Price at $3,500 (base + $1,000 premium)
- Impact: Lower margin, higher volume strategy

---

## 8. Team & Resource Assignment

### Required Roles

| Role | Allocation | Responsibilities | Duration |
|------|-----------|------------------|----------|
| **Technical Lead** | 75%+ | Architecture, code review, integration | Full duration |
| **Backend Engineer** | 50% | Mirofish integration, API, calculations | Weeks 1-6 |
| **Frontend Engineer** | 50% | Dashboard widgets, visualization | Weeks 5-10 |
| **Data Engineer** | 25% | Data validation, quality, enrichment | Weeks 1-4, 7-8 |
| **DevOps Engineer** | 25% | Infrastructure, CI/CD, monitoring | Weeks 1-2, 10 |
| **Product Manager** | 50% | Requirements, validation, stakeholder mgmt | Full duration |
| **Medical Affairs Advisor** | 10% | Business sense validation, clinical context | Weeks 4, 8, 10 |
| **Sales Lead** | 10% | Pilot client relationships | Weeks 1, 9-10 |

### Weekly Time Estimate

| Phase | Engineering | Product | Total Effort |
|-------|-------------|---------|--------------|
| Weeks 1-2 | 80 hours | 20 hours | 100 hours |
| Weeks 3-4 | 60 hours | 30 hours | 90 hours |
| Weeks 5-6 | 60 hours | 30 hours | 90 hours |
| Weeks 7-8 | 50 hours | 40 hours | 90 hours |
| Weeks 9-10 | 40 hours | 50 hours | 90 hours |
| **Total** | **290 hours** | **170 hours** | **460 hours** |

### Cost Estimation

| Category | Item | Cost |
|----------|------|------|
| **Personnel** | ~460 hours @ blended $150/hr | $69,000 |
| **Infrastructure** | AWS/GCP (10 weeks) | $2,000 |
| **3rd Party APIs** | Claude API + Twitter/X Academic | $1,500 |
| **Tools** | Datadog, Sentry, etc. | $1,000 |
| **Total** | | **$73,500** |

---

## 9. Client Pilot Program

### Pilot Client Selection Criteria

| Criteria | Weighting | Why It Matters |
|----------|-----------|----------------|
| **Data Availability** | 30% | Client must have rich KOL relationship history |
| **Feedback Willingness** | 25% | Willing to provide detailed outcome feedback |
| **High-Touch Culture** | 20% | Values intelligence over cost savings |
| **Growth Potential** | 15% | Likely to expand to SaaS subscription |
| **Reference Potential** | 10% | Willing to be case study |

### Pilot Program Structure

| Phase | Duration | Deliverable | Feedback Required |
|-------|----------|-------------|-------------------|
| **Kickoff** | Week 1-2 | Onboarding, expectations setting | Baseline questionnaire |
| **Generation** | Week 3-4 | 5 enhanced briefs delivered | Quality review |
| **Use Phase** | Week 5-8 | Client uses briefs for actual engagements | Weekly outcome reports |
| **Review** | Week 9-10 | Retrospective, testimonials | Structured interview |

### Pilot Incentives

| Incentive | Value | Rationale |
|-----------|-------|-----------|
| **Pricing** | $3,000 (vs $4,500) | Beta discount for feedback |
| **Feature Input** | Direct roadmap influence | Builds engagement |
| **White-glove Service** | Dedicated Slack channel | Premium support |
| **Success Bonus** | If predictions accurate, 20% credit | Performance alignment |

### Success Criteria by Pilot Client

| Client | Success Looks Like | Measures |
|--------|-------------------|----------|
| **Client A** (Large Pharma) | MSLs report predictions 85%+ accurate | Feedback survey |
| **Client B** (Mid-Stage) | Used briefs for 3+ successful engagements | Usage tracking |
| **Client C-G** | Willing to purchase ongoing SaaS subscription | Intent signals |

---

## 10. Appendices

### Appendix A: Reference Documents

| Document | Location | Purpose |
|----------|----------|---------|
| MMIS1 (Technical Blueprint) | `/a0/usr/ceo-files/mirofish-meddash-integration_step_1.md` | Detailed technical specifications |
| Strategic Bridge | `/a0/usr/ceo-files/mirofish_meddash-cq_bridge.md` | Market strategy, competitive analysis |
| Complete Business Plan | `MEDDASH_COMPLETE_BUSINESS_PLAN_2026.md` | Full MedDash business plan |
| GTM Strategy | `MEDDASH_GTM_STRATEGY_...` | Go-to-market details |

### Appendix B: API Specifications

```yaml
# POST /v2/kol-briefs/predictive
# Request
{
  "kol_ids": ["uuid-1", "uuid-2"],
  "client_context": {
    "therapeutic_area": "oncology-nsclc",
    "drug_mechanism": "pd1-inhibitor",
    "engagement_urgency": "high"
  },
  "prediction_scope": {
    "engagement_likelihood": true,
    "influence_cascade": true,
    "timeline_prediction": "30-days"
  }
}

# Response
{
  "brief_id": "mb-uuid",
  "brief_url": "https://...",
  "predictions": {
    "engagement_likelihood": {
      "score": 0.82,
      "confidence": "high",
      "decision": "Immediate Priority",
      "reasoning": ["RWPS ↑15%", "Network central", "No COI"]
    }
  },
  "generation_time_seconds": 287
}
```

### Appendix C: Glossary

| Term | Definition |
|------|------------|
| **MMIS** | Mirofish-MedDash Integration Steps |
| **EPS** | Engagement Probability Score (0.00-1.00) |
| **RWPS** | Recency-Weighted Publication Score |
| **ELS** | Engagement Likelihood Score (priority classification) |
| **ICP** | Influence Cascade Potential |
| **COI** | Conflict of Interest |
| **MSL** | Medical Science Liaison |
| **TA** | Therapeutic Area |

### Appendix D: Decision Matrix

**When to use which prediction?**

| Client Question | Use Prediction | Output Format | Section |
|---------------|---------------|---------------|---------|
| "Should I prioritize this KOL?" | EPS + ELS | Priority badge | Executive Summary |
| "When should I contact them?" | Optimal Window | Calendar highlight | Timeline |
| "Will my message resonate?" | Message Resonance | Recommended approach | Strategy |
| "Are competitors approaching?" | Competitive Threat | Alert banner | Risk Factors |
| "Who else will follow?" | Cascade Potential | Network graph | Cascade Map |

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | April 16, 2026 | Agent Zero | Initial creation, MMIS1 operational translation |

**Distribution:** Executive Team, Product Lead, Technical Lead, Sales Lead  
**Review Cycle:** Weekly during implementation  
**Next Review:** Week 1 Checkpoint (Friday)

---

**END OF DOCUMENT**

*This MMIS2 operational handbook transforms the MMIS1 technical blueprint into day-by-day executable tasks. Print and track progress weekly.*
