"""
LAYER 6: KOL INGEST TOOL — Dr. Don's Operational Tool
Separate tab per CEO request. Dashboard WATCHES, this tool DOES.
MeSH criteria → G.Scholar parse → Push to DB.

CEO: "Can we add this as a separate clickable tab to dashboard to launch,
      or keep it open separate localhost if merging complicates."
AC: Separate tab in sidebar. Same dashboard, same port (5090). Zero merge complexity.
"""

import streamlit as st
import requests
from supabase_client import sb
from config import SQLITE_PATHS

def render():
    st.title("🔧 KOL Ingest Tool")
    st.caption("*This TOOL does things. The dashboard WATCHES. Don't mix them.*")
    st.warning("⚠️ This tool modifies your database. Use with care.")

    # ── INGEST FORM ───────────────────────────────────────────────────────
    st.subheader("🔍 Search KOLs by MeSH Criteria")

    st.markdown("""
    **Workflow:**
    1. Enter MeSH terms (disease area / therapeutic area)
    2. Tool queries KOL database for matching specialists
    3. Review candidates → Push verified KOLs to staging database
    """)

    # MeSH search
    mesh_terms = st.text_input(
        "MeSH Terms (comma-separated)",
        placeholder="e.g., NSCLC, Non-Small Cell Lung Cancer, Immunotherapy",
        help="Enter MeSH terms to filter KOLs by therapeutic area"
    )

    if st.button("🔍 Search KOLs", type="primary"):
        if not mesh_terms:
            st.error("Enter at least one MeSH term.")
        else:
            terms = [t.strip() for t in mesh_terms.split(",")]
            st.info(f"Searching for: {', '.join(terms)}")

            # Query Supabase for matching KOLs
            if sb.is_configured:
                results = sb.select("kols", columns="*",
                                    filters={"verification_status": "verified"},
                                    limit=50)
                if results:
                    st.success(f"Found {len(results)} verified KOLs (filtering by MeSH terms needs backend implementation)")
                    display_rows = []
                    for r in results[:20]:
                        display_rows.append({
                            "Name": r.get("full_name", "—"),
                            "Specialty": r.get("specialty", "—"),
                            "Institution": r.get("institution", "—"),
                            "Status": r.get("verification_status", "—"),
                        })
                    st.dataframe(display_rows, use_container_width=True, hide_index=True)
                else:
                    st.warning("No KOLs found.")
            else:
                st.error("Supabase not configured.")

    # ── GOOGLE SCHOLAR PARSE — COMING SOON ─────────────────────────────────
    st.markdown("---")

    st.markdown("""
    <div style='text-align:center; padding:24px; border:2px dashed #42a5f5; border-radius:12px; background:#111827; margin:8px 0;'>
        <div style='font-size:32px;'>📚</div>
        <div style='font-size:18px; font-weight:bold; color:#42a5f5; margin-top:8px;'>Google Scholar Parse</div>
        <div style='font-size:0.85em; color:#888; margin-top:6px;'>Coming Soon — Auto-enrich KOL profiles with citation data</div>
        <div style='font-size:0.75em; color:#666; margin-top:4px;'>Requires SERPAPI_KEY configuration</div>
    </div>
    """, unsafe_allow_html=True)

    # ── PUSH TO DB ────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("⬆️ Push to Database")

    st.markdown("""
    **Manual KOL Entry:**
    """)

    with st.form("kol_entry"):
        name = st.text_input("Full Name *")
        specialty = st.text_input("Specialty")
        institution = st.text_input("Institution")
        indication = st.text_input("Primary Indication (MeSH)")
        email = st.text_input("Email (optional)")
        submit = st.form_submit_button("➕ Add KOL to Staging")

        if submit:
            if not name:
                st.error("Name is required.")
            elif sb.is_configured:
                row = {
                    "full_name": name.strip(),
                    "specialty": specialty.strip(),
                    "institution": institution.strip(),
                    "primary_indication": indication.strip(),
                }
                if email.strip():
                    row["email"] = email.strip()
                try:
                    r = requests.post(
                        f"{sb.url}/rest/v1/kols_staging",
                        headers={**sb.headers, "Prefer": "return=representation"},
                        json=row,
                        timeout=15,
                    )
                    if r.status_code in (200, 201):
                        st.success(f"✅ KOL '{name}' added to staging!")
                    else:
                        st.error(f"Failed to add KOL: {r.status_code} — {r.text[:200]}")
                except Exception as e:
                    st.error(f"Failed to add KOL: {e}")
            else:
                st.error("Supabase not configured.")

    # ── NOTE ───────────────────────────────────────────────────────────────
    st.markdown("---")
    st.caption("KOL Ingest Tool — Manual entry pushes to Supabase kols_staging. "
               "Google Scholar auto-enrichment coming in a future sprint.")