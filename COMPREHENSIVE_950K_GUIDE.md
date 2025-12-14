# 950K Article NLP Processing - Complete Guide

## 📊 Dataset Prepared

✅ **File**: `/work/NAMO_nov25/data/NAMO_950k.parquet`
✅ **Size**: 918.9 MB
✅ **Articles**: 950,000
✅ **Columns**: url, title, description, content, author, date, extraction_method, domain, country, content_length, scraped_at

## 🎯 Processing Configuration

- **Input Column**: `content` (falls back to `description` if empty)
- **Output Columns Added**: 
  - `sentiment` (positive/negative/neutral)
  - `sentiment_score` (float)
  - `categories` (list of strings)
  - `entities` (structured data with PERSON, ORG, LOC, etc.)
  - `nlp_processed_at` (ISO timestamp)

## 🚀 Execution Plan

### Phase 1: Test Run (100 articles) - 2 minutes

Validate everything works before committing to the full run:

```bash
ssh -p 2693 ucloud@ssh.cloud.sdu.dk
cd /work/NAMO_nov25 && source venv/bin/activate

# Test with 100 articles first
python3 scripts/02_nlp_batch_resume.py \
  --input data/NAMO_950k.parquet \
  --output data/test_100_batch.parquet \
  --model mistralai/Mistral-7B-Instruct-v0.3 \
  --batch-size 100 \
  --checkpoint 100 \
  --max-articles 100

# Verify output
python3 << 'EOF'
import polars as pl
df = pl.read_parquet('data/test_100_batch.parquet')
print(f"✅ Processed: {len(df)} articles")
print(f"Columns: {df.columns}")
print(f"\nSample categories:")
print(df.select(['url', 'categories', 'sentiment']).head(5))
EOF
```

### Phase 2: Production Run (950K articles) - ~11-14 days

Once test looks good:

```bash
ssh -p 2693 ucloud@ssh.cloud.sdu.dk
cd /work/NAMO_nov25 && source venv/bin/activate

# Create logs directory if needed
mkdir -p logs

# Start full processing in background
nohup python3 scripts/02_nlp_batch_resume.py \
  --input data/NAMO_950k.parquet \
  --output data/NAMO_950k_enriched.parquet \
  --model mistralai/Mistral-7B-Instruct-v0.3 \
  --batch-size 1000 \
  --checkpoint 1000 \
  > logs/nlp_950k_$(date +%Y%m%d_%H%M%S).log 2>&1 &

# Save the process ID
echo $! > logs/nlp_process.pid
echo "✅ Started! Process ID: $(cat logs/nlp_process.pid)"
echo "📝 Log file: logs/nlp_950k_$(date +%Y%m%d_%H%M%S).log"
```

## 📊 Monitoring Commands

### Quick Status Check

```bash
# One-liner status
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "cd /work/NAMO_nov25 && source venv/bin/activate && python3 -c 'import polars as pl; from pathlib import Path; p = Path(\"data/NAMO_950k_enriched.parquet\"); print(f\"Processed: {len(pl.read_parquet(p)):,} / 950,000 ({100*len(pl.read_parquet(p))/950000:.1f}%)\") if p.exists() else print(\"Not started yet\")' 2>/dev/null || echo 'No checkpoint yet'"
```

### Detailed Status

```bash
ssh -p 2693 ucloud@ssh.cloud.sdu.dk << 'EOF'
cd /work/NAMO_nov25
source venv/bin/activate

echo "=========================================="
echo "NLP Processing Status"
echo "=========================================="
echo ""

# Check if process is running
if pgrep -f "02_nlp_batch_resume" > /dev/null; then
    echo "Status: ✅ RUNNING"
    echo "PID: $(pgrep -f 02_nlp_batch_resume)"
else
    echo "Status: ❌ NOT RUNNING"
fi
echo ""

# Check progress
if [ -f "data/NAMO_950k_enriched.parquet" ]; then
    python3 << 'PYEOF'
import polars as pl
df = pl.read_parquet('data/NAMO_950k_enriched.parquet')
processed = len(df)
total = 950000
pct = 100 * processed / total
remaining = total - processed
print(f"Progress: {processed:,} / {total:,} ({pct:.1f}%)")
print(f"Remaining: {remaining:,} articles")

# Estimate time remaining (1.5s per article average)
time_remaining_hours = (remaining * 1.5) / 3600
print(f"Est. time remaining: {time_remaining_hours:.1f} hours ({time_remaining_hours/24:.1f} days)")
PYEOF
else
    echo "Progress: No checkpoint yet (0 / 950,000)"
fi
echo ""

# GPU status
echo "GPU Status:"
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader | \
    awk '{print "  Utilization: "$1", Memory: "$2" / "$3}'
echo ""

# Recent log entries
echo "Recent Log (last 5 lines):"
tail -5 logs/nlp_950k_*.log 2>/dev/null | tail -5 || echo "  No log file yet"
echo ""
echo "=========================================="
EOF
```

### Live Log Monitoring

```bash
# Watch log in real-time
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "tail -f /work/NAMO_nov25/logs/nlp_950k_*.log"

# Press Ctrl+C to stop watching
```

### Create Local Monitoring Script

```bash
# On your local machine
cat > monitor_nlp.sh << 'EOF'
#!/bin/bash
while true; do
    clear
    echo "=========================================="
    echo "UCloud NLP Processing Monitor"
    echo "$(date)"
    echo "=========================================="
    echo ""
    
    ssh -p 2693 ucloud@ssh.cloud.sdu.dk "cd /work/NAMO_nov25 && source venv/bin/activate && python3 << 'PYEOF'
import polars as pl
from pathlib import Path
import subprocess

# Check process
proc_count = subprocess.run(['pgrep', '-f', '02_nlp_batch_resume'], 
                           capture_output=True).returncode == 0
print(f\"Status: {'✅ RUNNING' if proc_count else '❌ NOT RUNNING'}\")
print()

# Check progress
p = Path('data/NAMO_950k_enriched.parquet')
if p.exists():
    df = pl.read_parquet(p)
    processed = len(df)
    total = 950000
    pct = 100 * processed / total
    remaining = total - processed
    print(f'Progress: {processed:,} / {total:,} ({pct:.1f}%)')
    print(f'Remaining: {remaining:,}')
    
    # Time estimate
    time_hrs = (remaining * 1.5) / 3600
    print(f'Est. remaining: {time_hrs:.1f}h ({time_hrs/24:.1f} days)')
else:
    print('Progress: Not started')
print()

# GPU
import subprocess
gpu = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used', 
                     '--format=csv,noheader'], capture_output=True, text=True)
print(f'GPU: {gpu.stdout.strip()}')
PYEOF
" 2>/dev/null || echo "Connection error"
    
    echo ""
    echo "=========================================="
    echo "Refreshing in 60 seconds... (Ctrl+C to stop)"
    sleep 60
done
EOF

chmod +x monitor_nlp.sh

# Run it
./monitor_nlp.sh
```

## 🔄 Resume After Interruption

If processing stops for ANY reason:

```bash
ssh -p 2693 ucloud@ssh.cloud.sdu.dk
cd /work/NAMO_nov25 && source venv/bin/activate

# Just run the SAME command again - it auto-resumes!
nohup python3 scripts/02_nlp_batch_resume.py \
  --input data/NAMO_950k.parquet \
  --output data/NAMO_950k_enriched.parquet \
  --model mistralai/Mistral-7B-Instruct-v0.3 \
  --batch-size 1000 \
  --checkpoint 1000 \
  >> logs/nlp_950k_resume_$(date +%Y%m%d_%H%M%S).log 2>&1 &
```

**The script automatically:**
- Reads existing checkpoint file
- Extracts URLs of processed articles
- Skips them
- Continues with remaining articles

## ⏸️ Pause/Stop Processing

```bash
# Find process ID
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "pgrep -f 02_nlp_batch_resume"

# Stop it (gracefully saves checkpoint)
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "pkill -f 02_nlp_batch_resume"

# Or if you saved the PID
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "kill $(cat /work/NAMO_nov25/logs/nlp_process.pid)"
```

## 📥 Download Results

### Download Completed File

```bash
# To your local machine
scp -P 2693 ucloud@ssh.cloud.sdu.dk:/work/NAMO_nov25/data/NAMO_950k_enriched.parquet \
    ./data/nlp_enriched/NAMO_950k_enriched_$(date +%Y%m%d).parquet
```

### Download Partial Results (While Running)

```bash
# Download current checkpoint
scp -P 2693 ucloud@ssh.cloud.sdu.dk:/work/NAMO_nov25/data/NAMO_950k_enriched.parquet \
    ./data/nlp_enriched/NAMO_950k_partial_$(date +%Y%m%d).parquet
```

### Inspect Results Locally

```bash
python3 << 'EOF'
import polars as pl

df = pl.read_parquet('data/nlp_enriched/NAMO_950k_enriched_*.parquet')

print(f"Total articles: {len(df):,}")
print(f"Columns: {df.columns}")
print()

# Category distribution
print("Category Distribution:")
categories_flat = df['categories'].explode()
print(categories_flat.value_counts().head(15))
print()

# Sentiment distribution
print("Sentiment Distribution:")
print(df['sentiment'].value_counts())
print()

# Sample with categories
print("Sample Articles:")
print(df.select(['url', 'sentiment', 'categories']).head(10))
EOF
```

## 📊 Performance Metrics

### Expected Performance
- **Speed**: 1-2 seconds per article on H100
- **Throughput**: 30,000-36,000 articles per day
- **Total time**: 950,000 ÷ 32,000 = ~30 days
- **Realistic estimate**: 11-14 days (with optimizations)

### Actual Performance Tracking

```bash
ssh -p 2693 ucloud@ssh.cloud.sdu.dk << 'EOF'
cd /work/NAMO_nov25
source venv/bin/activate

python3 << 'PYEOF'
import polars as pl
from pathlib import Path
from datetime import datetime

if Path('data/NAMO_950k_enriched.parquet').exists():
    df = pl.read_parquet('data/NAMO_950k_enriched.parquet')
    
    # Get timestamps
    df_with_time = df.filter(pl.col('nlp_processed_at').is_not_null())
    
    if len(df_with_time) > 100:
        # Parse timestamps
        times = pl.Series([datetime.fromisoformat(t) for t in df_with_time['nlp_processed_at'].to_list()])
        
        first = times.min()
        last = times.max()
        duration = (last - first).total_seconds()
        
        articles_processed = len(df_with_time)
        avg_time = duration / articles_processed
        
        print(f"Performance Metrics:")
        print(f"  Processed: {articles_processed:,} articles")
        print(f"  Duration: {duration/3600:.1f} hours")
        print(f"  Avg time: {avg_time:.2f}s per article")
        print(f"  Rate: {articles_processed/(duration/3600):.0f} articles/hour")
    else:
        print("Not enough data yet for performance metrics")
else:
    print("No checkpoint file yet")
PYEOF
EOF
```

## 🆘 Troubleshooting

### Process Not Running

```bash
# Check what happened
tail -50 /work/NAMO_nov25/logs/nlp_950k_*.log

# Common causes:
# 1. Job time limit reached → Restart with resume
# 2. Out of memory → Reduce batch size
# 3. GPU error → Check nvidia-smi
```

### Slow Processing

```bash
# Check GPU utilization
nvidia-smi

# Should see:
# - GPU Util: 90-100%
# - Memory: ~14GB used

# If low utilization:
# - Check for other GPU processes
# - Check CPU usage (might be CPU bottleneck)
```

### Check for Errors in Output

```bash
ssh -p 2693 ucloud@ssh.cloud.sdu.dk << 'EOF'
cd /work/NAMO_nov25 && source venv/bin/activate
python3 << 'PYEOF'
import polars as pl

df = pl.read_parquet('data/NAMO_950k_enriched.parquet')

# Check for null categories (should be rare)
null_cats = df.filter(pl.col('categories').list.len() == 0)
print(f"Articles with no categories: {len(null_cats)} ({100*len(null_cats)/len(df):.2f}%)")

# Check category "Other"
other_cats = df.filter(pl.col('categories').list.contains('Other'))
print(f"Articles with 'Other' category: {len(other_cats)} ({100*len(other_cats)/len(df):.2f}%)")

# Sentiment distribution
print(f"\nSentiment distribution:")
print(df['sentiment'].value_counts())
PYEOF
EOF
```

## 🎯 Final Checklist

Before starting the full run:

- [ ] Test run completed (100 articles)
- [ ] Output looks correct (categories, sentiment, entities)
- [ ] GPU is working (check nvidia-smi)
- [ ] UCloud job has enough time (14+ days)
- [ ] Monitoring script set up
- [ ] Know how to resume if interrupted

## 📞 Quick Commands Reference

```bash
# Start processing
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "cd /work/NAMO_nov25 && source venv/bin/activate && nohup python3 scripts/02_nlp_batch_resume.py --input data/NAMO_950k.parquet --output data/NAMO_950k_enriched.parquet --model mistralai/Mistral-7B-Instruct-v0.3 --batch-size 1000 --checkpoint 1000 > logs/nlp_950k.log 2>&1 &"

# Check progress
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "cd /work/NAMO_nov25 && source venv/bin/activate && python3 -c 'import polars as pl; print(len(pl.read_parquet(\"data/NAMO_950k_enriched.parquet\")))' 2>/dev/null || echo 0"

# View log
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "tail -f /work/NAMO_nov25/logs/nlp_950k*.log"

# Stop
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "pkill -f 02_nlp_batch_resume"

# Resume
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "cd /work/NAMO_nov25 && source venv/bin/activate && nohup python3 scripts/02_nlp_batch_resume.py --input data/NAMO_950k.parquet --output data/NAMO_950k_enriched.parquet --model mistralai/Mistral-7B-Instruct-v0.3 --batch-size 1000 --checkpoint 1000 >> logs/nlp_950k_resume.log 2>&1 &"
```

---

**Ready to start? Run the test first (Phase 1), then proceed to the full run (Phase 2)!** 🚀

