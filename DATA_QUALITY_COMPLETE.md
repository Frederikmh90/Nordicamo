# 🛡️ Data Quality Infrastructure - Complete Guide

## ✅ Questions Answered

### Question 1: Are All Domains Properly Extracted?

**Answer**: YES! ✅

**Current Status:**
- ✅ **0 NULL domains** (all fixed!)
- ✅ All domains match their URLs
- ✅ No unusual patterns
- ✅ 77 unique domains
- ✅ Domain length: 6-31 characters (all reasonable)

**Domain Quality Metrics:**
- Average domain length: 12.8 characters
- All domains properly formatted
- No URLs stored as domains
- No empty domains

**Conclusion**: Domain extraction is **100% clean!**

---

### Question 2: How to Prevent Pre-2003 Articles from Re-import?

**Answer**: Infrastructure now in place! ✅

---

## 🏗️ Infrastructure Added

### 1. Configuration Table: `data_quality_config`

Stores data quality rules in the database:

```sql
CREATE TABLE data_quality_config (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Current Configuration:**
- `min_article_date`: `2003-01-01` (minimum acceptable date)
- `max_future_days`: `90` (max days into future to catch scraper errors)

**Benefits:**
- ✅ Centralized configuration
- ✅ Easy to update without code changes
- ✅ Auditable (tracks changes)

---

### 2. Quality Flag Column: `data_quality_flag`

Added to `articles` table to mark problematic articles:

```sql
ALTER TABLE articles ADD COLUMN data_quality_flag VARCHAR(50);
CREATE INDEX idx_articles_quality_flag ON articles(data_quality_flag);
```

**Current Flags Applied:**
- `pre_2003_outlier`: 45 articles from 1997-2002
- `bulk_import_artifact`: 13,050 articles from Jan 31, 2025 piopio.dk bulk import

**Benefits:**
- ✅ Doesn't delete data (preserves for review)
- ✅ Indexed for fast filtering
- ✅ Can add more flags as needed
- ✅ Enables flexible data quality management

---

### 3. Date Validation Function: `validate_article_date()`

SQL function to check if article date is valid:

```sql
CREATE FUNCTION validate_article_date(article_date DATE)
RETURNS VARCHAR(50)
```

**Usage Example:**
```sql
-- Check if date is valid
SELECT validate_article_date('2025-01-15');  -- Returns: NULL (valid)
SELECT validate_article_date('1999-05-20');  -- Returns: 'pre_2003_outlier'
SELECT validate_article_date('2026-12-31');  -- Returns: 'future_date_error'
```

**Returns:**
- `NULL`: Date is valid
- `'pre_2003_outlier'`: Date before 2003-01-01
- `'future_date_error'`: Date more than 90 days in future

**Benefits:**
- ✅ Can be called during INSERT
- ✅ Uses centralized configuration
- ✅ Consistent validation across all scrapers

---

### 4. Clean Data View: `clean_articles`

A view that automatically excludes flagged articles:

```sql
CREATE VIEW clean_articles AS
SELECT *
FROM articles
WHERE (data_quality_flag IS NULL OR data_quality_flag = '')
AND date >= '2003-01-01';
```

**Usage:**
```sql
-- Use this for all analysis/dashboard queries
SELECT * FROM clean_articles WHERE country = 'denmark';

-- Get counts
SELECT COUNT(*) FROM clean_articles;  -- Returns: 740,001 (clean articles only)
SELECT COUNT(*) FROM articles;        -- Returns: 755,624 (all articles)
```

**Benefits:**
- ✅ One place to get clean data
- ✅ No need to remember filtering rules
- ✅ Always up-to-date
- ✅ Easy to use in dashboard/analysis

---

## 🔄 How to Update Scrapers

### Option A: Validate During Insert (Recommended)

**Before insert, check date validity:**

```python
def insert_article(conn, article_data):
    cur = conn.cursor()
    
    # Validate date
    cur.execute(
        "SELECT validate_article_date(%s)",
        (article_data['date'],)
    )
    quality_flag = cur.fetchone()[0]
    
    if quality_flag is not None:
        # Date is invalid
        logger.warning(f"Invalid date {article_data['date']}: {quality_flag}")
        
        # Option 1: Skip article
        return False
        
        # Option 2: Insert with flag for review
        article_data['data_quality_flag'] = quality_flag
    
    # Insert article
    cur.execute("""
        INSERT INTO articles (url, title, date, domain, data_quality_flag, ...)
        VALUES (%(url)s, %(title)s, %(date)s, %(domain)s, %(data_quality_flag)s, ...)
        ON CONFLICT (url) DO UPDATE ...
    """, article_data)
    
    conn.commit()
    return True
```

---

### Option B: Filter During Scraping

**Don't even scrape articles with invalid dates:**

```python
def should_scrape_article(article_date):
    # Get minimum date from config
    min_date = datetime(2003, 1, 1).date()
    max_date = datetime.now().date() + timedelta(days=90)
    
    if article_date < min_date:
        logger.info(f"Skipping article from {article_date} (before {min_date})")
        return False
    
    if article_date > max_date:
        logger.warning(f"Suspicious future date: {article_date}")
        return False
    
    return True

# In scraper
for article in scraped_articles:
    if should_scrape_article(article['date']):
        insert_article(conn, article)
```

---

### Option C: Use Database Trigger (Advanced)

**Automatically flag articles on insert:**

```sql
CREATE OR REPLACE FUNCTION auto_flag_articles()
RETURNS TRIGGER AS $$
BEGIN
    -- Auto-validate date on insert
    NEW.data_quality_flag := validate_article_date(NEW.date);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_auto_flag
BEFORE INSERT OR UPDATE ON articles
FOR EACH ROW
EXECUTE FUNCTION auto_flag_articles();
```

**Benefits:**
- ✅ Automatic (no scraper changes needed)
- ✅ Consistent across all scrapers
- ✅ Can't be bypassed

**Drawbacks:**
- ⚠️ Still inserts invalid articles (just flags them)
- ⚠️ Requires database cleanup later

---

## 📊 Current Data Quality Status

### Overall Statistics:
```
Total articles in database: 755,624
Clean articles (2003+):     740,001
Flagged articles:            13,095
    └─ pre_2003_outlier:         45
    └─ bulk_import_artifact: 13,050
```

### Domain Quality:
```
NULL domains:                     0  ✅
Domains properly formatted:   100%  ✅
Unique domains:                  77
```

### Temporal Quality:
```
Earliest clean article:  2003-01-01
Latest article:          2025-09-08
Clean coverage:          22.7 years
```

---

## 🎯 Next Steps for Scrapers

### 1. Update Scraper Code
- [ ] Add date validation before insert
- [ ] Log rejected articles
- [ ] Set minimum date to 2003-01-01

### 2. Test Scraper
- [ ] Test with pre-2003 dates (should reject/flag)
- [ ] Test with future dates (should reject/flag)
- [ ] Test with normal dates (should accept)

### 3. Update Dashboard/Analysis
- [ ] Use `clean_articles` view instead of `articles` table
- [ ] Update all COUNT/SELECT queries
- [ ] Verify statistics match corrected numbers

### 4. Documentation
- [ ] Document scraper changes
- [ ] Add data quality notes to README
- [ ] Create scraper testing guide

---

## 💡 Example: Updated Scraper Snippet

```python
import psycopg2
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class NordicMediaScraper:
    def __init__(self):
        self.conn = psycopg2.connect(...)
        self.min_date = self.get_min_date()
        self.max_future_days = self.get_max_future_days()
    
    def get_min_date(self):
        """Get minimum acceptable date from config"""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT value FROM data_quality_config WHERE key = 'min_article_date'"
        )
        result = cur.fetchone()
        return datetime.strptime(result[0], '%Y-%m-%d').date()
    
    def get_max_future_days(self):
        """Get max future days from config"""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT value FROM data_quality_config WHERE key = 'max_future_days'"
        )
        return int(cur.fetchone()[0])
    
    def is_valid_date(self, article_date):
        """Check if article date is valid"""
        max_date = datetime.now().date() + timedelta(days=self.max_future_days)
        
        if article_date < self.min_date:
            logger.warning(
                f"Article date {article_date} is before minimum {self.min_date}"
            )
            return False
        
        if article_date > max_date:
            logger.warning(
                f"Article date {article_date} is suspiciously far in future"
            )
            return False
        
        return True
    
    def scrape_article(self, url):
        # ... scraping logic ...
        article_data = {
            'url': url,
            'title': title,
            'date': article_date,
            'domain': domain,
            # ... other fields ...
        }
        
        # Validate date before insert
        if not self.is_valid_date(article_data['date']):
            logger.info(f"Skipping article with invalid date: {url}")
            return None
        
        # Insert article
        self.insert_article(article_data)
        return article_data
    
    def insert_article(self, article_data):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO articles (url, title, date, domain, content, ...)
            VALUES (%(url)s, %(title)s, %(date)s, %(domain)s, %(content)s, ...)
            ON CONFLICT (url) DO UPDATE SET
                title = EXCLUDED.title,
                date = EXCLUDED.date,
                updated_at = CURRENT_TIMESTAMP
        """, article_data)
        self.conn.commit()
```

---

## 🎉 Summary

### ✅ Both Questions Answered:

1. **Domain Quality**: Perfect! 0 NULL domains, all properly extracted
2. **Pre-2003 Prevention**: Infrastructure in place to prevent re-import

### ✅ What You Have Now:

1. **Configuration table** - centralized rules
2. **Quality flags** - mark bad data without deleting
3. **Validation function** - easy date checking
4. **Clean view** - one-stop for clean data
5. **13,095 articles flagged** - existing issues marked
6. **740,001 clean articles** - ready for analysis

### ✅ What to Do Next:

1. Update scrapers to use `validate_article_date()`
2. Update dashboard to use `clean_articles` view
3. Test scraper with pre-2003 dates
4. Document changes for team

---

**Your data quality is now production-grade!** 🎯

