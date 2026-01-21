from __future__ import annotations

import json
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from services.api import (
    fetch_articles,
    fetch_categories,
    fetch_overview,
    fetch_related_articles,
    fetch_top_outlets,
)


def show_content_engagement_page() -> None:
    """Show content engagement / deep dive page."""

    st.markdown('<h1 class="main-header">Dataset</h1>', unsafe_allow_html=True)

    # Get the latest article date from overview to use as "today"
    overview = fetch_overview()
    latest_article_date = None
    earliest_article_date = None
    if overview and overview.get("date_range", {}):
        if overview["date_range"].get("latest"):
            try:
                latest_article_date = datetime.fromisoformat(overview["date_range"]["latest"][:10]).date()
            except Exception:
                pass
        if overview["date_range"].get("earliest"):
            try:
                earliest_article_date = datetime.fromisoformat(overview["date_range"]["earliest"][:10]).date()
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
        help="Search for keywords in article titles and descriptions",
    )

    # Date range selection with presets
    st.subheader("Date Range")
    preset_col1, preset_col2 = st.columns([2, 1])

    with preset_col1:
        date_preset = st.selectbox(
            "Time period",
            options=["Last week", "Last month", "Last 2 months", "Last 6 months", "Last year", "Custom range"],
            index=2,  # Default to "Last 2 months"
            help="Select a preset time period or choose custom range",
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
                min_value=earliest_article_date if earliest_article_date else datetime(2000, 1, 1).date(),
            )
        with date_col2:
            date_to = st.date_input(
                "To",
                value=today,
                max_value=today,
                min_value=date_from,
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
            help="Filter by Nordic country",
        )
    with filter_col2:
        filter_partisan = st.selectbox(
            "Partisan",
            options=[None, "Right", "Left", "Other"],
            format_func=lambda x: "All" if x is None else x,
            help="Political orientation of the media outlet",
        )
    with filter_col3:
        filter_sentiment = st.selectbox(
            "Sentiment",
            options=[None, "positive", "neutral", "negative"],
            format_func=lambda x: "All" if x is None else x.capitalize(),
            help="Emotional tone of the article",
        )

    # Advanced filters in sidebar
    with st.sidebar:
        st.header("Advanced Filters")

        # Get available categories for filter
        categories_data = fetch_categories()
        available_categories = []
        if categories_data and categories_data.get("data"):
            available_categories = [item["category"] for item in categories_data["data"]]

        selected_categories = st.multiselect(
            "Categories",
            options=available_categories[:20],  # Limit to top 20
            help="Select one or more categories",
        )

        entity_search = st.text_input(
            "Entities mentioned",
            placeholder="Search for person, location, or organization...",
            help="Search for specific entities mentioned in articles",
        )
        selected_entities = [entity_search] if entity_search else None

        # Get available outlets
        outlets_data = fetch_top_outlets(limit=50)
        available_outlets = []
        if outlets_data and outlets_data.get("data"):
            available_outlets = [item["domain"] for item in outlets_data["data"]]

        selected_outlets = st.multiselect(
            "Outlets",
            options=available_outlets,
            help="Select specific media outlets",
        )

        st.divider()

        # Export section
        st.header("Export Options")
        export_format = st.radio(
            "Format",
            options=["CSV", "JSON"],
            help="Choose export format",
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
        offset=offset,
    )

    if not search_results:
        st.warning("Unable to load articles. Please check API connection.")
        return

    total_articles = search_results.get("total", 0)
    articles = search_results.get("articles", [])

    # Display results header
    st.markdown(f"### Showing {len(articles)} of {total_articles:,} articles")

    if total_articles == 0:
        st.info("No articles found matching your criteria. Try adjusting your filters.")
        return

    # Display articles
    for article in articles:
        article_id = article.get("id")
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
            if article.get("domain"):
                metadata_parts.append(f"**{article.get('domain')}**")
            if article.get("country"):
                metadata_parts.append(f"{article.get('country').capitalize()}")
            if article.get("partisan"):
                metadata_parts.append(f"{article.get('partisan')}")
            if article.get("date"):
                try:
                    article_date = datetime.fromisoformat(article.get("date")[:10])
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
                        date_str = article.get("date")[:10]
                    metadata_parts.append(f"{date_str}")
                except Exception:
                    metadata_parts.append(f"{article.get('date')[:10]}")

            st.markdown(" • ".join(metadata_parts))

            # Article preview
            description = article.get("description", "")
            content = article.get("content", "")
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
                if article.get("categories"):
                    categories_str = ", ".join(article.get("categories", [])[:3])
                    st.markdown(f"**Categories:** {categories_str}")
            with badge_col2:
                sentiment = article.get("sentiment", "")
                sentiment_score = article.get("sentiment_score", 0)
                if sentiment:
                    st.markdown(f"**Sentiment:** {sentiment.capitalize()} ({sentiment_score:.2f})")
            with badge_col3:
                entities = article.get("entities", {})
                entity_count = sum(len(v) if isinstance(v, list) else 0 for v in entities.values())
                if entity_count > 0:
                    st.markdown(f"**Entities:** {entity_count} mentioned")

            # Action buttons - all styled consistently
            button_col1, button_col2, button_col3, button_col4 = st.columns(4)
            with button_col1:
                if st.button(
                    "Read Full" if not is_expanded else "Collapse",
                    key=f"expand_{article_id}",
                    use_container_width=True,
                ):
                    if is_expanded:
                        st.session_state.expanded_articles.discard(article_id)
                    else:
                        st.session_state.expanded_articles.add(article_id)
                    st.rerun()
            with button_col2:
                article_url = article.get("url", "")
                if article_url:
                    # Use link_button which has consistent styling with st.button
                    st.link_button("View Source", article_url, use_container_width=True)
            with button_col3:
                # Share functionality - button that copies to clipboard
                article_url = article.get("url", "")
                share_text = f"{article.get('title', '')} - {article_url}"
                share_clicked = st.button("Share", key=f"share_btn_{article_id}", use_container_width=True)
                if share_clicked:
                    # Copy to clipboard using JavaScript
                    st.markdown(
                        f"""
                        <script>
                        (function() {{
                            const text = {repr(share_text)};
                            if (navigator.clipboard && navigator.clipboard.writeText) {{
                                navigator.clipboard.writeText(text);
                            }}
                        }})();
                        </script>
                    """,
                        unsafe_allow_html=True,
                    )
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
                if related and related.get("articles"):
                    for related_article in related["articles"]:
                        st.markdown(
                            f"- [{related_article.get('title', 'No title')}]"
                            f"({related_article.get('url', '#')})"
                            f" ({related_article.get('date', '')[:10]})"
                        )
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
            export_data.append(
                {
                    "id": article.get("id"),
                    "title": article.get("title", ""),
                    "url": article.get("url", ""),
                    "date": article.get("date", ""),
                    "domain": article.get("domain", ""),
                    "country": article.get("country", ""),
                    "partisan": article.get("partisan", ""),
                    "sentiment": article.get("sentiment", ""),
                    "categories": ", ".join(article.get("categories", [])),
                    "description": article.get("description", ""),
                }
            )

        if export_format == "CSV":
            df_export = pd.DataFrame(export_data)
            csv = df_export.to_csv(index=False)
            st.sidebar.download_button(
                "Download CSV",
                data=csv,
                file_name=f"namo_articles_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )
        else:  # JSON
            json_data = json.dumps(export_data, indent=2, ensure_ascii=False)
            st.sidebar.download_button(
                "Download JSON",
                data=json_data,
                file_name=f"namo_articles_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
            )
