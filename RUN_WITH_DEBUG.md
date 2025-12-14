# Run with Full Debug Logging

## The Problem

The model is still continuing article text instead of generating JSON. We need to see:
1. What prompt is actually being sent
2. What the model is actually responding with

## Enable Debug Logging

Run with debug logging enabled:

```bash
# On the server
cd ~/NAMO_nov25
source venv/bin/activate

# Enable debug logging
export NLP_DEBUG=true

# Run with full debug output
python3 scripts/02_nlp_processing.py \
  --input data/processed/test_100.parquet \
  --output data/nlp_enriched/test_100_mistral.parquet \
  --batch-size 2 \
  --no-quantization 2>&1 | tee logs/nlp_debug_full.log
```

## What Changed

1. **Mistral now uses tokenizer's chat template** - More reliable than manual formatting
2. **Enhanced STOP instruction** - "STOP. The article ends here..."
3. **Debug logging** - Set `NLP_DEBUG=true` to see full prompts and responses

## Check Debug Output

```bash
# See prompt endings (should end with JSON instruction)
grep "Prompt ending" logs/nlp_debug_full.log | head -3

# See raw LLM responses
grep "🤖 Raw LLM response" logs/nlp_debug_full.log | head -5

# See what's being analyzed
grep "📄 Analyzing article" logs/nlp_debug_full.log | head -5
```

## If Still Failing

If the model still continues text, share:
1. One "Prompt ending" log entry (last 400 chars)
2. One "Raw LLM response" that failed
3. The model name being used

This will help identify if it's:
- Prompt format issue
- Model behavior issue  
- Tokenizer chat template issue

