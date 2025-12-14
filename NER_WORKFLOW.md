# NER Workflow - Where to Run Each Step

## Overview

NER processing requires GPU (transformers models), so it runs on the **VM/Server**, not locally.

## Step-by-Step Workflow

### Step 1: Test Locally (Optional) ✅
**Location**: Your local machine  
**Purpose**: Verify script syntax and logic

```bash
# Just syntax check (no GPU needed)
python3 -m py_compile scripts/34_ner_country_specific.py
```

### Step 2: Sync Script to VM ✅
**Location**: Your local machine  
**Purpose**: Upload updated script to server

```bash
python3 scripts/35_sync_ner_script.py
```

### Step 3: Run NER on VM ⏳
**Location**: VM/Server (GPU required)  
**Purpose**: Extract entities using country-specific models

**Option A: Test with 100 articles (RECOMMENDED FIRST)**
```bash
# On your local machine - creates sample and syncs
python3 scripts/38_test_ner_100.py

# Then on VM:
ssh -p 2111 frede@212.27.13.34
cd ~/NAMO_nov25
source venv/bin/activate

python3 scripts/34_ner_country_specific.py \
  --input data/processed/test_ner_100.parquet \
  --output data/nlp_enriched/test_ner_100_results.parquet \
  --device cuda \
  --score-threshold 0.5
```

**Option B: Run via SSH manually (full dataset)**
```bash
ssh -p 2111 frede@212.27.13.34
cd ~/NAMO_nov25
source venv/bin/activate

python3 scripts/34_ner_country_specific.py \
  --input data/processed/sample_1000.parquet \
  --output data/nlp_enriched/sample_1000_ner.parquet \
  --device cuda \
  --score-threshold 0.5
```

**Option C: Run via automated script**
```bash
# On your local machine
python3 scripts/36_run_ner_remote.py \
  --input data/processed/sample_1000.parquet \
  --output data/nlp_enriched/sample_1000_ner.parquet
```

**📋 Logging**: All runs create detailed logs in `logs/ner_YYYYMMDD_HHMMSS.log` on the VM

### Step 4: Download Results ✅
**Location**: Your local machine  
**Purpose**: Get results from VM

```bash
scp -P 2111 frede@212.27.13.34:~/NAMO_nov25/data/nlp_enriched/sample_1000_ner.parquet \
  data/nlp_enriched/
```

### Step 5: Load to Database ✅
**Location**: Your local machine  
**Purpose**: Update PostgreSQL with entity data

```bash
python3 scripts/37_load_ner_to_db.py \
  --input data/nlp_enriched/sample_1000_ner.parquet
```

### Step 6: Verify Frontend ✅
**Location**: Your local machine  
**Purpose**: Check dashboard shows updated entities

```bash
# Backend should already be running
# Frontend should auto-refresh
streamlit run frontend/app.py
```

## Quick Summary

| Step | Location | GPU Needed? | Command |
|------|----------|-------------|---------|
| Syntax Check | Local | ❌ | `python3 -m py_compile scripts/34_ner_country_specific.py` |
| Sync Script | Local | ❌ | `python3 scripts/35_sync_ner_script.py` |
| **Run NER** | **VM** | **✅ YES** | `python3 scripts/34_ner_country_specific.py ...` |
| Download | Local | ❌ | `scp ...` |
| Load to DB | Local | ❌ | `python3 scripts/37_load_ner_to_db.py ...` |
| View Dashboard | Local | ❌ | `streamlit run frontend/app.py` |

## Current Status

✅ Script created: `scripts/34_ner_country_specific.py`  
✅ Enhanced logging: File + console logging with DEBUG level  
✅ Test script: `scripts/38_test_ner_100.py` for quick testing  
✅ Sync script: `scripts/35_sync_ner_script.py`  
✅ Remote runner: `scripts/36_run_ner_remote.py`  
✅ DB loader: `scripts/37_load_ner_to_db.py`  
⏳ Next: Test on VM with 100 articles

## Debugging Tips

If the script gets stuck:

1. **Check the log file** on VM:
   ```bash
   tail -f ~/NAMO_nov25/logs/ner_*.log
   ```

2. **Check GPU memory**:
   ```bash
   nvidia-smi
   ```

3. **Check if model is downloading** (first run):
   - Models download from Hugging Face on first use
   - This can take several minutes
   - Check network activity or Hugging Face cache: `~/.cache/huggingface/`

4. **Check Python process**:
   ```bash
   ps aux | grep python
   ```

5. **Common hang points**:
   - Model loading/downloading (first time)
   - GPU memory exhaustion
   - Network issues downloading models
   - CUDA initialization

