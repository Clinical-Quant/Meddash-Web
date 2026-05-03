"""
Page 1: Circuit Board — Live Pipeline Flow (Fragment)
Refreshes every 15 seconds. Pure HTML/CSS flow diagram — no Mermaid, no iframe flicker.
"""
import streamlit as st
from pipeline_registry import (
    get_registry, get_effective_status, get_pipeline_summary,
    COMPONENT_ORDER, COMPONENT_LABELS,
)
from datetime import datetime, timezone


STATUS_COLORS = {
    "idle":    "#64748b",
    "running": "#3b82f6",
    "success": "#22c55e",
    "failed":  "#ef4444",
    "hung":    "#f59e0b",
}

STATUS_CSS_CLASS = {
    "idle":    "cq-node-idle",
    "running": "cq-node-running",
    "success": "cq-node-done",
    "failed":  "cq-node-error",
    "hung":    "cq-node-running",  # orange blink
}

# Define pipeline rows — matches architecture flow
PIPELINE_ROWS = [
    # Row 1: Trigger & Orchestration
    ["n8n_schedule", "ops_api_detect", "cq_runner", "cq_engine"],
    # Row 2: Data ingestion
    ["sec_feed_fetch", "biotech_filter"],
    # Row 3: Path A — 8-K (left) and Path B — Form 4 (right) — split row
    # Rendered as two sub-rows
    # Row 3a: Path A
    ["path_a_dedup", "path_a_fetch", "path_a_llm_extract", "path_a_validate", "path_a_write"],
    # Row 3b: Path B
    ["path_b_dedup", "path_b_parse", "path_b_filter", "path_b_write"],
    # Row 4: Verification
    ["cq_selector", "cq_verifier", "cq_composer"],
    # Row 5: Approval & Export
    ["cq_approval", "cq_export", "healthcheck_ping"],
]


CSS = """
<style>
/* Circuit Board Pipeline Styles */
.cq-circuit-container {
    padding: 20px 10px;
    background: #0e1117;
    font-family: 'Segoe UI', system-ui, sans-serif;
    overflow-x: auto;
}
.cq-row {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0;
    margin: 6px 0;
    flex-wrap: nowrap;
}
.cq-row-label {
    color: #7dd3fc;
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    text-align: center;
    padding: 4px 0;
    margin: 4px 0 0 0;
}

/* Node */
.cq-node {
    min-width: 90px;
    max-width: 115px;
    padding: 10px 8px;
    border-radius: 8px;
    text-align: center;
    font-size: 0.7rem;
    font-weight: 600;
    color: #cbd5e1;
    background: linear-gradient(180deg, rgba(30,41,59,0.92), rgba(15,23,42,0.92));
    border: 1.5px solid rgba(100,116,139,0.35);
    box-shadow: 0 3px 10px rgba(0,0,0,0.2);
    transition: all 0.3s ease;
    margin: 2px;
}
.cq-node-label {
    font-size: 0.6rem;
    color: #93a4b8;
    display: block;
    margin-top: 1px;
}

/* Node states */
.cq-node-idle {
    border-color: rgba(100,116,139,0.35);
    opacity: 0.55;
}
.cq-node-running {
    border-color: #facc15 !important;
    background: linear-gradient(180deg, rgba(120,53,15,0.80), rgba(15,23,42,0.92)) !important;
    color: #f8fafc !important;
    animation: cq-blink 1.2s ease-in-out infinite;
}
.cq-node-done {
    border-color: #22c55e !important;
    background: linear-gradient(180deg, rgba(20,83,45,0.70), rgba(15,23,42,0.92)) !important;
    color: #f8fafc !important;
    opacity: 0.9;
}
.cq-node-error {
    border-color: #ef4444 !important;
    background: linear-gradient(180deg, rgba(127,29,29,0.85), rgba(15,23,42,0.92)) !important;
    color: #f8fafc !important;
    animation: cq-blink-red 1s ease-in-out infinite;
}

@keyframes cq-blink {
    0%, 100% { opacity: 1; box-shadow: 0 0 10px 3px rgba(250,204,21,0.3); }
    50% { opacity: 0.7; box-shadow: 0 0 22px 8px rgba(250,204,21,0.55); }
}
@keyframes cq-blink-red {
    0%, 100% { opacity: 1; box-shadow: 0 0 10px 3px rgba(239,68,68,0.3); }
    50% { opacity: 0.7; box-shadow: 0 0 22px 8px rgba(239,68,68,0.55); }
}

/* Arrows between nodes */
.cq-arrow {
    display: flex;
    align-items: center;
    min-width: 36px;
    height: 2px;
    margin: 0 2px;
}
.cq-arrow-line {
    width: 100%;
    height: 2px;
}
.cq-arrow-line-idle {
    background: repeating-linear-gradient(90deg, #475569 0px, #475569 5px, transparent 5px, transparent 10px);
}
.cq-arrow-line-running {
    background: repeating-linear-gradient(90deg, #facc15 0px, #facc15 5px, transparent 5px, transparent 10px);
    animation: cq-dash-move 0.6s linear infinite;
}
.cq-arrow-line-done {
    background: repeating-linear-gradient(90deg, rgba(34,197,94,0.5) 0px, rgba(34,197,94,0.5) 4px, transparent 4px, transparent 8px);
}
@keyframes cq-dash-move {
    0% { background-position: 0 0; }
    100% { background-position: 10px 0; }
}

/* Vertical connector between rows */
.cq-vconnector {
    text-align: center;
    color: #475569;
    font-size: 0.9rem;
    line-height: 1;
    margin: 0;
}
.cq-vconnector-active { color: #facc15; animation: cq-blink 1.2s ease-in-out infinite; }
.cq-vconnector-done { color: #22c55e; }

/* Split label */
.cq-split-label {
    text-align: center;
    color: #7dd3fc;
    font-size: 0.6rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding: 6px 0;
}

/* Status pills */
.cq-pills { display: flex; gap: 8px; flex-wrap: wrap; justify-content: center; margin: 10px 0; }
.cq-pill {
    padding: 6px 14px; border-radius: 16px; font-size: 0.72rem; font-weight: 700;
    background: rgba(30,41,59,0.9); border: 1px solid rgba(100,116,139,0.3); color: #93a4b8;
    text-align: center;
}
.cq-pill-count { font-size: 1.1rem; display: block; }

/* Watchdog alert */
.cq-alert { padding: 8px 14px; margin: 6px 0; border-radius: 8px; font-size: 0.75rem; }
.cq-alert-warn { background: rgba(245,158,11,0.15); border: 1px solid #f59e0b; color: #f59e0b; }
.cq-alert-err  { background: rgba(239,68,68,0.15); border: 1px solid #ef4444; color: #ef4444; }
</style>
"""


def _build_node_html(comp_id: str, status: str, last_updated: str = "") -> str:
    label = COMPONENT_LABELS.get(comp_id, comp_id)
    css_class = STATUS_CSS_CLASS.get(status, "cq-node-idle")
    tooltips = {
        "idle": "Waiting for next trigger cycle",
        "running": "Script is actively executing right now — dashboard sees live status",
        "success": "Completed successfully on last run",
        "failed": "Crashed or returned an error — check error log",
        "hung": "WATCHDOG: status is 'running' but last update >30 min ago — script may be frozen",
    }
    tip = tooltips.get(status, "")
    time_tip = f" (last update: {last_updated[:19]})" if last_updated else ""
    return f'<div class="cq-node {css_class}" title="{tip}{time_tip}">{label}</div>'


def _build_arrow(prev_status: str) -> str:
    if prev_status == "running" or prev_status == "hung":
        arrow_class = "cq-arrow-line-running"
    elif prev_status == "success":
        arrow_class = "cq-arrow-line-done"
    else:
        arrow_class = "cq-arrow-line-idle"
    return f'<div class="cq-arrow"><div class="cq-arrow-line {arrow_class}"></div></div>'


def _build_row(nodes: list[str], registry: dict) -> str:
    """Build one horizontal row of nodes + arrows."""
    parts = []
    for i, cid in enumerate(nodes):
        if i > 0:
            prev = nodes[i - 1]
            prev_status = get_effective_status(registry.get(prev, {}))
            parts.append(_build_arrow(prev_status))
        data = registry.get(cid, {})
        status = get_effective_status(data)
        parts.append(_build_node_html(cid, status, data.get("last_updated", "")))
    return "".join(parts)


def _render_full_circuit(registry: dict):
    """Render the complete pipeline flow diagram."""
    html_parts = [CSS, '<div class="cq-circuit-container">']

    # Row labels and connectors between logical groups
    row_configs = [
        ("TRIGGER & ORCHESTRATION", PIPELINE_ROWS[0]),
        ("DATA INGESTION", PIPELINE_ROWS[1]),
        ("PATH A — 8-K CATALYST EXTRACTION", PIPELINE_ROWS[2]),
        ("PATH B — FORM 4 INSIDER TRADES", PIPELINE_ROWS[3]),
        ("VERIFICATION PIPELINE", PIPELINE_ROWS[4]),
        ("APPROVAL & EXPORT", PIPELINE_ROWS[5]),
    ]

    for i, (label, nodes) in enumerate(row_configs):
        if i > 0:
            # Determine connector state from first node in previous row
            prev_nodes = row_configs[i - 1][1]
            prev_status = get_effective_status(registry.get(prev_nodes[-1], {}))
            vclass = ""
            if prev_status in ("running", "hung"):
                vclass = "cq-vconnector-active"
            elif prev_status == "success":
                vclass = "cq-vconnector-done"
            html_parts.append(f'<div class="cq-vconnector {vclass}">▼</div>')

        html_parts.append(f'<div class="cq-row-label">{label}</div>')
        html_parts.append(f'<div class="cq-row">{_build_row(nodes, registry)}</div>')

    html_parts.append('</div>')
    return "\n".join(html_parts)


def _render_status_pills(summary: dict):
    """Compact status summary row."""
    html = '<div class="cq-pills">'
    items = [
        ("🔵 Running", "running", "#3b82f6", "Script is actively executing right now"),
        ("🟢 Success", "success", "#22c55e", "Completed successfully on last pipeline run"),
        ("🔴 Failed", "failed", "#ef4444", "Crashed or returned an error — check operations tab"),
        ("🟠 Hung", "hung", "#f59e0b", "WATCHDOG: running status but not updated in 30+ min — likely frozen"),
        ("⚫ Idle", "idle", "#64748b", "Waiting for next n8n schedule trigger"),
    ]
    for label, key, color, tip in items:
        count = summary.get(key, 0)
        html += (
            f'<div class="cq-pill" style="border-color:{color};" title="{tip}">'
            f'<span class="cq-pill-count" style="color:{color};">{count}</span>{label}</div>'
        )
    html += '</div>'
    return html


def _render_watchdog_alerts(registry: dict) -> str:
    """Return HTML for hung/failed alerts."""
    alerts = []
    for cid in COMPONENT_ORDER:
        data = registry.get(cid, {})
        status = get_effective_status(data)
        label = COMPONENT_LABELS.get(cid, cid)
        if status == "hung":
            last = data.get("last_updated", "?")[:19]
            alerts.append(f'<div class="cq-alert cq-alert-warn">⚠️ <b>{label}</b> appears HUNG — status is "running" but last updated {last}</div>')
        elif status == "failed":
            error = data.get("error_message", "unknown")[:120]
            alerts.append(f'<div class="cq-alert cq-alert-err">🚨 <b>{label}</b> FAILED — {error}</div>')
    return "\n".join(alerts)


def render():
    st.subheader("⚡ Live Pipeline Circuit Board")
    st.caption("Refreshes every 15s — pure HTML/CSS, no iframe flicker. Yellow blink = running, green = done, red = failed, orange = hung (watchdog).")

    registry = get_registry()
    summary = get_pipeline_summary()

    # Status pills
    st.markdown(_render_status_pills(summary), unsafe_allow_html=True)

    # Watchdog alerts
    alert_html = _render_watchdog_alerts(registry)
    if alert_html.strip():
        st.markdown(alert_html, unsafe_allow_html=True)

    # Pipeline flow diagram
    circuit_html = _render_full_circuit(registry)
    st.markdown(circuit_html, unsafe_allow_html=True)

    # Full status table
    with st.expander("📋 Full Component Status Table"):
        from pipeline_registry import get_status_table
        st.dataframe(get_status_table(), use_container_width=True, hide_index=True, height=400)

    st.caption(f"Last fragment render: {datetime.now(timezone.utc).strftime('%H:%M:%S')} UTC")
