# Issue 5 — CQ Ticker Fuzzy Matching Fix

**Date:** 2026-04-24  
**Status:** ✅ APPROVED WITH CAUTION  
**Severity:** CRITICAL (was)  
**Team:** CQ-CTO  
**Fix Commit:** `enrich_tickers.py` (patched in-place)  
**Bug Report:** [[bug_fixes_2026-04-24]]

---

## Problem

`biotech_leads` ticker column was empty. CQ scripts were limited to a 9-ticker hardcoded watchlist. The original `enrich_tickers.py` used fuzzy matching with a `difflib` cutoff of 0.85, which produced 71 false positives — e.g., "Chordia" matched to "COYA".

## What Was Done Right

1. **Cleared 71 bad tickers** from the first run — no zombie data left behind
2. **Disabled Strategy D** (token overlap) — the worst offender. "Chordia" → "COYA" was pure noise. Gone.
3. **Raised difflib cutoff to 0.95** — original was 0.85, matching way too loosely. 0.95 is much tighter.
4. **Added SEC Submissions API validation** — Strategy C fuzzy matches now verify against the company's SIC code. Only SIC `283x` (Drugs) and `384x` (Medical Devices) pass. This is the smartest fix in the whole thing.
5. **Private company short-circuit** — lines 110-117 skip companies with zero token overlap with any SEC listing. Private companies can't have tickers, so this prevents wasted API calls.

## Caution Flag

**Strategy C now makes a live SEC API call per fuzzy match.**

- SEC informal rate limit: ~10 req/sec
- Current scale: ~100 Strategy C matches per nightly run = 100 API calls = fine
- Risk: If CQ moves to a real-time dashboard, this will hit rate limits

**Recommendation (not blocking):** Add a local SIC cache — a `cik_to_sic.json` file mapping CIK → SIC. Build it incrementally on each run (check cache first, only call SEC API on miss). This turns 100 API calls into ~10 new ones per run after the first week.

## Cross-Reference

- **Meddash CTO's parallel fix:** The Meddash CTO plan also addresses ticker matching in `biocrawler.py` → `scrape_sec_edgar_for_funding()`. That's the **source fix** (prevention). This CQ fix is the **downstream fix** (healing existing gaps). Both should go in.
- **Analogy:** CQ fix = bandage. Meddash biocrawler fix = vaccine.
- See: [[Meddash CTO Implementation Plan - QA Review]]

## Strategy Breakdown (Post-Fix)

| Strategy | Method | Status |
|----------|--------|--------|
| A | Exact name match | Active |
| B | Cleaned suffix match | Active |
| C | Fuzzy difflib (0.95 cutoff) + SEC SIC validation | Active (patched) |
| D | Token overlap | **DISABLED** |

---

*Filed by: Alfred Chief (QA / CTO)*
*Graph Memory: [[MEM_CLINICAL-QUANT_20260424_022636]]*