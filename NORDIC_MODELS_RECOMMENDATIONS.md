# Nordic Language Model Recommendations

## Best Models for Danish, Swedish, Norwegian, and Finnish

Based on research, here are the best models for your Nordic news classification task:

## 🏆 Top Recommendation: Viking Models

**Model**: `lumiopen/Viking-7B-Instruct` or `lumiopen/Viking-13B-Instruct`

**Why it's best for your task:**
- ✅ **Specifically designed for Nordic languages**: Danish, Swedish, Norwegian, Finnish, Icelandic
- ✅ **Trained on 2 trillion tokens** across these languages
- ✅ **Open source** (Apache 2.0 License)
- ✅ **Multiple sizes available**: 7B, 13B, 33B parameters
- ✅ **Developed by**: Silo AI + University of Turku's TurkuNLP group

**Hugging Face:**
- `lumiopen/Viking-7B-Instruct` (7.5B parameters) - **Recommended for your GPU**
- `lumiopen/Viking-13B-Instruct` (13B parameters) - Better quality, needs more GPU memory
- `lumiopen/Viking-33B-Instruct` (33B parameters) - Best quality, needs very large GPU

**Usage:**
```bash
python3 scripts/26_category_classification_only.py \
  --input data/processed/test_100.parquet \
  --output data/nlp_enriched/test_100_categories.parquet \
  --model lumiopen/Viking-7B-Instruct \
  --no-quantization
```

## Alternative Options

### 2. GPT-SW3 (Swedish-focused, but supports other Nordic languages)

**Model**: `AI-Sweden-Models/gpt-sw3-126m-instruct` up to `AI-Sweden-Models/gpt-sw3-40b-instruct`

**Pros:**
- ✅ Excellent for Swedish
- ✅ Good for Norwegian and Danish (Scandinavian languages)
- ❌ Less optimized for Finnish (different language family)

**Best for**: If most articles are Swedish/Norwegian/Danish

### 3. Llama 3 8B Nordic

**Model**: `AI-Sweden-Models/Llama-3-8B-Nordic`

**Pros:**
- ✅ Fine-tuned specifically for Nordic languages
- ✅ Trained on 227B token Nordic corpus
- ✅ Good balance of size/quality (8B parameters)
- ✅ Supports context up to 8192 tokens

**Hugging Face**: `AI-Sweden-Models/Llama-3-8B-Nordic`

### 4. SnakModel (Danish-specific)

**Model**: `SnakModel/SnakModel-7B`

**Pros:**
- ✅ Excellent for Danish
- ✅ Based on Llama2-7B
- ❌ Less optimized for other Nordic languages

**Best for**: If most articles are Danish

### 5. Poro (Finnish-specific)

**Model**: `TurkuNLP/Poro-34B` (or smaller variants)

**Pros:**
- ✅ Best for Finnish
- ✅ 34B parameters (high quality)
- ❌ Less optimized for other Nordic languages
- ❌ Very large (needs big GPU)

**Best for**: If most articles are Finnish

## Comparison Table

| Model | Size | Danish | Swedish | Norwegian | Finnish | GPU Memory |
|-------|------|--------|---------|-----------|---------|------------|
| **Viking-7B** | 7.5B | ✅✅✅ | ✅✅✅ | ✅✅✅ | ✅✅✅ | ~15GB |
| **Viking-13B** | 13B | ✅✅✅ | ✅✅✅ | ✅✅✅ | ✅✅✅ | ~26GB |
| GPT-SW3-7B | 7B | ✅✅ | ✅✅✅ | ✅✅ | ✅ | ~14GB |
| Llama-3-8B-Nordic | 8B | ✅✅ | ✅✅ | ✅✅ | ✅✅ | ~16GB |
| SnakModel-7B | 7B | ✅✅✅ | ✅ | ✅ | ❌ | ~14GB |
| Poro-34B | 34B | ❌ | ❌ | ❌ | ✅✅✅ | ~68GB |

**Legend**: ✅✅✅ Excellent | ✅✅ Good | ✅ Acceptable | ❌ Not optimized

## Recommendation for Your Use Case

**For mixed Nordic languages (Danish, Swedish, Norwegian, Finnish):**

1. **Start with**: `lumiopen/Viking-7B-Instruct`
   - Best overall support for all your languages
   - Fits on most GPUs (~15GB)
   - Specifically designed for Nordic languages

2. **If you have more GPU memory**: `lumiopen/Viking-13B-Instruct`
   - Better quality
   - Still supports all languages well

3. **If most articles are Swedish/Norwegian/Danish**: `AI-Sweden-Models/gpt-sw3-7b-instruct`
   - Excellent for Scandinavian languages
   - Smaller model, faster inference

## Testing Different Models

You can easily test different models by changing the `--model` parameter:

```bash
# Test Viking-7B
python3 scripts/26_category_classification_only.py \
  --input data/processed/test_100.parquet \
  --output data/nlp_enriched/test_100_viking7b.parquet \
  --model lumiopen/Viking-7B-Instruct \
  --no-quantization

# Test GPT-SW3
python3 scripts/26_category_classification_only.py \
  --input data/processed/test_100.parquet \
  --output data/nlp_enriched/test_100_gptsw3.parquet \
  --model AI-Sweden-Models/gpt-sw3-7b-instruct \
  --no-quantization

# Test Llama-3-Nordic
python3 scripts/26_category_classification_only.py \
  --input data/processed/test_100.parquet \
  --output data/nlp_enriched/test_100_llama3nordic.parquet \
  --model AI-Sweden-Models/Llama-3-8B-Nordic \
  --no-quantization
```

Then compare the results to see which gives the best category classifications for your specific dataset!

## Notes

- **Viking models** are the most balanced choice for multi-Nordic language support
- **Mistral** (current default) is good for general multilingual tasks but not specifically optimized for Nordic languages
- **Qwen** is also general-purpose multilingual, not Nordic-specific

## References

- Viking Models: https://huggingface.co/lumiopen/Viking-7B-Instruct
- GPT-SW3: https://huggingface.co/AI-Sweden-Models
- Llama-3-Nordic: https://huggingface.co/AI-Sweden-Models/Llama-3-8B-Nordic

