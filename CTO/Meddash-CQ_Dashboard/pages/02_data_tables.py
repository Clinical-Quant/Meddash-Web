"""
Page 2: Data Tables — Supabase CQ Tables (Manual Sync Only)
Tables are cached for 1 hour. Dr. Don clicks 'Force Synchronize' once per weekday.
Plotly charts load after sync.
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Load env vars BEFORE creating connection
import config as _cfg  # noqa: F401 — side-effect: loads .env into os.environ

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Supabase credentials not found. Check .env files.")


TABLES = [
    "cq_selected_candidates",
    "cq_research_confirmations",
    "cq_content_queue",
    "cq_source_artifacts",
    "cq_catalysts",
    "cq_insider_trades",
]


@st.cache_data(ttl=3600)
def load_table(table_name: str) -> pd.DataFrame:
    """Cached Supabase pull — cleared on manual sync. Uses raw REST, not st.connection."""
    import urllib.request, json
    try:
        url = f"{SUPABASE_URL}/rest/v1/{table_name}?select=*"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        return pd.DataFrame(data)
    except Exception as e:
        return pd.DataFrame({"error": [str(e)]})


def _render_sync_panel():
    """Manual sync button + last sync time."""
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🔄 Force Synchronize", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.session_state["cq_last_sync"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
            st.rerun()
    with col2:
        last = st.session_state.get("cq_last_sync", "Never")
        st.caption(f"Last sync: {last} | Tables cached 1 hour | Sync once per weekday to preserve Supabase quota")


def _render_table_tab(table_name: str):
    """Single table view with editable grid."""
    st.subheader(f"📊 {table_name}")
    df = load_table(table_name)
    if "error" in df.columns:
        st.warning(f"Could not load {table_name}: {df.iloc[0]['error']}")
        return
    st.caption(f"{len(df)} rows")
    st.data_editor(df, use_container_width=True, num_rows="dynamic", key=f"editor_{table_name}")


def _render_charts():
    """Plotly charts — load only after sync, placeholder for now."""
    st.subheader("📈 Analytics Charts")
    st.caption("Charts load after manual data sync.")

    df = load_table("cq_selected_candidates")
    if "error" in df.columns or len(df) == 0:
        st.info("No data loaded yet. Click 'Force Synchronize' to pull tables, then charts will appear here.")
        return

    try:
        import plotly.express as px

        if "status" in df.columns:
            status_counts = df["status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]
            fig = px.pie(status_counts, names="Status", values="Count",
                        title="Candidate Status Distribution",
                        color_discrete_sequence=px.colors.qualitative.Set2)
            st.plotly_chart(fig, use_container_width=True)

        if "created_at" in df.columns:
            df_time = df.copy()
            df_time["created_at"] = pd.to_datetime(df_time["created_at"])
            df_time["date"] = df_time["created_at"].dt.date
            timeline = df_time.groupby("date").size().reset_index(name="count")
            fig2 = px.line(timeline, x="date", y="count",
                         title="Candidates by Day", markers=True)
            st.plotly_chart(fig2, use_container_width=True)

    except Exception as e:
        st.warning(f"Chart rendering skipped: {e}")


def render():
    st.subheader("📊 Data Tables & Analytics")
    st.caption("All Supabase tables are cached. Use 'Force Synchronize' to pull fresh data (recommended: once per weekday).")

    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("Cannot connect to Supabase. Set SUPABASE_URL and SUPABASE_KEY in .env.")
        return

    _render_sync_panel()

    tabs = st.tabs(TABLES)
    for tab, table_name in zip(tabs, TABLES):
        with tab:
            _render_table_tab(table_name)

    st.markdown("---")
    _render_charts()
