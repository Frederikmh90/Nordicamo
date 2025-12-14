"""
Debug Missing Categories
========================
Investigates why articles don't have categories assigned.
"""

import polars as pl
import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "nlp_enriched"


def debug_missing_categories(parquet_path: Path):
    """Debug articles without categories."""
    logger.info(f"Loading data from {parquet_path}")
    df = pl.read_parquet(parquet_path)
    
    total = len(df)
    
    # Find articles without categories
    no_categories = df.filter(
        (pl.col("categories").is_null()) | 
        (pl.col("categories") == "[]") |
        (pl.col("categories") == "")
    )
    
    logger.info(f"\n{'='*80}")
    logger.info("MISSING CATEGORIES ANALYSIS")
    logger.info(f"{'='*80}")
    logger.info(f"Total articles: {total}")
    logger.info(f"Articles without categories: {len(no_categories)} ({len(no_categories)/total*100:.1f}%)")
    
    # Analyze by country
    logger.info(f"\nMissing categories by country:")
    by_country = no_categories.group_by("country").len().sort("len", descending=True)
    for row in by_country.iter_rows(named=True):
        logger.info(f"  {row['country']:15s}: {row['len']:4d} articles")
    
    # Analyze by sentiment
    logger.info(f"\nMissing categories by sentiment:")
    by_sentiment = no_categories.group_by("sentiment").len().sort("len", descending=True)
    for row in by_sentiment.iter_rows(named=True):
        logger.info(f"  {row['sentiment']:10s}: {row['len']:4d} articles")
    
    # Analyze by domain/outlet
    logger.info(f"\nTop 10 outlets with missing categories:")
    by_domain = no_categories.group_by("domain").len().sort("len", descending=True).head(10)
    for row in by_domain.iter_rows(named=True):
        logger.info(f"  {row['domain']:40s}: {row['len']:4d} articles")
    
    # Sample articles for manual review
    logger.info(f"\n{'='*80}")
    logger.info("SAMPLE ARTICLES WITHOUT CATEGORIES")
    logger.info(f"{'='*80}")
    
    samples = no_categories.sample(min(10, len(no_categories)))
    
    for i, row in enumerate(samples.iter_rows(named=True), 1):
        logger.info(f"\n{i}. Title: {row['title'][:100]}")
        logger.info(f"   Domain: {row['domain']}")
        logger.info(f"   Country: {row['country']}")
        logger.info(f"   Sentiment: {row['sentiment']}")
        logger.info(f"   Categories: {row['categories']}")
        logger.info(f"   Content length: {len(row['content']) if row['content'] else 0} chars")
        logger.info(f"   Content preview: {row['content'][:200] if row['content'] else 'No content'}...")
    
    # Check if content length is a factor
    logger.info(f"\n{'='*80}")
    logger.info("CONTENT LENGTH ANALYSIS")
    logger.info(f"{'='*80}")
    
    with_categories = df.filter(
        (pl.col("categories").is_not_null()) & 
        (pl.col("categories") != "[]") &
        (pl.col("categories") != "")
    )
    
    avg_length_with = with_categories.select(pl.col("content").str.len_chars().mean()).item()
    avg_length_without = no_categories.select(pl.col("content").str.len_chars().mean()).item()
    
    logger.info(f"Average content length WITH categories: {avg_length_with:.0f} chars")
    logger.info(f"Average content length WITHOUT categories: {avg_length_without:.0f} chars")
    
    # Check for very short articles
    short_articles = no_categories.filter(pl.col("content").str.len_chars() < 100)
    logger.info(f"\nVery short articles (<100 chars) without categories: {len(short_articles)}")
    
    return {
        "total": total,
        "without_categories": len(no_categories),
        "percentage": len(no_categories)/total*100,
        "avg_content_length_with": avg_length_with,
        "avg_content_length_without": avg_length_without,
        "short_articles_count": len(short_articles)
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Debug missing categories')
    parser.add_argument('--input', type=str, default='data/nlp_enriched/nlp_enriched_NAMO_preprocessed_test.parquet')
    
    args = parser.parse_args()
    input_path = Path(args.input)
    
    if not input_path.exists():
        logger.error(f"File not found: {input_path}")
    else:
        debug_missing_categories(input_path)

