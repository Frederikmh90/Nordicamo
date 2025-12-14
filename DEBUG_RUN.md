# Debug Run Instructions

## Data Check ✅
- All 100 articles have content
- Average content length: 1815 chars
- No empty content articles

## Enhanced Debugging Added

The script now logs:
1. **Article text length** before truncation
2. **Truncated text length** after processing
3. **Prompt format** being used (Mistral/Qwen/Other)
4. **Raw LLM response** (first 300 chars)

## Run with Enhanced Logging

```bash
# On the server
cd ~/NAMO_nov25
source venv/bin/activate

# Run with INFO level logging (shows article analysis)
python3 scripts/02_nlp_processing.py \
  --input data/processed/test_100.parquet \
  --output data/nlp_enriched/test_100_mistral.parquet \
  --batch-size 4 \
  --no-quantization 2>&1 | tee logs/nlp_debug_mistral.log
```

## Check Logs

```bash
# See what articles are being analyzed
grep "📄 Analyzing article" logs/nlp_debug_mistral.log | head -10

# See prompt format being used
grep "🔧 Using" logs/nlp_debug_mistral.log | head -5

# See raw LLM responses
grep "🤖 Raw LLM response" logs/nlp_debug_mistral.log | head -10

# Check for errors
grep -E "(ERROR|No JSON|text continuation)" logs/nlp_debug_mistral.log | head -20
```

## What to Look For

1. **Prompt format**: Should show "Using Mistral format" 
2. **Article length**: Should be ~1800 chars before truncation
3. **Raw responses**: Check if they start with `{` or continue article text
4. **Prompt preview**: Last 300 chars should show the article ending and JSON instruction

## If Still Failing

If responses still continue article text:
1. Check the "Prompt preview" in logs - does it end with JSON instruction?
2. Check "Raw LLM response" - does it start with `{`?
3. Share a sample log entry for one failing article

