# EuroLLM-9B Model Information

## Model Details

**Model**: `utter-project/EuroLLM-9B`
**Hugging Face**: https://huggingface.co/utter-project/EuroLLM-9B

## Usage

```bash
python3 scripts/26_category_classification_only.py \
  --input data/processed/test_100.parquet \
  --output data/nlp_enriched/test_100_categories.parquet \
  --model utter-project/EuroLLM-9B \
  --no-quantization
```

## Advantages

- ✅ **9B parameters** - Good balance between size and quality
- ✅ **35 languages supported** - All 24 EU official languages + Norwegian, Finnish, Swedish
- ✅ **4 trillion tokens** - Extensive training data
- ✅ **Open source** - Available on Hugging Face
- ✅ **No token required** - Publicly accessible
- ✅ **EU-funded** - Developed by consortium including Unbabel, IST, University of Edinburgh
- ✅ **Strong benchmarks** - Outperforms Mistral-7B in European language tasks

## Nordic-Specific Variant

There's also a **Nordic-focused variant**:
- `mpasila/EuroLLM-Nordic-Instruct-9B` - Fine-tuned specifically for Nordic languages
- Enhanced performance for Danish, Swedish, Norwegian, Finnish

**Usage:**
```bash
python3 scripts/26_category_classification_only.py \
  --input data/processed/test_100.parquet \
  --output data/nlp_enriched/test_100_categories.parquet \
  --model mpasila/EuroLLM-Nordic-Instruct-9B \
  --no-quantization
```

## Comparison with Other Models

| Model | Size | Nordic Support | Token Required | GPU Memory |
|-------|------|----------------|----------------|------------|
| **EuroLLM-9B** | 9B | ✅✅ All EU languages (Danish, Swedish, Norwegian, Finnish) | ❌ No | ~18GB |
| **EuroLLM-Nordic-Instruct-9B** | 9B | ✅✅✅ Nordic-specific fine-tuning | ❌ No | ~18GB |
| **Viking-7B** | 7.5B | ✅✅✅ Nordic-specific | ✅ Yes | ~15GB |
| **GPT-SW3-6.7B** | 6.7B | ✅✅ Scandinavian | ❌ No | ~14GB |
| **Llama-3-8B-Nordic** | 8B | ✅✅ All Nordic | ❌ No | ~16GB |
| **Mistral-7B** | 7B | ✅ General multilingual | ❌ No | ~14GB |

## Recommendation

**EuroLLM-9B** is an excellent option because:
- ✅ Supports all your Nordic languages (Danish, Swedish, Norwegian, Finnish)
- ✅ No token required (easier to use)
- ✅ Strong performance in European language benchmarks
- ✅ 9B parameters (good quality)
- ✅ EU-funded, well-documented

**Best choice for Nordic languages:**
1. **`mpasila/EuroLLM-Nordic-Instruct-9B`** - Nordic-specific variant (recommended!)
2. **`utter-project/EuroLLM-9B`** - General EuroLLM (also very good)
3. **Viking-7B** - Nordic-specific but requires token
4. **GPT-SW3-6.7B** - Excellent for Scandinavian languages

**If you have ~18GB GPU memory**, EuroLLM-Nordic-Instruct-9B is probably your best bet!

## Testing

You can test EuroLLM-9B and compare with other models:

```bash
# Test EuroLLM-Nordic-Instruct-9B (Nordic-specific variant - RECOMMENDED)
python3 scripts/26_category_classification_only.py \
  --input data/processed/test_100.parquet \
  --output data/nlp_enriched/test_100_eurollm_nordic.parquet \
  --model mpasila/EuroLLM-Nordic-Instruct-9B \
  --no-quantization

# Test EuroLLM-9B (general European)
python3 scripts/26_category_classification_only.py \
  --input data/processed/test_100.parquet \
  --output data/nlp_enriched/test_100_eurollm9b.parquet \
  --model utter-project/EuroLLM-9B \
  --no-quantization

# Compare with Viking-7B
python3 scripts/26_category_classification_only.py \
  --input data/processed/test_100.parquet \
  --output data/nlp_enriched/test_100_viking7b.parquet \
  --model LumiOpen/Viking-7B \
  --hf-token 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 \
  --no-quantization

# Compare with GPT-SW3
python3 scripts/26_category_classification_only.py \
  --input data/processed/test_100.parquet \
  --output data/nlp_enriched/test_100_gptsw3.parquet \
  --model AI-Sweden-Models/gpt-sw3-6.7b-instruct \
  --no-quantization
```

Then compare the category distributions to see which model performs best for your specific dataset!

