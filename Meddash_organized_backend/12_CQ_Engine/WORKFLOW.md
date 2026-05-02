# CQ Engine — Workflow & Pipeline Detail

**Created:** 2026-05-01  
**Revised:** 2026-05-01 15:57 UTC (v2 — dual-path architecture + Nemotron + revised polling)  
**Status:** BUILD READY

---

## Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                   CQ UNIFIED DUAL-PATH ENGINE                       │
│         edgartools · Nemotron-3-super · Supabase                    │
│         Hourly (market) · 12-hour (off-market)                      │
└─────────────────────────────────────────────────────────────────────┘

  TICKER SPINE (13,257 biotech tickers, CIK-mapped, in Supabase)
         │
         ▼
  ┌──────────────────────────────────────┐
  │  STEP 0: GLOBAL MONITOR              │
  │  SEC EDGAR "Latest Filings" feed     │
  │  Pull latest 100 filings in one req  │
  │  Filter against biotech_tickers      │
  │  Dedup: skip known accession_numbers  │
  │  Route by form type:                 │
  │    Form 4  → Path B                  │
  │    8-K    → Path A                   │
  │    Other  → Skip                     │
  └──────────────┬───────────────────────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
  ┌──────────────┐  ┌──────────────────────────────┐
  │  PATH B      │  │  PATH A                       │
  │  Form 4      │  │  8-K Catalyst Extraction      │
  │  INSIDER     │  │  (Reasoning Path)              │
  │  TRADES      │  │                                │
  │  (Zero AI)  │  │  filing.markdown()             │
  │              │  │  → Section splice (8.01, 7.01, │
  │ filing.obj() │  │    5.02, EX-99.1)             │
  │ .transactions│  │  → Truncate ~4000 chars       │
  │ → DataFrame  │  │  → Nemotron-3-super (Ollama)  │
  │ → Filter 'P' │  │  → Strict JSON schema         │
  │ → Extract    │  │  → Binary gate + validation   │
  │   name, date,│  │  → PDUFA date computation     │
  │   shares,    │  │    (accept + 6/10 months)     │
  │   price      │  │                                │
  └──────┬───────┘  └──────────────┬───────────────┘
         │                         │
         ▼                         ▼
  ┌──────────────┐  ┌──────────────────────────────┐
  │  SUPABASE   │  │  SUPABASE                     │
  │  cq_insider │  │  cq_catalysts                  │
  │  _trades    │  │  (dedup on accession_number)  │
  └──────┬───────┘  └──────────────┬───────────────┘
         │                         │
         └──────────┬──────────────┘
                    ▼
         CQ-Selector (Paperclip) reads both tables
         → Drafts newsletter → Dr. Don publishes
```

---

## Step 0 Detail — GLOBAL MONITOR

### Source
- SEC EDGAR "Latest Filings" RSS/Atom feed
- URL: `https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=&output=atom`
- Alternative: `edgar` Python package provides `get_latest_filings()` or similar
- One pull gets the latest 100 filings across ALL companies — no per-ticker queries

### Ticker Filtering
- At startup, load the biotech watchlist from Supabase:
  ```sql
  SELECT ticker, cik, company_name FROM biotech_tickers
  WHERE cik IS NOT NULL AND is_biotech = true AND is_active_listing = true
  ```
- For each filing in the feed, extract the CIK or ticker
- Match against the watchlist — skip any filing not in the watchlist
- This eliminates 95%+ of filings (most SEC filings are non-biotech)

### Dedup
- Before processing, check if the filing's `accession_number` already exists in:
  - `cq_catalysts` (for 8-K)
  - `cq_insider_trades` (for Form 4)
- If already processed, skip

### Form Router
| Form Type | Route | Reason |
|-----------|-------|--------|
| 4 | Path B (Deterministic) | Form 4 data is structured XML — no LLM needed |
| 8-K | Path A (Reasoning) | 8-K text is unstructured — LLM classification required |
| 10-K, 10-Q, 3, 5 | Skip | Not in scope for this build (deferred) |

### Polling Schedule
- **NY Market Hours (Mon–Fri 09:30–16:00 ET / 13:30–20:00 UTC):** HOURLY
- **Off-Market & Weekends:** EVERY 12 HOURS
- Enforced by the caller (n8n schedule trigger or cron), NOT by the script itself
- Script is stateless — it runs, processes, exits

### SEC Compliance
- `set_identity("Clinical Quant contact@meddash.ai")` MUST be called before any EDGAR request
- SEC requires a User-Agent identifying the requester
- Rate limit: 10 requests/second (SEC mandates 0.1s minimum between requests)
- No API key required — EDGAR is a public API

---

## Path B Detail — FORM 4 INSIDER TRADES (Deterministic)

### Why No LLM?
Form 4 filings are structured XML with standardized fields. The data is already tabular — transaction code, shares, price, date, insider name. An LLM would add nothing and introduce hallucination risk. This path is 100% Python code.

### edgartools Method
```python
filing = get_filing(accession_number)
form4 = filing.obj()  # Returns Form4 object
transactions = form4.transactions  # DataFrame of non_derivative_transactions
purchases = transactions[transactions['transaction_code'] == 'P']
```

### Extraction Logic
For each row in the filtered DataFrame:
| Field | Source | Transformation |
|-------|--------|---------------|
| `insider_name` | Reporting person field | Direct string |
| `transaction_date` | Transaction date field | Parse to DATE |
| `shares_amount` | Shares acquired field | Integer |
| `price_per_share` | Price field | Numeric (nullable — not always reported) |
| `ticker` | Filing CIK → biotech_tickers match | Lookup |
| `accession_number` | Filing metadata | String (unique) |
| `filing_url` | SEC EDGAR URL | Direct URL |

### Transaction Code Filter
Only `transaction_code == 'P'` (open market purchases) are captured. These are the most informative:
- `'P'` = Purchase (informative — insider is buying with their own money)
- Ignored: `'S'` (sale), `'G'` (gift), `'M'` (option exercise), `'F'` (payment), `'J'` (other)

### Supabase Write
```python
for _, row in purchases.iterrows():
    existing = supabase.table('cq_insider_trades').select('accession_number') \
        .eq('accession_number', accession_no).execute()
    if existing.data:
        continue  # dedup
    supabase.table('cq_insider_trades').insert({
        'ticker': ticker,
        'company_name': company_name,
        'accession_number': accession_no,
        'insider_name': row['reporting_name'],
        'transaction_date': row['transaction_date'],
        'shares_amount': int(row['shares_amount']),
        'price_per_share': float(row['price']) if row.get('price') else None,
        'filing_url': filing_url,
    }).execute()
```

---

## Path A Detail — 8-K CATALYST EXTRACTION (Reasoning)

### Why LLM?
8-K filings contain unstructured natural language. PDUFA dates, drug names, and indications are embedded in paragraphs with varied formatting. Regex or keyword matching fails on:
- Varied sentence structures ("PDUFA goal date of", "target action date", "FDA deadline")
- Missing explicit dates that must be computed from acceptance dates
- Distinguishing a real catalyst from routine corporate noise (address changes, auditor switches)

A reasoning model (Nemotron-3-super) cross-references context before outputting a classification, reducing wrong-date hallucination.

### Step A1 — Convert to Markdown
```python
filing = get_filing(accession_number)
md_text = filing.markdown()
```

- `edgartools` provides `.markdown()` which converts SEC HTML to clean structured text
- Handles boilerplate stripping automatically — no manual BeautifulSoup needed for primary path
- BeautifulSoup remains as **fallback** if `filing.markdown()` fails or returns empty

### Step A2 — Section Splicing
Parse the markdown output to extract only relevant Items:

| Item | Content | Why Extract |
|------|---------|-------------|
| Item 8.01 | Other Events | Clinical trial results, FDA decisions, PDUFA date announcements |
| Item 7.01 | Regulation FD | Investor decks, conference presentations, forward-looking statements |
| Item 5.02 | Compensatory Arrangements | CEO/CMO/CRO changes — leadership signal in biotech |
| Exhibit 99.1 | Press Release | Often contains the actual PDUFA/CRL/approval letter text |

Splicing logic:
```
1. Split markdown by "Item" headers
2. Extract text for Items 8.01, 7.01, 5.02
3. Extract EX-99.1 exhibit text
4. Concatenate relevant sections
5. Truncate to ~4000 chars (Nemotron context budget)
6. If no relevant Items found → skip filing (avoid wasting LLM cycles)
```

### Step A3 — LLM Classification (Nemotron-3-super)

**Endpoint:** `http://172.23.61.64:11434/api/generate`  
**Model:** `nemotron-3-super`

**System Prompt (Strict Schema):**
```
You are a biotech catalyst classifier. Read the following SEC 8-K filing excerpt.
Determine if it describes a biotech catalyst event. If yes, classify it.

Catalyst types: PDUFA, AdCom, Phase 1 Data, Phase 2 Data, Phase 3 Data,
                Interim Analysis, CRL, FDA Approval, M&A, Partnering, Offering

Output JSON only. Schema:
{
  "is_catalyst": true or false,
  "event_type": "one of the types above" or null,
  "catalyst_date": "YYYY-MM-DD" or null,
  "drug_name": "string" or null,
  "indication": "string" or null,
  "source_sentence": "the exact sentence from the filing that contains the catalyst event"
}

Rules:
- is_catalyst = true ONLY if the filing describes a specific biotech event.
- Routine corporate filings (address changes, auditor changes, insider sales, name changes) are NOT catalysts.
- If the PDUFA date is not explicitly stated but the NDA acceptance date is, compute:
  Standard Review: acceptance_date + 10 months
  Priority Review: acceptance_date + 6 months
- The source_sentence must be a direct quote from the filing text, not a paraphrase.
```

### Two-Step Filter (No Arbitrary Thresholds)

| Step | Check | Action |
|------|-------|--------|
| **1. LLM binary gate** | `is_catalyst == true`? | If false, skip the filing entirely. |
| **2. Validation rules** | Deterministic Python checks | `event_type` must be in known enum. `catalyst_date` (if not null) must parse to valid date. `ticker` must exist in biotech_tickers. |

No confidence_score. No 0.6 threshold. Binary gate + deterministic validation.

Known event_type enum:
```python
VALID_EVENT_TYPES = [
    'PDUFA', 'AdCom', 'Phase 1 Data', 'Phase 2 Data',
    'Phase 3 Data', 'Interim Analysis', 'CRL', 'FDA Approval',
    'M&A', 'Partnering', 'Offering'
]
```

A null `catalyst_date` with `is_catalyst=true` is still written — better to have a PDUFA event with a missing date than to lose the event. PDUFA date computation (acceptance + 6/10 months) fills most nulls.

### PDUFA Date Computation Rule
If the LLM cannot extract a PDUFA date explicitly but the filing mentions an NDA/BLA acceptance:
- **Priority Review:** acceptance_date + 6 months
- **Standard Review:** acceptance_date + 10 months
- The LLM prompt instructs the model to compute this when possible
- Validation still checks that the computed date parses correctly

### Handling LLM Failures
| Failure Mode | Action |
|-------------|--------|
| Invalid JSON returned | Log warning, skip filing, continue |
| `is_catalyst = false` | Skip filing silently |
| LLM timeout (30s) | Log warning, skip filing, continue |
| `source_sentence` is empty | Write row but flag for manual review |
| `event_type` not in enum | Set to `'Unknown'`, still write (capture > lose) |

---

## Supabase Write Detail

### Table: `cq_catalysts` (Path A output)

```sql
CREATE TABLE public.cq_catalysts (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker           VARCHAR(10) NOT NULL,
    company_name     TEXT,
    accession_number VARCHAR(20) NOT NULL,
    filing_type      VARCHAR(10) NOT NULL,        -- '8-K', '10-K', '10-Q'
    event_type       VARCHAR(20) NOT NULL,          -- PDUFA, AdCom, Phase 3 Data, CRL, M&A...
    catalyst_date    DATE,                          -- ISO format, nullable
    drug_name        TEXT,
    indication       TEXT,
    source_sentence  TEXT,                           -- exact quote from filing for manual verification
    filing_url       TEXT,                           -- SEC EDGAR link
    created_at       TIMESTAMPTZ DEFAULT now()
);

CREATE UNIQUE INDEX idx_cq_catalysts_accession ON public.cq_catalysts (accession_number);
CREATE INDEX idx_cq_catalysts_ticker ON public.cq_catalysts (ticker);
CREATE INDEX idx_cq_catalysts_event_type ON public.cq_catalysts (event_type);
CREATE INDEX idx_cq_catalysts_catalyst_date ON public.cq_catalysts (catalyst_date DESC);
```

### Insert Logic (Path A)
```python
# Dedup check
existing = supabase.table('cq_catalysts').select('accession_number') \
    .eq('accession_number', accession_no).execute()
if existing.data:
    continue  # skip duplicate

# Validate event_type
valid_event_types = ['PDUFA', 'AdCom', 'Phase 1 Data', 'Phase 2 Data',
                    'Phase 3 Data', 'Interim Analysis', 'CRL', 'FDA Approval',
                    'M&A', 'Partnering', 'Offering']
if result.get('event_type') not in valid_event_types:
    result['event_type'] = 'Unknown'

supabase.table('cq_catalysts').insert({
    'ticker': ticker,
    'company_name': company_name,
    'accession_number': accession_no,
    'filing_type': '8-K',
    'event_type': result['event_type'],
    'catalyst_date': result.get('catalyst_date'),  # null is OK
    'drug_name': result.get('drug_name'),
    'indication': result.get('indication'),
    'source_sentence': result.get('source_sentence'),
    'filing_url': filing_url,
}).execute()
```

### Table: `cq_insider_trades` (Path B output)

```sql
CREATE TABLE public.cq_insider_trades (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker           VARCHAR(10) NOT NULL,
    company_name     TEXT,
    accession_number VARCHAR(20) NOT NULL,
    insider_name     TEXT NOT NULL,
    transaction_date DATE NOT NULL,
    shares_amount    INTEGER,
    price_per_share  NUMERIC,                       -- nullable (not always reported)
    filing_url       TEXT,
    created_at       TIMESTAMPTZ DEFAULT now()
);

CREATE UNIQUE INDEX idx_cq_insider_trades_accession ON public.cq_insider_trades (accession_number);
CREATE INDEX idx_cq_insider_trades_ticker ON public.cq_insider_trades (ticker);
CREATE INDEX idx_cq_insider_trades_date ON public.cq_insider_trades (transaction_date DESC);
```

### Insert Logic (Path B)
```python
existing = supabase.table('cq_insider_trades').select('accession_number') \
    .eq('accession_number', accession_no).execute()
if existing.data:
    continue  # dedup

supabase.table('cq_insider_trades').insert({
    'ticker': ticker,
    'company_name': company_name,
    'accession_number': accession_no,
    'insider_name': row['reporting_name'],
    'transaction_date': row['transaction_date'],
    'shares_amount': int(row['shares_amount']),
    'price_per_share': float(row['price']) if row.get('price') else None,
    'filing_url': filing_url,
}).execute()
```

---

## Validation Targets

The pipeline must correctly detect these known upcoming catalysts:

| Date | Ticker | Event | Drug |
|------|--------|-------|------|
| May 10, 2026 | ARGX | PDUFA | VYVGART (Immune Thrombocytopenia) |
| May 10, 2026 | CYTK | Data Readout | Omecamtiv Mecarbil (Ph3 COMET-HF) |
| May 31, 2026 | CING | PDUFA | CTx-1301 (ADHD) |
| Jun 5, 2026 | ARVN | PDUFA | Vepdegestrant (Breast Cancer) |
| H1 2026 | AKRO | Data Readout | Efruxifermin (NASH/MASH) |
| H1 2026 | QTTB | Data Readout | Bempikibart (Alopecia Areata) |

Path B validation: find a known Form 4 insider purchase for any biotech ticker and verify deterministic extraction produces correct fields.

---

## Tables RETAINED (Meddash-owned, DO NOT ALTER)

| Table | Owner | Purpose |
|-------|-------|---------|
| `biotech_tickers` | Meddash Ticker Spine | 13,257 tickers with CIK, exchange, company name |
| `biotech_ticker_aliases` | Meddash Ticker Spine | Normalized company name aliases |
| `biocrawler_ticker_matches` | Meddash BioCrawler | Reverse-match bridge BioCrawler→ticker |
| `cq_market_sentiment` | Meddash | Yahoo RSS news metadata (kept, not part of catalyst pipeline) |

## Tables RETIRED (Drop or Ignore)

| Table | Reason |
|-------|--------|
| `cq_regulatory_catalysts` | Old schema — keyword-matched, no LLM, no accession_number dedup. Replaced by `cq_catalysts`. |
| `cq_market_events` | Old news link table — no LLM classification. CQ-Selector reads `cq_catalysts` now. |
| `cq_price_bars` | Empty — never had a production writer. Not needed for this phase. |
| `biotech_leads` | Legacy — pre-ticker-spine. Do not expand. |

---

## Retired Scripts Reference

| Script | Old Location | Why Retired |
|--------|-------------|-------------|
| `sec_8k_monitor.py` | `scripts/phase1_regulatory/` | Never read filing body. Keyword matching missed PDUFA dates. Replaced by edgartools + LLM. |
| `fda_pdufa_tracker.py` | `scripts/phase1_regulatory/` | Scraped WRONG page. Missed ARGX, CING, ARVN PDUFA dates. |
| `pr_wire_aggregator.py` | `scripts/phase1_regulatory/` | RSS timeouts. Keyword matching on headlines inferior to LLM on filing body. |
| `alpha_vantage_tracker.py` | `scripts/phase3_sentiment/` | Prototype. Hardcoded. No DB writes. |
| `massive_tracker.py` | `scripts/phase4_quant/` | Prototype. Mocked REST. No writer. |
| `enrich_tickers.py` | `scripts/` (DISABLED) | Fuzzy matching produced false positives. |
| `clear_inaccurate_tickers.py` | `scripts/` | One-shot cleanup. No longer needed. |

---

## Downstream Consumers

- **CQ-Selector** (Paperclip agent `31049770`): reads `cq_catalysts`, deduplicates against posted-events-log, selects top 3-5 novel catalysts
- **CQ-Researcher** (Paperclip agent `26105f52`): deep-verifies each selected catalyst
- **CQ-Monitor** (Paperclip agent `bb9deb04`): daily health check on pipeline
- **Newsletter Draft**: written to Obsidian vault by CQ-Selector → Dr. Don publishes to Substack/LinkedIn

---

## Polling Schedule Reference

| Period | Frequency | UTC Window | Trigger |
|--------|-----------|------------|---------|
| NY Market Hours (Mon–Fri) | Hourly | 13:30–20:00 | n8n Schedule Trigger → `python3 cq_engine.py` |
| Off-Market (Mon–Fri) | Every 12 hours | 20:00–13:30 next day | n8n Schedule Trigger → `python3 cq_engine.py` |
| Weekends (Sat–Sun) | Every 12 hours | 00:00 / 12:00 | n8n Schedule Trigger → `python3 cq_engine.py` |

Script is stateless — runs, processes new filings since last poll, exits. No daemon mode.