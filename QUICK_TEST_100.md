# Quick Test with 100 Articles

## Option 1: Run on Remote Server (Recommended)

The remote server already has all dependencies installed. Run this:

```bash
# SSH to server
ssh -p 2111 frede@212.27.13.34

# Navigate to project
cd ~/NAMO_nov25
source venv/bin/activate

# Create test dataset (100 articles)
python3 -c "
import polars as pl
df = pl.read_parquet('data/processed/NAMO_preprocessed_test.parquet')
df.head(100).write_parquet('data/processed/test_100.parquet')
print('Created test_100.parquet')
"

# Run NLP processing with debug logging
python3 scripts/02_nlp_processing.py \
  --input data/processed/test_100.parquet \
  --output data/nlp_enriched/test_100_debug.parquet \
  --batch-size 4 \
  --no-quantization 2>&1 | tee logs/nlp_debug_100.log
```

## Option 2: Install Dependencies Locally

If you want to test locally, install dependencies:

```bash
# Install PyTorch (CPU version for local testing)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install other dependencies
pip install transformers accelerate polars spacy tqdm

# Download spaCy models
python -m spacy download xx_ent_wiki_sm

# Then run the script
python3 scripts/02_nlp_processing.py \
  --input data/processed/test_100.parquet \
  --output data/nlp_enriched/test_100_debug.parquet \
  --batch-size 4 \
  --no-quantization 2>&1 | tee logs/nlp_debug_100.log
```

**Note**: Local testing will be slower (CPU only) and won't have GPU acceleration.

## What to Check in Logs

After running, check `logs/nlp_debug_100.log` for:

✅ **Success indicators**:
- Responses starting with `{`
- "LLM loaded successfully"
- "Processing batch of X articles..."

❌ **Error indicators**:
- "No JSON found in response"
- "Response didn't start with {"
- "ASSIGNED 'Other' CATEGORY" (should be rare)

## Expected Results

With the new prompt format:
- **Most responses should start with `{`** (JSON format)
- **Fewer "Other" category assignments** (<5%)
- **No text continuation errors** (model should stop after JSON)

## If Still Having Issues

If you still see text continuations:
1. Check the log file for actual prompt format
2. Verify model is loading correctly
3. Check GPU memory (if using GPU)
4. Try with even smaller batch (--batch-size 1)

