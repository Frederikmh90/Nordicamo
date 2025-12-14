"""
NAMO NLP Processing Pipeline - Database-Driven Version
======================================================
Queries database for unprocessed articles and processes them in batches.
Updates database directly after each batch.

Usage:
    python scripts/02_nlp_processing_from_db.py \
        --total-articles 200 \
        --chunk-size 50 \
        --model mistralai/Mistral-7B-Instruct-v0.3
"""

import polars as pl
import json
import os
import time
from pathlib import Path
from typing import List, Dict, Optional
from tqdm import tqdm
import logging
from datetime import datetime
import argparse
import sys
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import NLPProcessor
import importlib.util
nlp_script_path = Path(__file__).parent / "02_nlp_processing.py"
spec = importlib.util.spec_from_file_location("nlp_processing", nlp_script_path)
nlp_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nlp_module)
NLPProcessor = nlp_module.NLPProcessor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'user': os.getenv('DB_USER', 'namo_user'),
    'password': os.getenv('DB_PASSWORD', 'namo_password'),
    'database': os.getenv('DB_NAME', 'namo_db')
}


def get_unprocessed_articles(conn, limit: int, offset: int = 0) -> pl.DataFrame:
    """Query database for articles that need NLP processing."""
    query = f"""
        SELECT 
            id,
            url,
            title,
            description,
            content,
            country,
            domain,
            date,
            scraped_at
        FROM articles
        WHERE (nlp_processed_at IS NULL OR sentiment IS NULL)
          AND content IS NOT NULL
          AND LENGTH(content) > 50
        ORDER BY id
        LIMIT {limit}
        OFFSET {offset}
    """
    
    df = pl.read_database(query, conn)
    return df


def count_unprocessed_articles(conn) -> int:
    """Count how many articles need processing."""
    query = """
        SELECT COUNT(*) as count
        FROM articles
        WHERE (nlp_processed_at IS NULL OR sentiment IS NULL)
          AND content IS NOT NULL
          AND LENGTH(content) > 50
    """
    with conn.cursor() as cur:
        cur.execute(query)
        result = cur.fetchone()
        return result[0] if result else 0


def update_articles_batch(conn, results: List[Dict]):
    """Update articles in database with NLP results."""
    if not results:
        return
    
    sql = """
        UPDATE articles
        SET 
            sentiment = %s,
            sentiment_score = %s,
            categories = %s::jsonb,
            entities_json = %s::jsonb,
            nlp_processed_at = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """
    
    data = []
    for r in results:
        data.append((
            r['sentiment'],
            r['sentiment_score'],
            json.dumps(r['categories']),
            json.dumps(r['entities']),
            datetime.now(),
            r['article_id']
        ))
    
    with conn.cursor() as cur:
        execute_values(cur, sql, data, page_size=100)
    conn.commit()


def process_chunk(
    processor: NLPProcessor,
    chunk_df: pl.DataFrame,
    chunk_num: int,
    total_chunks: int
) -> List[Dict]:
    """Process a single chunk of articles and return results."""
    logger.info(f"Processing chunk {chunk_num}/{total_chunks} ({len(chunk_df)} articles)...")
    start_time = time.time()
    
    results = []
    for row in tqdm(chunk_df.iter_rows(named=True), total=len(chunk_df), desc=f"Chunk {chunk_num}"):
        article_id = row.get("id")
        content = row.get("content", "")
        title = row.get("title", "")
        description = row.get("description", "")
        country = row.get("country", "")
        
        if not content or len(content.strip()) < 50:
            content = f"{title}\n\n{description}".strip()
            if len(content) < 50:
                results.append({
                    "article_id": article_id,
                    "sentiment": "neutral",
                    "sentiment_score": 0.0,
                    "categories": ["Other"],
                    "entities": {"persons": [], "locations": [], "organizations": []},
                })
                continue
        
        # Process article
        result = processor.process_article(content, country)
        result["article_id"] = article_id
        results.append(result)
    
    elapsed = time.time() - start_time
    avg_time = elapsed / len(chunk_df)
    logger.info(f"✓ Chunk {chunk_num} completed in {elapsed:.1f}s ({avg_time:.1f}s/article)")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="NAMO NLP Processing Pipeline - Database-Driven"
    )
    parser.add_argument(
        "--total-articles",
        type=int,
        default=200,
        help="Total number of articles to process (default: 200)"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=50,
        help="Number of articles per chunk (default: 50)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="mistralai/Mistral-7B-Instruct-v0.3",
        help="LLM model to use"
    )
    parser.add_argument(
        "--use-quantization",
        action="store_true",
        help="Enable 4-bit quantization (saves GPU memory)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Query and show articles but don't process"
    )
    
    args = parser.parse_args()
    
    # Connect to database
    logger.info("Connecting to database...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        logger.info("✓ Connected to database")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        logger.error(f"Config: host={DB_CONFIG['host']}, db={DB_CONFIG['database']}")
        return
    
    # Count unprocessed articles
    total_unprocessed = count_unprocessed_articles(conn)
    logger.info(f"Found {total_unprocessed} unprocessed articles in database")
    
    if total_unprocessed == 0:
        logger.info("No articles need processing!")
        conn.close()
        return
    
    # Determine how many to process
    articles_to_process = min(args.total_articles, total_unprocessed)
    logger.info(f"Will process {articles_to_process} articles")
    
    if args.dry_run:
        logger.info("DRY RUN - Querying articles...")
        df = get_unprocessed_articles(conn, limit=min(10, articles_to_process))
        logger.info(f"Sample articles:")
        print(df.select(["id", "url", "title"]).head(5))
        conn.close()
        return
    
    # Initialize NLP processor
    logger.info("Initializing NLP Processor...")
    processor = NLPProcessor(
        model_name=args.model,
        use_quantization=args.use_quantization,
        batch_size=1,
    )
    logger.info("✓ NLP Processor initialized")
    
    # Process in chunks
    total_chunks = (articles_to_process + args.chunk_size - 1) // args.chunk_size
    total_processed = 0
    
    logger.info(f"Processing {articles_to_process} articles in {total_chunks} chunks of {args.chunk_size}")
    logger.info("=" * 80)
    
    for chunk_num in range(total_chunks):
        # Calculate offset
        offset = chunk_num * args.chunk_size
        limit = min(args.chunk_size, articles_to_process - offset)
        
        # Get chunk from database
        logger.info(f"Fetching chunk {chunk_num + 1}/{total_chunks} from database...")
        chunk_df = get_unprocessed_articles(conn, limit=limit, offset=offset)
        
        if len(chunk_df) == 0:
            logger.warning(f"No more articles to process at offset {offset}")
            break
        
        # Process chunk
        results = process_chunk(processor, chunk_df, chunk_num + 1, total_chunks)
        
        # Update database
        logger.info(f"Updating database with {len(results)} results...")
        try:
            update_articles_batch(conn, results)
            logger.info(f"✓ Updated {len(results)} articles in database")
            total_processed += len(results)
        except Exception as e:
            logger.error(f"Failed to update database: {e}")
            conn.rollback()
            continue
        
        # Small delay between chunks
        if chunk_num < total_chunks - 1:
            time.sleep(2)
    
    # Summary
    conn.close()
    logger.info("=" * 80)
    logger.info("PROCESSING COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total articles processed: {total_processed}")
    
    # Check remaining
    conn = psycopg2.connect(**DB_CONFIG)
    remaining = count_unprocessed_articles(conn)
    conn.close()
    logger.info(f"Remaining unprocessed articles: {remaining}")


if __name__ == "__main__":
    main()

