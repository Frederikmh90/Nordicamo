# Using Viking Model with Hugging Face Token

## Setup

The Viking model (`LumiOpen/Viking-7B`) requires authentication via Hugging Face token.

## Usage

### Option 1: Pass token as command-line argument

```bash
python3 scripts/26_category_classification_only.py \
  --input data/processed/test_100.parquet \
  --output data/nlp_enriched/test_100_categories.parquet \
  --model LumiOpen/Viking-7B \
  --hf-token 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 \
  --no-quantization
```

### Option 2: Set environment variable

```bash
export HF_TOKEN="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"

python3 scripts/26_category_classification_only.py \
  --input data/processed/test_100.parquet \
  --output data/nlp_enriched/test_100_categories.parquet \
  --model lumiopen/Viking-7B-Instruct \
  --no-quantization
```

### Option 3: Login via Hugging Face CLI

```bash
huggingface-cli login
# Enter token when prompted

python3 scripts/26_category_classification_only.py \
  --input data/processed/test_100.parquet \
  --output data/nlp_enriched/test_100_categories.parquet \
  --model lumiopen/Viking-7B-Instruct \
  --no-quantization
```

## Why Viking Model?

- ✅ Specifically designed for Nordic languages (Danish, Swedish, Norwegian, Finnish)
- ✅ Trained on 2 trillion tokens across Nordic languages
- ✅ Open source (Apache 2.0 License)
- ✅ Optimized for Nordic text understanding

## Alternative Models (No Token Required)

If you prefer not to use a token, try these Nordic models:

```bash
# GPT-SW3 (Swedish/Norwegian/Danish focus)
python3 scripts/26_category_classification_only.py \
  --input data/processed/test_100.parquet \
  --output data/nlp_enriched/test_100_categories.parquet \
  --model AI-Sweden-Models/gpt-sw3-6.7b-instruct \
  --no-quantization

# Llama-3-Nordic (All Nordic languages including Finnish)
python3 scripts/26_category_classification_only.py \
  --input data/processed/test_100.parquet \
  --output data/nlp_enriched/test_100_categories.parquet \
  --model AI-Sweden-Models/Llama-3-8B-Nordic \
  --no-quantization
```

