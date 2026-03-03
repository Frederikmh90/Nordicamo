from __future__ import annotations

import streamlit as st

from pages.footer import render_footer_bar

def show_get_access_page() -> None:
    """Show contact form for data access requests."""
    st.markdown('<h1 class="main-header">Send Us a Message</h1>', unsafe_allow_html=True)
    st.markdown(
        "Please describe your research purpose, specify the datasets/variables you are requesting, and "
        "outline how you intend to use the data (e.g., methodology, scope, and anticipated outputs). "
        "Feel free to tip us if you find alternative news media we should include.",
        unsafe_allow_html=True,
    )
    st.markdown("")
    st.markdown("Requests can be send to **frmohe @ ruc.dk** (Frederik)")
    render_footer_bar()
