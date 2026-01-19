from typing import Iterable, List, Dict


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
