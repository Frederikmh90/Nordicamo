# Database Setup Complete! ✅

## Status

✅ **Database created:** `namo_db`  
✅ **User created:** `namo_user`  
✅ **Schema created:** `articles` and `actors` tables  
✅ **Connection tested:** Working!  
✅ **Environment file:** `.env` created with credentials

## Current Status

- **Unprocessed articles:** 0 (database is empty)
- **Next step:** Load articles into database

## How to Use

### 1. Load Articles into Database

You have two options:

**Option A: Load from parquet file**
```bash
cd /home/frede/NAMO_nov25
python3 scripts/04_load_data_to_db.py \
  --articles /path/to/articles.parquet \
  --batch-size 100
```

**Option B: Load preprocessed data**
```bash
# If you have preprocessed parquet files
python3 scripts/04_load_data_to_db.py \
  --articles /home/frede/namo_samples/NAMO_2025_09_sample50.parquet \
  --batch-size 100
```

### 2. Process Articles with NLP

Once articles are loaded, run:

```bash
cd /home/frede/NAMO_nov25

# Check how many need processing
python3 scripts/02_nlp_processing_from_db.py --dry-run

# Process 200 articles in chunks of 50
python3 scripts/02_nlp_processing_from_db.py \
  --total-articles 200 \
  --chunk-size 50 \
  --model mistralai/Mistral-7B-Instruct-v0.3
```

### 3. Check Progress

```bash
# Connect to database
psql -h localhost -U namo_user -d namo_db

# Check how many articles are processed
SELECT COUNT(*) FROM articles WHERE nlp_processed_at IS NOT NULL;

# Check how many still need processing
SELECT COUNT(*) FROM articles WHERE nlp_processed_at IS NULL;

# See sample of processed articles
SELECT title, sentiment, categories FROM articles 
WHERE nlp_processed_at IS NOT NULL 
LIMIT 5;
```

## Database Credentials

Stored in `/home/frede/NAMO_nov25/.env`:
```
DB_HOST=localhost
DB_PORT=5432
DB_USER=namo_user
DB_PASSWORD=namo_password
DB_NAME=namo_db
```

## Connection String

For direct psql access:
```bash
psql -h localhost -U namo_user -d namo_db
# Password: namo_password
```

## Performance

With the optimized script (no reasoning field):
- **Speed:** ~10-12 seconds per article
- **200 articles:** ~35-40 minutes
- **1000 articles:** ~3-3.5 hours

## Troubleshooting

**"No articles need processing":**
- Database is empty - load articles first using `scripts/04_load_data_to_db.py`

**"Permission denied":**
- Schema permissions are already granted, but if issues persist:
  ```bash
  sudo -u postgres psql namo_db -c "GRANT ALL ON SCHEMA public TO namo_user;"
  ```

**"Connection refused":**
- PostgreSQL is running (verified), but if issues:
  ```bash
  sudo systemctl status postgresql
  ```


