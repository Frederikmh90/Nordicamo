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

# Configuration
API_BASE_URL = "http://localhost:8000"
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
if "page_override" not in st.session_state:
    st.session_state["page_override"] = None
if "page" not in st.session_state:
    st.session_state["page"] = "Overview"

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
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');

    :root {
        --color-bg: #f7f9fb;
        --color-card: #ffffff;
        --color-border: #dce3eb;
        --color-text: #222;
        --color-text-muted: #5a6a7a;
        --color-accent: #1f77b4;
        --color-accent-strong: #155d8f;
        --color-code-bg: #f5f7f9;
        --color-code-border: #d8dee9;
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
        background: var(--color-bg);
        color: var(--color-text);
        font-family: 'Roboto', 'Helvetica', 'Arial', sans-serif;
        line-height: 1.5;
    }

    /* Container spacing */
    .block-container {
        padding: var(--space-5);
        max-width: 1200px;
        margin: 0 auto;
    }

    /* Header */
    .main-header {
        font-size: 2.2rem;
        font-weight: 600;
        color: var(--color-accent);
        margin: 0 0 var(--space-3) 0;
        line-height: 1.2;
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

    # Data freshness indicator
    if freshness and freshness.get("hours_ago") is not None:
        hours_ago = freshness.get("hours_ago", 0)
        if hours_ago < 24:
            freshness_text = f"Updated {hours_ago}h ago"
        elif hours_ago < 168:  # 7 days
            days_ago = hours_ago // 24
            freshness_text = f"Updated {days_ago}d ago"
        else:
            weeks_ago = hours_ago // 168
            freshness_text = f"Updated {weeks_ago}w ago"
        
        st.info(f"🕒 {freshness_text} | Last article: {freshness.get('last_article_date', 'N/A')[:10] if freshness.get('last_article_date') else 'N/A'}")

    # Enhanced KPI strip with new metrics
    if overview:
        k1, k2, k3, k4, k5 = st.columns(5)
        with k1:
            render_kpi("Total Articles", f"{overview.get('total_articles', 0):,}")
        with k2:
            render_kpi("Outlets", f"{overview.get('total_outlets', 0):,}")
        with k3:
            # Articles per outlet average
            avg_per_outlet = enhanced_overview.get('avg_articles_per_outlet', 0) if enhanced_overview else 0
            render_kpi("Avg per Outlet", f"{avg_per_outlet:,.0f}", "articles/outlet")
        with k4:
            # Coverage with year range
            coverage_years = enhanced_overview.get('coverage_years') if enhanced_overview else None
            if not coverage_years:
                dr = overview.get("date_range", {})
                earliest = dr.get("earliest") or "N/A"
                latest = dr.get("latest") or "N/A"
                coverage_years = f"{earliest[:4]}-{latest[:4]}" if earliest != "N/A" else "N/A"
            render_kpi("Coverage", coverage_years, "years")
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
    
    # Outlet Concentration Section
    st.subheader("📊 Market Concentration")
    comparative = fetch_comparative_metrics()
    if comparative:
        conc_cols = st.columns(4)
        countries_order = ["denmark", "sweden", "norway", "finland"]
        for idx, country in enumerate(countries_order):
            with conc_cols[idx]:
                country_data = comparative.get(country, {})
                concentration = country_data.get("outlet_concentration", 0)
                st.metric(
                    country.capitalize(),
                    f"{concentration}%",
                    help=f"Top 3 outlets control {concentration}% of articles"
                )
    else:
        # Fallback: show overall concentration
        overall_conc = fetch_outlet_concentration()
        if overall_conc:
            st.metric(
                "Overall Concentration",
                f"{overall_conc.get('concentration_percentage', 0)}%",
                help="Top 3 outlets control this percentage of all articles"
            )
    
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

        c1, c2, c3 = st.columns([1, 1.6, 0.9])
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
                fig = px.pie(
                    partisan_data,
                    values='Articles',
                    names='Partisan',
                    color_discrete_map={
                        'Right': '#1f77b4',   # blue
                        'Left': '#d62728',    # red
                        'Other': '#808080'    # gray
                    },
                    category_orders={"Partisan": ["Right", "Left", "Other"]},
                    hole=0.45
                )
                fig.update_traces(
                    textinfo='none',
                    hovertemplate='<b>%{label}</b><br>Articles: %{value:,}<br>Percentage: %{percent}<extra></extra>'
                )
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
    
    # Articles over time - Multi-country comparison with year slider
    st.subheader("📅 Articles Over Time")
    
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
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_country = st.selectbox(
            "Filter by Country",
            options=[None, "denmark", "sweden", "norway", "finland"],
            format_func=lambda x: "All Countries" if x is None else x.capitalize()
        )
    with col2:
        selected_partisan = st.selectbox(
            "Filter by Partisan",
            options=[None, "Right", "Left", "Other"],
            format_func=lambda x: "All" if x is None else x
        )
    with col3:
        granularity = st.selectbox(
            "Time Granularity",
            options=["year", "month", "week"],
            index=1
        )
    
    # Show multi-country comparison if no country filter
    if not selected_country:
        # Fetch data for all countries
        fig = go.Figure()
        countries = ["denmark", "sweden", "norway", "finland"]
        colors = {'denmark': '#1f77b4', 'sweden': '#d62728', 'norway': '#2ca02c', 'finland': '#ff7f0e'}
        
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
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
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
    st.subheader("📂 News Categories")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        categories_data = fetch_categories(country=selected_country, partisan=selected_partisan)
        if categories_data and categories_data.get('data'):
            df_cat = pd.DataFrame(categories_data['data'])
            df_cat = df_cat.sort_values('count', ascending=False)
            
            fig = px.bar(
                df_cat,
                x='category',
                y='count',
                color='count',
                text='count',
                color_continuous_scale='Blues',
                title="Article Distribution by Category"
            )
            fig.update_traces(
                texttemplate='%{text:,}',
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>Articles: %{y:,}<extra></extra>'
            )
            fig.update_layout(
                xaxis_title="Category",
                yaxis_title="Number of Articles",
                height=400,
                xaxis={'categoryorder': 'total descending'},
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No category data available.")
    
    with col2:
        if categories_data and categories_data.get('data'):
            st.dataframe(
                df_cat.style.format({'count': '{:,}'}),
                use_container_width=True,
                hide_index=True
            )
    
    # Sentiment analysis
    st.subheader("😊 Sentiment Analysis")
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
    st.subheader("👥 Named Entity Recognition")
    
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
        key="entity_type_selector"
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
    st.subheader("🔍 Topic Modeling")
    
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
            key="topic_selector"
        )
        granularity = st.selectbox(
            "Time Granularity",
            options=["day", "week", "month", "year"],
            index=2,
            key="topic_granularity"
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
            key="topic_country_filter"
        )
    with col2:
        selected_partisan = st.selectbox(
            "Filter by Partisan",
            options=[None, "left", "right", "center"],
            format_func=lambda x: "All" if x is None else x.capitalize(),
            key="topic_partisan_filter"
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
            key="topic_time_selector"
        )
        
        granularity = st.selectbox(
            "Time Granularity",
            options=["day", "week", "month", "year"],
            index=2,
            key="topic_time_granularity"
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
    st.markdown('<h1 class="main-header">🌍 Country Analysis</h1>', unsafe_allow_html=True)
    
    # Country selector
    default_country = st.session_state.get("quick_country", "denmark")
    country = st.selectbox(
        "Select Country",
        options=["denmark", "sweden", "norway", "finland"],
        index=["denmark", "sweden", "norway", "finland"].index(default_country) if default_country in ["denmark", "sweden", "norway", "finland"] else 0,
        format_func=lambda x: x.capitalize()
    )
    st.session_state["quick_country"] = country
    
    st.divider()
    
    # Top outlets for country
    st.subheader(f"📰 Top 10 Outlets in {country.capitalize()}")
    outlets_data = fetch_top_outlets(country=country, limit=10)
    
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
                    'Right': '#d62728',
                    'Left': '#1f77b4',
                    'Other': '#2ca02c'
                },
                text='count',
                title=f"Top 10 Outlets by Article Count"
            )
            fig.update_traces(
                texttemplate='%{text:,}',
                textposition='outside',
                hovertemplate='<b>%{y}</b><br>Articles: %{x:,}<br>Partisan: %{customdata}<extra></extra>',
                customdata=df_outlets['partisan']
            )
            fig.update_layout(
                xaxis_title="Number of Articles",
                yaxis_title="Outlet",
                height=400,
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
    st.subheader(f"📅 Articles Over Time - {country.capitalize()}")
    
    col1, col2 = st.columns(2)
    with col1:
        partisan_filter = st.selectbox(
            "Filter by Partisan",
            options=[None, "Right", "Left", "Other"],
            format_func=lambda x: "All" if x is None else x,
            key="country_partisan"
        )
    with col2:
        granularity = st.selectbox(
            "Time Granularity",
            options=["year", "month", "week"],
            index=1,
            key="country_granularity"
        )
    
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
            title=f"Articles Over Time - {country.capitalize()}"
        )
        fig.update_traces(
            line=dict(width=3),
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
    
    # Category and sentiment for country
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📂 Categories")
        categories_data = fetch_categories(country=country, partisan=partisan_filter)
        if categories_data and categories_data.get('data'):
            df_cat = pd.DataFrame(categories_data['data'])
            df_cat = df_cat.sort_values('count', ascending=False).head(10)
            
            fig = px.pie(
                df_cat,
                values='count',
                names='category',
                title=f"Top Categories - {country.capitalize()}"
            )
            fig.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate='<b>%{label}</b><br>Articles: %{value:,}<br>Percentage: %{percent}<extra></extra>'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("😊 Sentiment")
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


def main():
    """Main application."""
    # Top bar with brand logo, title, and data badge
    logo_col, title_col = st.columns([2.2, 4.8])
    with logo_col:
        logo_to_use = get_trimmed_logo()
        if logo_to_use and logo_to_use.exists():
            st.image(str(logo_to_use), width=320, output_format="PNG")
        else:
            st.markdown(
                '<div style="font-size:1.6rem; font-weight:700; color:#1f77b4;">NAMO</div>',
                unsafe_allow_html=True,
            )
    with title_col:
        # Title hidden per request
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        # Version badge
        st.markdown(
            f'<div style="text-align: right; font-size: 11px; color: var(--color-text-muted);">v{DASHBOARD_VERSION}</div>',
            unsafe_allow_html=True
        )

    # Top navigation tabs using active state (pill style)
    nav_cols = st.columns(3)
    nav_items = ["Overview", "Country Analysis", "Topic Analysis"]
    current_page = st.session_state.get("page", "Overview")
    for col, item in zip(nav_cols, nav_items):
        with col:
            is_active = current_page == item
            button_label = item
            if st.button(button_label, use_container_width=True, key=f"nav_{item}", type="primary" if is_active else "secondary"):
                st.session_state["page"] = item
                if item != "Country Analysis":
                    st.session_state["quick_country"] = None

    # Quick country buttons as a full-width row beneath the nav
    button_cols = st.columns(4)
    for col, country_label, country_value in [
        (button_cols[0], "Denmark", "denmark"),
        (button_cols[1], "Finland", "finland"),
        (button_cols[2], "Norway", "norway"),
        (button_cols[3], "Sweden", "sweden"),
    ]:
        with col:
            if st.button(country_label, use_container_width=True, key=f"quick_{country_value}"):
                st.session_state["quick_country"] = country_value
                st.session_state["page_override"] = "Country Analysis"

    # If a quick country was chosen, override to Country Analysis
    if st.session_state.get("page_override"):
        st.session_state["page"] = st.session_state["page_override"]
        st.session_state["page_override"] = None

    page = st.session_state.get("page", "Overview")
    
    # Route to page
    if page == "Overview":
        show_overview_page()
    elif page == "Country Analysis":
        show_country_page()
    elif page == "Topic Analysis":
        show_topic_analysis_page()


if __name__ == "__main__":
    main()
