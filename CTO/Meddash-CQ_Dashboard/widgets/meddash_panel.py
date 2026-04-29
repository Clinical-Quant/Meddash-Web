"""
LAYER 2: MEDDASH PANEL — Medical Affairs Engine
Blue department. KOL funnel, CT engine, BioCrawler, Products, Scholar.
"""

import streamlit as st
from datetime import datetime, timedelta
import json
import os
import sqlite3
from supabase_client import sb
from config import SQLITE_PATHS, PRODUCT_PATHS

def render():
    st.markdown('<div class="meddash-header">', unsafe_allow_html=True)
    st.title("🔬 Meddash Panel")
    st.caption("*Medical Affairs Intelligence — KOLs, Clinical Trials, BioCrawler, Products*")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── KOL PIPELINE FUNNEL ────────────────────────────────────────────────
    st.subheader("👥 KOL Pipeline Funnel")
    st.caption("*Where do KOLs drop off? Every verified KOL is a potential brief.*")

    # Get counts at each stage
    funnel_data = _get_kol_funnel()

    # Render as visual funnel using streamlit
    funnel_cols = st.columns(4)
    stages = [
        ("Discovered", funnel_data.get("discovered", 0), "#42a5f5"),
        ("Disambiguated", funnel_data.get("disambiguated", 0), "#29b6f6"),
        ("Verified", funnel_data.get("verified", 0), "#26c6da"),
        ("Briefed", funnel_data.get("briefed", 0), "#00e676"),
    ]
    max_count = max(s[1] for s in stages) if stages else 1

    for i, (stage, count, color) in enumerate(stages):
        with funnel_cols[i]:
            pct = (count / max_count * 100) if max_count > 0 else 0
            width = max(pct, 15)  # min width for visibility
            st.markdown(
                f"<div style='text-align:center; padding:12px; "
                f"border:2px solid {color}; border-radius:8px; background:#1a1d23; "
                f"min-height:80px; display:flex; flex-direction:column; justify-content:center;'>"
                f"<div style='font-size:24px; font-weight:bold; color:{color}'>{count:,}</div>"
                f"<div style='font-size:0.8em; color:#999; margin-top:4px'>{stage}</div>"
                f"</div>",
                unsafe_allow_html=True
            )
            if i < 3:
                # Down arrow
                st.markdown("→", unsafe_allow_html=True)

    # Funnel detail table
    if any(s[1] > 0 for s in stages):
        st.markdown("---")
        dropoff = {}
        for i in range(1, len(stages)):
            prev = stages[i-1][1]
            curr = stages[i][1]
            if prev > 0:
                drop_rate = ((prev - curr) / prev) * 100
                dropoff[stages[i][0]] = f"{drop_rate:.0f}% drop-off"
            else:
                dropoff[stages[i][0]] = "N/A"

        d_cols = st.columns(3)
        names = list(dropoff.keys())
        for i, name in enumerate(names):
            with d_cols[i]:
                st.metric(name, dropoff[name])

    # ── KOL ENGINE DETAIL ─────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("⚙️ KOL Engine Detail")

    ke_cols = st.columns(3)
    with ke_cols[0]:
        review_queue = funnel_data.get("merge_pending", 0)
        st.metric("Merge Review Queue", review_queue)
    with ke_cols[1]:
        deep_review = funnel_data.get("deep_disambiguation", 0)
        st.metric("Deep Disambiguation Needed", deep_review)
    with ke_cols[2]:
        scholar_count = _sqlite_count("kols", "kol_scholar_metrics") or (sb.count("kol_scholar_metrics") if sb.is_configured else 0)
        st.metric("KOLs with Scholar Metrics", scholar_count)

    # ── KOL CENTRALITY ENGINE ──────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🧠 KOL Centrality Engine")
    st.caption(
        "Authorship-network influence score for every KOL. This is mapped centrality, not absolute real-world authority; reliability must be read with the score."
    )

    centrality = _get_centrality_summary()
    c_cols = st.columns(4)
    with c_cols[0]:
        st.metric("Centrality Scores", f"{centrality.get('scores_written', 0):,}", help="Rows populated in kol_centrality_scores for the latest run.")
    with c_cols[1]:
        st.metric("Graph Edges", f"{centrality.get('edge_count', 0):,}", help="Weighted coauthorship edges in the latest authorship graph.")
    with c_cols[2]:
        st.metric("Mapping Rate", f"{centrality.get('mapping_rate', 0):.1%}", help="Share of KOLs with mapped coauthors in the latest run.")
    with c_cols[3]:
        st.metric("Tier 1 Anchors", f"{centrality.get('tier1', 0):,}", help="KOLs currently classified as Tier 1 — Network Anchor within the mapped authorship graph.")

    st.info(
        f"Latest run: {centrality.get('run_id', 'not available')} · Method: {centrality.get('method_version', 'authorship_centrality_v1.0')} · Reliability is stored per KOL in Supabase.",
        icon="🧠",
    )

    # ── CT ENGINE ──────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🧪 Clinical Trials Engine")

    ct_cols = st.columns(3)
    total_ct = _sqlite_count("trials", "ct_trials") or (sb.count("trials") if sb.is_configured else 0)

    with ct_cols[0]:
        st.metric("Total Trials", f"{total_ct:,}")

    # Trials by phase from SQLite
    with ct_cols[1]:
        phase_data = _sqlite_query("trials", "SELECT phase, count(*) as cnt FROM ct_trials GROUP BY phase")
        if phase_data:
            for row in phase_data:
                phase = row[0] or "Unknown"
                st.markdown(f"**Phase {phase}**: {row[1]:,}")
        else:
            st.caption("No phase data in SQLite")

    with ct_cols[2]:
        db_path = SQLITE_PATHS.get("trials")
        if db_path and db_path.exists():
            mtime = datetime.fromtimestamp(db_path.stat().st_mtime)
            st.metric("Last Crawl", mtime.strftime("%Y-%m-%d %H:%M"))

    # ── BIOCRAWLER ────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🎯 BioCrawler (GTM Engine)")

    bio_cols = st.columns(3)
    leads_total = sb.count("biotech_leads") if sb.is_configured else _sqlite_count("biocrawler", "biotech_leads")
    tier_a = 0
    tier_b = 0
    tier_c = 0
    tickers_filled = 0

    if sb.is_configured and leads_total > 0:
        leads = sb.select("biotech_leads", columns="tier,ticker", limit=1000)
        for l in leads:
            t = l.get("tier", "unclassified")
            if t == "A": tier_a += 1
            elif t == "B": tier_b += 1
            elif t == "C": tier_c += 1
            if l.get("ticker"): tickers_filled += 1

    with bio_cols[0]:
        st.metric("Total Leads", f"{leads_total:,}")
    with bio_cols[1]:
        st.metric("Tier A / B / C", f"{tier_a} / {tier_b} / {tier_c}")
    with bio_cols[2]:
        missing = leads_total - tickers_filled
        st.metric("Tickers Filled / Missing", f"{tickers_filled} / {missing}")

    # ── PRODUCT VELOCITY ───────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📊 Product Velocity")
    st.caption("*Briefs per week. If velocity = 0, the factory is not producing reviewable output.*")

    vel_cols = st.columns(3)
    brief_path = PRODUCT_PATHS.get("kol_briefs")
    ta_path = PRODUCT_PATHS.get("ta_landscapes")

    # Count files in last 7 days
    briefs_week = _count_recent_files(brief_path, 7)
    briefs_month = _count_recent_files(brief_path, 30)
    ta_week = _count_recent_files(ta_path, 7)
    ta_month = _count_recent_files(ta_path, 30)

    with vel_cols[0]:
        delta_b = f"+{briefs_week} this week"
        st.metric("KOL Briefs (month)", briefs_month, delta=delta_b)
    with vel_cols[1]:
        delta_t = f"+{ta_week} this week"
        st.metric("TA Landscapes (month)", ta_month, delta=delta_t)
    with vel_cols[2]:
        total_prod = briefs_month + ta_month
        producing = total_prod > 0
        st.metric("Factory Producing?", "YES ✅" if producing else "NO ❌",
                   delta=f"{total_prod} products this month")


def _get_kol_funnel():
    """Get KOL funnel counts from SQLite + Supabase."""
    data = {}
    # Try SQLite first
    kols_db = SQLITE_PATHS.get("kols")
    if kols_db and kols_db.exists():
        try:
            conn = sqlite3.connect(str(kols_db))
            cur = conn.cursor()

            # Total discovered
            cur.execute("SELECT count(*) FROM kols")
            data["discovered"] = cur.fetchone()[0]

            # Verified
            cur.execute("SELECT count(*) FROM kols WHERE verification_status='verified'")
            data["verified"] = cur.fetchone()[0]

            # Disambiguated (staging processed)
            cur.execute("SELECT count(*) FROM kols_staging")
            data["disambiguated"] = cur.fetchone()[0]

            # Merge candidates pending
            cur.execute("SELECT count(*) FROM kol_merge_candidates WHERE merge_status='pending'")
            data["merge_pending"] = cur.fetchone()[0]

            conn.close()
        except:
            pass

    # Briefs count = product output
    brief_path = PRODUCT_PATHS.get("kol_briefs")
    if brief_path and brief_path.exists():
        data["briefed"] = sum(1 for f in brief_path.iterdir() if f.is_file())
    else:
        data["briefed"] = 0

    return data


def _get_centrality_summary():
    """Read latest centrality engine summary and provide dashboard-safe defaults."""
    summary_path = SQLITE_PATHS["kols"].parent / "pipeline_summaries" / "kol_centrality_summary.json"
    data = {}
    if summary_path.exists():
        try:
            data = json.loads(summary_path.read_text(encoding="utf-8"))
        except Exception:
            data = {}

    score_dist = data.get("score_distribution", {}) or {}
    tier_counts = score_dist.get("tier_counts", {}) or {}
    graph_stats = data.get("graph_stats", {}) or {}
    join_quality = data.get("join_quality", {}) or {}

    scores_written = data.get("scores_written")
    if scores_written is None and sb.is_configured:
        scores_written = sb.count("kol_centrality_scores")
    if scores_written is None:
        scores_written = 0

    return {
        "scores_written": scores_written if isinstance(scores_written, int) else 0,
        "edge_count": graph_stats.get("edge_count", 0) or 0,
        "mapping_rate": join_quality.get("coauthor_mapping_rate", 0) or 0,
        "tier1": tier_counts.get("Tier 1 — Network Anchor", 0) or 0,
        "run_id": data.get("run_id", "not available"),
        "method_version": data.get("method_version", "authorship_centrality_v1.0"),
    }



def _sqlite_count(db_key, table):
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


def _sqlite_query(db_key, sql):
    db_path = SQLITE_PATHS.get(db_key)
    if not db_path or not db_path.exists():
        return []
    try:
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        conn.close()
        return rows
    except:
        return []


def _count_recent_files(path, days):
    if not path or not path.exists():
        return 0
    cutoff = datetime.now() - timedelta(days=days)
    return sum(1 for f in path.iterdir() if f.is_file() and datetime.fromtimestamp(f.stat().st_mtime) > cutoff)