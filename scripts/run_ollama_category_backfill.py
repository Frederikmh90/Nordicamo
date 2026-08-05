#!/usr/bin/env python3
"""Backfill missing Nordicamo article categories through the local Ollama Mistral model."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Iterable

import psycopg2


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
CATEGORY_BY_CASEFOLD = {category.casefold(): category for category in CATEGORY_LABELS}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="mistral:7b", help="Installed Ollama model name")
    parser.add_argument("--limit", type=int, required=True, help="Maximum eligible articles to process")
    parser.add_argument("--commit-interval", type=int, default=25, help="Database commits per N updates")
    parser.add_argument("--max-words", type=int, default=500, help="Article text limit sent to the model")
    parser.add_argument("--timeout", type=int, default=180, help="Ollama request timeout in seconds")
    parser.add_argument("--dry-run", action="store_true", help="Classify but do not update Postgres")
    return parser.parse_args()


def database_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "namo_db"),
        user=os.getenv("DB_USER", "namo_user"),
        password=os.getenv("DB_PASSWORD", "namo_password"),
    )


def eligible_articles(conn, limit: int) -> Iterable[tuple[int, str]]:
    query = """
        SELECT id, COALESCE(NULLIF(BTRIM(content), ''), NULLIF(BTRIM(title), '')) AS article_text
        FROM articles
        WHERE (categories IS NULL OR categories = '[]'::jsonb)
          AND COALESCE(NULLIF(BTRIM(content), ''), NULLIF(BTRIM(title), '')) IS NOT NULL
        ORDER BY date DESC NULLS LAST, id DESC
        LIMIT %s
    """
    with conn.cursor() as cursor:
        cursor.execute(query, (limit,))
        yield from cursor.fetchall()


def canonical_categories(value: object) -> list[str]:
    if not isinstance(value, list):
        return ["Other"]
    categories = []
    for category in value:
        canonical = CATEGORY_BY_CASEFOLD.get(str(category).strip().casefold())
        if canonical and canonical not in categories:
            categories.append(canonical)
    return categories[:3] or ["Other"]


def classify_article(model: str, article_text: str, max_words: int, timeout: int) -> list[str]:
    text = " ".join(article_text.split()[:max_words])
    prompt = (
        "Classify this Nordic alternative news article. Choose one to three categories only from this exact list: "
        f"{json.dumps(CATEGORY_LABELS)}. Return only valid JSON in exactly this form: "
        '{"categories":["Category"]}.\n\n'
        f"Article:\n{text}"
    )
    payload = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0},
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        result = json.load(response)
    try:
        parsed = json.loads(result["response"])
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Ollama returned invalid category JSON: {result!r}") from exc
    return canonical_categories(parsed.get("categories"))


def save_category(conn, article_id: int, categories: list[str]) -> bool:
    query = """
        UPDATE articles
        SET categories = %s::jsonb, nlp_processed_at = NOW(), updated_at = NOW()
        WHERE id = %s
          AND (categories IS NULL OR categories = '[]'::jsonb)
    """
    with conn.cursor() as cursor:
        cursor.execute(query, (json.dumps(categories), article_id))
        return cursor.rowcount == 1


def main() -> int:
    args = parse_args()
    if args.limit < 1:
        raise SystemExit("--limit must be positive")
    if args.commit_interval < 1:
        raise SystemExit("--commit-interval must be positive")

    with database_connection() as conn:
        articles = list(eligible_articles(conn, args.limit))
        print(f"Eligible articles selected: {len(articles):,}", flush=True)
        processed = updated = failed = 0
        started = time.monotonic()
        for index, (article_id, article_text) in enumerate(articles, start=1):
            try:
                categories = classify_article(args.model, article_text, args.max_words, args.timeout)
                processed += 1
                if args.dry_run:
                    print(f"DRY RUN id={article_id} categories={categories}", flush=True)
                elif save_category(conn, article_id, categories):
                    updated += 1
                if not args.dry_run and index % args.commit_interval == 0:
                    conn.commit()
                elapsed = max(time.monotonic() - started, 0.001)
                print(
                    f"{index}/{len(articles)} id={article_id} categories={categories} "
                    f"updated={updated} rate={processed / elapsed:.2f}/s",
                    flush=True,
                )
            except (RuntimeError, urllib.error.URLError, TimeoutError) as exc:
                failed += 1
                print(f"ERROR id={article_id}: {exc}", file=sys.stderr, flush=True)
        if not args.dry_run:
            conn.commit()
    print(f"Complete: processed={processed} updated={updated} failed={failed}", flush=True)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
