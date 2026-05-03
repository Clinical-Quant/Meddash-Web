"""
Pipeline Registry — SQLite read/write helpers for deterministic dashboard status.
Reads from cq_pipeline_registry.db with watchdog logic for hung processes.
"""
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path

DB_PATH = Path("/mnt/c/Users/email/.gemini/antigravity/Meddash_organized_backend/06_Shared_Datastores/cq_pipeline_registry.db")

STATUS_COLORS = {
    "idle":    "#64748b",  # grey
    "running": "#3b82f6",  # blue
    "success": "#22c55e",  # green
    "failed":  "#ef4444",  # red
    "hung":    "#f59e0b",  # orange
}

COMPONENT_ORDER = [
    "n8n_schedule", "ops_api_detect", "cq_runner", "cq_engine",
    "sec_feed_fetch", "biotech_filter",
    "path_a_dedup", "path_a_fetch", "path_a_llm_extract", "path_a_validate", "path_a_write",
    "path_b_dedup", "path_b_parse", "path_b_filter", "path_b_write",
    "cq_selector", "cq_verifier", "cq_composer",
    "cq_approval", "cq_export", "healthcheck_ping",
]

COMPONENT_LABELS = {
    "n8n_schedule": "n8n Schedule",
    "ops_api_detect": "Ops API /detect",
    "cq_runner": "CQ Runner",
    "cq_engine": "CQ Engine",
    "sec_feed_fetch": "SEC Feed",
    "biotech_filter": "CIK Filter",
    "path_a_dedup": "8-K Dedup",
    "path_a_fetch": "8-K Fetch",
    "path_a_llm_extract": "LLM Extract",
    "path_a_validate": "Validate",
    "path_a_write": "cq_catalysts",
    "path_b_dedup": "F4 Dedup",
    "path_b_parse": "Parse XML",
    "path_b_filter": "Filter P",
    "path_b_write": "cq_trades",
    "cq_selector": "Selector",
    "cq_verifier": "Verifier",
    "cq_composer": "Composer",
    "cq_approval": "Dr. Don",
    "cq_export": "Export",
    "healthcheck_ping": "HC Ping",
}


def get_registry() -> dict:
    """Read all registry entries. Returns {component_id: {status, last_updated, ...}}."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM pipeline_registry").fetchall()
        conn.close()
        return {r["component_id"]: dict(r) for r in rows}
    except Exception:
        return {}


def get_effective_status(data: dict) -> str:
    """Apply watchdog: if 'running' but last_updated > 30min, override to 'hung'."""
    if not data:
        return "idle"
    status = data.get("status", "idle")
    if status == "running":
        try:
            last = datetime.fromisoformat(data["last_updated"])
            if datetime.now(timezone.utc) - last > timedelta(minutes=30):
                return "hung"
        except (ValueError, KeyError):
            pass
    return status


def get_status_table() -> list:
    """Return flat list for Streamlit table display."""
    registry = get_registry()
    rows = []
    for cid in COMPONENT_ORDER:
        data = registry.get(cid, {})
        eff = get_effective_status(data)
        rows.append({
            "Component": COMPONENT_LABELS.get(cid, cid),
            "Status": eff.upper(),
            "Last Updated": data.get("last_updated", "")[:19],
            "Error": data.get("error_message", "")[:80],
        })
    return rows


def generate_circuit_mermaid() -> str:
    """Build a Mermaid 'graph LR' diagram with live status colors from the registry."""
    registry = get_registry()
    diagram = "graph LR\n"
    diagram += "    classDef idle fill:#64748b,stroke:#333,stroke-width:2px,color:#cbd5e1\n"
    diagram += "    classDef running fill:#3b82f6,stroke:#333,stroke-width:2px,color:#fff\n"
    diagram += "    classDef success fill:#22c55e,stroke:#333,stroke-width:2px,color:#fff\n"
    diagram += "    classDef failed fill:#ef4444,stroke:#333,stroke-width:2px,color:#fff\n"
    diagram += "    classDef hung fill:#f59e0b,stroke:#333,stroke-width:2px,color:#000\n"

    for cid in COMPONENT_ORDER:
        data = registry.get(cid, {})
        status = get_effective_status(data)
        label = COMPONENT_LABELS.get(cid, cid)
        diagram += f"    {cid}['{label}']\n"
        diagram += f"    class {cid} {status}\n"

    # Edges — full architecture flow
    edges = [
        ("n8n_schedule", "ops_api_detect"),
        ("ops_api_detect", "cq_runner"),
        ("cq_runner", "cq_engine"),
        ("cq_engine", "sec_feed_fetch"),
        ("sec_feed_fetch", "biotech_filter"),
        ("biotech_filter", "path_a_dedup"),
        ("biotech_filter", "path_b_dedup"),
        ("path_a_dedup", "path_a_fetch"),
        ("path_a_fetch", "path_a_llm_extract"),
        ("path_a_llm_extract", "path_a_validate"),
        ("path_a_validate", "path_a_write"),
        ("path_b_dedup", "path_b_parse"),
        ("path_b_parse", "path_b_filter"),
        ("path_b_filter", "path_b_write"),
        ("path_a_write", "cq_selector"),
        ("path_b_write", "cq_selector"),
        ("cq_selector", "cq_verifier"),
        ("cq_verifier", "cq_composer"),
        ("cq_composer", "cq_approval"),
        ("cq_approval", "cq_export"),
        ("cq_export", "healthcheck_ping"),
    ]
    for src, dst in edges:
        diagram += f"    {src} --> {dst}\n"

    return diagram


def get_pipeline_summary() -> dict:
    """Return counts by status for summary display."""
    registry = get_registry()
    counts = {"idle": 0, "running": 0, "success": 0, "failed": 0, "hung": 0}
    for cid in COMPONENT_ORDER:
        data = registry.get(cid, {})
        status = get_effective_status(data)
        counts[status] = counts.get(status, 0) + 1
    return counts
