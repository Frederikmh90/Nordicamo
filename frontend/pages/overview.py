"""Overview (landing) page layout."""

import html

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import get_api_base_url
from overview_helpers import format_freshness
from services.api import (
    fetch_articles,
    fetch_articles_over_time,
    fetch_data_freshness,
    fetch_enhanced_overview,
    fetch_overview,
)

API_BASE_URL = get_api_base_url()


@st.cache_data(ttl=300)
def _fetch_latest_articles() -> list[dict]:
    data = fetch_articles(limit=100, offset=0)
    if not data:
        return []
    return data.get("articles", []) or []


def _build_ticker_sample(articles: list[dict]) -> list[dict]:
    if not articles:
        return []

    groups: dict[tuple[str, str], list[dict]] = {}
    for article in articles:
        domain = article.get("domain") or ""
        country = (article.get("country") or "").lower()
        if not domain:
            continue
        groups.setdefault((domain, country), []).append(article)

    ordered_groups = sorted(groups.items(), key=lambda item: len(item[1]), reverse=True)
    if not ordered_groups:
        return []

    sample: list[dict] = []
    countries_seen: set[str] = set()
    for (domain, country), items in ordered_groups:
        sample.extend(items[:2])
        if country:
            countries_seen.add(country)
        if len(sample) >= 10 and len(countries_seen) >= 3:
            break

    if len(countries_seen) < 4 or len(sample) < 6:
        for (domain, country), items in ordered_groups:
            if all(item.get("domain") != domain for item in sample):
                sample.append(items[0])
                if country:
                    countries_seen.add(country)
            if len(sample) >= 12 and len(countries_seen) >= 4:
                break

    if len(sample) < 6:
        sample = []
        for items in groups.values():
            sample.extend(items[:1])
        sample = sample[:12]

    return sample


def show_overview_page() -> None:
    """Show overview dashboard page."""
    enhanced_overview = fetch_enhanced_overview()
    freshness = fetch_data_freshness()
    overview = enhanced_overview or fetch_overview()

    def render_kpi(label: str, value: str, subtitle: str | None = None) -> None:
        subtitle_html = (
            f'<div style="font-size:11px; color: var(--color-text-muted); margin-top:4px;">{subtitle}</div>'
            if subtitle
            else ""
        )
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

    articles = _build_ticker_sample(_fetch_latest_articles())
    if articles:
        ticker_items = []
        for article in articles:
            domain = article.get("domain") or "Unknown outlet"
            title = article.get("title") or "Untitled"
            date = (article.get("date") or "")[:10]
            item = f"<strong>{html.escape(domain)}</strong> — {html.escape(title)} ({html.escape(date)})"
            ticker_items.append(f"<span class='news-ticker-item'>{item}</span>")
        ticker_html = "".join(ticker_items)
        st.markdown(
            f"""
            <div class="news-ticker">
                <div class="news-ticker-label">Latest</div>
                <div class="news-ticker-track">
                    <div class="news-ticker-items">{ticker_html}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    hero_left, hero_right = st.columns([2.3, 1.2])
    with hero_left:
        st.markdown(
            "<div class='section-title'>Observatory</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='subtle'>Monitoring of alternative media signals across the Nordic region. Access high-level "
            "comparative analytics (Explorer), engage with the latest content from alternative media outlets (Media) "
            "or get access to current or historical data (Get Access). Enjoy!</div>",
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

    if overview:
        k1, k2, k3, k4, k5 = st.columns(5)
        with k1:
            total_articles = overview.get("total_articles", 0)
            render_kpi("Total Articles", f"{total_articles:,}")
        with k2:
            render_kpi("Outlets", f"{overview.get('total_outlets', 0):,}")
        with k3:
            avg_per_outlet = enhanced_overview.get("avg_articles_per_outlet", 0) if enhanced_overview else 0
            render_kpi("Articles per Outlet", f"{avg_per_outlet:,.0f}")
        with k4:
            coverage_years = enhanced_overview.get("coverage_years") if enhanced_overview else None
            if not coverage_years:
                dr = overview.get("date_range", {})
                earliest = dr.get("earliest") or "N/A"
                latest = dr.get("latest") or "N/A"
                coverage_years = f"{earliest[:4]}-{latest[:4]}" if earliest != "N/A" else "N/A"
            render_kpi("Coverage", f"{coverage_years}")
        with k5:
            growth_rate = enhanced_overview.get("growth_rate_per_year") if enhanced_overview else None
            if growth_rate:
                growth_display = f"+{growth_rate:,.0f}" if growth_rate > 0 else f"{growth_rate:,.0f}"
                render_kpi("Growth Rate", growth_display, "articles/year")
            else:
                render_kpi("Countries", f"{len(overview.get('by_country', {}))}")

    if not overview:
        st.error("Unable to load data. Please check API connection.")
        st.info(f"Trying to connect to: {API_BASE_URL}")
        return

    st.divider()

    st.subheader("Articles Over Time")

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

    col1, col2, col3 = st.columns(3)
    with col1:
        selected_country = st.selectbox(
            "Filter by Country",
            options=[None, "denmark", "sweden", "norway", "finland"],
            format_func=lambda x: "All Countries" if x is None else x.capitalize(),
            help="Select a specific Nordic country or view all countries together",
        )
    with col2:
        selected_partisan = st.selectbox(
            "Filter by Partisan",
            options=[None, "Right", "Left", "Other"],
            format_func=lambda x: "All" if x is None else x,
            help="Political orientation of the media outlet (self-identified or classified)",
        )
    with col3:
        granularity = st.selectbox(
            "Time Granularity",
            options=["Year", "Month", "Week"],
            index=0,
            help="Time period grouping for the time series chart (year, month, or week)",
        )

    if not selected_country:
        fig = go.Figure()
        countries = ["denmark", "sweden", "norway", "finland"]
        colors = {
            "denmark": "#C8102E",
            "sweden": "#FECC00",
            "norway": "#87CEEB",
            "finland": "#003580",
        }

        for country in countries:
            time_data = fetch_articles_over_time(
                country=country,
                partisan=selected_partisan,
                granularity=granularity.lower(),
                date_from=str(date_from) if date_from else None,
                date_to=str(date_to) if date_to else None,
            )

            if time_data and time_data.get("data"):
                df_time = pd.DataFrame(time_data["data"])
                df_time["date"] = pd.to_datetime(df_time["date"], errors="coerce")
                df_time = df_time.sort_values("date")

                fig.add_trace(
                    go.Scatter(
                        x=df_time["date"],
                        y=df_time["count"],
                        mode="lines+markers",
                        name=country.capitalize(),
                        line=dict(color=colors.get(country, "#808080"), width=2),
                        marker=dict(size=6),
                        hovertemplate=(
                            f"<b>{country.capitalize()}</b><br>Date: %{{x}}<br>Articles: %{{y:,}}<extra></extra>"
                        ),
                    )
                )

        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Number of Articles",
            height=450,
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                font=dict(size=12),
            ),
            margin=dict(b=50, t=40, l=50, r=50),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        time_data = fetch_articles_over_time(
            country=selected_country,
            partisan=selected_partisan,
            granularity=granularity.lower(),
            date_from=str(date_from) if date_from else None,
            date_to=str(date_to) if date_to else None,
        )

        if time_data and time_data.get("data"):
            df_time = pd.DataFrame(time_data["data"])
            df_time["date"] = pd.to_datetime(df_time["date"], errors="coerce")
            df_time = df_time.sort_values("date")

            fig = px.line(
                df_time,
                x="date",
                y="count",
                markers=True,
            )
            fig.update_traces(
                line=dict(width=3),
                marker=dict(size=8),
                hovertemplate="<b>Date:</b> %{x}<br><b>Articles:</b> %{y:,}<extra></extra>",
            )
            fig.update_layout(
                xaxis_title="Time",
                yaxis_title="Number of Articles",
                height=450,
                hovermode="x unified",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available for selected filters.")

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class="about-card">
            <h4>What is Nordicamo?</h4>
            <p>Nordicamo provides a comparative view of alternative news media across the Nordic region. The observatory
            combines structured data collection with descriptive analytics so researchers can trace publication patterns,
            outlet concentration, and category shifts over time, then move into deeper qualitative interpretation.</p>
            <div class="about-card-spacer"></div>
            <p>Nordicamo is part of the research project
            <a href='https://ruc.dk/en/forskningsprojekt/alternative-media-and-ideological-counterpublics'
            target='_blank' rel='noopener'>AlterPublics</a> based at
            <a href='https://ruc.dk/en' target='_blank' rel='noopener'>Roskilde University</a> (Denmark) and
            supported by the <a href='https://digitalmedialab.ruc.dk/' target='_blank' rel='noopener'>
            Digital Media Lab</a> (RUC) (thanks!).</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
