from typing import Iterable, List, Dict, Any


def normalize_domain(domain: str) -> str:
    if not domain:
        return domain
    lowered = domain.strip().lower()
    if lowered == "document.no":
        return "www.document.no"
    return lowered


def filter_outlets(outlets: Iterable[Dict], query: str) -> List[Dict]:
    if not query:
        return list(outlets)
    needle = query.strip().lower()
    if not needle:
        return list(outlets)
    filtered = []
    for outlet in outlets:
        name = (outlet.get("outlet_name") or outlet.get("domain") or "").lower()
        if needle in name:
            filtered.append(outlet)
    return filtered


def consolidate_outlets(outlets: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_domain: Dict[str, Dict[str, Any]] = {}
    for outlet in outlets:
        domain = normalize_domain(outlet.get("domain"))
        if not domain:
            continue
        current = by_domain.get(domain)
        if not current:
            by_domain[domain] = {
                "domain": domain,
                "outlet_name": outlet.get("outlet_name"),
                "country": outlet.get("country"),
                "partisan": outlet.get("partisan"),
                "count": outlet.get("count", 0) or 0,
            }
            continue
        current["count"] += outlet.get("count", 0) or 0
        for key in ("outlet_name", "country", "partisan"):
            if not current.get(key) and outlet.get(key):
                current[key] = outlet.get(key)
    return list(by_domain.values())


def best_article_count(*values: Any) -> int:
    counts: List[int] = []
    for value in values:
        try:
            count = int(value or 0)
        except (TypeError, ValueError):
            continue
        if count >= 0:
            counts.append(count)
    return max(counts, default=0)


def related_outlets(
    outlets: Iterable[Dict[str, Any]],
    selected_domain: str,
    country: str | None = None,
    partisan: str | None = None,
    limit: int = 6,
) -> List[Dict[str, Any]]:
    selected = normalize_domain(selected_domain)
    target_country = str(country or "").strip().lower()
    target_partisan = str(partisan or "").strip().lower()
    candidates = []

    for outlet in outlets or []:
        domain = normalize_domain(outlet.get("domain") or "")
        if not domain or domain == selected:
            continue
        outlet_country = str(outlet.get("country") or outlet.get("country_code") or "").strip().lower()
        outlet_partisan = str(outlet.get("partisan") or "").strip().lower()
        score = 0
        if target_country and outlet_country == target_country:
            score += 2
        if target_partisan and outlet_partisan == target_partisan:
            score += 1
        if score <= 0:
            continue
        candidate = dict(outlet)
        candidate["domain"] = domain
        candidate["_related_score"] = score
        candidates.append(candidate)

    candidates.sort(
        key=lambda item: (
            -int(item.get("_related_score", 0)),
            -best_article_count(item.get("count", 0)),
            str(item.get("domain") or ""),
        )
    )
    return candidates[:limit]


def select_latest_articles(response: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
    if not response:
        return []
    articles = response.get("articles") or []
    if not isinstance(articles, list):
        return []
    return articles[:limit]


def latest_article_dates_by_domain(response: Dict[str, Any]) -> Dict[str, str]:
    if not response:
        return {}
    articles = response.get("articles") or []
    if not isinstance(articles, list):
        return {}

    latest: Dict[str, str] = {}
    for article in articles:
        domain = normalize_domain(article.get("domain") or "")
        date = str(article.get("date") or "")[:10]
        if not domain or not date:
            continue
        if domain not in latest:
            latest[domain] = date
    return latest
