#!/usr/bin/env python3
"""Meddash Pipeline Status — called by n8n Command Handler for /status command."""
import json, os, sqlite3
from datetime import datetime

SUMMARY_DIR = "/mnt/c/Users/email/.gemini/antigravity/Meddash_organized_backend/06_Shared_Datastores/pipeline_summaries"
DB_DIR = "/mnt/c/Users/email/.gemini/antigravity/Meddash_organized_backend/06_Shared_Datastores"

lines = ["📊 Meddash Pipeline Status", f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}", ""]

# Read summary JSONs
for f in ["biocrawler_summary.json", "ct_crawler_summary.json", "kol_pipeline_summary.json"]:
    path = os.path.join(SUMMARY_DIR, f)
    name = f.replace('.json', '').replace('_', ' ')
    try:
        data = json.load(open(path))
        mtime = datetime.fromtimestamp(os.path.getmtime(path))
        age_h = (datetime.now() - mtime).total_seconds() / 3600
        emoji = "✅" if data.get('status') == 'success' else "🟡" if data.get('status') == 'partial' else "❌"
        freshness = "FRESH" if age_h < 48 else f"STALE ({age_h:.0f}h)"
        lines.append(f"{emoji} {name}: {data.get('status', '?')} ({freshness})")
    except:
        lines.append(f"❌ {name}: MISSING")

lines.append("")
lines.append("📁 Databases:")

# Read DB counts
for db_file, table in [("biocrawler_leads.db", "biotech_leads"), ("meddash_kols.db", "kols"), ("ct_trials.db", "trials")]:
    path = os.path.join(DB_DIR, db_file)
    try:
        conn = sqlite3.connect(path)
        count = conn.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
        mtime = datetime.fromtimestamp(os.path.getmtime(path))
        age_h = (datetime.now() - mtime).total_seconds() / 3600
        freshness = "🟢" if age_h < 48 else "🔴"
        lines.append(f"  {freshness} {db_file}: {count:,} rows (updated {age_h:.0f}h ago)")
        conn.close()
    except Exception as e:
        lines.append(f"  ❌ {db_file}: {e}")

# Supabase check
try:
    import urllib.request
    req = urllib.request.Request(
        "https://tlyhaedxqrgluphwfkgu.supabase.co/rest/v1/kols?select=first_name&limit=1",
        headers={"apikey": "sb_publishable_HLJwmfBThUHD51uAJqMgAg_JuYCYvBp", "Authorization": "Bearer sb_publishable_HLJwmfBThUHD51uAJqMgAg_JuYCYvBp"}
    )
    resp = urllib.request.urlopen(req, timeout=10)
    lines.append(f"\n☁️ Supabase: ✅ Connected (HTTP {resp.status})")
except:
    lines.append(f"\n☁️ Supabase: ❌ Connection failed")

print('\n'.join(lines))