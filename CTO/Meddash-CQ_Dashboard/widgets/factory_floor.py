"""
LAYER 5: THE BRIDGE — Factory Floor
Modern executive overview of the MEDDASH-CQ production line.

Purpose:
- Explain what the factory is producing.
- Show whether engines are fresh, stale, missing, or idle.
- Connect raw data inventory → engine flow → commercial products.
"""

from datetime import datetime, timedelta, timezone
import html
import json
import sqlite3

import streamlit as st

from supabase_client import sb
from config import SQLITE_PATHS, PRODUCT_PATHS


STATUS_META = {
    "green": {
        "dot": "●",
        "label": "Fresh / active",
        "class": "status-green",
        "explain": "Recent successful activity. For SQLite engines this means the database changed within 6 hours; for CQ this means recent catalysts exist.",
    },
    "yellow": {
        "dot": "●",
        "label": "Stale / needs attention",
        "class": "status-yellow",
        "explain": "Some activity exists, but it is not fresh. For SQLite engines this means last update is 6–24 hours old.",
    },
    "red": {
        "dot": "●",
        "label": "Missing / broken",
        "class": "status-red",
        "explain": "Expected source was not found or a check failed. This needs investigation.",
    },
    "grey": {
        "dot": "●",
        "label": "Idle / not instrumented",
        "class": "status-grey",
        "explain": "No direct health signal yet, or the component is intentionally idle. Grey does not always mean broken.",
    },
}


ENGINE_DESCRIPTIONS = {
    "kol_engine": "Builds the key-opinion-leader database used to create KOL intelligence briefs.",
    "ct_engine": "Collects clinical trial records that support therapeutic-area context and trial landscape views.",
    "biocrawler": "Finds biotech companies and lead targets that can become prospects or CQ-tracked tickers.",
    "bridge": "Connects Meddash company/ticker data into Clinical Quant monitoring. No separate DB yet, so shown grey until instrumented.",
    "scholar": "Adds publication/scholar metrics to KOL profiles. Uses the KOL database, so it needs a dedicated health signal later.",
    "kol_centrality": "Calculates authorship-network centrality for every KOL and writes transparent score/reliability rows back to Supabase.",
    "sec_8k": "Watches SEC 8-K events for biotech catalyst signals.",
    "fda_pdufa": "Tracks FDA/PDUFA dates that can become Clinical Quant newsletter catalysts.",
    "pr_wire": "Aggregates biotech press releases for catalyst detection.",
    "ticker_enrich": "Adds stock tickers to biotech leads so companies can flow into CQ monitoring.",
    "cq_agent": "Paperclip/n8n agent layer that turns detected catalysts into researched newsletter workflow items.",
}


PRODUCT_DESCRIPTIONS = {
    "KOL Briefs": "Client-ready deliverable: a concise medical-affairs intelligence brief around a named expert, disease area, or company need.",
    "TA Landscapes": "Therapeutic-area map: trials, experts, companies, and context assembled into a reusable landscape asset.",
    "CQ Posts": "Clinical Quant newsletter/social posts generated from verified catalyst events.",
}


def render():
    st.markdown(
        """
        <div class="factory-hero">
          <div class="factory-eyebrow">Layer 5 · Executive factory floor</div>
          <h1>🏭 MEDDASH-CQ Factory Floor</h1>
          <p>
            This page explains the business machine: raw medical/biotech data enters on the left,
            engines process it in the middle, and sellable outputs leave on the right.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _render_status_legend()
    _render_factory_output()
    _render_production_line()
    _render_data_inventory()
    _render_bridge_spine()


def _render_status_legend():
    st.markdown("### How to read this page")
    st.caption("Every colored dot is a health signal. Hover a dot/card where your browser supports tooltips.")

    cols = st.columns(4)
    for col, status in zip(cols, ["green", "yellow", "red", "grey"]):
        meta = STATUS_META[status]
        with col:
            st.markdown(
                f"""
                <div class="legend-card" title="{html.escape(meta['explain'])}">
                  <span class="factory-dot {meta['class']}">{meta['dot']}</span>
                  <strong>{meta['label']}</strong>
                  <div>{meta['explain']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_factory_output():
    st.markdown("---")
    st.markdown("### Factory output this week")
    st.caption(
        "This is the production scoreboard. It counts files created in product folders during the last 7 days. "
        "If output is zero, the factory may be running but not producing client-ready assets."
    )

    briefs_this_week = _count_recent_files(PRODUCT_PATHS.get("kol_briefs"))
    ta_this_week = _count_recent_files(PRODUCT_PATHS.get("ta_landscapes"))
    cq_posts_this_week = 0  # newsletter publishing is still manual/not wired to a product folder

    cols = st.columns(3)
    with cols[0]:
        _metric_card(
            title="KOL Briefs",
            value=str(briefs_this_week),
            state="producing" if briefs_this_week else "idle",
            description=PRODUCT_DESCRIPTIONS["KOL Briefs"],
            footer="Counted from the KOL brief output folder.",
        )
    with cols[1]:
        _metric_card(
            title="TA Landscapes",
            value=str(ta_this_week),
            state="producing" if ta_this_week else "idle",
            description=PRODUCT_DESCRIPTIONS["TA Landscapes"],
            footer="Counted from the TA landscape output folder.",
        )
    with cols[2]:
        _metric_card(
            title="CQ Posts",
            value=str(cq_posts_this_week),
            state="idle",
            description=PRODUCT_DESCRIPTIONS["CQ Posts"],
            footer="Manual publishing is not counted automatically yet.",
        )

    st.info(
        "Revenue and pipeline value are intentionally hidden until a CRM is connected. "
        "For now this page only shows production output — not sales, bookings, or client revenue.",
        icon="ℹ️",
    )


def _render_production_line():
    st.markdown("---")
    st.markdown("### Production line")
    st.caption(
        "A readable map of what each engine does. Meddash builds intelligence assets; Clinical Quant turns market catalysts into publishable content."
    )

    engine_status = _get_engine_status()

    st.markdown(
        """
        <div class="department-header meddash-modern">
          <div>
            <h3>🔬 MEDDASH Department</h3>
            <p>Builds medical-affairs intelligence assets: KOL data, trial context, biotech lead lists, and client-facing briefs.</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    engines_meddash = [
        ("KOL Engine", "kol_engine", "Database → KOL profiles"),
        ("CT Engine", "ct_engine", "Trials → context"),
        ("BioCrawler GTM", "biocrawler", "Companies → leads"),
        ("Bridge Engine", "bridge", "Tickers → CQ handoff"),
        ("Scholar Scraper", "scholar", "Publications → credibility"),
        ("KOL Centrality", "kol_centrality", "Authorship graph → scores"),
    ]
    _render_engine_row(engines_meddash, engine_status, accent="#42a5f5")

    st.markdown("<div class='flow-down'>↓ Output layer</div>", unsafe_allow_html=True)
    p_cols = st.columns(2)
    with p_cols[0]:
        _product_card(
            "📄 KOL Briefs",
            "Client-ready intelligence brief",
            PRODUCT_DESCRIPTIONS["KOL Briefs"],
            "Not a button — this is a product output type leaving the factory.",
            "#42a5f5",
        )
    with p_cols[1]:
        _product_card(
            "📊 TA Landscapes",
            "Reusable intelligence asset",
            PRODUCT_DESCRIPTIONS["TA Landscapes"],
            "Supports sales, briefs, and expert mapping.",
            "#42a5f5",
        )

    st.markdown(
        """
        <div class="department-header cq-modern">
          <div>
            <h3>💊 CLINICAL QUANT Department</h3>
            <p>Monitors public biotech catalysts and converts verified signals into newsletter/social publishing workflow.</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    engines_cq = [
        ("SEC 8-K Monitor", "sec_8k", "Filings → catalysts"),
        ("FDA PDUFA Tracker", "fda_pdufa", "FDA dates → catalysts"),
        ("PR Wire Aggregator", "pr_wire", "Press releases → signals"),
        ("Ticker Enrichment", "ticker_enrich", "Companies → tickers"),
        ("Agent Layer", "cq_agent", "Research → draft workflow"),
    ]
    _render_engine_row(engines_cq, engine_status, accent="#66bb6a")

    st.markdown("<div class='flow-down'>↓ Content workflow</div>", unsafe_allow_html=True)
    _render_agent_pipeline()


def _render_engine_row(engines, engine_status, accent):
    cols = st.columns(len(engines))
    for col, (name, key, output) in zip(cols, engines):
        status = engine_status.get(key, "grey")
        meta = STATUS_META[status]
        description = ENGINE_DESCRIPTIONS.get(key, "No description yet.")
        with col:
            st.markdown(
                f"""
                <div class="engine-card" style="--accent:{accent};" title="{html.escape(description)}">
                  <div class="engine-status-line">
                    <span class="factory-dot {meta['class']}">●</span>
                    <span>{meta['label']}</span>
                  </div>
                  <h4>{html.escape(name)}</h4>
                  <div class="engine-output">{html.escape(output)}</div>
                  <p>{html.escape(description)}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_agent_pipeline():
    stages = [
        ("🔍 Detect", "Catalyst found", "AUTO", "A script or monitor finds a market-moving event."),
        ("🔬 Research", "Deep analysis", "AUTO", "Agent gathers context and checks why the catalyst matters."),
        ("✅ Verify", "Fact check", "AUTO", "Agent confirms source quality and removes false positives."),
        ("📝 Draft", "Write post", "AUTO", "Agent prepares a newsletter/social draft."),
        ("👨‍⚕️ Approve", "CEO review", "MANUAL", "Dr. Don reviews before public publishing."),
        ("📢 Publish", "Substack/LinkedIn", "MANUAL", "Final publishing remains manual unless later automated."),
    ]
    cols = st.columns(len(stages))
    for col, (stage, desc, mode, tooltip) in zip(cols, stages):
        auto = mode == "AUTO"
        with col:
            st.markdown(
                f"""
                <div class="stage-card {'stage-auto' if auto else 'stage-manual'}" title="{html.escape(tooltip)}">
                  <div class="stage-title">{html.escape(stage)}</div>
                  <div class="stage-desc">{html.escape(desc)}</div>
                  <div class="stage-badge">{mode}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_data_inventory():
    st.markdown("---")
    st.markdown("### Data inventory")
    st.caption(
        "This is the warehouse. It shows whether the local SQLite stores and Supabase tables contain usable stock for the engines."
    )

    inventory = _sqlite_inventory()
    sb_tables = [
        "kols",
        "kols_staging",
        "kol_merge_candidates",
        "kol_scholar_metrics",
        "kol_centrality_runs",
        "kol_centrality_scores",
        "biotech_leads",
        "trials",
        "cq_regulatory_catalysts",
    ]
    sb_counts = sb.get_table_row_counts(sb_tables) if sb.is_configured else {}

    inv_cols = st.columns(4)
    for i, (db_name, tables) in enumerate(inventory.items()):
        with inv_cols[i % 4]:
            total = sum(cnt for cnt in tables.values() if isinstance(cnt, int) and cnt > 0)
            _inventory_card(f"🗄️ {db_name}.db", total, tables, "Local SQLite store")

    with inv_cols[3]:
        if sb_counts:
            total = sum(cnt for cnt in sb_counts.values() if isinstance(cnt, int) and cnt > 0)
            _inventory_card("☁️ Supabase", total, sb_counts, "Cloud/Postgres warehouse")
        else:
            _inventory_card("☁️ Supabase", 0, {"Not configured or unavailable": 0}, "Cloud/Postgres warehouse")


def _render_bridge_spine():
    st.markdown("---")
    st.markdown("### Bridge spine: Meddash → Clinical Quant")
    st.caption(
        "The bridge is the shared data spine. Biotech leads with tickers can flow from Meddash prospecting into CQ catalyst monitoring."
    )

    leads_total = 0
    leads_with_tickers = 0
    if sb.is_configured:
        leads_total = sb.count("biotech_leads")
        leads_with_tickers = sb.count_with_filter("biotech_leads", "ticker", "not.is", None)

    bridging = leads_with_tickers if leads_with_tickers > 0 else 0
    missing = leads_total - bridging if leads_total > 0 else 0
    pct = (bridging / leads_total * 100) if leads_total > 0 else 0

    cols = st.columns(3)
    cols[0].metric("Leads with tickers", f"{bridging:,}", help="These can flow into CQ catalyst monitoring.")
    cols[1].metric("Leads missing tickers", f"{missing:,}", help="These are stuck before the bridge because CQ needs tickers.")
    cols[2].metric("Bridge completion", f"{pct:.0f}%", help="Share of biotech leads that have tickers.")

    st.progress(pct / 100 if pct else 0, text=f"Bridge status: {bridging:,}/{leads_total:,} leads have tickers → available for CQ")

    st.markdown(
        """
        <div class="explain-box">
          <strong>Why this matters:</strong> Meddash and CQ are not separate toys. Meddash builds the company/KOL/trial intelligence base;
          CQ uses ticker-connected companies to monitor catalysts and create public market-facing content.
        </div>
        """,
        unsafe_allow_html=True,
    )


def _metric_card(title, value, state, description, footer):
    state_label = "PRODUCING" if state == "producing" else "IDLE / ZERO OUTPUT"
    state_class = "metric-producing" if state == "producing" else "metric-idle"
    st.markdown(
        f"""
        <div class="modern-metric {state_class}" title="{html.escape(description)}">
          <div class="metric-kicker">{state_label}</div>
          <h4>{html.escape(title)}</h4>
          <div class="metric-value">{html.escape(value)}</div>
          <p>{html.escape(description)}</p>
          <div class="metric-footer">{html.escape(footer)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _product_card(title, subtitle, description, footer, accent):
    st.markdown(
        f"""
        <div class="product-card" style="--accent:{accent};" title="{html.escape(description)}">
          <div class="product-title">{html.escape(title)}</div>
          <div class="product-subtitle">{html.escape(subtitle)}</div>
          <p>{html.escape(description)}</p>
          <div class="product-footer">{html.escape(footer)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _inventory_card(title, total, rows, subtitle):
    row_html = []
    for table, cnt in rows.items():
        status = "green" if isinstance(cnt, int) and cnt > 0 else "yellow" if cnt == 0 else "red"
        cnt_display = f"{cnt:,}" if isinstance(cnt, int) else str(cnt)
        row_html.append(
            f"<div class='inventory-row'><span><span class='factory-dot {STATUS_META[status]['class']}'>●</span>{html.escape(str(table))}</span><strong>{html.escape(cnt_display)}</strong></div>"
        )
    st.markdown(
        f"""
        <div class="inventory-card">
          <div class="inventory-subtitle">{html.escape(subtitle)}</div>
          <h4>{html.escape(title)}</h4>
          <div class="inventory-total">{total:,}</div>
          {''.join(row_html)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _count_recent_files(path):
    if not path or not path.exists():
        return 0
    week_ago = datetime.now() - timedelta(days=7)
    count = 0
    for f in path.iterdir():
        if f.is_file() and f.stat().st_mtime > week_ago.timestamp():
            count += 1
    return count


def _sqlite_inventory():
    inventory = {}
    for db_name, db_path in SQLITE_PATHS.items():
        if db_path.exists():
            try:
                conn = sqlite3.connect(str(db_path))
                cur = conn.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [r[0] for r in cur.fetchall()]
                counts = {}
                for table in tables:
                    try:
                        cur.execute(f"SELECT count(*) FROM [{table}]")
                        counts[table] = cur.fetchone()[0]
                    except Exception:
                        counts[table] = -1
                inventory[db_name] = counts
                conn.close()
            except Exception:
                inventory[db_name] = {"ERROR": -1}
        else:
            inventory[db_name] = {"NOT FOUND": 0}
    return inventory


def _get_engine_status():
    """Check engine health: green=recent activity, yellow=stale, red=missing/error, grey=unknown or not instrumented."""
    status = {}
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

    engine_map = {
        "kol_engine": status.get("kols", "grey"),
        "ct_engine": status.get("trials", "grey"),
        "biocrawler": status.get("biocrawler", "grey"),
        "bridge": "grey",
        "scholar": "grey",
        "kol_centrality": _centrality_status(),
        "sec_8k": "grey",
        "fda_pdufa": "grey",
        "pr_wire": "grey",
        "ticker_enrich": "grey",
        "cq_agent": "grey",
    }

    if sb.is_configured:
        catalysts = sb.select("cq_regulatory_catalysts", columns="created_at", limit=1)
        if catalysts:
            try:
                latest = catalysts[0].get("created_at", "")
                if latest:
                    latest_dt = datetime.fromisoformat(latest.replace("Z", "+00:00"))
                    age_h = (datetime.now(timezone.utc) - latest_dt).total_seconds() / 3600
                    if age_h < 48:
                        engine_map["sec_8k"] = "green"
                        engine_map["fda_pdufa"] = "green"
                        engine_map["pr_wire"] = "green"
            except Exception:
                pass

        ticker_count = sb.count_with_filter("biotech_leads", "ticker", "not.is", None)
        if ticker_count > 0:
            engine_map["ticker_enrich"] = "green"
            engine_map["bridge"] = "green"

    return engine_map


def _centrality_status():
    """Health for Engine 10: KOL Centrality. Uses summary freshness first, Supabase rows second."""
    summary_path = SQLITE_PATHS["kols"].parent / "pipeline_summaries" / "kol_centrality_summary.json"
    if summary_path.exists():
        try:
            data = json.loads(summary_path.read_text(encoding="utf-8"))
            status = data.get("status")
            latest = data.get("timestamp")
            if status in ("failure", "error"):
                return "red"
            if latest:
                latest_dt = datetime.fromisoformat(latest.replace("Z", "+00:00"))
                age_h = (datetime.now(timezone.utc) - latest_dt).total_seconds() / 3600
                if age_h < 24:
                    return "green"
                if age_h < 72:
                    return "yellow"
                return "grey"
            if data.get("scores_written", 0) > 0:
                return "yellow"
        except Exception:
            return "yellow"

    if sb.is_configured and sb.count("kol_centrality_scores") > 0:
        return "yellow"
    return "grey"
