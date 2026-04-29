"""
LAYER 1: THE PULSE — Top Bar Metrics
Always-visible heartbeat of the factory.
Shows: health, deltas, staleness, and production output.
"""

import streamlit as st
from datetime import datetime, timedelta
import json
import os
import sqlite3
from supabase_client import sb
from config import SQLITE_PATHS, PRODUCT_PATHS

def render():
    st.title("💗 Pulse — Factory Heartbeat")
    st.caption("*Stale green lights are lying lights. Deltas beat totals. CRM/revenue stays hidden until connected.*")

    # ── ROW 1: Engine Heartbeat ────────────────────────────────────────────
    st.subheader("🫀 Engine Heartbeat")
    cols = st.columns(7)

    engines = [
        ("KOL Engine", "kols"),
        ("Centrality", "centrality_summary"),
        ("CT Engine", "trials"),
        ("BioCrawler", "biocrawler"),
        ("SEC 8K", None),     # Supabase-only
        ("FDA/PDUFA", None),
        ("PR Wire", None),
    ]

    for i, (name, db_key) in enumerate(engines):
        with cols[i]:
            if db_key == "centrality_summary":
                _render_centrality_heartbeat(name)
            elif db_key and db_key in SQLITE_PATHS:
                db_path = SQLITE_PATHS[db_key]
                if db_path.exists():
                    mtime = datetime.fromtimestamp(db_path.stat().st_mtime)
                    age_h = (datetime.now() - mtime).total_seconds() / 3600
                    if age_h < 6:
                        st.markdown(f"🟢 **{name}**")
                        st.caption(f"Last: {mtime.strftime('%H:%M')} ({age_h:.1f}h ago)")
                    elif age_h < 24:
                        st.markdown(f"🟡 **{name}**")
                        st.caption(f"Last: {mtime.strftime('%H:%M %m/%d')} ({age_h:.1f}h ago)")
                    else:
                        st.markdown(f"🔴 **{name}**")
                        st.caption(f"Last: {mtime.strftime('%m/%d')} ({age_h:.0f}h STALE")
                else:
                    st.markdown(f"⚫ **{name}**")
                    st.caption("DB not found")
            else:
                # Check Supabase for CQ engines
                if sb.is_configured:
                    try:
                        rows = sb.select("cq_regulatory_catalysts",
                                         columns="created_at",
                                         filters={"source_type": "SEC_8K" if "SEC" in name else "FDA_PDUFA" if "FDA" in name else "PR_WIRE"},
                                         limit=1)
                        if rows:
                            st.markdown(f"🟢 **{name}**")
                            st.caption("Active in Supabase")
                        else:
                            st.markdown(f"🟡 **{name}**")
                            st.caption("No recent data")
                    except:
                        st.markdown(f"⚫ **{name}**")
                        st.caption("Check failed")
                else:
                    st.markdown(f"⚫ **{name}**")
                    st.caption("No Supabase")

    # ── ROW 2: Core Metrics with Deltas ────────────────────────────────────
    st.markdown("---")
    st.subheader("📊 Core Metrics")
    m_cols = st.columns(6)

    # KOLs
    with m_cols[0]:
        kol_count = _sqlite_count("kols", "kols")
        kol_staging = _sqlite_count("kols", "kols_staging")
        sb_kols = sb.count("kols") if sb.is_configured else -1
        total = kol_count or sb_kols or 0
        st.metric("KOLs", f"{total:,}", delta="+staging: {:,}".format(kol_staging) if kol_staging else None)

    # Biotech Leads by tier
    with m_cols[1]:
        leads_total = sb.count("biotech_leads") if sb.is_configured else 0
        tier_a = 0
        if sb.is_configured:
            tier_rows = sb.select("biotech_leads", columns="tier", limit=1000)
            tier_counts = {}
            for r in tier_rows:
                t = r.get("tier", "unclassified")
                tier_counts[t] = tier_counts.get(t, 0) + 1
            tier_a = tier_counts.get("A", 0)
            st.metric("Biotech Leads", f"{leads_total:,}", delta=f"Tier A: {tier_a}")
        else:
            st.metric("Biotech Leads", leads_total or "—")

    # CQ Catalysts
    with m_cols[2]:
        cat_total = sb.count("cq_regulatory_catalysts") if sb.is_configured else 0
        cat_week = 0
        if sb.is_configured:
            # Approximate: get recent catalysts
            recent = sb.select("cq_regulatory_catalysts", columns="created_at", limit=100)
            week_ago = datetime.now() - timedelta(days=7)
            for r in recent:
                try:
                    ca = r.get("created_at", "")
                    if ca:
                        dt = datetime.fromisoformat(ca.replace("Z", "+00:00"))
                        if dt > week_ago.replace(tzinfo=dt.tzinfo):
                            cat_week += 1
                except:
                    pass
        st.metric("CQ Catalysts", f"{cat_total:,}", delta=f"+{cat_week} this week")

    # CT Trials
    with m_cols[3]:
        ct_count = _sqlite_count("trials", "ct_trials")
        sb_ct = sb.count("trials") if sb.is_configured else -1
        total_ct = ct_count or sb_ct or 0
        st.metric("CT Trials", f"{total_ct:,}")

    # Centrality Scores
    with m_cols[4]:
        centrality = _get_centrality_summary()
        st.metric("Centrality Scores", f"{centrality.get('scores_written', 0):,}", delta=f"Tier 1: {centrality.get('tier1', 0):,}")

    # Production output placeholder — not revenue
    with m_cols[5]:
        brief_path = PRODUCT_PATHS.get("kol_briefs")
        brief_count = 0
        if brief_path and brief_path.exists():
            brief_count = sum(1 for f in brief_path.iterdir() if f.is_file())
        st.metric("KOL Brief Files", f"{brief_count:,}", delta="CRM not connected")

    # ── ROW 3: Last Crawl Staleness ───────────────────────────────────────
    st.markdown("---")
    st.subheader("⏱️ Last Crawl Staleness")
    st.caption("*Green = <6h, Yellow = <24h, Red = >24h, Grey = unknown*")

    staleness_data = []
    for db_name, db_path in SQLITE_PATHS.items():
        if db_path.exists():
            mtime = datetime.fromtimestamp(db_path.stat().st_mtime)
            age_h = (datetime.now() - mtime).total_seconds() / 3600
            status = "🟢" if age_h < 6 else "🟡" if age_h < 24 else "🔴"
            staleness_data.append({"Engine": db_name, "Last Modified": mtime.strftime("%Y-%m-%d %H:%M"), "Age (hours)": f"{age_h:.1f}", "Status": status})

    centrality_path = SQLITE_PATHS["kols"].parent / "pipeline_summaries" / "kol_centrality_summary.json"
    if centrality_path.exists():
        mtime = datetime.fromtimestamp(centrality_path.stat().st_mtime)
        age_h = (datetime.now() - mtime).total_seconds() / 3600
        status = "🟢" if age_h < 6 else "🟡" if age_h < 24 else "🔴"
        staleness_data.append({"Engine": "kol_centrality", "Last Modified": mtime.strftime("%Y-%m-%d %H:%M"), "Age (hours)": f"{age_h:.1f}", "Status": status})

    if staleness_data:
        st.dataframe(staleness_data, use_container_width=True, hide_index=True)

    # ── Data Delta Section ────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📈 Data Deltas")
    st.caption("*Totals are vanity. Deltas are decisions.*")
    st.info("Delta tracking requires a baseline snapshot. Run the dashboard daily to build history. For now, showing current totals vs last known.")


def _get_centrality_summary():
    summary_path = SQLITE_PATHS["kols"].parent / "pipeline_summaries" / "kol_centrality_summary.json"
    data = {}
    if summary_path.exists():
        try:
            data = json.loads(summary_path.read_text(encoding="utf-8"))
        except Exception:
            data = {}
    tiers = ((data.get("score_distribution") or {}).get("tier_counts") or {})
    return {
        "scores_written": data.get("scores_written") or (sb.count("kol_centrality_scores") if sb.is_configured else 0),
        "tier1": tiers.get("Tier 1 — Network Anchor", 0),
    }


def _render_centrality_heartbeat(name):
    summary_path = SQLITE_PATHS["kols"].parent / "pipeline_summaries" / "kol_centrality_summary.json"
    if not summary_path.exists():
        st.markdown(f"⚫ **{name}**")
        st.caption("No summary")
        return
    mtime = datetime.fromtimestamp(summary_path.stat().st_mtime)
    age_h = (datetime.now() - mtime).total_seconds() / 3600
    data = {}
    try:
        data = json.loads(summary_path.read_text(encoding="utf-8"))
    except Exception:
        pass
    status = data.get("status", "unknown")
    if status == "success" and age_h < 6:
        dot = "🟢"
    elif status == "success" and age_h < 24:
        dot = "🟡"
    elif status == "success":
        dot = "🔴"
    else:
        dot = "⚫"
    st.markdown(f"{dot} **{name}**")
    st.caption(f"{data.get('scores_written', 0):,} scores · {age_h:.1f}h ago")


def _sqlite_count(db_key, table):
    """Get count from SQLite database."""
    db_path = SQLITE_PATHS.get(db_key)
    if not db_path or not db_path.exists():
        return 0
    try:
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute(f"SELECT count(*) FROM {table}")
        count = cur.fetchone()[0]
        conn.close()
        return count
    except:
        return 0