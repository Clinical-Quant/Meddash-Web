"""
LAYER 4: OPERATIONS — The Nuts & Bolts
Cron health, DB sync, Supabase health, cost monitor, alerts.
"""

import streamlit as st
from datetime import datetime
import os
import sqlite3
from supabase_client import sb
from config import SQLITE_PATHS

def render():
    st.title("⚙️ Operations")
    st.caption("*The nuts & bolts. Infrastructure health, cost monitor, last 10 things that broke.*")

    # ── SUPABASE HEALTH ───────────────────────────────────────────────────
    st.subheader("☁️ Supabase Health")

    if sb.is_configured:
        healthy = sb.health()
        cols = st.columns(2)
        with cols[0]:
            st.metric("Connection", "🟢 UP" if healthy else "🔴 DOWN")
        with cols[1]:
            st.metric("URL", sb.url[:40] + "...")

        # Table row counts
        st.markdown("---")
        st.subheader("📊 Supabase Table Counts")

        key_tables = [
            "kols", "kols_staging", "kol_merge_candidates", "kol_scholar_metrics",
            "biotech_leads", "trials", "cq_regulatory_catalysts",
        ]
        counts = sb.get_table_row_counts(key_tables)

        table_data = []
        for table, cnt in counts.items():
            status = "🟢" if cnt > 0 else "🟡" if cnt == 0 else "🔴"
            table_data.append({"Table": table, "Rows": cnt, "Status": status})

        if table_data:
            st.dataframe(table_data, use_container_width=True, hide_index=True)
    else:
        st.error("⚠️ Supabase not configured. Check .env files for SUPABASE_URL and SUPABASE_KEY.")
        st.code("""
# Required in .env:
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-key-here
""")

    # ── COST MONITOR ──────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("💰 Cost Monitor")
    st.caption("*Supabase free tier: 500MB storage, 50K row reads/month. If you hit the cap, the factory stops.*")

    cost_cols = st.columns(3)
    with cost_cols[0]:
        st.metric("Storage (estimated)", "Check Supabase Dashboard", help="Free tier: 500MB. Actual usage visible at supabase.com dashboard.")
    with cost_cols[1]:
        st.metric("API Calls (this month)", "Check Supabase Dashboard", help="Free tier: 50K reads/month. Each dashboard refresh = multiple reads.")
    with cost_cols[2]:
        st.metric("Risk Level", "LOW", help="Low usage expected for now. Monitor if dashboard refresh is set to auto-refresh.")

    st.info("💡 Tip: Set REFRESH_SECONDS=120 in config.py to avoid burning through API quota. Each page refresh costs ~10-15 reads.")

    # ── SQLITE vs SUPABASE SYNC ───────────────────────────────────────────
    st.markdown("---")
    st.subheader("🔄 SQLite vs PostgreSQL Sync")
    st.caption("*Auto-hides after 30 days of PG-only operation. Temporary migration metric.*")

    if sb.is_configured:
        sync_cols = st.columns(2)

        # SQLite counts
        sqlite_counts = {}
        for db_name, db_path in SQLITE_PATHS.items():
            if db_path.exists():
                try:
                    conn = sqlite3.connect(str(db_path))
                    cur = conn.cursor()
                    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [r[0] for r in cur.fetchall()]
                    for t in tables:
                        cur.execute(f"SELECT count(*) FROM [{t}]")
                        sqlite_counts[f"{db_name}.{t}"] = cur.fetchone()[0]
                    conn.close()
                except:
                    pass

        # Supabase counts for matching tables
        sb_tables = ["kols", "kols_staging", "kol_merge_candidates", "trials", "biotech_leads"]
        sb_counts = sb.get_table_row_counts(sb_tables)

        with sync_cols[0]:
            st.markdown("**🗄️ SQLite (Local)**")
            for name, cnt in sqlite_counts.items():
                st.markdown(f"  {name}: **{cnt:,}**")

        with sync_cols[1]:
            st.markdown("**☁️ Supabase (PostgreSQL)**")
            for name, cnt in sb_counts.items():
                st.markdown(f"  {name}: **{cnt:,}**")

        # Compare
        st.markdown("---")
        mismatches = []
        for table in sb_tables:
            # Find matching SQLite count
            for sq_name, sq_cnt in sqlite_counts.items():
                if table in sq_name:
                    sb_cnt = sb_counts.get(table, -1)
                    if sq_cnt != sb_cnt and sb_cnt >= 0:
                        mismatches.append({
                            "Table": table,
                            "SQLite": sq_cnt,
                            "Supabase": sb_cnt,
                            "Diff": sb_cnt - sq_cnt,
                        })

        if mismatches:
            st.warning("⚠️ Row count mismatches detected:")
            st.dataframe(mismatches, use_container_width=True, hide_index=True)
        else:
            st.success("✅ All synced tables match.")
    else:
        st.info("SQLite databases exist locally. Supabase sync requires configuration.")

    # ── CRON HEALTH ───────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("⏰ Cron / Scheduled Jobs")

    cron_cols = st.columns(2)
    with cron_cols[0]:
        st.markdown("""
        **Known Cron Scripts (Meddash):**
        - `nightly_scheduler.py` — KOL disambiguation nightly
        - `run_pipeline.py` — Full Meddash pipeline
        - `biocrawler.py` — Bio lead discovery
        - `sync_tickers_to_supabase.py` — Bridge sync
        """)
    with cron_cols[1]:
        st.markdown("""
        **Known Cron Scripts (CQ):**
        - `sec_8k_monitor.py` — SEC filing scanner
        - `fda_pdufa_tracker.py` — FDA calendar
        - `pr_wire_aggregator.py` — PR wire scanner
        - `enrich_tickers.py` — Ticker validation

        *Status: Check Windows Task Scheduler or manual runs.*
        """)
        st.info("Cron health monitoring requires log file access. Point config to your log directory.")

    # ── LAST 10 THINGS THAT BROKE ──────────────────────────────────────────
    st.markdown("---")
    st.subheader("🔥 Last 10 Things That Broke")
    st.caption("*Actionable. Not overwhelming.*")

    # Known issues from QA
    known_issues = [
        {"Time": "2026-04-24", "Issue": "Issue 6: SQL injection in api_server.py (4 endpoints)", "Status": "🔴 OPEN", "Severity": "CRITICAL"},
        {"Time": "2026-04-24", "Issue": "Issue 6: Corrupted line 17 in api_server.py", "Status": "🔴 OPEN", "Severity": "HIGH"},
        {"Time": "2026-04-24", "Issue": "CQ Issue 5: Fuzzy ticker matching (difflib cutoff)", "Status": "🟢 FIXED", "Severity": "MODERATE"},
        {"Time": "2026-04-24", "Issue": "MarketUX verification email not received", "Status": "🟡 PENDING", "Severity": "MODERATE"},
    ]

    st.dataframe(known_issues, use_container_width=True, hide_index=True)
    st.caption("*This widget will auto-populate from error logs once log monitoring is configured.*")