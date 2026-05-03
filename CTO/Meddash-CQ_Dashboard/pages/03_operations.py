"""
Page 3: Operations — PM2 Status, Healthchecks, Error Log
Health dashboard for the CQ pipeline infrastructure.
"""
import streamlit as st
import subprocess
from datetime import datetime, timezone


def _render_pm2_status():
    """Query PM2 for process status."""
    st.subheader("🔧 PM2 Process Manager")
    try:
        result = subprocess.run(["pm2", "status"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            st.code(result.stdout, language="text")
        else:
            st.warning("PM2 not reachable. It may not be running or the dashboard user lacks permissions.")
    except FileNotFoundError:
        st.error("PM2 CLI not found in PATH.")
    except Exception as e:
        st.warning(f"PM2 query failed: {e}")


def _render_healthcheck_status():
    """Display Healthchecks.io status information."""
    st.subheader("📡 Healthchecks.io")
    st.markdown("""
    | Check | UUID | Status |
    |-------|------|--------|
    | CQ Pipeline Master | `93e4e6b2` | Active — pinged by n8n final node |
    | Alert Channel | Telegram (CQ-Alerts bot) | Configured |
    
    **How it works:** Every successful n8n pipeline execution pings this URL.
    If no ping arrives within the grace period, Healthchecks.io alerts Dr. Don via Telegram.
    """)
    st.info("💡 To check real-time status: visit https://healthchecks.io and log in.")


def _render_error_log():
    """Show recent errors from pipeline_registry."""
    st.subheader("🚨 Recent Pipeline Errors")
    from pipeline_registry import get_registry, get_effective_status, COMPONENT_ORDER, COMPONENT_LABELS
    
    registry = get_registry()
    errors = []
    for cid in COMPONENT_ORDER:
        data = registry.get(cid, {})
        status = get_effective_status(data)
        if status in ("failed", "hung"):
            label = COMPONENT_LABELS.get(cid, cid)
            error = data.get("error_message", "N/A")
            last = data.get("last_updated", "")[:19]
            errors.append({"Component": label, "Status": status.upper(), "Last": last, "Error": error})
    
    if errors:
        st.dataframe(errors, use_container_width=True, hide_index=True)
    else:
        st.success("No errors detected in current pipeline registry.")


def _render_system_info():
    """Basic system health."""
    st.subheader("🖥️ System")
    import os, platform
    st.markdown(f"""
    - **Host:** {platform.node()}
    - **Platform:** {platform.system()} {platform.release()}
    - **Python:** {platform.python_version()}
    - **Dashboard PID:** {os.getpid()}
    - **Render time:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC
    """)


def render():
    st.subheader("⚙️ Operations & Health")
    st.caption("Infrastructure monitoring — PM2 processes, Healthchecks.io, error logs.")

    col1, col2 = st.columns(2)
    with col1:
        _render_pm2_status()
    with col2:
        _render_healthcheck_status()

    st.markdown("---")
    _render_error_log()

    st.markdown("---")
    with st.expander("🖥️ System Info"):
        _render_system_info()
