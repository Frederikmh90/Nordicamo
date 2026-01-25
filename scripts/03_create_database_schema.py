"""
NAMO PostgreSQL Database Schema Creation
=========================================
Creates the database schema for storing articles and actors with all NLP outputs.
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from pathlib import Path
import logging
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration (can be overridden by environment variables)
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'user': os.getenv('DB_USER', 'namo_user'),
    'password': os.getenv('DB_PASSWORD', '<DB_PASSWORD>'),
    'database': os.getenv('DB_NAME', 'namo_db')
}


def create_database(config: dict):
    """Create the database if it doesn't exist."""
    # Connect to postgres database to create our database
    admin_config = config.copy()
    admin_config['database'] = 'postgres'
    
    try:
        conn = psycopg2.connect(**admin_config)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (config['database'],)
        )
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f"CREATE DATABASE {config['database']}")
            logger.info(f"Database '{config['database']}' created successfully")
        else:
            logger.info(f"Database '{config['database']}' already exists")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.warning(f"Could not create database (may already exist or PostgreSQL not running): {e}")
        logger.info("Proceeding with schema creation assuming database exists...")


def create_schema(config: dict):
    """Create tables and indexes."""
    conn = psycopg2.connect(**config)
    cursor = conn.cursor()
    
    try:
        # Create actors table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS actors (
                id SERIAL PRIMARY KEY,
                actor_domain VARCHAR(255) UNIQUE NOT NULL,
                actor_name VARCHAR(255),
                country VARCHAR(50),
                primary_format VARCHAR(100),
                secondary_format VARCHAR(100),
                partisan VARCHAR(50),
                partisan_fullcategories TEXT,
                self_description TEXT,
                website VARCHAR(255),
                facebook_page VARCHAR(255),
                facebook_group VARCHAR(255),
                twitter VARCHAR(255),
                instagram VARCHAR(255),
                youtube VARCHAR(255),
                telegram VARCHAR(255),
                vkontakte VARCHAR(255),
                tiktok VARCHAR(255),
                gab VARCHAR(255),
                robots_txt TEXT,
                notes_robots_txt TEXT,
                notes TEXT,
                about TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create articles table with all columns including NLP outputs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id SERIAL PRIMARY KEY,
                url TEXT NOT NULL,
                title TEXT,
                description TEXT,
                content TEXT,
                author VARCHAR(255),
                date DATE,
                extraction_method VARCHAR(100),
                domain VARCHAR(255),
                country VARCHAR(50),
                content_length INTEGER,
                scraped_at TIMESTAMP,
                
                -- Actor/Partisan data (from merge)
                actor VARCHAR(255),
                actor_country VARCHAR(50),
                partisan VARCHAR(50),
                partisan_fullcategories TEXT,
                
                -- Basic features
                external_links JSONB,
                word_count INTEGER,
                preprocessed_at TIMESTAMP,
                
                -- NLP outputs
                sentiment VARCHAR(20),
                sentiment_score FLOAT,
                categories JSONB,
                entities_json JSONB,
                nlp_processed_at TIMESTAMP,
                
                -- Topic modeling outputs
                topic_id INTEGER,
                topic_probability FLOAT,
                
                -- Metadata
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Constraints
                UNIQUE(url, scraped_at)
            );
        """)
        
        # Create indexes for efficient querying
        logger.info("Creating indexes...")
        
        # Articles indexes
        indexes = [
            ("CREATE INDEX IF NOT EXISTS idx_articles_domain ON articles(domain);"),
            ("CREATE INDEX IF NOT EXISTS idx_articles_country ON articles(country);"),
            ("CREATE INDEX IF NOT EXISTS idx_articles_date ON articles(date);"),
            ("CREATE INDEX IF NOT EXISTS idx_articles_partisan ON articles(partisan);"),
            ("CREATE INDEX IF NOT EXISTS idx_articles_sentiment ON articles(sentiment);"),
            ("CREATE INDEX IF NOT EXISTS idx_articles_scraped_at ON articles(scraped_at);"),
            ("CREATE INDEX IF NOT EXISTS idx_articles_topic_id ON articles(topic_id);"),
            ("CREATE INDEX IF NOT EXISTS idx_articles_domain_country ON articles(domain, country);"),
            ("CREATE INDEX IF NOT EXISTS idx_articles_date_country ON articles(date, country);"),
            ("CREATE INDEX IF NOT EXISTS idx_articles_categories ON articles USING GIN(categories);"),
            ("CREATE INDEX IF NOT EXISTS idx_articles_entities ON articles USING GIN(entities_json);"),
            ("CREATE INDEX IF NOT EXISTS idx_articles_external_links ON articles USING GIN(external_links);"),
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        # Actors indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_actors_domain ON actors(actor_domain);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_actors_country ON actors(country);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_actors_partisan ON actors(partisan);")
        
        # Create function to update updated_at timestamp
        cursor.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        """)
        
        # Create triggers
        cursor.execute("""
            DROP TRIGGER IF EXISTS update_articles_updated_at ON articles;
            CREATE TRIGGER update_articles_updated_at
                BEFORE UPDATE ON articles
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
        """)
        
        cursor.execute("""
            DROP TRIGGER IF EXISTS update_actors_updated_at ON actors;
            CREATE TRIGGER update_actors_updated_at
                BEFORE UPDATE ON actors
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
        """)
        
        conn.commit()
        logger.info("Schema created successfully!")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating schema: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Create NAMO PostgreSQL database schema')
    parser.add_argument('--create-db', action='store_true', help='Create database if it does not exist')
    parser.add_argument('--host', type=str, help='Database host')
    parser.add_argument('--port', type=str, help='Database port')
    parser.add_argument('--user', type=str, help='Database user')
    parser.add_argument('--password', type=str, help='Database password')
    parser.add_argument('--database', type=str, help='Database name')
    
    args = parser.parse_args()
    
    # Update config with command line arguments
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
    
    logger.info("=" * 80)
    logger.info("Creating NAMO Database Schema")
    logger.info("=" * 80)
    logger.info(f"Host: {config['host']}")
    logger.info(f"Database: {config['database']}")
    logger.info(f"User: {config['user']}")
    
    try:
        if args.create_db:
            create_database(config)
        
        create_schema(config)
        
        logger.info("=" * 80)
        logger.info("Database setup complete!")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Failed to create schema: {e}")
        raise


if __name__ == "__main__":
    main()

