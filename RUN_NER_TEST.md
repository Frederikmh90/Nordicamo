# Quick Start: Test NER with 100 Articles

## Step-by-Step Guide

### 1. Sync Script to VM (Local Machine)
```bash
cd /Users/Codebase/projects/alterpublics/NAMO_nov25
python3 scripts/35_sync_ner_script.py
```

### 2. Create Test Sample (Local Machine)
```bash
python3 scripts/38_test_ner_100.py
```

This creates `data/processed/test_ner_100.parquet` with 100 articles.

### 3. Upload Sample to VM (Local Machine)
```bash
scp -P 2111 data/processed/test_ner_100.parquet \
  frede@212.27.13.34:~/NAMO_nov25/data/processed/
```

### 4. Run NER on VM
```bash
ssh -p 2111 frede@212.27.13.34
cd ~/NAMO_nov25
source venv/bin/activate

python3 scripts/34_ner_country_specific.py \
  --input data/processed/test_ner_100.parquet \
  --output data/nlp_enriched/test_ner_100_results.parquet \
  --device cuda \
  --score-threshold 0.5
```

### 5. Monitor Progress

**In another terminal (local machine):**
```bash
ssh -p 2111 frede@212.27.13.34
tail -f ~/NAMO_nov25/logs/ner_*.log
```

**Or check GPU usage:**
```bash
watch -n 2 nvidia-smi
```

### 6. Download Results (Local Machine)
```bash
scp -P 2111 frede@212.27.13.34:~/NAMO_nov25/data/nlp_enriched/test_ner_100_results.parquet \
  data/nlp_enriched/
```

### 7. Load to Database (Local Machine)
```bash
python3 scripts/37_load_ner_to_db.py \
  --input data/nlp_enriched/test_ner_100_results.parquet
```

## What to Look For

### ✅ Success Indicators:
- Log shows "Loading NER model for..." messages
- Progress bar advances
- "Extracted X raw entities" messages appear
- Final summary shows entity counts

### ❌ Problem Indicators:
- Script hangs at "Loading tokenizer..."
- No progress after 5+ minutes
- GPU memory errors
- Network timeout errors

### 🔍 Debug Commands:

**Check if script is running:**
```bash
ps aux | grep "34_ner_country_specific"
```

**Check GPU:**
```bash
nvidia-smi
```

**Check latest log:**
```bash
ls -lt ~/NAMO_nov25/logs/ner_*.log | head -1
tail -50 <latest_log>
```

**Check Hugging Face cache (model downloads):**
```bash
ls -lh ~/.cache/huggingface/hub/
```

## Expected Runtime

- **First run**: 10-15 minutes (model downloads)
- **Subsequent runs**: 2-5 minutes (models cached)
- **Per article**: ~1-3 seconds

## Log File Location

Logs are saved to: `~/NAMO_nov25/logs/ner_YYYYMMDD_HHMMSS.log`

Each run creates a new log file with timestamp.




