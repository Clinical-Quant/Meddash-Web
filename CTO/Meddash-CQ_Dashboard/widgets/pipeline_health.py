"""
LIVE PIPELINE HEALTH — Real-time Mermaid-style visualization of the Meddash data pipeline.
Reads summary JSONs + SQLite DBs to produce live health status overlaid on the pipeline architecture.
Non-editable, pure visual health check — Dr. Don's always-on production line monitor.
"""

import streamlit as st
from datetime import datetime, timedelta, timezone
import os
import json
import sqlite3
from config import SQLITE_PATHS, PRODUCT_PATHS

MEDDASH_ROOT = os.environ.get("MEDDASH_ROOT", str(SQLITE_PATHS["kols"].parent))
SUMMARY_DIR = os.path.join(MEDDASH_ROOT, "pipeline_summaries")
STATE_DIR = os.path.join(MEDDASH_ROOT, "pipeline_state")


def render():
    st.title("🛠️ Live Pipeline Health")
    st.caption("*Your production line — always visible. Green = healthy, yellow = stale, red = broken, grey = idle.*")

    # ── READ ALL LIVE DATA ────────────────────────────────────────────────
    summaries = _read_summaries()
    db_counts = _read_db_counts()
    rotation = _read_rotation_state()
    engine_health = _classify_health(summaries, db_counts)

    # ── TIMESTAMP BAR ────────────────────────────────────────────────────
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    overall = engine_health.get("overall", "grey")
    overall_icon = {"healthy": "🟢", "degraded": "🟡", "failed": "🔴", "idle": "⚫"}.get(overall, "⚫")
    st.markdown(f"**{overall_icon} Pipeline Status: {overall.upper()}** — Last checked: {now_utc}")

    # ── MERMAID LIVE DIAGRAM ─────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🗺️ Pipeline Architecture — Live Health Overlay")
    st.caption("*Data flows top → bottom. Node color = health. Click nothing — just watch.*")

    mermaid_code = _build_mermaid(engine_health, db_counts, rotation)
    _render_mermaid(mermaid_code)

    # ── ENGINE DETAIL CARDS ───────────────────────────────────────────────
    st.markdown("---")
    st.subheader("⚙️ Engine Detail")
    st.caption("*Per-engine health, last run, and counts.*")

    engine_cards = [
        ("01_KOL_Data_Engine", "kol_engine", "🔬", "nightly_scheduler.py"),
        ("02_CT_Data_Engine", "ct_engine", "🧪", "ct_crawler.py"),
        ("03_BioCrawler_GTM", "biocrawler", "🎯", "biocrawler.py"),
        ("04_Product_KOL_Briefs", "kol_briefs", "📄", "generate_kol_brief.py"),
        ("05_Product_TA_Landscape", "ta_landscape", "📊", "generate_ta_landscape.py"),
    ]

    cols = st.columns(len(engine_cards))
    for i, (name, key, emoji, script) in enumerate(engine_cards):
        health = engine_health.get(key, {"status": "grey"})
        status = health.get("status", "grey")
        icon = {"green": "🟢", "yellow": "🟡", "red": "🔴", "grey": "⚫"}.get(status, "⚫")
        summary = summaries.get(key, {})
        last_run = summary.get("timestamp", "Never")
        duration = summary.get("duration_seconds", "—")
        run_status = summary.get("status", "unknown")

        with cols[i]:
            border_color = {"green": "#00e676", "yellow": "#ffeb3b", "red": "#f44336", "grey": "#555"}.get(status, "#555")
            bg_color = {"green": "#0a1f0a", "yellow": "#1f1f0a", "red": "#2a0a0a", "grey": "#1a1d23"}.get(status, "#1a1d23")
            st.markdown(
                f"<div style='padding:12px; border:2px solid {border_color}; border-radius:10px; "
                f"background:{bg_color}; min-height:180px;'>"
                f"<div style='font-size:24px'>{emoji} {icon}</div>"
                f"<div style='font-size:0.85em; color:#e0e0e0; margin-top:6px; font-weight:bold'>{name}</div>"
                f"<div style='font-size:0.7em; color:#999; margin-top:4px'>{script}</div>"
                f"<div style='font-size:0.75em; color:#e0e0e0; margin-top:8px'>"
                f"═ Last: {last_run[:16] if last_run != 'Never' else 'Never'}<br>"
                f"═ Status: {run_status}<br>"
                f"═ Duration: {duration}s</div>"
                f"</div>",
                unsafe_allow_html=True
            )

    # ── DATABASE HEALTH ──────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🗄️ Database Health")
    st.caption("*Row counts + freshness. 20%+ drop = 🚨 URGENT.*")

    db_cards = [
        ("meddash_kols.db", "kols", "👥 KOLs"),
        ("biocrawler_leads.db", "biotech_leads", "🎯 Leads"),
        ("ct_trials.db", "trials", "🧪 Trials"),
    ]

    db_cols = st.columns(len(db_cards))
    for i, (db_file, table, label) in enumerate(db_cards):
        count = db_counts.get(table, 0)
        db_path = SQLITE_PATHS.get("kols" if "kols" in db_file else "biocrawler" if "biocrawler" in db_file else "trials")
        freshness = "⚫ Unknown"
        if db_path and os.path.exists(str(db_path)):
            mtime = datetime.fromtimestamp(os.path.getmtime(str(db_path)))
            age_h = (datetime.now() - mtime).total_seconds() / 3600
            freshness = f"🟢 {age_h:.1f}h ago" if age_h < 6 else f"🟡 {age_h:.1f}h ago" if age_h < 24 else f"🔴 {age_h:.0f}h STALE"

        with db_cols[i]:
            st.markdown(
                f"<div style='padding:12px; border:1px solid #2a2e35; border-radius:8px; background:#1a1d23;'>"
                f"<div style='font-size:18px; font-weight:bold; color:#e0e0e0'>{label}</div>"
                f"<div style='font-size:28px; font-weight:bold; color:#42a5f5; margin-top:4px'>{count:,}</div>"
                f"<div style='font-size:0.75em; color:#999; margin-top:4px'>Freshness: {freshness}</div>"
                f"</div>",
                unsafe_allow_html=True
            )

    # ── SUPABASE HEALTH ─────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("☁️ Supabase Health")
    st.caption("*REST API reachability + key tables row count. Critical for cloud sync.*")

    supabase_status = _check_supabase()
    sb_color = "#00e676" if supabase_status["reachable"] else "#f44336"
    sb_icon = "🟢" if supabase_status["reachable"] else "🔴"
    sb_bg = "#0a1f0a" if supabase_status["reachable"] else "#2a0a0a"

    sb_cols = st.columns(4)
    with sb_cols[0]:
        st.markdown(
            f"<div style='padding:12px; border:2px solid {sb_color}; border-radius:8px; background:{sb_bg};'>"
            f"<div style='font-size:18px; font-weight:bold; color:#e0e0e0'>REST API</div>"
            f"<div style='font-size:28px; font-weight:bold; color:{sb_color}; margin-top:4px'>{sb_icon}</div>"
            f"<div style='font-size:0.75em; color:#999; margin-top:4px'>{supabase_status.get('latency_ms', '—')}ms</div>"
            f"</div>",
            unsafe_allow_html=True
        )

    sb_tables = [("kols", "👥 KOLs"), ("biotech_leads", "🎯 Leads"), ("trials", "🧪 Trials")]
    for i, (tbl, label) in enumerate(sb_tables):
        with sb_cols[i + 1]:
            count = supabase_status.get("tables", {}).get(tbl, "—")
            if isinstance(count, int):
                ct_color = "#42a5f5"
                ct_text = f"{count:,}"
            else:
                ct_color = "#f44336"
                ct_text = "❌"
            st.markdown(
                f"<div style='padding:12px; border:1px solid #2a2e35; border-radius:8px; background:#1a1d23;'>"
                f"<div style='font-size:18px; font-weight:bold; color:#e0e0e0'>{label}</div>"
                f"<div style='font-size:28px; font-weight:bold; color:{ct_color}; margin-top:4px'>{ct_text}</div>"
                f"<div style='font-size:0.75em; color:#999; margin-top:4px'>pg: {tbl}</div>"
                f"</div>",
                unsafe_allow_html=True
            )

    # ── MeSH ROTATION ────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🔄 MeSH Rotation")
    if rotation:
        cat = rotation.get("current_category", "Unknown")
        week = rotation.get("current_week", 0)
        cycle = rotation.get("cycle_count", 0)
        completed = rotation.get("categories_completed_this_cycle", [])
        st.markdown(
            f"<div style='padding:12px; border:1px solid #42a5f5; border-radius:8px; background:#1a2332;'>"
            f"<div style='font-size:18px; color:#42a5f5;'>{cat}</div>"
            f"<div style='font-size:0.85em; color:#e0e0e0; margin-top:6px'>Week {week}/12 • Cycle {cycle}</div>"
            f"<div style='font-size:0.75em; color:#999; margin-top:4px'>Completed: {len(completed)} categories</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    else:
        st.info("No rotation state found. Run the pipeline first.")


# ══════════════════════════════════════════════════════════════════════════
# DATA READERS
# ══════════════════════════════════════════════════════════════════════════

def _read_summaries():
    """Read all pipeline summary JSONs."""
    summaries = {}
    if not os.path.isdir(SUMMARY_DIR):
        return summaries

    summary_map = {
        "kol_pipeline_summary.json": "kol_engine",
        "biocrawler_summary.json": "biocrawler",
        "ct_crawler_summary.json": "ct_engine",
    }
    for filename, key in summary_map.items():
        filepath = os.path.join(SUMMARY_DIR, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                data["_mtime"] = os.path.getmtime(filepath)
                data["_age_hours"] = (datetime.now().timestamp() - data["_mtime"]) / 3600
                summaries[key] = data
            except Exception:
                summaries[key] = {"status": "error", "_age_hours": 999}
        else:
            summaries[key] = {"status": "missing", "_age_hours": 999}

    # Product engines — check by file existence in product dirs
    brief_dir = PRODUCT_PATHS.get("kol_briefs")
    if brief_dir and os.path.exists(str(brief_dir)):
        week_ago = datetime.now().timestamp() - 604800
        recent = sum(1 for f in os.scandir(str(brief_dir)) if f.is_file() and f.stat().st_mtime > week_ago)
        summaries["kol_briefs"] = {"status": "active" if recent > 0 else "idle", "recent_week": recent, "_age_hours": 0}
    else:
        summaries["kol_briefs"] = {"status": "missing", "_age_hours": 999}

    ta_dir = PRODUCT_PATHS.get("ta_landscapes")
    if ta_dir and os.path.exists(str(ta_dir)):
        week_ago = datetime.now().timestamp() - 604800
        recent = sum(1 for f in os.scandir(str(ta_dir)) if f.is_file() and f.stat().st_mtime > week_ago)
        summaries["ta_landscape"] = {"status": "active" if recent > 0 else "idle", "recent_week": recent, "_age_hours": 0}
    else:
        summaries["ta_landscape"] = {"status": "missing", "_age_hours": 999}

    return summaries


def _read_db_counts():
    """Get row counts from all SQLite DBs."""
    counts = {}
    db_table_map = {
        "kols": ("kols", "kols"),
        "biocrawler": ("biocrawler", "biotech_leads"),
        "trials": ("trials", "trials"),
    }
    for db_key, (_, table) in db_table_map.items():
        db_path = SQLITE_PATHS.get(db_key)
        if db_path and os.path.exists(str(db_path)):
            try:
                conn = sqlite3.connect(str(db_path))
                cur = conn.cursor()
                cur.execute(f"SELECT count(*) FROM {table}")
                counts[table] = cur.fetchone()[0]
                conn.close()
            except Exception:
                counts[table] = -1
        else:
            counts[table] = 0
    return counts


def _read_rotation_state():
    """Read MeSH rotation state file."""
    state_file = os.path.join(STATE_DIR, "mesh_rotation_state.json")
    if os.path.exists(state_file):
        try:
            with open(state_file, "r") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def _classify_health(summaries, db_counts):
    """Classify each engine as green/yellow/red/grey and determine overall status."""
    health = {}
    has_any = False
    has_failure = False

    for key, summary in summaries.items():
        status_val = summary.get("status", "missing")
        age_h = summary.get("_age_hours", 999)

        if status_val == "failure" or status_val == "error":
            health[key] = {"status": "red", "detail": "failure"}
            has_failure = True
        elif status_val == "missing":
            health[key] = {"status": "grey", "detail": "no data"}
        elif age_h > 24:
            health[key] = {"status": "yellow", "detail": f"stale ({age_h:.0f}h)"}
            has_any = True
        elif age_h > 6:
            health[key] = {"status": "yellow", "detail": f"aging ({age_h:.1f}h)"}
            has_any = True
        elif status_val in ("success", "active", "api", "deep", "all"):
            health[key] = {"status": "green", "detail": "healthy"}
            has_any = True
        elif status_val in ("idle", "partial"):
            health[key] = {"status": "grey", "detail": status_val}
            has_any = True
        else:
            health[key] = {"status": "grey", "detail": status_val}

    if has_failure:
        health["overall"] = "failed"
    elif any(h["status"] == "yellow" for h in health.values() if isinstance(h, dict)):
        health["overall"] = "degraded"
    elif has_any:
        health["overall"] = "healthy"
    else:
        health["overall"] = "idle"

    return health


# ══════════════════════════════════════════════════════════════════════════
# MERMAID DIAGRAM BUILDER
# ══════════════════════════════════════════════════════════════════════════

def _hcolor(status):
    """Map engine health status to Mermaid node fill color."""
    return {
        "green": "#1b5e20",
        "yellow": "#4e342e",
        "red": "#b71c1c",
        "grey": "#263238",
    }.get(status, "#263238")


def _hstroke(status):
    """Map engine health status to Mermaid node border color."""
    return {
        "green": "#00e676",
        "yellow": "#ffeb3b",
        "red": "#f44336",
        "grey": "#546e7a",
    }.get(status, "#546e7a")


def _build_mermaid(engine_health, db_counts, rotation):
    """Build the live Mermaid flowchart with health-colored nodes."""

    # Engine health colors
    kol_h = engine_health.get("kol_engine", {}).get("status", "grey")
    ct_h = engine_health.get("ct_engine", {}).get("status", "grey")
    bio_h = engine_health.get("biocrawler", {}).get("status", "grey")
    brief_h = engine_health.get("kol_briefs", {}).get("status", "grey")
    ta_h = engine_health.get("ta_landscape", {}).get("status", "grey")

    # DB labels with counts
    kols_count = db_counts.get("kols", 0)
    leads_count = db_counts.get("biotech_leads", 0)
    trials_count = db_counts.get("trials", 0)

    # Rotation label
    rot_cat = rotation.get("current_category", "—") if rotation else "—"
    rot_week = rotation.get("current_week", "0") if rotation else "0"

    # Overall pipeline color
    overall = engine_health.get("overall", "grey")

    m = f"""---
config:
  layout: elk
  theme: dark
---
flowchart TB
  subgraph triggers["⚡ Triggers"]
    n8n_cron["n8n Morning Cron"]
    telegram_cmd["Telegram /run"]
  end

  subgraph engines["🔧 Data Engines"]
    nightly["🔬 KOL Engine\\nnightly_scheduler.py\\n{kols_count:,} KOLs"]
    biocrawler["🎯 BioCrawler\\nbiocrawler.py\\n{leads_count:,} Leads"]
    ct_crawler["🧪 CT Engine\\nct_crawler.py\\n{trials_count:,} Trials"]
  end

  subgraph products["📦 Products"]
    kol_brief["📄 KOL Briefs\\n$2,450/revenue"]
    ta_landscape["📊 TA Landscapes\\nProduct output"]
  end

  subgraph databases["🗄️ Datastores"]
    kols_db[("👥 meddash_kols.db\\n{kols_count:,} rows")]
    leads_db[("🎯 biocrawler_leads.db\\n{leads_count:,} rows")]
    trials_db[("🧪 ct_trials.db\\n{trials_count:,} rows")]
  end

  subgraph devops["🛠️ DevOps"]
    mesh_rot["🔄 MeSH Rotation\\n{rot_cat} Wk{rot_week}/12"]
    summaries["📋 pipeline_summaries/"]
    monitor["👁️ Monitor Agent\\nministral-3:3b"]
  end

  subgraph triarchy["🏛️ Triarchy"]
    hands["🤚 n8n\\nDeterministic Hands"]
    workers["🧠 Paperclip\\nLLM Workers"]
    eye["👁️ Alfred Chief\\nEye + Fixer"]
  end

  triggers --> nightly
  triggers --> biocrawler
  triggers --> ct_crawler

  nightly --> kols_db
  biocrawler --> leads_db
  ct_crawler --> trials_db

  kols_db --> kol_brief
  leads_db --> kol_brief
  trials_db --> kol_brief
  kols_db --> ta_landscape
  leads_db --> ta_landscape
  trials_db --> ta_landscape

  biocrawler -. "T1 leads" .-> mesh_rot
  mesh_rot -. "T2 rotation" .-> nightly

  nightly --> summaries
  biocrawler --> summaries
  ct_crawler --> summaries

  summaries --> monitor
  monitor -. "escalate" .-> workers

  hands --> nightly
  hands --> biocrawler
  hands --> ct_crawler
  workers --> monitor
  eye -. "break-glass" .-> workers

  style nightly fill:{_hcolor(kol_h)},stroke:{_hstroke(kol_h)},stroke-width:3px,color:#e0e0e0
  style biocrawler fill:{_hcolor(bio_h)},stroke:{_hstroke(bio_h)},stroke-width:3px,color:#e0e0e0
  style ct_crawler fill:{_hcolor(ct_h)},stroke:{_hstroke(ct_h)},stroke-width:3px,color:#e0e0e0
  style kol_brief fill:{_hcolor(brief_h)},stroke:{_hstroke(brief_h)},stroke-width:3px,color:#e0e0e0
  style ta_landscape fill:{_hcolor(ta_h)},stroke:{_hstroke(ta_h)},stroke-width:3px,color:#e0e0e0
  style kols_db fill:#1a2332,stroke:#42a5f5,stroke-width:2px,color:#e0e0e0
  style leads_db fill:#1a2332,stroke:#42a5f5,stroke-width:2px,color:#e0e0e0
  style trials_db fill:#1a2332,stroke:#42a5f5,stroke-width:2px,color:#e0e0e0
  style mesh_rot fill:#1a2332,stroke:#ab47bc,stroke-width:2px,color:#e0e0e0
  style summaries fill:#1a2332,stroke:#78909c,stroke-width:2px,color:#e0e0e0
  style monitor fill:#1a2332,stroke:#00e676,stroke-width:2px,color:#e0e0e0
  style triggers fill:#1a2332,stroke:#ffa726,stroke-width:2px,color:#e0e0e0
  style hands fill:#1a2332,stroke:#ffa726,stroke-width:2px,color:#e0e0e0
  style workers fill:#1a2332,stroke:#ce93d8,stroke-width:2px,color:#e0e0e0
  style eye fill:#1a2332,stroke:#f44336,stroke-width:2px,color:#e0e0e0
  style n8n_cron fill:#2e2a1a,stroke:#ffa726,stroke-width:2px,color:#e0e0e0
  style telegram_cmd fill:#2e2a1a,stroke:#ffa726,stroke-width:2px,color:#e0e0e0
  style products fill:#0d1117,stroke:#42a5f5,stroke-width:2px,color:#e0e0e0
  style engines fill:#0d1117,stroke:#78909c,stroke-width:2px,color:#e0e0e0
  style databases fill:#0d1117,stroke:#42a5f5,stroke-width:2px,color:#e0e0e0
  style devops fill:#0d1117,stroke:#ab47bc,stroke-width:2px,color:#e0e0e0
  style triarchy fill:#0d1117,stroke:#ce93d8,stroke-width:2px,color:#e0e0e0
"""
    return m.format(
        kols_count=kols_count,
        leads_count=leads_count,
        trials_count=trials_count,
        rot_cat=rot_cat,
        rot_week=rot_week,
    )


def _render_mermaid(mermaid_code):
    """Render Mermaid diagram using CDN via iframe with srcdoc."""
    html = f"""<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
  <style>
    body {{
      margin: 0;
      padding: 16px;
      background: #0e1117;
      font-family: 'Source Sans Pro', sans-serif;
    }}
    .mermaid {{
      display: flex;
      justify-content: center;
    }}
    @keyframes node-pulse-green {{
      0%, 100% {{ filter: drop-shadow(0 0 2px rgba(0,230,118,0.3)); }}
      50% {{ filter: drop-shadow(0 0 8px rgba(0,230,118,0.6)); }}
    }}
    @keyframes node-pulse-red {{
      0%, 100% {{ filter: drop-shadow(0 0 2px rgba(244,67,54,0.4)); }}
      50% {{ filter: drop-shadow(0 0 12px rgba(244,67,54,0.7)); }}
    }}
    @keyframes flow-dash {{
      0% {{ stroke-dashoffset: 20; }}
      100% {{ stroke-dashoffset: 0; }}
    }}
    .edge-pattern-solid {{
      stroke-dasharray: 5 3;
      animation: flow-dash 1.5s linear infinite;
    }}
  </style>
</head>
<body>
  <div class="mermaid">
{mermaid_code}
  </div>
  <script>
    mermaid.initialize({{
      startOnLoad: true,
      theme: 'dark',
      themeVariables: {{
        darkMode: true,
        background: '#0e1117',
        primaryColor: '#1a2332',
        primaryTextColor: '#e0e0e0',
        primaryBorderColor: '#42a5f5',
        lineColor: '#546e7a',
        secondaryColor: '#1e2228',
        tertiaryColor: '#1a1d23',
        fontFamily: 'Source Sans Pro, sans-serif',
        fontSize: '13px',
      }},
      flowchart: {{
        useMaxWidth: true,
        htmlLabels: true,
        curve: 'basis',
        nodeSpacing: 40,
        rankSpacing: 50,
        padding: 15,
      }},
      elk: {{
        nodePlacementStrategy: 'BRANDES_KOEPF'
      }}
    }});
  </script>
</body>
</html>"""
    # Encode as base64 data URI for iframe — avoids Streamlit html() API version issues
    import base64
    encoded = base64.b64encode(html.encode('utf-8')).decode('utf-8')
    iframe_src = f"data:text/html;base64,{encoded}"
    iframe_html = f'<iframe src="{iframe_src}" width="100%" height="750" style="border:none; border-radius:8px; background:#0e1117;" sandbox="allow-scripts"></iframe>'
    st.markdown(iframe_html, unsafe_allow_html=True)


def _check_supabase():
    """Check Supabase REST API reachability and row counts for key tables."""
    import urllib.request
    import urllib.error

    result = {"reachable": False, "latency_ms": None, "tables": {}}

    supabase_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    supabase_key = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

    if not supabase_url or not supabase_key:
        # Try loading from .env
        env_file = os.path.join(MEDDASH_ROOT, ".env")
        if os.path.exists(env_file):
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("SUPABASE_URL="):
                        supabase_url = line.split("=", 1)[1].strip('"').strip("'").rstrip("/")
                    elif line.startswith("SUPABASE_KEY="):
                        supabase_key = line.split("=", 1)[1].strip('"').strip("'")
                    elif line.startswith("SUPABASE_SERVICE_ROLE_KEY="):
                        if not supabase_key:
                            supabase_key = line.split("=", 1)[1].strip('"').strip("'")

    if not supabase_url or not supabase_key:
        result["reachable"] = False
        result["error"] = "No SUPABASE_URL or KEY configured"
        return result

    # Check REST API reachability
    try:
        start = datetime.now()
        req = urllib.request.Request(
            f"{supabase_url}/rest/v1/kols?select=first_name&limit=1",
            headers={"apikey": supabase_key, "Authorization": f"Bearer {supabase_key}"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            latency = (datetime.now() - start).total_seconds() * 1000
            result["reachable"] = True
            result["latency_ms"] = int(latency)
    except Exception as e:
        result["reachable"] = False
        result["error"] = str(e)[:200]
        return result

    # Get row counts for key tables (use actual column names per Supabase schema)
    sb_columns = {"kols": "first_name", "biotech_leads": "company_slug", "trials": "nct_id"}
    for table, col in sb_columns.items():
        try:
            req = urllib.request.Request(
                f"{supabase_url}/rest/v1/{table}?select={col}&limit=1",
                headers={"apikey": supabase_key, "Authorization": f"Bearer {supabase_key}",
                          "Prefer": "count=exact"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                # Supabase returns total count in Content-Range header
                content_range = resp.headers.get("Content-Range", "")
                # Parse "0-0/8298" or "*/0" format
                if "/" in content_range:
                    count_str = content_range.split("/")[-1]
                    try:
                        result["tables"][table] = int(count_str)
                    except ValueError:
                        result["tables"][table] = 0 if count_str == "*" else "accessible"
                else:
                    # Fallback: just mark as accessible
                    result["tables"][table] = "accessible"
        except urllib.error.HTTPError as e:
            if e.code == 400:
                # Table exists but schema mismatch — still count as accessible
                result["tables"][table] = "schema_mismatch"
            else:
                result["tables"][table] = f"error_{e.code}"
        except Exception:
            result["tables"][table] = "error"

    return result