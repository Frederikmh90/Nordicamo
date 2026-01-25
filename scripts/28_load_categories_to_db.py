#!/usr/bin/env python3
"""
Load category classification results into PostgreSQL database.
Updates the articles table with category information.
"""

import polars as pl
import json
from pathlib import Path
import psycopg2
from psycopg2.extras import execute_batch
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'user': os.getenv('DB_USER', 'namo_user'),
    'password': os.getenv('DB_PASSWORD', '<DB_PASSWORD>'),
    'database': os.getenv('DB_NAME', 'namo_db')
}


def load_categories_to_db(parquet_file: str):
    """Load category classification results into database."""
    parquet_path = BASE_DIR / parquet_file
    
    if not parquet_path.exists():
        logger.error(f"Parquet file not found: {parquet_path}")
        return
    
    logger.info(f"Loading categories from {parquet_path}")
    df = pl.read_parquet(parquet_path)
    logger.info(f"Loaded {len(df)} articles")
    
    # Check required columns
    required_cols = ["url", "category"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return
    
    # Connect to database
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check if category column exists, if not add it
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='articles' AND column_name='category'
        """)
        column_exists = cursor.fetchone()
        
        if not column_exists:
            logger.info("Adding 'category' column to articles table...")
            cursor.execute("ALTER TABLE articles ADD COLUMN category VARCHAR(100)")
            cursor.execute("ALTER TABLE articles ADD COLUMN category_reasoning TEXT")
            cursor.execute("ALTER TABLE articles ADD COLUMN category_processed_at TIMESTAMP")
            conn.commit()
            logger.info("✅ Added category columns")
        
        # Prepare update data
        update_data = []
        for row in df.iter_rows(named=True):
            url = row.get("url")
            category = row.get("category", "Other")
            category_reasoning = row.get("category_reasoning", "")
            category_processed_at = row.get("category_processed_at", "")
            
            if url:
                # Note: categories column is JSONB, so we need to store as JSON array
                categories_json = json.dumps([category])
                update_data.append((category, category_reasoning, category_processed_at, categories_json, url))
        
        # Batch update
        update_query = """
            UPDATE articles 
            SET category = %s,
                category_reasoning = %s,
                category_processed_at = %s,
                categories = %s::jsonb
            WHERE url = %s
        """
        
        execute_batch(cursor, update_query, update_data, page_size=100)
        conn.commit()
        
        updated = cursor.rowcount
        logger.info(f"✅ Updated {updated} articles with categories")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error loading categories: {e}")
        if 'conn' in locals():
            conn.rollback()
        raise


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Load category classifications into database")
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to parquet file with category classifications",
    )
    
    args = parser.parse_args()
    load_categories_to_db(args.input)


if __name__ == "__main__":
    main()

