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


def select_latest_articles(response: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
    if not response:
        return []
    articles = response.get("articles") or []
    if not isinstance(articles, list):
        return []
    return articles[:limit]
