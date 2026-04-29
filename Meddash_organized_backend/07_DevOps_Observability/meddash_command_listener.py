#!/usr/bin/env python3
"""Meddash Command Listener — Standalone Telegram bot.
Polls for /status, /rotation, /help and responds instantly.
Runs as a lightweight background process (no n8n dependency).
"""
import json, time, sqlite3, os, urllib.request, urllib.parse
from datetime import datetime

BOT_TOKEN = "8515229822:AAGgPRuVkTSiccltsKyhsO1TqvitYSr6Geo"
API = f"https://api.telegram.org/bot{BOT_TOKEN}"
CHAT_ID = "6253013213"

SUMMARY_DIR = "/mnt/c/Users/email/.gemini/antigravity/Meddash_organized_backend/06_Shared_Datastores/pipeline_summaries"
DB_BASE = "/mnt/c/Users/email/.gemini/antigravity/Meddash_organized_backend/06_Shared_Datastores"

MESHI_CATEGORIES = [
    "Neoplasms (C04)", "Nervous System (C10)", "Cardiovascular (C14)",
    "Immune System Diseases (C20)", "Respiratory (C08)", "Digestive (C11)",
    "Musculoskeletal (C05)", "Mental Disorders (F03)", "Infections (C01)",
    "Endocrine (C19)", "Eye Diseases (C11)", "Urogenital (C12)"
]

def tg_request(method, data=None):
    url = f"{API}/{method}"
    if data:
        req = urllib.request.Request(url, data=json.dumps(data).encode(), 
                                     headers={"Content-Type": "application/json"})
    else:
        req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"TG API error: {e}")
        return {}

def get_updates(offset=0):
    result = tg_request("getUpdates", {"offset": offset, "timeout": 30})
    return result.get("result", [])

def send_message(chat_id, text):
    tg_request("sendMessage", {"chat_id": chat_id, "text": text})

def get_status():
    lines = ["**Meddash Pipeline Status**\n"]
    # Read summary JSONs
    for name in ["biocrawler", "ct_crawler", "kol_pipeline"]:
        path = os.path.join(SUMMARY_DIR, f"{name}_summary.json")
        try:
            with open(path) as f:
                s = json.load(f)
            status = s.get("status", "?")
            lines.append(f"  {name}: {status}")
        except:
            lines.append(f"  {name}: MISSING")
    
    # DB counts
    for db_file, label in [("meddash_kols.db", "KOLs"), ("ct_trials.db", "Trials"), ("biocrawler_leads.db", "Leads")]:
        path = os.path.join(DB_BASE, db_file)
        try:
            conn = sqlite3.connect(path)
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            tables = cur.fetchone()[0]
            if tables > 0:
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
                tname = cur.fetchone()[0]
                cur.execute(f"SELECT COUNT(*) FROM [{tname}]")
                count = cur.fetchone()[0]
                lines.append(f"  {label} DB: {count} rows")
            conn.close()
        except:
            lines.append(f"  {label} DB: ERROR")
    
    lines.append(f"\nDashboard: http://localhost:5090")
    lines.append(f"Checked: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC")
    return "\n".join(lines)

def get_rotation():
    week = datetime.now().isocalendar()[1]
    cat = MESHI_CATEGORIES[(week - 1) % 12]
    return f"MeSH Week {week}: {cat} (category {(week-1)%12+1}/12)"

def handle_command(text, chat_id):
    text = text.strip()
    if text == "/status":
        return get_status()
    elif text == "/rotation":
        return get_rotation()
    elif text.startswith("/help"):
        return "Meddash Pipeline Bot Commands:\n/status — Full pipeline health summary\n/rotation — Current MeSH rotation week\n/help — This message"
    else:
        return "Unknown command. Try /status, /rotation, or /help"

def main():
    print(f"[{datetime.utcnow().isoformat()}] Meddash Command Listener started")
    last_offset = 0
    while True:
        try:
            updates = get_updates(last_offset)
            for u in updates:
                last_offset = u["update_id"] + 1
                msg = u.get("message", {})
                chat_id = str(msg.get("chat", {}).get("id", ""))
                text = msg.get("text", "")
                if not text:
                    continue
                print(f"[{datetime.utcnow().isoformat()}] Received: {text} from {chat_id}")
                response = handle_command(text, chat_id)
                send_message(chat_id, response)
                print(f"[{datetime.utcnow().isoformat()}] Sent response ({len(response)} chars)")
        except Exception as e:
            print(f"[{datetime.utcnow().isoformat()}] Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()