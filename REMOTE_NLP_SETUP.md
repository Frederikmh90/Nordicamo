# Remote NLP Processing Setup Guide

## Overview

This guide explains how to run NLP processing on the remote GPU server using SSH.

## Prerequisites

1. **SSH Access**: You need SSH access to the server
   - Host: `212.27.13.34`
   - Port: `2111`
   - User: `frede`
   - Password: (you'll be prompted)

2. **Python Environment**: Python 3 should be installed on the remote server

3. **GPU Access**: The server should have CUDA/GPU support for Qwen2.5

## Method 1: Interactive Python Script (Recommended)

This method handles password authentication interactively:

```bash
# Install paramiko if not already installed
pip install paramiko

# Run the interactive script
python3 scripts/05_run_nlp_remote_interactive.py \
    --input data/processed/NAMO_preprocessed_test.parquet \
    --batch-size 4
```

**What it does:**
1. Prompts for SSH password
2. Connects to remote server
3. Sets up directory structure
4. Syncs necessary files (scripts, data, requirements)
5. Installs Python dependencies
6. Runs NLP processing
7. Shows output in real-time

**Options:**
- `--input`: Path to input parquet file (default: `data/processed/NAMO_preprocessed_test.parquet`)
- `--batch-size`: Batch size for processing (default: 4)
- `--setup-only`: Only set up environment, don't run processing

## Method 2: Shell Script (Requires SSH Key Setup)

If you have SSH keys set up (passwordless login):

```bash
# Make script executable
chmod +x scripts/05_run_nlp_remote.sh

# Run the script
./scripts/05_run_nlp_remote.sh data/processed/NAMO_preprocessed_test.parquet 4
```

**What it does:**
1. Syncs files using `rsync`
2. Sets up environment
3. Runs processing in background
4. Provides commands to monitor progress

## Manual Steps (If Scripts Don't Work)

### Step 1: Connect to Server

```bash
ssh -p 2111 frede@212.27.13.34
```

### Step 2: Set Up Directory Structure

```bash
mkdir -p ~/NAMO_nov25/{scripts,data/processed,data/nlp_enriched,models,logs}
cd ~/NAMO_nov25
```

### Step 3: Upload Files

From your local machine:

```bash
# Upload scripts
scp -P 2111 scripts/02_nlp_processing.py frede@212.27.13.34:~/NAMO_nov25/scripts/

# Upload input data
scp -P 2111 data/processed/NAMO_preprocessed_test.parquet frede@212.27.13.34:~/NAMO_nov25/data/processed/

# Upload requirements
scp -P 2111 requirements.txt frede@212.27.13.34:~/NAMO_nov25/
```

### Step 4: Install Dependencies (on remote server)

```bash
cd ~/NAMO_nov25
pip install -r requirements.txt
python3 -m spacy download xx_ent_wiki_sm
```

### Step 5: Run NLP Processing (on remote server)

```bash
cd ~/NAMO_nov25
python3 scripts/02_nlp_processing.py \
    --input data/processed/NAMO_preprocessed_test.parquet \
    --batch-size 4 \
    > logs/nlp_processing.log 2>&1 &
```

### Step 6: Monitor Progress

```bash
# Watch log file
tail -f ~/NAMO_nov25/logs/nlp_processing.log

# Check if process is running
ps aux | grep nlp_processing
```

### Step 7: Download Results (from local machine)

```bash
scp -P 2111 frede@212.27.13.34:~/NAMO_nov25/data/nlp_enriched/* data/nlp_enriched/
```

## Troubleshooting

### Issue: "Authentication failed"

**Solution**: Make sure you're using the correct password. If you have SSH keys set up, the interactive script will try those first.

### Issue: "Connection timeout"

**Solution**: Check that the server is accessible:
```bash
ping 212.27.13.34
```

### Issue: "CUDA out of memory"

**Solution**: Reduce batch size:
```bash
python3 scripts/05_run_nlp_remote_interactive.py --batch-size 2
```

### Issue: "Module not found"

**Solution**: Make sure dependencies are installed:
```bash
# On remote server
cd ~/NAMO_nov25
pip install -r requirements.txt
```

### Issue: "spaCy model not found"

**Solution**: Download the model:
```bash
# On remote server
python3 -m spacy download xx_ent_wiki_sm
```

## Expected Processing Time

- **Test set (100 articles)**: ~5-10 minutes
- **Small sample (1,000 articles)**: ~1-2 hours
- **Medium sample (10,000 articles)**: ~10-20 hours
- **Full dataset (950K articles)**: ~2-4 weeks (run in batches)

## Next Steps

After processing completes:

1. Download results to local machine
2. Load enriched data into PostgreSQL:
   ```bash
   python scripts/04_load_data_to_db.py \
       --articles data/nlp_enriched/nlp_enriched_NAMO_preprocessed_test.parquet
   ```
3. Test the backend API with enriched data
4. Update dashboard to show categories and sentiment

