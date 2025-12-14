# UCloud Quick Reference - 950K Articles

## 🎯 What's Analyzed?
**Column**: `content` (falls back to `description` if empty)
**Output**: `sentiment`, `sentiment_score`, `categories` (list), `entities`, `nlp_processed_at`

## ⚡ Quick Start

```bash
# Connect
ssh -p 2693 ucloud@ssh.cloud.sdu.dk

# Start processing (950K articles, batch 1000, auto-resume)
cd /work/NAMO_nov25 && source venv/bin/activate
nohup python3 scripts/02_nlp_batch_resume.py \
  --input data/NAMO_950k.parquet \
  --output data/NAMO_950k_enriched.parquet \
  --model mistralai/Mistral-7B-Instruct-v0.3 \
  --batch-size 1000 \
  --checkpoint 1000 \
  > logs/nlp_950k.log 2>&1 &

# Monitor
tail -f logs/nlp_950k.log
```

## 📊 Check Progress

```bash
# How many processed?
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "cd /work/NAMO_nov25 && source venv/bin/activate && python3 -c 'import polars as pl; df = pl.read_parquet(\"data/NAMO_950k_enriched.parquet\"); print(f\"{len(df):,} / 950,000\")'"

# Is it running?
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "ps aux | grep 02_nlp_batch_resume | grep -v grep"

# GPU usage
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "nvidia-smi"
```

## 🔄 Resume After Stop

Just run the same command again - it automatically skips processed articles!

```bash
nohup python3 scripts/02_nlp_batch_resume.py \
  --input data/NAMO_950k.parquet \
  --output data/NAMO_950k_enriched.parquet \
  --model mistralai/Mistral-7B-Instruct-v0.3 \
  --batch-size 1000 \
  --checkpoint 1000 \
  >> logs/nlp_950k.log 2>&1 &
```

## ⏱️ Time Estimate
- **Speed**: 1-2 seconds/article
- **950K articles**: ~11-14 days
- **Checkpoints**: Every 1000 articles (auto-save)

## 📥 Download Results

```bash
scp -P 2693 ucloud@ssh.cloud.sdu.dk:/work/NAMO_nov25/data/NAMO_950k_enriched.parquet ./data/nlp_enriched/
```

## 🆘 Troubleshooting

**Process died?** → Check logs, then restart (auto-resumes)
**Too slow?** → Check `nvidia-smi` for GPU utilization  
**Out of memory?** → Reduce batch: `--batch-size 500`

See `UCLOUD_950K_PROCESSING.md` for full details.

