# Phase 1 Progress - 10% Stratified Sample

## ✅ Started: $(date)

### Configuration
- **Input**: `NAMO_10pct_stratified.parquet`
- **Output**: `NAMO_10pct_enriched.parquet`
- **Articles**: 81,272 (10% from each of 57 outlets)
- **Model**: Mistral-7B-Instruct-v0.3
- **Batch size**: 1000
- **Checkpoint**: Every 1000 articles
- **Estimated time**: 1-2 days

### Test Results (100 articles)
✅ Successfully processed 100 articles
✅ Multiple outlets represented (17 different domains)
✅ Categories assigned correctly
✅ Sentiment analysis working

### Quick Monitoring Commands

```bash
# Check progress
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "cd /work/NAMO_nov25 && source venv/bin/activate && python3 -c 'import polars as pl; df = pl.read_parquet(\"data/NAMO_10pct_enriched.parquet\"); print(f\"{len(df):,} / 81,272 ({100*len(df)/81272:.1f}%)\")' 2>/dev/null || echo 'No checkpoint yet'"

# Watch log
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "tail -f /work/NAMO_nov25/logs/nlp_phase1_*.log"

# Check if running
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "ps aux | grep 02_nlp_batch_resume | grep -v grep"

# GPU status
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "nvidia-smi"
```

### Resume If Interrupted

```bash
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "cd /work/NAMO_nov25 && source venv/bin/activate && nohup python3 scripts/02_nlp_batch_resume.py --input data/NAMO_10pct_stratified.parquet --output data/NAMO_10pct_enriched.parquet --model mistralai/Mistral-7B-Instruct-v0.3 --batch-size 1000 --checkpoint 1000 >> logs/nlp_phase1_resume.log 2>&1 &"
```

### Download Results When Complete

```bash
scp -P 2693 ucloud@ssh.cloud.sdu.dk:/work/NAMO_nov25/data/NAMO_10pct_enriched.parquet ./data/nlp_enriched/
```

---

## Progress Log

Will update as processing continues...

