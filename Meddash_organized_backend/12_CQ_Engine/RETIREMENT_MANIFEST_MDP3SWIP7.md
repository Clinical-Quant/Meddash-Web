# MDP3.SWIP7 Retirement Manifest — CQ Engine

Timestamp: 2026-05-01T23:26Z

## Retired production lane

The old CQ regulatory workflow is retired as an execution path:

1. `sec_8k_monitor.py`
   - Former role: RSS/title/summary keyword scan for SEC 8-Ks.
   - Reason retired: did not inspect full filing body; missed PDUFA/action-date context.
   - Replacement: `Meddash_organized_backend/scripts/phase1_regulatory/cq_engine.py` Path A.

2. `fda_pdufa_tracker.py`
   - Former role: FDA AdCom calendar scrape.
   - Reason retired: wrong source for PDUFA action dates; missed target dates.
   - Replacement: edgartools SEC filing body extraction + Nemotron reasoning inside `cq_engine.py`.

3. `pr_wire_aggregator.py`
   - Former role: PRNewswire/GlobeNewswire RSS keyword scan.
   - Reason retired: feed instability and weak headline-only keyword matching.
   - Replacement: SEC latest filings global monitor + LLM classification on filing body/exhibits.

## Files physically found

The three old scripts were searched under both the organized backend and `CTO/CQ_Team/scripts`; no live copies were present to rename.

## Compatibility retained

`/mnt/c/Users/email/.gemini/antigravity/CTO/CQ_Team/scripts/cq_pipeline_runner.py` is now a shim that delegates to:

`/mnt/c/Users/email/.gemini/antigravity/Meddash_organized_backend/scripts/cq_pipeline_runner.py`

This protects the existing Ops API/n8n chain while moving the real implementation into the organized backend.

## New production lane

n8n/Ops API → `scripts/cq_pipeline_runner.py detect` → `scripts/phase1_regulatory/cq_engine.py`

Outputs:
- Path A: `public.cq_catalysts`
- Path B: `public.cq_insider_trades`
