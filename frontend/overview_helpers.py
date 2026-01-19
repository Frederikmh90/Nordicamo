from typing import Tuple, Optional, Dict, Any


def format_freshness(freshness: Optional[Dict[str, Any]]) -> Tuple[str, str]:
    if not freshness or freshness.get("hours_ago") is None:
        return ("Freshness data unavailable", "N/A")

    hours_ago = freshness.get("hours_ago", 0)
    if hours_ago < 24:
        freshness_text = f"Last updated: {hours_ago} hours ago"
    elif hours_ago < 168:
        days_ago = hours_ago // 24
        freshness_text = f"Last updated: {days_ago} days ago"
    else:
        weeks_ago = hours_ago // 168
        freshness_text = f"Last updated: {weeks_ago} weeks ago"

    last_article = freshness.get("last_article_date", "N/A")
    if last_article and last_article != "N/A":
        last_article_formatted = str(last_article)[:10]
    else:
        last_article_formatted = "N/A"

    return (freshness_text, last_article_formatted)
