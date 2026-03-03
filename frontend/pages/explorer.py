"""Explorer page layout."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from media_helpers import consolidate_outlets
from pages.footer import render_footer_bar
from services.api import (
    fetch_articles_over_time,
    fetch_articles_over_time_by_outlet,
    fetch_categories,
    fetch_categories_over_time,
    fetch_concentration_metrics,
    fetch_overview,
    fetch_partisan_mix,
    fetch_topic_similarity,
    fetch_top_outlets,
)

COUNTRIES = ["denmark", "sweden", "norway", "finland"]
MODE_COMPARE = "Compare Countries"
MODE_DEEP_DIVE = "Country Deep Dive"

COUNTRY_COLORS = {
    "denmark": "#C8102E",
    "sweden": "#FECC00",
    "norway": "#87CEEB",
    "finland": "#003580",
}


def normalize_explorer_mode(mode: str | None) -> str:
    if mode in {MODE_COMPARE, MODE_DEEP_DIVE}:
        return mode
    return MODE_COMPARE


def normalize_country(country: str | None) -> str:
    if country in COUNTRIES:
        return country
    return "denmark"


def deep_dive_view_options() -> list[str]:
    return ["Total Count", "Separate Outlets", "Partisan Accumulated", "Topics Over Time"]


def topics_metric_transform(df: pd.DataFrame, mode: str) -> tuple[pd.DataFrame, str]:
    """Transform topic counts for chart mode."""
    if df.empty:
        return df, "Articles"
    if mode == "Share of Outlet Topics (%)":
        total_per_outlet = df.groupby("outlet")["count"].transform("sum")
        df = df.copy()
        df["value"] = (df["count"] / total_per_outlet * 100).round(2)
        return df, "Share (%)"
    df = df.copy()
    df["value"] = df["count"]
    return df, "Articles"


def _wrap_two_line_label(label: str) -> str:
    """Wrap long category labels into max two lines for x-axis readability."""
    text = str(label or "").strip()
    if len(text) <= 16:
        return text
    if " & " in text:
        left, right = text.split(" & ", 1)
        return f"{left} &<br>{right}"
    words = text.split()
    if len(words) <= 2:
        return text
    split_at = len(words) // 2
    return f"{' '.join(words[:split_at])}<br>{' '.join(words[split_at:])}"


def _matrix_records_to_df(records: list[dict], entities: list[str]) -> pd.DataFrame:
    """Convert pairwise records to symmetric matrix."""
    if not entities:
        return pd.DataFrame()
    matrix = pd.DataFrame(0.0, index=entities, columns=entities)
    for entity in entities:
        matrix.loc[entity, entity] = 1.0
    for row in records or []:
        a = row.get("entity_a")
        b = row.get("entity_b")
        value = float(row.get("value", 0.0))
        if a in matrix.index and b in matrix.columns:
            matrix.loc[a, b] = value
            matrix.loc[b, a] = value
    return matrix


def _plot(fig: go.Figure) -> None:
    """Render plotly chart with zoom-friendly config."""
    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"scrollZoom": True, "responsive": True, "displaylogo": False},
    )


def _year_bounds(overview: dict | None) -> tuple[int, int]:
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
    return year_min, year_max


def _default_year_range(year_min: int, year_max: int) -> tuple[int, int]:
    """Prefer 2016-2026 defaults while respecting available bounds."""
    default_start = max(year_min, 2016)
    default_end = min(year_max, 2026)
    if default_end < default_start:
        return year_min, year_max
    return default_start, default_end


def _inject_explorer_styles() -> None:
    st.markdown(
        """
        <style>
        .explorer-control-bar {
            position: sticky;
            top: 76px;
            z-index: 980;
            background: rgba(248, 251, 248, 0.95);
            border: 1px solid var(--color-border);
            border-radius: 10px;
            padding: 10px 12px 2px 12px;
            margin-bottom: 14px;
            backdrop-filter: blur(6px);
        }
        .explorer-note {
            color: var(--color-text-muted);
            font-size: 0.9rem;
            margin-top: 2px;
        }
        /* Keep Plotly charts flush inside Streamlit containers on Explorer. */
        .stPlotlyChart {
            background: transparent !important;
            border: 0 !important;
            padding: 0 !important;
            overflow: hidden !important;
        }
        .stPlotlyChart > div,
        .stPlotlyChart .js-plotly-plot,
        .stPlotlyChart .plot-container,
        .stPlotlyChart .svg-container {
            width: 100% !important;
            max-width: 100% !important;
            overflow: hidden !important;
        }
        /* Make selected outlet tags in multiselect use green instead of red. */
        div[data-testid="stMultiSelect"] [data-baseweb="tag"] {
            background-color: rgba(46, 125, 50, 0.10) !important;
            border: 1px solid #2E7D32 !important;
            color: #1B5E20 !important;
        }
        div[data-testid="stMultiSelect"] [data-baseweb="tag"] span {
            color: #1B5E20 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_global_country_kpis(overview: dict | None) -> None:
    by_country = (overview or {}).get("by_country", {})
    if not by_country:
        return

    with st.container():
        top_left, top_right = st.columns(2)
        with top_left:
            st.markdown(
                f"<div style='padding:4px 2px;'><div style='font-size:13px; color: var(--color-text-muted);'>Denmark</div>"
                f"<div style='font-size:28px; color: var(--color-text); font-weight:600; line-height:1.1;'>{int(by_country.get('denmark', 0)):,}</div></div>",
                unsafe_allow_html=True,
            )
        with top_right:
            st.markdown(
                f"<div style='padding:4px 2px;'><div style='font-size:13px; color: var(--color-text-muted);'>Sweden</div>"
                f"<div style='font-size:28px; color: var(--color-text); font-weight:600; line-height:1.1;'>{int(by_country.get('sweden', 0)):,}</div></div>",
                unsafe_allow_html=True,
            )

        bottom_left, bottom_right = st.columns(2)
        with bottom_left:
            st.markdown(
                f"<div style='padding:4px 2px;'><div style='font-size:13px; color: var(--color-text-muted);'>Norway</div>"
                f"<div style='font-size:28px; color: var(--color-text); font-weight:600; line-height:1.1;'>{int(by_country.get('norway', 0)):,}</div></div>",
                unsafe_allow_html=True,
            )
        with bottom_right:
            st.markdown(
                f"<div style='padding:4px 2px;'><div style='font-size:13px; color: var(--color-text-muted);'>Finland</div>"
                f"<div style='font-size:28px; color: var(--color-text); font-weight:600; line-height:1.1;'>{int(by_country.get('finland', 0)):,}</div></div>",
                unsafe_allow_html=True,
            )


def _render_outlets_table(country: str, date_from: str, date_to: str) -> None:
    outlets_data = fetch_top_outlets(country=country, date_from=date_from, date_to=date_to, limit=300)
    if not outlets_data or not outlets_data.get("data"):
        st.info("No outlet data available for this selection.")
        return
    df_outlets = pd.DataFrame(consolidate_outlets(outlets_data["data"]))
    st.dataframe(
        df_outlets[["domain", "partisan", "count"]].style.format({"count": "{:,}"}),
        use_container_width=True,
        hide_index=True,
        column_config={"domain": "Domain", "partisan": "Partisanship", "count": "Articles"},
    )


def _render_categories_table(country: str) -> None:
    categories_data = fetch_categories(country=country, partisan=None)
    if not categories_data or not categories_data.get("data"):
        st.info("No category data available for this selection.")
        return
    df_cat = pd.DataFrame(categories_data["data"]).sort_values("count", ascending=False).head(10)
    total = df_cat["count"].sum() or 1
    df_cat["percentage"] = (df_cat["count"] / total * 100).round(1)
    st.dataframe(
        df_cat[["category", "count", "percentage"]].style.format(
            {"count": "{:,}", "percentage": "{:.1f}%"}
        ),
        use_container_width=True,
        hide_index=True,
        column_config={"category": "Category", "count": "Articles", "percentage": "Percentage"},
    )


def _render_compare_mode(overview: dict | None) -> None:
    year_min, year_max = _year_bounds(overview)
    default_year_from, default_year_to = _default_year_range(year_min, year_max)

    st.subheader("Articles Over Time by Country")
    c1, c2, c3 = st.columns([1, 1, 1.4])
    with c1:
        granularity = st.selectbox(
            "Time Granularity",
            options=["Year", "Month", "Week"],
            index=1,
            key="cmp_granularity",
        )
    with c2:
        partisan_filter = st.selectbox(
            "Filter by Partisan",
            options=[None, "Right", "Left", "Other"],
            format_func=lambda x: "All" if x is None else x,
            key="cmp_partisan",
        )
    with c3:
        year_from, year_to = st.slider(
            "Year range",
            min_value=year_min,
            max_value=year_max,
            value=(default_year_from, default_year_to),
            step=1,
            key="cmp_year_range",
        )

    date_from = f"{year_from}-01-01"
    date_to = f"{year_to}-12-31"

    with st.container(border=True):
        fig = go.Figure()
        for ctry in COUNTRIES:
            time_data = fetch_articles_over_time(
                country=ctry,
                partisan=partisan_filter,
                granularity=granularity.lower(),
                date_from=date_from,
                date_to=date_to,
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
                        name=ctry.capitalize(),
                        line=dict(color=COUNTRY_COLORS.get(ctry, "#1f77b4"), width=2),
                        marker=dict(size=6),
                    )
                )
        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Articles",
            height=430,
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.08, xanchor="center", x=0.5),
            title="",
        )
        _plot(fig)

    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.subheader("Partisanship Mix by Country")
            partisan_rows = []
            for ctry in COUNTRIES:
                mix = fetch_partisan_mix(country=ctry, date_from=date_from, date_to=date_to)
                if mix and mix.get("data"):
                    for row in mix["data"]:
                        partisan_rows.append(
                            {
                                "country": ctry.capitalize(),
                                "partisan": row.get("partisan"),
                                "share": float(row.get("share", 0.0)) * 100.0,
                            }
                        )
            if partisan_rows:
                df_partisan = pd.DataFrame(partisan_rows)
                # Re-normalize displayed categories so each country sums to 100%.
                country_totals = df_partisan.groupby("country")["share"].transform("sum")
                df_partisan["share"] = (df_partisan["share"] / country_totals * 100.0).fillna(0.0)
                fig_partisan = px.bar(
                    df_partisan,
                    x="share",
                    y="country",
                    color="partisan",
                    orientation="h",
                    color_discrete_map={"Right": "#0066CC", "Left": "#DC143C", "Other": "#2ca02c"},
                )
                fig_partisan.update_layout(
                    xaxis_title="Share (%)",
                    yaxis_title="",
                    height=430,
                    xaxis=dict(range=[0, 100]),
                    barmode="stack",
                    legend=dict(
                        orientation="h",
                        yanchor="top",
                        y=-0.2,
                        xanchor="center",
                        x=0.5,
                        title_text="Partisan",
                        font=dict(size=14),
                        title_font=dict(size=14),
                    ),
                    margin=dict(b=80),
                )
                _plot(fig_partisan)
            else:
                st.info("No partisan data available for this selection.")
    with right:
        with st.container(border=True):
            st.subheader("Outlet Concentration")
            st.caption(
                "ENP (Effective Number of Outlets) summarizes outlet concentration for each country in the selected period; higher ENP means publication volume is spread across more outlets."
            )
            concentration_rows = []
            for ctry in COUNTRIES:
                metrics = fetch_concentration_metrics(
                    country=ctry,
                    partisan=partisan_filter,
                    date_from=date_from,
                    date_to=date_to,
                    top_n=5,
                )
                if metrics:
                    concentration_rows.append(
                        {
                            "country": ctry.capitalize(),
                            "enp": float(metrics.get("enp", 0.0)),
                        }
                    )
            if concentration_rows:
                df_concentration = pd.DataFrame(concentration_rows)
                fig_concentration = px.bar(
                    df_concentration,
                    x="country",
                    y="enp",
                    color="country",
                    color_discrete_map={
                        "Denmark": COUNTRY_COLORS["denmark"],
                        "Sweden": COUNTRY_COLORS["sweden"],
                        "Norway": COUNTRY_COLORS["norway"],
                        "Finland": COUNTRY_COLORS["finland"],
                    },
                )
                fig_concentration.update_layout(
                    height=430,
                    yaxis_title="ENP",
                    xaxis_title="",
                    showlegend=False,
                )
                fig_concentration.update_traces(texttemplate="%{y:.2f}", textposition="outside")
                _plot(fig_concentration)
            else:
                st.info("No concentration data available for this selection.")

    with st.container(border=True):
        st.subheader("Topics Over Time (All Countries)")
        topic_data = fetch_categories_over_time(
            country=None,
            partisan=partisan_filter,
            granularity=granularity.lower(),
            date_from=date_from,
            date_to=date_to,
            limit=8,
        )
        if topic_data and topic_data.get("data"):
            df_topics = pd.DataFrame(topic_data["data"])
            if not df_topics.empty and {"date", "category", "count"}.issubset(df_topics.columns):
                df_topics["date"] = pd.to_datetime(df_topics["date"], errors="coerce")
                df_topics = df_topics.sort_values("date")
                fig_topics = go.Figure()
                for topic in df_topics["category"].dropna().unique():
                    rows = df_topics[df_topics["category"] == topic]
                    fig_topics.add_trace(
                        go.Scatter(
                            x=rows["date"],
                            y=rows["count"],
                            mode="lines",
                            name=str(topic),
                            line=dict(width=2),
                        )
                    )
                fig_topics.update_layout(
                    title="",
                    xaxis_title="Date",
                    yaxis_title="Articles",
                    height=430,
                    hovermode="x unified",
                    legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),
                    margin=dict(b=90),
                )
                _plot(fig_topics)
            else:
                st.info("No topic data available for this selection.")
        else:
            st.info("No topic data available for this selection.")

    with st.container(border=True):
        st.subheader("Agenda Similarity (Countries)")
        st.caption(
            "This chart compares agenda similarity using topic distributions, not full-text semantics. "
            "Cosine Similarity: higher values indicate more similar relative topic emphasis. "
            "It is computed from normalized topic-share vectors built from article category counts in the selected filters."
        )
        similarity = fetch_topic_similarity(
            level="country",
            partisan=partisan_filter,
            date_from=date_from,
            date_to=date_to,
            limit_topics=12,
        )
        if similarity and similarity.get("entities"):
            entities = [str(e).capitalize() for e in similarity.get("entities", [])]
            raw_records = similarity.get("cosine", [])
            records = []
            for row in raw_records:
                records.append(
                    {
                        "entity_a": str(row.get("entity_a", "")).capitalize(),
                        "entity_b": str(row.get("entity_b", "")).capitalize(),
                        "value": float(row.get("value", 0.0)),
                    }
                )
            matrix = _matrix_records_to_df(records, entities)
            if not matrix.empty:
                zmin = 0.8
                zmax = 1.0
                colorscale = "Blues"
                heatmap = go.Figure(
                    data=go.Heatmap(
                        z=matrix.values,
                        x=matrix.columns,
                        y=matrix.index,
                        colorscale=colorscale,
                        zmin=zmin,
                        zmax=zmax,
                    )
                )
                heatmap.update_layout(
                    height=420,
                    xaxis_title="",
                    yaxis_title="",
                    margin=dict(t=20, b=20, l=20, r=20),
                )
                _plot(heatmap)
            else:
                st.info("No similarity matrix available for this selection.")
        else:
            st.info("No similarity data available for this selection.")


def _render_deep_dive_mode(overview: dict | None) -> None:
    year_min, year_max = _year_bounds(overview)
    default_year_from, default_year_to = _default_year_range(year_min, year_max)
    default_country = normalize_country(st.session_state.get("quick_country"))

    st.markdown("<div class='explorer-control-bar'>", unsafe_allow_html=True)
    st.markdown(
        "<div class='explorer-note'>Focus on one country and inspect outlet-level and partisan dynamics over time.</div>",
        unsafe_allow_html=True,
    )
    top1, top2 = st.columns([1.2, 1.8])
    with top1:
        country = st.selectbox(
            "Country",
            options=COUNTRIES,
            index=COUNTRIES.index(default_country),
            format_func=lambda x: x.capitalize(),
            key="deep_country",
        )
    with top2:
        view_type = st.radio(
            "View",
            options=deep_dive_view_options(),
            index=0,
            horizontal=True,
            key="deep_view_type",
        )
    c1, c2, c3 = st.columns([1, 1, 1.4])
    with c1:
        granularity = st.selectbox(
            "Time Granularity",
            options=["Year", "Month", "Week"],
            index=1,
            key="deep_granularity",
        )
    with c2:
        partisan_filter = st.selectbox(
            "Filter by Partisan",
            options=[None, "Right", "Left", "Other"],
            format_func=lambda x: "All" if x is None else x,
            key="deep_partisan",
        )
    with c3:
        year_from, year_to = st.slider(
            "Year range",
            min_value=year_min,
            max_value=year_max,
            value=(default_year_from, default_year_to),
            step=1,
            key="deep_year_range",
        )
    st.markdown("</div>", unsafe_allow_html=True)

    st.session_state["quick_country"] = country
    date_from = f"{year_from}-01-01"
    date_to = f"{year_to}-12-31"

    with st.container(border=True):
        st.subheader(f"Articles Over Time ({country.capitalize()})")
        if view_type == "Total Count":
            time_data = fetch_articles_over_time(
                country=country,
                partisan=partisan_filter,
                granularity=granularity.lower(),
                date_from=date_from,
                date_to=date_to,
            )
            if time_data and time_data.get("data"):
                df_time = pd.DataFrame(time_data["data"])
                df_time["date"] = pd.to_datetime(df_time["date"], errors="coerce")
                df_time = df_time.sort_values("date")
                fig = px.line(df_time, x="date", y="count", markers=True)
                fig.update_traces(line=dict(width=3, color="#1f77b4"), marker=dict(size=8))
                fig.update_layout(
                    title="",
                    xaxis_title="Date",
                    yaxis_title="Articles",
                    height=420,
                    hovermode="x unified",
                )
                _plot(fig)
            else:
                st.info("No data available for selected filters.")
        elif view_type == "Separate Outlets":
            outlets_list = fetch_top_outlets(
                country=country, partisan=partisan_filter, date_from=date_from, date_to=date_to, limit=20
            )
            selected_outlets = []
            if outlets_list and outlets_list.get("data"):
                outlet_options = [o["domain"] for o in outlets_list["data"]]
                selected_outlets = st.multiselect(
                    "Select Outlets",
                    options=outlet_options,
                    default=outlet_options[:5] if len(outlet_options) >= 5 else outlet_options,
                    key="deep_selected_outlets",
                )
            if not selected_outlets:
                st.info("Please select at least one outlet to display.")
            else:
                outlet_time_data = fetch_articles_over_time_by_outlet(
                    country=country,
                    outlets=selected_outlets,
                    granularity=granularity.lower(),
                    date_from=date_from,
                    date_to=date_to,
                )
                if outlet_time_data and outlet_time_data.get("data"):
                    df_outlets = pd.DataFrame(outlet_time_data["data"])
                    if not df_outlets.empty and {"date", "outlet", "count"}.issubset(df_outlets.columns):
                        df_outlets["date"] = pd.to_datetime(df_outlets["date"], errors="coerce")
                        df_outlets = df_outlets.sort_values("date")
                        fig = go.Figure()
                        colors_list = px.colors.qualitative.Set3
                        for idx, outlet in enumerate(selected_outlets):
                            outlet_rows = df_outlets[df_outlets["outlet"] == outlet.lower()]
                            if outlet_rows.empty:
                                continue
                            fig.add_trace(
                                go.Scatter(
                                    x=outlet_rows["date"],
                                    y=outlet_rows["count"],
                                    mode="lines+markers",
                                    name=outlet,
                                    line=dict(color=colors_list[idx % len(colors_list)], width=2),
                                    marker=dict(size=6),
                                )
                            )
                        fig.update_layout(
                            title="",
                            xaxis_title="Date",
                            yaxis_title="Articles",
                            height=420,
                            hovermode="x unified",
                            legend=dict(orientation="h", yanchor="bottom", y=1.08, xanchor="center", x=0.5),
                        )
                        _plot(fig)
                    else:
                        st.info("No data available for selected outlets.")
                else:
                    st.info("No data available for selected outlets.")
        elif view_type == "Partisan Accumulated":
            fig = go.Figure()
            partisan_colors = {"Right": "#0066CC", "Left": "#DC143C", "Other": "#2ca02c"}
            for partisan in ["Right", "Left", "Other"]:
                time_data = fetch_articles_over_time(
                    country=country,
                    partisan=partisan,
                    granularity=granularity.lower(),
                    date_from=date_from,
                    date_to=date_to,
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
                            name=partisan,
                            line=dict(color=partisan_colors[partisan], width=3),
                            marker=dict(size=8),
                        )
                    )
            fig.update_layout(
                title="",
                xaxis_title="Date",
                yaxis_title="Articles",
                height=420,
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.08, xanchor="center", x=0.5),
            )
            _plot(fig)
        else:
            topic_data = fetch_categories_over_time(
                country=country,
                partisan=partisan_filter,
                granularity=granularity.lower(),
                date_from=date_from,
                date_to=date_to,
                limit=8,
            )
            if topic_data and topic_data.get("data"):
                df_topics = pd.DataFrame(topic_data["data"])
                if not df_topics.empty and {"date", "category", "count"}.issubset(df_topics.columns):
                    df_topics["date"] = pd.to_datetime(df_topics["date"], errors="coerce")
                    df_topics = df_topics.sort_values("date")
                    fig = go.Figure()
                    for topic in df_topics["category"].dropna().unique():
                        rows = df_topics[df_topics["category"] == topic]
                        fig.add_trace(
                            go.Scatter(
                                x=rows["date"],
                                y=rows["count"],
                                mode="lines",
                                name=str(topic),
                                line=dict(width=2),
                            )
                        )
                    fig.update_layout(
                        title="",
                        xaxis_title="Date",
                        yaxis_title="Articles",
                        height=420,
                        hovermode="x unified",
                        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),
                        margin=dict(b=90),
                    )
                    _plot(fig)
                else:
                    st.info("No topic data available for this selection.")
            else:
                st.info("No topic data available for this selection.")

    with st.container(border=True):
        st.subheader("Topics by Media")
        st.caption("Compare agenda profiles across outlets in the selected country and period.")
        outlet_options_data = fetch_top_outlets(
            country=country,
            partisan=partisan_filter,
            date_from=date_from,
            date_to=date_to,
            limit=20,
        )
        outlet_options = []
        if outlet_options_data and outlet_options_data.get("data"):
            outlet_options = [row.get("domain") for row in outlet_options_data["data"] if row.get("domain")]

        selected_media = st.multiselect(
            "Select Media Outlets",
            options=outlet_options,
            default=outlet_options[:3] if len(outlet_options) >= 3 else outlet_options,
            key="deep_topics_by_media_outlets",
        )
        topics_value_mode = st.radio(
            "Metric",
            options=["Absolute Topic Counts", "Share of Outlet Topics (%)"],
            index=0,
            horizontal=True,
            key="deep_topics_by_media_metric",
        )

        if not selected_media:
            st.info("Select at least one outlet to compare topic profiles.")
        else:
            topic_rows = []
            for outlet in selected_media:
                outlet_topics = fetch_categories_over_time(
                    country=country,
                    partisan=partisan_filter,
                    outlets=[outlet],
                    granularity=granularity.lower(),
                    date_from=date_from,
                    date_to=date_to,
                    limit=8,
                )
                if not outlet_topics or not outlet_topics.get("data"):
                    continue
                df_outlet_topics = pd.DataFrame(outlet_topics["data"])
                if df_outlet_topics.empty or not {"category", "count"}.issubset(df_outlet_topics.columns):
                    continue
                aggregated = (
                    df_outlet_topics.groupby("category", as_index=False)["count"]
                    .sum()
                    .sort_values("count", ascending=False)
                )
                for _, row in aggregated.iterrows():
                    topic_rows.append(
                        {
                            "outlet": outlet,
                            "category": row["category"],
                            "count": int(row["count"]),
                        }
                    )

            if topic_rows:
                df_topics_by_media = pd.DataFrame(topic_rows)
                available_topics = (
                    df_topics_by_media.groupby("category", as_index=False)["count"]
                    .sum()
                    .sort_values("count", ascending=False)["category"]
                    .tolist()
                )
                default_topics = available_topics[:10]
                selected_topics = st.multiselect(
                    "Select Topics",
                    options=available_topics,
                    default=default_topics,
                    key="deep_topics_by_media_topics",
                )
                if selected_topics:
                    df_topics_by_media = df_topics_by_media[
                        df_topics_by_media["category"].isin(selected_topics)
                    ].copy()
                else:
                    df_topics_by_media = df_topics_by_media.iloc[0:0]

            if not topic_rows or df_topics_by_media.empty:
                st.info("No topic-by-media data available for this selection.")
            else:
                df_topics_by_media, y_label = topics_metric_transform(
                    df_topics_by_media,
                    mode=topics_value_mode,
                )
                df_topics_by_media["category_label"] = df_topics_by_media["category"].apply(_wrap_two_line_label)
                fig_topics_media = px.bar(
                    df_topics_by_media,
                    x="category_label",
                    y="value",
                    color="outlet",
                    barmode="group",
                )
                fig_topics_media.update_layout(
                    title="",
                    xaxis_title="Topic",
                    yaxis_title=y_label,
                    height=420,
                    legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5),
                    margin=dict(t=90, b=130),
                )
                fig_topics_media.update_xaxes(tickangle=0, automargin=True)
                _plot(fig_topics_media)

    with st.container(border=True):
        st.subheader("Agenda Similarity (Outlets)")
        st.caption(
            "This chart compares agenda similarity using topic distributions, not full-text semantics. "
            "Cosine Similarity: higher values indicate more similar relative topic emphasis. "
            "It is computed from normalized topic-share vectors built from article category counts in the selected filters."
        )
        similarity_outlet_options_data = fetch_top_outlets(
            country=country,
            partisan=partisan_filter,
            date_from=date_from,
            date_to=date_to,
            limit=12,
        )
        similarity_outlet_options = []
        if similarity_outlet_options_data and similarity_outlet_options_data.get("data"):
            similarity_outlet_options = [
                row.get("domain") for row in similarity_outlet_options_data["data"] if row.get("domain")
            ]
        selected_similarity_outlets = st.multiselect(
            "Select Outlets for Similarity",
            options=similarity_outlet_options,
            default=similarity_outlet_options[:5] if len(similarity_outlet_options) >= 5 else similarity_outlet_options,
            key="deep_similarity_outlets",
        )
        if len(selected_similarity_outlets) < 2:
            st.info("Select at least two outlets to compute pairwise similarity.")
        else:
            similarity = fetch_topic_similarity(
                level="outlet",
                country=country,
                partisan=partisan_filter,
                outlets=selected_similarity_outlets,
                date_from=date_from,
                date_to=date_to,
                limit_topics=12,
            )
            if similarity and similarity.get("entities"):
                entities = [str(e) for e in similarity.get("entities", [])]
                raw_records = similarity.get("cosine", [])
                records = [
                    {
                        "entity_a": str(row.get("entity_a", "")),
                        "entity_b": str(row.get("entity_b", "")),
                        "value": float(row.get("value", 0.0)),
                    }
                    for row in raw_records
                ]
                matrix = _matrix_records_to_df(records, entities)
                if not matrix.empty:
                    heatmap = go.Figure(
                        data=go.Heatmap(
                            z=matrix.values,
                            x=matrix.columns,
                            y=matrix.index,
                            colorscale="Blues",
                            zmin=0.5,
                            zmax=1.0,
                        )
                    )
                    heatmap.update_layout(
                        height=420,
                        xaxis_title="",
                        yaxis_title="",
                        margin=dict(t=20, b=20, l=20, r=20),
                    )
                    _plot(heatmap)
                else:
                    st.info("No similarity matrix available for selected outlets.")
            else:
                st.info("No similarity data available for selected outlets.")

    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.subheader(f"Outlets ({country.capitalize()})")
            _render_outlets_table(country=country, date_from=date_from, date_to=date_to)
    with right:
        with st.container(border=True):
            st.subheader(f"News Categories ({country.capitalize()})")
            _render_categories_table(country=country)


def show_explorer_page() -> None:
    """Show comparative Explorer with explicit mode separation."""
    _inject_explorer_styles()

    st.markdown('<h1 class="main-header">Explorer</h1>', unsafe_allow_html=True)
    overview = fetch_overview()

    intro_col, kpi_col = st.columns([1.6, 1.0])
    with intro_col:
        st.markdown(
            "<div class='subtle' style='font-size:1.15rem;'>The Explorer provides a high-level overview of the alternative news media content. "
            "Start with all countries for a broad comparison, or select a country to see outlets and "
            "publishing activity over time. Adjust filters to narrow the view.</div>",
            unsafe_allow_html=True,
        )
    with kpi_col:
        _render_global_country_kpis(overview)

    mode = normalize_explorer_mode(st.session_state.get("explorer_mode"))
    mode = st.radio(
        "Explorer Mode",
        options=[MODE_COMPARE, MODE_DEEP_DIVE],
        index=0 if mode == MODE_COMPARE else 1,
        horizontal=True,
        key="explorer_mode",
    )
    st.divider()

    if mode == MODE_COMPARE:
        _render_compare_mode(overview)
    else:
        _render_deep_dive_mode(overview)

    render_footer_bar()
