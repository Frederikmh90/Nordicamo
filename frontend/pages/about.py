from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st
from pages.footer import render_footer_bar


def show_about_page() -> None:
    """Show about page for the observatory."""
    st.markdown('<h1 class="main-header">About Nordicamo</h1>', unsafe_allow_html=True)
    st.markdown(
        "<div class='about-intro'><strong>Nordic Alternative Media Observatory (Nordicamo)</strong> is a comparative "
        "platform for studying alternative news media across Denmark, Finland, Norway, and Sweden. Alternative news media "
        "refers to publisher-operated outlets that position themselves as alternatives to mainstream journalism, political "
        "institutions, or dominant public narratives. The observatory focuses on outlet websites rather than social media "
        "accounts.</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='about-intro'>The platform provides structured data and descriptive analytics for comparing publication "
        "patterns, outlet structures, and topic distributions across countries and over time. Nordicamo supports case "
        "selection, documentation, and exploratory analysis; it should not be read as a complete census of all alternative "
        "media activity or as an evaluation of outlet influence, audience reach, or societal impact. Code and version history "
        "are available on "
        "<a href='https://github.com/Frederikmh90/Nordicamo' target='_blank' rel='noopener'>GitHub</a>.</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div class='about-grid-spacer'></div>", unsafe_allow_html=True)

    def _encode_image(path: Path) -> str:
        if not path.exists():
            return ""
        return base64.b64encode(path.read_bytes()).decode("ascii")

    top_left, top_right = st.columns(2, gap="large")
    st.markdown("<div class='about-row'>", unsafe_allow_html=True)
    with top_left:
        st.markdown(
            """
            <div class="about-card top-row">
                <h4>Outlet Selection</h4>
                <p>Outlets are included based on (1) sustained publication activity and (2) a clear alternative positioning, reflected in public
                self-descriptions, editorial statements, or consistent framing practices. Country experts contribute to identifying relevant
                outlets and validating contextual relevance. Nordicamo maintains a versioned outlet list that documents additions, removals,
                and selection rationales over time.</p>
                <h5>Coverage Limits</h5>
                <p>To support both current analysis and historical research, Nordicamo distinguishes between:</p>
                <ul>
                    <li>Active observatory: outlets meeting a minimum activity threshold in the current monitoring period.</li>
                    <li>Historical data: a broader historical collection that may include outlets primarily active in earlier decades (e.g., the 2000s-2010s).</li>
                </ul>
                <p>Collection focuses on recently updated outlets or outlets with an accessible web presence, so historical
                coverage reflects the subset of outlets that remain technically reachable at the time of collection.</p>
                <p>Because selection criteria prioritize stability and technical feasibility, the dataset may underrepresent short-lived projects,
                irregular publishers, and outlets without indexable structures.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with top_right:
        st.markdown(
            """
            <div class="about-card top-row">
                <h4>Ethics</h4>
                <p>Nordicamo is designed for research on politically sensitive material and follows safeguards to reduce potential harm.</p>
                <h5>Collection and data minimization</h5>
                <p>Collection is limited to publicly accessible content and is conducted with respect for site policies (robots.txt/Terms of
                Service where applicable) and operational constraints (rate limiting/backoff). Nordicamo avoids collecting user-level data,
                private communications, comments, and social media interactions unless explicitly required for a separately approved research
                purpose.</p>
                <div class="about-card-spacer"></div>
                <h5>Access, governance, and retention</h5>
                <p>Access to raw content is restricted and governed by clear access tiers, logging, and retention/deletion practices.
                Public-facing outputs prioritize aggregated summaries. Data handling procedures are documented and versioned to maintain
                transparency about what is collected, how it is processed, and what is excluded.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    bottom_left, bottom_right = st.columns(2, gap="large")
    st.markdown("<div class='about-row'>", unsafe_allow_html=True)
    with bottom_left:
        st.markdown(
            """
            <div class="about-card bottom-row">
                <h4>Data Collection</h4>
                <p>A seed list of outlet domains is compiled, and article URLs are collected from site structures (e.g., category pages, archive pages)
                and sitemaps when available. Custom scrapers are used for some outlets where sitemaps are unavailable. Collection respects robots.txt
                guidance and applies rate limits and backoff to minimize server load. Outlets that block automated access, rely heavily on dynamic
                rendering, or provide unreliable timestamps may have partial coverage.</p>
                <div class="about-card-spacer"></div>
                <h5>Extraction, normalization, and quality checks</h5>
                <p>Content is extracted using Trafilatura and cleaned of boilerplate. Articles are normalized into a common schema (e.g., publication
                date, outlet, domain, country, URL, and main text). Quality checks include routine sampling for extraction validity, duplicate
                detection where feasible, and date verification (noting that some sites provide ambiguous or unstable timestamps).</p>
                <p>Lightweight metadata (e.g., self-described political orientation and news classification) are added based on public self-descriptions
                and manual checks. These tags are provided as contextual aids rather than authoritative classifications.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with bottom_right:
        st.markdown(
            """
            <div class="about-card bottom-row">
                <h4>Analytical Approach</h4>
                <p>Nordicamo is intentionally descriptive and exploratory. The platform highlights high-level patterns in alternative news media
                production and coverage, including total output, country distribution, outlet concentration, publication trends over time, and
                (where available) topical/category patterns.</p>
                <p>These summaries are intended to help users:</p>
                <ul>
                    <li>detect shifts and spikes that may warrant closer attention,</li>
                    <li>identify cross-national similarities and differences,</li>
                    <li>guide deeper qualitative work (close reading, case selection, or interpretive analysis).</li>
                </ul>
                <p>Nordicamo is descriptive and exploratory. Results should be interpreted in light of the documented selection criteria,
                technical constraints, and the evolving nature of the outlet list.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

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
                <div class="affiliation-text"><strong>Nordicamo</strong> is part of the Carlsberg-funded research project
                <strong>AlterPublics</strong>, which is based at Roskilde University (Denmark). It studies
                alternative media and counterpublics across the Nordic countries (Denmark, Sweden,
                Norway, Finland) and Austria and Germany, using big data, network analysis, and computational text analysis to
                understand how alternative information environments function and connect with traditional
                discourse.</div>
            </div>
            <div class="affiliation-row">
                <img class="affiliation-logo" src="{dml_img}" alt="Digital Media Lab logo"/>
                <div class="affiliation-text"><a href="https://digitalmedialab.ruc.dk/" target="_blank" rel="noopener"><strong>Digital Media Lab (DML)</strong></a> hosts this platform. DML is a
                digital and physical lab in the Department of Communication and Arts - Roskilde University
                supporting students, faculty, and external practitioners who work with digital data and digital
                methods.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_footer_bar()
