import pandas as pd
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
import os

# Create necessary directories
os.makedirs("../reports", exist_ok=True)

print("Loading data...")
# Load the data - we'll do this once to make the dashboard more responsive
df_full = pl.read_csv("../data/full_da_fi_sw.csv")
df_full = df_full.with_columns(pl.col("date").str.to_datetime(strict=False))
# Remove nordfront domains from the dataset completely
df_full = df_full.filter(~pl.col("domain").is_in(["www.nordfront.dk", "nordfront.se"]))
print(f"Loaded {df_full.shape[0]} rows (nordfront excluded)")

# Extract date components for filtering
df_full = df_full.with_columns(
    [pl.col("date").dt.year().alias("year"), pl.col("date").dt.month().alias("month")]
)

# Calculate content length for each article
df_with_length = df_full.with_columns(
    pl.col("content").str.len_bytes().alias("content_length")
)

# Filter out potential outliers or empty content
df_filtered = df_with_length.filter(
    (pl.col("content_length") > 0)
    & (
        pl.col("content_length") < 100000
    )  # Exclude extremely long articles that might be errors
)

# Convert to pandas for easier plotting with plotly
df_pandas = df_filtered.to_pandas()

# Initialize the Dash app with a nice theme
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define the layout
app.layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H1(
                            "Nordic Alternative Media Observatory",
                            className="text-center my-4",
                        ),
                        html.P(
                            "Interactive dashboard for exploring Nordic alternative news media content",
                            className="text-center mb-5",
                        ),
                    ]
                )
            ]
        ),
        # Filters
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H4("Filters"),
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.Label("Select Countries:"),
                                        dcc.Checklist(
                                            id="country-filter",
                                            options=[
                                                {"label": c.capitalize(), "value": c}
                                                for c in df_pandas["country"].unique()
                                            ],
                                            value=df_pandas["country"]
                                            .unique()
                                            .tolist(),
                                            inline=True,
                                        ),
                                        html.Br(),
                                        html.Label("Year Range:"),
                                        dcc.RangeSlider(
                                            id="year-slider",
                                            min=2005,
                                            max=df_pandas["year"].max(),
                                            value=[2005, df_pandas["year"].max()],
                                            marks={
                                                str(year): str(year)
                                                for year in range(
                                                    2005,
                                                    int(df_pandas["year"].max()) + 1,
                                                    2,
                                                )
                                            },
                                            step=1,
                                        ),
                                    ]
                                )
                            ],
                            className="mb-4",
                        ),
                    ]
                )
            ]
        ),
        # First row of visualizations
        dbc.Row(
            [
                # Longitudinal plot
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader("News Articles Over Time"),
                                dbc.CardBody([dcc.Graph(id="time-series-graph")]),
                            ]
                        ),
                    ],
                    width=12,
                    className="mb-4",
                ),
            ]
        ),
        # Second row of visualizations
        dbc.Row(
            [
                # Top news outlets
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader("Top News Outlets by Country"),
                                dbc.CardBody(
                                    [
                                        dcc.Dropdown(
                                            id="country-dropdown",
                                            options=[
                                                {"label": c.capitalize(), "value": c}
                                                for c in df_pandas["country"].unique()
                                            ],
                                            value=df_pandas["country"].unique()[0],
                                            clearable=False,
                                        ),
                                        dcc.Graph(id="top-outlets-graph"),
                                    ]
                                ),
                            ]
                        ),
                    ],
                    width=6,
                ),
                # Article length
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader("Article Length Distribution"),
                                dbc.CardBody(
                                    [
                                        dcc.RadioItems(
                                            id="length-view-selector",
                                            options=[
                                                {
                                                    "label": "Top 20 by Length",
                                                    "value": "top",
                                                },
                                                {
                                                    "label": "Bottom 20 by Length",
                                                    "value": "bottom",
                                                },
                                                {
                                                    "label": "Distribution by Country",
                                                    "value": "distribution",
                                                },
                                            ],
                                            value="top",
                                            inline=True,
                                        ),
                                        dcc.Graph(id="article-length-graph"),
                                    ]
                                ),
                            ]
                        ),
                    ],
                    width=6,
                ),
            ],
            className="mb-4",
        ),
        # Third row - additional insights
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader("Monthly Publishing Patterns"),
                                dbc.CardBody([dcc.Graph(id="monthly-pattern-graph")]),
                            ]
                        ),
                    ],
                    width=12,
                ),
            ]
        ),
        html.Footer(
            [
                html.P(
                    "Data Dashboard - Created with Plotly Dash",
                    className="text-center mt-5",
                )
            ]
        ),
    ],
    fluid=True,
)


# Callback for time series graph
@app.callback(
    Output("time-series-graph", "figure"),
    [Input("country-filter", "value"), Input("year-slider", "value")],
)
def update_time_series(selected_countries, year_range):
    filtered_df = df_pandas[
        (df_pandas["country"].isin(selected_countries))
        & (df_pandas["year"] >= year_range[0])
        & (df_pandas["year"] <= year_range[1])
    ]

    # Group by year and country
    yearly_counts = (
        filtered_df.groupby(["year", "country"]).size().reset_index(name="count")
    )

    fig = px.line(
        yearly_counts,
        x="year",
        y="count",
        color="country",
        labels={"count": "Number of Articles", "year": "Year"},
        title="News Articles by Country Over Time",
        line_shape="linear",
        render_mode="svg",
    )

    fig.update_traces(mode="lines+markers")
    fig.update_layout(
        xaxis=dict(tickmode="linear", dtick=1),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=500,
    )

    return fig


# Callback for top outlets
@app.callback(
    Output("top-outlets-graph", "figure"),
    [Input("country-dropdown", "value"), Input("year-slider", "value")],
)
def update_top_outlets(selected_country, year_range):
    filtered_df = df_pandas[
        (df_pandas["country"] == selected_country)
        & (df_pandas["year"] >= year_range[0])
        & (df_pandas["year"] <= year_range[1])
    ]

    # Get top 10 domains
    domain_counts = filtered_df.groupby("domain").size().reset_index(name="count")
    top_domains = domain_counts.sort_values("count", ascending=False).head(10)

    fig = px.bar(
        top_domains,
        y="domain",
        x="count",
        orientation="h",
        labels={"count": "Number of Articles", "domain": "News Outlet"},
        title=f"Top 10 News Outlets in {selected_country.capitalize()}",
    )

    fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=500)

    return fig


# Callback for article length
@app.callback(
    Output("article-length-graph", "figure"),
    [
        Input("length-view-selector", "value"),
        Input("country-filter", "value"),
        Input("year-slider", "value"),
    ],
)
def update_article_length(view_type, selected_countries, year_range):
    filtered_df = df_pandas[
        (df_pandas["country"].isin(selected_countries))
        & (df_pandas["year"] >= year_range[0])
        & (df_pandas["year"] <= year_range[1])
        & (df_pandas["content_length"] > 0)
    ]

    if view_type == "distribution":
        fig = px.box(
            filtered_df,
            x="country",
            y="content_length",
            labels={
                "content_length": "Article Length (characters)",
                "country": "Country",
            },
            title="Article Length Distribution by Country",
        )
        fig.update_layout(height=500)

    else:  # 'top' or 'bottom'
        # Get article length by domain with at least 50 articles
        domain_length = (
            filtered_df.groupby("domain")
            .agg(
                article_count=("domain", "count"),
                avg_length=("content_length", "mean"),
                std_length=("content_length", "std"),
            )
            .reset_index()
        )

        domain_length = domain_length[domain_length["article_count"] >= 50]

        if view_type == "top":
            domain_subset = domain_length.sort_values(
                "avg_length", ascending=False
            ).head(20)
            title = "Top 20 News Outlets by Average Article Length"
        else:  # 'bottom'
            domain_subset = domain_length.sort_values(
                "avg_length", ascending=True
            ).head(20)
            title = "Bottom 20 News Outlets by Average Article Length"

        fig = px.bar(
            domain_subset,
            y="domain",
            x="avg_length",
            orientation="h",
            labels={
                "avg_length": "Average Length (characters)",
                "domain": "News Outlet",
            },
            title=title,
        )

        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=500)

    return fig


# Callback for monthly patterns
@app.callback(
    Output("monthly-pattern-graph", "figure"),
    [Input("country-filter", "value"), Input("year-slider", "value")],
)
def update_monthly_pattern(selected_countries, year_range):
    filtered_df = df_pandas[
        (df_pandas["country"].isin(selected_countries))
        & (df_pandas["year"] >= year_range[0])
        & (df_pandas["year"] <= year_range[1])
        & (df_pandas["month"].notna())
    ]

    # Group by month and country
    monthly_counts = (
        filtered_df.groupby(["month", "country"]).size().reset_index(name="count")
    )

    fig = px.line(
        monthly_counts,
        x="month",
        y="count",
        color="country",
        labels={"count": "Average Number of Articles", "month": "Month"},
        title="Monthly Publishing Patterns by Country",
        line_shape="spline",
    )

    fig.update_xaxes(
        tickvals=list(range(1, 13)),
        ticktext=[
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ],
    )

    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=500,
    )

    return fig


# Run the app
if __name__ == "__main__":
    print("Starting Dashboard. Access at http://127.0.0.1:8051/")
    app.run(debug=True, port=8051)
