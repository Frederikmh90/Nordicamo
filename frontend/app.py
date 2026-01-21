"""
NORDICAMO Dashboard - Streamlit Frontend
====================================
Interactive dashboard for Nordic Alternative Media Observatory
"""

import sys
from pathlib import Path
import base64

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import streamlit as st
from PIL import Image, ImageChops

from pages.about import show_about_page
from pages.explorer import show_explorer_page
from pages.get_access import show_get_access_page
from pages.media import show_media_page
from pages.overview import show_overview_page

# Page config
WEBSITE_ICON_PATH = Path(__file__).resolve().parent.parent / "graphics" / "website_icon_2.png"
st.set_page_config(
    page_title="NORDICAMO - Nordic Alternative Media Observatory",
    page_icon=Image.open(WEBSITE_ICON_PATH) if WEBSITE_ICON_PATH.exists() else "📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session defaults for quick country navigation and page selection
if "quick_country" not in st.session_state:
    st.session_state["quick_country"] = None
if "page" not in st.session_state:
    st.session_state["page"] = "Nordicamo"

# Paths
LOGO_PATH = Path(__file__).resolve().parent.parent / "graphics" / "Nordisk Alternativ Medieobservatorium.png"
TRIMMED_LOGO_PATH = Path(__file__).resolve().parent.parent / "graphics" / "logo_trimmed.png"
PREFERRED_LOGO_PATH = Path(__file__).resolve().parent.parent / "graphics" / "logo_trimmed_v2.png"


def get_trimmed_logo():
    """
    Load logo and auto-trim surrounding whitespace/transparency once.
    Returns path to trimmed logo if possible, else original.
    """
    # Prefer the manually provided trimmed asset if available
    if PREFERRED_LOGO_PATH.exists():
        return PREFERRED_LOGO_PATH
    try:
        if TRIMMED_LOGO_PATH.exists():
            return TRIMMED_LOGO_PATH
        if not LOGO_PATH.exists():
            return LOGO_PATH

        img = Image.open(LOGO_PATH).convert("RGBA")
        # Use alpha if present; otherwise trim near-white background
        alpha = img.split()[-1]
        bbox = alpha.getbbox()
        if not bbox:
            # Fallback: trim near-white
            bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
            diff = Image.eval(ImageChops.difference(img, bg), lambda x: x)
            bbox = diff.getbbox()
        if bbox:
            trimmed = img.crop(bbox)
            trimmed.save(TRIMMED_LOGO_PATH)
            return TRIMMED_LOGO_PATH
    except Exception:
        pass
    return LOGO_PATH


def build_topbar_html(current_page: str) -> str:
    nav_items = [
        ("Explorer", "Explorer"),
        ("Media", "Media"),
        ("About", "About"),
        ("Get Access", "GetAccess"),
    ]
    logo_to_use = get_trimmed_logo()
    logo_html = "<div class='topbar-logo'>NAMO</div>"
    if logo_to_use and logo_to_use.exists():
        data = logo_to_use.read_bytes()
        encoded = base64.b64encode(data).decode("ascii")
        logo_html = f"<div class='topbar-logo'><img src='data:image/png;base64,{encoded}' alt='NAMO logo'/></div>"

    links = []
    for label, page_key in nav_items:
        active_class = "active" if current_page == page_key else ""
        cta_class = "cta" if page_key == "GetAccess" else ""
        links.append(
            f"<a class='nav-link {active_class} {cta_class}' href='?page={page_key}' target='_self' onclick=\"window.location.search='page={page_key}'; return false;\">{label}</a>"
        )
    links_html = "".join(links)

    return f"""
    <div class="topbar">
        <div class="topbar-inner">
            <a class="topbar-logo-link" href="/?page=Nordicamo" target="_self">{logo_html}</a>
            <nav class="topbar-nav">
                {links_html}
            </nav>
        </div>
    </div>
    """

# Custom CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');

    :root {
        --color-bg: #f4f7f6;
        --color-card: #ffffff;
        --color-border: #dce3eb;
        --color-text: #222;
        --color-text-muted: #5a6a7a;
        --color-accent: #1f77b4;
        --color-accent-strong: #155d8f;
        --color-logo: #8c342f;
        --color-slider: #8c342f;
        --color-code-bg: #f5f7f9;
        --color-code-border: #d8dee9;
        --color-topbar: rgba(248, 251, 248, 0.95);
        --radius: 8px;
        --space-1: 4px;
        --space-2: 8px;
        --space-3: 12px;
        --space-4: 16px;
        --space-5: 24px;
        --space-6: 32px;
        --shadow-soft: 0 8px 16px rgba(0, 0, 0, 0.04);
    }

    body, .stApp {
        background: radial-gradient(circle at top left, #eef3f7 0%, #f8fbf9 45%, #f4f7f6 100%);
        color: var(--color-text);
        font-family: 'Inter', 'Helvetica', 'Arial', sans-serif;
        line-height: 1.5;
    }

    /* Container spacing */
    .block-container {
        padding: calc(var(--space-6) + 72px) var(--space-5) var(--space-6);
        max-width: 1200px;
        margin: 0 auto;
    }

    /* Header */
    .main-header {
        font-size: 2.2rem;
        font-weight: 600;
        font-family: 'Manrope', 'Helvetica', 'Arial', sans-serif;
        color: var(--color-accent);
        margin: 0 0 var(--space-3) 0;
        line-height: 1.2;
    }

    .section-title {
        font-family: 'Manrope', 'Helvetica', 'Arial', sans-serif;
        font-size: 1.2rem;
        font-weight: 600;
        color: #23313f;
        margin: 0 0 var(--space-2) 0;
    }

    .subtle {
        color: var(--color-text-muted);
        font-size: 0.95rem;
    }

    .hero {
        background: linear-gradient(135deg, #ffffff 0%, #f0f6f4 100%);
        border: 1px solid var(--color-border);
        border-radius: 16px;
        padding: 24px 28px;
        box-shadow: var(--shadow-soft);
    }

    .chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 10px;
        border-radius: 999px;
        background: #e8f2f8;
        color: #1f5b86;
        font-size: 12px;
        font-weight: 600;
    }

    .pulse {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #22c55e;
        box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7);
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7); }
        70% { box-shadow: 0 0 0 8px rgba(34, 197, 94, 0); }
        100% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
    }

    .topbar {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 1000;
        background: var(--color-topbar);
        border-bottom: 1px solid var(--color-border);
        backdrop-filter: blur(10px);
        padding: 12px 0;
    }
    .stMainBlockContainer {
        padding-top: 96px !important;
    }
    .topbar-inner {
        max-width: 1200px;
        margin: 0 auto;
        padding: 0 var(--space-5);
        display: flex;
        align-items: center;
        gap: 24px;
    }
    .topbar-logo img {
        height: 48px;
    }
    .topbar-nav {
        display: flex;
        gap: 18px;
        margin-left: auto;
    }
    .nav-link {
        font-family: 'Manrope', 'Helvetica', 'Arial', sans-serif;
        font-size: 0.95rem;
        font-weight: 600;
        color: #1b3a53;
        text-decoration: none;
        padding: 8px 12px;
        border-radius: 8px;
        border: none;
        background: transparent;
        cursor: pointer;
        transition: background 120ms ease, color 120ms ease;
        display: inline-block;
        outline: none;
        box-shadow: none;
    }
    .nav-link,
    .nav-link:visited,
    .nav-link:hover,
    .nav-link:active {
        text-decoration: none !important;
    }
    .nav-link:focus,
    .nav-link:focus-visible {
        outline: none;
        box-shadow: none;
    }
    .nav-link:hover {
        background: #e6eef4;
    }
    .nav-link.active {
        color: #0f3855;
        text-decoration: none;
    }
    .nav-link.cta {
        background: linear-gradient(135deg, rgba(31, 119, 180, 0.18), rgba(231, 76, 60, 0.18));
        border: 1px solid rgba(31, 119, 180, 0.35);
        color: #1b3a53;
        box-shadow: 0 6px 14px rgba(31, 119, 180, 0.18);
    }
    .nav-link.cta:hover {
        background: linear-gradient(135deg, rgba(31, 119, 180, 0.26), rgba(231, 76, 60, 0.26));
        color: #0f2a3a;
    }
    .nav-link.active.cta {
        background: linear-gradient(135deg, rgba(31, 119, 180, 0.28), rgba(231, 76, 60, 0.28));
        border-color: rgba(31, 119, 180, 0.5);
        box-shadow: 0 8px 18px rgba(31, 119, 180, 0.22);
    }

    .media-card {
        border: 1px solid var(--color-border);
        border-radius: 14px;
        padding: 16px;
        background: rgba(255, 255, 255, 0.6);
        box-shadow: var(--shadow-soft);
        min-height: 170px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .media-card h3 {
        font-family: 'Manrope', 'Helvetica', 'Arial', sans-serif;
        font-size: 1.05rem;
        margin: 0 0 6px 0;
        color: #15212c;
    }
    .media-meta {
        font-size: 0.9rem;
        color: var(--color-text-muted);
        margin-bottom: 8px;
    }
    .media-count {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1f77b4;
    }
    .stat-card {
        border: 1px solid var(--color-border);
        border-radius: 14px;
        padding: 14px 16px;
        background: #ffffff;
        box-shadow: var(--shadow-soft);
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    .stat-card .label {
        font-size: 0.85rem;
        color: var(--color-text-muted);
    }
    .stat-card .value {
        font-size: 1.3rem;
        font-weight: 700;
        color: #15212c;
    }

    /* Buttons */
    .stButton > button {
        background: var(--color-accent);
        color: #fff;
        border: none;
        padding: 10px 20px;
        border-radius: var(--radius);
        font-weight: 600;
        box-shadow: var(--shadow-soft);
        transition: all 120ms ease;
    }
    .stButton > button:hover {
        background: var(--color-accent-strong);
        transform: translateY(-1px);
    }

    div[data-baseweb="slider"] [role="slider"] {
        background-color: var(--color-slider) !important;
        border-color: var(--color-slider) !important;
    }
    div[data-baseweb="slider"] > div > div > div {
        background-color: var(--color-slider) !important;
    }
    div[data-baseweb="slider"] [data-testid="stTickBarTick"] {
        color: #0154a3 !important;
        font-size: 0.9rem !important;
        font-weight: 600;
    }
    div[data-baseweb="slider"] [data-testid="stTickBarTickLabel"] {
        color: #0154a3 !important;
        font-size: 0.9rem !important;
        font-weight: 600;
    }
    div[data-baseweb="slider"] [data-testid="stSliderTickBar"] span {
        display: none !important;
    }
    .stSlider [class*="st-c"] {
        color: #0154a3 !important;
        font-size: 0.9rem !important;
        font-weight: 600;
    }
    div[data-baseweb="slider"] [data-testid="stTickBarTickLabel"] + div,
    div[data-baseweb="slider"] .st-cs.st-ct.st-c8.st-c7.st-as.st-cu.st-cv,
    div[data-baseweb="slider"] .st-cs.st-ct.st-c8.st-c7.st-cs.st-cu.st-cv,
    .stSlider [class*="st-c"] {
        color: #0154a3 !important;
        font-size: 0.9rem !important;
        font-weight: 600;
    }
    div[data-baseweb="slider"] [role="tooltip"],
    div[data-baseweb="slider"] [data-testid="stTooltipIcon"] {
        display: none !important;
    }

    /* Cards / metrics */
    .metric-card, .stMetric {
        background: var(--color-card);
        padding: var(--space-4);
        border-radius: var(--radius);
        border: 1px solid var(--color-border);
        box-shadow: var(--shadow-soft);
        color: var(--color-text);
    }

    /* Plotly charts */
    .stPlotlyChart {
        background: var(--color-card) !important;
        border: 1px solid var(--color-border);
        border-radius: var(--radius);
        padding: var(--space-3);
    }

    .affiliation-text {
        margin-top: 4px;
    }
    .about-intro {
        color: #111111;
        margin-bottom: 18px;
    }
    .about-grid-spacer {
        height: 12px;
    }
    .about-card {
        background: rgba(255, 255, 255, 0.75);
        border: 1px solid var(--color-border);
        border-radius: 12px;
        padding: 14px 16px;
        box-shadow: var(--shadow-soft);
        margin-bottom: 12px;
    }
    .about-card:empty {
        display: none;
    }
    .about-card h4 {
        margin-top: 0;
        margin-bottom: 8px;
    }
    .about-card p {
        margin: 0;
    }
    .about-card-spacer {
        height: 10px;
    }
    .affiliation-row {
        display: flex;
        gap: 12px;
        align-items: flex-start;
        margin-top: 12px;
    }
    .affiliation-logo {
        width: 120px;
        height: auto;
    }

    /* Tables */
    .dataframe tbody tr:hover {
        background: #eef3f7;
    }

    .news-ticker {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 16px;
        margin: 0 0 16px 0;
        background: rgba(255, 255, 255, 0.85);
        border: 1px solid var(--color-border);
        border-radius: 999px;
        overflow: hidden;
        box-shadow: var(--shadow-soft);
    }

    .news-ticker-label {
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--color-logo);
        white-space: nowrap;
    }

    .news-ticker-track {
        position: relative;
        flex: 1;
        overflow: hidden;
        white-space: nowrap;
    }

    .news-ticker-items {
        display: inline-block;
        padding-left: 100%;
        animation: ticker-scroll 39s linear infinite;
        font-size: 13px;
        color: var(--color-text-muted);
    }

    .news-ticker-item {
        display: inline-block;
        margin-right: 32px;
    }

    @keyframes ticker-scroll {
        0% {
            transform: translateX(0);
        }
        100% {
            transform: translateX(-100%);
        }
    }

    /* Code blocks */
    code, pre {
        background: var(--color-code-bg);
        border-bottom: 1px solid var(--color-code-border);
        color: #a7adba;
    }
    code {
        padding: 2px 4px;
        vertical-align: text-bottom;
    }
    pre {
        padding: 1em;
        border-left: 2px solid #69c;
        border-radius: var(--radius);
    }

    /* Hide Streamlit status/toolbar strip */
    [data-testid="stStatusWidget"],
    [data-testid="stToolbar"] {
        display: none !important;
    }
    /* Hide default Streamlit sidebar and header */
    [data-testid="stSidebar"], [data-testid="stSidebarContent"], [data-testid="stHeader"] {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)
def main():
    """Main application."""
    page = None
    try:
        params = st.query_params
        page = params.get("page")
    except Exception:
        params = st.experimental_get_query_params()
        page_list = params.get("page")
        page = page_list[0] if page_list else None

    legacy_pages = {"Platform": "Nordicamo", "Countries": "Explorer", "Get Access": "GetAccess"}
    if page in legacy_pages:
        page = legacy_pages[page]
        try:
            st.query_params["page"] = page
        except Exception:
            st.experimental_set_query_params(page=page)

    allowed_pages = {"Nordicamo", "Explorer", "Media", "About", "GetAccess"}
    if page in allowed_pages:
        st.session_state["page"] = page

    current_page = st.session_state.get("page", "Nordicamo")
    if current_page not in allowed_pages:
        current_page = "Nordicamo"
        st.session_state["page"] = current_page

    if current_page != "Explorer":
        st.session_state["quick_country"] = None

    st.markdown(build_topbar_html(current_page), unsafe_allow_html=True)

    # Route to page
    if current_page == "Nordicamo":
        show_overview_page()
    elif current_page == "Explorer":
        show_explorer_page()
    elif current_page == "Media":
        show_media_page()
    elif current_page == "About":
        show_about_page()
    elif current_page == "GetAccess":
        show_get_access_page()


if __name__ == "__main__":
    main()
