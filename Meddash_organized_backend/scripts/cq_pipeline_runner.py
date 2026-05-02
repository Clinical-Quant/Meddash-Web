#!/usr/bin/env python3
"""CQ pipeline runner.

Replaces the old CQ orchestrator that called:
- sec_8k_monitor.py
- fda_pdufa_tracker.py
- pr_wire_aggregator.py

Current production command:
  python3 cq_pipeline_runner.py detect
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, UTC
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CQ_ENGINE_DIR = ROOT / "scripts" / "phase1_regulatory"
CQ_ENGINE = CQ_ENGINE_DIR / "cq_engine.py"


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def run_command(name: str, command: list[str], cwd: Path, timeout: int = 300) -> dict:
    start = datetime.now(UTC)
    try:
        result = subprocess.run(command, cwd=str(cwd), capture_output=True, text=True, timeout=timeout, env={**os.environ, "MEDDASH_ROOT": str(ROOT)})
        elapsed = (datetime.now(UTC) - start).total_seconds()
        return {
            "script": name,
            "status": "success" if result.returncode == 0 else "error",
            "exit_code": result.returncode,
            "elapsed_seconds": round(elapsed, 1),
            "stdout": result.stdout[-4000:],
            "stderr": result.stderr[-4000:],
        }
    except subprocess.TimeoutExpired as e:
        return {"script": name, "status": "timeout", "timeout_seconds": timeout, "stdout": (e.stdout or "")[-2000:], "stderr": (e.stderr or "")[-2000:]}


def detect(extra_args: list[str] | None = None) -> dict:
    if not CQ_ENGINE.exists():
        return {"status": "error", "error": f"missing engine script: {CQ_ENGINE}"}
    args = [sys.executable, str(CQ_ENGINE)] + (extra_args or [])
    res = run_command("cq_engine.py", args, CQ_ENGINE_DIR, timeout=300)
    return {
        "pipeline": "Clinical Quant",
        "mode": "detect",
        "timestamp": utc_now(),
        "retired_scripts_not_called": ["sec_8k_monitor.py", "fda_pdufa_tracker.py", "pr_wire_aggregator.py"],
        "retired_workflows_not_used": ["old three-script CQ regulatory lane", "FDA AdCom-calendar PDUFA scraper", "PR-wire headline keyword lane"],
        "results": [res],
        "status": "success" if res.get("status") == "success" else "error",
    }


def ticker_spine() -> dict:
    """Validate existing Supabase ticker spine; no rebuild in the new SEC-global flow."""
    if not CQ_ENGINE.exists():
        return {"status": "error", "error": f"missing engine script: {CQ_ENGINE}"}
    code = """
from cq_engine import load_env, build_supabase, load_watchlist
sb = build_supabase(load_env())
watch = load_watchlist(sb)
print({'watchlist_count': len(watch), 'client': type(sb).__name__})
"""
    res = run_command("ticker_spine_check", [sys.executable, "-c", code], CQ_ENGINE_DIR, timeout=90)
    return {
        "pipeline": "Clinical Quant",
        "mode": "ticker_spine_check",
        "timestamp": utc_now(),
        "description": "Validated existing biotech_tickers CIK watchlist; no Alpha Vantage rebuild needed for SEC global-feed polling.",
        "results": [res],
        "status": "success" if res.get("status") == "success" else "error",
    }


def select_file() -> dict:
    report_dir = Path("/mnt/c/Users/email/.gemini/antigravity/CEO Notes/CQ Daily Update")
    report_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(report_dir.glob("cq-daily-update-*.md"))
    if not files:
        return {"status": "no_file", "directory": str(report_dir), "files_found": 0}
    latest = files[-1]
    return {"status": "found", "directory": str(report_dir), "filename": latest.name, "filepath": str(latest), "files_found": len(files), "latest": str(latest)}


def main() -> int:
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: cq_pipeline_runner.py detect|ticker_spine|select_file [--dry-run ...]"}, indent=2))
        return 2
    cmd = sys.argv[1]
    if cmd == "detect":
        result = detect(sys.argv[2:])
    elif cmd == "ticker_spine":
        result = ticker_spine()
    elif cmd == "select_file":
        result = select_file()
    elif cmd == "yahoo_ticker_news":
        result = {"status": "retired", "script": "pull_yahoo_ticker_news.py", "replacement": "cq_engine.py global SEC latest-filings flow"}
    else:
        result = {"status": "error", "error": f"Unknown command: {cmd}"}
    print(json.dumps(result, indent=2))
    return 0 if result.get("status") in {"success", "found", "no_file", "retired"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
