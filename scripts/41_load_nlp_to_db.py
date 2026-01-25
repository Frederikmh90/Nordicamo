"""
ETL: load NLP-enriched parquet into Postgres articles table.

Assumptions
- articles table has columns:
  url (unique, not null), sentiment, sentiment_score, categories (jsonb),
  entities_json (jsonb), topic_id, topic_probability, url_hash (optional).
- A UNIQUE constraint exists on url.
- Environment variables for DB connection:
  DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

Usage
  source .venv/bin/activate
  python scripts/41_load_nlp_to_db.py --input data/nlp_enriched/file.parquet --batch-size 5000
"""

import argparse
import json
import os
from typing import Iterable, List, Tuple

import polars as pl
import psycopg2
from psycopg2.extras import execute_values


def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        user=os.getenv("DB_USER", "namo_user"),
        password=os.getenv("DB_PASSWORD", "<DB_PASSWORD>"),
        dbname=os.getenv("DB_NAME", "namo_db"),
    )


def iter_batches(df: pl.DataFrame, batch_size: int) -> Iterable[pl.DataFrame]:
    for start in range(0, len(df), batch_size):
        yield df[start : start + batch_size]


def normalize_row(row: dict) -> Tuple:
    url = row.get("url")
    if not url:
        return None

    sentiment = row.get("sentiment")
    sentiment_score = row.get("sentiment_score")

    categories = row.get("categories")
    if isinstance(categories, str):
        try:
            categories = json.loads(categories)
        except Exception:
            categories = []
    if categories is None:
        categories = []

    entities = row.get("entities_json")
    if isinstance(entities, str):
        try:
            entities = json.loads(entities)
        except Exception:
            entities = {}
    if entities is None:
        entities = {}

    topic_id = row.get("topic_id")
    topic_probability = row.get("topic_probability")

    return (
        url,
        sentiment,
        sentiment_score,
        json.dumps(categories),
        json.dumps(entities),
        topic_id,
        topic_probability,
    )


def upsert_batch(conn, rows: List[Tuple]):
    if not rows:
        return

    sql = """
    INSERT INTO articles (
        url, sentiment, sentiment_score, categories, entities_json, topic_id, topic_probability
    ) VALUES %s
    ON CONFLICT (url) DO UPDATE SET
        sentiment = EXCLUDED.sentiment,
        sentiment_score = EXCLUDED.sentiment_score,
        categories = EXCLUDED.categories,
        entities_json = EXCLUDED.entities_json,
        topic_id = EXCLUDED.topic_id,
        topic_probability = EXCLUDED.topic_probability;
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, rows, page_size=1000)
    conn.commit()


def main():
    parser = argparse.ArgumentParser(description="Upsert NLP outputs into articles table.")
    parser.add_argument("--input", required=True, help="Path to NLP-enriched parquet file")
    parser.add_argument("--batch-size", type=int, default=5000, help="Batch size for upserts")
    args = parser.parse_args()

    df = pl.read_parquet(args.input)
    needed = {"url", "sentiment", "sentiment_score", "categories", "entities_json", "topic_id", "topic_probability"}
    missing = needed - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in input file: {missing}")

    conn = get_conn()
    try:
        total = 0
        for batch in iter_batches(df, args.batch_size):
            prepared = []
            for row in batch.iter_rows(named=True):
                normalized = normalize_row(row)
                if normalized:
                    prepared.append(normalized)
            upsert_batch(conn, prepared)
            total += len(prepared)
            print(f"Upserted {total} rows...", flush=True)
        print(f"Done. Upserted {total} rows total.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()


