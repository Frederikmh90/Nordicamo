from __future__ import annotations

import streamlit as st

from pages.footer import render_footer_bar

from media_helpers import (
    consolidate_outlets,
    filter_outlets,
    normalize_domain,
    select_latest_articles,
)
from services.api import (
    fetch_articles_search,
    fetch_full_enhanced_overview,
    fetch_outlet_profile,
    fetch_top_outlets,
)


def show_media_page() -> None:
    """Show media directory page."""
    st.markdown('<h1 class="main-header">Media Directory</h1>', unsafe_allow_html=True)
    st.markdown(
        "<div class='subtle'>A searchable directory of alternative media outlets across the Nordics.</div>",
        unsafe_allow_html=True,
    )

    full_overview = fetch_full_enhanced_overview()
    kpi_source = full_overview

    outlets_data = fetch_top_outlets(limit=1000)
    outlets = outlets_data.get("data", []) if outlets_data else []
    outlets = consolidate_outlets(outlets)

    total_outlets = kpi_source.get("total_outlets", len(outlets)) if kpi_source else len(outlets)
    total_articles = kpi_source.get("total_articles", 0) if kpi_source else sum(
        o.get("count", 0) for o in outlets
    )
    avg_articles = kpi_source.get("avg_articles_per_outlet") if kpi_source else None
    if avg_articles is None:
        avg_articles = int(total_articles / total_outlets) if total_outlets else 0
    nordic_countries = {"denmark", "finland", "norway", "sweden"}
    outlet_countries = {
        str(o.get("country")).strip().lower()
        for o in outlets
        if o.get("country")
    }
    countries = outlet_countries.intersection(nordic_countries) or outlet_countries

    stat_cols = st.columns(4)
    stat_values = [
        ("Total Media", f"{total_outlets:,}"),
        ("Countries Represented", f"{len(countries)}"),
        ("Total Articles", f"{total_articles:,}"),
        ("Articles per Outlet", f"{avg_articles:,.0f}"),
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
        selected_domain = normalize_domain(selected_domain)
        profile = fetch_outlet_profile(selected_domain)
        if profile:
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            st.markdown(
                f"<div class='section-title'>{profile.get('domain') or profile.get('outlet_name')}</div>",
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
            domain = normalize_domain(profile.get("domain") or selected_domain)
            latest_response = fetch_articles_search(outlets=[domain], limit=5, offset=0)
            latest_articles = select_latest_articles(latest_response, limit=5)
            if latest_articles:
                st.markdown("<div class='section-title'>Latest Articles</div>", unsafe_allow_html=True)
                for article in latest_articles:
                    title = article.get("title") or "Untitled"
                    date = article.get("date") or "Unknown date"
                    url = article.get("url")
                    if url:
                        st.markdown(
                            f"- [{title}]({url}) <span class='subtle'>({date})</span>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(f"- {title} ({date})")
            else:
                st.markdown("<div class='subtle'>No recent articles found.</div>", unsafe_allow_html=True)
            if st.button("Back", use_container_width=False):
                try:
                    st.query_params.pop("media", None)
                    st.rerun()
                except Exception:
                    st.experimental_set_query_params(page="Media")
            st.divider()

    # Removed summary caption to reduce clutter

    if not filtered:
        st.info("No media outlets match your search.")
        return

    cols = st.columns(3)
    for idx, outlet in enumerate(filtered):
        col = cols[idx % 3]
        name = outlet.get("outlet_name") or outlet.get("domain") or "Unknown outlet"
        country = outlet.get("country") or outlet.get("country_code") or "Unknown"
        country = country.lower() if isinstance(country, str) else country
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
                    st.query_params["media"] = normalize_domain(outlet.get("domain") or "")
                    st.rerun()
                except Exception:
                    st.experimental_set_query_params(page="Media", media=outlet.get("domain"))
    render_footer_bar()
