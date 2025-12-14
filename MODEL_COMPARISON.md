# Model Comparison for Scandinavian Languages

## Problem

Qwen2.5-7B-Instruct is continuing article text instead of generating JSON, despite prompt improvements.

## Alternative Models to Test

### 1. **Mistral-7B-Instruct-v0.2** (Recommended First Test)
- **Model**: `mistralai/Mistral-7B-Instruct-v0.2`
- **Pros**: 
  - Excellent instruction following
  - Good JSON generation
  - Strong multilingual support (including Scandinavian)
  - Better at stopping generation
- **Cons**: 
  - Slightly larger than Qwen
  - May need more GPU memory
- **Prompt Format**: Uses `[INST]` tags

### 2. **Mistral-7B-Instruct-v0.3**
- **Model**: `mistralai/Mistral-7B-Instruct-v0.3`
- **Pros**: 
  - Latest version with improvements
  - Even better instruction following
- **Cons**: 
  - Newer, less tested

### 3. **Llama-3-8B-Instruct**
- **Model**: `meta-llama/Llama-3-8B-Instruct`
- **Pros**: 
  - Excellent instruction following
  - Good multilingual support
  - Strong JSON generation
- **Cons**: 
  - Requires Hugging Face authentication
  - Larger model

### 4. **Mixtral-8x7B-Instruct**
- **Model**: `mistralai/Mixtral-8x7B-Instruct-v0.1`
- **Pros**: 
  - Best quality
  - Excellent multilingual
- **Cons**: 
  - Much larger (requires more GPU memory)
  - Slower inference

## Testing Strategy

1. **Start with Mistral-7B-Instruct-v0.2** (default now)
2. Test with 100 articles
3. Compare JSON generation quality
4. If successful, test with full dataset

## How to Test Different Models

```bash
# Test Mistral (default)
python3 scripts/02_nlp_processing.py \
  --input data/processed/test_100.parquet \
  --output data/nlp_enriched/test_100_mistral.parquet \
  --batch-size 4 \
  --no-quantization \
  --model mistralai/Mistral-7B-Instruct-v0.2

# Test Qwen (original)
python3 scripts/02_nlp_processing.py \
  --input data/processed/test_100.parquet \
  --output data/nlp_enriched/test_100_qwen.parquet \
  --batch-size 4 \
  --no-quantization \
  --model Qwen/Qwen2.5-7B-Instruct

# Test Llama-3 (if available)
python3 scripts/02_nlp_processing.py \
  --input data/processed/test_100.parquet \
  --output data/nlp_enriched/test_100_llama.parquet \
  --batch-size 4 \
  --no-quantization \
  --model meta-llama/Llama-3-8B-Instruct
```

## Expected Results

If it's a **model issue**:
- Mistral should generate proper JSON
- Fewer text continuation errors
- Better category classification

If it's a **prompt issue**:
- All models will have similar problems
- Need to refine prompt further

## Next Steps

1. Test Mistral with 100 articles
2. Compare results with Qwen
3. If Mistral works better, switch to Mistral
4. If both fail, refine prompt further

