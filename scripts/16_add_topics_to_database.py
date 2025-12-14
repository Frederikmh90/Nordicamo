"""
Add Topic Modeling Results to Database
======================================
Loads topic modeling results into PostgreSQL database.
Adds topic_id and topic_probability columns if they don't exist.
"""

import polars as pl
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
import logging
from tqdm import tqdm
import argparse

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def add_topic_columns(engine, table_name="articles"):
    """Add topic columns to articles table if they don't exist."""
    logger.info("Checking for topic columns...")
    
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    
    with engine.connect() as conn:
        if 'topic_id' not in columns:
            logger.info("Adding topic_id column...")
            conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN topic_id INTEGER"))
            conn.commit()
        
        if 'topic_probability' not in columns:
            logger.info("Adding topic_probability column...")
            conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN topic_probability FLOAT"))
            conn.commit()
        
        logger.info("Topic columns ready")


def load_topics_to_db(
    topics_file: Path,
    db_url: str,
    batch_size: int = 1000,
    table_name: str = "articles"
):
    """Load topic modeling results into database."""
    logger.info(f"Loading topics from {topics_file}")
    
    # Load topics data
    df_topics = pl.read_parquet(topics_file)
    logger.info(f"Loaded {len(df_topics):,} articles with topics")
    
    # Check required columns
    required_cols = ['url', 'topic_id', 'topic_probability']
    missing_cols = [col for col in required_cols if col not in df_topics.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Create database connection
    engine = create_engine(db_url)
    
    # Add topic columns if needed
    add_topic_columns(engine, table_name)
    
    # Convert to pandas for SQL operations
    df_pd = df_topics.select(['url', 'topic_id', 'topic_probability']).to_pandas()
    
    # Update articles with topics
    logger.info("Updating articles with topic assignments...")
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        total = len(df_pd)
        for i in tqdm(range(0, total, batch_size), desc="Updating topics"):
            batch = df_pd.iloc[i:i+batch_size]
            
            for _, row in batch.iterrows():
                session.execute(
                    text(f"""
                        UPDATE {table_name}
                        SET topic_id = :topic_id,
                            topic_probability = :topic_probability
                        WHERE url = :url
                    """),
                    {
                        "topic_id": int(row['topic_id']) if pd.notna(row['topic_id']) else None,
                        "topic_probability": float(row['topic_probability']) if pd.notna(row['topic_probability']) else None,
                        "url": row['url']
                    }
                )
            
            session.commit()
        
        logger.info("Topics loaded successfully")
        
        # Statistics
        result = session.execute(text(f"""
            SELECT 
                COUNT(*) FILTER (WHERE topic_id IS NOT NULL) as with_topics,
                COUNT(*) as total,
                COUNT(DISTINCT topic_id) as unique_topics
            FROM {table_name}
        """)).fetchone()
        
        logger.info(f"Articles with topics: {result[0]:,} / {result[1]:,}")
        logger.info(f"Unique topics: {result[2]}")
        
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description="Load topic modeling results into database")
    parser.add_argument(
        "--topics",
        type=str,
        required=False,
        help="Path to topics parquet file",
    )
    parser.add_argument(
        "--input",
        type=str,
        required=False,
        dest="topics",
        help="Path to topics parquet file (alias for --topics)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Database host",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5432,
        help="Database port",
    )
    parser.add_argument(
        "--user",
        type=str,
        default="namo_user",
        help="Database user",
    )
    parser.add_argument(
        "--password",
        type=str,
        default="namo_password",
        help="Database password",
    )
    parser.add_argument(
        "--database",
        type=str,
        default="namo_db",
        help="Database name",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Batch size for updates",
    )
    
    args = parser.parse_args()
    
    # Validate that topics file is provided
    if not args.topics:
        parser.error("Either --topics or --input must be provided")
    
    # Build database URL
    db_url = f"postgresql://{args.user}:{args.password}@{args.host}:{args.port}/{args.database}"
    
    # Load topics
    topics_file = Path(args.topics)
    if not topics_file.exists():
        raise FileNotFoundError(f"Topics file not found: {topics_file}")
    
    load_topics_to_db(
        topics_file,
        db_url,
        batch_size=args.batch_size
    )


if __name__ == "__main__":
    main()

