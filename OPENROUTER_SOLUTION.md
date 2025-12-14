# OpenRouter Solution - Function Calling for Reliable JSON

## The Key Difference

Your working example uses **function calling** (tools) which **forces** the model to return structured JSON. This is why it works reliably!

**Current approach (not working):**
- Asking model to generate JSON in free text
- Model continues article text instead
- No guarantee of JSON format

**OpenRouter approach (working):**
- Uses `tools` parameter with function specification
- Model **must** call the function with structured arguments
- **Guaranteed JSON output** - can't fail!

## Why This Works

Function calling enforces structured output:
```python
"tools": [{
    "type": "function",
    "function": {
        "name": "analyze_article",
        "parameters": {
            "type": "object",
            "properties": {
                "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]},
                "categories": {"type": "array", "items": {"type": "string", "enum": NEWS_CATEGORIES}},
                ...
            }
        }
    }
}],
"tool_choice": {"type": "function", "function": {"name": "analyze_article"}}
```

The model **cannot** continue article text - it must call the function with valid JSON!

## How to Use

### 1. Get OpenRouter API Key

Sign up at https://openrouter.ai and get an API key.

### 2. Set API Key

```bash
export OPENROUTER_API_KEY="your-api-key-here"
```

Or create `api_key.txt` file with your key.

### 3. Run with OpenRouter

```bash
# On server or locally
cd ~/NAMO_nov25
source venv/bin/activate

# Install requests if needed
pip install requests

# Run with OpenRouter (much more reliable!)
python3 scripts/25_nlp_with_openrouter.py \
  --input data/processed/test_100.parquet \
  --output data/nlp_enriched/test_100_openrouter.parquet \
  --model openai/gpt-4o-mini  # or anthropic/claude-3-haiku, etc.
```

### 4. Available Models

OpenRouter supports many models:
- `openai/gpt-4o-mini` - Fast, cheap, reliable
- `openai/gpt-4o` - Best quality
- `anthropic/claude-3-haiku` - Fast, good quality
- `anthropic/claude-3-sonnet` - Better quality
- `google/gemini-pro` - Alternative option

## Cost Estimate

For ~1M articles:
- GPT-4o-mini: ~$50-100 (very affordable)
- Claude-3-haiku: ~$100-200
- GPT-4o: ~$500-1000 (best quality)

## Advantages

1. ✅ **Reliable JSON** - Function calling guarantees structure
2. ✅ **No "Other" spam** - Model follows instructions properly
3. ✅ **Works immediately** - No debugging prompt formats
4. ✅ **Multiple models** - Can switch models easily
5. ✅ **No GPU needed** - Runs via API

## Disadvantages

1. ❌ **API costs** - Pay per request
2. ❌ **Internet required** - Needs API access
3. ❌ **Rate limits** - May need to throttle requests

## Recommendation

**Use OpenRouter for now** to get reliable results, then we can optimize later:
1. Test with 100 articles using OpenRouter
2. Verify JSON output is reliable
3. Process full dataset
4. Later: Can try to optimize local models if needed

The function calling approach is **proven to work** - your example shows it!

