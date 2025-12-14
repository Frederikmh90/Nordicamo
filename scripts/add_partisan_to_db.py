#!/usr/bin/env python3
"""
Add partisan leaning information to the database
Based on NAMO_actor_251118.xlsx
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'user': 'namo_user',
    'password': 'namo_password',
    'database': 'namo_db'
}

print("="*80)
print("ADDING PARTISAN LEANING TO DATABASE")
print("="*80)

# Read partisan mapping from Excel
print("\n📂 Loading partisan data from Excel...")
df = pd.read_excel("data/NAMO_actor_251118.xlsx")
print(f"  Total outlets in Excel: {len(df)}")

# Create mapping (Actor_domain -> Partisan)
partisan_mapping = {}
for _, row in df.iterrows():
    domain = row['Actor_domain']
    partisan = row['Partisan']
    if pd.notna(domain) and pd.notna(partisan):
        partisan_mapping[domain] = partisan

print(f"  Valid mappings: {len(partisan_mapping)}")

print("\n📊 Partisan Distribution:")
partisan_counts = {}
for partisan in partisan_mapping.values():
    partisan_counts[partisan] = partisan_counts.get(partisan, 0) + 1
for partisan, count in sorted(partisan_counts.items()):
    print(f"  {partisan}: {count}")

# Connect to database
print("\n🔌 Connecting to database...")
try:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    print("  ✓ Connected")
except Exception as e:
    print(f"  ❌ Connection failed: {e}")
    exit(1)

# Add partisan column if it doesn't exist
print("\n📝 Ensuring partisan column exists...")
cur.execute("""
    ALTER TABLE articles 
    ADD COLUMN IF NOT EXISTS partisan VARCHAR(20);
""")
conn.commit()
print("  ✓ Column ensured")

# Check current state
print("\n📊 Current database state...")
cur.execute("SELECT COUNT(*) FROM articles")
total_articles = cur.fetchone()[0]
print(f"  Total articles: {total_articles:,}")

cur.execute("SELECT COUNT(*) FROM articles WHERE partisan IS NOT NULL")
articles_with_partisan = cur.fetchone()[0]
print(f"  Articles with partisan: {articles_with_partisan:,}")

# Get unique domains in database
print("\n🔍 Checking domains in database...")
cur.execute("SELECT DISTINCT domain FROM articles WHERE domain IS NOT NULL")
db_domains = [row[0] for row in cur.fetchall()]
print(f"  Unique domains in DB: {len(db_domains)}")

# Match domains
matched_domains = []
unmatched_domains = []

for db_domain in db_domains:
    if db_domain in partisan_mapping:
        matched_domains.append((db_domain, partisan_mapping[db_domain]))
    else:
        # Try with/without www prefix
        domain_variants = [
            db_domain.replace('www.', ''),
            'www.' + db_domain,
            db_domain.replace('www.', '').replace('http://', '').replace('https://', '')
        ]
        
        matched = False
        for variant in domain_variants:
            if variant in partisan_mapping:
                matched_domains.append((db_domain, partisan_mapping[variant]))
                matched = True
                break
        
        if not matched:
            unmatched_domains.append(db_domain)

print(f"\n✅ Matched domains: {len(matched_domains)}")
print(f"❌ Unmatched domains: {len(unmatched_domains)}")

if unmatched_domains[:10]:
    print("\n  First 10 unmatched domains:")
    for domain in unmatched_domains[:10]:
        print(f"    - {domain}")

# Update database with partisan information
print(f"\n🔄 Updating {len(matched_domains)} domains with partisan leaning...")
update_query = """
    UPDATE articles 
    SET partisan = %s 
    WHERE domain = %s
"""

update_data = [(partisan, domain) for domain, partisan in matched_domains]

execute_batch(cur, update_query, update_data, page_size=100)
conn.commit()
print("  ✓ Updated")

# Final statistics
print("\n📊 Final database state...")
cur.execute("SELECT COUNT(*) FROM articles WHERE partisan IS NOT NULL")
final_with_partisan = cur.fetchone()[0]
print(f"  Articles with partisan: {final_with_partisan:,} ({100*final_with_partisan/total_articles:.1f}%)")

print("\n  Partisan distribution in database:")
cur.execute("""
    SELECT partisan, COUNT(*) 
    FROM articles 
    WHERE partisan IS NOT NULL 
    GROUP BY partisan 
    ORDER BY COUNT(*) DESC
""")
for row in cur.fetchall():
    partisan, count = row
    pct = 100 * count / final_with_partisan if final_with_partisan > 0 else 0
    print(f"    {partisan}: {count:,} ({pct:.1f}%)")

# Close connection
cur.close()
conn.close()

print("\n" + "="*80)
print("✅ PARTISAN LEANING ADDED TO DATABASE")
print("="*80)
print(f"\nUpdated {final_with_partisan:,} articles with partisan information")
print(f"Coverage: {100*final_with_partisan/total_articles:.1f}% of all articles")
print("="*80)

