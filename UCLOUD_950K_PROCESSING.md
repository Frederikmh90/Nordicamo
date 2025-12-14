# Processing 950K Articles on UCloud - Guide

## ✅ What Column Is Being Analyzed?

**The script analyzes the `content` column** for categories and sentiment.

Line 78 in the script:
```python
text = article.get('content', '') or article.get('description', '') or ''
```

It uses `content` first, falling back to `description` if content is empty.

## 📊 Batch Processing Strategy for 950K Articles

### Recommended Settings:
- **Batch size**: 1000 articles (processes 1000, then saves checkpoint)
- **Checkpoint interval**: 1000 articles (saves every 1000)
- **Format**: Parquet (faster and more reliable than CSV)
- **Resume**: Automatic (skips already-processed articles)

### Time Estimate:
- **Speed**: ~1-2 seconds per article on H100
- **Total time**: 950,000 articles ÷ 1 second = ~11 days
- **With overhead**: ~12-14 days realistic

## 🚀 Step-by-Step: Process 950K Articles

### Step 1: Prepare Data (Convert CSV to Parquet)

```bash
ssh -p 2693 ucloud@ssh.cloud.sdu.dk
cd /work/NAMO_nov25
source venv/bin/activate

# Check how many rows in the CSV
wc -l data/NAMO_2025_09.csv

# Convert to Parquet (more reliable)
python3 << 'EOF'
import polars as pl
print("📂 Loading CSV...")
df = pl.read_csv('data/NAMO_2025_09.csv', infer_schema_length=50000, ignore_errors=True)
print(f"✅ Loaded {len(df):,} articles")

# Take first 950K if needed
if len(df) > 950000:
    df = df.head(950000)
    print(f"Trimmed to {len(df):,} articles")

print("💾 Writing to parquet...")
df.write_parquet('data/NAMO_950k.parquet')
print(f"✅ Done! File: data/NAMO_950k.parquet")
EOF
```

### Step 2: Start Processing with Auto-Resume

```bash
cd /work/NAMO_nov25
source venv/bin/activate

# Start processing in background
nohup python3 scripts/02_nlp_batch_resume.py \
  --input data/NAMO_950k.parquet \
  --output data/NAMO_950k_enriched.parquet \
  --model mistralai/Mistral-7B-Instruct-v0.3 \
  --batch-size 1000 \
  --checkpoint 1000 \
  > logs/nlp_950k_$(date +%Y%m%d_%H%M%S).log 2>&1 &

echo "✅ Processing started in background!"
echo "Process ID: $!"
```

### Step 3: Monitor Progress

```bash
# View live log
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "tail -f /work/NAMO_nov25/logs/nlp_950k_*.log"

# Check how many processed so far
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "cd /work/NAMO_nov25 && source venv/bin/activate && python3 -c 'import polars as pl; df = pl.read_parquet(\"data/NAMO_950k_enriched.parquet\") if __import__(\"pathlib\").Path(\"data/NAMO_950k_enriched.parquet\").exists() else None; print(f\"Processed: {len(df):,}\" if df is not None else \"No checkpoint yet\")'"

# Check GPU usage
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "nvidia-smi"

# Check if process is running
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "ps aux | grep 02_nlp_batch_resume | grep -v grep"
```

### Step 4: Resume After Interruption

If the process stops for any reason (connection loss, job time limit, etc.):

```bash
ssh -p 2693 ucloud@ssh.cloud.sdu.dk
cd /work/NAMO_nov25
source venv/bin/activate

# Simply run the same command again - it will auto-resume!
nohup python3 scripts/02_nlp_batch_resume.py \
  --input data/NAMO_950k.parquet \
  --output data/NAMO_950k_enriched.parquet \
  --model mistralai/Mistral-7B-Instruct-v0.3 \
  --batch-size 1000 \
  --checkpoint 1000 \
  >> logs/nlp_950k_$(date +%Y%m%d_%H%M%S).log 2>&1 &
```

**The script automatically:**
- ✅ Detects already-processed articles (by URL)
- ✅ Skips them
- ✅ Continues from where it left off

### Step 5: Download Results

When complete (or for intermediate results):

```bash
# Download enriched data to your local machine
scp -P 2693 ucloud@ssh.cloud.sdu.dk:/work/NAMO_nov25/data/NAMO_950k_enriched.parquet ./data/nlp_enriched/

# Or download logs
scp -P 2693 ucloud@ssh.cloud.sdu.dk:/work/NAMO_nov25/logs/nlp_950k_*.log ./logs/
```

## 📈 Progress Tracking Script

Create a simple monitoring script:

```bash
# On your local machine
cat > monitor_ucloud.sh << 'EOF'
#!/bin/bash
while true; do
    clear
    echo "=========================================="
    echo "UCloud NLP Processing Monitor"
    echo "=========================================="
    echo ""
    
    # Check if process running
    echo "Process Status:"
    ssh -p 2693 ucloud@ssh.cloud.sdu.dk "ps aux | grep 02_nlp_batch_resume | grep -v grep | wc -l" | \
        awk '{if ($1 > 0) print "✅ RUNNING"; else print "❌ NOT RUNNING"}'
    echo ""
    
    # Check progress
    echo "Progress:"
    ssh -p 2693 ucloud@ssh.cloud.sdu.dk "cd /work/NAMO_nov25 && source venv/bin/activate && python3 -c 'import polars as pl; from pathlib import Path; p = Path(\"data/NAMO_950k_enriched.parquet\"); df = pl.read_parquet(p) if p.exists() else None; print(f\"Processed: {len(df):,} / 950,000 ({100*len(df)/950000:.1f}%)\") if df is not None else print(\"No checkpoint yet\")' 2>/dev/null"
    echo ""
    
    # GPU usage
    echo "GPU Usage:"
    ssh -p 2693 ucloud@ssh.cloud.sdu.dk "nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader" | \
        awk '{print "  GPU: "$1", Memory: "$2" / "$3}'
    echo ""
    
    # Last log lines
    echo "Recent Log:"
    ssh -p 2693 ucloud@ssh.cloud.sdu.dk "tail -3 /work/NAMO_nov25/logs/nlp_950k_*.log 2>/dev/null | tail -3"
    echo ""
    echo "=========================================="
    echo "Refreshing in 30 seconds... (Ctrl+C to stop)"
    sleep 30
done
EOF

chmod +x monitor_ucloud.sh
./monitor_ucloud.sh
```

## ⚙️ Advanced Options

### Test Run First (Recommended!)
Before the full 950K run, test with 10K:

```bash
ssh -p 2693 ucloud@ssh.cloud.sdu.dk
cd /work/NAMO_nov25 && source venv/bin/activate

python3 scripts/02_nlp_batch_resume.py \
  --input data/NAMO_950k.parquet \
  --output data/NAMO_10k_test.parquet \
  --model mistralai/Mistral-7B-Instruct-v0.3 \
  --batch-size 1000 \
  --checkpoint 1000 \
  --max-articles 10000
```

This will process 10K articles (~3-4 hours) to validate everything works.

### Start Fresh (Ignore Previous Checkpoint)

```bash
python3 scripts/02_nlp_batch_resume.py \
  --input data/NAMO_950k.parquet \
  --output data/NAMO_950k_enriched_v2.parquet \
  --no-resume \
  ...
```

### Adjust Batch Size

- **Smaller batches** (500): More frequent checkpoints, easier to resume
- **Larger batches** (2000): Fewer checkpoints, slightly faster

```bash
--batch-size 500 --checkpoint 500
```

## 🔧 Troubleshooting

### Process Died
```bash
# Check logs
tail -100 /work/NAMO_nov25/logs/nlp_950k_*.log

# Restart (will auto-resume)
nohup python3 scripts/02_nlp_batch_resume.py ... &
```

### Out of Memory
- GPU memory should be fine (H100 80GB, model uses ~14GB)
- If issues, reduce batch size: `--batch-size 500`

### Slow Processing
- Check GPU usage: `nvidia-smi`
- Should see ~90-100% GPU utilization
- If not, check for other processes: `nvidia-smi | grep python`

### Check Intermediate Results
```bash
cd /work/NAMO_nov25 && source venv/bin/activate
python3 -c "
import polars as pl
df = pl.read_parquet('data/NAMO_950k_enriched.parquet')
print(f'Total: {len(df):,}')
print(f'Columns: {df.columns}')
print(f'\\nSample row:')
print(df[0])
print(f'\\nCategories sample:')
print(df['categories'].head(10))
"
```

## 📊 Summary: What to Run

**For 950K articles with batch size 1000:**

```bash
# 1. SSH to UCloud
ssh -p 2693 ucloud@ssh.cloud.sdu.dk

# 2. Prepare data
cd /work/NAMO_nov25 && source venv/bin/activate
python3 << 'EOF'
import polars as pl
df = pl.read_csv('data/NAMO_2025_09.csv', infer_schema_length=50000, ignore_errors=True)
df = df.head(950000)
df.write_parquet('data/NAMO_950k.parquet')
print(f"✅ Ready: {len(df):,} articles")
EOF

# 3. Start processing
nohup python3 scripts/02_nlp_batch_resume.py \
  --input data/NAMO_950k.parquet \
  --output data/NAMO_950k_enriched.parquet \
  --model mistralai/Mistral-7B-Instruct-v0.3 \
  --batch-size 1000 \
  --checkpoint 1000 \
  > logs/nlp_950k_$(date +%Y%m%d_%H%M%S).log 2>&1 &

# 4. Monitor
tail -f logs/nlp_950k_*.log
```

**That's it!** The script handles everything else automatically.

