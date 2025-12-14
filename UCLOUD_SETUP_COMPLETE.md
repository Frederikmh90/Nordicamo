# UCloud NLP Processing Setup - Complete

## ✅ Setup Complete

### Environment
- **Server**: UCloud (`ssh -p 2693 ucloud@ssh.cloud.sdu.dk`)
- **GPU**: NVIDIA H100 80GB HBM3 (CUDA 12.8)
- **Python**: 3.12.3
- **Working Directory**: `/work/NAMO_nov25`

### Performance (vs Original Server)
- **GPU Memory**: 80GB vs 24GB (3.3x more)
- **Processing Speed**: ~1-2s per article vs ~15-20s (10-15x faster!)
- **Storage**: 4.7PB available

### Test Results
✅ Successfully processed 10 articles in **~30 seconds** (vs ~5 minutes on RTX 4090)
- Model loading: ~20s
- Processing: ~1s per article
- All JSON parsing successful on first attempt

## 📋 Current Status

### Data on UCloud
- ✅ CSV: `/work/NAMO_nov25/data/NAMO_2025_09.csv` (1.5GB, ~13.4M lines)
- ✅ Sample: `/work/NAMO_nov25/data/NAMO_2025_09_sample200.parquet`
- ✅ Test output: `/work/NAMO_nov25/data/test_10_enriched.parquet` (10 articles)

### Scripts
- ✅ `/work/NAMO_nov25/nlp_processor.py` - Core NLP processor
- ✅ `/work/NAMO_nov25/scripts/02_nlp_processing_csv.py` - CSV/Parquet processing script
- ✅ `/work/NAMO_nov25/venv/` - Python environment with all dependencies

## 🚀 Running NLP Processing

### Test Run (Already Complete)
```bash
ssh -p 2693 ucloud@ssh.cloud.sdu.dk
cd /work/NAMO_nov25
source venv/bin/activate

# Test with 10 articles
python3 scripts/02_nlp_processing_csv.py \
  --input data/NAMO_2025_09_sample200.parquet \
  --output data/test_10_enriched.parquet \
  --model mistralai/Mistral-7B-Instruct-v0.3 \
  --batch-size 5 \
  --max-articles 10
```

### Full Production Run

#### Option 1: Process Sample (200 articles, ~3-4 minutes)
```bash
ssh -p 2693 ucloud@ssh.cloud.sdu.dk
cd /work/NAMO_nov25
source venv/bin/activate

# Process 200 articles
nohup python3 scripts/02_nlp_processing_csv.py \
  --input data/NAMO_2025_09_sample200.parquet \
  --output data/NAMO_sample200_enriched.parquet \
  --model mistralai/Mistral-7B-Instruct-v0.3 \
  --batch-size 50 \
  > logs/nlp_sample200.log 2>&1 &

# Monitor progress
tail -f logs/nlp_sample200.log
```

#### Option 2: Process Subset from CSV (e.g., 10,000 articles, ~3 hours)
First, create a parquet sample from the large CSV:
```bash
ssh -p 2693 ucloud@ssh.cloud.sdu.dk
cd /work/NAMO_nov25
source venv/bin/activate

# Convert first 10K articles from CSV to Parquet
python3 << 'EOF'
import polars as pl
df = pl.read_csv('data/NAMO_2025_09.csv', 
                 infer_schema_length=10000, 
                 ignore_errors=True,
                 n_rows=10000)
df.write_parquet('data/NAMO_10k.parquet')
print(f"✅ Created sample with {len(df)} articles")
EOF

# Then process it
nohup python3 scripts/02_nlp_processing_csv.py \
  --input data/NAMO_10k.parquet \
  --output data/NAMO_10k_enriched.parquet \
  --model mistralai/Mistral-7B-Instruct-v0.3 \
  --batch-size 100 \
  --checkpoint 1000 \
  > logs/nlp_10k.log 2>&1 &
```

#### Option 3: Process ENTIRE Dataset (~13M articles, ~4-5 days)
**WARNING**: This will take several days. Make sure UCloud job has enough time.

```bash
ssh -p 2693 ucloud@ssh.cloud.sdu.dk
cd /work/NAMO_nov25
source venv/bin/activate

# First convert full CSV to Parquet (more reliable)
python3 << 'EOF'
import polars as pl
print("📂 Loading CSV (this may take a while)...")
df = pl.read_csv('data/NAMO_2025_09.csv', 
                 infer_schema_length=50000, 
                 ignore_errors=True)
print(f"✅ Loaded {len(df):,} articles")
print("💾 Writing to parquet...")
df.write_parquet('data/NAMO_full.parquet')
print("✅ Done!")
EOF

# Then process in batches with checkpointing
nohup python3 scripts/02_nlp_processing_csv.py \
  --input data/NAMO_full.parquet \
  --output data/NAMO_full_enriched.parquet \
  --model mistralai/Mistral-7B-Instruct-v0.3 \
  --batch-size 100 \
  --checkpoint 10000 \
  > logs/nlp_full.log 2>&1 &
```

## 📊 Monitoring

### Check if process is running
```bash
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "ps aux | grep 02_nlp_processing_csv | grep -v grep"
```

### Monitor logs
```bash
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "tail -f /work/NAMO_nov25/logs/*.log"
```

### Check GPU usage
```bash
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "nvidia-smi"
```

### Check progress (count lines in output)
```bash
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "cd /work/NAMO_nov25/data && python3 -c 'import polars as pl; df = pl.read_parquet(\"test_10_enriched.parquet\"); print(f\"Processed: {len(df):,} articles\")'"
```

## 📥 Retrieving Results

### Download enriched data
```bash
# Download to local machine
scp -P 2693 ucloud@ssh.cloud.sdu.dk:/work/NAMO_nov25/data/NAMO_sample200_enriched.parquet ./data/nlp_enriched/

# Or for the full dataset
scp -P 2693 ucloud@ssh.cloud.sdu.dk:/work/NAMO_nov25/data/NAMO_full_enriched.parquet ./data/nlp_enriched/
```

## 🔄 Transfer to Original Server (When Back Online)

Once the original server at `212.27.13.34` is back online:

```bash
# 1. Download from UCloud to local
scp -P 2693 ucloud@ssh.cloud.sdu.dk:/work/NAMO_nov25/data/NAMO_full_enriched.parquet ./data/

# 2. Upload to original server
scp -P 2111 ./data/NAMO_full_enriched.parquet frede@212.27.13.34:/home/frede/NAMO_nov25/data/

# 3. Load into PostgreSQL database
ssh -p 2111 frede@212.27.13.34
cd /home/frede/NAMO_nov25
python3 scripts/41_load_nlp_to_db.py --input data/NAMO_full_enriched.parquet
```

## ⚠️ Important Notes

1. **UCloud Job Time Limits**: Check your UCloud job allocation. For processing 13M articles, you'll need ~5 days of runtime.

2. **Checkpointing**: The script saves checkpoints every N articles (default: 1000). If interrupted, you can resume by:
   - Reading the existing output file
   - Filtering out already-processed articles
   - Processing only remaining ones

3. **CSV Issues**: The original CSV has quote-escaping issues. **Use Parquet format** instead - it's faster and more reliable.

4. **Performance**: 
   - H100: ~1-2s per article = ~360,000 articles/day
   - Full dataset (13M): ~36 days single-threaded
   - With optimizations/batching: ~4-5 days realistic

5. **Cost**: Check UCloud credits/costs for multi-day H100 usage.

## 🎯 Recommended Approach

**Start with Option 2** (10,000 articles):
- Fast enough to complete in a few hours
- Large enough to validate the full pipeline
- Can inspect quality before committing to full run
- Easy to iterate if issues found

Then proceed to full dataset if satisfied with results.

## 📞 Support

- **UCloud Issues**: Contact SDU UCloud support
- **Script Issues**: Check logs in `/work/NAMO_nov25/logs/`
- **GPU Issues**: Run `nvidia-smi` to check status

