#!/usr/bin/env python3
"""
Fix domain extraction for articles with NULL domain
Extract domain from URL field
"""

import psycopg2
from urllib.parse import urlparse
from tqdm import tqdm

DB_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'user': 'namo_user',
    'password': 'namo_password',
    'database': 'namo_db'
}

print("="*80)
print("FIXING DOMAIN EXTRACTION")
print("="*80)

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

# Count articles with NULL domain
cur.execute("SELECT COUNT(*) FROM articles WHERE domain IS NULL")
null_domains = cur.fetchone()[0]
print(f"\n📊 Articles with NULL domain: {null_domains:,}")

# Get all articles with NULL domain but valid URL
print("\n🔍 Extracting domains from URLs...")
cur.execute("""
    SELECT url 
    FROM articles 
    WHERE domain IS NULL 
    AND url IS NOT NULL
""")

urls_to_fix = cur.fetchall()
print(f"  Found {len(urls_to_fix):,} URLs to process")

# Extract domains
domain_updates = []
for (url,) in tqdm(urls_to_fix, desc="Processing URLs"):
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # Clean domain
        domain = domain.lower().strip()
        if domain:
            domain_updates.append((domain, url))
    except:
        continue

print(f"\n✅ Extracted {len(domain_updates):,} domains")

# Update database
print("\n🔄 Updating database...")
update_query = "UPDATE articles SET domain = %s WHERE url = %s"

batch_size = 1000
for i in tqdm(range(0, len(domain_updates), batch_size), desc="Updating"):
    batch = domain_updates[i:i+batch_size]
    cur.executemany(update_query, batch)
    conn.commit()

print(f"  ✓ Updated {len(domain_updates):,} articles")

# Verify
cur.execute("SELECT COUNT(*) FROM articles WHERE domain IS NULL")
remaining_null = cur.fetchone()[0]
print(f"\n📊 Articles with NULL domain after fix: {remaining_null:,}")
print(f"  Fixed: {null_domains - remaining_null:,} articles")

# Show top domains that were fixed
print("\n🏆 Top domains that were fixed:")
cur.execute("""
    SELECT domain, COUNT(*) as count
    FROM articles
    WHERE domain IN (
        SELECT DISTINCT domain FROM (VALUES %s) AS v(d)
    )
    GROUP BY domain
    ORDER BY count DESC
    LIMIT 10
""", (tuple([d for d, _ in set([(d, '') for d, u in domain_updates])]),))

for domain, count in cur.fetchall():
    print(f"  {domain}: {count:,} articles")

cur.close()
conn.close()

print("\n" + "="*80)
print("✅ DOMAIN EXTRACTION COMPLETE")
print("="*80)

