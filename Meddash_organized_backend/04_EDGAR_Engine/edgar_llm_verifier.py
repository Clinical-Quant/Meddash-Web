#!/usr/bin/env python3
"""
edgar_llm_verifier.py — Stage 2: LLM Precision Gate for EDGAR Catalyst Crawler

Receives candidate catalyst events from Stage 1 (Python regex extraction),
sends each to an LLM with the excerpt for verification, and returns structured
JSON verdicts. Only verified rows should be displayed on the calendar.

Design: "machines pull, intelligence verifies" — same pattern as the SR factory.

The LLM fixes exactly the failure classes regex can't:
- Pembrolizumab-on-Pfizer misattribution (is this the filing company's drug?)
- CGT1145 identifier grab (canonical name resolution > alias map)
- Window tense ("Q1 2026" as past vs future)

Usage:
    from edgar_llm_verifier import verify_candidates
    results = verify_candidates(candidates)

    # Or standalone:
    python edgar_llm_verifier.py --input candidates.json --output verified.json
"""

import json
import urllib.request
import time
import logging
import argparse
from pathlib import Path

log = logging.getLogger(__name__)

# Mutable model name (can be overridden via _set_model)
_OLLAMA_MODEL = "gemma4:31b-cloud"


def _set_model(model_name: str):
    """Override the Ollama model name."""
    global _OLLAMA_MODEL
    _OLLAMA_MODEL = model_name


def _get_model() -> str:
    """Get the current Ollama model name."""
    return _OLLAMA_MODEL

# ── Ollama endpoint ──
OLLAMA_URL = "http://localhost:11434/api/chat"

# ── Verification prompt template ──
VERIFY_PROMPT = """You are a biotech regulatory intelligence analyst. Verify this catalyst event extracted from an SEC 8-K filing.

Filing company: {company} (ticker: {ticker})
Extracted event type: {event_type}
Extracted date/window: {date_or_window}
Extracted asset (drug): {asset}
Extracted indication: {indication}
Filing date: {filing_date}

Excerpt from the 8-K filing:
---
{excerpt}
---

Answer these questions:
1. Does this excerpt actually announce a {event_type} event with date "{date_or_window}"?
2. Is "{asset}" a drug belonging to {company}? If not, what drug IS being discussed?
3. What is the canonical name for the drug discussed (generic name or brand name)?
4. Is the date/window in the past or future relative to today ({today})?

Reply as JSON ONLY (no markdown, no explanation outside JSON):
{{
  "verified": true/false,
  "is_company_drug": true/false,
  "canonical_asset": "canonical drug name",
  "canonical_indication": "indication if determinable, else null",
  "date_is_past": true/false,
  "reasoning": "1-2 sentence explanation"
}}"""


def _call_ollama(prompt: str, timeout: int = 60) -> str:
    """Call the local Ollama endpoint with the verification prompt."""
    payload = json.dumps({
        "model": _get_model(),
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0.1},
    }).encode("utf-8")

    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data.get("message", {}).get("content", "")


def _parse_llm_json(raw: str) -> dict | None:
    """Parse JSON from LLM response, tolerant of markdown wrappers."""
    # Strip markdown code fences if present
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
        cleaned = cleaned.rsplit("```", 1)[0]
    cleaned = cleaned.strip()

    # Try to find JSON object in the response
    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1
    if start >= 0 and end > start:
        json_str = cleaned[start:end]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # Try fixing common issues (trailing commas)
            json_str = json_str.replace(",}", "}").replace(",]", "]")
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                return None
    return None


def verify_candidate(candidate: dict, today_str: str = None) -> dict:
    """Verify a single catalyst candidate via LLM.

    Args:
        candidate: Dict with company, ticker, event_type, date_or_window,
                   asset, indication, filing_date, excerpt
        today_str: Today's date as YYYY-MM-DD string

    Returns:
        Dict with original fields + verification fields:
        - verification_status: 'verified' | 'rejected' | 'error'
        - verification_note: LLM reasoning
        - canonical_asset: LLM-resolved drug name (if verified)
        - canonical_indication: LLM-resolved indication (if verified)
        - date_is_past: LLM's tense assessment
    """
    from datetime import date
    if today_str is None:
        today_str = date.today().isoformat()

    prompt = VERIFY_PROMPT.format(
        company=candidate.get("company", ""),
        ticker=candidate.get("ticker", ""),
        event_type=candidate.get("event_type", ""),
        date_or_window=candidate.get("date_or_window", ""),
        asset=candidate.get("asset", "UNKNOWN"),
        indication=candidate.get("indication") or "N/A",
        filing_date=candidate.get("filing_date", ""),
        excerpt=candidate.get("excerpt", "")[:1200],
        today=today_str,
    )

    try:
        raw_response = _call_ollama(prompt)
        parsed = _parse_llm_json(raw_response)

        if parsed is None:
            log.warning(f"  LLM returned unparseable JSON for {candidate['ticker']} "
                        f"{candidate['event_type']}")
            return {
                **candidate,
                "verification_status": "error",
                "verification_note": "LLM returned unparseable response",
                "canonical_asset": candidate.get("asset"),
                "canonical_indication": candidate.get("indication"),
            }

        verified = parsed.get("verified", False)
        is_company_drug = parsed.get("is_company_drug", False)
        canonical_asset = parsed.get("canonical_asset") or candidate.get("asset")
        canonical_indication = parsed.get("canonical_indication") or candidate.get("indication")
        date_is_past = parsed.get("date_is_past", False)
        reasoning = parsed.get("reasoning", "")

        # A candidate is verified if:
        # 1. The LLM confirms the event exists in the excerpt
        # 2. The drug belongs to the filing company (or is UNKNOWN and LLM doesn't flag it)
        if verified and (is_company_drug or candidate.get("asset") == "UNKNOWN"):
            status = "verified"
            # Update asset if LLM provided a better canonical name
            if canonical_asset and canonical_asset.upper() != "UNKNOWN":
                candidate["asset"] = canonical_asset
            if canonical_indication:
                candidate["indication"] = canonical_indication
        else:
            status = "rejected"

        # Update status based on LLM tense assessment
        if date_is_past and candidate.get("date_precision") == "exact":
            candidate["status"] = "occurred"

        return {
            **candidate,
            "verification_status": status,
            "verification_note": reasoning,
            "canonical_asset": canonical_asset,
            "canonical_indication": canonical_indication,
        }

    except Exception as e:
        log.warning(f"  LLM call failed for {candidate.get('ticker', '?')} "
                    f"{candidate.get('event_type', '?')}: {str(e)[:80]}")
        return {
            **candidate,
            "verification_status": "error",
            "verification_note": f"LLM call failed: {str(e)[:60]}",
            "canonical_asset": candidate.get("asset"),
            "canonical_indication": candidate.get("indication"),
        }


def verify_candidates(candidates: list[dict], delay: float = 0.2) -> list[dict]:
    """Verify a batch of catalyst candidates via LLM.

    Args:
        candidates: List of candidate dicts from Stage 1
        delay: Delay between LLM calls (seconds)

    Returns:
        List of verified/rejected candidates with verification fields added
    """
    if not candidates:
        return []

    log.info(f"LLM Verification: {len(candidates)} candidates to verify")

    results = []
    verified_count = 0
    rejected_count = 0
    error_count = 0

    for i, candidate in enumerate(candidates, 1):
        log.info(f"  [{i}/{len(candidates)}] {candidate['ticker']} | "
                 f"{candidate['event_type']} | {candidate['date_or_window']} | "
                 f"{candidate.get('asset', '?')}")

        verified = verify_candidate(candidate)
        results.append(verified)

        if verified["verification_status"] == "verified":
            verified_count += 1
            log.info(f"    ✅ VERIFIED — {verified.get('canonical_asset', verified.get('asset', '?'))}")
        elif verified["verification_status"] == "rejected":
            rejected_count += 1
            log.info(f"    ❌ REJECTED — {verified.get('verification_note', '')[:80]}")
        else:
            error_count += 1
            log.info(f"    ⚠️ ERROR — {verified.get('verification_note', '')[:80]}")

        if i < len(candidates):
            time.sleep(delay)

    log.info(f"\nLLM Verification complete: "
             f"{verified_count} verified, {rejected_count} rejected, {error_count} errors")

    return results


# ═══════════════════════════════════════════════════════════════════════
# CLI (standalone mode)
# ═══════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="LLM Verification Gate for EDGAR Catalyst Crawler (Stage 2)"
    )
    parser.add_argument("--input", type=str, required=True,
                        help="JSON file with candidate catalyst events")
    parser.add_argument("--output", type=str, default="verified.json",
                        help="Output JSON file with verification results")
    parser.add_argument("--model", type=str, default="gemma4:31b-cloud",
                        help="Ollama model (default: gemma4:31b-cloud)")

    args = parser.parse_args()

    # Override model if specified
    if args.model != OLLAMA_MODEL:
        _set_model(args.model)

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")

    with open(args.input, "r", encoding="utf-8") as f:
        candidates = json.load(f)

    results = verify_candidates(candidates)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nResults written to {args.output}")

    # Summary
    verified = [r for r in results if r["verification_status"] == "verified"]
    rejected = [r for r in results if r["verification_status"] == "rejected"]
    errors = [r for r in results if r["verification_status"] == "error"]

    print(f"\nSummary: {len(verified)} verified, {len(rejected)} rejected, {len(errors)} errors")

    if rejected:
        print(f"\nRejected candidates:")
        for r in rejected:
            print(f"  {r['ticker']} | {r['event_type']} | {r['date_or_window']} | "
                  f"{r.get('verification_note', '')[:80]}")


if __name__ == "__main__":
    main()