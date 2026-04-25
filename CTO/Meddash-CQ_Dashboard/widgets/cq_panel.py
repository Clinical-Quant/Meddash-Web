"""
LAYER 3: CLINICAL QUANT PANEL — Market Intelligence Engine
Green department. Catalyst pipeline, newsletter, permanent agent workflow.
CEO request: 1 catalyst → 1 post via permanent agent (not py scripts).
CQ-Free Newsletter branch.
"""

import streamlit as st
from datetime import datetime, timedelta
from supabase_client import sb
from config import SQLITE_PATHS

def render():
    st.markdown('<div class="cq-header">', unsafe_allow_html=True)
    st.title("💊 Clinical Quant Panel")
    st.caption("*Market Intelligence — Catalysts, Trading Signals, Newsletter*")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── CATALYST-TO-NEWSLETTER PIPELINE ────────────────────────────────────
    st.subheader("📢 Catalyst → Newsletter Pipeline")
    st.caption("*1 catalyst = 1 post. Permanent agent does the research, writing, verification. CEO approves.*")

    pipe_cols = st.columns(6)
    stages = [
        ("🔍 Detect", "Catalyst found", "auto"),
        ("🔬 Research", "Deep analysis", "agent"),
        ("✅ Verify", "Fact check", "agent"),
        ("📝 Draft", "Write post", "agent"),
        ("👨‍⚕️ Approve", "CEO review", "manual"),
        ("📢 Publish", "CQ-Free Newsletter", "manual"),
    ]

    # Get actual catalyst counts
    cat_total = sb.count("cq_regulatory_catalysts") if sb.is_configured else 0

    for i, (stage, desc, mode) in enumerate(stages):
        with pipe_cols[i]:
            bg = "#1a2e1a" if mode in ("auto", "agent") else "#2e2a1a"
            border = "#66bb6a" if mode in ("auto", "agent") else "#ffa726"
            mode_label = "🤖 AGENT" if mode == "agent" else "⚡ AUTO" if mode == "auto" else "👤 MANUAL"
            st.markdown(
                f"<div style='text-align:center; padding:10px; border:1px solid {border}; "
                f"border-radius:8px; background:{bg}; min-height:90px; "
                f"display:flex; flex-direction:column; justify-content:center;'>"
                f"<div style='font-size:16px; font-weight:bold'>{stage}</div>"
                f"<div style='font-size:0.7em; color:#999; margin-top:4px'>{desc}</div>"
                f"<div style='font-size:0.6em; color:{border}; margin-top:6px'>{mode_label}</div>"
                f"</div>",
                unsafe_allow_html=True
            )

    # Pipeline count
    st.markdown("---")
    pipeline_cols = st.columns(3)
    with pipeline_cols[0]:
        st.metric("Catalysts Detected", cat_total, help="Total catalysts in database")
    with pipeline_cols[1]:
        st.metric("Posts Drafted", "—", help="Permanent agent not yet deployed")
    with pipeline_cols[2]:
        st.metric("Posts Published", "—", help="Newsletter automation pending")

    # ── PHASE 1: REGULATORY CATALYSTS ─────────────────────────────────────
    st.markdown("---")
    st.subheader("📋 Phase 1 — Regulatory Catalysts (LIVE)")

    if sb.is_configured and cat_total > 0:
        # Breakdown by source type
        sources = sb.select("cq_regulatory_catalysts", columns="source_type", limit=2000)
        source_counts = {}
        for s in sources:
            st_type = s.get("source_type", "unknown")
            source_counts[st_type] = source_counts.get(st_type, 0) + 1

        cat_cols = st.columns(len(source_counts) if source_counts else 1)
        for i, (src, cnt) in enumerate(sorted(source_counts.items(), key=lambda x: -x[1])):
            with cat_cols[i]:
                icon = {"SEC_8K": "📋", "FDA_PDUFA": "💊", "PR_WIRE": "📰"}.get(src, "📄")
                st.metric(f"{icon} {src}", cnt)

        # Unique tickers covered
        tickers = sb.select("cq_regulatory_catalysts", columns="ticker", limit=2000)
        unique_tickers = len(set(t.get("ticker") for t in tickers if t.get("ticker")))
        leads_total = sb.count("biotech_leads") if sb.is_configured else 0

        signal_cols = st.columns(2)
        with signal_cols[0]:
            st.metric("Unique Tickers in Catalysts", unique_tickers)
        with signal_cols[1]:
            coverage = (unique_tickers / leads_total * 100) if leads_total > 0 else 0
            st.metric("Lead Coverage", f"{coverage:.0f}%")

        # Signal-to-Noise Ratio
        st.markdown("---")
        st.subheader("📉 Signal-to-Noise Ratio")
        st.caption("*What % of detected events are actionable biotech catalysts vs noise?*")
        # This requires knowing total filings scanned vs actual catalysts stored
        # Approximate: show catalysts as % of leads
        if leads_total > 0 and cat_total > 0:
            ratio = min((cat_total / max(leads_total * 10, 1)) * 100, 100)  # rough estimate
            st.info(f"Approximate signal rate: **{ratio:.1f}%** of scanned filings become catalysts. (Needs proper tracking for accuracy.)")
        else:
            st.warning("Not enough data to calculate signal-to-noise ratio yet.")

        # Recent catalysts table
        st.markdown("---")
        st.subheader("🕐 Recent Catalysts")
        recent = sb.select("cq_regulatory_catalysts",
                           columns="ticker,company_name,event_type,source_type,created_at",
                           limit=20)
        if recent:
            # Format for display
            display_rows = []
            for r in recent:
                display_rows.append({
                    "Ticker": r.get("ticker", "—"),
                    "Company": r.get("company_name", "—"),
                    "Event": r.get("event_type", "—"),
                    "Source": r.get("source_type", "—"),
                    "Detected": r.get("created_at", "—")[:16] if r.get("created_at") else "—",
                })
            st.dataframe(display_rows, use_container_width=True, hide_index=True)
        else:
            st.info("No recent catalysts found.")
    else:
        st.warning("⚠️ No catalysts found in Supabase. Check your CQ pipeline scripts are running.")
        if not sb.is_configured:
            st.error("Supabase not configured. Check .env files.")

    # ── PHASES 2-4 (locked) ───────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🔒 Future Phases")
    st.caption("*Gamification: unlock phases as Phase 1 grows.*")

    unlock_threshold = 100  # catalysts needed to unlock Phase 2
    phase_cols = st.columns(3)
    phases = [
        ("Phase 2", "Congress Abstracts", "📈", unlock_threshold),
        ("Phase 3", "Sentiment Analysis", "💭", 300),
        ("Phase 4", "Quant Analytics", "🧮", 500),
    ]

    for i, (phase, desc, icon, threshold) in enumerate(phases):
        with phase_cols[i]:
            locked = cat_total < threshold
            if locked:
                remaining = threshold - cat_total
                st.markdown(
                    f"<div style='padding:16px; border:1px solid #333; border-radius:8px; "
                    f"background:#1a1d23; opacity:0.5; text-align:center;'>"
                    f"<div style='font-size:24px'>{icon} 🔒</div>"
                    f"<div style='font-size:14px; color:#666; margin-top:8px'>{phase}</div>"
                    f"<div style='font-size:0.8em; color:#555; margin-top:4px'>{desc}</div>"
                    f"<div style='font-size:0.75em; color:#ffa726; margin-top:8px'>"
                    f"Unlock at {threshold} catalysts ({remaining} more needed)</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"<div style='padding:16px; border:2px solid #66bb6a; border-radius:8px; "
                    f"background:#1a2e1a; text-align:center;'>"
                    f"<div style='font-size:24px'>{icon} ✅</div>"
                    f"<div style='font-size:14px; color:#66bb6a; margin-top:8px'>{phase}</div>"
                    f"<div style='font-size:0.8em; color:#999; margin-top:4px'>{desc}</div>"
                    f"<div style='font-size:0.75em; color:#66bb6a; margin-top:8px'>UNLOCKED!</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )

    # ── PERMANENT AGENT SECTION ───────────────────────────────────────────
    st.markdown("---")
    st.subheader("🤖 Permanent Agent: CQ Content Factory")
    st.caption("*CEO directive: Not Python scripts. A permanent agent that researches, writes, and drafts — CEO approves.*")

    agent_cols = st.columns(2)
    with agent_cols[0]:
        st.markdown("""
        **Agent Workflow:**
        1. New catalyst detected → agent triggered
        2. Agent deep-researches the catalyst (company, context, market impact)
        3. Agent verifies facts against primary sources
        4. Agent drafts newsletter post
        5. Draft queued for CEO approval
        6. CEO approves → published to CQ-Free Newsletter
        """)
    with agent_cols[1]:
        st.markdown("""
        **Status: NOT DEPLOYED**
        
        To deploy:
        - Set up Hermes cron job to poll new catalysts
        - Spawn agent on each new catalyst event
        - Agent output saved to draft queue
        - CEO reviews via dashboard or Obsidian
        - Approved posts pushed to Substack API
        
        *Blocking: Need Substack API key + publication URL*
        """)

    # ── NEWSLETTER SUBSCRIBERS ────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📬 Newsletter Metrics")
    st.info("Subscriber counts require Substack API integration. Provide publication URL to enable.")