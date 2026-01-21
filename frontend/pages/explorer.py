"""Explorer page layout."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from media_helpers import consolidate_outlets
from overview_helpers import compute_lorenz_curve, compute_partisan_shares, compute_top_n_share
from services.api import (
    fetch_articles_over_time,
    fetch_articles_over_time_by_outlet,
    fetch_categories,
    fetch_categories_over_time,
    fetch_overview,
    fetch_top_outlets,
)


def show_explorer_page() -> None:
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
        help="Select a Nordic country or view all countries",
    )
    st.session_state["quick_country"] = country

    st.divider()

    colors = {
        "denmark": "#C8102E",
        "sweden": "#FECC00",
        "norway": "#87CEEB",
        "finland": "#003580",
    }

    tables_col1, tables_col2 = st.columns(2)
    with tables_col1:
        heading = "Outlets (All Countries)" if not country else f"Outlets ({country.capitalize()})"
        st.subheader(heading)
        outlets_data = fetch_top_outlets(country=country, limit=1000)

        if outlets_data and outlets_data.get("data"):
            df_outlets = pd.DataFrame(consolidate_outlets(outlets_data["data"]))
            recent_data = fetch_top_outlets(
                country=country,
                limit=1000,
                date_from="2025-01-01",
                date_to="2026-12-31",
            )
            recent = (
                pd.DataFrame(consolidate_outlets(recent_data.get("data", [])))
                if recent_data
                else pd.DataFrame()
            )
            recent_counts = {}
            if not recent.empty:
                recent_counts = dict(zip(recent["domain"], recent["count"]))
            df_outlets["count_2025_26"] = df_outlets["domain"].map(recent_counts).fillna(0).astype(int)
            df_outlets = df_outlets.rename(columns={"count": "total_count"})
            st.dataframe(
                df_outlets[["domain", "partisan", "total_count", "count_2025_26"]].style.format(
                    {"total_count": "{:,}", "count_2025_26": "{:,}"}
                ),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "domain": "Domain",
                    "partisan": "Partisanship",
                    "total_count": "Total Count",
                    "count_2025_26": "Count (2025-26)",
                },
            )

    with tables_col2:
        category_heading = (
            "News Categories (All Countries)" if not country else f"News Categories ({country.capitalize()})"
        )
        st.subheader(
            category_heading,
            help="Content has been classified by an LLM to predefined news categories.",
        )
        categories_data = fetch_categories(country=country, partisan=None)
        if categories_data and categories_data.get("data"):
            df_cat = pd.DataFrame(categories_data["data"])
            df_cat = df_cat.sort_values("count", ascending=False).head(10)

            total = df_cat["count"].sum()
            df_cat["percentage"] = (df_cat["count"] / total * 100).round(1)

            st.dataframe(
                df_cat[["category", "count", "percentage"]].style.format(
                    {"count": "{:,}", "percentage": "{:.1f}%"}
                ),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "category": "Category",
                    "count": "Articles",
                    "percentage": "Percentage",
                },
            )

    if not country:
        conc_col, partisan_col = st.columns(2)
        with conc_col:
            st.subheader("Outlet Concentration")
            st.caption(
                "Share of total articles produced by the top 5 outlets in each country "
                "(higher = more concentrated)."
            )
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
                    concentration_rows.append({"country": ctry.capitalize(), "top5_share": share * 100})
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

    over_time_title = (
        "Articles Over Time (All Countries)" if not country else f"Articles Over Time ({country.capitalize()})"
    )
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
                help="Time period grouping for the time series chart (year, month, or week)",
            )
        with col2:
            partisan_filter = st.selectbox(
                "Filter by Partisan",
                options=[None, "Right", "Left", "Other"],
                format_func=lambda x: "All" if x is None else x,
                key="country_partisan_all",
                help="Political orientation of the media outlet (self-identified or classified)",
            )

        fig = go.Figure()
        countries = ["denmark", "sweden", "norway", "finland"]

        for ctry in countries:
            time_data = fetch_articles_over_time(
                country=ctry,
                partisan=partisan_filter,
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
                        name=ctry.capitalize(),
                        line=dict(color=colors.get(ctry, "#1f77b4"), width=2),
                        marker=dict(size=6),
                        hovertemplate=(
                            f"<b>{ctry.capitalize()}</b><br>Date: %{{x}}<br>Articles: %{{y:,}}<extra></extra>"
                        ),
                    )
                )

        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Number of Articles",
            height=450,
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.12, xanchor="center", x=0.5),
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
                    fig_category.add_trace(
                        go.Scatter(
                            x=df_cat["date"],
                            y=df_cat["share"],
                            stackgroup="one",
                            name=category,
                            hovertemplate=(
                                "<b>%{fullData.name}</b><br>Date: %{x}<br>"
                                "Share: %{y:.1f}%<extra></extra>"
                            ),
                        )
                    )
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
                    lorenz_fig.add_trace(
                        go.Scatter(
                            x=x_vals,
                            y=y_vals,
                            mode="lines",
                            name=f"{ctry.capitalize()} (Gini {gini:.2f})",
                            line=dict(color=colors.get(ctry, "#1f77b4"), width=2),
                            hovertemplate="Outlets: %{x:.0%}<br>Articles: %{y:.0%}<extra></extra>",
                        )
                    )
            lorenz_fig.add_trace(
                go.Scatter(
                    x=[0, 1],
                    y=[0, 1],
                    mode="lines",
                    name="Equality",
                    line=dict(color="#999999", width=1, dash="dash"),
                    hoverinfo="skip",
                )
            )
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
        view_type = st.radio(
            "View",
            options=["Total Count", "Separate Outlets", "Partisan Accumulated"],
            index=0,
            horizontal=True,
            key="country_view_type",
            help=(
                "Choose how to display articles over time: total count (aggregate), individual outlets, "
                "or grouped by partisan"
            ),
        )

        col1, col2 = st.columns(2)
        with col1:
            granularity = st.selectbox(
                "Time Granularity",
                options=["Year", "Month", "Week"],
                index=0,
                key="country_granularity",
                help="Time period grouping for the time series chart (year, month, or week)",
            )
        with col2:
            if view_type == "Separate Outlets":
                outlets_list = fetch_top_outlets(country=country, limit=20)
                if outlets_list and outlets_list.get("data"):
                    outlet_options = [o["domain"] for o in outlets_list["data"]]
                    selected_outlets = st.multiselect(
                        "Select Outlets",
                        options=outlet_options,
                        default=outlet_options[:5] if len(outlet_options) >= 5 else outlet_options,
                        key="country_selected_outlets",
                        help="Select outlets to display (shows top 5 by default)",
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
                    help="Political orientation of the media outlet (self-identified or classified)",
                )
                selected_outlets = []

        if view_type == "Total Count":
            time_data = fetch_articles_over_time(
                country=country,
                partisan=partisan_filter,
                granularity=granularity.lower(),
            )

            if time_data and time_data.get("data"):
                df_time = pd.DataFrame(time_data["data"])
                df_time["date"] = pd.to_datetime(df_time["date"], errors="coerce")
                df_time = df_time.sort_values("date")

                title_country = country.capitalize() if country else "All Countries"
                fig = px.line(
                    df_time,
                    x="date",
                    y="count",
                    markers=True,
                    title=f"Articles Over Time - {title_country} (Total Count)",
                )
                fig.update_traces(
                    line=dict(width=3, color="#1f77b4"),
                    marker=dict(size=8),
                    hovertemplate="<b>Date:</b> %{x}<br><b>Articles:</b> %{y:,}<extra></extra>",
                )
                fig.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Number of Articles",
                    height=400,
                    hovermode="x unified",
                )
                st.plotly_chart(fig, use_container_width=True)

        elif view_type == "Separate Outlets":
            if selected_outlets:
                outlet_time_data = fetch_articles_over_time_by_outlet(
                    country=country,
                    outlets=selected_outlets,
                    granularity=granularity.lower(),
                )

                if outlet_time_data and outlet_time_data.get("data"):
                    fig = go.Figure()
                    colors_list = px.colors.qualitative.Set3

                    for idx, outlet in enumerate(selected_outlets):
                        if outlet in outlet_time_data["data"]:
                            outlet_series = outlet_time_data["data"][outlet]
                            df_outlet = pd.DataFrame(outlet_series)
                            df_outlet["date"] = pd.to_datetime(df_outlet["date"], errors="coerce")
                            df_outlet = df_outlet.sort_values("date")

                            color = colors_list[idx % len(colors_list)]
                            fig.add_trace(
                                go.Scatter(
                                    x=df_outlet["date"],
                                    y=df_outlet["count"],
                                    mode="lines+markers",
                                    name=outlet,
                                    line=dict(color=color, width=2),
                                    marker=dict(size=6),
                                    hovertemplate=(
                                        f"<b>{outlet}</b><br>Date: %{{x}}<br>Articles: %{{y:,}}"
                                        "<extra></extra>"
                                    ),
                                )
                            )

                    fig.update_layout(
                        title=f"Articles Over Time - {country.capitalize()} (By Outlet)",
                        xaxis_title="Date",
                        yaxis_title="Number of Articles",
                        height=400,
                        hovermode="x unified",
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No data available for selected outlets.")
            else:
                st.info("Please select at least one outlet to display.")

        elif view_type == "Partisan Accumulated":
            fig = go.Figure()
            partisan_colors = {"Right": "#0066CC", "Left": "#DC143C", "Other": "#2ca02c"}

            for partisan in ["Right", "Left", "Other"]:
                time_data = fetch_articles_over_time(
                    country=country,
                    partisan=partisan,
                    granularity=granularity.lower(),
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
                            hovertemplate=(
                                f"<b>{partisan}</b><br>Date: %{{x}}<br>Articles: %{{y:,}}"
                                "<extra></extra>"
                            ),
                        )
                    )

            title_country = country.capitalize() if country else "All Countries"
            fig.update_layout(
                title=f"Articles Over Time - {title_country} (By Partisan)",
                xaxis_title="Date",
                yaxis_title="Number of Articles",
                height=400,
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig, use_container_width=True)
