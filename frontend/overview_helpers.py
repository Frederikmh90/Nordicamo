from typing import Tuple, Optional, Dict, Any, List, Iterable, Mapping, Sequence


def format_freshness(freshness: Optional[Dict[str, Any]]) -> Tuple[str, str]:
    if not freshness or freshness.get("hours_ago") is None:
        return ("Freshness data unavailable", "N/A")

    hours_ago = freshness.get("hours_ago", 0)
    if hours_ago < 24:
        freshness_text = f"Dashboard last updated: {hours_ago} hours ago"
    elif hours_ago < 168:
        days_ago = hours_ago // 24
        freshness_text = f"Dashboard last updated: {days_ago} days ago"
    else:
        weeks_ago = hours_ago // 168
        freshness_text = f"Dashboard last updated: {weeks_ago} weeks ago"

    last_article = freshness.get("last_article_date", "N/A")
    if last_article and last_article != "N/A":
        last_article_formatted = str(last_article)[:10]
    else:
        last_article_formatted = "N/A"

    return (freshness_text, last_article_formatted)


def compute_country_shares(
    series_by_country: Dict[str, List[Dict[str, Any]]]
) -> Dict[str, List[Dict[str, Any]]]:
    if not series_by_country:
        return {}

    dates = set()
    country_counts = {}
    for country, rows in series_by_country.items():
        counts = {}
        for row in rows or []:
            date = row.get("date")
            if date is None:
                continue
            counts[str(date)] = int(row.get("count", 0))
            dates.add(str(date))
        country_counts[country] = counts

    if not dates:
        return {}

    ordered_dates = sorted(dates)
    totals = {}
    for date in ordered_dates:
        totals[date] = sum(counts.get(date, 0) for counts in country_counts.values())

    shares = {}
    for country, counts in country_counts.items():
        rows = []
        for date in ordered_dates:
            total = totals.get(date, 0)
            count = counts.get(date, 0)
            share = (count / total) if total else 0
            rows.append(
                {
                    "date": date,
                    "count": count,
                    "total": total,
                    "share": share,
                }
            )
        shares[country] = rows
    return shares


def compute_top_n_share(
    rows: Iterable[Mapping[str, Any]],
    n: int = 5,
    count_key: str = "count",
) -> float:
    counts = []
    for row in rows or []:
        try:
            counts.append(int(row.get(count_key, 0)))
        except (TypeError, ValueError):
            counts.append(0)
    total = sum(counts)
    if total <= 0:
        return 0.0
    top_n = sorted(counts, reverse=True)[:n]
    return sum(top_n) / total


def compute_partisan_shares(
    rows: Iterable[Mapping[str, Any]],
    partisan_key: str = "partisan",
    count_key: str = "count",
) -> Dict[str, float]:
    totals: Dict[str, int] = {}
    overall = 0
    for row in rows or []:
        partisan = row.get(partisan_key) or "Other"
        try:
            count = int(row.get(count_key, 0))
        except (TypeError, ValueError):
            count = 0
        totals[partisan] = totals.get(partisan, 0) + count
        overall += count

    if overall <= 0:
        return {}

    return {key: value / overall for key, value in totals.items()}


def compute_lorenz_curve(counts: Sequence[int]) -> Tuple[List[float], List[float], float]:
    cleaned = [max(int(value), 0) for value in counts if value is not None]
    if not cleaned:
        return [0.0, 1.0], [0.0, 1.0], 0.0

    sorted_counts = sorted(cleaned)
    total = sum(sorted_counts)
    if total <= 0:
        return [0.0, 1.0], [0.0, 1.0], 0.0

    cumulative = [0]
    running = 0
    for value in sorted_counts:
        running += value
        cumulative.append(running)

    n = len(sorted_counts)
    x = [i / n for i in range(0, n + 1)]
    y = [value / total for value in cumulative]

    area = 0.0
    for i in range(1, len(x)):
        area += (x[i] - x[i - 1]) * (y[i] + y[i - 1]) / 2
    gini = max(0.0, min(1.0, 1 - 2 * area))

    return x, y, gini
