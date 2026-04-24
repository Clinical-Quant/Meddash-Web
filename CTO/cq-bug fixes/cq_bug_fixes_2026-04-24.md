# CQ Bug Fixes - 2026-04-24

## Issues Identified in `enrich_tickers.py`

- [x] 1. Raise fuzzy cutoff from 0.85 to 0.92 in `get_close_matches()`.
- [x] 2. Add a private company filter: Skip matching entirely if the lead's core token has no match in SEC data (after exact/clean matching fails).
- [x] 3. Add a minimum token length guard: Skip fuzzy matching if the longest token in the lead name is less than 5 characters.
- [x] 4. Fix Strategy D (Token overlap): Require at least 2 non-generic tokens overlap, OR the single token must be 6+ characters AND match score >= 0.90.
- [x] 5. Log all matches with the strategy used (A/B/C/D).
- [x] 6. After re-run, report the counts for each strategy and list all Strategy C and D matches.

## Remediation Steps
- [x] Clear inaccurate tickers (fuzzy matches from the first run) while preserving Strategy A and B exact matches (183 cleared).
- [x] Apply the aforementioned fixes to `enrich_tickers.py`.
- [x] Re-run the script and record the final reporting metrics.
