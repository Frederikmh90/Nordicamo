"""Pure helpers for the bounded Nordicamo research workshop."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any
from urllib.parse import urlparse


MAX_BROWSER_PREVIEW_ROWS = 100
CATEGORY_LABELS = (
    "Politics & Governance",
    "Immigration & National Identity",
    "Health & Medicine",
    "Media & Censorship",
    "International Relations & Conflict",
    "Economy & Labor",
    "Crime & Justice",
    "Social Issues & Culture",
    "Environment, Climate & Energy",
    "Technology, Science & Digital Society",
    "Other",
)
CATEGORY_LABELS_BY_CASEFOLD = {label.casefold(): label for label in CATEGORY_LABELS}


@dataclass(frozen=True)
class WorkshopProject:
    key: str
    title: str
    question: str
    description: str


WORKSHOP_PROJECTS = (
    WorkshopProject(
        key="compare_agendas",
        title="Compare national agendas",
        question="How do two national alternative media landscapes develop over time?",
        description="Compare publication volume and inspect a bounded sample of the articles behind each country.",
    ),
    WorkshopProject(
        key="outlet_drivers",
        title="Find outlet drivers",
        question="Which outlets account for the most indexed publication activity in a selected period?",
        description="Identify the outlets driving a pattern, then inspect the underlying article sample.",
    ),
    WorkshopProject(
        key="trace_topic",
        title="Trace a topic",
        question="How does a selected topic develop within one national media landscape?",
        description="Follow category trends, select outlets, and review the relevant article records.",
    ),
    WorkshopProject(
        key="reporting_case",
        title="Build a reporting case",
        question="Which indexed articles provide an evidence base for a reporting or teaching case?",
        description="Build a bounded article selection around a country, time period, outlets, and keyword.",
    ),
)


def project_by_key(value: str | None) -> WorkshopProject:
    for project in WORKSHOP_PROJECTS:
        if project.key == value:
            return project
    return WORKSHOP_PROJECTS[0]


def format_category_labels(value: object) -> str:
    """Present category values as clean, canonical labels in the browser."""
    labels: list[str] = []

    def append_value(item: object) -> None:
        if isinstance(item, (list, tuple)):
            for nested_item in item:
                append_value(nested_item)
            return
        text = str(item or "").strip()
        if not text:
            return
        if text.startswith("["):
            try:
                append_value(json.loads(text))
                return
            except json.JSONDecodeError:
                text = text.strip("[] \\t\\r\\n\\\"'")
        canonical = CATEGORY_LABELS_BY_CASEFOLD.get(text.casefold(), text)
        if canonical and canonical not in labels:
            labels.append(canonical)

    append_value(value)
    return ", ".join(labels[:3]) if labels else "Not yet categorized"


def preview_records(articles: list[dict[str, Any]], max_rows: int = MAX_BROWSER_PREVIEW_ROWS) -> list[dict[str, str]]:
    """Return metadata-only rows suitable for the public browser preview."""
    rows: list[dict[str, str]] = []
    for article in articles[:max_rows]:
        rows.append(
            {
                "Date": str(article.get("date") or ""),
                "Country": str(article.get("country") or "").capitalize(),
                "Outlet": str(article.get("domain") or ""),
                "Orientation": str(article.get("partisan") or ""),
                "Categories": format_category_labels(article.get("categories")),
                "Title": str(article.get("title") or ""),
                "Article URL": str(article.get("url") or ""),
            }
        )
    return rows


def safe_article_url(value: object) -> str:
    """Return only absolute HTTP(S) article URLs for browser links."""
    url = str(value or "").strip()
    return url if urlparse(url).scheme in {"http", "https"} else ""


def build_access_request_context(
    project: WorkshopProject,
    countries: list[str],
    date_from: str,
    date_to: str,
    outlets: list[str] | None = None,
    categories: list[str] | None = None,
    keyword: str | None = None,
) -> str:
    """Create a concise, reproducible description for an access request."""
    country_label = ", ".join(country.capitalize() for country in countries if country) or "Not specified"
    lines = [
        f"Workshop: {project.title}",
        f"Research question: {project.question}",
        f"Countries: {country_label}",
        f"Period: {date_from} to {date_to}",
    ]
    if outlets:
        lines.append(f"Selected outlets: {', '.join(outlets)}")
    if categories:
        lines.append(f"Selected categories: {', '.join(categories)}")
    if keyword:
        lines.append(f"Keyword: {keyword}")
    lines.extend(
        [
            "Purpose and affiliation: [Please add before sending]",
            "Requested fields: article ID, date, country, outlet, orientation, categories, title, and URL.",
        ]
    )
    return "\n".join(lines)
