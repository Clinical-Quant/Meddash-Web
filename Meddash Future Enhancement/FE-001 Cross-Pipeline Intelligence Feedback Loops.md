# FE-001: Cross-Pipeline Intelligence Feedback Loops

> **Created:** 2026-04-26 14:15 EDT  
> **Author:** Alfred Chief  
> **Priority:** Deferred — no direct correlation to first revenue  
> **Depends on:** MDP3-SWIP2 completion, CQ pipeline running daily, Meddash pipeline running daily  
> **Revisit when:** Meddash has paying customers and CQ newsletter has 500+ subscribers

---

## Problem

CQ and Meddash pipelines run sequentially but **blind to each other**:

| Pipeline | Time | Data Source | Output | Cross-Product Signal |
|----------|------|-------------|--------|---------------------|
| CQ | 11:00 AM EST | SEC 8-K, FDA PDUFA, PR wires | Newsletter draft | None from Meddash |
| Meddash | 02:00 UTC (9PM EST) | ClinicalTrials.gov, PubMed, biotech leads | SQLite + JSON summaries | None from CQ |

Meddash-COO → CQ-COO daily report (SWIP2-D.2.2) is only a **status memo** ("pipeline ran, X KOLs, Y leads, healthy"). It does NOT close the intelligence feedback loop between products.

---

## Two Missing Feedback Loops

### Loop 1: Meddash → CQ (Upstream Priority Boost)

**Evening (9PM):** BioCrawler discovers high-priority biotech companies ( Series A fundings, breakthrough therapy designations, M&A activity).

**Morning (11AM):** CQ-Selector should prioritize those companies' catalyst events higher. Currently it doesn't — CQ-Selector scores independently.

**Data contract:** `hot_leads.json` written by Meddash pipeline to `06_Shared_Datastores/` → read by CQ-Selector next morning.

### Loop 2: CQ → Meddash (Downstream Brief Generation)

**Morning (11AM):** CQ-Selector identifies hot catalyst events (PDUFA dates, Phase readouts, FDA decisions).

**Evening (9PM):** Meddash-CTO should flag those conditions for KOL brief generation. Currently doesn't — Meddash engines follow MeSH rotation blindly.

**Data contract:** `hot_catalysts.json` written by CQ pipeline to shared datastores → read by Meddash-CTO at health-check time.

---

## Use Cases

### Daily
- **Shared outage detection**: One Supabase outage breaks both products. Coordinated response avoids duplicate escalation.
- **Resource contention alert**: If Meddash is running heavy (KOL brief generation), CQ-Selector may be slow. Heads-up prevents frustration.
- **Data spine verification**: BioCrawler feeds both products. If biotech_leads table is stale, CQ's ticker enrichment is also degraded.

### Short-term (Revenue)
- **Cross-sell signal**: Meddash sees KOL brief requests for condition X (e.g., KRAS G12C). CQ covers catalysts for same condition → newsletter becomes MORE valuable to Meddash's audience. Same buyers, reinforced signal.
- **Lead heat scoring**: CQ tracks companies with upcoming binary events. Meddash-COO gets that signal → those are hotter KOL brief prospects. A $2,450 brief on a company with a catalyst in 2 weeks sells faster than a cold lead.
- **Pre-build intelligence**: CQ reports "3 catalyst events in KRAS this week" + Meddash reports "2 KOL brief requests for KRAS" → pre-build KRAS brief template. First-mover advantage.

### Long-term (Moat)
- **Pricing power**: Correlating CQ engagement metrics (which conditions get clicks) with Meddash demand (which briefs sell) reveals exactly what to charge. High interest + high demand = premium pricing tier.
- **Product convergence**: Daily cross-reports build a dataset showing therapeutic areas with BOTH catalyst events AND KOL activity. That intersection is the defensible moat — competitors can't replicate the combined signal.
- **Anti-cannibalization**: CQ (free) might overserve a segment Meddash (paid) should monetize. Meddash might under-price something CQ data shows has high interest. Without coordination, the two products cannibalize instead of reinforce.

---

## Technical Design

### Data Contracts

```
06_Shared_Datastores/
├── hot_leads.json          # Written by Meddash pipeline (9PM), read by CQ-Selector (11AM)
│   {
│     "date": "2026-04-26",
│     "source": "biocrawler",
│     "hot_companies": [
│       {"ticker": "MRNA", "name": "Moderna", "reason": "Breakthrough therapy designation", "priority": "high"},
│       {"ticker": "LLY", "name": "Eli Lilly", "reason": "Phase 3 readout next 2 weeks", "priority": "medium"}
│     ],
│     "hot_conditions": ["KRAS G12C", "HER2 breast cancer"]
│   }
│
├── hot_catalysts.json      # Written by CQ pipeline (11AM), read by Meddash-CTO (9PM)
│   {
│     "date": "2026-04-26",
│     "source": "cq-selector",
│     "upcoming_events": [
│       {"ticker": "MRNA", "event_type": "PDUFA", "date": "2026-04-30", "condition": "RSV"},
│       {"ticker": "AZN", "event_type": "Phase 3 readout", "date": "2026-05-02", "condition": "NSCLC"}
│     ],
│     "trending_conditions": ["KRAS", "NSCLC"]
│   }
```

### Script Modifications Required

| Script | Change | Pipeline |
|--------|--------|----------|
| `biocrawler.py` | After daily run, write `hot_leads.json` with top 5 companies by priority | Meddash |
| `sec_8k_monitor.py` | After run, write `hot_catalysts.json` with upcoming binary events | CQ |
| `cq_selector.py` | Read `hot_leads.json`, boost priority score for matching tickers | CQ |
| Meddash-CTO AGENTS.md | Read `hot_catalysts.json`, flag conditions for brief generation | Meddash |
| n8n CQ workflow | After CQ-Selector, copy `hot_catalysts.json` to shared datastores | n8n |
| n8n Meddash workflow | After Health Check, write `hot_leads.json` to shared datastores | n8n |

### Tech Stack

| Component | Technology | Notes |
|-----------|-----------|-------|
| Shared data files | JSON in `06_Shared_Datastores/` | Simplest possible contract — no database needed |
| Cross-pipeline sync | n8n Code nodes | Copy/share JSON files after each pipeline completes |
| Priority boosting | CQ-Selector scoring module | Add weight multiplier for hot_leads tickers |
| Brief flagging | Meddash-CTO agent instructions | Read hot_catalysts, create brief assignment if match found |
| COO cross-report | Paperclip issue comment | Meddash-COO posts daily summary to CQ-COO via shared company |

---

## Why Deferred

1. **No direct revenue impact**: CQ is free (newsletter), Meddash is paid (briefs). The feedback loop makes both products *better* but doesn't directly generate the **first** $2,450 brief sale.
2. **First revenue path is clearer**: Dr. Don should sell KOL briefs to medical affairs teams. The Meddash pipeline running correctly (SWIP2) produces the product. Selling (GTM) produces revenue. Cross-pipeline intelligence makes a good product *great*, but a great product unsold still earns $0.
3. **Complexity tax**: Adding shared data contracts between CQ and Meddash pipelines means both sides need to agree on schema, timing, and error handling. This is coordination overhead that delays shipping.
4. **Both pipelines must be running reliably first**: Can't add intelligence feedback loops to pipelines that haven't had their first production run yet.

---

## Revisit Criteria

- Meddash has ≥1 paying customer for KOL briefs
- CQ newsletter has ≥500 subscribers
- Both pipelines have run reliably for ≥2 weeks without manual intervention
- Dr. Don has bandwidth for script modifications on both sides