from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st


def show_about_page() -> None:
    """Show about page for the observatory."""
    st.markdown('<h1 class="main-header">About Nordicamo</h1>', unsafe_allow_html=True)
    st.markdown(
        "<div class='about-intro'><strong>Nordic Alternative Media Observatory (Nordicamo)</strong> is a comparative "
        "platform for studying alternative news media across the Nordic countries (currently <strong>Denmark, Finland, "
        "Norway, and Sweden</strong>). Nordicamo supports research, journalism, and teaching by providing structured access to "
        "alternative news media content. The platform blends scalable computational analysis with opportunities for "
        "qualitative interpretation, enabling reporting and research through cross-national comparison of alternative "
        "information landscapes.</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div class='about-grid-spacer'></div>", unsafe_allow_html=True)

    def _encode_image(path: Path) -> str:
        if not path.exists():
            return ""
        return base64.b64encode(path.read_bytes()).decode("ascii")

    top_left, top_right = st.columns(2, gap="large")
    with top_left:
        st.markdown(
            """
            <div class="about-card">
                <h4>Data Collection</h4>
                <p>Outlets are selected based on stable publication patterns and clear alternative positioning.
                Country experts help identify relevant outlets for inclusion. A seed list of outlet domains is compiled,
                and article links are collected from site structures and sitemaps when available. Scraping respects
                robots.txt guidance, rate limits, and site stability constraints.
                Content is extracted with Trafilatura and cleaned of boilerplate. Media with very low activity in 2026
                are excluded from the active observatory, while the full archive retains historical ANM primarily active
                in the 2000s and 2010s.</p>
                <div class="about-card-spacer"></div>
                <p>Collected articles are normalized into a common schema (date, outlet, domain, country, and text).
                Quality checks include sampling for content validity and date accuracy. Optional lightweight metadata
                tags (e.g., partisan orientation) are derived from public self-descriptions and manual checks for
                context.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with top_right:
        st.markdown(
            """
            <div class="about-card">
                <h4>Analytical Approach</h4>
                <p>Nordicamo is intentionally descriptive. The platform focuses on high-level patterns in coverage:
                total output, country distribution, outlet concentration, category mix, and publication trends over
                time. These summaries are meant to highlight signals and guide deeper qualitative interpretation,
                rather than produce definitive causal claims (at least in v1.0).</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    bottom_left, bottom_right = st.columns(2, gap="large")
    with bottom_left:
        st.markdown(
            """
            <div class="about-card">
                <h4>Ethics</h4>
                <p>Nordicamo is designed for research on politically sensitive material and follows clear safeguards to
                reduce potential harm. Collection is limited to publicly accessible content, respects site policies
                (including robots.txt/terms where applicable), and uses rate-limiting/backoff to minimize server load.
                We practice data minimization: we avoid collecting unnecessary personal data and exclude high-risk
                identifiers where not essential; access to raw data is restricted, logged, and governed by clear
                retention and deletion practices.</p>
                <p>We document and version scraping procedures to maintain transparency about what is collected, how it
                is processed, and what is excluded. Analyses and outputs are reported primarily in aggregate, with
                careful redaction and quoting rules to reduce risks of amplification, re-identification, or targeting
                of individuals. Findings are presented as exploratory and contextual, not as judgments about persons or
                groups. Nordicamo is intended to support responsible research and to avoid contributing to
                stigmatization, harassment, or misuse.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with bottom_right:
        assets_root = Path(__file__).resolve().parent.parent.parent / "graphics"
        alterpublics_logo = assets_root / "Alterpublics_newlogo.png"
        dml_logo = assets_root / "DML_Logo_nobackground.png"
        alter_encoded = _encode_image(alterpublics_logo)
        dml_encoded = _encode_image(dml_logo)
        alter_img = f"data:image/png;base64,{alter_encoded}" if alter_encoded else ""
        dml_img = f"data:image/png;base64,{dml_encoded}" if dml_encoded else ""
        st.markdown(
            f"""
            <div class="about-card">
                <h4>Affiliations</h4>
                <div class="affiliation-row">
                    <img class="affiliation-logo" src="{alter_img}" alt="AlterPublics logo"/>
                    <div class="affiliation-text"><strong>Nordicamo</strong> is part of the European research project
                    <strong>AlterPublics</strong>, which is based at Roskilde University (Denmark). It studies
                    alternative media and counterpublics across the Nordic countries (Denmark, Sweden,
                    Norway, Finland) and Austria and Germany, using big data, network analysis, and computational text analysis to
                    understand how alternative information environments function and connect with traditional
                    discourse.</div>
                </div>
                <div class="affiliation-row">
                    <img class="affiliation-logo" src="{dml_img}" alt="Digital Media Lab logo"/>
                    <div class="affiliation-text"><strong>Digital Media Lab (DML)</strong> hosts this platform. DML is a
                    digital and physical lab in the Department of Communication and Arts - Roskilde University
                    supporting students, faculty, and external practitioners who work with digital data and digital
                    methods.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
