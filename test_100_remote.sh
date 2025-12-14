#!/bin/bash
# Quick test script for remote server

echo "=========================================="
echo "Testing NLP Processing with 100 Articles"
echo "=========================================="

# Create test dataset
echo "Creating test dataset..."
python3 -c "
import polars as pl
df = pl.read_parquet('data/processed/NAMO_preprocessed_test.parquet')
df.head(100).write_parquet('data/processed/test_100.parquet')
print(f'✅ Created test_100.parquet with {len(df.head(100))} articles')
"

# Run NLP processing
echo ""
echo "Running NLP processing..."
python3 scripts/02_nlp_processing.py \
  --input data/processed/test_100.parquet \
  --output data/nlp_enriched/test_100_debug.parquet \
  --batch-size 4 \
  --no-quantization 2>&1 | tee logs/nlp_debug_100.log

echo ""
echo "=========================================="
echo "Check logs/nlp_debug_100.log for results"
echo "=========================================="
