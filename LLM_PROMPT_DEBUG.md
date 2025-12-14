# LLM Prompt Debugging - Critical Fix

## Problem

The model is **continuing article text** instead of generating JSON:

```
Raw LLM response: iv med 25.000+ artikler 24/7...
Raw LLM response: i Centralafrikanska republiken...
```

These are **fragments of article text**, not JSON responses.

## Root Cause Analysis

1. **Chat Template Issue**: Qwen2.5's `apply_chat_template` might be formatting the prompt in a way that makes the model think it should continue the article
2. **Prompt Structure**: The prompt might not have a clear enough separator between article and instruction
3. **Generation Mode**: Using sampling (`do_sample=True`) might be causing non-deterministic continuation

## Fix Applied

### 1. **Manual Prompt Formatting**

Instead of relying on `apply_chat_template`, we now format the prompt manually using Qwen's special tokens:

```python
prompt = f"""<|im_start|>user
[Instructions]
Article: {text}
STOP. Do not continue the article. Now respond with JSON only:<|im_end|>
<|im_start|>assistant
{{"""
```

This ensures:
- Clear separation between article and instruction
- Explicit "STOP" instruction
- Starts JSON response with `{` already in prompt

### 2. **Greedy Decoding**

Changed from sampling to greedy decoding:

```python
outputs = self.model.generate(
    **inputs,
    max_new_tokens=200,
    do_sample=False,  # Greedy - most deterministic
    repetition_penalty=1.1,
)
```

Greedy decoding (`do_sample=False`) is more deterministic and should follow instructions better.

### 3. **Better Error Detection**

Enhanced logging to show:
- Full response when JSON is missing
- Prompt preview for debugging
- Clear error messages

## Testing

Run on a small dataset first:

```bash
# On the server
cd ~/NAMO_nov25
source venv/bin/activate

# Test with 100 articles
python3 scripts/02_nlp_processing.py \
  --input data/processed/NAMO_preprocessed_test.parquet \
  --output data/nlp_enriched/test_100.parquet \
  --batch-size 4 \
  --no-quantization
```

Then check the logs for:
- ✅ Responses starting with `{`
- ❌ Any "No JSON found" errors
- ⚠️  "Response didn't start with {" warnings

## If Still Failing

If the model still continues article text:

1. **Check the actual prompt**: Add logging to see what's being sent
2. **Try different model**: Qwen2.5-7B-Instruct might need different formatting
3. **Use structured output**: Consider using a library that enforces JSON schema
4. **Post-processing**: Add a retry mechanism with different prompts

## Next Steps

1. Test with 100 articles
2. Review logs for JSON compliance
3. If successful, run full dataset
4. If still failing, try alternative prompt formats

