# Category Classification Only - Simplified NLP

## Overview

This script (`scripts/26_category_classification_only.py`) performs **ONLY** category classification:
- ✅ Classifies articles into ONE primary category (from 11 categories)
- ❌ No sentiment analysis
- ❌ No NER
- ❌ No other features

## Why This Simplification?

1. **Easier for LLM**: Single task is simpler than multi-task
2. **More reliable**: Less chance of confusion/errors
3. **Faster**: Only one LLM call per article
4. **Clearer output**: Just one category per article

## Categories

1. Politics & Governance
2. Immigration & National Identity
3. Health & Medicine
4. Media & Censorship
5. International Relations & Conflict
6. Economy & Labor
7. Crime & Justice
8. Social Issues & Culture
9. Environment, Climate & Energy
10. Technology, Science & Digital Society
11. Other

## Usage

### Basic Usage

```bash
# On server with GPU
cd ~/NAMO_nov25
source venv/bin/activate

# Run category classification
python3 scripts/26_category_classification_only.py \
  --input data/processed/test_100.parquet \
  --output data/nlp_enriched/test_100_categories.parquet \
  --model mistralai/Mistral-7B-Instruct-v0.2 \
  --no-quantization
```

### Options

- `--input`: Input parquet file (required)
- `--output`: Output parquet file (optional, auto-generated if not provided)
- `--model`: Hugging Face model name (default: `mistralai/Mistral-7B-Instruct-v0.2`)
- `--device`: `cuda` or `cpu` (default: `cuda`)
- `--use-quantization`: Enable 4-bit quantization (saves GPU memory)
- `--no-quantization`: Disable quantization (default, better quality)

### Output Columns

The script adds these columns to your dataframe:
- `category`: The primary category (string)
- `category_reasoning`: Brief explanation from LLM (string)
- `category_processed_at`: Timestamp (ISO format)

## Prompt Design

The prompt is simplified to focus on ONE task:

```
You are a news article classifier. Your task is to classify the article into EXACTLY ONE category.

CATEGORIES:
1. Politics & Governance
2. Immigration & National Identity
...

INSTRUCTIONS:
1. Read the article below
2. Choose the SINGLE most relevant category
3. Respond with ONLY a JSON object: {"category": "Category Name", "reasoning": "brief explanation"}
```

## Expected Output Format

```json
{
  "category": "Politics & Governance",
  "reasoning": "Article discusses government policy and elections"
}
```

## Troubleshooting

### If model continues article text

The script includes JSON extraction logic that:
1. Finds JSON objects in response
2. Validates category is in the list
3. Falls back to "Other" if parsing fails

### If too many "Other" categories

Check the logs for:
- JSON parsing failures
- Invalid category names
- Model responses that don't follow format

Enable debug logging:
```bash
export NLP_DEBUG=true
python3 scripts/26_category_classification_only.py ...
```

## Next Steps

After category classification works reliably:
1. Test on 100 articles
2. Check category distribution
3. Review "Other" category assignments
4. Process full dataset if results look good

