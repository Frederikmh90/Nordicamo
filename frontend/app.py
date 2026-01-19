"""
NAMO Dashboard - Streamlit Frontend
====================================
Interactive dashboard for Nordic Alternative Media Observatory
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging
from pathlib import Path
from PIL import Image, ImageChops
from config import get_api_base_url
from contact import build_access_mailto

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
    st.session_state["page"] = "Platform"

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

# Custom CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Source+Sans+3:wght@400;500;600&display=swap');

    :root {
        --color-bg: #f4f7f6;
        --color-card: #ffffff;
        --color-border: #dce3eb;
        --color-text: #222;
        --color-text-muted: #5a6a7a;
        --color-accent: #1f77b4;
        --color-accent-strong: #155d8f;
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
        font-family: 'Source Sans 3', 'Helvetica', 'Arial', sans-serif;
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
        font-family: 'Space Grotesk', 'Helvetica', 'Arial', sans-serif;
        color: var(--color-accent);
        margin: 0 0 var(--space-3) 0;
        line-height: 1.2;
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
        padding: 10px 0;
    }
    .topbar-spacer {
        height: 0;
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
def fetch_top_outlets(country=None, partisan=None, limit=10):
    """Fetch top outlets."""
    try:
        params = {"limit": limit}
        if country:
            params["country"] = country
        if partisan:
            params["partisan"] = partisan
        
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
                background: var(--color-card);
                border: 1px solid var(--color-border);
                border-radius: var(--radius);
                box-shadow: var(--shadow-soft);
                padding: 16px 18px;
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

    # Data freshness indicator - Enhanced display
    freshness_col1, freshness_col2 = st.columns([3, 1])
    with freshness_col1:
        if freshness and freshness.get("hours_ago") is not None:
            hours_ago = freshness.get("hours_ago", 0)
            if hours_ago < 24:
                freshness_text = f"Last updated: {hours_ago} hours ago"
            elif hours_ago < 168:  # 7 days
                days_ago = hours_ago // 24
                freshness_text = f"Last updated: {days_ago} days ago"
            else:
                weeks_ago = hours_ago // 168
                freshness_text = f"Last updated: {weeks_ago} weeks ago"
            
            last_article = freshness.get('last_article_date', 'N/A')
            if last_article and last_article != 'N/A':
                last_article_formatted = last_article[:10] if len(str(last_article)) >= 10 else str(last_article)
            else:
                last_article_formatted = "N/A"
            
            st.info(f"{freshness_text} | Last article: {last_article_formatted}")
        else:
            st.info("Data freshness information unavailable")
    
    with freshness_col2:
        # Data dictionary expander
        with st.expander("What does this mean?"):
            st.markdown("""
            **Data Dictionary:**
            - **Partisan**: Political leaning of outlet (Right, Left, Other)
            - **Entity**: Person, location, or organization mentioned in articles
            - **Sentiment**: Emotional tone (positive/neutral/negative)
            - **Topic**: Thematic cluster identified by machine learning
            - **Coverage**: Date range of articles in the dataset
            - **Growth Rate**: Average change in article volume per year
            - **Concentration**: Percentage of articles from top 3 outlets
            """)

    # Enhanced KPI strip with new metrics
    if overview:
        k1, k2, k3, k4, k5 = st.columns(5)
        with k1:
            total_articles = overview.get('total_articles', 0)
            render_kpi("Total Articles", f"{total_articles:,}")
        with k2:
            render_kpi("Outlets", f"{overview.get('total_outlets', 0):,}")
        with k3:
            # Articles per outlet average
            avg_per_outlet = enhanced_overview.get('avg_articles_per_outlet', 0) if enhanced_overview else 0
            render_kpi("Avg per Outlet", f"{avg_per_outlet:,.0f}", "articles/outlet")
        with k4:
            # Coverage with year range and article count
            coverage_years = enhanced_overview.get('coverage_years') if enhanced_overview else None
            if not coverage_years:
                dr = overview.get("date_range", {})
                earliest = dr.get("earliest") or "N/A"
                latest = dr.get("latest") or "N/A"
                coverage_years = f"{earliest[:4]}-{latest[:4]}" if earliest != "N/A" else "N/A"
            
            # Format: "2003-2025 (740,129 articles)"
            coverage_display = f"{coverage_years}"
            coverage_subtitle = f"({total_articles:,} articles)"
            render_kpi("Coverage", coverage_display, coverage_subtitle)
        with k5:
            # Growth rate
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
    
    # Articles by country (table) + Partisan distribution (chart) + Right box
    with st.container():
        country_data = pd.DataFrame(
            list(overview['by_country'].items()),
            columns=['Country', 'Articles']
        ).sort_values('Articles', ascending=False)

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

        c1, c2, c3, c4 = st.columns([1, 1.6, 0.9, 0.9])
        with c1:
            st.markdown("**Countries**")
            st.dataframe(
                country_data.style.format({'Articles': '{:,}'}),
                use_container_width=True,
                hide_index=True,
                height=260
            )
        with c2:
            st.markdown("**Partisan Distribution**")
            if len(partisan_data) > 0:
                # Create color mapping - ensure exact match with data
                color_map = {
                    'Right': '#0066CC',   # blue
                    'Left': '#DC143C',    # red
                    'Other': '#2ca02c'    # green
                }
                
                # Sort data according to category order
                category_order = ["Right", "Left", "Other"]
                partisan_data_sorted = partisan_data.copy()
                partisan_data_sorted['Partisan'] = pd.Categorical(
                    partisan_data_sorted['Partisan'], 
                    categories=category_order, 
                    ordered=True
                )
                partisan_data_sorted = partisan_data_sorted.sort_values('Partisan')
                
                # Create colors list matching the sorted order
                colors_list = [color_map.get(str(name), '#808080') for name in partisan_data_sorted['Partisan'].values]
                
                # Use go.Pie for explicit color control
                fig = go.Figure(data=[go.Pie(
                    labels=partisan_data_sorted['Partisan'].values,
                    values=partisan_data_sorted['Articles'].values,
                    hole=0.45,
                    marker=dict(colors=colors_list, line=dict(color='white', width=2)),
                    textinfo='none',
                    hovertemplate='<b>%{label}</b><br>Articles: %{value:,}<br>Percentage: %{percent}<extra></extra>'
                )])
                fig.update_layout(
                    height=260,
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
        with c3:
            st.markdown("**Live ingest**")
            st.markdown(
                """
                <div style="
                    background: var(--color-card);
                    border: 1px solid var(--color-border);
                    border-radius: var(--radius);
                    box-shadow: var(--shadow-soft);
                    padding: 14px;
                    height: 260px;
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
        with c4:
            # Fetch comparative metrics for outlet concentration
            comparative = fetch_comparative_metrics()
            st.markdown("**Media Diversity**")
            
            # Build the content with percentages
            percentages_html = ""
            if comparative:
                countries_order = ["denmark", "sweden", "norway", "finland"]
                for country in countries_order:
                    country_data = comparative.get(country, {})
                    concentration = country_data.get("outlet_concentration", 0)
                    percentages_html += f"<div style='margin-bottom: 8px;'><strong>{country.capitalize()}:</strong> {concentration}%</div>"
            else:
                # Fallback: show overall concentration
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
                    height: 260px;
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
            options=["year", "month", "week"],
            index=1,
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
                granularity=granularity,
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
            title=f"Articles Over Time by Country ({granularity.capitalize()})",
            xaxis_title="Date",
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
            margin=dict(b=50, t=80, l=50, r=50)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        time_data = fetch_articles_over_time(
            country=selected_country,
            partisan=selected_partisan,
            granularity=granularity,
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
    
    # Category distribution
    st.subheader("News Categories")
    st.caption("News categories are based on automated content analysis using mistralai/Mistral-Small-24B-Instruct-2501 on content level")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        categories_data = fetch_categories(country=selected_country, partisan=selected_partisan)
        if categories_data and categories_data.get('data'):
            df_cat = pd.DataFrame(categories_data['data'])
            df_cat = df_cat.sort_values('count', ascending=False)
            
            # Process category names to add line breaks using <br> (HTML) - break into 2-3 lines
            def format_category_name(name):
                # First, replace " & " with " &<br>" for line breaks
                name = name.replace(' & ', ' &<br>')
                
                # Split by existing line breaks and process each part
                parts = name.split('<br>')
                result_parts = []
                
                for part in parts:
                    # If a part is longer than 18 characters, break it further
                    if len(part) > 18:
                        words = part.split()
                        if len(words) >= 3:
                            # Break into 2-3 lines: aim for ~12-15 chars per line
                            # Try to break at natural points
                            if ', ' in part:
                                # Break at comma
                                subparts = part.split(', ')
                                if len(subparts) == 2:
                                    part = subparts[0] + ',<br>' + subparts[1]
                                else:
                                    # Multiple commas - break into 2-3 parts
                                    mid = len(subparts) // 2
                                    part = ',<br>'.join(subparts[:mid]) + ',<br>' + ',<br>'.join(subparts[mid:])
                            else:
                                # Break at word boundaries - split into roughly 2-3 equal parts
                                if len(words) <= 4:
                                    # 2 lines
                                    mid = len(words) // 2
                                    part = ' '.join(words[:mid]) + '<br>' + ' '.join(words[mid:])
                                else:
                                    # 3 lines
                                    third = len(words) // 3
                                    part = ' '.join(words[:third]) + '<br>' + ' '.join(words[third:2*third]) + '<br>' + ' '.join(words[2*third:])
                    result_parts.append(part)
                
                return '<br>'.join(result_parts)
            
            # Create display names with line breaks for chart only
            df_cat_display = df_cat.copy()
            df_cat_display['category_display'] = df_cat_display['category'].apply(format_category_name)
            
            # Create the figure with original category names first
            fig = px.bar(
                df_cat,
                x='category',
                y='count',
                color='count',
                text='count',
                color_continuous_scale='Blues',
                title="Article Distribution by Category"
            )
            
            # Update x-axis with formatted labels using ticktext and tickvals
            fig.update_xaxes(
                ticktext=df_cat_display['category_display'].values,
                tickvals=df_cat['category'].values,
                tickangle=0,
                tickfont={'size': 10},
                categoryorder='total descending'
            )
            
            # Store original category names for hover tooltip
            fig.update_traces(
                texttemplate='%{text:,}',
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>Articles: %{y:,}<extra></extra>'
            )
            
            fig.update_layout(
                xaxis_title="Category",
                yaxis_title="Number of Articles",
                height=480,  # Increased height to accommodate all labels
                margin=dict(b=150, t=100, l=50, r=50),  # Increased top margin for value labels, bottom for category labels
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No category data available.")
    
    with col2:
        if categories_data and categories_data.get('data'):
            # Display only original columns (category and count), not category_display
            df_cat_table = df_cat[['category', 'count']].copy()
            st.dataframe(
                df_cat_table.style.format({'count': '{:,}'}),
                use_container_width=True,
                hide_index=True
            )
    
    # Sentiment analysis
    st.subheader("Sentiment Analysis")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        sentiment_data = fetch_sentiment(country=selected_country, partisan=selected_partisan)
        if sentiment_data and sentiment_data.get('data'):
            df_sent = pd.DataFrame(sentiment_data['data'])
            
            fig = px.bar(
                df_sent,
                x='sentiment',
                y='count',
                color='sentiment',
                text='count',
                color_discrete_map={
                    'positive': '#2ca02c',
                    'neutral': '#808080',
                    'negative': '#d62728'
                },
                title="Sentiment Distribution"
            )
            fig.update_traces(
                texttemplate='%{text:,}',
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>Articles: %{y:,}<br>Avg Score: %{customdata:.2f}<extra></extra>',
                customdata=df_sent['avg_score']
            )
            fig.update_layout(
                xaxis_title="Sentiment",
                yaxis_title="Number of Articles",
                height=350,
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No sentiment data available.")
    
    with col2:
        if sentiment_data and sentiment_data.get('data'):
            st.dataframe(
                df_sent[['sentiment', 'count', 'avg_score']].style.format({
                    'count': '{:,}',
                    'avg_score': '{:.2f}'
                }),
                use_container_width=True,
                hide_index=True
            )
    
    # Named Entity Recognition (NER)
    st.subheader("Named Entity Recognition")
    
    # Entity statistics
    entity_stats = fetch_entity_statistics(country=selected_country, partisan=selected_partisan)
    if entity_stats:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Articles with Persons", f"{entity_stats.get('articles_with_persons', 0):,}")
        with col2:
            st.metric("Articles with Locations", f"{entity_stats.get('articles_with_locations', 0):,}")
        with col3:
            st.metric("Articles with Organizations", f"{entity_stats.get('articles_with_organizations', 0):,}")
        with col4:
            total = entity_stats.get('total_articles', 0)
            coverage = entity_stats.get('coverage', {})
            avg_coverage = sum(coverage.values()) / len(coverage) if coverage else 0
            st.metric("Avg Coverage", f"{avg_coverage:.1f}%")
    
    # Top entities by type
    entity_type = st.selectbox(
        "Entity Type",
        options=["persons", "locations", "organizations"],
        index=0,
        key="entity_type_selector",
        help="Type of named entities to analyze: persons (people), locations (places), or organizations (companies, institutions)"
    )
    
    entities_data = fetch_top_entities(
        entity_type=entity_type,
        country=selected_country,
        partisan=selected_partisan,
        limit=15
    )
    
    if entities_data and entities_data.get('data'):
        df_entities = pd.DataFrame(entities_data['data'])
        df_entities = df_entities.sort_values('count', ascending=False)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Create stacked bar chart showing sentiment breakdown
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                name='Positive',
                x=df_entities['entity_name'],
                y=df_entities['positive_count'],
                marker_color='#2ca02c',
                hovertemplate='<b>%{x}</b><br>Positive: %{y:,}<extra></extra>'
            ))
            fig.add_trace(go.Bar(
                name='Neutral',
                x=df_entities['entity_name'],
                y=df_entities['neutral_count'],
                marker_color='#808080',
                hovertemplate='<b>%{x}</b><br>Neutral: %{y:,}<extra></extra>'
            ))
            fig.add_trace(go.Bar(
                name='Negative',
                x=df_entities['entity_name'],
                y=df_entities['negative_count'],
                marker_color='#d62728',
                hovertemplate='<b>%{x}</b><br>Negative: %{y:,}<extra></extra>'
            ))
            
            fig.update_layout(
                barmode='stack',
                title=f"Top {entity_type.capitalize()} by Mention Count (with Sentiment)",
                xaxis_title=entity_type.capitalize(),
                yaxis_title="Number of Mentions",
                height=450,
                xaxis={'categoryorder': 'total descending'},
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.dataframe(
                df_entities[['entity_name', 'count', 'positive_count', 'negative_count', 'neutral_count']].style.format({
                    'count': '{:,}',
                    'positive_count': '{:,}',
                    'negative_count': '{:,}',
                    'neutral_count': '{:,}'
                }),
                use_container_width=True,
                hide_index=True,
                column_config={
                    'entity_name': 'Entity',
                    'count': 'Total',
                    'positive_count': 'Pos',
                    'negative_count': 'Neg',
                    'neutral_count': 'Neu'
                }
            )
    else:
        st.info(f"No {entity_type} data available.")
    
    # Topic Modeling
    st.divider()
    st.subheader("Topic Modeling")
    
    # Topic statistics
    topic_stats = fetch_topic_statistics(country=selected_country, partisan=selected_partisan)
    if topic_stats:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Articles with Topics", f"{topic_stats.get('articles_with_topics', 0):,}")
        with col2:
            st.metric("Unique Topics", topic_stats.get('unique_topics', 0))
        with col3:
            st.metric("Total Articles", f"{topic_stats.get('total_articles', 0):,}")
        with col4:
            coverage = topic_stats.get('coverage', 0)
            st.metric("Topic Coverage", f"{coverage:.1f}%")
    
    # Topic distribution
    st.markdown("#### Topic Distribution")
    topic_dist_data = fetch_topic_distribution(
        country=selected_country,
        partisan=selected_partisan
    )
    
    if topic_dist_data and topic_dist_data.get('data'):
        df_topics = pd.DataFrame(topic_dist_data['data'])
        df_topics = df_topics.sort_values('count', ascending=False)
        # Filter out noise topic (-1) if present
        df_topics = df_topics[df_topics['topic_id'] != -1]
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig = px.bar(
                df_topics.head(20),  # Show top 20 topics
                x='topic_id',
                y='count',
                color='avg_probability',
                text='count',
                color_continuous_scale='Viridis',
                title="Top Topics by Article Count"
            )
            fig.update_traces(
                texttemplate='%{text:,}',
                textposition='outside',
                hovertemplate='<b>Topic %{x}</b><br>Articles: %{y:,}<br>Avg Probability: %{customdata:.3f}<extra></extra>',
                customdata=df_topics.head(20)['avg_probability']
            )
            fig.update_layout(
                xaxis_title="Topic ID",
                yaxis_title="Number of Articles",
                height=450,
                xaxis={'categoryorder': 'total descending'},
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.dataframe(
                df_topics.head(20)[['topic_id', 'count', 'avg_probability']].style.format({
                    'count': '{:,}',
                    'avg_probability': '{:.3f}'
                }),
                use_container_width=True,
                hide_index=True,
                column_config={
                    'topic_id': 'Topic',
                    'count': 'Articles',
                    'avg_probability': 'Avg Prob'
                }
            )
    
    # Topics over time
    st.markdown("#### Topics Over Time")
    col1, col2 = st.columns([1, 3])
    
    with col1:
        selected_topic_id = st.selectbox(
            "Select Topic",
            options=[None] + sorted(df_topics['topic_id'].tolist() if topic_dist_data and topic_dist_data.get('data') else []),
            format_func=lambda x: f"All Topics" if x is None else f"Topic {x}",
            key="topic_selector",
            help="Select a specific topic to analyze its distribution over time, or view all topics together"
        )
        granularity = st.selectbox(
            "Time Granularity",
            options=["day", "week", "month", "year"],
            index=2,
            key="topic_granularity",
            help="Time period grouping for the time series chart (day, week, month, or year)"
        )
    
    with col2:
        topics_time_data = fetch_topics_over_time(
            topic_id=selected_topic_id,
            country=selected_country,
            granularity=granularity
        )
        
        if topics_time_data and topics_time_data.get('data'):
            df_time = pd.DataFrame(topics_time_data['data'])
            
            if selected_topic_id is None:
                # Show all topics as separate lines
                fig = px.line(
                    df_time,
                    x='date',
                    y='count',
                    color='topic_id',
                    markers=True,
                    title=f"All Topics Over Time ({granularity.capitalize()})"
                )
                fig.update_traces(
                    line=dict(width=2),
                    marker=dict(size=6)
                )
            else:
                # Show single topic
                df_time = df_time[df_time['topic_id'] == selected_topic_id]
                df_time = df_time.sort_values('date')
                fig = px.line(
                    df_time,
                    x='date',
                    y='count',
                    markers=True,
                    title=f"Topic {selected_topic_id} Over Time ({granularity.capitalize()})"
                )
                fig.update_traces(
                    line=dict(width=3, color='#1f77b4'),
                    marker=dict(size=8)
                )
            
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Number of Articles",
                height=400,
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No topic time series data available.")


def show_topic_analysis_page():
    """Show dedicated topic analysis page."""
    st.markdown('<h1 class="main-header">🔍 Topic Analysis</h1>', unsafe_allow_html=True)
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        selected_country = st.selectbox(
            "Filter by Country",
            options=[None, "denmark", "sweden", "norway", "finland"],
            format_func=lambda x: "All Countries" if x is None else x.capitalize(),
            key="topic_country_filter",
            help="Select a specific Nordic country or view all countries together"
        )
    with col2:
        selected_partisan = st.selectbox(
            "Filter by Partisan",
            options=[None, "left", "right", "center"],
            format_func=lambda x: "All" if x is None else x.capitalize(),
            key="topic_partisan_filter",
            help="Political orientation of the media outlet (self-identified or classified)"
        )
    
    st.divider()
    
    # Topic statistics
    st.subheader("📊 Topic Statistics")
    topic_stats = fetch_topic_statistics(country=selected_country, partisan=selected_partisan)
    if topic_stats:
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Articles", f"{topic_stats.get('total_articles', 0):,}")
        with col2:
            st.metric("Articles with Topics", f"{topic_stats.get('articles_with_topics', 0):,}")
        with col3:
            st.metric("Unique Topics", topic_stats.get('unique_topics', 0))
        with col4:
            coverage = topic_stats.get('coverage', 0)
            st.metric("Topic Coverage", f"{coverage:.1f}%")
        with col5:
            avg_prob = topic_stats.get('avg_probability', 0)
            st.metric("Avg Probability", f"{avg_prob:.3f}")
    
    st.divider()
    
    # Topic distribution
    st.subheader("📈 Topic Distribution")
    topic_dist_data = fetch_topic_distribution(
        country=selected_country,
        partisan=selected_partisan
    )
    
    if topic_dist_data and topic_dist_data.get('data'):
        df_topics = pd.DataFrame(topic_dist_data['data'])
        df_topics = df_topics.sort_values('count', ascending=False)
        # Filter out noise topic (-1) if present
        df_topics = df_topics[df_topics['topic_id'] != -1]
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Show top 30 topics
            top_n = st.slider("Number of Topics to Display", 10, min(50, len(df_topics)), 20, key="topic_top_n")
            
            fig = px.bar(
                df_topics.head(top_n),
                x='topic_id',
                y='count',
                color='avg_probability',
                text='count',
                color_continuous_scale='Viridis',
                title=f"Top {top_n} Topics by Article Count"
            )
            fig.update_traces(
                texttemplate='%{text:,}',
                textposition='outside',
                hovertemplate='<b>Topic %{x}</b><br>Articles: %{y:,}<br>Avg Probability: %{customdata:.3f}<extra></extra>',
                customdata=df_topics.head(top_n)['avg_probability']
            )
            fig.update_layout(
                xaxis_title="Topic ID",
                yaxis_title="Number of Articles",
                height=500,
                xaxis={'categoryorder': 'total descending'},
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### Top Topics Table")
            st.dataframe(
                df_topics.head(top_n)[['topic_id', 'count', 'avg_probability']].style.format({
                    'count': '{:,}',
                    'avg_probability': '{:.3f}'
                }),
                use_container_width=True,
                hide_index=True,
                column_config={
                    'topic_id': 'Topic',
                    'count': 'Articles',
                    'avg_probability': 'Avg Prob'
                },
                height=500
            )
    else:
        st.info("No topic distribution data available. Make sure topics have been loaded to the database.")
    
    st.divider()
    
    # Topics over time
    st.subheader("📅 Topics Over Time")
    col1, col2 = st.columns([1, 4])
    
    with col1:
        # Get available topic IDs
        available_topics = []
        if topic_dist_data and topic_dist_data.get('data'):
            df_topics_temp = pd.DataFrame(topic_dist_data['data'])
            df_topics_temp = df_topics_temp[df_topics_temp['topic_id'] != -1]
            available_topics = sorted(df_topics_temp['topic_id'].tolist())
        
        selected_topic_id = st.selectbox(
            "Select Topic",
            options=[None] + available_topics,
            format_func=lambda x: f"All Topics" if x is None else f"Topic {x}",
            key="topic_time_selector",
            help="Select a specific topic to analyze its distribution over time, or view all topics together"
        )
        
        granularity = st.selectbox(
            "Time Granularity",
            options=["day", "week", "month", "year"],
            index=2,
            key="topic_time_granularity",
            help="Time period grouping for the time series chart (day, week, month, or year)"
        )
        
        # Date range filter
        st.markdown("**Date Range** (optional)")
        date_from = st.date_input("From", value=None, key="topic_date_from")
        date_to = st.date_input("To", value=None, key="topic_date_to")
    
    with col2:
        topics_time_data = fetch_topics_over_time(
            topic_id=selected_topic_id,
            country=selected_country,
            granularity=granularity,
            date_from=str(date_from) if date_from else None,
            date_to=str(date_to) if date_to else None
        )
        
        if topics_time_data and topics_time_data.get('data'):
            df_time = pd.DataFrame(topics_time_data['data'])
            df_time['date'] = pd.to_datetime(df_time['date'], errors='coerce')
            df_time = df_time.sort_values('date')
            
            if selected_topic_id is None:
                # Show all topics as separate lines
                fig = px.line(
                    df_time,
                    x='date',
                    y='count',
                    color='topic_id',
                    markers=True,
                    title=f"All Topics Over Time ({granularity.capitalize()})"
                )
                fig.update_traces(
                    line=dict(width=2),
                    marker=dict(size=6)
                )
                fig.update_layout(
                    legend=dict(
                        orientation="v",
                        yanchor="top",
                        y=1,
                        xanchor="left",
                        x=1.02
                    )
                )
            else:
                # Show single topic
                df_time_single = df_time[df_time['topic_id'] == selected_topic_id]
                df_time_single = df_time_single.sort_values('date')
                fig = px.line(
                    df_time_single,
                    x='date',
                    y='count',
                    markers=True,
                    title=f"Topic {selected_topic_id} Over Time ({granularity.capitalize()})"
                )
                fig.update_traces(
                    line=dict(width=3, color='#1f77b4'),
                    marker=dict(size=8)
                )
            
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Number of Articles",
                height=500,
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Summary statistics
            if selected_topic_id is not None:
                st.markdown("#### Topic Statistics")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Articles", f"{df_time_single['count'].sum():,}")
                with col2:
                    st.metric("Peak Month", df_time_single.loc[df_time_single['count'].idxmax(), 'date'].strftime('%Y-%m') if len(df_time_single) > 0 else "N/A")
                with col3:
                    st.metric("Peak Count", f"{df_time_single['count'].max():,}" if len(df_time_single) > 0 else "N/A")
        else:
            st.info("No topic time series data available.")


def show_country_page():
    """Show country-specific analysis page."""
    st.markdown('<h1 class="main-header">Countries</h1>', unsafe_allow_html=True)
    
    # Country selector
    default_country = st.session_state.get("quick_country", "denmark")
    country = st.selectbox(
        "Select Country",
        options=["denmark", "sweden", "norway", "finland"],
        index=["denmark", "sweden", "norway", "finland"].index(default_country) if default_country in ["denmark", "sweden", "norway", "finland"] else 0,
        format_func=lambda x: x.capitalize(),
        help="Select a Nordic country to view country-specific analytics and statistics"
    )
    st.session_state["quick_country"] = country
    
    st.divider()
    
    # All outlets for country
    st.subheader(f"Outlets in {country.capitalize()}")
    outlets_data = fetch_top_outlets(country=country, limit=1000)  # Get all outlets
    
    if outlets_data and outlets_data.get('data'):
        df_outlets = pd.DataFrame(outlets_data['data'])
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig = px.bar(
                df_outlets,
                x='count',
                y='domain',
                orientation='h',
                color='partisan',
                color_discrete_map={
                    'Right': '#0066CC',   # blue
                    'Left': '#DC143C',    # red
                    'Other': '#2ca02c'     # green
                },
                text='count',
                title=f"Outlets by Article Count"
            )
            fig.update_traces(
                texttemplate='%{text:,}',
                textposition='outside',
                hovertemplate='<b>%{y}</b><br>Articles: %{x:,}<br>Partisan: %{customdata}<extra></extra>',
                customdata=df_outlets['partisan']
            )
            # Adjust height based on number of outlets
            num_outlets = len(df_outlets)
            chart_height = max(400, min(800, 30 * num_outlets + 100))  # Dynamic height, max 800px
            
            fig.update_layout(
                xaxis_title="Number of Articles",
                yaxis_title="Outlet",
                height=chart_height,
                yaxis={'categoryorder': 'total ascending'},
                showlegend=True
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.dataframe(
                df_outlets[['domain', 'outlet_name', 'partisan', 'count']].style.format({'count': '{:,}'}),
                use_container_width=True,
                hide_index=True
            )
    
    # Articles over time for country
    st.subheader(f"Articles Over Time - {country.capitalize()}")
    
    # View type selector
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
            options=["year", "month", "week"],
            index=1,
            key="country_granularity",
            help="Time period grouping for the time series chart (year, month, or week)"
        )
    with col2:
        if view_type == "Separate Outlets":
            # Get top outlets for selection
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
            partisan_filter = None  # Not used in this view
        else:
            partisan_filter = st.selectbox(
                "Filter by Partisan",
                options=[None, "Right", "Left", "Other"],
                format_func=lambda x: "All" if x is None else x,
                key="country_partisan",
                help="Political orientation of the media outlet (self-identified or classified)"
            )
            selected_outlets = []  # Not used in other views
    
    # Fetch and display data based on view type
    if view_type == "Total Count":
        time_data = fetch_articles_over_time(
            country=country,
            partisan=partisan_filter,
            granularity=granularity
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
                title=f"Articles Over Time - {country.capitalize()} (Total Count)"
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
                granularity=granularity
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
                granularity=granularity
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
        
        fig.update_layout(
            title=f"Articles Over Time - {country.capitalize()} (By Partisan)",
            xaxis_title="Date",
            yaxis_title="Number of Articles",
            height=400,
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Category and sentiment for country
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Categories")
        categories_data = fetch_categories(country=country, partisan=partisan_filter)
        if categories_data and categories_data.get('data'):
            df_cat = pd.DataFrame(categories_data['data'])
            df_cat = df_cat.sort_values('count', ascending=False).head(10)
            
            # Calculate percentage
            total = df_cat['count'].sum()
            df_cat['percentage'] = (df_cat['count'] / total * 100).round(1)
            
            # Display as table
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
    
    with col2:
        st.subheader("Sentiment")
        sentiment_data = fetch_sentiment(country=country, partisan=partisan_filter)
        if sentiment_data and sentiment_data.get('data'):
            df_sent = pd.DataFrame(sentiment_data['data'])
            
            fig = px.pie(
                df_sent,
                values='count',
                names='sentiment',
                color='sentiment',
                color_discrete_map={
                    'positive': '#2ca02c',
                    'neutral': '#808080',
                    'negative': '#d62728'
                },
                title=f"Sentiment Distribution - {country.capitalize()}"
            )
            fig.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate='<b>%{label}</b><br>Articles: %{value:,}<br>Percentage: %{percent}<extra></extra>'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)


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
    st.markdown('<h1 class="main-header">Get Access</h1>', unsafe_allow_html=True)
    st.markdown(
        "Request data access or specific extracts from the NAMO collection. "
        "This will open your email client with a prepared message."
    )

    with st.form("access_request"):
        tabs = st.tabs(["Name", "Email", "Request"])
        with tabs[0]:
            name = st.text_input("Full name", placeholder="Your name")
        with tabs[1]:
            email = st.text_input("Email address", placeholder="name@organization.org")
        with tabs[2]:
            request = st.text_area(
                "Request details",
                height=220,
                placeholder="Describe the data you need (countries, outlets, date ranges, or full dataset).",
            )
        submitted = st.form_submit_button("Prepare request")

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

        mailto_link = build_access_mailto(name=name, email=email, request=request)
        st.success("Ready to send. This is a placeholder and will open your email client.")
        st.markdown(f"[Send request]({mailto_link})")


def main():
    """Main application."""
    st.markdown('<div class="topbar">', unsafe_allow_html=True)
    top_cols = st.columns([2.6, 7.4])
    with top_cols[0]:
        logo_to_use = get_trimmed_logo()
        if logo_to_use and logo_to_use.exists():
            st.image(str(logo_to_use), width=240, output_format="PNG")
        else:
            st.markdown(
                '<div style="font-size:1.4rem; font-weight:700; color:#1f77b4;">NAMO</div>',
                unsafe_allow_html=True,
            )
    with top_cols[1]:
        nav_cols = st.columns(4)
        nav_items = [
            ("Platform", "Platform"),
            ("Countries", "Countries"),
            ("Dataset", "Dataset"),
            ("Get Access", "Get Access"),
        ]
        current_page = st.session_state.get("page", "Platform")
        for col, (label, page_key) in zip(nav_cols, nav_items):
            with col:
                is_active = current_page == page_key
                if st.button(
                    label,
                    use_container_width=True,
                    key=f"nav_{page_key}",
                    type="primary" if is_active else "secondary",
                ):
                    st.session_state["page"] = page_key
                    if page_key != "Countries":
                        st.session_state["quick_country"] = None
    st.markdown('</div>', unsafe_allow_html=True)

    page = st.session_state.get("page", "Platform")
    
    # Route to page
    if page == "Platform":
        show_overview_page()
    elif page == "Countries":
        show_country_page()
    elif page == "Dataset":
        show_content_engagement_page()
    elif page == "Get Access":
        show_get_access_page()


if __name__ == "__main__":
    main()
