# LLM JSON Output Fix

## Problem Identified

The Qwen2.5 model was generating **text continuations** instead of JSON responses. Looking at the logs:

```
Raw LLM response: mot organiserede kriminalitet i Oslo....
Raw LLM response: ende reformer av sin regelbok...
Raw LLM response: Putinin viestintästrategian karkotuksen...
```

These responses are **fragments of article text**, not JSON objects. This indicates the model is:
1. **Continuing the article text** instead of generating a JSON analysis
2. **Not recognizing the instruction** to output JSON
3. **Not stopping** after generating the JSON object

## Root Causes

1. **Prompt Format**: Qwen2.5 sometimes ignores system messages, so instructions need to be in the user message
2. **Generation Parameters**: Temperature (0.3) was too high, causing non-deterministic output
3. **Response Parsing**: No detection for when the model continues article text instead of generating JSON
4. **Missing Stop Logic**: No mechanism to stop at the first complete JSON object

## Fixes Applied

### 1. Improved Prompt Structure
- Moved all instructions into the user message (removed separate system message)
- Made JSON format requirements more explicit
- Added explicit instruction: "Do NOT continue the article text"

### 2. Better Generation Parameters
- **Temperature**: Reduced from `0.3` to `0.1` for more deterministic JSON output
- **Max tokens**: Reduced from `300` to `200` (JSON should be shorter)
- **Top-p**: Adjusted to `0.95` for better quality

### 3. Enhanced Response Parsing
- **Detect text continuation**: If response doesn't start with `{`, find the first `{` character
- **Extract complete JSON**: Stop at first balanced JSON object (matching braces)
- **Better logging**: Log when text continuation is detected

### 4. Code Changes

```python
# Before: Simple decoding
response = self.tokenizer.decode(outputs[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True)

# After: Smart parsing with continuation detection
generated_tokens = outputs[0][inputs["input_ids"].shape[1] :]
response = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)

# Detect if model continued article text instead of generating JSON
if not response.startswith("{"):
    json_start = response.find("{")
    if json_start > 0:
        logger.debug(f"⚠️  Response didn't start with {{ - found at position {json_start}")
        response = response[json_start:]

# Stop at first complete JSON object
brace_count = 0
json_end = -1
for i, char in enumerate(response):
    if char == "{":
        brace_count += 1
    elif char == "}":
        brace_count -= 1
        if brace_count == 0:
            json_end = i + 1
            break

if json_end > 0:
    response = response[:json_end]
```

## Expected Improvements

1. **Better JSON compliance**: Lower temperature should produce more consistent JSON
2. **Text continuation detection**: Will catch and fix cases where model continues article text
3. **Complete JSON extraction**: Will stop at first complete JSON object, preventing trailing text

## Testing

To test the fix, run NLP processing again:

```bash
python scripts/05_run_nlp_remote_interactive.py \
  --input data/processed/NAMO_preprocessed_test.parquet \
  --batch-size 4
```

**Monitor for**:
- ✅ Responses starting with `{`
- ✅ Complete JSON objects being extracted
- ⚠️  Warnings about text continuation (should be rare now)
- ⚠️  "Other" category assignments (should be <1%)

## If Issues Persist

If the model still generates text continuations:

1. **Check quantization**: Ensure `--no-quantization` flag is used (quantization can degrade JSON output)
2. **Verify model**: Check that Qwen2.5-7B-Instruct is loaded correctly
3. **GPU memory**: Ensure enough GPU memory for full precision model
4. **Consider alternative**: May need to use a different model or add JSON schema enforcement

