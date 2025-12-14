import pandas as pd
import polars as pl
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set up the plot style
plt.style.use("ggplot")
sns.set_palette("colorblind")

# Create directories for the visualization outputs
os.makedirs("../reports", exist_ok=True)

# Load the data
print("Loading data...")
df_full = pl.read_csv("../data/full_all_countries_250908.csv")

df_full = df_full.with_columns(pl.col("date").str.to_datetime(strict=False))
print(f"Loaded {df_full.shape[0]} rows")

# 1. Longitudinal plot: news items per country per year
print("Creating longitudinal plot...")

# Extract year from date and count by year and country
yearly_counts = (
    df_full.filter((pl.col("date").is_not_null()) & (pl.col("date").dt.year() >= 2005))
    .with_columns(pl.col("date").dt.year().alias("year"))
    .group_by(["year", "country"])
    .len()
    .sort(["country", "year"])
)

# Convert to pandas for easier plotting
yearly_counts_pd = yearly_counts.to_pandas()

# Define colors and markers for each country
country_styles = {
    "denmark": {"color": "#1f77b4", "marker": "o"},
    "finland": {"color": "#ff7f0e", "marker": "s"},
    "norway": {"color": "#2ca02c", "marker": "^"},
    "sweden": {"color": "#d62728", "marker": "D"},
}

# Create color version
plt.figure(figsize=(14, 8))
for country in yearly_counts_pd["country"].unique():
    country_data = yearly_counts_pd[yearly_counts_pd["country"] == country]
    style = country_styles.get(country, {"color": "gray", "marker": "o"})
    plt.plot(
        country_data["year"],
        country_data["len"],
        marker=style["marker"],
        linewidth=2,
        color=style["color"],
        label=country.capitalize(),
        markersize=8,
    )

plt.title("Articles over time per country", fontsize=16)
plt.xlabel("Year", fontsize=14)
plt.ylabel("Number of Articles", fontsize=14)
plt.legend(fontsize=12)
plt.grid(True, alpha=0.3)
plt.tight_layout()

# Set white background
plt.gca().set_facecolor("white")
plt.gcf().set_facecolor("white")

# Set x-axis to show 2-year intervals from 2005 to 2025
years = list(range(2005, 2026, 2))
plt.xticks(years, rotation=45)
plt.xlim(2004, 2026)

# Save the color figure
plt.savefig(
    "../reports/news_items_by_country_yearly.png",
    dpi=300,
    bbox_inches="tight",
    facecolor="white",
)
print("Saved color longitudinal plot")

# Create black and white version
plt.figure(figsize=(14, 8))
for country in yearly_counts_pd["country"].unique():
    country_data = yearly_counts_pd[yearly_counts_pd["country"] == country]
    style = country_styles.get(country, {"marker": "o"})
    plt.plot(
        country_data["year"],
        country_data["len"],
        marker=style["marker"],
        linewidth=2,
        color="black",
        label=country.capitalize(),
        markersize=8,
    )

plt.title("Articles over time per country", fontsize=16)
plt.xlabel("Year", fontsize=14)
plt.ylabel("Number of Articles", fontsize=14)
plt.legend(fontsize=12)
plt.grid(True, alpha=0.3)
plt.tight_layout()

# Set white background
plt.gca().set_facecolor("white")
plt.gcf().set_facecolor("white")

# Set x-axis to show 2-year intervals from 2005 to 2025
plt.xticks(years, rotation=45)
plt.xlim(2004, 2026)

# Save the black and white figure
plt.savefig(
    "../reports/news_items_by_country_yearly_bw.png",
    dpi=300,
    bbox_inches="tight",
    facecolor="white",
)
print("Saved black and white longitudinal plot")

# 2. Top 10 news outlets per country
print("Creating top news outlets plots...")

# Group data by country and domain, count articles (filter out null domains)
domain_counts = (
    df_full.filter(pl.col("domain").is_not_null())
    .group_by(["country", "domain"])
    .len()
    .sort(["country", "len"], descending=[False, True])
)

# Process each country separately
countries = domain_counts["country"].unique().to_list()

for country in countries:
    country_domains = domain_counts.filter(pl.col("country") == country).limit(10)
    country_domains_pd = country_domains.to_pandas()

    # Filter out any remaining null domains in pandas
    country_domains_pd = country_domains_pd.dropna(subset=["domain"])

    if len(country_domains_pd) == 0:
        print(f"No valid domains found for {country}")
        continue

    plt.figure(figsize=(12, 7))
    bars = plt.barh(country_domains_pd["domain"], country_domains_pd["len"])

    # Add count labels to the bars
    for bar in bars:
        width = bar.get_width()
        plt.text(
            width + (width * 0.01),
            bar.get_y() + bar.get_height() / 2,
            f"{int(width):,}",
            ha="left",
            va="center",
            fontsize=10,
        )

    plt.title(f"Top 10 News Outlets in {country.capitalize()}", fontsize=16)
    plt.xlabel("Number of Articles", fontsize=14)
    plt.ylabel("News Outlet", fontsize=14)
    plt.gca().invert_yaxis()  # To have the highest count at the top
    plt.tight_layout()

    # Save the figure
    plt.savefig(
        f"../reports/top_10_outlets_{country}.png", dpi=300, bbox_inches="tight"
    )
    print(f"Saved top 10 plot for {country}")

# 3. Average content length by domain (Top 20)
print("Analyzing average article length by domain...")

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

# Group by domain and calculate average content length
domain_length = (
    df_filtered.filter(pl.col("domain").is_not_null())
    .group_by("domain")
    .agg(
        [
            pl.len().alias("article_count"),
            pl.col("content_length").mean().alias("avg_length"),
            pl.col("content_length").std().alias("std_length"),
        ]
    )
    .filter(
        pl.col("article_count")
        >= 50  # Only include domains with at least 50 articles for more reliable averages
    )
    .sort("avg_length", descending=True)
)

# Get top 20 domains by average content length
top_20_length = domain_length.limit(20)
top_20_length_pd = top_20_length.to_pandas()

# Plot average content length for top 20 domains
plt.figure(figsize=(14, 10))
bars = plt.barh(top_20_length_pd["domain"], top_20_length_pd["avg_length"])

# Add length labels to the bars
for bar in bars:
    width = bar.get_width()
    plt.text(
        width + (width * 0.01),
        bar.get_y() + bar.get_height() / 2,
        f"{int(width):,}",
        ha="left",
        va="center",
        fontsize=10,
    )

plt.title("Top 20 News Outlets by Average Article Length", fontsize=16)
plt.xlabel("Average Content Length (characters)", fontsize=14)
plt.ylabel("News Outlet", fontsize=14)
plt.gca().invert_yaxis()  # To have the highest avg length at the top
plt.tight_layout()

# Save the figure
plt.savefig("../reports/top_20_avg_length.png", dpi=300, bbox_inches="tight")
print("Saved average content length plot")

# Save the data as a CSV for reference
top_20_length.write_csv("../reports/top_20_avg_length.csv")
print("Saved average content length data to CSV")

# Add bottom 20 domains by average content length
bottom_20_length = domain_length.sort("avg_length", descending=False).limit(20)
bottom_20_length_pd = bottom_20_length.to_pandas()

# Plot average content length for bottom 20 domains
plt.figure(figsize=(14, 10))
bars = plt.barh(bottom_20_length_pd["domain"], bottom_20_length_pd["avg_length"])

# Add length labels to the bars
for bar in bars:
    width = bar.get_width()
    plt.text(
        width + (width * 0.01),
        bar.get_y() + bar.get_height() / 2,
        f"{int(width):,}",
        ha="left",
        va="center",
        fontsize=10,
    )

plt.title("Bottom 20 News Outlets by Average Article Length", fontsize=16)
plt.xlabel("Average Content Length (characters)", fontsize=14)
plt.ylabel("News Outlet", fontsize=14)
plt.gca().invert_yaxis()  # To have the shortest avg length at the top
plt.tight_layout()

# Save the figure
plt.savefig("../reports/bottom_20_avg_length.png", dpi=300, bbox_inches="tight")
print("Saved bottom average content length plot")

# Save the data as a CSV for reference
bottom_20_length.write_csv("../reports/bottom_20_avg_length.csv")
print("Saved bottom average content length data to CSV")

# 4. Productivity Normalization Analysis
print("Creating productivity normalization analysis...")

# Calculate articles per year per domain for productivity analysis
domain_yearly_counts = (
    df_full.filter((pl.col("date").is_not_null()) & (pl.col("date").dt.year() >= 2005))
    .with_columns(pl.col("date").dt.year().alias("year"))
    .group_by(["domain", "country", "year"])
    .len()
    .filter(pl.col("domain").is_not_null())
)

# Calculate productivity metrics per domain
domain_productivity = (
    domain_yearly_counts.group_by(["domain", "country"])
    .agg(
        [
            pl.col("len").mean().alias("avg_articles_per_year"),
            pl.col("len").std().alias("std_articles_per_year"),
            pl.col("len").sum().alias("total_articles"),
            pl.len().alias("years_active"),
            pl.col("year").min().alias("first_year"),
            pl.col("year").max().alias("last_year"),
        ]
    )
    .filter(pl.col("years_active") >= 3)  # Only domains active for 3+ years
    .sort("avg_articles_per_year", descending=True)
)

# Top 20 most productive domains (by average articles per year)
top_20_productive = domain_productivity.limit(20)
top_20_productive_pd = top_20_productive.to_pandas()

# Plot productivity analysis
plt.figure(figsize=(14, 10))
bars = plt.barh(
    top_20_productive_pd["domain"], top_20_productive_pd["avg_articles_per_year"]
)

# Add productivity labels to the bars
for bar in bars:
    width = bar.get_width()
    plt.text(
        width + (width * 0.01),
        bar.get_y() + bar.get_height() / 2,
        f"{int(width):,}",
        ha="left",
        va="center",
        fontsize=10,
    )

plt.title(
    "Top 20 Most Productive News Outlets (Average Articles per Year)", fontsize=16
)
plt.xlabel("Average Articles per Year", fontsize=14)
plt.ylabel("News Outlet", fontsize=14)
plt.gca().invert_yaxis()
plt.tight_layout()

# Save the figure
plt.savefig("../reports/top_20_productive_domains.png", dpi=300, bbox_inches="tight")
print("Saved productivity analysis plot")

# Save the data as CSV
top_20_productive.write_csv("../reports/top_20_productive_domains.csv")
print("Saved productivity data to CSV")

# 4b. Top 10 Most Productive Domains per Country
print("Creating top 10 productive domains per country...")

# Get top 10 per country
top_10_per_country = (
    domain_productivity.group_by("country")
    .head(10)
    .sort(["country", "avg_articles_per_year"], descending=[False, True])
)

# Convert to pandas for easier processing
top_10_per_country_pd = top_10_per_country.to_pandas()

# Create separate plots for each country
countries = top_10_per_country_pd["country"].unique()

for country in countries:
    country_data = top_10_per_country_pd[top_10_per_country_pd["country"] == country]

    if len(country_data) == 0:
        continue

    plt.figure(figsize=(12, 8))
    bars = plt.barh(country_data["domain"], country_data["avg_articles_per_year"])

    # Add productivity labels to the bars
    for bar in bars:
        width = bar.get_width()
        plt.text(
            width + (width * 0.01),
            bar.get_y() + bar.get_height() / 2,
            f"{int(width):,}",
            ha="left",
            va="center",
            fontsize=10,
        )

    plt.title(
        f"Top 10 Most Productive News Outlets in {country.capitalize()}\n(Average Articles per Year)",
        fontsize=16,
    )
    plt.xlabel("Average Articles per Year", fontsize=14)
    plt.ylabel("News Outlet", fontsize=14)
    plt.gca().invert_yaxis()
    plt.tight_layout()

    # Save the figure
    plt.savefig(
        f"../reports/top_10_productive_{country}.png", dpi=300, bbox_inches="tight"
    )
    print(f"Saved top 10 productive plot for {country}")

# Save the combined data as CSV
top_10_per_country.write_csv("../reports/top_10_productive_per_country.csv")
print("Saved top 10 productive per country data to CSV")

# 5. Domain Survival Rate Analysis
print("Creating domain survival rate analysis...")

# Calculate survival metrics
survival_analysis = (
    domain_productivity.with_columns(
        [
            (pl.col("last_year") - pl.col("first_year") + 1).alias("potential_years"),
            (
                pl.col("years_active")
                / (pl.col("last_year") - pl.col("first_year") + 1)
            ).alias("survival_rate"),
        ]
    )
    .filter(pl.col("potential_years") >= 5)  # Only domains with 5+ potential years
    .sort("survival_rate", descending=True)
)

# Top 20 most persistent domains
top_20_survivors = survival_analysis.limit(20)
top_20_survivors_pd = top_20_survivors.to_pandas()

# Plot survival rate analysis
plt.figure(figsize=(14, 10))
bars = plt.barh(top_20_survivors_pd["domain"], top_20_survivors_pd["survival_rate"])

# Add survival rate labels to the bars
for bar in bars:
    width = bar.get_width()
    plt.text(
        width + 0.01,
        bar.get_y() + bar.get_height() / 2,
        f"{width:.2f}",
        ha="left",
        va="center",
        fontsize=10,
    )

plt.title("Top 20 Most Persistent News Outlets (Survival Rate)", fontsize=16)
plt.xlabel("Survival Rate (Years Active / Potential Years)", fontsize=14)
plt.ylabel("News Outlet", fontsize=14)
plt.gca().invert_yaxis()
plt.xlim(0, 1.1)
plt.tight_layout()

# Save the figure
plt.savefig("../reports/top_20_survivor_domains.png", dpi=300, bbox_inches="tight")
print("Saved survival rate analysis plot")

# Save the data as CSV
top_20_survivors.write_csv("../reports/top_20_survivor_domains.csv")
print("Saved survival rate data to CSV")

# 6. Simple Rolling Window Analysis (5-year periods)
print("Creating rolling window analysis...")

# Create 5-year rolling windows
rolling_windows = []
for start_year in range(2005, 2021, 5):  # 2005-2009, 2010-2014, 2015-2019, 2020-2024
    end_year = start_year + 4
    window_data = (
        df_full.filter(
            (pl.col("date").is_not_null())
            & (pl.col("date").dt.year() >= start_year)
            & (pl.col("date").dt.year() <= end_year)
        )
        .with_columns(pl.col("date").dt.year().alias("year"))
        .group_by(["country", "domain"])
        .len()
        .with_columns(
            [
                pl.lit(f"{start_year}-{end_year}").alias("period"),
                pl.lit(start_year).alias("start_year"),
            ]
        )
    )
    rolling_windows.append(window_data)

# Combine all rolling windows
rolling_combined = pl.concat(rolling_windows)

# Calculate productivity per period
period_productivity = (
    rolling_combined.group_by(["country", "period", "start_year"])
    .agg(
        [
            pl.col("len").sum().alias("total_articles"),
            pl.col("domain").n_unique().alias("unique_domains"),
            (pl.col("len").sum() / pl.col("domain").n_unique()).alias(
                "avg_articles_per_domain"
            ),
        ]
    )
    .sort(["start_year", "country"])
)

# Convert to pandas for plotting
period_productivity_pd = period_productivity.to_pandas()

# Create rolling window visualization
plt.figure(figsize=(14, 8))
for country in period_productivity_pd["country"].unique():
    country_data = period_productivity_pd[period_productivity_pd["country"] == country]
    style = country_styles.get(country, {"color": "gray", "marker": "o"})
    plt.plot(
        country_data["start_year"],
        country_data["avg_articles_per_domain"],
        marker=style["marker"],
        linewidth=2,
        color=style["color"],
        label=country.capitalize(),
        markersize=8,
    )

plt.title("Average Articles per Domain by 5-Year Periods", fontsize=16)
plt.xlabel("Period Start Year", fontsize=14)
plt.ylabel("Average Articles per Domain", fontsize=14)
plt.legend(fontsize=12)
plt.grid(True, alpha=0.3)
plt.tight_layout()

# Set white background
plt.gca().set_facecolor("white")
plt.gcf().set_facecolor("white")

# Save the rolling window figure
plt.savefig("../reports/rolling_window_productivity.png", dpi=300, bbox_inches="tight")
print("Saved rolling window analysis plot")

# Save the rolling window data
period_productivity.write_csv("../reports/rolling_window_productivity.csv")
print("Saved rolling window data to CSV")

# 6b. Create Multiple Solid Visualizations for Rolling Window Productivity
print("Creating multiple solid visualizations for rolling window productivity...")

import numpy as np

# Prepare data
periods = period_productivity_pd["period"].unique()
countries = period_productivity_pd["country"].unique()
colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
country_colors = dict(zip(countries, colors))

# 1. Stacked Bar Chart
plt.figure(figsize=(14, 8))
x = np.arange(len(periods))
width = 0.2

for i, country in enumerate(countries):
    country_data = period_productivity_pd[period_productivity_pd["country"] == country]
    values = []
    for period in periods:
        period_data = country_data[country_data["period"] == period]
        if len(period_data) > 0:
            values.append(period_data["avg_articles_per_domain"].iloc[0])
        else:
            values.append(0)

    plt.bar(
        x + i * width,
        values,
        width,
        label=country.capitalize(),
        color=country_colors[country],
        alpha=0.8,
    )

plt.xlabel("5-Year Periods", fontsize=14)
plt.ylabel("Average Articles per Domain", fontsize=14)
plt.title(
    "Productivity per Domain by Country and Period\n(Grouped Bar Chart)", fontsize=16
)
plt.xticks(x + width * 1.5, periods, rotation=45)
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("../reports/rolling_window_grouped_bars.png", dpi=300, bbox_inches="tight")
print("Saved grouped bar chart")

# 2. Heatmap
plt.figure(figsize=(10, 6))
# Create pivot table for heatmap
heatmap_data = period_productivity_pd.pivot(
    index="country", columns="period", values="avg_articles_per_domain"
)
heatmap_data = heatmap_data.fillna(0)

sns.heatmap(
    heatmap_data,
    annot=True,
    fmt=".0f",
    cmap="YlOrRd",
    cbar_kws={"label": "Average Articles per Domain"},
)
plt.title(
    "Productivity per Domain Heatmap\n(Articles per Domain by Country and Period)",
    fontsize=16,
)
plt.xlabel("5-Year Periods", fontsize=14)
plt.ylabel("Country", fontsize=14)
plt.tight_layout()
plt.savefig("../reports/rolling_window_heatmap.png", dpi=300, bbox_inches="tight")
print("Saved heatmap")

# 3. Area Chart
plt.figure(figsize=(14, 8))
for country in countries:
    country_data = period_productivity_pd[period_productivity_pd["country"] == country]
    values = []
    for period in periods:
        period_data = country_data[country_data["period"] == period]
        if len(period_data) > 0:
            values.append(period_data["avg_articles_per_domain"].iloc[0])
        else:
            values.append(0)

    plt.fill_between(
        periods,
        values,
        alpha=0.6,
        label=country.capitalize(),
        color=country_colors[country],
    )
    plt.plot(
        periods,
        values,
        color=country_colors[country],
        linewidth=2,
        marker="o",
        markersize=6,
    )

plt.xlabel("5-Year Periods", fontsize=14)
plt.ylabel("Average Articles per Domain", fontsize=14)
plt.title("Productivity per Domain by Country and Period\n(Area Chart)", fontsize=16)
plt.legend()
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("../reports/rolling_window_area_chart.png", dpi=300, bbox_inches="tight")
print("Saved area chart")

# 4. Multi-line Chart with Markers
plt.figure(figsize=(14, 8))
for country in countries:
    country_data = period_productivity_pd[period_productivity_pd["country"] == country]
    values = []
    for period in periods:
        period_data = country_data[country_data["period"] == period]
        if len(period_data) > 0:
            values.append(period_data["avg_articles_per_domain"].iloc[0])
        else:
            values.append(0)

    plt.plot(
        periods,
        values,
        marker="o",
        linewidth=3,
        markersize=8,
        label=country.capitalize(),
        color=country_colors[country],
    )

plt.xlabel("5-Year Periods", fontsize=14)
plt.ylabel("Average Articles per Domain", fontsize=14)
plt.title(
    "Productivity per Domain by Country and Period\n(Multi-line Chart)", fontsize=16
)
plt.legend(fontsize=12)
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("../reports/rolling_window_multiline.png", dpi=300, bbox_inches="tight")
print("Saved multi-line chart")

# 5. Horizontal Bar Chart
plt.figure(figsize=(14, 10))
# Create a combined dataset for horizontal bars
combined_data = []
for country in countries:
    country_data = period_productivity_pd[period_productivity_pd["country"] == country]
    for _, row in country_data.iterrows():
        combined_data.append(
            {
                "country": row["country"],
                "period": row["period"],
                "value": row["avg_articles_per_domain"],
                "label": f"{row['country'].capitalize()} - {row['period']}",
            }
        )

combined_df = pd.DataFrame(combined_data)
combined_df = combined_df.sort_values("value", ascending=True)

bars = plt.barh(
    combined_df["label"],
    combined_df["value"],
    color=[country_colors[row["country"]] for _, row in combined_df.iterrows()],
    alpha=0.8,
)

# Add value labels
for i, (bar, value) in enumerate(zip(bars, combined_df["value"])):
    plt.text(
        bar.get_width() + 50,
        bar.get_y() + bar.get_height() / 2,
        f"{int(value):,}",
        ha="left",
        va="center",
        fontsize=10,
    )

plt.xlabel("Average Articles per Domain", fontsize=14)
plt.ylabel("Country - Period", fontsize=14)
plt.title(
    "Productivity per Domain by Country and Period\n(Horizontal Bar Chart)", fontsize=16
)
plt.grid(True, alpha=0.3, axis="x")
plt.tight_layout()
plt.savefig(
    "../reports/rolling_window_horizontal_bars.png", dpi=300, bbox_inches="tight"
)
print("Saved horizontal bar chart")

# 7. Updated Longitudinal Plot with Interpretation
print("Creating updated longitudinal plot with interpretation...")

# Create the original plot but with updated title and interpretation
plt.figure(figsize=(14, 8))
for country in yearly_counts_pd["country"].unique():
    country_data = yearly_counts_pd[yearly_counts_pd["country"] == country]
    style = country_styles.get(country, {"color": "#1f77b4", "marker": "o"})
    plt.plot(
        country_data["year"],
        country_data["len"],
        marker=style["marker"],
        linewidth=2,
        color=style["color"],
        label=country.capitalize(),
        markersize=8,
    )

plt.title(
    "Articles over time per country\n(Note: Reflects both outlet productivity and survival rates)",
    fontsize=16,
)
plt.xlabel("Year", fontsize=14)
plt.ylabel("Number of Articles", fontsize=14)
plt.legend(fontsize=12)
plt.grid(True, alpha=0.3)
plt.tight_layout()

# Set white background
plt.gca().set_facecolor("white")
plt.gcf().set_facecolor("white")

# Set x-axis to show 2-year intervals from 2005 to 2025
years = list(range(2005, 2026, 2))
plt.xticks(years, rotation=45)
plt.xlim(2004, 2026)

# Add interpretation text
plt.figtext(
    0.02,
    0.02,
    "Interpretation: This plot shows total article counts, which reflect both the productivity of individual outlets\n"
    "and their survival rates over the 20-year period. See separate productivity and survival rate analyses\n"
    "for more detailed insights into outlet performance.",
    fontsize=10,
    ha="left",
    va="bottom",
    style="italic",
)

# Save the updated figure
plt.savefig(
    "../reports/news_items_by_country_yearly_with_interpretation.png",
    dpi=300,
    bbox_inches="tight",
    facecolor="white",
)
print("Saved updated longitudinal plot with interpretation")

print("All visualizations have been saved to the 'reports' directory")
print("New analyses include:")
print("- Productivity normalization (articles per year per domain)")
print("- Top 10 productive domains per country")
print("- Domain survival rate analysis")
print("- Simple 5-year rolling window analysis")
print("- Multiple solid visualizations for rolling window productivity:")
print("  * Grouped bar chart")
print("  * Heatmap")
print("  * Area chart")
print("  * Multi-line chart")
print("  * Horizontal bar chart")
print("- Updated longitudinal plot with interpretation")
