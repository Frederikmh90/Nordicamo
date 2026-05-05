from __future__ import annotations

import html

import streamlit as st

from pages.footer import render_footer_bar

from media_helpers import (
    best_article_count,
    consolidate_outlets,
    filter_outlets,
    latest_article_dates_by_domain,
    normalize_domain,
    select_latest_articles,
)
from services.api import (
    fetch_articles_search,
    fetch_full_enhanced_overview,
    fetch_outlet_profile,
    fetch_top_outlets,
)
from ui_labels import AVG_ARTICLES_PER_OUTLET_LABEL


COUNTRY_FILTER_OPTIONS = ["All", "Denmark", "Finland", "Norway", "Sweden"]


def _normalize_media_country_filter(value: str | None) -> str:
    if value in COUNTRY_FILTER_OPTIONS:
        return value
    return "All"


def _render_media_country_filter(selected: str) -> str:
    if hasattr(st, "segmented_control"):
        choice = st.segmented_control(
            "Filter by Country",
            options=COUNTRY_FILTER_OPTIONS,
            default=selected,
            selection_mode="single",
            key="media_country_filter",
            label_visibility="collapsed",
        )
        return _normalize_media_country_filter(choice)
    choice = st.radio(
        "Filter by Country",
        options=COUNTRY_FILTER_OPTIONS,
        index=COUNTRY_FILTER_OPTIONS.index(selected),
        horizontal=True,
        key="media_country_filter",
        label_visibility="collapsed",
    )
    return _normalize_media_country_filter(choice)


def _filter_outlets_by_country(outlets: list[dict], selected_country: str) -> list[dict]:
    if selected_country == "All":
        return outlets
    target = selected_country.lower()
    return [
        outlet
        for outlet in outlets
        if str(outlet.get("country") or outlet.get("country_code") or "").strip().lower() == target
    ]


def show_media_page() -> None:
    """Show media directory page."""
    st.markdown('<h1 class="main-header">Media Archive</h1>', unsafe_allow_html=True)
    st.markdown(
        "<div class='subtle'>Search outlet profiles and recent articles from the observatory archive.</div>",
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
        (AVG_ARTICLES_PER_OUTLET_LABEL, f"{avg_articles:,.0f}"),
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
    selected_country = _normalize_media_country_filter(
        st.session_state.get("media_country_filter")
    )
    selected_country = _render_media_country_filter(selected_country)
    filtered = _filter_outlets_by_country(filtered, selected_country)
    latest_dates = latest_article_dates_by_domain(fetch_articles_search(limit=500, offset=0))

    selected_domain = None
    selected_profile_domain = None
    selected_profile_articles = None
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
            profile_domain = normalize_domain(profile.get("domain") or selected_domain)
            outlet_fallback = next(
                (outlet for outlet in outlets if normalize_domain(outlet.get("domain") or "") == profile_domain),
                {},
            )
            profile_country = profile.get("country") or outlet_fallback.get("country") or "Unknown country"
            profile_partisan = profile.get("partisan") or outlet_fallback.get("partisan") or "Orientation unknown"
            latest_response = fetch_articles_search(outlets=[profile_domain], limit=5, offset=0)
            profile_articles = best_article_count(
                profile.get("total_articles"),
                outlet_fallback.get("count"),
                latest_response.get("total") if isinstance(latest_response, dict) else 0,
            )
            selected_profile_domain = profile_domain
            selected_profile_articles = profile_articles
            latest_articles = select_latest_articles(latest_response, limit=5)
            latest_date = str(latest_articles[0].get("date"))[:10] if latest_articles else "Not in latest sample"
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            st.markdown(
                f"<div class='section-title'>{html.escape(profile.get('outlet_name') or profile_domain or selected_domain)}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"""
                <div class='media-pill-row'>
                    <span class='media-pill'>{html.escape(str(profile_country)).capitalize()}</span>
                    <span class='media-pill'>{html.escape(str(profile_partisan))}</span>
                    <span class='media-pill'>{int(profile_articles):,} articles</span>
                    <span class='media-pill'>Latest: {html.escape(latest_date)}</span>
                </div>
                <div class='subtle' style='margin-top:6px;'>Outlet profile for archive browsing and case selection.</div>
                """,
                unsafe_allow_html=True,
            )
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
        domain = normalize_domain(outlet.get("domain") or "")
        partisan = outlet.get("partisan") or "Orientation unknown"
        count = best_article_count(outlet.get("count", 0))
        if selected_profile_domain == domain:
            count = best_article_count(count, selected_profile_articles)
        latest_date = latest_dates.get(domain, "not in latest sample")
        with col:
            st.markdown(
                f"""
                <div class="media-card">
                    <div>
                        <h3>{html.escape(str(name))}</h3>
                        <div class="media-domain">{html.escape(domain)}</div>
                        <div class="media-pill-row">
                            <span class="media-pill">{html.escape(str(country).capitalize())}</span>
                            <span class="media-pill">{html.escape(str(partisan))}</span>
                        </div>
                        <div class="media-count">{count:,} articles</div>
                        <div class="media-latest">Latest activity: {html.escape(str(latest_date))}</div>
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
