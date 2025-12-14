# Available Nordic Models on Hugging Face

## Verified Models (Available Now)

### 1. GPT-SW3 Models (Swedish/Nordic Focus)

**Available models:**
- `AI-Sweden-Models/gpt-sw3-126m-instruct` - Smallest (126M)
- `AI-Sweden-Models/gpt-sw3-400m-instruct` - Small (400M)
- `AI-Sweden-Models/gpt-sw3-1.3b-instruct` - Medium (1.3B)
- `AI-Sweden-Models/gpt-sw3-6.7b-instruct` - Large (6.7B) ⭐ **Recommended**
- `AI-Sweden-Models/gpt-sw3-20b-instruct` - Very Large (20B)
- `AI-Sweden-Models/gpt-sw3-40b-instruct` - Largest (40B)

**Best for**: Swedish, Norwegian, Danish (Scandinavian languages)
**GPU Memory**: 6.7B needs ~14GB, 20B needs ~40GB

**Usage:**
```bash
python3 scripts/26_category_classification_only.py \
  --input data/processed/test_100.parquet \
  --output data/nlp_enriched/test_100_categories.parquet \
  --model AI-Sweden-Models/gpt-sw3-6.7b-instruct \
  --no-quantization
```

### 2. Llama-3-8B-Nordic

**Model**: `AI-Sweden-Models/Llama-3-8B-Nordic`

**Best for**: All Nordic languages (Swedish, Danish, Norwegian, Finnish)
**GPU Memory**: ~16GB
**Trained on**: 227B token Nordic corpus

**Usage:**
```bash
python3 scripts/26_category_classification_only.py \
  --input data/processed/test_100.parquet \
  --output data/nlp_enriched/test_100_categories.parquet \
  --model AI-Sweden-Models/Llama-3-8B-Nordic \
  --no-quantization
```

### 3. SnakModel (Danish-specific)

**Model**: `SnakModel/SnakModel-7B`

**Best for**: Danish (excellent), Swedish/Norwegian (good), Finnish (limited)
**GPU Memory**: ~14GB

**Usage:**
```bash
python3 scripts/26_category_classification_only.py \
  --input data/processed/test_100.parquet \
  --output data/nlp_enriched/test_100_categories.parquet \
  --model SnakModel/SnakModel-7B \
  --no-quantization
```

## Viking Models Status

**Note**: The Viking models (`lumiopen/Viking-7B-Instruct`) mentioned in research may not be publicly available on Hugging Face yet, or may require special access. 

**Alternative**: Use GPT-SW3 or Llama-3-Nordic which are verified available and optimized for Nordic languages.

## Recommendation

For your use case (Danish, Swedish, Norwegian, Finnish):

1. **Try first**: `AI-Sweden-Models/gpt-sw3-6.7b-instruct`
   - Excellent for Scandinavian languages
   - Good size/quality balance
   - Verified available

2. **Alternative**: `AI-Sweden-Models/Llama-3-8B-Nordic`
   - Good for all Nordic languages including Finnish
   - Slightly larger but better Finnish support

3. **If mostly Danish**: `SnakModel/SnakModel-7B`
   - Best Danish performance

## Testing

Test different models to see which works best for your specific dataset:

```bash
# Test GPT-SW3
python3 scripts/26_category_classification_only.py \
  --input data/processed/test_100.parquet \
  --output data/nlp_enriched/test_100_gptsw3.parquet \
  --model AI-Sweden-Models/gpt-sw3-6.7b-instruct \
  --no-quantization

# Test Llama-3-Nordic
python3 scripts/26_category_classification_only.py \
  --input data/processed/test_100.parquet \
  --output data/nlp_enriched/test_100_llama3nordic.parquet \
  --model AI-Sweden-Models/Llama-3-8B-Nordic \
  --no-quantization
```

Then compare the category distributions to see which model gives better results!

