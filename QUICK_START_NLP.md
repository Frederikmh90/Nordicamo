# Quick Start: Running NLP Processing on Remote GPU Server

## Prerequisites

1. Install paramiko for SSH:
```bash
pip install paramiko
```

2. Have your SSH password ready (you'll be prompted)

## Quick Start

Run the interactive script that handles everything:

```bash
python3 scripts/05_run_nlp_remote_interactive.py \
    --input data/processed/NAMO_preprocessed_test.parquet \
    --batch-size 4
```

**What happens:**
1. You'll be prompted for SSH password
2. Script connects to remote server (212.27.13.34:2111)
3. Sets up directory structure
4. Syncs scripts and data files
5. Installs Python dependencies
6. Runs NLP processing with Qwen2.5
7. Shows progress in real-time

## Options

```bash
# Use different input file
python3 scripts/05_run_nlp_remote_interactive.py \
    --input data/processed/NAMO_preprocessed_full.parquet \
    --batch-size 4

# Smaller batch size if GPU memory is limited
python3 scripts/05_run_nlp_remote_interactive.py \
    --input data/processed/NAMO_preprocessed_test.parquet \
    --batch-size 2

# Only set up environment (don't run processing)
python3 scripts/05_run_nlp_remote_interactive.py \
    --input data/processed/NAMO_preprocessed_test.parquet \
    --setup-only
```

## Monitor Progress

In another terminal, you can monitor the log file:

```bash
ssh -p 2111 frede@212.27.13.34 'tail -f ~/NAMO_nov25/logs/nlp_processing.log'
```

## Download Results

When processing completes, download results:

```bash
scp -P 2111 frede@212.27.13.34:~/NAMO_nov25/data/nlp_enriched/* data/nlp_enriched/
```

## Troubleshooting

**"Authentication failed"**: Make sure password is correct

**"Connection timeout"**: Check server is accessible

**"CUDA out of memory"**: Reduce batch size (try --batch-size 2)

See `REMOTE_NLP_SETUP.md` for detailed troubleshooting.

