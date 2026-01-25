#!/usr/bin/env python3
"""
Load NER results into PostgreSQL database.
Updates the entities_json column in the articles table.
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


def load_ner_to_db(parquet_file: str):
    """Load NER results into database."""
    parquet_path = BASE_DIR / parquet_file if not Path(parquet_file).is_absolute() else Path(parquet_file)
    
    if not parquet_path.exists():
        logger.error(f"Parquet file not found: {parquet_path}")
        return
    
    logger.info(f"Loading NER results from {parquet_path}")
    df = pl.read_parquet(parquet_path)
    logger.info(f"Loaded {len(df)} articles")
    
    # Check required columns
    required_cols = ["url", "entities_json"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return
    
    # Connect to database
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check if entities_json column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='articles' AND column_name='entities_json'
        """)
        entities_json_exists = cursor.fetchone()
        
        # Check if ner_processed_at column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='articles' AND column_name='ner_processed_at'
        """)
        ner_processed_at_exists = cursor.fetchone()
        
        if not entities_json_exists:
            logger.info("Adding 'entities_json' column to articles table...")
            cursor.execute("ALTER TABLE articles ADD COLUMN entities_json JSONB")
            conn.commit()
            logger.info("✅ Added entities_json column")
        
        if not ner_processed_at_exists:
            logger.info("Adding 'ner_processed_at' column to articles table...")
            cursor.execute("ALTER TABLE articles ADD COLUMN ner_processed_at TIMESTAMP")
            conn.commit()
            logger.info("✅ Added ner_processed_at column")
        
        # Prepare update data
        update_data = []
        for row in df.iter_rows(named=True):
            url = row.get("url")
            entities_json = row.get("entities_json", "{}")
            ner_processed_at = row.get("ner_processed_at", "")
            
            if url:
                # Ensure entities_json is valid JSON string
                if isinstance(entities_json, str):
                    try:
                        # Validate JSON
                        json.loads(entities_json)
                    except:
                        entities_json = "{}"
                else:
                    entities_json = json.dumps(entities_json) if entities_json else "{}"
                
                update_data.append((entities_json, ner_processed_at, url))
        
        # Batch update
        update_query = """
            UPDATE articles 
            SET entities_json = %s::jsonb,
                ner_processed_at = %s
            WHERE url = %s
        """
        
        execute_batch(cursor, update_query, update_data, page_size=100)
        conn.commit()
        
        updated = len(update_data)
        logger.info(f"✅ Updated {updated} articles with NER results")
        
        # Statistics
        cursor.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE entities_json IS NOT NULL) as with_entities,
                COUNT(*) as total
            FROM articles
        """)
        result = cursor.fetchone()
        logger.info(f"Articles with entities: {result[0]:,} / {result[1]:,}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error loading NER results: {e}")
        if 'conn' in locals():
            conn.rollback()
        raise


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Load NER results into database")
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to parquet file with NER results",
    )
    
    args = parser.parse_args()
    load_ner_to_db(args.input)


if __name__ == "__main__":
    main()

