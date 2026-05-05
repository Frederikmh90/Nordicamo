from __future__ import annotations

import streamlit as st

from pages.footer import render_footer_bar

ACCESS_FEEDBACK_TEXT = (
    "You are also welcome to suggest platform features, outlet candidates for future "
    "observation, or other feedback that could strengthen Nordicamo as a research infrastructure."
)


def show_get_access_page() -> None:
    """Show contact form for data access requests."""
    st.markdown('<h1 class="main-header">Request Access</h1>', unsafe_allow_html=True)
    st.markdown(
        "<div class='subtle' style='font-size:1.08rem;'>Request current or historical Nordicamo data for research, journalism, or teaching. "
        "Please describe your purpose, the countries/outlets/time period you need, and the variables or article fields you expect to use.</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class='access-checklist'>
            <strong>Include this in your request</strong>
            <ul>
                <li>Research purpose and institutional affiliation.</li>
                <li>Countries, outlets, and time period needed.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='about-card'><strong>Email:</strong> frmohe @ ruc.dk "
        "(Frederik Henriksen, postdoc in the AlterPublics research project)<br/>"
        f"<span class='subtle'>{ACCESS_FEEDBACK_TEXT}</span></div>",
        unsafe_allow_html=True,
    )
    render_footer_bar()
