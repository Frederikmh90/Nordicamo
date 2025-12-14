# SSH Login Instructions

## Connect to Server

```bash
ssh -p 2111 frede@212.27.13.34
```

You'll be prompted for your password.

## After Login

Once connected, you'll be in your home directory. Navigate to the project:

```bash
cd ~/NAMO_nov25
source venv/bin/activate
```

## Run the Command

```bash
# Enable debug logging
export NLP_DEBUG=true

# Create logs directory if it doesn't exist
mkdir -p logs

# Run with debug logging
python3 scripts/26_category_classification_only.py \
  --input data/processed/test_100.parquet \
  --output data/nlp_enriched/test_100_categories.parquet \
  --model LumiOpen/Viking-7B \
  --hf-token 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 \
  --no-quantization 2>&1 | tee logs/viking_debug.log
```

## Check Logs

While it's running, you can check the log file in another terminal:

```bash
# In another terminal, SSH in again
ssh -p 2111 frede@212.27.13.34
cd ~/NAMO_nov25

# Watch the log file
tail -f logs/viking_debug.log
```

## Quick Copy-Paste Sequence

```bash
# 1. Connect
ssh -p 2111 frede@212.27.13.34

# 2. Navigate and activate
cd ~/NAMO_nov25
source venv/bin/activate

# 3. Create logs directory
mkdir -p logs

# 4. Run with debug
export NLP_DEBUG=true
python3 scripts/26_category_classification_only.py \
  --input data/processed/test_100.parquet \
  --output data/nlp_enriched/test_100_categories.parquet \
  --model LumiOpen/Viking-7B \
  --hf-token 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 \
  --no-quantization 2>&1 | tee logs/viking_debug.log
```

## Troubleshooting

If you get "Permission denied":
- Make sure you're using the correct password
- Check that SSH is allowed on port 2111

If the venv doesn't activate:
- Check if it exists: `ls -la ~/NAMO_nov25/venv`
- If missing, you may need to recreate it

If the script isn't found:
- Check you're in the right directory: `pwd`
- List scripts: `ls scripts/26*.py`

