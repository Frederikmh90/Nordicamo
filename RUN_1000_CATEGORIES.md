# Running Category Classification on 1000 Articles

## Overview

This guide walks you through:
1. Running category classification on 1000 articles (with second pass for "Other")
2. Loading results into PostgreSQL database
3. Updating the dashboard

## Step-by-Step

### 1. Run Category Classification

```bash
# On your server
cd ~/NAMO_nov25
source venv/bin/activate

# Run the automated script
python3 scripts/29_run_category_classification_1000.py \
  --input data/processed/NAMO_preprocessed_test.parquet \
  --model mistralai/Mistral-7B-Instruct-v0.2
```

This script will:
- ✅ Create a sample of 1000 articles
- ✅ Run category classification (with second pass for "Other")
- ✅ Load results into database
- ✅ Show summary statistics

### 2. Manual Steps (if needed)

If you prefer to run steps manually:

```bash
# Step 1: Create 1000 article sample
python3 -c "
import polars as pl
df = pl.read_parquet('data/processed/NAMO_preprocessed_test.parquet')
df.head(1000).write_parquet('data/processed/sample_1000.parquet')
print('Created sample_1000.parquet')
"

# Step 2: Run classification
python3 scripts/26_category_classification_only.py \
  --input data/processed/sample_1000.parquet \
  --output data/nlp_enriched/sample_1000_categories.parquet \
  --model mistralai/Mistral-7B-Instruct-v0.2 \
  --no-quantization

# Step 3: Load to database
python3 scripts/28_load_categories_to_db.py \
  --input data/nlp_enriched/sample_1000_categories.parquet
```

### 3. Update Dashboard

The dashboard should automatically show the new categories. If not:

```bash
# Start backend (if not running)
cd backend
uvicorn app.main:app --reload

# Start frontend (if not running)
streamlit run frontend/app.py
```

## Features

### Second Pass for "Other" Categories

The script automatically:
1. Processes all articles (first pass)
2. Identifies articles classified as "Other"
3. Re-processes those articles (second pass)
4. Updates if a different category is found
5. Keeps "Other" if it's still "Other" after second pass

This reduces false "Other" assignments!

## Database Schema

The script automatically adds these columns if they don't exist:
- `category` (VARCHAR) - Primary category
- `category_reasoning` (TEXT) - LLM reasoning
- `category_processed_at` (TIMESTAMP) - Processing timestamp

## Dashboard

The dashboard will show:
- Category distribution chart
- Category statistics
- Filterable by country and partisan

## Troubleshooting

If database connection fails:
- Check PostgreSQL is running: `brew services list | grep postgresql`
- Check connection settings in `backend/app/config.py`

If categories don't show in dashboard:
- Clear Streamlit cache: `rm -rf ~/.streamlit/cache`
- Restart backend and frontend

