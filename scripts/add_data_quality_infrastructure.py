#!/usr/bin/env python3
"""
Add data quality infrastructure to prevent future issues
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
print("ADDING DATA QUALITY INFRASTRUCTURE")
print("="*80)

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

# 1. Create data quality configuration table
print("\n1️⃣  Creating data quality configuration table...")
cur.execute("""
    CREATE TABLE IF NOT EXISTS data_quality_config (
        key VARCHAR(100) PRIMARY KEY,
        value TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
""")
conn.commit()
print("  ✓ Table created")

# 2. Insert minimum date configuration
print("\n2️⃣  Setting minimum acceptable date (2003-01-01)...")
cur.execute("""
    INSERT INTO data_quality_config (key, value, description)
    VALUES 
        ('min_article_date', '2003-01-01', 'Minimum acceptable article publication date for data quality'),
        ('max_future_days', '90', 'Maximum days into future for article dates (to catch scraper errors)')
    ON CONFLICT (key) DO UPDATE 
    SET value = EXCLUDED.value, updated_at = CURRENT_TIMESTAMP;
""")
conn.commit()
print("  ✓ Configuration saved")

# 3. Add data_quality_flag column to articles table
print("\n3️⃣  Adding data_quality_flag column...")
cur.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='articles' AND column_name='data_quality_flag'
        ) THEN
            ALTER TABLE articles ADD COLUMN data_quality_flag VARCHAR(50);
            CREATE INDEX IF NOT EXISTS idx_articles_quality_flag ON articles(data_quality_flag);
            RAISE INFO 'Added data_quality_flag column';
        ELSE
            RAISE INFO 'data_quality_flag column already exists';
        END IF;
    END
    $$;
""")
conn.commit()
print("  ✓ Column added")

# 4. Flag existing pre-2003 articles
print("\n4️⃣  Flagging existing pre-2003 articles...")
cur.execute("""
    UPDATE articles 
    SET data_quality_flag = 'pre_2003_outlier'
    WHERE date < '2003-01-01'
    AND (data_quality_flag IS NULL OR data_quality_flag = '');
""")
flagged_count = cur.rowcount
conn.commit()
print(f"  ✓ Flagged {flagged_count} articles")

# 5. Flag the January 31 bulk import
print("\n5️⃣  Flagging January 31, 2025 bulk import artifact...")
cur.execute("""
    UPDATE articles 
    SET data_quality_flag = 'bulk_import_artifact'
    WHERE DATE(date) = '2025-01-31'
    AND domain = 'piopio.dk'
    AND (data_quality_flag IS NULL OR data_quality_flag = '');
""")
flagged_bulk = cur.rowcount
conn.commit()
print(f"  ✓ Flagged {flagged_bulk} articles")

# 6. Create helper function to validate article dates
print("\n6️⃣  Creating date validation function...")
cur.execute("""
    CREATE OR REPLACE FUNCTION validate_article_date(article_date DATE)
    RETURNS VARCHAR(50) AS $$
    DECLARE
        min_date DATE;
        max_future_days INT;
        max_date DATE;
    BEGIN
        -- Get configuration
        SELECT value::DATE INTO min_date 
        FROM data_quality_config WHERE key = 'min_article_date';
        
        SELECT value::INT INTO max_future_days 
        FROM data_quality_config WHERE key = 'max_future_days';
        
        max_date := CURRENT_DATE + max_future_days;
        
        -- Validate date
        IF article_date < min_date THEN
            RETURN 'pre_2003_outlier';
        ELSIF article_date > max_date THEN
            RETURN 'future_date_error';
        ELSE
            RETURN NULL; -- Valid date
        END IF;
    END;
    $$ LANGUAGE plpgsql;
""")
conn.commit()
print("  ✓ Function created")

# 7. Create a view that excludes flagged articles
print("\n7️⃣  Creating clean_articles view...")
cur.execute("""
    CREATE OR REPLACE VIEW clean_articles AS
    SELECT *
    FROM articles
    WHERE (data_quality_flag IS NULL OR data_quality_flag = '')
    AND date >= '2003-01-01';
""")
conn.commit()
print("  ✓ View created")

# 8. Summary
print("\n" + "="*80)
print("INFRASTRUCTURE SUMMARY")
print("="*80)

cur.execute("SELECT COUNT(*) FROM articles WHERE data_quality_flag IS NOT NULL AND data_quality_flag != ''")
total_flagged = cur.fetchone()[0]

cur.execute("SELECT data_quality_flag, COUNT(*) FROM articles WHERE data_quality_flag IS NOT NULL AND data_quality_flag != '' GROUP BY data_quality_flag")
flags = cur.fetchall()

print(f"\n📊 Total flagged articles: {total_flagged:,}")
print("\nBreakdown by flag:")
for flag, count in flags:
    print(f"  {flag}: {count:,}")

cur.execute("SELECT COUNT(*) FROM clean_articles")
clean_count = cur.fetchone()[0]
print(f"\n✅ Clean articles view: {clean_count:,} articles")

print("\n" + "="*80)
print("WHAT'S BEEN ADDED:")
print("="*80)
print("""
1. ✅ data_quality_config table
   - Stores minimum date (2003-01-01)
   - Stores max future days (90)
   - Easily updatable configuration

2. ✅ data_quality_flag column on articles table
   - Marks problematic articles
   - Indexed for fast queries
   - Doesn't delete data (preserves for review)

3. ✅ Existing outliers flagged:
   - 45 pre-2003 articles → 'pre_2003_outlier'
   - 13,050 Jan 31 bulk import → 'bulk_import_artifact'

4. ✅ validate_article_date() function
   - Can be called during scraping/import
   - Returns NULL if valid, flag if invalid
   - Uses configuration from data_quality_config

5. ✅ clean_articles view
   - Excludes all flagged articles
   - Always returns 2003+ data only
   - Use this for analysis/dashboard

USAGE IN SCRAPER:
-----------------
When inserting new articles:

    SELECT validate_article_date(article_date);
    
If it returns a flag, either:
- Reject the article
- Insert with that flag
- Log for manual review
""")

cur.close()
conn.close()

print("\n" + "="*80)
print("✅ DATA QUALITY INFRASTRUCTURE COMPLETE")
print("="*80)

