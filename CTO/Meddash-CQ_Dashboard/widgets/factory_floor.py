"""
LAYER 5: THE BRIDGE — Factory Floor
Animated Mermaid-style data flow diagram of the MEDDASH-CQ production line.
This is the centerpiece — Dr. Don's factory.
"""

import streamlit as st
from datetime import datetime, timedelta
import os
import sqlite3
from supabase_client import sb
from config import SQLITE_PATHS, PRODUCT_PATHS

def render():
    st.title("🏭 Factory Floor")
    st.caption("*This is your factory. The production line. Watch it flow.*")

    # ── FACTORY OUTPUT (top of page — the most important metric) ───────────
    st.markdown("---")
    st.subheader("📦 Factory Output This Week")
    cols = st.columns(4)

    # Count briefs
    brief_path = PRODUCT_PATHS.get("kol_briefs")
    briefs_this_week = 0
    if brief_path and brief_path.exists():
        week_ago = datetime.now() - timedelta(days=7)
        for f in brief_path.iterdir():
            if f.is_file() and f.stat().st_mtime > week_ago.timestamp():
                briefs_this_week += 1

    # Count TA landscapes
    ta_path = PRODUCT_PATHS.get("ta_landscapes")
    ta_this_week = 0
    if ta_path and ta_path.exists():
        week_ago = datetime.now() - timedelta(days=7)
        for f in ta_path.iterdir():
            if f.is_file() and f.stat().st_mtime > week_ago.timestamp():
                ta_this_week += 1

    # CQ posts — placeholder (newsletter not automated yet)
    cq_posts_this_week = 0

    with cols[0]:
        if briefs_this_week > 0:
            st.markdown('<div class="output-producing">', unsafe_allow_html=True)
            st.metric("KOL Briefs", briefs_this_week, delta="PRODUCING")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="output-zero">', unsafe_allow_html=True)
            st.metric("KOL Briefs", 0, delta="IDLE", delta_color="inverse")
            st.markdown('</div>', unsafe_allow_html=True)
    with cols[1]:
        if ta_this_week > 0:
            st.markdown('<div class="output-producing">', unsafe_allow_html=True)
            st.metric("TA Landscapes", ta_this_week, delta="PRODUCING")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="output-zero">', unsafe_allow_html=True)
            st.metric("TA Landscapes", 0, delta="IDLE", delta_color="inverse")
            st.markdown('</div>', unsafe_allow_html=True)
    with cols[2]:
        if cq_posts_this_week > 0:
            st.markdown('<div class="output-producing">', unsafe_allow_html=True)
            st.metric("CQ Posts", cq_posts_this_week, delta="PRODUCING")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="output-zero">', unsafe_allow_html=True)
            st.metric("CQ Posts", 0, delta="IDLE", delta_color="inverse")
            st.markdown('</div>', unsafe_allow_html=True)
    with cols[3]:
        revenue = briefs_this_week * 2450
        if revenue > 0:
            st.metric("Revenue This Week", f"${revenue:,}", delta="🟢 CASH FLOWING")
        else:
            st.metric("Revenue This Week", "$0", delta="🔴 NO REVENUE", delta_color="inverse")

    # ── DATA INVENTORY (warehouse counts) ──────────────────────────────────
    st.markdown("---")
    st.subheader("🗂️ Data Inventory")
    st.caption("*Your stock. If inventory is low, you can't fulfill orders.*")

    # SQLite counts
    inventory = {}
    for db_name, db_path in SQLITE_PATHS.items():
        if db_path.exists():
            try:
                conn = sqlite3.connect(str(db_path))
                cur = conn.cursor()
                # Get list of tables
                cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [r[0] for r in cur.fetchall()]
                counts = {}
                for t in tables:
                    try:
                        cur.execute(f"SELECT count(*) FROM [{t}]")
                        counts[t] = cur.fetchone()[0]
                    except:
                        pass
                inventory[db_name] = counts
                conn.close()
            except:
                inventory[db_name] = {"ERROR": -1}
        else:
            inventory[db_name] = {"NOT FOUND": 0}

    # Supabase counts (key tables)
    sb_tables = ["kols", "kols_staging", "kol_merge_candidates", "kol_scholar_metrics",
                  "biotech_leads", "trials", "cq_regulatory_catalysts"]
    sb_counts = {}
    if sb.is_configured:
        sb_counts = sb.get_table_row_counts(sb_tables)

    inv_cols = st.columns(3)
    for i, (db_name, tables) in enumerate(inventory.items()):
        with inv_cols[i]:
            st.markdown(f"**🗄️ {db_name}.db**")
            for table, cnt in tables.items():
                health = "🟢" if cnt > 0 else "🟡" if cnt == 0 else "🔴"
                st.markdown(f"  {health} {table}: **{cnt:,}**")

    if sb_counts:
        with inv_cols[2]:
            st.markdown("**☁️ Supabase (PostgreSQL)**")
            for table, cnt in sb_counts.items():
                health = "🟢" if cnt > 0 else "🟡" if cnt == 0 else "🔴"
                st.markdown(f"  {health} {table}: **{cnt:,}**")

    # ── ANIMATED DATA FLOW DIAGRAM ────────────────────────────────────────
    st.markdown("---")
    st.subheader("🔀 Production Line — Data Flow")
    st.caption("*Active engines pulse green. Idle grey. Broken flash red. Arrow thickness = data volume.*")

    # Build the flow diagram using Streamlit columns + HTML/CSS
    # This is the Mermaid-style flow, recreated with Streamlit layout

    # Get engine health for coloring
    engine_status = _get_engine_status()

    # ROW 1: Meddash Engine → Products
    st.markdown('<div class="meddash-header"><h3>🔬 MEDDASH Department</h3></div>', unsafe_allow_html=True)

    m_cols = st.columns(7)
    engines_meddash = [
        ("KOL\nEngine", "kol_engine"),
        ("CT\nEngine", "ct_engine"),
        ("BioCrawler\nGTM", "biocrawler"),
        ("Bridge\nEngine", "bridge"),
        ("Scholar\nScraper", "scholar"),
    ]

    for i, (name, key) in enumerate(engines_meddash):
        status = engine_status.get(key, "grey")
        icon = {"green": "🟢", "yellow": "🟡", "red": "🔴", "grey": "⚫"}.get(status, "⚫")
        with m_cols[i]:
            st.markdown(f"<div style='text-align:center; padding:8px; border:1px solid #2a2e35; border-radius:8px; background:#1a1d23;'>"
                        f"<div style='font-size:24px'>{icon}</div>"
                        f"<div style='font-size:0.75em; color:#e0e0e0; margin-top:4px'>{name}</div>"
                        f"</div>", unsafe_allow_html=True)
        # Arrow between engines
        if i < len(engines_meddash) - 1:
            with m_cols[i]:
                st.markdown("<div class='flow-arrow'>→</div>", unsafe_allow_html=True)

    # Arrow down to products
    st.markdown("<div class='flow-arrow' style='font-size:32px; padding: 4px 0;'>⬇</div>", unsafe_allow_html=True)

    p_cols = st.columns(2)
    with p_cols[0]:
        st.markdown("<div style='text-align:center; padding:12px; border:2px solid #42a5f5; border-radius:8px; background:#1a2332;'>"
                    "<div style='font-size:18px'>📄 KOL Briefs</div>"
                    "<div style='font-size:0.8em; color:#42a5f5'>$2,450/revenue</div>"
                    "</div>", unsafe_allow_html=True)
    with p_cols[1]:
        st.markdown("<div style='text-align:center; padding:12px; border:2px solid #42a5f5; border-radius:8px; background:#1a2332;'>"
                    "<div style='font-size:18px'>📊 TA Landscapes</div>"
                    "<div style='font-size:0.8em; color:#42a5f5'>Product output</div>"
                    "</div>", unsafe_allow_html=True)

    # ROW 2: CQ Engine → Newsletter
    st.markdown("---")
    st.markdown('<div class="cq-header"><h3>💊 CLINICAL QUANT Department</h3></div>', unsafe_allow_html=True)

    cq_cols = st.columns(5)
    engines_cq = [
        ("SEC 8K\nMonitor", "sec_8k"),
        ("FDA PDUFA\nTracker", "fda_pdufa"),
        ("PR Wire\nAggregator", "pr_wire"),
        ("Ticker\nEnrichment", "ticker_enrich"),
        ("Permanent\nAgent ✨", "cq_agent"),
    ]

    for i, (name, key) in enumerate(engines_cq):
        status = engine_status.get(key, "grey")
        icon = {"green": "🟢", "yellow": "🟡", "red": "🔴", "grey": "⚫"}.get(status, "⚫")
        label = "✨" if key == "cq_agent" else icon
        with cq_cols[i]:
            border_color = "#66bb6a" if key == "cq_agent" else "#2a2e35"
            st.markdown(f"<div style='text-align:center; padding:8px; border:1px solid {border_color}; border-radius:8px; background:#1a1d23;'>"
                        f"<div style='font-size:24px'>{icon}</div>"
                        f"<div style='font-size:0.7em; color:#e0e0e0; margin-top:4px'>{name}</div>"
                        f"</div>", unsafe_allow_html=True)

    # Arrow down to CQ output
    st.markdown("<div class='flow-arrow' style='font-size:32px; padding: 4px 0;'>⬇</div>", unsafe_allow_html=True)

    # CQ Agent Pipeline (CEO request: catalyst → research → verify → draft → approval → post)
    agent_cols = st.columns(6)
    agent_stages = [
        ("🔍 Detect", "Catalyst found"),
        ("🔬 Research", "Deep analysis"),
        ("✅ Verify", "Fact check"),
        ("📝 Draft", "Write post"),
        ("👨‍⚕️ Approve", "CEO review"),
        ("📢 Publish", "CQ Free Newsletter"),
    ]
    for i, (stage, desc) in enumerate(agent_stages):
        with agent_cols[i]:
            # First 4 are automated, last 2 need human
            auto = i < 4
            bg = "#1a2e1a" if auto else "#2e2a1a"
            border = "#66bb6a" if auto else "#ffa726"
            st.markdown(f"<div style='text-align:center; padding:8px; border:1px solid {border}; border-radius:8px; background:{bg};'>"
                        f"<div style='font-size:14px'>{stage}</div>"
                        f"<div style='font-size:0.65em; color:#999; margin-top:2px'>{desc}</div>"
                        f"<div style='font-size:0.6em; color:{border}; margin-top:2px'>{('AUTO' if auto else 'MANUAL')}</div>"
                        f"</div>", unsafe_allow_html=True)

    # ── BRIDGE SPINE ───────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🔗 Bridge Spine (Meddash → CQ)")
    st.caption("*The shared data spine. Biotech leads with tickers flow from Meddash into CQ catalyst tracking.*")

    # Ticker bridge stats
    leads_total = 0
    leads_with_tickers = 0
    if sb.is_configured:
        leads_total = sb.count("biotech_leads")
        leads_with_tickers = sb.count_with_filter("biotech_leads", "ticker", "not.is", None)

    bridging = leads_with_tickers if leads_with_tickers > 0 else 0
    missing = leads_total - bridging if leads_total > 0 else 0

    b_cols = st.columns(3)
    with b_cols[0]:
        st.metric("Leads with Tickers", bridging, help="These flow into CQ")
    with b_cols[1]:
        st.metric("Leads Missing Tickers", missing, help="Gap in the bridge", delta_color="inverse")
    with b_cols[2]:
        pct = (bridging / leads_total * 100) if leads_total > 0 else 0
        st.metric("Bridge Completion", f"{pct:.0f}%")

    # Visual bridge
    if leads_total > 0:
        st.progress(pct / 100, text=f"Bridge: {bridging}/{leads_total} leads have tickers → flow to CQ")


def _get_engine_status():
    """Check engine health: green=recent activity, yellow=stale, red=error, grey=unknown."""
    status = {}
    # Check SQLite modification times as proxy for engine activity
    for db_name, db_path in SQLITE_PATHS.items():
        if db_path.exists():
            mtime = datetime.fromtimestamp(db_path.stat().st_mtime)
            age_hours = (datetime.now() - mtime).total_seconds() / 3600
            if age_hours < 6:
                status[db_name] = "green"
            elif age_hours < 24:
                status[db_name] = "yellow"
            else:
                status[db_name] = "grey"
        else:
            status[db_name] = "red"

    # Map SQLite names to engine names
    engine_map = {
        "kol_engine": status.get("kols", "grey"),
        "ct_engine": status.get("trials", "grey"),
        "biocrawler": status.get("biocrawler", "grey"),
        "bridge": "grey",      # bridge_engine.py doesn't have its own DB
        "scholar": "grey",     # scholar metrics are in kols DB
        "sec_8k": "grey",      # CQ engines — check Supabase
        "fda_pdufa": "grey",
        "pr_wire": "grey",
        "ticker_enrich": "grey",
        "cq_agent": "grey",    # permanent agent — not yet running
    }

    # If Supabase has recent catalysts, CQ engines are green
    if sb.is_configured:
        catalysts = sb.select("cq_regulatory_catalysts", columns="created_at", limit=1)
        if catalysts:
            try:
                latest = catalysts[0].get("created_at", "")
                if latest:
                    # If any catalyst in last 48h, engines are green
                    from datetime import timezone
                    latest_dt = datetime.fromisoformat(latest.replace("Z", "+00:00"))
                    age_h = (datetime.now(timezone.utc) - latest_dt).total_seconds() / 3600
                    if age_h < 48:
                        engine_map["sec_8k"] = "green"
                        engine_map["fda_pdufa"] = "green"
                        engine_map["pr_wire"] = "green"
            except:
                pass

    return engine_map