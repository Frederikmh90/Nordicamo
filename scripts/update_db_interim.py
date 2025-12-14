#!/usr/bin/env python3
"""
Update database with interim NLP-enriched dataset
For Nordic Media Observatory presentation
"""

import polars as pl
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime
import json
from tqdm import tqdm

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'user': 'namo_user',
    'password': 'namo_password',
    'database': 'namo_db'
}

print("="*80)
print("UPDATING DATABASE WITH INTERIM NLP-ENRICHED DATASET")
print("="*80)

# Load interim dataset
print("\n📂 Loading interim dataset...")
df = pl.read_parquet("data/NAMO_interim_enriched.parquet")
print(f"  Total articles: {len(df):,}")

# Connect to database
print("\n🔌 Connecting to database...")
try:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    print("  ✓ Connected")
except Exception as e:
    print(f"  ❌ Connection failed: {e}")
    print("\n  Trying to start PostgreSQL...")
    import subprocess
    subprocess.run(["brew", "services", "start", "postgresql@14"], check=False)
    print("  Waiting 5 seconds for PostgreSQL to start...")
    import time
    time.sleep(5)
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        print("  ✓ Connected after restart")
    except Exception as e2:
        print(f"  ❌ Still failed: {e2}")
        print("\n📝 Please start PostgreSQL manually and run again:")
        print("     brew services start postgresql@14")
        exit(1)

# Check current database state
print("\n📊 Current database state...")
cur.execute("SELECT COUNT(*) FROM articles")
current_count = cur.fetchone()[0]
print(f"  Current articles in DB: {current_count:,}")

cur.execute("""
    SELECT COUNT(*) FROM articles 
    WHERE sentiment IS NOT NULL AND categories IS NOT NULL
""")
enriched_count = cur.fetchone()[0]
print(f"  Articles with NLP: {enriched_count:,}")

# Update strategy
print("\n🔄 Update strategy:")
print("  1. Add new NLP columns if needed")
print("  2. Update existing articles with NLP data")
print("  3. Insert new articles")

# Ensure NLP columns exist
print("\n📝 Ensuring NLP columns exist...")
nlp_columns = """
    ALTER TABLE articles ADD COLUMN IF NOT EXISTS sentiment VARCHAR(20);
    ALTER TABLE articles ADD COLUMN IF NOT EXISTS sentiment_score FLOAT;
    ALTER TABLE articles ADD COLUMN IF NOT EXISTS categories JSONB;
    ALTER TABLE articles ADD COLUMN IF NOT EXISTS entities JSONB;
    ALTER TABLE articles ADD COLUMN IF NOT EXISTS nlp_processed_at TIMESTAMP;
"""
cur.execute(nlp_columns)
conn.commit()
print("  ✓ Columns ensured")

# Prepare data for update
print("\n📦 Preparing data for database...")
articles = df.to_dicts()

# Split into updates vs inserts
print("  Checking which articles already exist...")
urls = [a['url'] for a in articles]
cur.execute("""
    SELECT url FROM articles WHERE url = ANY(%s)
""", (urls,))
existing_urls = set(row[0] for row in cur.fetchall())
print(f"  Existing in DB: {len(existing_urls):,}")
print(f"  New articles: {len(urls) - len(existing_urls):,}")

# Update existing articles
updates = [a for a in articles if a['url'] in existing_urls]
inserts = [a for a in articles if a['url'] not in existing_urls]

if updates:
    print(f"\n🔄 Updating {len(updates):,} existing articles with NLP data...")
    update_query = """
        UPDATE articles SET
            sentiment = %s,
            sentiment_score = %s,
            categories = %s,
            entities = %s,
            nlp_processed_at = %s
        WHERE url = %s
    """
    update_data = [
        (
            a.get('sentiment'),
            a.get('sentiment_score'),
            json.dumps(a.get('categories', [])) if a.get('categories') else None,
            json.dumps(a.get('entities', {})) if a.get('entities') else None,
            datetime.fromisoformat(a['nlp_processed_at']) if a.get('nlp_processed_at') else None,
            a['url']
        )
        for a in updates
    ]
    
    for i in tqdm(range(0, len(update_data), 1000), desc="Updating"):
        batch = update_data[i:i+1000]
        execute_batch(cur, update_query, batch, page_size=1000)
        conn.commit()
    
    print(f"  ✓ Updated {len(updates):,} articles")

if inserts:
    print(f"\n➕ Inserting {len(inserts):,} new articles...")
    insert_query = """
        INSERT INTO articles (
            url, title, description, content, author, date,
            extraction_method, domain, country, content_length,
            scraped_at, sentiment, sentiment_score, categories,
            entities, nlp_processed_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (url) DO NOTHING
    """
    
    insert_data = [
        (
            a['url'],
            a.get('title'),
            a.get('description'),
            a.get('content'),
            a.get('author'),
            datetime.fromisoformat(a['date']) if a.get('date') else None,
            a.get('extraction_method'),
            a.get('domain'),
            a.get('country'),
            a.get('content_length'),
            datetime.fromisoformat(a['scraped_at']) if a.get('scraped_at') else None,
            a.get('sentiment'),
            a.get('sentiment_score'),
            json.dumps(a.get('categories', [])) if a.get('categories') else None,
            json.dumps(a.get('entities', {})) if a.get('entities') else None,
            datetime.fromisoformat(a['nlp_processed_at']) if a.get('nlp_processed_at') else None
        )
        for a in inserts
    ]
    
    for i in tqdm(range(0, len(insert_data), 1000), desc="Inserting"):
        batch = insert_data[i:i+1000]
        execute_batch(cur, insert_query, batch, page_size=1000)
        conn.commit()
    
    print(f"  ✓ Inserted {len(inserts):,} articles")

# Final statistics
print("\n📊 Final database state...")
cur.execute("SELECT COUNT(*) FROM articles")
final_count = cur.fetchone()[0]
print(f"  Total articles: {final_count:,}")

cur.execute("""
    SELECT COUNT(*) FROM articles 
    WHERE sentiment IS NOT NULL AND categories IS NOT NULL
""")
final_enriched = cur.fetchone()[0]
print(f"  Articles with NLP: {final_enriched:,} ({100*final_enriched/final_count:.1f}%)")

# Close connection
cur.close()
conn.close()

print("\n" + "="*80)
print("✅ DATABASE UPDATE COMPLETE!")
print("="*80)
print(f"\nDatabase is ready for Nordic Media Observatory presentation")
print(f"Added: {final_count - current_count:,} new articles")
print(f"NLP enriched: {final_enriched - enriched_count:,} additional articles")
print("="*80)

