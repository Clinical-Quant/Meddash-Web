# MDP3-BF1 — Paperclip Hermes Adapter: Session ID Mis-parse Bug

> **Author:** Hermes Alfred Chief  
> **Date:** 2026-04-26 12:50 EDT  
> **Severity:** P1 — Agent fully down for 10+ hours  
> **Status:** FIXED  
> **Affects:** CQ-Monitor(CQ-FNL) agent (Paperclip), all hermes_local adapter agents  
> **Reference:** SWIP2 Section — Paperclip agent triarchy automation  

---

## Summary

The CQ-Monitor agent on Paperclip entered a failure death spiral at **06:03 UTC on April 26**. Every heartbeat run (every 10 min) failed with:

```
Session not found: from
Use a session ID from a previous CLI run (hermes sessions list).
```

The agent was completely non-functional for **~10 hours** (70+ consecutive failed runs).

---

## Root Cause Chain

### Bug 1: Hermes adapter reads `session_id:` from stdout instead of stderr

**File:** `hermes-paperclip-adapter/dist/server/execute.js`  
**Line:** 196 (original)  
**Code:** `const sessionMatch = stdout.match(SESSION_ID_REGEX);`

In quiet mode (`-Q`), Hermes CLI writes `session_id: <id>` to **stderr**, not stdout. The adapter only checked **stdout**, so it never found the real session ID. This caused the adapter to fall through to the legacy regex path.

### Bug 2: Legacy regex captures arbitrary English words

**File:** `hermes-paperclip-adapter/dist/server/execute.js`  
**Line:** 147 (original)  
**Code:** `SESSION_ID_REGEX_LEGACY = /session[_ ](?:id|saved)[:\s]+([a-zA-Z0-9_-]+)/i`

This regex was designed for non-quiet mode output, but it matches ANY word after "session id" or "session saved" — including English words from the model's response text like "from" or "means".

### Bug 3: No session ID validation

The adapter never validated that a parsed session ID actually looks like a Hermes session ID (which always contains digits and underscores, e.g., `20260425_180519_ceaa04`). Any short word captured by the legacy regex was blindly stored.

### Cascade

1. **05:51 UTC** — CQ-Monitor run succeeds but agent response text contains "session means..." near a pattern the legacy regex matches → adapter parses `"means"` as the session ID
2. Paperclip stores `"means"` as `sessionIdAfter` → next run passes `--resume means`
3. **06:03 UTC** — Hermes tries `--resume means` → fails with "Session not found: from\nUse a session ID from a previous CLI run" → legacy regex matches "session ID **from**" → captures `"from"`
4. Paperclip stores `"from"` as session ID → every subsequent run tries `--resume from` → same error → **infinite failure loop**

---

## Evidence

### Timeline from run logs

| Time (UTC) | Run | Session Before | Session After | Status |
|------------|-----|---------------|---------------|--------|
| 05:41 | 84980112 | 20260425_180519_ceaa04 | 20260425_180519_ceaa04 | OK |
| 05:51 | 71b0f695 | 20260425_180519_ceaa04 | **means** | FAILED (first parse of "means") |
| 06:03 | d89e3280 | **means** | **from** | FAILED |
| 06:13+ | all subsequent | **from** | **from** | FAILED (70+ runs) |

### Log excerpt (first corruption at 05:51)

```
[hermes] Resuming session: 20260425_180519_ceaa04
↻ Resumed session 20260425_180519_ceaa04 (60 user messages, 318 total messages)
...
session_id: 20260425_180519_ceaa04   ← real session ID on stderr
[hermes] Session: means              ← adapter output: WRONG
```

### Log excerpt (cascading failure from 06:03 onward)

```
[hermes] Resuming session: from      ← corrupted session ID
Session not found: from
Use a session ID from a previous CLI run (hermes sessions list).
[hermes] Session: from               ← adapter re-captures "from" from error text
```

---

## Fixes Applied

### Fix 1: Check stderr first for session_id (authoritative source)

**Before:**
```js
const sessionMatch = stdout.match(SESSION_ID_REGEX);
```

**After:**
```js
const sessionMatch = stderr.match(SESSION_ID_REGEX) || stdout.match(SESSION_ID_REGEX);
```

In quiet mode, Hermes writes `session_id: <id>` to stderr. Checking stderr first ensures the real session ID is always found.

### Fix 2: Minimum length requirement on legacy regex

**Before:**
```js
const SESSION_ID_REGEX_LEGACY = /session[_ ](?:id|saved)[:\s]+([a-zA-Z0-9_-]+)/i;
```

**After:**
```js
const SESSION_ID_REGEX_LEGACY = /session[_ ](?:id|saved)[:\s]+([a-zA-Z0-9_-]{6,})/i;
```

Required minimum 6 characters. English words like "from" (4 chars) and "means" (5 chars) can no longer match.

### Fix 3: Reject pure-alpha short strings as session IDs

**Added validation after legacy regex match:**
```js
const candidate = legacyMatch[1];
if (/^[a-zA-Z]+$/.test(candidate) && candidate.length < 10) {
    // Looks like a common English word — skip it
} else {
    result.sessionId = candidate;
}
```

Real Hermes session IDs always contain digits and/or underscores. A purely alphabetic string under 10 chars is almost certainly an English word mis-parsed from response text.

### Fix 4: Reset corrupted Paperclip agent session state

Used Paperclip API to clear the poisoned `"from"` session ID:

```bash
curl -X POST http://127.0.0.1:3100/api/agents/bb9deb04.../runtime-state/reset-session \
  -H "Content-Type: application/json" \
  -d '{"companyId":"cf39ae28-5bd5-44d1-b888-b01f83192fd5"}'
```

Result: `sessionParamsJson: null, sessionId: null` — clean slate.

### Fix 5: Paperclip restart to load patched adapter

Paperclip was restarted to load the patched `execute.js` module.

---

## Verification

Post-fix heartbeat run succeeded immediately:

```
Run: e5d4b8ee → status: succeeded
Session before: None
Session after: 20260426_125036_
```

Agent status changed from `error` to `idle` → `active`.

---

## Impact Assessment

| Metric | Value |
|--------|-------|
| Downtime | ~10 hours (06:03 UTC → 16:50 UTC) |
| Failed runs | 70+ |
| Wasted API calls | 70+ (each attempted model init then immediately failed) |
| Tokens wasted | Minimal (Hermes exits with code 1 before inference) |
| Cost | Negligible (early exit, no LLM completion) |
| Data loss | None (no data was modified during failure window) |

---

## Prevention

1. **Adapter patch** (applied): Three-layer defense — stderr-first, min-length regex, pure-alpha rejection
2. **Paperclip guard**: Consider adding session ID format validation in Paperclip's `resolveNextSessionState()` — reject values that don't match `^\d{8}_\d{6}_[a-z0-9]+$`
3. **Monitoring**: Add alert when agent fails 3x consecutively with same error pattern

---

## Files Modified

| File | Change |
|------|--------|
| `~/.npm/_npx/.../hermes-paperclip-adapter/dist/server/execute.js` | Lines 145-147 (regex), 189-225 (parseHermesOutput), 214-224 (legacy match validation) |
| Paperclip agent `bb9deb04` | Session state reset via API |

---

## Post-Fix: Model Change

**2026-04-26 13:00 EDT** — Changed CQ-Monitor model from `glm-4.7` (thinking model) to `deepseek-v4-flash` (non-thinking, fast, binary-oriented). CQ-Monitor's role is QA check-and-report — no deep reasoning needed. The thinking model was burning tokens on unnecessary chain-of-thought for every heartbeat check.

| Before | After |
|--------|-------|
| `glm-4.7` (ollama-cloud) | `deepseek-v4-flash` (ollama-cloud) |
| Thinking model | Non-thinking, fast |
| ~15-30s per heartbeat | Expected ~3-5s per heartbeat |

*Report filed by Alfred Chief — 2026-04-26 12:50 EDT*