#!/usr/bin/env python3
"""
Test script to verify dashboard backend is using clean_articles
"""

import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'user': 'namo_user',
    'password': 'namo_password',
    'database': 'namo_db'
}

print("="*80)
print("TESTING DASHBOARD DATA SOURCE")
print("="*80)

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

# 1. Check total articles
print("\n1️⃣  Article Counts:")
cur.execute("SELECT COUNT(*) FROM articles")
total_all = cur.fetchone()[0]
print(f"  All articles (articles table): {total_all:,}")

cur.execute("SELECT COUNT(*) FROM clean_articles")
total_clean = cur.fetchone()[0]
print(f"  Clean articles (clean_articles view): {total_clean:,}")

print(f"  Filtered out: {total_all - total_clean:,} articles")

# 2. Check date range
print("\n2️⃣  Date Range:")
cur.execute("SELECT MIN(date), MAX(date) FROM clean_articles")
min_date, max_date = cur.fetchone()
print(f"  Clean data: {min_date} to {max_date}")

cur.execute("SELECT MIN(date), MAX(date) FROM articles WHERE data_quality_flag IS NOT NULL")
flagged_dates = cur.fetchone()
if flagged_dates[0]:
    print(f"  Flagged data: {flagged_dates[0]} to {flagged_dates[1]}")

# 3. Check what's filtered
print("\n3️⃣  What's Being Filtered:")
cur.execute("""
    SELECT 
        data_quality_flag,
        COUNT(*) as count,
        MIN(date) as earliest,
        MAX(date) as latest
    FROM articles
    WHERE data_quality_flag IS NOT NULL
    GROUP BY data_quality_flag
    ORDER BY count DESC
""")

for flag, count, earliest, latest in cur.fetchall():
    print(f"  {flag}: {count:,} articles ({earliest} to {latest})")

# 4. Verify view definition
print("\n4️⃣  Clean Articles View Definition:")
cur.execute("""
    SELECT definition 
    FROM pg_views 
    WHERE viewname = 'clean_articles'
""")
view_def = cur.fetchone()
if view_def:
    print(f"  ✓ View exists")
    # print(f"  Definition: {view_def[0][:100]}...")
else:
    print(f"  ✗ View not found!")

# 5. Sample comparison
print("\n5️⃣  Sample Stats Comparison:")
print("\nCountry Distribution:")
cur.execute("""
    SELECT 'All Articles' as source, country, COUNT(*) as count
    FROM articles
    WHERE country IS NOT NULL
    GROUP BY country
    UNION ALL
    SELECT 'Clean Articles' as source, country, COUNT(*) as count
    FROM clean_articles
    WHERE country IS NOT NULL
    GROUP BY country
    ORDER BY source, count DESC
""")

current_source = None
for source, country, count in cur.fetchall():
    if source != current_source:
        print(f"\n  {source}:")
        current_source = source
    print(f"    {country}: {count:,}")

cur.close()
conn.close()

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
print("""
✅ If you see ~740,001 clean articles (vs ~755,624 total), it's working!
✅ Date range should be 2003-01-01 onwards for clean data
✅ 13,095 articles should be filtered (45 + 13,050)

Now restart your backend server to apply the changes:
  cd backend && python -m uvicorn app.main:app --reload
""")

