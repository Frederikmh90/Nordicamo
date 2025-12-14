# Batch Processing Guide for NLP Enrichment

## Overview

This guide explains how to process large datasets (e.g., 1000 articles) in manageable chunks to avoid overwhelming the server.

## Quick Start - Database-Driven (Recommended)

### Process 200 articles from database in chunks of 50:

```bash
cd /home/frede/NAMO_nov25
python3 scripts/02_nlp_processing_from_db.py \
  --total-articles 200 \
  --chunk-size 50 \
  --model mistralai/Mistral-7B-Instruct-v0.3
```

**This script:**
- Queries database for unprocessed articles (`nlp_processed_at IS NULL`)
- Processes them in chunks
- Updates database directly after each chunk
- Can be run multiple times (automatically skips processed articles)

### Check how many articles need processing:

```bash
python3 scripts/02_nlp_processing_from_db.py --dry-run
```

## Alternative: Process from Parquet File

### Process 1000 articles in chunks of 100:

```bash
cd /home/frede/NAMO_nov25
python3 scripts/02_nlp_processing_batch.py \
  --input /home/frede/namo_samples/NAMO_2025_09_sample50.parquet \
  --output-dir /home/frede/namo_samples/enriched_batches \
  --total-articles 1000 \
  --chunk-size 100 \
  --start-from 0 \
  --model mistralai/Mistral-7B-Instruct-v0.3
```

### Parameters for Database Script:

- `--total-articles`: Total number to process (default: 200)
- `--chunk-size`: Articles per chunk (default: 50)
- `--model`: Model to use (default: Mistral 7B v0.3)
- `--use-quantization`: Enable 4-bit quantization (faster, less memory)
- `--dry-run`: Query and show articles but don't process

## Parameters for Parquet Script:

- `--input`: Input parquet file
- `--output-dir`: Directory where chunks will be saved
- `--total-articles`: Total number to process (default: 1000)
- `--chunk-size`: Articles per chunk (default: 100)
- `--start-from`: Resume from article index (default: 0)
- `--model`: Model to use (default: Mistral 7B v0.3)
- `--use-quantization`: Enable 4-bit quantization (faster, less memory)

## How Database Script Works

1. **Queries database** for unprocessed articles (`nlp_processed_at IS NULL`)
2. **Processes in chunks** of `--chunk-size` articles
3. **Updates database** directly after each chunk
4. **Automatically skips** already processed articles
5. **Can be run multiple times** - will process remaining articles

## How Parquet Script Works

1. **Loads data** from input parquet
2. **Slices** articles based on `--start-from` and `--total-articles`
3. **Processes in chunks** of `--chunk-size` articles
4. **Saves each chunk** immediately (so you don't lose progress)
5. **Combines all chunks** into final output file

## Example Output

```
/home/frede/namo_samples/enriched_batches/
├── chunk_0001.parquet  (articles 0-99)
├── chunk_0002.parquet  (articles 100-199)
├── ...
├── chunk_0010.parquet  (articles 900-999)
└── nlp_enriched_0_999.parquet  (combined file)
```

## Resuming After Interruption

### Database Script (Automatic Resume)

The database script automatically resumes - just run it again:

```bash
# Run again - will process remaining unprocessed articles
python3 scripts/02_nlp_processing_from_db.py \
  --total-articles 200 \
  --chunk-size 50
```

It queries for `nlp_processed_at IS NULL`, so already processed articles are automatically skipped.

### Parquet Script (Manual Resume)

If processing stops, you can resume:

```bash
# Check how many articles were processed
ls /home/frede/namo_samples/enriched_batches/chunk_*.parquet | wc -l

# Resume from article 500 (if 500 were already processed)
python3 scripts/02_nlp_processing_batch.py \
  --input /home/frede/namo_samples/NAMO_2025_09_sample50.parquet \
  --output-dir /home/frede/namo_samples/enriched_batches \
  --total-articles 1000 \
  --chunk-size 100 \
  --start-from 500
```

## Performance

- **Current speed**: ~24 seconds per article
- **1000 articles**: ~6.7 hours
- **With quantization**: ~15s/article = ~4.2 hours

See `PERFORMANCE_ANALYSIS.md` for details on why it's slow and optimization options.

## Database Loading

### Database Script (No Loading Needed!)

The database script updates articles directly - **no separate loading step required!**

### Parquet Script (Load After Processing)

If using the parquet script, load results into database:

```bash
# Load the combined file
python3 scripts/41_load_nlp_to_db.py \
  --input /home/frede/namo_samples/enriched_batches/nlp_enriched_0_999.parquet \
  --batch-size 5000
```

## Category Boolean Columns

The database stores categories as JSONB array, but you can also query using boolean columns:

- `newscat_crimejustice` (from "Crime & Justice")
- `newscat_politicsgovernance` (from "Politics & Governance")
- etc.

To add these columns, run:

```bash
psql -U namo_user -d namo_db -f scripts/42_add_category_boolean_columns.sql
```

Then query like:
```sql
SELECT * FROM articles WHERE newscat_crimejustice = TRUE;
```

