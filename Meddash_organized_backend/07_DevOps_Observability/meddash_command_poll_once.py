#!/usr/bin/env python3
"""Meddash Telegram command poller — single-shot for n8n Execute Command.

No webhook required. n8n runs this every 10–60 seconds.
It polls Telegram getUpdates, handles the newest unprocessed command, sends a reply, then exits.
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BOT_TOKEN = os.environ.get("MEDDASH_TELEGRAM_BOT_TOKEN", "8515229822:AAGgPRuVkTSiccltsKyhsO1TqvitYSr6Geo")
DEFAULT_CHAT_ID = os.environ.get("MEDDASH_TELEGRAM_CHAT_ID", "6253013213")
API = f"https://api.telegram.org/bot{BOT_TOKEN}"

ROOT = Path("/mnt/c/Users/email/.gemini/antigravity/Meddash_organized_backend")
SUMMARY_DIR = ROOT / "06_Shared_Datastores" / "pipeline_summaries"
DB_DIR = ROOT / "06_Shared_Datastores"
STATE_FILE = Path("/tmp/meddash_command_listener_last_update_id.txt")


def api_call(method: str, payload: dict | None = None, timeout: int = 20) -> dict:
    url = f"{API}/{method}"
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def send_message(chat_id: str | int, text: str) -> None:
    api_call("sendMessage", {"chat_id": str(chat_id), "text": text})


def read_last_update_id() -> int:
    try:
        return int(STATE_FILE.read_text().strip())
    except Exception:
        return 0


def write_last_update_id(update_id: int) -> None:
    STATE_FILE.write_text(str(update_id))


def latest_updates(offset: int) -> list[dict]:
    result = api_call("getUpdates", {"offset": offset, "timeout": 1}, timeout=10)
    return result.get("result", []) if result.get("ok") else []


def summary_line(name: str) -> str:
    path = SUMMARY_DIR / f"{name}_summary.json"
    try:
        data = json.loads(path.read_text())
        status = data.get("status", "?")
        timestamp = data.get("timestamp", "?")
        return f"  {name}: {status} ({timestamp[:16]})"
    except Exception:
        return f"  {name}: MISSING"


def count_first_table(db_path: Path) -> int | None:
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name LIMIT 1")
        row = cur.fetchone()
        if not row:
            return None
        table = row[0].replace('"', '""')
        cur.execute(f'SELECT COUNT(*) FROM "{table}"')
        return int(cur.fetchone()[0])
    finally:
        conn.close()


def db_line(db_file: str, label: str) -> str:
    try:
        count = count_first_table(DB_DIR / db_file)
        return f"  {label} DB: {count if count is not None else 'NO TABLE'} rows"
    except Exception as exc:
        return f"  {label} DB: ERROR ({type(exc).__name__})"


def build_status() -> str:
    lines = ["📊 Meddash Pipeline Status", ""]
    for name in ["biocrawler", "ct_crawler", "kol_pipeline"]:
        lines.append(summary_line(name))
    lines.append("")
    lines.append(db_line("biocrawler_leads.db", "BioCrawler Leads"))
    lines.append(db_line("ct_trials.db", "Clinical Trials"))
    lines.append(db_line("meddash_kols.db", "KOL"))
    lines.append("")
    lines.append("Dashboard: http://localhost:5090")
    lines.append(f"Checked: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    return "\n".join(lines)


def build_rotation() -> str:
    categories = [
        "Neoplasms (C04)", "Nervous System (C10)", "Cardiovascular (C14)",
        "Immune System Diseases (C20)", "Respiratory (C08)", "Digestive (C11)",
        "Musculoskeletal (C05)", "Mental Disorders (F03)", "Infections (C01)",
        "Endocrine (C19)", "Eye Diseases (C11)", "Urogenital (C12)",
    ]
    week = datetime.now(timezone.utc).isocalendar().week
    category = categories[(week - 1) % len(categories)]
    return f"🔄 MeSH Week {week}: {category} (category {(week - 1) % len(categories) + 1}/12)"


def handle(text: str) -> str | None:
    normalized = text.strip().split()[0].lower() if text.strip() else ""
    if normalized == "/status":
        return build_status()
    if normalized == "/rotation":
        return build_rotation()
    if normalized in {"/help", "/start"}:
        return "Meddash Pipeline Bot Commands:\n/status — Full pipeline health summary\n/rotation — Current MeSH rotation week\n/help — This message"
    if normalized.startswith("/"):
        return "Unknown command. Try /status, /rotation, or /help"
    return None


def main() -> int:
    last_id = read_last_update_id()
    updates = latest_updates(last_id + 1)
    if not updates:
        print(json.dumps({"status": "idle", "message": "no new updates", "last_update_id": last_id}))
        return 0

    processed = 0
    for update in updates:
        update_id = int(update.get("update_id", 0))
        write_last_update_id(update_id)
        msg = update.get("message") or update.get("edited_message") or {}
        text = msg.get("text") or ""
        chat_id = msg.get("chat", {}).get("id") or DEFAULT_CHAT_ID
        response = handle(text)
        if response:
            send_message(chat_id, response)
            processed += 1
            print(json.dumps({"status": "replied", "update_id": update_id, "text": text, "chat_id": chat_id}))
        else:
            print(json.dumps({"status": "ignored", "update_id": update_id, "text": text}))

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc), "type": type(exc).__name__}), file=sys.stderr)
        raise SystemExit(2)
