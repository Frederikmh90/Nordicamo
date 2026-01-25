"""
NAMO Database Loading Script
============================
Loads preprocessed and NLP-enriched data into PostgreSQL database.
Handles batch insertion, duplicate detection, and updates.
"""

import polars as pl
import psycopg2
from psycopg2.extras import execute_batch, execute_values
from pathlib import Path
import logging
from typing import List, Dict, Optional
from tqdm import tqdm
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_loading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'user': os.getenv('DB_USER', 'namo_user'),
    'password': os.getenv('DB_PASSWORD', '<DB_PASSWORD>'),
    'database': os.getenv('DB_NAME', 'namo_db')
}


class DatabaseLoader:
    """Handles loading data into PostgreSQL database."""
    
    def __init__(self, config: dict, batch_size: int = 1000):
        self.config = config
        self.batch_size = batch_size
        self.conn = None
        
    def connect(self):
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(**self.config)
            logger.info("Connected to database successfully")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def load_actors(self, actors_path: Path):
        """Load actor data into database."""
        logger.info(f"Loading actors from {actors_path}")
        
        import pandas as pd
        df_actors = pd.read_excel(actors_path)
        
        cursor = self.conn.cursor()
        
        # Prepare data
        actors_data = []
        for _, row in df_actors.iterrows():
            actors_data.append((
                row.get('Actor_domain'),
                row.get('Actor'),
                row.get('Country'),
                row.get('primary_format'),
                row.get('secondary_format'),
                row.get('Partisan'),
                row.get('Partisan_fullcategories'),
                row.get('Self-description'),
                row.get('Website'),
                row.get('Facebook Page'),
                row.get('Facebook Group'),
                row.get('Twitter'),
                row.get('Instagram'),
                row.get('Youtube'),
                row.get('Telegram'),
                row.get('Vkontakte'),
                row.get('TikTok'),
                row.get('Gab'),
                row.get('robots_txt'),
                row.get('Notes_robots_txt'),
                row.get('Notes'),
                row.get('About'),
            ))
        
        # Deduplicate actors by actor_domain (keep last occurrence)
        actors_dict = {}
        for actor_tuple in actors_data:
            actor_domain = actor_tuple[0]  # actor_domain is first field
            actors_dict[actor_domain] = actor_tuple
        
        actors_data_deduped = list(actors_dict.values())
        
        if len(actors_data_deduped) < len(actors_data):
            logger.info(f"Deduplicated {len(actors_data) - len(actors_data_deduped)} duplicate actors")
        
        # Use INSERT ... ON CONFLICT to handle duplicates
        insert_sql = """
            INSERT INTO actors (
                actor_domain, actor_name, country, primary_format, secondary_format,
                partisan, partisan_fullcategories, self_description, website,
                facebook_page, facebook_group, twitter, instagram, youtube,
                telegram, vkontakte, tiktok, gab, robots_txt, notes_robots_txt,
                notes, about
            ) VALUES %s
            ON CONFLICT (actor_domain) 
            DO UPDATE SET
                actor_name = EXCLUDED.actor_name,
                country = EXCLUDED.country,
                partisan = EXCLUDED.partisan,
                updated_at = CURRENT_TIMESTAMP
        """
        
        execute_values(cursor, insert_sql, actors_data_deduped, page_size=self.batch_size)
        self.conn.commit()
        
        logger.info(f"Loaded {len(actors_data)} actors")
        cursor.close()
    
    def prepare_article_row(self, row: dict) -> tuple:
        """Prepare a single article row for database insertion."""
        # Parse JSON fields
        external_links = row.get('external_links', '[]')
        if isinstance(external_links, str):
            try:
                external_links = json.loads(external_links)
            except:
                external_links = []
        
        categories = row.get('categories', '[]')
        if isinstance(categories, str):
            try:
                categories = json.loads(categories)
            except:
                categories = []
        
        entities_json = row.get('entities_json', '{}')
        if isinstance(entities_json, str):
            try:
                entities_json = json.loads(entities_json)
            except:
                entities_json = {}
        
        # Parse dates
        date_val = row.get('date')
        if date_val:
            try:
                if isinstance(date_val, str):
                    date_val = datetime.strptime(date_val.split()[0], '%Y-%m-%d').date()
            except:
                date_val = None
        
        scraped_at = row.get('scraped_at')
        if scraped_at:
            try:
                if isinstance(scraped_at, str):
                    scraped_at = datetime.fromisoformat(scraped_at.replace('Z', '+00:00'))
            except:
                scraped_at = None
        
        preprocessed_at = row.get('preprocessed_at')
        if preprocessed_at:
            try:
                if isinstance(preprocessed_at, str):
                    preprocessed_at = datetime.fromisoformat(preprocessed_at.replace('Z', '+00:00'))
            except:
                preprocessed_at = None
        
        nlp_processed_at = row.get('nlp_processed_at')
        if nlp_processed_at:
            try:
                if isinstance(nlp_processed_at, str):
                    nlp_processed_at = datetime.fromisoformat(nlp_processed_at.replace('Z', '+00:00'))
            except:
                nlp_processed_at = None
        
        return (
            row.get('url'),
            row.get('title'),
            row.get('description'),
            row.get('content'),
            row.get('author'),
            date_val,
            row.get('extraction_method'),
            row.get('domain'),
            row.get('country'),
            row.get('content_length'),
            scraped_at,
            row.get('Actor'),  # From actor merge
            row.get('Country'),  # From actor merge (may differ from article country)
            row.get('Partisan'),
            row.get('Partisan_fullcategories'),
            json.dumps(external_links) if external_links else None,
            row.get('word_count'),
            preprocessed_at,
            row.get('sentiment'),
            row.get('sentiment_score'),
            json.dumps(categories) if categories else None,
            json.dumps(entities_json) if entities_json else None,
            nlp_processed_at,
        )
    
    def load_articles(self, articles_path: Path, skip_existing: bool = True):
        """Load articles into database in batches."""
        logger.info(f"Loading articles from {articles_path}")
        
        # Read parquet file
        df = pl.read_parquet(articles_path)
        total_rows = len(df)
        logger.info(f"Total articles to load: {total_rows}")
        
        cursor = self.conn.cursor()
        
        # Process in batches
        inserted = 0
        updated = 0
        skipped = 0
        errors = 0
        
        for batch_start in tqdm(range(0, total_rows, self.batch_size), desc="Loading batches"):
            batch_end = min(batch_start + self.batch_size, total_rows)
            batch_df = df[batch_start:batch_end]
            
            articles_data = []
            for row in batch_df.iter_rows(named=True):
                try:
                    article_row = self.prepare_article_row(row)
                    articles_data.append(article_row)
                except Exception as e:
                    logger.warning(f"Error preparing article row: {e}")
                    errors += 1
                    continue
            
            if not articles_data:
                continue
            
            # Insert with conflict handling
            insert_sql = """
                INSERT INTO articles (
                    url, title, description, content, author, date,
                    extraction_method, domain, country, content_length, scraped_at,
                    actor, actor_country, partisan, partisan_fullcategories,
                    external_links, word_count, preprocessed_at,
                    sentiment, sentiment_score, categories, entities_json, nlp_processed_at
                ) VALUES %s
                ON CONFLICT (url, scraped_at) 
                DO UPDATE SET
                    title = EXCLUDED.title,
                    content = EXCLUDED.content,
                    sentiment = EXCLUDED.sentiment,
                    sentiment_score = EXCLUDED.sentiment_score,
                    categories = EXCLUDED.categories,
                    entities_json = EXCLUDED.entities_json,
                    updated_at = CURRENT_TIMESTAMP
            """
            
            try:
                execute_values(
                    cursor, 
                    insert_sql, 
                    articles_data, 
                    page_size=len(articles_data)
                )
                self.conn.commit()
                inserted += len(articles_data)
            except Exception as e:
                self.conn.rollback()
                logger.error(f"Error inserting batch {batch_start}-{batch_end}: {e}")
                errors += len(articles_data)
        
        cursor.close()
        
        logger.info("=" * 80)
        logger.info("Loading complete!")
        logger.info(f"Inserted/Updated: {inserted}")
        logger.info(f"Errors: {errors}")
        logger.info("=" * 80)
    
    def get_stats(self):
        """Get database statistics."""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM articles")
        article_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM actors")
        actor_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT country, COUNT(*) 
            FROM articles 
            WHERE country IS NOT NULL 
            GROUP BY country 
            ORDER BY COUNT(*) DESC
        """)
        country_stats = cursor.fetchall()
        
        cursor.execute("""
            SELECT partisan, COUNT(*) 
            FROM articles 
            WHERE partisan IS NOT NULL 
            GROUP BY partisan 
            ORDER BY COUNT(*) DESC
        """)
        partisan_stats = cursor.fetchall()
        
        cursor.close()
        
        logger.info("=" * 80)
        logger.info("Database Statistics")
        logger.info("=" * 80)
        logger.info(f"Total articles: {article_count:,}")
        logger.info(f"Total actors: {actor_count}")
        logger.info("\nArticles by country:")
        for country, count in country_stats:
            logger.info(f"  {country}: {count:,}")
        logger.info("\nArticles by partisan:")
        for partisan, count in partisan_stats:
            logger.info(f"  {partisan}: {count:,}")
        logger.info("=" * 80)


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Load NAMO data into PostgreSQL')
    parser.add_argument('--articles', type=str, required=True, help='Path to preprocessed articles parquet file')
    parser.add_argument('--actors', type=str, help='Path to actor Excel file (optional if already loaded)')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for insertion')
    parser.add_argument('--host', type=str, help='Database host')
    parser.add_argument('--port', type=str, help='Database port')
    parser.add_argument('--user', type=str, help='Database user')
    parser.add_argument('--password', type=str, help='Database password')
    parser.add_argument('--database', type=str, help='Database name')
    parser.add_argument('--stats', action='store_true', help='Show database statistics after loading')
    
    args = parser.parse_args()
    
    # Update config
    config = DB_CONFIG.copy()
    if args.host:
        config['host'] = args.host
    if args.port:
        config['port'] = args.port
    if args.user:
        config['user'] = args.user
    if args.password:
        config['password'] = args.password
    if args.database:
        config['database'] = args.database
    
    loader = DatabaseLoader(config, batch_size=args.batch_size)
    
    try:
        loader.connect()
        
        # Load actors if provided
        if args.actors:
            actors_path = Path(args.actors)
            if actors_path.exists():
                loader.load_actors(actors_path)
            else:
                logger.warning(f"Actor file not found: {actors_path}")
        
        # Load articles
        articles_path = Path(args.articles)
        if not articles_path.exists():
            logger.error(f"Articles file not found: {articles_path}")
            return
        
        loader.load_articles(articles_path)
        
        if args.stats:
            loader.get_stats()
        
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        raise
    finally:
        loader.close()


if __name__ == "__main__":
    main()

