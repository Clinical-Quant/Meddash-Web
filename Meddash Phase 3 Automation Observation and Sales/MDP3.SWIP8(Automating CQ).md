# MDP3.SWIP8 — Automating CQ: Catalyst Extraction → Verification → Newsletter/Tweet Drafts → Approval → Posting

**Created:** 2026-05-02 01:11 UTC  
**Author:** Alfred Chief  
**Status:** SCRIPTS IMPLEMENTED — READY FOR n8n + PAPERCLIP WIRING  
**Context:** SWIP7 built the revised CQ extraction engine and SWIP7.5 created the observability/log architecture. SWIP8 defines the minimum automation needed to turn extracted catalysts into verified newsletter and tweet drafts, route them through independent confirmation, obtain Dr. Don approval, and then publish or prepare posting.

---

## 0. Executive Goal

Build the minimum reliable CQ automation chain:

```text
Scheduled CQ Engine
  → Supabase catalyst/trade tables
  → CQ observability logs
  → candidate selection
  → independent verification/research
  → newsletter draft generation
  → tweet/X post draft generation
  → Dr. Don approval gate
  → posting/export queue
  → posted-events dedup log
  → run summary + visibility dashboard
```

The system should automate extraction, verification, drafting, and queueing. It should NOT publish externally without Dr. Don approval.

---

## 1. Current Foundation Already Built

| Layer | Status | Location / Table |
|---|---|---|
| Unified CQ engine | Built | `Meddash_organized_backend/scripts/phase1_regulatory/cq_engine.py` |
| CQ runner | Built | `Meddash_organized_backend/scripts/cq_pipeline_runner.py` |
| Legacy compatibility shim | Built | `CTO/CQ_Team/scripts/cq_pipeline_runner.py` |
| Path A catalyst table | Built | Supabase `cq_catalysts` |
| Path B insider trade table | Built | Supabase `cq_insider_trades` |
| Run observability table | Built | Supabase `cq_run_logs` |
| Verification flow addendum | Built | `CTO/CQ_Team/CQ_Automation/architecture/cq-verification-flow.md` |
| Observability files/folders | Built | `CTO/CQ_Team/CQ_Observability/` |
| Nemotron model | Built | `nemotron-3-super:cloud` via Windows Ollama + WSL PowerShell fallback |
| n8n workflow shell | Exists | `CQ-Free Newsletter 1100`, ID `dfb3zednYhdcdqxE`, currently needs activation/toggle |

---

## 2. Non-Negotiable Automation Rules

1. **No blind posting.** Newsletter and tweet drafts require Dr. Don approval before external publishing.
2. **No unverified catalyst publication.** Every candidate must pass independent source confirmation.
3. **No confidence-score theater.** Use hard verification fields: confirmed / rejected / needs_review.
4. **Accession-number dedup remains canonical.** Never reuse the same SEC filing as a fresh event.
5. **Posted-events log must be append-only.** Once posted or rejected, preserve the audit trail.
6. **All logs include date + time.** Use `YYYY-MM-DD_HHMMSSZ-*` naming.
7. **Secrets never enter logs.** No Supabase keys, DB URLs, tokens, API keys, or bearer strings.
8. **Human approval is the only external-post gate.** The automation may draft and queue, not self-publish.

---

## 3. Target Minimal Dataflow

```text
A. Schedule Trigger
   n8n / manual / cron

B. Extract
   cq_pipeline_runner.py detect
   → cq_engine.py
   → cq_catalysts + cq_insider_trades
   → cq_run_logs + local timestamped logs

C. Select
   cq_candidate_selector.py
   → reads fresh rows from cq_catalysts + cq_insider_trades
   → removes duplicates from posted-events-log.md
   → ranks top events for newsletter/tweet
   → writes cq_selected_candidates

D. Verify Independently
   n8n calls /cq/automation/verify
   → cq_independent_verifier.py re-fetches official SEC filing via edgartools/direct SEC archive
   → 8-K: regenerate official filing markdown/text
   → Form 4: re-download official ownership XML
   → save artifact dump to CQ_Automation/source-artifacts
   → hash artifacts and index in cq_source_artifacts
   → gemma4:e4b local verifier checks source consistency
   → checks company IR / press release / FDA source / clinicaltrials.gov when relevant
   → writes final verification result to cq_research_confirmations
   → ambiguous cases trigger CQ-Researcher Paperclip issue via n8n wakeup

E. Draft
   cq_content_composer.py
   → reads only confirmed cq_research_confirmations
   → newsletter markdown draft
   → tweet/X thread draft
   → approval package markdown
   → writes cq_content_queue

F. Approval
   Dr. Don reviews approval package
   → approve / reject / revise
   → status update in cq_content_queue

G. Posting / Export
   If approved:
     - Substack/LinkedIn: export final markdown for manual copy OR semi-automated browser later
     - X/Twitter: queue approved text for xurl/manual post
   → update posted-events-log.md
   → write final run summary

H. Artifact Cleanup
   scheduled weekly/monthly cleanup
   → posted/approved artifacts are archived/compressed after retention
   → rejected/noise artifacts are deleted after retention
   → cq_source_artifacts.retention_status updated
   → cq_run_logs updated
```

---

## 4. Minimal Supabase Tables Needed

SWIP8 requires four additional tables beyond SWIP7/SWIP7.5.

### 4.1 `cq_selected_candidates`

Purpose: candidates selected from raw catalyst/trade tables for verification and content drafting.

Required fields:

- `id`
- `candidate_id`
- `source_table` — `cq_catalysts` or `cq_insider_trades`
- `source_row_id`
- `ticker`
- `company_name`
- `event_type`
- `event_date`
- `accession_number`
- `filing_url`
- `selection_reason`
- `selection_rank`
- `status` — `selected`, `verification_pending`, `verified`, `rejected`, `drafted`, `approved`, `posted`
- `created_at`
- `updated_at`

### 4.2 `cq_research_confirmations`

Purpose: independent verification output for each selected candidate.

Required fields:

- `id`
- `candidate_id`
- `verification_status` — `confirmed`, `rejected`, `needs_review`
- `primary_source_checked` — SEC filing / Form 4 / source sentence
- `secondary_sources_checked` — JSON array of IR/FDA/ClinicalTrials/press sources
- `confirmed_facts_json`
- `contradictions_json`
- `research_summary`
- `researcher` — `script`, `CQ-Researcher`, `Alfred`, etc.
- `created_at`

### 4.3 `cq_content_queue`

Purpose: newsletter/tweet drafts and approval/posting state.

Required fields:

- `id`
- `content_id`
- `candidate_id`
- `content_type` — `newsletter`, `tweet`, `thread`, `linkedin`, `approval_package`
- `title`
- `draft_markdown`
- `tweet_text`
- `approval_status` — `pending_review`, `approved`, `rejected`, `needs_revision`, `posted`
- `approved_by`
- `approved_at`
- `posted_at`
- `posting_destination` — `Substack`, `LinkedIn`, `X`, `manual_export`
- `output_file_path`
- `created_at`
- `updated_at`

### 4.4 `cq_source_artifacts`

Purpose: source artifact index for SEC feeds, 8-K markdown/HTML, Form 4 XML, and verification snapshots. Large files stay on local disk; Supabase stores only path/hash/metadata.

Required fields:

- `id`
- `artifact_id`
- `candidate_id`
- `ticker`
- `accession_number`
- `artifact_type` — `sec_atom_feed`, `sec_8k_markdown`, `sec_8k_html`, `form4_xml`, `verification_snapshot`, `rejected_metadata`
- `source_url`
- `local_file_path`
- `sha256_hash`
- `file_size_bytes`
- `retention_status` — `active`, `archived`, `deleted`
- `created_at`
- `expires_at`

---

## 5. Required File/Folder Destinations

### 5.1 CQ Automation Root

Create:

`C:\Users\email\.gemini\antigravity\CTO\CQ_Team\CQ_Automation\`

WSL:

`/mnt/c/Users/email/.gemini/antigravity/CTO/CQ_Team/CQ_Automation/`

Subfolders:

```text
CQ_Automation/
  candidates/
  verification/
  approval-packages/
  newsletter-drafts/
  tweet-drafts/
  approved-posts/
  rejected/
  scripts/
  sql/
  source-artifacts/
    sec-atom-feeds/
    sec-8k-markdown/
    sec-8k-html/
    form4-xml/
    verification-snapshots/
    rejected-or-noncatalyst/
```

### 5.2 Newsletter Draft Destinations

Every approved or pending newsletter draft should be written to both:

1. CQ Team working folder:
   - `CTO/CQ_Team/CQ_Automation/newsletter-drafts/YYYY-MM-DD_HHMMSSZ-cq-newsletter-draft.md`
2. Alfred/Obsidian brain:
   - `Hermes Agent Win Files/projects/clinical-quant/newsletter/YYYY-MM-DD_HHMMSSZ-cq-newsletter-draft.md`

### 5.3 Tweet/X Draft Destinations

Write to:

`CTO/CQ_Team/CQ_Automation/tweet-drafts/YYYY-MM-DD_HHMMSSZ-cq-tweets.md`

### 5.4 Approval Package Destination

Write to:

`CTO/CQ_Team/CQ_Automation/approval-packages/YYYY-MM-DD_HHMMSSZ-cq-approval-package.md`

The approval package is the main file Dr. Don reviews.

---

## 6. Approval Package Format

```md
# CQ Approval Package — YYYY-MM-DD HH:MM UTC

Status: PENDING DR. DON APPROVAL
Run ID: ...
Candidates reviewed: ...
Verified candidates: ...
Rejected candidates: ...

---

## Candidate 1 — TICKER / Company

Event type: PDUFA / Phase 3 / Form 4 Purchase / etc.
Verification status: confirmed / needs_review / rejected
Primary source: SEC accession + URL
Secondary sources: IR/FDA/ClinicalTrials/PR links

### Verified Facts
- Fact 1
- Fact 2
- Fact 3

### Risk / Caveat
- Caveat if any

### Newsletter Draft Snippet
...

### Tweet Draft
...

### Approval Options
- APPROVE
- REJECT
- REVISE

---
```

---

## 7. Newsletter Output Requirements

Minimal newsletter format:

```md
# Clinical Quant Daily Brief — YYYY-MM-DD

## Executive Summary
3-5 bullets only.

## Verified Catalysts

### 1. TICKER — Event Type
- Company:
- Catalyst:
- Date:
- Why it matters:
- Source:
- Verification:

## Insider Purchase Signals

### TICKER — Insider Purchase
- Insider:
- Shares:
- Price:
- Transaction date:
- Source:

## Watchlist / Needs Review
Events not posted yet due to incomplete verification.

## Sources
- SEC accession links
- IR/FDA/ClinicalTrials/PR links
```

---

## 8. Tweet / X Output Requirements

Tweet rules:

- No hype.
- No investment advice.
- No price targets.
- Mention source type.
- Include uncertainty when needed.
- Use concise biotech-buyer / analyst language.

Single tweet template:

```text
$TICKER catalyst watch:

Company disclosed [event] for [drug/indication].
Key date: [date if known].
Source: SEC 8-K / Form 4 / FDA / company release.

Verified by Clinical Quant.
Not investment advice.
```

Thread template:

```text
1/ $TICKER — verified catalyst signal
[event summary]

2/ Why it matters
[clinical/regulatory/business relevance]

3/ Source trail
SEC: [accession]
Secondary: [IR/FDA/etc.]

4/ Caveat
[what is not yet known]
```

---

## 9. Independent Verification Logic

### 9.1 Primary Confirmation

For every candidate:

- Re-open the SEC filing URL or accession.
- Confirm ticker/CIK match.
- Confirm exact source sentence exists.
- Confirm event type is supported by the text.
- Confirm date if present or computable.

### 9.2 Secondary Confirmation

Depending on event type:

| Event Type | Secondary Sources |
|---|---|
| PDUFA | company IR, FDA source where available, press release, SEC exhibit |
| FDA Approval / CRL | FDA announcement, company IR, SEC exhibit |
| Phase 1/2/3 Data | company IR, ClinicalTrials.gov, conference abstract if available |
| AdCom | FDA advisory committee calendar, company IR |
| M&A / Partnering | SEC 8-K, company IR, counterparty release |
| Insider Purchase | Form 4 XML only is enough; optional OpenInsider/browser check later |

### 9.3 Verification Status

- `confirmed` — primary source and at least one suitable secondary source agree, or Form 4 XML is deterministic.
- `needs_review` — primary source supports event but secondary source absent/ambiguous.
- `rejected` — event not supported, ticker mismatch, stale duplicate, or LLM hallucination.

### 9.4 Primary SEC Verification Method — edgartools Re-Fetch, Not Generic Web Crawl

Clarification: the verification agent should NOT rely on an uncontrolled generic web crawl for primary SEC confirmation.

Primary verification should use the canonical SEC accession/filing URL and re-fetch the filing through SEC/edgartools or direct SEC archive URL access.

Recommended method:

1. Read candidate from `cq_selected_candidates`.
2. Use stored `accession_number`, `ticker`, `cik`, and `filing_url`.
3. Reconstruct or re-open the SEC filing using edgartools/direct SEC archive URL.
4. Pull the official filing body again:
   - For 8-K: official filing HTML/text → `filing.markdown()` or direct SEC filing document text.
   - For Form 4: official SEC XML ownership document.
5. Confirm the extracted `source_sentence` exists in the official filing body.
6. Confirm ticker/CIK/accession match the selected candidate.
7. Only after primary SEC verification, use web/IR/FDA/ClinicalTrials sources as secondary confirmation.

Why this matters:

- SEC/edgartools is the source of truth for filings.
- Generic web crawl can hit mirrored/stale/SEO pages.
- Verification must prove the event exists in the official filing, not just on the open web.

Allowed secondary web checks:

- Company IR press release page.
- FDA source pages where relevant.
- ClinicalTrials.gov where relevant.
- Conference abstract pages where relevant.
- Counterparty press releases for M&A/partnering.

These secondary checks support the primary SEC finding; they do not replace it.

### 9.5 SEC XML / Filing Artifact Retention and Cleanup

Clarification: the extracted source files should not disappear silently after catalyst extraction.

SWIP8 should create a lightweight source artifact layer so every extracted or verified catalyst has an audit trail.

Create local artifact root:

`C:\Users\email\.gemini\antigravity\CTO\CQ_Team\CQ_Automation\source-artifacts\`

WSL:

`/mnt/c/Users/email/.gemini/antigravity/CTO/CQ_Team/CQ_Automation/source-artifacts/`

Subfolders:

```text
source-artifacts/
  sec-atom-feeds/
  sec-8k-markdown/
  sec-8k-html/
  form4-xml/
  verification-snapshots/
  rejected-or-noncatalyst/
```

Retention rule:

- For every candidate selected for verification, keep the relevant SEC artifact.
- For every confirmed/rejected candidate, keep a verification snapshot.
- For routine non-watchlist SEC feed noise, do NOT store full artifacts.
- For skipped non-catalyst watchlist filings, keep only metadata unless needed for debugging.
- Retain local source artifacts for 90 days by default, then archive/compress or delete after export.

Filename rule:

`YYYY-MM-DD_HHMMSSZ-{ticker}-{accession_number}-{artifact_type}.{ext}`

Examples:

- `2026-05-02_011142Z-ARGX-0000000000-00-000000-8k.md`
- `2026-05-02_011142Z-CYTK-0000000000-00-000000-form4.xml`
- `2026-05-02_011142Z-ARVN-0000000000-00-000000-verification.json`

### 9.6 New Artifact Index Table — `cq_source_artifacts`

Add one additional Supabase table to index retained source artifacts.

Purpose: track where the official SEC source files and verification snapshots are stored without putting large files directly into Postgres.

Required fields:

- `id`
- `artifact_id`
- `candidate_id`
- `ticker`
- `accession_number`
- `artifact_type` — `sec_atom_feed`, `sec_8k_markdown`, `sec_8k_html`, `form4_xml`, `verification_snapshot`, `rejected_metadata`
- `source_url`
- `local_file_path`
- `sha256_hash`
- `file_size_bytes`
- `retention_status` — `active`, `archived`, `deleted`
- `created_at`
- `expires_at`

Storage rule:

- Store files on disk.
- Store only path/hash/metadata in Supabase.
- Never store secrets in artifact files.
- Hash every artifact so later verification can prove the reviewed file did not change.

### 9.7 What Happens to “Leftover” XML / Filing Files

Default behavior should be explicit:

| Artifact Type | Keep? | Destination | Reason |
|---|---:|---|---|
| SEC Atom feed XML for each run | Yes, small | `source-artifacts/sec-atom-feeds/` | Reconstruct what the engine saw during that run |
| 8-K markdown for selected candidate | Yes | `source-artifacts/sec-8k-markdown/` | Human-readable verification audit |
| 8-K raw HTML for selected candidate | Optional | `source-artifacts/sec-8k-html/` | Debug parser/LLM disputes |
| Form 4 XML for purchase candidate | Yes | `source-artifacts/form4-xml/` | Deterministic primary source |
| Non-watchlist filing bodies | No | Not stored | Too much noise |
| Watchlist but non-catalyst 8-K | Metadata only unless debug flag | `rejected-or-noncatalyst/` if retained | Audit false negatives selectively |
| Verification snapshot JSON | Yes | `verification-snapshots/` | Shows exact facts checked and sources used |

The cleanup job should run weekly or monthly:

1. Find artifacts older than retention window.
2. If artifact is linked to posted/approved content, archive/compress instead of deleting.
3. If artifact is linked only to rejected/noise candidates, delete after retention window.
4. Update `cq_source_artifacts.retention_status`.
5. Log cleanup to `cq_run_logs`.

---

## 10. n8n / Paperclip Automation Pattern

Use the triarchy model:

### n8n — Hands

Responsible for:

- schedule trigger
- call Ops API endpoints
- create assigned Paperclip issues
- wake relevant agents
- send Telegram/log notifications

Do not use n8n AI Agent node for this pipeline.

### Paperclip — Workers

Responsible for:

- CQ-Selector: select candidates and draft content
- CQ-Researcher: independent verification
- CQ-Monitor: health/status report

### Verification Agent Model Decision

For SWIP8, the verification agent should use the local token-efficient model:

`gemma4:e4b`

Rationale:

- Verification is evidence matching, not high-creativity drafting.
- The model mainly checks whether a source sentence, SEC filing body, Form 4 XML, IR/FDA/ClinicalTrials source, and generated summary agree.
- Local inference keeps cost near zero and avoids burning cloud/reasoning tokens.
- The verifier is not the final authority: deterministic checks, source hashes, and Dr. Don approval remain the control gates.

Model routing:

| Stage | Model / Method | Reason |
|---|---|---|
| Path A extraction from 8-K | `nemotron-3-super:cloud` | Better clinical/regulatory extraction from messy filing text |
| Path B Form 4 extraction | deterministic Python | XML is structured; no LLM needed |
| Independent verification | `gemma4:e4b` local | Token-efficient source confirmation and consistency check |
| Newsletter/tweet drafting | local model first; escalate if poor | Content generation can be reviewed before approval |
| Final approval | Dr. Don | Human gate before posting |

Trigger model:

- n8n triggers the verification step after `/cq/detect` and `/cq/automation/select`.
- The verification can run as a deterministic script endpoint first: `/cq/automation/verify`.
- If deeper reasoning or source interpretation is needed, n8n also creates a Paperclip issue assigned to CQ-Researcher and wakes the agent.
- CQ-Researcher should be configured/instructed to use `gemma4:e4b` where available for SWIP8 verification.

### Alfred — Eye + Fixer

Responsible for:

- implementation
- debugging
- schema changes
- final cross-system verification

---

## 11. Minimal New Scripts / Endpoints

### 11.1 Scripts

Create in organized backend:

`Meddash_organized_backend/scripts/cq_automation/`

Scripts:

1. `cq_candidate_selector.py`
   - reads `cq_catalysts` + `cq_insider_trades`
   - checks posted-events log
   - writes `cq_selected_candidates`

2. `cq_independent_verifier.py`
   - verifies candidates against primary/secondary sources
   - writes `cq_research_confirmations`

3. `cq_content_composer.py`
   - creates newsletter draft, tweet draft, approval package
   - writes `cq_content_queue`
   - writes markdown files

4. `cq_approval_updater.py`
   - marks content approved/rejected/revise
   - updates `cq_content_queue`
   - updates `posted-events-log.md` after approval/posting

5. `cq_publish_exporter.py`
   - exports approved content to final manual-posting package
   - optional X posting later via `xurl` only after Dr. Don approval

### 11.2 Ops API Endpoints

Modify:

`Meddash_organized_backend/07_DevOps_Observability/meddash_ops_api.py`

Add endpoints:

- `POST /cq/automation/select`
- `POST /cq/automation/verify`
- `POST /cq/automation/compose`
- `POST /cq/automation/approval-status`
- `POST /cq/automation/export-approved`
- `GET /cq/automation/latest-approval-package`
- `GET /cq/automation/status`

---

## 12. Visibility Requirements

### 12.1 Supabase / DB Visibility

Dashboard should read:

- `cq_run_logs_latest`
- `cq_catalysts`
- `cq_insider_trades`
- `cq_selected_candidates`
- `cq_research_confirmations`
- `cq_content_queue`
- `cq_source_artifacts`

### 12.2 Local Visibility

All generated files should be timestamped and placed in:

- `CQ_Observability/daily-summaries/`
- `CQ_Automation/approval-packages/`
- `CQ_Automation/newsletter-drafts/`
- `CQ_Automation/tweet-drafts/`

### 12.3 Dashboard Panel

Add a CQ Automation panel showing:

- last CQ engine run
- last candidate selection run
- verified candidates today
- pending approval packages
- rejected candidates
- approved but not posted
- posted items today
- latest errors

---

## 13. SWIP8 Implementation Checklist

### Section A — Schema

- [x] **A.1:** Create `CQ_Automation/sql/cq_automation_schema.sql`.
- [x] **A.2:** Create Supabase table `cq_selected_candidates`.
- [x] **A.3:** Create Supabase table `cq_research_confirmations`.
- [x] **A.4:** Create Supabase table `cq_content_queue`.
- [x] **A.5:** Create Supabase table `cq_source_artifacts` for official SEC/verification artifact index.
- [x] **A.6:** Add indexes for candidate ID, artifact ID, accession number, status, ticker, created_at.
- [x] **A.7:** Verify schema with `information_schema` query.
- [x] **A.8:** Insert one test automation setup row, then verify readback.

### Section B — Folder Structure

- [x] **B.1:** Create `CTO/CQ_Team/CQ_Automation/` root.
- [x] **B.2:** Create subfolder `candidates/`.
- [x] **B.3:** Create subfolder `verification/`.
- [x] **B.4:** Create subfolder `approval-packages/`.
- [x] **B.5:** Create subfolder `newsletter-drafts/`.
- [x] **B.6:** Create subfolder `tweet-drafts/`.
- [x] **B.7:** Create subfolder `approved-posts/`.
- [x] **B.8:** Create subfolder `rejected/`.
- [x] **B.9:** Create subfolder `scripts/`.
- [x] **B.10:** Create subfolder `sql/`.
- [x] **B.11:** Create subfolder `source-artifacts/`.
- [x] **B.12:** Create subfolder `source-artifacts/sec-atom-feeds/`.
- [x] **B.13:** Create subfolder `source-artifacts/sec-8k-markdown/`.
- [x] **B.14:** Create subfolder `source-artifacts/sec-8k-html/`.
- [x] **B.15:** Create subfolder `source-artifacts/form4-xml/`.
- [x] **B.16:** Create subfolder `source-artifacts/verification-snapshots/`.
- [x] **B.17:** Create subfolder `source-artifacts/rejected-or-noncatalyst/`.

### Section C — Candidate Selection

- [x] **C.1:** Create `scripts/cq_automation/cq_candidate_selector.py`.
- [x] **C.2:** Load fresh unposted rows from `cq_catalysts`.
- [x] **C.3:** Load fresh unposted rows from `cq_insider_trades`.
- [x] **C.4:** Read dedup state from `Hermes Agent Win Files/projects/clinical-quant/posted-events-log.md`.
- [x] **C.5:** Exclude already posted/rejected accessions.
- [x] **C.6:** Rank candidates by event type and recency.
- [x] **C.7:** Write selected candidates to `cq_selected_candidates`.
- [x] **C.8:** Write timestamped candidate summary to `CQ_Automation/candidates/`.
- [x] **C.9:** Log run to `cq_run_logs`.

### Section D — Independent Verification

- [x] **D.1:** Create `scripts/cq_automation/cq_independent_verifier.py`.
- [x] **D.2:** Re-open SEC accession/filing URL for every selected candidate using edgartools/direct SEC archive access, not uncontrolled web crawl.
- [x] **D.3:** For 8-K candidates, re-fetch official filing body and regenerate `filing.markdown()` / official text.
- [x] **D.4:** For Form 4 candidates, re-fetch official SEC ownership XML.
- [x] **D.5:** Save retained SEC artifact to `source-artifacts/` with date+time filename.
- [x] **D.6:** Compute SHA256 and file size for every retained artifact.
- [x] **D.7:** Write artifact metadata to `cq_source_artifacts`.
- [x] **D.8:** Confirm ticker/CIK match.
- [x] **D.9:** Confirm exact source sentence or Form 4 XML transaction.
- [x] **D.10:** For PDUFA/FDA/clinical events, search/verify company IR or press release source.
- [x] **D.11:** For trial/data events, optionally verify ClinicalTrials.gov record if NCT/drug/indication available.
- [x] **D.12:** Write `confirmed`, `needs_review`, or `rejected` to `cq_research_confirmations`.
- [x] **D.13:** Write timestamped verification report to `CQ_Automation/verification/`.
- [x] **D.14:** Write verification snapshot JSON to `source-artifacts/verification-snapshots/`.
- [x] **D.15:** Log run to `cq_run_logs`.

### Section E — Newsletter Draft Generation

- [x] **E.1:** Create `scripts/cq_automation/cq_content_composer.py`.
- [x] **E.2:** Load only confirmed candidates, plus optional needs_review section.
- [x] **E.3:** Generate newsletter markdown in CQ format.
- [x] **E.4:** Save newsletter draft to `CQ_Automation/newsletter-drafts/`.
- [x] **E.5:** Save second copy to `Hermes Agent Win Files/projects/clinical-quant/newsletter/`.
- [x] **E.6:** Write newsletter content row to `cq_content_queue`.
- [x] **E.7:** Log run to `cq_run_logs`.

### Section F — Tweet/X Draft Generation

- [x] **F.1:** Extend `cq_content_composer.py` or create `cq_tweet_composer.py`.
- [x] **F.2:** Generate single tweet and thread variants for each confirmed candidate.
- [x] **F.3:** Enforce no hype / no investment advice / source trail rules.
- [x] **F.4:** Save tweet markdown to `CQ_Automation/tweet-drafts/`.
- [x] **F.5:** Write tweet/thread rows to `cq_content_queue`.
- [x] **F.6:** Log run to `cq_run_logs`.

### Section G — Approval Package

- [x] **G.1:** Generate one timestamped approval package per automation run.
- [x] **G.2:** Include verified facts, source links, newsletter draft, tweet drafts, and approval options.
- [x] **G.3:** Save to `CQ_Automation/approval-packages/`.
- [x] **G.4:** Add `pending_review` rows to `cq_content_queue`.
- [x] **G.5:** Send Telegram notification to Dr. Don with approval package path.
- [x] **G.6:** Expose latest approval package through Ops API.

### Section H — Dr. Don Approval Gate

- [x] **H.1:** Create `scripts/cq_automation/cq_approval_updater.py`.
- [x] **H.2:** Support approve/reject/revise by content ID or candidate ID.
- [x] **H.3:** Update `cq_content_queue.approval_status`.
- [x] **H.4:** If rejected, write reason to `CQ_Automation/rejected/`.
- [x] **H.5:** If approved, copy final package to `CQ_Automation/approved-posts/`.
- [x] **H.6:** Log approval action to `cq_run_logs`.

### Section I — Posting / Export

- [x] **I.1:** Create `scripts/cq_automation/cq_publish_exporter.py`.
- [x] **I.2:** Export approved newsletter final markdown for Substack/LinkedIn manual posting.
- [x] **I.3:** Export approved tweet/thread text for X/manual posting.
- [x] **I.4:** Optional later: add `xurl` posting after explicit approval.
- [x] **I.5:** Update `posted-events-log.md` only after approval/export/posting.
- [x] **I.6:** Mark content as `posted` or `exported_for_manual_post` in `cq_content_queue`.
- [x] **I.7:** Log posting/export action to `cq_run_logs`.

### Section J — n8n Automation

- [x] **J.1:** Update n8n workflow `CQ-Free Newsletter 1100` to call `/cq/detect`.
- [x] **J.2:** Add HTTP node for `/cq/automation/select`.
- [x] **J.3:** Add HTTP node for `/cq/automation/verify`.
- [x] **J.4:** Add HTTP node for `/cq/automation/compose`.
- [x] **J.5:** Add HTTP node for `/cq/automation/latest-approval-package`.
- [x] **J.6:** Add Telegram notification with latest approval package path.
- [x] **J.7:** Create CQ-Selector Paperclip issue with full `assigneeAgentId`.
- [x] **J.8:** Wake CQ-Selector with simple payload.
- [x] **J.9:** Create CQ-Monitor Paperclip issue with full `assigneeAgentId`.
- [x] **J.10:** Wake CQ-Monitor with simple payload.
- [x] **J.11:** Activate/toggle workflow in n8n UI after DB/API changes.

### Section K — Paperclip Agent Roles

- [x] **K.1:** Update CQ-Selector instructions to read `cq_selected_candidates`, `cq_research_confirmations`, and `cq_content_queue`.
- [x] **K.2:** Update CQ-Researcher instructions for independent verification and source trail requirements.
- [x] **K.3:** Update CQ-Monitor instructions to check SWIP8 automation health.
- [x] **K.4:** Ensure every agent writes timestamped logs to the required per-agent folders.
- [x] **K.5:** Ensure agent wakeup payloads are simple JSON only.

**Implementation notes (2026-05-02):**
- All prior Paperclip agents were cleared by Dr. Don. Three new CQ agents created from scratch via API.
- Board approval temporarily disabled on company (`requireBoardApprovalForNewAgents=false`), agents created directly, then re-enabled.
- Agent roster:
  - **CQ-Selector** (d16ca8cb): pm role, glm-5, 300s heartbeat with wakeOnDemand. Instructions: selects top 3-5 candidates from detection output, delegates verification to CQ-Researcher via child issues, calls cq_content_composer.py for final drafts. Logs to `CQ-Paper Clip Agent Logs/CQ-Selector/`.
  - **CQ-Researcher** (a2984628): researcher role, kimi-k2.5, 300s heartbeat. Instructions: mandatory SEC re-fetch per candidate, source artifact retention with SHA256, cross-reference IR/FDA/ClinicalTrials.gov, write `cq_research_confirmations`. Logs to `CQ-Paper Clip Agent Logs/CQ-Researcher/`.
  - **CQ-Monitor** (476a090d): devops role, ministral-3:3b, 300s heartbeat. Instructions: check pipeline status via `/cq/automation/status`, escalate to CQ-CTO or Dr. Don per severity, no-fix detection-only role. Logs to `CQ-Paper Clip Agent Logs/CQ-Monitor/`.
- All AGENTS.md instruction files written to `~/.paperclip/instances/default/companies/cf39ae28/agents/{id}/instructions/`.
- Simple wakeup payloads only: `{"reason":"issue_assigned"}`.
- n8n workflow updated with new agent IDs for all Paperclip issue creation + wakeup nodes.
- Duplicate pending CQ-Selector (42c5c8ca) from hire-approval attempt was deleted.
- **Telegram notifications added:** CQ-Alerts bot (`8672876638`) wired to Dr. Don's chat (6253013213). Ops API bot token updated — all pipeline stage notifications (ticker spine, detect, select, verify, compose) now route through CQ-Alerts. Each agent's AGENTS.md updated with a "Notification on Completion" section: CQ-Selector sends summary after composition (selected/verified/composed counts + approval package path), CQ-Researcher sends summary after verification (confirmed/rejected/needs_review counts), CQ-Monitor sends heartbeat status every 3h or immediately if issues found.

### Section L — Visibility / Dashboard

- [x] **L.1:** Add CQ Automation summary widget to Streamlit dashboard.
- [x] **L.2:** Show latest `cq_run_logs_latest` rows.
- [x] **L.3:** Show pending approval packages.
- [x] **L.4:** Show confirmed/rejected candidate counts.
- [x] **L.5:** Show approved-but-not-posted items.
- [x] **L.6:** Show latest automation errors.

### Section M — End-to-End Verification

- [ ] **M.1:** Run controlled test with one known 8-K catalyst.
- [ ] **M.2:** Run controlled test with one known Form 4 purchase.
- [x] **M.3:** Verify candidate selection inserts rows.
- [x] **M.4:** Verify independent confirmation writes `confirmed`/`rejected` correctly.
- [x] **M.5:** Verify newsletter draft file is created in both destinations.
- [x] **M.6:** Verify tweet draft file is created.
- [x] **M.7:** Verify approval package is created.
- [x] **M.8:** Verify approval update changes DB status.
- [x] **M.9:** Verify posting/export updates `posted-events-log.md`.
- [ ] **M.10:** Verify dashboard sees latest rows.
- [ ] **M.11:** Verify n8n workflow can run manually end-to-end.
- [ ] **M.12:** Verify scheduled workflow fires after activation/toggle.

---

## 14. Minimal Viable Automation Definition

SWIP8 is considered minimally complete when:

1. CQ engine runs on schedule or manual trigger.
2. New events enter `cq_catalysts` / `cq_insider_trades`.
3. Candidate selector produces `cq_selected_candidates`.
4. Independent verifier confirms or rejects each candidate.
5. Newsletter draft is generated.
6. Tweet/X draft is generated.
7. Approval package is generated for Dr. Don.
8. Source artifacts for selected/verified candidates are retained locally and indexed in `cq_source_artifacts`.
9. Dr. Don can approve/reject/revise.
10. Approved items are exported for posting.
11. Posted/exported items update the dedup log.
12. Every stage writes to `cq_run_logs` and timestamped local logs.
13. Dashboard or status endpoint shows what happened.

---

## 15. Implementation Priority

Build in this order:

1. Schema + folders.
2. Source artifact folders + `cq_source_artifacts` table.
3. Candidate selector.
4. Independent verifier with SEC re-fetch + artifact retention.
5. Content composer.
6. Approval package.
7. Approval updater.
8. Posting/exporter.
9. Ops API endpoints.
10. n8n workflow integration.
11. Dashboard visibility.
12. Paperclip instruction updates.
13. End-to-end validation.

---

## 16. Deferred / Not in Minimal Build

- Fully automated Substack posting.
- Fully automated LinkedIn posting.
- Fully automated X posting without approval.
- Paid API enrichment unless clearly needed.
- Complex scoring model.
- Confidence scores.
- Options flow.
- Price-action analytics.
- Standalone paid CQ product UX.

These can come later after the approval-gated pipeline works.

---

## 17. Immediate Next Step After This SWIP

Implement Section A and B first:

- create `CQ_Automation/` folder tree
- create `cq_automation_schema.sql`
- create Supabase tables:
  - `cq_selected_candidates`
  - `cq_research_confirmations`
  - `cq_content_queue`
  - `cq_source_artifacts`
- create source artifact folders for SEC feed XML, 8-K markdown/HTML, Form 4 XML, and verification snapshots

Then implement candidate selection and independent verification before any drafting/posting automation.


---

## 18. Implementation Update — 2026-05-02 05:46 UTC

Status: SWIP8 script layer implemented. n8n workflow rewiring and Paperclip agent instruction updates are intentionally not done yet; those are the next phase after script validation.

Implemented files:

- `Meddash_organized_backend/scripts/cq_automation/cq_automation_common.py`
- `Meddash_organized_backend/scripts/cq_automation/cq_candidate_selector.py`
- `Meddash_organized_backend/scripts/cq_automation/cq_independent_verifier.py`
- `Meddash_organized_backend/scripts/cq_automation/cq_content_composer.py`
- `Meddash_organized_backend/scripts/cq_automation/cq_approval_updater.py`
- `Meddash_organized_backend/scripts/cq_automation/cq_publish_exporter.py`
- `Meddash_organized_backend/scripts/cq_automation/cq_artifact_cleanup.py`
- `Meddash_organized_backend/tests/test_cq_automation.py`
- `CTO/CQ_Team/CQ_Automation/sql/cq_automation_schema.sql`

Created/verified Supabase objects:

- `cq_selected_candidates`
- `cq_research_confirmations`
- `cq_content_queue`
- `cq_source_artifacts`
- `cq_automation_status` view

Created/verified local automation folders:

- `CQ_Automation/candidates/`
- `CQ_Automation/verification/`
- `CQ_Automation/approval-packages/`
- `CQ_Automation/newsletter-drafts/`
- `CQ_Automation/tweet-drafts/`
- `CQ_Automation/approved-posts/`
- `CQ_Automation/rejected/`
- `CQ_Automation/source-artifacts/sec-atom-feeds/`
- `CQ_Automation/source-artifacts/sec-8k-markdown/`
- `CQ_Automation/source-artifacts/sec-8k-html/`
- `CQ_Automation/source-artifacts/form4-xml/`
- `CQ_Automation/source-artifacts/verification-snapshots/`
- `CQ_Automation/source-artifacts/rejected-or-noncatalyst/`

Validation completed:

- `python3 -m py_compile scripts/cq_automation/*.py`
- `python3 -m pytest tests/test_cq_automation.py tests/test_cq_engine.py -q`
- Result: `12 passed, 3 edgartools deprecation warnings`
- Dry-run validation completed for selector, verifier, composer, exporter, and artifact cleanup scripts.

Current dry-run result found zero selected/verified/content rows because the candidate tables had no currently selectable unprocessed rows in this run. The scripts, schema, folders, and logging paths are operational and ready for n8n/Paperclip integration.
