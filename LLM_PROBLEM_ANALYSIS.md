# LLM Problem Analysis

## What We're Using

**Hugging Face Transformers** (NOT Ollama)
- Using `AutoModelForCausalLM` from `transformers` library
- Loading models directly from Hugging Face Hub (e.g., `mistralai/Mistral-7B-Instruct-v0.2`)
- Running inference locally on GPU

## What the Logs Mean

### Example Log Entry:
```
⚠️  No JSON found in response - got text continuation instead
Response preview: tså kunne være penge til andet, er det faktisk den tendens...
Raw LLM response: tså kunne være penge til andet, er det faktisk den tendens, der er udmærket...
Article preview: Hvornår er man gammel nok til at tage vare på sig selv? Danske kommuner...
```

### What This Indicates:

1. **"No JSON found in response"** = The model didn't generate any JSON at all
2. **"got text continuation instead"** = The model is **literally continuing the article text**
3. **"Response preview"** = Shows what the model generated (article continuation, not JSON)
4. **"Raw LLM response"** = The full response from the model (still article text)
5. **"Article preview"** = The original article that was sent to the model

### The Problem:

The model is **completing the article** instead of **analyzing it**. It's acting like an autocomplete/text generator, not a JSON analyzer.

Example:
- **Article ends with**: "...penge til andet"
- **Model continues**: "er det faktisk den tendens, der er udmærket. Det er en tendens, hvor man tager vare på folk..."

This means the model thinks its job is to **continue writing the article**, not to **analyze it and return JSON**.

## Why "Other" Category?

When the model fails to generate JSON:
1. Script tries to parse JSON → fails
2. Script tries to extract categories from text → finds nothing (it's just article continuation)
3. Script assigns "Other" as fallback → to ensure every article has at least one category

**"Other" doesn't mean the article is unclassifiable** - it means **the model failed to generate JSON**.

## Root Cause

The model is not recognizing the instruction to generate JSON. Possible reasons:

1. **Prompt format issue**: Mistral's chat template might not be working correctly
2. **Model confusion**: The model sees article text and thinks it should continue it
3. **Generation parameters**: Greedy decoding might be causing it to continue the most likely sequence (article text)

## Next Steps

We need to see what prompt is actually being sent. Enable debug logging:

```bash
export NLP_DEBUG=true
python3 scripts/02_nlp_processing.py \
  --input data/processed/test_100.parquet \
  --output test.parquet \
  --batch-size 2 \
  --no-quantization 2>&1 | grep -A 5 "Prompt ending" | head -20
```

This will show us the actual prompt format being sent to the model.

