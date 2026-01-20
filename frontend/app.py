"""
NAMO Dashboard - Streamlit Frontend
====================================
Interactive dashboard for Nordic Alternative Media Observatory
"""

import sys
from pathlib import Path
import importlib.machinery
import types
import base64

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

def _load_local_module(module_name: str, file_name: str):
    module_path = (BASE_DIR / file_name).resolve()
    if not module_path.exists():
        raise FileNotFoundError(f"Missing {module_name} at {module_path}")
    loader = importlib.machinery.SourceFileLoader(module_name, str(module_path))
    module = types.ModuleType(module_name)
    loader.exec_module(module)
    sys.modules[module_name] = module
    return module

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging
from PIL import Image, ImageChops
try:
    from config import get_api_base_url
except ModuleNotFoundError:
    get_api_base_url = _load_local_module("config", "config.py").get_api_base_url

try:
    from overview_helpers import (
        format_freshness,
        compute_top_n_share,
        compute_partisan_shares,
        compute_lorenz_curve,
    )
except ModuleNotFoundError:
    overview_helpers = _load_local_module("overview_helpers", "overview_helpers.py")
    format_freshness = overview_helpers.format_freshness
    compute_top_n_share = overview_helpers.compute_top_n_share
    compute_partisan_shares = overview_helpers.compute_partisan_shares
    compute_lorenz_curve = overview_helpers.compute_lorenz_curve

try:
    from media_helpers import filter_outlets, consolidate_outlets
except ModuleNotFoundError:
    media_module = _load_local_module("media_helpers", "media_helpers.py")
    filter_outlets = media_module.filter_outlets
    consolidate_outlets = media_module.consolidate_outlets

# Configuration
API_BASE_URL = get_api_base_url()
DASHBOARD_VERSION = "0.1.0"  # Version 0.1 - Initial release

# Page config
st.set_page_config(
    page_title="NAMO - Nordic Alternative Media Observatory",
    page_icon="📰",
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


@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_overview():
    """Fetch overview statistics."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/stats/overview", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching overview: {e}")
        return None


@st.cache_data(ttl=300)
def fetch_enhanced_overview():
    """Fetch enhanced overview with additional metrics."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/stats/overview/enhanced", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching enhanced overview: {e}")
        return None


@st.cache_data(ttl=60)  # Cache for 1 minute (fresher data)
def fetch_data_freshness():
    """Fetch data freshness information."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/stats/data-freshness", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return None


@st.cache_data(ttl=300)
def fetch_outlet_concentration(country=None):
    """Fetch outlet concentration ratio."""
    try:
        params = {}
        if country:
            params["country"] = country
        response = requests.get(
            f"{API_BASE_URL}/api/stats/outlet-concentration",
            params=params,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return None


@st.cache_data(ttl=300)
def fetch_comparative_metrics():
    """Fetch comparative metrics across countries."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/stats/comparative", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return None


@st.cache_data(ttl=60)  # Cache for 1 minute (fresher for article search)
def fetch_articles(
    query=None,
    date_from=None,
    date_to=None,
    country=None,
    partisan=None,
    sentiment=None,
    categories=None,
    entities=None,
    outlets=None,
    limit=50,
    offset=0
):
    """Search articles with filters."""
    try:
        params = {
            "limit": limit,
            "offset": offset
        }
        if query:
            params["q"] = query
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        if country:
            params["country"] = country
        if partisan:
            params["partisan"] = partisan
        if sentiment:
            params["sentiment"] = sentiment
        if categories:
            params["categories"] = ",".join(categories) if isinstance(categories, list) else categories
        if entities:
            params["entities"] = ",".join(entities) if isinstance(entities, list) else entities
        if outlets:
            params["outlets"] = ",".join(outlets) if isinstance(outlets, list) else outlets
        
        response = requests.get(
            f"{API_BASE_URL}/api/articles/search",
            params=params,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error searching articles: {e}")
        return None


@st.cache_data(ttl=300)
def fetch_article_by_id(article_id: int):
    """Fetch a single article by ID."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/articles/{article_id}",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return None


@st.cache_data(ttl=300)
def fetch_related_articles(article_id: int, limit=5):
    """Fetch related articles."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/articles/{article_id}/related",
            params={"limit": limit},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return None


@st.cache_data(ttl=300)
def fetch_articles_by_country(partisan=None, date_from=None, date_to=None):
    """Fetch articles by country."""
    try:
        params = {}
        if partisan:
            params["partisan"] = partisan
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        
        response = requests.get(
            f"{API_BASE_URL}/api/stats/articles-by-country",
            params=params,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching articles by country: {e}")
        return None


@st.cache_data(ttl=300)
def fetch_articles_over_time(country=None, partisan=None, granularity="month", date_from=None, date_to=None):
    """Fetch articles over time."""
    try:
        params = {"granularity": granularity}
        if country:
            params["country"] = country
        if partisan:
            params["partisan"] = partisan
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        
        response = requests.get(
            f"{API_BASE_URL}/api/stats/articles-over-time",
            params=params,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching articles over time: {e}")
        return None


@st.cache_data(ttl=300)
def fetch_articles_over_time_by_outlet(country=None, outlets=None, granularity="month", date_from=None, date_to=None):
    """Fetch articles over time grouped by outlet."""
    try:
        params = {"granularity": granularity}
        if country:
            params["country"] = country
        if outlets:
            params["outlets"] = ",".join(outlets) if isinstance(outlets, list) else outlets
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        
        response = requests.get(
            f"{API_BASE_URL}/api/stats/articles-over-time-by-outlet",
            params=params,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching articles over time by outlet: {e}")
        return None


@st.cache_data(ttl=300, show_spinner=False)
def fetch_top_outlets(country=None, partisan=None, date_from=None, date_to=None, limit=10):
    """Fetch top outlets."""
    try:
        params = {"limit": limit}
        if country:
            params["country"] = country
        if partisan:
            params["partisan"] = partisan
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        
        response = requests.get(
            f"{API_BASE_URL}/api/stats/top-outlets",
            params=params,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching top outlets: {e}")
        return None


@st.cache_data(ttl=300, show_spinner=False)
def fetch_outlet_profile(domain: str):
    """Fetch outlet profile summary by domain."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/stats/outlet-profile",
            params={"domain": domain},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching outlet profile: {e}")
        return None


def send_access_request(name: str, email: str, message: str) -> bool:
    """Send access request to backend for email delivery."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/contact",
            json={"name": name, "email": email, "message": message},
            timeout=10
        )
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Error sending request: {e}")
        return False


@st.cache_data(ttl=300)
def fetch_categories(country=None, partisan=None):
    """Fetch category distribution."""
    try:
        params = {}
        if country:
            params["country"] = country
        if partisan:
            params["partisan"] = partisan
        
        response = requests.get(
            f"{API_BASE_URL}/api/stats/categories",
            params=params,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching categories: {e}")
        return None


@st.cache_data(ttl=300)
def fetch_categories_over_time(country=None, partisan=None, granularity="month", date_from=None, date_to=None, limit=6):
    """Fetch category trends over time."""
    try:
        params = {"granularity": granularity, "limit": limit}
        if country:
            params["country"] = country
        if partisan:
            params["partisan"] = partisan
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to

        response = requests.get(
            f"{API_BASE_URL}/api/stats/categories/over-time",
            params=params,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching category trends: {e}")
        return None


@st.cache_data(ttl=300)
def fetch_sentiment(country=None, partisan=None):
    """Fetch sentiment distribution."""
    try:
        params = {}
        if country:
            params["country"] = country
        if partisan:
            params["partisan"] = partisan
        
        response = requests.get(
            f"{API_BASE_URL}/api/stats/sentiment",
            params=params,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching sentiment: {e}")
        return None


@st.cache_data(ttl=300)
def fetch_top_entities(entity_type="persons", country=None, partisan=None, limit=20):
    """Fetch top entities."""
    try:
        params = {"entity_type": entity_type, "limit": limit}
        if country:
            params["country"] = country
        if partisan:
            params["partisan"] = partisan
        
        response = requests.get(
            f"{API_BASE_URL}/api/stats/entities/top",
            params=params,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching entities: {e}")
        return None


@st.cache_data(ttl=300)
def fetch_entity_statistics(country=None, partisan=None):
    """Fetch entity statistics."""
    try:
        params = {}
        if country:
            params["country"] = country
        if partisan:
            params["partisan"] = partisan
        
        response = requests.get(
            f"{API_BASE_URL}/api/stats/entities/statistics",
            params=params,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching entity statistics: {e}")
        return None


@st.cache_data(ttl=300)
def fetch_topic_distribution(country=None, partisan=None, date_from=None, date_to=None):
    """Fetch topic distribution."""
    try:
        params = {}
        if country:
            params["country"] = country
        if partisan:
            params["partisan"] = partisan
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        
        response = requests.get(
            f"{API_BASE_URL}/api/topics/distribution",
            params=params,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching topic distribution: {e}")
        return None


@st.cache_data(ttl=300)
def fetch_topics_over_time(topic_id=None, country=None, granularity="month", date_from=None, date_to=None):
    """Fetch topics over time."""
    try:
        params = {"granularity": granularity}
        if topic_id is not None:
            params["topic_id"] = topic_id
        if country:
            params["country"] = country
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        
        response = requests.get(
            f"{API_BASE_URL}/api/topics/over-time",
            params=params,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching topics over time: {e}")
        return None


@st.cache_data(ttl=300)
def fetch_topic_statistics(country=None, partisan=None):
    """Fetch topic statistics."""
    try:
        params = {}
        if country:
            params["country"] = country
        if partisan:
            params["partisan"] = partisan
        
        response = requests.get(
            f"{API_BASE_URL}/api/topics/statistics",
            params=params,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching topic statistics: {e}")
        return None


def show_overview_page():
    """Show overview dashboard page."""
    # Fetch enhanced overview and data freshness
    enhanced_overview = fetch_enhanced_overview()
    freshness = fetch_data_freshness()
    overview = enhanced_overview or fetch_overview()  # Fallback to basic overview
    
    # Helper to render KPI inside a card
    def render_kpi(label: str, value: str, subtitle: str = None):
        subtitle_html = f'<div style="font-size:11px; color: var(--color-text-muted); margin-top:4px;">{subtitle}</div>' if subtitle else ""
        st.markdown(
            f"""
            <div style="
                padding: 4px 2px;
                display:flex;
                flex-direction:column;
                gap:6px;
            ">
                <div style="font-size:13px; color: var(--color-text-muted);">{label}</div>
                <div style="font-size:28px; color: var(--color-text); font-weight:600; line-height:1;">{value}</div>
                {subtitle_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Live status
    hero_left, hero_right = st.columns([2.3, 1.2])
    with hero_left:
        st.markdown(
            "<div class='section-title'>Nordic Alternative Media Observatory</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='subtle'>Live monitoring of alternative media signals across the Nordic region, "
            "with searchable historical coverage.</div>",
            unsafe_allow_html=True,
        )
    with hero_right:
        st.markdown(
            "<div class='chip'><span class='pulse'></span> Live intake active</div>",
            unsafe_allow_html=True,
        )
        if freshness:
            freshness_text, last_article_formatted = format_freshness(freshness)
            st.markdown(
                f"<div class='subtle' style='margin-top:8px;'>{freshness_text}<br/>Last article: {last_article_formatted}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div class='subtle' style='margin-top:8px;'>Freshness data unavailable</div>",
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Signal KPIs
    if overview:
        k1, k2, k3, k4, k5 = st.columns(5)
        with k1:
            total_articles = overview.get('total_articles', 0)
            render_kpi("Total Articles", f"{total_articles:,}")
        with k2:
            render_kpi("Outlets", f"{overview.get('total_outlets', 0):,}")
        with k3:
            avg_per_outlet = enhanced_overview.get('avg_articles_per_outlet', 0) if enhanced_overview else 0
            render_kpi("Avg per Outlet", f"{avg_per_outlet:,.0f}", "articles/outlet")
        with k4:
            coverage_years = enhanced_overview.get('coverage_years') if enhanced_overview else None
            if not coverage_years:
                dr = overview.get("date_range", {})
                earliest = dr.get("earliest") or "N/A"
                latest = dr.get("latest") or "N/A"
                coverage_years = f"{earliest[:4]}-{latest[:4]}" if earliest != "N/A" else "N/A"
            coverage_subtitle = f"({total_articles:,} articles)"
            render_kpi("Coverage", f"{coverage_years}", coverage_subtitle)
        with k5:
            growth_rate = enhanced_overview.get('growth_rate_per_year') if enhanced_overview else None
            if growth_rate:
                growth_display = f"+{growth_rate:,.0f}" if growth_rate > 0 else f"{growth_rate:,.0f}"
                render_kpi("Growth Rate", growth_display, "articles/year")
            else:
                render_kpi("Countries", f"{len(overview.get('by_country', {}))}")

    # Fetch overview data
    if not overview:
        st.error("Unable to load data. Please check API connection.")
        st.info(f"Trying to connect to: {API_BASE_URL}")
        return
    
    st.divider()

    # Articles over time - Multi-country comparison with year slider
    st.subheader("Articles Over Time")
    
    # Derive year range from overview (fallback to 2005-2025)
    dr = overview.get("date_range", {}) if overview else {}
    try:
        year_min = int(str(dr.get("earliest"))[:4]) if dr.get("earliest") else 2005
    except Exception:
        year_min = 2005
    try:
        year_max = int(str(dr.get("latest"))[:4]) if dr.get("latest") else 2025
    except Exception:
        year_max = 2025
    if year_min > year_max:
        year_min, year_max = 2005, 2025
    year_from, year_to = st.slider(
        "Year range",
        min_value=year_min,
        max_value=year_max,
        value=(year_min, year_max),
        step=1,
        key="ov_year_range",
    )
    date_from = f"{year_from}-01-01"
    date_to = f"{year_to}-12-31"
    
    # Filters with tooltips
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_country = st.selectbox(
            "Filter by Country",
            options=[None, "denmark", "sweden", "norway", "finland"],
            format_func=lambda x: "All Countries" if x is None else x.capitalize(),
            help="Select a specific Nordic country or view all countries together"
        )
    with col2:
        selected_partisan = st.selectbox(
            "Filter by Partisan",
            options=[None, "Right", "Left", "Other"],
            format_func=lambda x: "All" if x is None else x,
            help="Political orientation of the media outlet (self-identified or classified)"
        )
    with col3:
        granularity = st.selectbox(
            "Time Granularity",
            options=["Year", "Month", "Week"],
            index=0,
            help="Time period grouping for the time series chart (year, month, or week)"
        )
    
    # Show multi-country comparison if no country filter
    if not selected_country:
        # Fetch data for all countries
        fig = go.Figure()
        countries = ["denmark", "sweden", "norway", "finland"]
        # Nordic flag-inspired colors
        colors = {
            'denmark': '#C8102E',    # Danish red (from flag)
            'sweden': '#FECC00',     # Swedish yellow/gold
            'norway': '#87CEEB',     # Light blue (sky blue)
            'finland': '#003580'     # Finnish dark blue (from flag)
        }
        
        for country in countries:
            time_data = fetch_articles_over_time(
                country=country,
                partisan=selected_partisan,
                granularity=granularity.lower(),
                date_from=str(date_from) if date_from else None,
                date_to=str(date_to) if date_to else None
            )
            
            if time_data and time_data.get('data'):
                df_time = pd.DataFrame(time_data['data'])
                df_time['date'] = pd.to_datetime(df_time['date'], errors='coerce')
                df_time = df_time.sort_values('date')
                
                fig.add_trace(go.Scatter(
                    x=df_time['date'],
                    y=df_time['count'],
                    mode='lines+markers',
                    name=country.capitalize(),
                    line=dict(color=colors.get(country, '#808080'), width=2),
                    marker=dict(size=6),
                    hovertemplate=f'<b>{country.capitalize()}</b><br>Date: %{{x}}<br>Articles: %{{y:,}}<extra></extra>'
                ))
        
        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Number of Articles",
            height=450,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                font=dict(size=12)
            ),
            margin=dict(b=50, t=40, l=50, r=50)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        time_data = fetch_articles_over_time(
            country=selected_country,
            partisan=selected_partisan,
            granularity=granularity.lower(),
            date_from=str(date_from) if date_from else None,
            date_to=str(date_to) if date_to else None
        )
        
        if time_data and time_data.get('data'):
            df_time = pd.DataFrame(time_data['data'])
            df_time['date'] = pd.to_datetime(df_time['date'], errors='coerce')
            df_time = df_time.sort_values('date')
            
            fig = px.line(
                df_time,
                x='date',
                y='count',
                markers=True,
                title=f"Articles Over Time - {selected_country.capitalize()} ({granularity.capitalize()})"
            )
            fig.update_traces(
                line=dict(width=3),
                marker=dict(size=8),
                hovertemplate='<b>Date:</b> %{x}<br><b>Articles:</b> %{y:,}<extra></extra>'
            )
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Number of Articles",
                height=450,
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available for selected filters.")
    



def show_topic_analysis_page():
    """Show dedicated topic analysis page."""
    st.markdown('<h1 class="main-header">Dataset</h1>', unsafe_allow_html=True)

    overview = fetch_enhanced_overview() or fetch_overview()
    if overview:
        st.markdown("<div class='section-title'>Coverage overview</div>", unsafe_allow_html=True)
        with st.container():
            country_data = pd.DataFrame(
                list(overview['by_country'].items()),
                columns=['Country', 'Articles']
            ).sort_values('Articles', ascending=True)

            partisan_raw = pd.DataFrame(
                list(overview.get('by_partisan', {}).items()),
                columns=['Partisan', 'Articles']
            )
            if len(partisan_raw) > 0:
                partisan_data = partisan_raw.copy()
                partisan_data['Partisan'] = partisan_data['Partisan'].str.strip().str.title()
                partisan_data = partisan_data.sort_values('Articles', ascending=False)
            else:
                partisan_data = partisan_raw

            left, right = st.columns([1.4, 1])
            with left:
                st.markdown("**Articles by country**")
                fig = px.bar(
                    country_data,
                    x="Articles",
                    y="Country",
                    orientation="h",
                    color_discrete_sequence=["#1f77b4"],
                    text="Articles",
                )
                fig.update_traces(texttemplate="%{text:,}", textposition="outside")
                fig.update_layout(
                    height=320,
                    margin=dict(l=10, r=10, t=10, b=10),
                    xaxis_title="Articles",
                    yaxis_title="",
                )
                st.plotly_chart(fig, use_container_width=True)
            with right:
                st.markdown("**Partisan distribution**")
                if len(partisan_data) > 0:
                    color_map = {
                        'Right': '#0066CC',
                        'Left': '#DC143C',
                        'Other': '#2ca02c'
                    }
                    category_order = ["Right", "Left", "Other"]
                    partisan_data_sorted = partisan_data.copy()
                    partisan_data_sorted['Partisan'] = pd.Categorical(
                        partisan_data_sorted['Partisan'],
                        categories=category_order,
                        ordered=True
                    )
                    partisan_data_sorted = partisan_data_sorted.sort_values('Partisan')
                    colors_list = [color_map.get(str(name), '#808080') for name in partisan_data_sorted['Partisan'].values]

                    fig = go.Figure(data=[go.Pie(
                        labels=partisan_data_sorted['Partisan'].values,
                        values=partisan_data_sorted['Articles'].values,
                        hole=0.45,
                        marker=dict(colors=colors_list, line=dict(color='white', width=2)),
                        textinfo='none',
                        hovertemplate='<b>%{label}</b><br>Articles: %{value:,}<br>Percentage: %{percent}<extra></extra>'
                    )])
                    fig.update_layout(
                        height=320,
                        margin=dict(l=10, r=10, t=10, b=10),
                        showlegend=True,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=-0.2,
                            xanchor="center",
                            x=0.5,
                            font=dict(size=12)
                        )
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No partisan data.")

            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            card_left, card_right = st.columns(2)
            with card_left:
                st.markdown("**Live ingest**")
                st.markdown(
                    """
                    <div style="
                        background: var(--color-card);
                        border: 1px solid var(--color-border);
                        border-radius: var(--radius);
                        box-shadow: var(--shadow-soft);
                        padding: 14px;
                        min-height: 180px;
                        display:flex;
                        flex-direction:column;
                        gap:8px;
                        justify-content:space-between;
                    ">
                        <div style="font-size:13px; color: var(--color-text-muted);">
                            Wiring to full DB soon. Will show last run, delta, and per-country freshness.
                        </div>
                        <div style="font-size:13px; color: var(--color-text-muted);">
                            • Last run: placeholder<br/>
                            • +1.8k articles (14d)<br/>
                            • Per-country freshness dots
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with card_right:
                comparative = fetch_comparative_metrics()
                st.markdown("**Media diversity**")

                percentages_html = ""
                if comparative:
                    countries_order = ["denmark", "sweden", "norway", "finland"]
                    for country in countries_order:
                        country_data = comparative.get(country, {})
                        concentration = country_data.get("outlet_concentration", 0)
                        percentages_html += f"<div style='margin-bottom: 8px;'><strong>{country.capitalize()}:</strong> {concentration}%</div>"
                else:
                    overall_conc = fetch_outlet_concentration()
                    if overall_conc:
                        concentration = overall_conc.get('concentration_percentage', 0)
                        percentages_html = f"<div style='margin-bottom: 8px;'><strong>Overall:</strong> {concentration}%</div>"
                    else:
                        percentages_html = "<div style='margin-bottom: 8px;'>Data unavailable</div>"

                st.markdown(
                    f"""
                    <div style="
                        background: var(--color-card);
                        border: 1px solid var(--color-border);
                        border-radius: var(--radius);
                        box-shadow: var(--shadow-soft);
                        padding: 14px;
                        min-height: 180px;
                        display:flex;
                        flex-direction:column;
                        gap:8px;
                        justify-content:space-between;
                    ">
                        <div style="font-size:13px; color: var(--color-text-muted); line-height:1.5; margin-bottom: 12px;">
                            Percentage of articles published by the top 3 outlets in each country.
                        </div>
                        <div style="font-size:14px; color: var(--color-text);">
                            {percentages_html}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.divider()
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        selected_country = st.selectbox(
            "Filter by Country",
            options=[None, "denmark", "sweden", "norway", "finland"],
            format_func=lambda x: "All Countries" if x is None else x.capitalize(),
            key="dataset_country_filter",
            help="Select a specific Nordic country or view all countries together",
        )
    with col2:
        selected_partisan = st.selectbox(
            "Filter by Partisan",
            options=[None, "Right", "Left", "Other"],
            format_func=lambda x: "All" if x is None else x,
            key="dataset_partisan_filter",
            help="Political orientation of the media outlet (self-identified or classified)",
        )

    # Category distribution
    st.subheader("News Categories")
    st.caption("News categories are based on automated content analysis using mistralai/Mistral-Small-24B-Instruct-2501 on content level")
    col1, col2 = st.columns([2, 1])

    with col1:
        categories_data = fetch_categories(country=selected_country, partisan=selected_partisan)
        if categories_data and categories_data.get('data'):
            df_cat = pd.DataFrame(categories_data['data'])
            df_cat = df_cat.sort_values('count', ascending=False)

            def format_category_name(name):
                name = name.replace(' & ', ' &<br>')
                parts = name.split('<br>')
                result_parts = []

                for part in parts:
                    if len(part) > 18:
                        words = part.split()
                        if len(words) >= 3:
                            if ', ' in part:
                                subparts = part.split(', ')
                                if len(subparts) == 2:
                                    part = subparts[0] + ',<br>' + subparts[1]
                                else:
                                    mid = len(subparts) // 2
                                    part = ',<br>'.join(subparts[:mid]) + ',<br>' + ',<br>'.join(subparts[mid:])
                            else:
                                if len(words) <= 4:
                                    mid = len(words) // 2
                                    part = ' '.join(words[:mid]) + '<br>' + ' '.join(words[mid:])
                                else:
                                    third = len(words) // 3
                                    part = ' '.join(words[:third]) + '<br>' + ' '.join(words[third:2*third]) + '<br>' + ' '.join(words[2*third:])
                    result_parts.append(part)

                return '<br>'.join(result_parts)

            df_cat_display = df_cat.copy()
            df_cat_display['category_display'] = df_cat_display['category'].apply(format_category_name)

            fig = px.bar(
                df_cat,
                x='category',
                y='count',
                color='count',
                text='count',
                color_continuous_scale='Blues',
                title="Article Distribution by Category",
            )

            fig.update_xaxes(
                ticktext=df_cat_display['category_display'].values,
                tickvals=df_cat['category'].values,
                tickangle=0,
                tickfont={'size': 10},
                categoryorder='total descending',
            )

            fig.update_traces(
                texttemplate='%{text:,}',
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>Articles: %{y:,}<extra></extra>',
            )

            fig.update_layout(
                xaxis_title="Category",
                yaxis_title="Number of Articles",
                height=480,
                margin=dict(b=150, t=100, l=50, r=50),
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No category data available.")

    with col2:
        if categories_data and categories_data.get('data'):
            df_cat_table = df_cat[['category', 'count']].copy()
            st.dataframe(
                df_cat_table.style.format({'count': '{:,}'}),
                use_container_width=True,
                hide_index=True,
            )

    st.divider()

def show_country_page():
    """Show country-specific analysis page."""
    st.markdown('<h1 class="main-header">First Stop: The Overview</h1>', unsafe_allow_html=True)
    st.markdown(
        "<div class='subtle'>The Explorer provides a high-level overview of the dataset. "
        "Start with all countries for a broad comparison, or select a country to see outlets and "
        "publishing activity over time. Adjust filters to narrow the view.</div>",
        unsafe_allow_html=True,
    )
    overview = fetch_overview()
    
    # Country selector
    default_country = st.session_state.get("quick_country")
    country_options = [None, "denmark", "sweden", "norway", "finland"]
    country_labels = {
        None: "All Countries",
        "denmark": "Denmark",
        "sweden": "Sweden",
        "norway": "Norway",
        "finland": "Finland",
    }
    country = st.selectbox(
        "Scope",
        options=country_options,
        index=country_options.index(default_country) if default_country in country_options else 0,
        format_func=lambda x: country_labels.get(x, "All Countries"),
        help="Select a Nordic country or view all countries"
    )
    st.session_state["quick_country"] = country
    
    st.divider()

    colors = {
        'denmark': '#C8102E',
        'sweden': '#FECC00',
        'norway': '#87CEEB',
        'finland': '#003580'
    }

    tables_col1, tables_col2 = st.columns(2)
    with tables_col1:
        # All outlets for country
        heading = "Outlets (All Countries)" if not country else f"Outlets ({country.capitalize()})"
        st.subheader(heading)
        outlets_data = fetch_top_outlets(country=country, limit=1000)  # Get all outlets

        if outlets_data and outlets_data.get('data'):
            df_outlets = pd.DataFrame(consolidate_outlets(outlets_data['data']))
            recent_data = fetch_top_outlets(
                country=country,
                limit=1000,
                date_from="2025-01-01",
                date_to="2026-12-31"
            )
            recent = pd.DataFrame(consolidate_outlets(recent_data.get("data", []))) if recent_data else pd.DataFrame()
            recent_counts = {}
            if not recent.empty:
                recent_counts = dict(zip(recent["domain"], recent["count"]))
            df_outlets["count_2025_26"] = df_outlets["domain"].map(recent_counts).fillna(0).astype(int)
            df_outlets = df_outlets.rename(columns={"count": "total_count"})
            st.dataframe(
                df_outlets[['domain', 'partisan', 'total_count', 'count_2025_26']].style.format({
                    'total_count': '{:,}',
                    'count_2025_26': '{:,}'
                }),
                use_container_width=True,
                hide_index=True,
                column_config={
                    'domain': 'Domain',
                    'partisan': 'Partisanship',
                    'total_count': 'Total Count',
                    'count_2025_26': 'Count (2025-26)'
                }
            )

    with tables_col2:
        category_heading = "News Categories (All Countries)" if not country else f"News Categories ({country.capitalize()})"
        st.subheader(
            category_heading,
            help="Content has been classified by an LLM to predefined news categories.",
        )
        categories_data = fetch_categories(country=country, partisan=None)
        if categories_data and categories_data.get('data'):
            df_cat = pd.DataFrame(categories_data['data'])
            df_cat = df_cat.sort_values('count', ascending=False).head(10)

            total = df_cat['count'].sum()
            df_cat['percentage'] = (df_cat['count'] / total * 100).round(1)

            st.dataframe(
                df_cat[['category', 'count', 'percentage']].style.format({
                    'count': '{:,}',
                    'percentage': '{:.1f}%'
                }),
                use_container_width=True,
                hide_index=True,
                column_config={
                    'category': 'Category',
                    'count': 'Articles',
                    'percentage': 'Percentage'
                }
            )

    if not country:
        conc_col, partisan_col = st.columns(2)
        with conc_col:
            st.subheader("Outlet Concentration")
            st.caption("Share of total articles produced by the top 5 outlets in each country (higher = more concentrated).")
            concentration_rows = []
            countries = ["denmark", "sweden", "norway", "finland"]
            country_colors = {
                "Denmark": "#C8102E",
                "Sweden": "#FECC00",
                "Norway": "#87CEEB",
                "Finland": "#003580",
            }
            for ctry in countries:
                outlets_for_country = fetch_top_outlets(country=ctry, limit=1000)
                if outlets_for_country and outlets_for_country.get("data"):
                    consolidated = consolidate_outlets(outlets_for_country["data"])
                    share = compute_top_n_share(consolidated, n=5)
                    concentration_rows.append(
                        {"country": ctry.capitalize(), "top5_share": share * 100}
                    )
            if concentration_rows:
                df_concentration = pd.DataFrame(concentration_rows)
                fig_concentration = go.Figure(
                    data=[
                        go.Pie(
                            labels=df_concentration["country"],
                            values=df_concentration["top5_share"],
                            hole=0.45,
                            marker=dict(
                                colors=[
                                    country_colors.get(country, "#1f77b4")
                                    for country in df_concentration["country"]
                                ]
                            ),
                            textinfo="label+percent",
                            textposition="outside",
                            textfont=dict(size=12),
                            pull=[0.03] * len(df_concentration),
                            hovertemplate="<b>%{label}</b><br>Top 5 Share: %{value:.1f}%<extra></extra>",
                        )
                    ]
                )
                fig_concentration.update_layout(
                    height=360,
                    showlegend=False,
                )
                st.plotly_chart(fig_concentration, use_container_width=True)

        with partisan_col:
            st.subheader("Partisanship Mix by Country")
            st.caption(
                "Share of total articles by partisan group within each country. "
                "Higher shares indicate stronger dominance of a partisan orientation."
            )
            partisan_rows = []
            for ctry in ["denmark", "sweden", "norway", "finland"]:
                outlets_for_country = fetch_top_outlets(country=ctry, limit=1000)
                if outlets_for_country and outlets_for_country.get("data"):
                    consolidated = consolidate_outlets(outlets_for_country["data"])
                    shares = compute_partisan_shares(consolidated)
                    for partisan, share in shares.items():
                        partisan_rows.append(
                            {
                                "country": ctry.capitalize(),
                                "partisan": partisan,
                                "share": share * 100,
                            }
                        )
            if partisan_rows:
                df_partisan = pd.DataFrame(partisan_rows)
                fig_partisan = px.bar(
                    df_partisan,
                    x="country",
                    y="share",
                    color="partisan",
                    text=df_partisan["share"].map(lambda x: f"{x:.1f}%"),
                    color_discrete_map={
                        "Right": "#0066CC",
                        "Left": "#DC143C",
                        "Other": "#2ca02c",
                    },
                )
                fig_partisan.update_traces(
                    textposition="inside",
                    hovertemplate="<b>%{x}</b><br>%{legendgroup}: %{y:.1f}%<extra></extra>",
                )
                fig_partisan.update_layout(
                    yaxis_title="Share of Articles (%)",
                    xaxis_title="",
                    height=360,
                    yaxis=dict(range=[0, 100]),
                    barmode="stack",
                    legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),
                    legend_title_text=None,
                    margin=dict(b=80),
                )
                st.plotly_chart(fig_partisan, use_container_width=True)

    # Articles over time for country
    over_time_title = "Articles Over Time (All Countries)" if not country else f"Articles Over Time ({country.capitalize()})"
    st.subheader(over_time_title)

    partisan_filter = None
    if not country:
        dr = overview.get("date_range", {}) if overview else {}
        try:
            year_min = int(str(dr.get("earliest"))[:4]) if dr.get("earliest") else 2005
        except Exception:
            year_min = 2005
        try:
            year_max = int(str(dr.get("latest"))[:4]) if dr.get("latest") else 2025
        except Exception:
            year_max = 2025
        if year_min > year_max:
            year_min, year_max = 2005, 2025
        year_from, year_to = st.slider(
            "Year range",
            min_value=year_min,
            max_value=year_max,
            value=(year_min, year_max),
            step=1,
            key="country_year_range",
        )
        date_from = f"{year_from}-01-01"
        date_to = f"{year_to}-12-31"

        col1, col2 = st.columns(2)
        with col1:
            granularity = st.selectbox(
                "Time Granularity",
                options=["Year", "Month", "Week"],
                index=0,
                key="country_granularity_all",
                help="Time period grouping for the time series chart (year, month, or week)"
            )
        with col2:
            partisan_filter = st.selectbox(
                "Filter by Partisan",
                options=[None, "Right", "Left", "Other"],
                format_func=lambda x: "All" if x is None else x,
                key="country_partisan_all",
                help="Political orientation of the media outlet (self-identified or classified)"
            )

        fig = go.Figure()
        countries = ["denmark", "sweden", "norway", "finland"]

        for ctry in countries:
            time_data = fetch_articles_over_time(
                country=ctry,
                partisan=partisan_filter,
                granularity=granularity.lower(),
                date_from=str(date_from) if date_from else None,
                date_to=str(date_to) if date_to else None
            )
            if time_data and time_data.get('data'):
                df_time = pd.DataFrame(time_data['data'])
                df_time['date'] = pd.to_datetime(df_time['date'], errors='coerce')
                df_time = df_time.sort_values('date')
                fig.add_trace(go.Scatter(
                    x=df_time['date'],
                    y=df_time['count'],
                    mode='lines+markers',
                    name=ctry.capitalize(),
                    line=dict(color=colors.get(ctry, '#1f77b4'), width=2),
                    marker=dict(size=6),
                    hovertemplate=f"<b>{ctry.capitalize()}</b><br>Date: %{{x}}<br>Articles: %{{y:,}}<extra></extra>"
                ))

        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Number of Articles",
            height=450,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.12,
                xanchor="center",
                x=0.5
            )
        )
        st.plotly_chart(fig, use_container_width=True)

        share_col, lorenz_col = st.columns(2)
        with share_col:
            st.subheader("Category Mix Over Time")
            category_data = fetch_categories_over_time(
                country=None,
                partisan=partisan_filter,
                granularity=granularity.lower(),
                date_from=str(date_from) if date_from else None,
                date_to=str(date_to) if date_to else None,
                limit=6,
            )
            if category_data and category_data.get("data"):
                df_category = pd.DataFrame(category_data["data"])
                df_category["date"] = pd.to_datetime(df_category["date"], errors="coerce")
                df_category = df_category.sort_values("date")
                totals = df_category.groupby("date")["count"].transform("sum")
                df_category["share"] = df_category["count"] / totals * 100
                fig_category = go.Figure()
                for category in df_category["category"].unique():
                    df_cat = df_category[df_category["category"] == category]
                    fig_category.add_trace(go.Scatter(
                        x=df_cat["date"],
                        y=df_cat["share"],
                        stackgroup="one",
                        name=category,
                        hovertemplate="<b>%{fullData.name}</b><br>Date: %{x}<br>Share: %{y:.1f}%<extra></extra>",
                    ))
                fig_category.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Share of Articles (%)",
                    height=450,
                    hovermode="x unified",
                    legend=dict(orientation="h", yanchor="bottom", y=1.12, xanchor="center", x=0.5),
                    yaxis=dict(range=[0, 100]),
                )
                st.plotly_chart(fig_category, use_container_width=True)
            else:
                st.info("No category trend data available for this selection.")

        with lorenz_col:
            st.subheader("Outlet Concentration Curve")
            st.caption("Lorenz curve of article production per outlet (more bowed = more concentrated).")
            lorenz_fig = go.Figure()
            for ctry in ["denmark", "sweden", "norway", "finland"]:
                outlets_for_country = fetch_top_outlets(country=ctry, limit=1000)
                if outlets_for_country and outlets_for_country.get("data"):
                    consolidated = consolidate_outlets(outlets_for_country["data"])
                    counts = [row.get("count", 0) for row in consolidated]
                    x_vals, y_vals, gini = compute_lorenz_curve(counts)
                    lorenz_fig.add_trace(go.Scatter(
                        x=x_vals,
                        y=y_vals,
                        mode="lines",
                        name=f"{ctry.capitalize()} (Gini {gini:.2f})",
                        line=dict(color=colors.get(ctry, "#1f77b4"), width=2),
                        hovertemplate="Outlets: %{x:.0%}<br>Articles: %{y:.0%}<extra></extra>"
                    ))
            lorenz_fig.add_trace(go.Scatter(
                x=[0, 1],
                y=[0, 1],
                mode="lines",
                name="Equality",
                line=dict(color="#999999", width=1, dash="dash"),
                hoverinfo="skip",
            ))
            lorenz_fig.update_layout(
                xaxis_title="Share of Outlets",
                yaxis_title="Share of Articles",
                height=450,
                yaxis=dict(range=[0, 1]),
                xaxis=dict(range=[0, 1]),
                legend=dict(orientation="h", yanchor="bottom", y=1.08, xanchor="center", x=0.5),
            )
            st.plotly_chart(lorenz_fig, use_container_width=True)
    else:
        # View type selector (single-country)
        view_type = st.radio(
            "View",
            options=["Total Count", "Separate Outlets", "Partisan Accumulated"],
            index=0,
            horizontal=True,
            key="country_view_type",
            help="Choose how to display articles over time: total count (aggregate), individual outlets, or grouped by partisan"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            granularity = st.selectbox(
                "Time Granularity",
                options=["Year", "Month", "Week"],
                index=0,
                key="country_granularity",
                help="Time period grouping for the time series chart (year, month, or week)"
            )
        with col2:
            if view_type == "Separate Outlets":
                outlets_list = fetch_top_outlets(country=country, limit=20)
                if outlets_list and outlets_list.get('data'):
                    outlet_options = [o['domain'] for o in outlets_list['data']]
                    selected_outlets = st.multiselect(
                        "Select Outlets",
                        options=outlet_options,
                        default=outlet_options[:5] if len(outlet_options) >= 5 else outlet_options,
                        key="country_selected_outlets",
                        help="Select outlets to display (shows top 5 by default)"
                    )
                else:
                    selected_outlets = []
                partisan_filter = None
            else:
                partisan_filter = st.selectbox(
                    "Filter by Partisan",
                    options=[None, "Right", "Left", "Other"],
                    format_func=lambda x: "All" if x is None else x,
                    key="country_partisan",
                    help="Political orientation of the media outlet (self-identified or classified)"
                )
                selected_outlets = []
        
        # Fetch and display data based on view type
        if view_type == "Total Count":
            time_data = fetch_articles_over_time(
                country=country,
                partisan=partisan_filter,
                granularity=granularity.lower()
            )
            
            if time_data and time_data.get('data'):
                df_time = pd.DataFrame(time_data['data'])
                df_time['date'] = pd.to_datetime(df_time['date'], errors='coerce')
                df_time = df_time.sort_values('date')
                
                title_country = country.capitalize() if country else "All Countries"
                fig = px.line(
                    df_time,
                    x='date',
                    y='count',
                    markers=True,
                    title=f"Articles Over Time - {title_country} (Total Count)"
                )
                fig.update_traces(
                    line=dict(width=3, color='#1f77b4'),
                    marker=dict(size=8),
                    hovertemplate='<b>Date:</b> %{x}<br><b>Articles:</b> %{y:,}<extra></extra>'
                )
                fig.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Number of Articles",
                    height=400,
                    hovermode='x unified'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        elif view_type == "Separate Outlets":
            if selected_outlets:
                outlet_time_data = fetch_articles_over_time_by_outlet(
                    country=country,
                    outlets=selected_outlets,
                    granularity=granularity.lower()
                )
                
                if outlet_time_data and outlet_time_data.get('data'):
                    fig = go.Figure()
                    colors_list = px.colors.qualitative.Set3
                    
                    for idx, outlet in enumerate(selected_outlets):
                        if outlet in outlet_time_data['data']:
                            outlet_series = outlet_time_data['data'][outlet]
                            df_outlet = pd.DataFrame(outlet_series)
                            df_outlet['date'] = pd.to_datetime(df_outlet['date'], errors='coerce')
                            df_outlet = df_outlet.sort_values('date')
                            
                            color = colors_list[idx % len(colors_list)]
                            fig.add_trace(go.Scatter(
                                x=df_outlet['date'],
                                y=df_outlet['count'],
                                mode='lines+markers',
                                name=outlet,
                                line=dict(color=color, width=2),
                                marker=dict(size=6),
                                hovertemplate=f'<b>{outlet}</b><br>Date: %{{x}}<br>Articles: %{{y:,}}<extra></extra>'
                            ))
                    
                    fig.update_layout(
                        title=f"Articles Over Time - {country.capitalize()} (By Outlet)",
                        xaxis_title="Date",
                        yaxis_title="Number of Articles",
                        height=400,
                        hovermode='x unified',
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No data available for selected outlets.")
            else:
                st.info("Please select at least one outlet to display.")
        
        elif view_type == "Partisan Accumulated":
            fig = go.Figure()
            partisan_colors = {'Right': '#0066CC', 'Left': '#DC143C', 'Other': '#2ca02c'}
            
            for partisan in ['Right', 'Left', 'Other']:
                time_data = fetch_articles_over_time(
                    country=country,
                    partisan=partisan,
                    granularity=granularity.lower()
                )
                
                if time_data and time_data.get('data'):
                    df_time = pd.DataFrame(time_data['data'])
                    df_time['date'] = pd.to_datetime(df_time['date'], errors='coerce')
                    df_time = df_time.sort_values('date')
                    
                    fig.add_trace(go.Scatter(
                        x=df_time['date'],
                        y=df_time['count'],
                        mode='lines+markers',
                        name=partisan,
                        line=dict(color=partisan_colors[partisan], width=3),
                        marker=dict(size=8),
                        hovertemplate=f'<b>{partisan}</b><br>Date: %{{x}}<br>Articles: %{{y:,}}<extra></extra>'
                    ))
            
            title_country = country.capitalize() if country else "All Countries"
            fig.update_layout(
                title=f"Articles Over Time - {title_country} (By Partisan)",
                xaxis_title="Date",
                yaxis_title="Number of Articles",
                height=400,
                hovermode='x unified',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Categories moved next to outlets table above.


def show_content_engagement_page():
    """Show content engagement / deep dive page."""
    
    st.markdown('<h1 class="main-header">Dataset</h1>', unsafe_allow_html=True)
    
    # Get the latest article date from overview to use as "today"
    overview = fetch_overview()
    latest_article_date = None
    earliest_article_date = None
    if overview and overview.get('date_range', {}):
        if overview['date_range'].get('latest'):
            try:
                latest_article_date = datetime.fromisoformat(overview['date_range']['latest'][:10]).date()
            except Exception:
                pass
        if overview['date_range'].get('earliest'):
            try:
                earliest_article_date = datetime.fromisoformat(overview['date_range']['earliest'][:10]).date()
            except Exception:
                pass
    
    # Use latest article date as "today" (not system date)
    if latest_article_date:
        today = latest_article_date
    else:
        # Fallback to current date if no data available, but cap at reasonable date
        today = datetime.now().date()
        # If system date seems wrong (future), use a reasonable fallback
        if today.year > 2025 or (today.year == 2025 and today.month > 9):
            today = datetime(2025, 9, 8).date()  # Use latest known article date
    
    # Initialize session state for expanded articles
    if "expanded_articles" not in st.session_state:
        st.session_state.expanded_articles = set()
    if "bookmarked_articles" not in st.session_state:
        st.session_state.bookmarked_articles = set()
    if "date_range_preset" not in st.session_state:
        st.session_state.date_range_preset = "2 months"
    
    # Search section
    search_query = st.text_input(
        "Search articles by keyword",
        placeholder="Search in titles and descriptions...",
        help="Search for keywords in article titles and descriptions"
    )
    
    # Date range selection with presets
    st.subheader("Date Range")
    preset_col1, preset_col2 = st.columns([2, 1])
    
    with preset_col1:
        date_preset = st.selectbox(
            "Time period",
            options=["Last week", "Last month", "Last 2 months", "Last 6 months", "Last year", "Custom range"],
            index=2,  # Default to "Last 2 months"
            help="Select a preset time period or choose custom range"
        )
    
    # Calculate date range based on preset
    if date_preset == "Last week":
        date_from = today - timedelta(days=7)
    elif date_preset == "Last month":
        date_from = today - timedelta(days=30)
    elif date_preset == "Last 2 months":
        date_from = today - timedelta(days=60)
    elif date_preset == "Last 6 months":
        date_from = today - timedelta(days=180)
    elif date_preset == "Last year":
        date_from = today - timedelta(days=365)
    else:  # Custom range
        date_col1, date_col2 = st.columns(2)
        with date_col1:
            date_from = st.date_input(
                "From",
                value=today - timedelta(days=60),
                max_value=today,
                min_value=earliest_article_date if earliest_article_date else datetime(2000, 1, 1).date()
            )
        with date_col2:
            date_to = st.date_input(
                "To",
                value=today,
                max_value=today,
                min_value=date_from
            )
        date_from_str = date_from.isoformat()
        date_to_str = date_to.isoformat()
        st.info(f"Showing articles from {date_from_str} to {date_to_str}")
    
    # For presets, set date_to to today (latest article date)
    if date_preset != "Custom range":
        date_to = today
        # Ensure date_from doesn't go before earliest article
        if earliest_article_date and date_from < earliest_article_date:
            date_from = earliest_article_date
        date_from_str = date_from.isoformat()
        date_to_str = date_to.isoformat()
        st.info(f"Showing articles from {date_from_str} to {date_to_str} ({date_preset.lower()})")
    
    # Quick filters
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        filter_country = st.selectbox(
            "Country",
            options=[None, "denmark", "sweden", "norway", "finland"],
            format_func=lambda x: "All Countries" if x is None else x.capitalize(),
            help="Filter by Nordic country"
        )
    with filter_col2:
        filter_partisan = st.selectbox(
            "Partisan",
            options=[None, "Right", "Left", "Other"],
            format_func=lambda x: "All" if x is None else x,
            help="Political orientation of the media outlet"
        )
    with filter_col3:
        filter_sentiment = st.selectbox(
            "Sentiment",
            options=[None, "positive", "neutral", "negative"],
            format_func=lambda x: "All" if x is None else x.capitalize(),
            help="Emotional tone of the article"
        )
    
    # Advanced filters in sidebar
    with st.sidebar:
        st.header("Advanced Filters")
        
        # Get available categories for filter
        categories_data = fetch_categories()
        available_categories = []
        if categories_data and categories_data.get('data'):
            available_categories = [item['category'] for item in categories_data['data']]
        
        selected_categories = st.multiselect(
            "Categories",
            options=available_categories[:20],  # Limit to top 20
            help="Select one or more categories"
        )
        
        entity_search = st.text_input(
            "Entities mentioned",
            placeholder="Search for person, location, or organization...",
            help="Search for specific entities mentioned in articles"
        )
        selected_entities = [entity_search] if entity_search else None
        
        # Get available outlets
        outlets_data = fetch_top_outlets(limit=50)
        available_outlets = []
        if outlets_data and outlets_data.get('data'):
            available_outlets = [item['domain'] for item in outlets_data['data']]
        
        selected_outlets = st.multiselect(
            "Outlets",
            options=available_outlets,
            help="Select specific media outlets"
        )
        
        st.divider()
        
        # Export section
        st.header("Export Options")
        export_format = st.radio(
            "Format",
            options=["CSV", "JSON"],
            help="Choose export format"
        )
    
    # Pagination
    if "article_page" not in st.session_state:
        st.session_state.article_page = 0
    
    articles_per_page = 20
    offset = st.session_state.article_page * articles_per_page
    
    # Search articles
    search_results = fetch_articles(
        query=search_query if search_query else None,
        date_from=date_from_str,
        date_to=date_to_str,
        country=filter_country,
        partisan=filter_partisan,
        sentiment=filter_sentiment,
        categories=selected_categories if selected_categories else None,
        entities=selected_entities,
        outlets=selected_outlets if selected_outlets else None,
        limit=articles_per_page,
        offset=offset
    )
    
    if not search_results:
        st.warning("Unable to load articles. Please check API connection.")
        return
    
    total_articles = search_results.get('total', 0)
    articles = search_results.get('articles', [])
    
    # Display results header
    st.markdown(f"### Showing {len(articles)} of {total_articles:,} articles")
    
    if total_articles == 0:
        st.info("No articles found matching your criteria. Try adjusting your filters.")
        return
    
    # Display articles
    for article in articles:
        article_id = article.get('id')
        is_expanded = article_id in st.session_state.expanded_articles
        is_bookmarked = article_id in st.session_state.bookmarked_articles
        
        # Article card
        with st.container():
            # Card header
            header_col1, header_col2 = st.columns([4, 1])
            with header_col1:
                st.markdown(f"#### {article.get('title', 'No title')}")
            with header_col2:
                bookmark_label = "Unbookmark" if is_bookmarked else "Bookmark"
                if st.button(bookmark_label, key=f"bookmark_{article_id}", help="Bookmark this article"):
                    if is_bookmarked:
                        st.session_state.bookmarked_articles.discard(article_id)
                    else:
                        st.session_state.bookmarked_articles.add(article_id)
                    st.rerun()
            
            # Article metadata
            metadata_parts = []
            if article.get('domain'):
                metadata_parts.append(f"**{article.get('domain')}**")
            if article.get('country'):
                metadata_parts.append(f"{article.get('country').capitalize()}")
            if article.get('partisan'):
                metadata_parts.append(f"{article.get('partisan')}")
            if article.get('date'):
                try:
                    article_date = datetime.fromisoformat(article.get('date')[:10])
                    days_ago = (today - article_date.date()).days
                    if days_ago == 0:
                        date_str = "Today"
                    elif days_ago == 1:
                        date_str = "Yesterday"
                    elif days_ago < 7:
                        date_str = f"{days_ago} days ago"
                    elif days_ago < 30:
                        date_str = f"{days_ago // 7} weeks ago"
                    else:
                        date_str = article.get('date')[:10]
                    metadata_parts.append(f"{date_str}")
                except Exception:
                    metadata_parts.append(f"{article.get('date')[:10]}")
            
            st.markdown(" • ".join(metadata_parts))
            
            # Article preview
            description = article.get('description', '')
            content = article.get('content', '')
            preview_text = description if description else (content[:200] + "..." if len(content) > 200 else content)
            
            if is_expanded:
                # Show full content
                st.markdown(f"**Description:** {description}")
                if content:
                    st.markdown("**Content:**")
                    st.markdown(content)
            else:
                # Show preview
                st.markdown(preview_text)
            
            # Article metadata badges
            badge_col1, badge_col2, badge_col3 = st.columns(3)
            with badge_col1:
                if article.get('categories'):
                    categories_str = ", ".join(article.get('categories', [])[:3])
                    st.markdown(f"**Categories:** {categories_str}")
            with badge_col2:
                sentiment = article.get('sentiment', '')
                sentiment_score = article.get('sentiment_score', 0)
                if sentiment:
                    st.markdown(f"**Sentiment:** {sentiment.capitalize()} ({sentiment_score:.2f})")
            with badge_col3:
                entities = article.get('entities', {})
                entity_count = sum(len(v) if isinstance(v, list) else 0 for v in entities.values())
                if entity_count > 0:
                    st.markdown(f"**Entities:** {entity_count} mentioned")
            
            # Action buttons - all styled consistently
            button_col1, button_col2, button_col3, button_col4 = st.columns(4)
            with button_col1:
                if st.button("Read Full" if not is_expanded else "Collapse", key=f"expand_{article_id}", use_container_width=True):
                    if is_expanded:
                        st.session_state.expanded_articles.discard(article_id)
                    else:
                        st.session_state.expanded_articles.add(article_id)
                    st.rerun()
            with button_col2:
                article_url = article.get('url', '')
                if article_url:
                    # Use link_button which has consistent styling with st.button
                    st.link_button("View Source", article_url, use_container_width=True)
            with button_col3:
                # Share functionality - button that copies to clipboard
                article_url = article.get('url', '')
                share_text = f"{article.get('title', '')} - {article_url}"
                share_clicked = st.button("Share", key=f"share_btn_{article_id}", use_container_width=True)
                if share_clicked:
                    # Copy to clipboard using JavaScript
                    st.markdown(f"""
                        <script>
                        (function() {{
                            const text = {repr(share_text)};
                            if (navigator.clipboard && navigator.clipboard.writeText) {{
                                navigator.clipboard.writeText(text);
                            }}
                        }})();
                        </script>
                    """, unsafe_allow_html=True)
                    st.success("✓ Link copied to clipboard!")
            with button_col4:
                # Related articles button
                if st.button("Related", key=f"related_{article_id}", use_container_width=True):
                    st.session_state[f"show_related_{article_id}"] = True
            
            # Show related articles if requested
            if st.session_state.get(f"show_related_{article_id}", False):
                st.markdown("---")
                st.markdown("#### Related Articles")
                related = fetch_related_articles(article_id, limit=5)
                if related and related.get('articles'):
                    for related_article in related['articles']:
                        st.markdown(f"- [{related_article.get('title', 'No title')}]({related_article.get('url', '#')}) ({related_article.get('date', '')[:10]})")
                else:
                    st.info("No related articles found.")
                if st.button("Close", key=f"close_related_{article_id}"):
                    st.session_state[f"show_related_{article_id}"] = False
                    st.rerun()
            
            st.divider()
    
    # Pagination controls
    total_pages = (total_articles + articles_per_page - 1) // articles_per_page
    if total_pages > 1:
        pagination_col1, pagination_col2, pagination_col3 = st.columns([1, 2, 1])
        with pagination_col1:
            if st.button("◀ Previous", disabled=st.session_state.article_page == 0):
                st.session_state.article_page -= 1
                st.rerun()
        with pagination_col2:
            st.markdown(f"**Page {st.session_state.article_page + 1} of {total_pages}**")
        with pagination_col3:
            if st.button("Next ▶", disabled=st.session_state.article_page >= total_pages - 1):
                st.session_state.article_page += 1
                st.rerun()
    
    # Export functionality
    st.sidebar.divider()
    if st.sidebar.button("Export Results", use_container_width=True):
        # Prepare export data
        export_data = []
        for article in articles:
            export_data.append({
                "id": article.get('id'),
                "title": article.get('title', ''),
                "url": article.get('url', ''),
                "date": article.get('date', ''),
                "domain": article.get('domain', ''),
                "country": article.get('country', ''),
                "partisan": article.get('partisan', ''),
                "sentiment": article.get('sentiment', ''),
                "categories": ", ".join(article.get('categories', [])),
                "description": article.get('description', '')
            })
        
        if export_format == "CSV":
            df_export = pd.DataFrame(export_data)
            csv = df_export.to_csv(index=False)
            st.sidebar.download_button(
                "Download CSV",
                data=csv,
                file_name=f"namo_articles_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:  # JSON
            import json
            json_data = json.dumps(export_data, indent=2, ensure_ascii=False)
            st.sidebar.download_button(
                "Download JSON",
                data=json_data,
                file_name=f"namo_articles_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )


def show_get_access_page():
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


def show_media_page():
    """Show media directory page."""
    st.markdown('<h1 class="main-header">Media Directory</h1>', unsafe_allow_html=True)
    st.markdown(
        "<div class='subtle'>A searchable directory of alternative media outlets across the Nordics.</div>",
        unsafe_allow_html=True,
    )

    outlets_data = fetch_top_outlets(limit=1000)
    outlets = outlets_data.get("data", []) if outlets_data else []
    outlets = consolidate_outlets(outlets)

    total_outlets = len(outlets)
    countries = {o.get("country") for o in outlets if o.get("country")}
    total_articles = sum(o.get("count", 0) for o in outlets)
    avg_articles = int(total_articles / total_outlets) if total_outlets else 0

    stat_cols = st.columns(4)
    stat_values = [
        ("Total Media", f"{total_outlets:,}"),
        ("Countries Represented", f"{len(countries)}"),
        ("Total Articles", f"{total_articles:,}"),
        ("Avg Articles / Media", f"{avg_articles:,}"),
    ]
    for col, (label, value) in zip(stat_cols, stat_values):
        with col:
            st.markdown(
                f"""
                <div class="stat-card">
                    <div class="label">{label}</div>
                    <div class="value">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    query = st.text_input("Search media by name", placeholder="Type a media name...")
    filtered = filter_outlets(outlets, query)

    selected_domain = None
    try:
        params = st.query_params
        selected_domain = params.get("media")
    except Exception:
        params = st.experimental_get_query_params()
        selected_list = params.get("media")
        selected_domain = selected_list[0] if selected_list else None

    if selected_domain:
        profile = fetch_outlet_profile(selected_domain)
        if profile:
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            st.markdown(
                f"<div class='section-title'>{profile.get('outlet_name') or profile.get('domain')}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div class='subtle'>{profile.get('country', 'Unknown country')} · "
                f"{profile.get('total_articles', 0):,} articles</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<div class='subtle' style='margin-top:6px;'>Profile details coming soon.</div>",
                unsafe_allow_html=True,
            )
            if st.button("Back to Media", use_container_width=False):
                try:
                    st.query_params.pop("media", None)
                    st.rerun()
                except Exception:
                    st.experimental_set_query_params(page="Media")
            st.divider()

    st.caption(f"Showing {min(len(filtered), len(outlets))} of {len(outlets)} media outlets")

    if not filtered:
        st.info("No media outlets match your search.")
        return

    cols = st.columns(3)
    for idx, outlet in enumerate(filtered):
        col = cols[idx % 3]
        name = outlet.get("outlet_name") or outlet.get("domain") or "Unknown outlet"
        country = outlet.get("country") or outlet.get("country_code") or "Unknown"
        count = outlet.get("count", 0)
        with col:
            st.markdown(
                f"""
                <div class="media-card">
                    <div>
                        <h3>{name}</h3>
                        <div class="media-meta">{country}</div>
                        <div class="media-count">{count:,} articles</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("View Media", key=f"media_{idx}", use_container_width=True):
                try:
                    st.query_params["page"] = "Media"
                    st.query_params["media"] = outlet.get("domain") or ""
                    st.rerun()
                except Exception:
                    st.experimental_set_query_params(page="Media", media=outlet.get("domain"))


def show_about_page():
    """Show about page for the observatory."""
    st.markdown('<h1 class="main-header">About Nordicamo</h1>', unsafe_allow_html=True)
    st.markdown(
        "<div class='about-intro'><strong>Nordic Alternative Media Observatory (Nordicamo)</strong> is a comparative "
        "platform for studying alternative news media across the Nordic countries (Denmark, Finland, Norway, and "
        "Sweden). Nordicamo supports research, journalism, and teaching by providing structured access to alternative "
        "news media content. The platform blends scalable computational analysis with possibilities of qualitative "
        "interpretation, enabling reporting and reserach on cross-national comparison between alternative information "
        "landscapes.</div>",
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
                <p>Outlets are selected based on stable publication patterns and clear alternative positioning. A seed
                list of outlet domains is compiled, and article links are collected from site structures and sitemaps
                when available. Scraping respects robots.txt guidance, rate limits, and site stability constraints.
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
        alterpublics_logo = Path(__file__).resolve().parent.parent / "graphics" / "Alterpublics_newlogo.png"
        dml_logo = Path(__file__).resolve().parent.parent / "graphics" / "DML_Logo_nobackground.png"
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
                    alternative media, counterpublics, and disinformation across the Nordic countries (Denmark, Sweden,
                    Norway, Finland) and Austria and Germany, using big data, network analysis, and interviews to
                    understand how non-mainstream information environments function and connect with traditional
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
        show_country_page()
    elif current_page == "Media":
        show_media_page()
    elif current_page == "About":
        show_about_page()
    elif current_page == "GetAccess":
        show_get_access_page()


if __name__ == "__main__":
    main()
