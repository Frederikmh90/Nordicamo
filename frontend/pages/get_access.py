from __future__ import annotations

import streamlit as st

from services.api import send_access_request


def show_get_access_page() -> None:
    """Show contact form for data access requests."""
    st.markdown('<h1 class="main-header">Get Access - Send Us a Message</h1>', unsafe_allow_html=True)
    st.markdown(
        "Please describe your research purpose, specify the datasets/variables you are requesting, and "
        "outline how you intend to use the data (e.g., methodology, scope, and anticipated outputs). "
        "Feel free to tip us if you find alternative news media we should include.",
        unsafe_allow_html=True,
    )

    with st.form("access_request"):
        st.markdown("<div class='section-title'>Contact</div>", unsafe_allow_html=True)

        name = st.text_input("Name", placeholder="Your full name")
        email = st.text_input("Email", placeholder="name@organization.org")
        request = st.text_area(
            "Message",
            height=200,
            placeholder="Describe the data you need (countries, outlets, date ranges, or full dataset).",
        )
        submitted = st.form_submit_button("Submit")

    if submitted:
        missing = []
        if not name.strip():
            missing.append("name")
        if not email.strip():
            missing.append("email")
        if not request.strip():
            missing.append("request details")

        if missing:
            st.error(f"Please provide {', '.join(missing)}.")
            return

        if send_access_request(name=name, email=email, message=request):
            st.success("Request sent. We will get back to you soon.")
