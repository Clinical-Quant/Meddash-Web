"""
MEDDASH-CQ DASHBOARD v2
Stripped-down, deterministic, fragment-based.

Startup: streamlit run app.py --server.port 5090

Tabs:
  1. Circuit Board — live pipeline flow (fragment, 15s refresh)
  2. Data Tables — Supabase tables (manual sync only)
  3. Operations — PM2, Healthchecks, errors
"""

import streamlit as st
import os
from datetime import datetime

# ── Page config ──
st.set_page_config(
    page_title="MEDDASH-CQ",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ──
css_path = os.path.join(os.path.dirname(__file__), "styles.css")
if os.path.exists(css_path):
    with open(css_path, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── Auto-refresh ──
REFRESH_SECONDS = 120
st.markdown(
    f'<meta http-equiv="refresh" content="{REFRESH_SECONDS}">',
    unsafe_allow_html=True,
)

_RENDERED_AT = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ── Sidebar ──
st.sidebar.title("MEDDASH-CQ")
st.sidebar.markdown("---")
st.sidebar.markdown("🏭 *Live Pipeline Diagnostic*")
st.sidebar.markdown("---")

# Tab selection
TABS = {
    "🏭 Circuit Board": "pages.01_circuit_board",
    "📊 Data Tables": "pages.02_data_tables",
    "⚙️ Operations": "pages.03_operations",
}

tab = st.sidebar.radio("Navigate", list(TABS.keys()), label_visibility="collapsed")

# ── Fragment wrapper for Circuit Board ──
if tab == "🏭 Circuit Board":
    @st.fragment(run_every=15)
    def _circuit_board_fragment():
        import importlib
        mod = importlib.import_module(TABS[tab])
        mod.render()
    _circuit_board_fragment()
else:
    import importlib
    mod = importlib.import_module(TABS[tab])
    mod.render()

# ── Footer ──
st.sidebar.markdown("---")
st.sidebar.caption("Built by Alfred Chief for Dr. Don")
st.sidebar.caption(f"Render: {_RENDERED_AT}")
st.sidebar.caption("v2 — Deterministic Registry")
