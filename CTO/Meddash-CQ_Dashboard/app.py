"""
MEDDASH-CQ FACTORY DASHBOARD
The production line for your business — one dashboard, two departments.

Startup:
  cd /mnt/c/Users/email/.gemini/antigravity/CTO/Meddash-CQ_Dashboard
  source venv/bin/activate
  streamlit run app.py --server.port 5090

Architecture:
  app.py          → Main router (sidebar tabs)
  config.py       → Environment, DB paths, queries
  supabase_client → Singleton Supabase REST client
  widgets/        → One file per widget (modular, add new = add file)
"""

import streamlit as st
import importlib
import os
import sys
from datetime import datetime
from config import REFRESH_SECONDS

# ── Page config (must be first) ──────────────────────────────────────────────
st.set_page_config(
    page_title="MEDDASH-CQ Factory",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inject custom CSS ────────────────────────────────────────────────────────
css_path = os.path.join(os.path.dirname(__file__), "styles.css")
with open(css_path, "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── Browser auto-refresh guard ───────────────────────────────────────────────
# REFRESH_SECONDS existed in config.py but was previously not wired into the app,
# so a live browser tab could sit on stale Streamlit state forever. Keep this
# zero-dependency: importing streamlit_autorefresh from the Windows-mounted venv
# was observed to hang startup under WSL/NTFS.
st.markdown(f'<meta http-equiv="refresh" content="{REFRESH_SECONDS}">', unsafe_allow_html=True)
_refresh_mode = "browser_meta_refresh"

_rendered_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ── Route map ────────────────────────────────────────────────────────────────
PAGES = {
    "🏭 Factory Floor": "widgets.factory_floor",     # Layer 5 Bridge + animated flow
    "🛠️ Pipeline Health": "widgets.pipeline_health", # Live Mermaid health diagram
    "💗 Pulse":         "widgets.pulse",               # Layer 1 top bar
    "🔬 Meddash":       "widgets.meddash_panel",        # Layer 2
    "🤝 Meddash CRM":   "widgets.meddash_crm",          # CRM placeholder — coming soon
    "💊 Clinical Quant": "widgets.cq_panel",            # Layer 3
    "⚙️ Operations":    "widgets.operations",           # Layer 4
    "🔧 KOL Ingest":   "widgets.kol_ingest",           # Dr. Don's tool — separate tab
}

# ── Sidebar navigation ───────────────────────────────────────────────────────
st.sidebar.title("MEDDASH-CQ")
st.sidebar.markdown("---")
st.sidebar.markdown("*One factory. Two departments.*")
st.sidebar.markdown("---")

selection = st.sidebar.radio("Navigate", list(PAGES.keys()), label_visibility="collapsed")

# ── Load and render selected page ────────────────────────────────────────────
module_name = PAGES[selection]
try:
    mod = importlib.import_module(module_name)
    mod.render()
except Exception as e:
    st.error(f"Failed to load `{module_name}`: {e}")
    with st.expander("Traceback"):
        st.code(str(e))

# ── Footer ───────────────────────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.caption("Built by Alfred Chief for Dr. Don")
st.sidebar.caption(f"Last render: {_rendered_at}")
st.sidebar.caption(f"Auto-refresh: {REFRESH_SECONDS}s ({_refresh_mode})")
st.sidebar.caption("v1.1 — 2026-04-29")