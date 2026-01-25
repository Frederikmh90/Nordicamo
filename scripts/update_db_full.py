#!/usr/bin/env python3
"""
Update database with merged Phase 1 + Phase 2 dataset
755,624 articles with full NLP enrichment
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
    'password': '<DB_PASSWORD>',
    'database': 'namo_db'
}

print("="*80)
print("UPDATING DATABASE WITH MERGED DATASET (755K+ ARTICLES)")
print("="*80)

# Load merged dataset
print("\n📂 Loading merged dataset...")
df = pl.read_parquet("data/NAMO_merged_enriched.parquet")
print(f"  Total articles: {len(df):,}")
print(f"  All with NLP enrichment: 100%")

# Connect to database
print("\n🔌 Connecting to database...")
try:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    print("  ✓ Connected")
except Exception as e:
    print(f"  ❌ Connection failed: {e}")
    print("\n  Please ensure PostgreSQL is running:")
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

# Prepare data for database
print("\n📦 Preparing data for database...")
articles = df.to_dicts()

# Check which articles already exist
print("  Checking existing articles...")
urls = [a['url'] for a in articles]

# Process in chunks to avoid memory issues
chunk_size = 50000
existing_urls = set()

for i in range(0, len(urls), chunk_size):
    chunk = urls[i:i+chunk_size]
    cur.execute("SELECT url FROM articles WHERE url = ANY(%s)", (chunk,))
    existing_urls.update(row[0] for row in cur.fetchall())
    if (i + chunk_size) < len(urls):
        print(f"    Checked {i+chunk_size:,} / {len(urls):,}...")

print(f"  Existing in DB: {len(existing_urls):,}")
print(f"  New articles: {len(urls) - len(existing_urls):,}")

# Split into updates vs inserts
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
    
    batch_size = 1000
    for i in tqdm(range(0, len(update_data), batch_size), desc="Updating"):
        batch = update_data[i:i+batch_size]
        execute_batch(cur, update_query, batch, page_size=batch_size)
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
    
    batch_size = 1000
    for i in tqdm(range(0, len(insert_data), batch_size), desc="Inserting"):
        batch = insert_data[i:i+batch_size]
        execute_batch(cur, insert_query, batch, page_size=batch_size)
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

# Sentiment breakdown
print("\n  Sentiment Distribution:")
cur.execute("""
    SELECT sentiment, COUNT(*) 
    FROM articles 
    WHERE sentiment IS NOT NULL 
    GROUP BY sentiment 
    ORDER BY COUNT(*) DESC
""")
for row in cur.fetchall():
    pct = 100 * row[1] / final_enriched if final_enriched > 0 else 0
    print(f"    {row[0]}: {row[1]:,} ({pct:.1f}%)")

# Close connection
cur.close()
conn.close()

print("\n" + "="*80)
print("✅ DATABASE UPDATE COMPLETE!")
print("="*80)
print(f"\nDatabase ready for presentation with MAXIMUM DATA:")
print(f"  Total articles: {final_count:,}")
print(f"  NLP enriched: {final_enriched:,} ({100*final_enriched/final_count:.1f}%)")
print(f"  Added: {final_count - current_count:,} new articles")
print(f"  NLP added: {final_enriched - enriched_count:,} enriched articles")
print("="*80)

