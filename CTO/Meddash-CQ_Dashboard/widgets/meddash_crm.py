"""
MEDDASH CRM — Coming Soon
Placeholder tab for future CRM integration.

This page intentionally avoids revenue, pipeline value, and client metrics until
a real CRM source is connected.
"""

import streamlit as st


def render():
    st.markdown(
        """
        <div class="factory-hero crm-hero">
          <div class="factory-eyebrow">Meddash CRM · Coming soon</div>
          <h1>🤝 Meddash CRM</h1>
          <p>
            This page will become the sales/client layer once the simple CRM is fixed and connected.
            Until then, the dashboard will not display revenue, deal value, pipeline value, or client-count metrics.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info(
        "CRM is intentionally not connected yet. We have not spoken to clients through a tracked CRM flow, so showing revenue or deal value would be misleading.",
        icon="🧭",
    )

    cols = st.columns(3)
    with cols[0]:
        _coming_card(
            "Contacts",
            "Coming soon",
            "Prospects, clinicians, biotech contacts, and relationship history will appear here after CRM connection.",
        )
    with cols[1]:
        _coming_card(
            "Outreach Pipeline",
            "Coming soon",
            "Lead status, next action, last touch, and follow-up reminders will appear here after the simple CRM is fixed.",
        )
    with cols[2]:
        _coming_card(
            "Revenue / Deals",
            "Hidden for now",
            "This will stay blank until a real CRM/deal source exists. No estimated revenue figures are shown.",
        )

    st.markdown("### Planned CRM summary")
    st.markdown(
        """
        - Contact list and lead source
        - Outreach status: not contacted, contacted, replied, meeting booked, proposal sent, closed
        - Next action and follow-up date
        - Notes from calls/messages
        - Only after that: real deal/revenue fields from actual CRM records
        """
    )


def _coming_card(title: str, value: str, description: str):
    st.markdown(
        f"""
        <div class="modern-metric metric-idle">
          <div class="metric-kicker">CRM MODULE</div>
          <h4>{title}</h4>
          <div class="metric-value">{value}</div>
          <p>{description}</p>
          <div class="metric-footer">No CRM source connected yet.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
