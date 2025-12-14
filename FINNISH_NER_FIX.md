# Finnish NER Fix

## Problem
Finnish articles returned 0 entities. The model `TurkuNLP/bert-base-finnish-cased-v1` is a BERT language model, not an NER model.

## Solution
Updated to use `xlm-roberta-large-finetuned-conll03-english`, a multilingual NER model that works well for Finnish.

## Changes Made

1. **Updated Finnish model**: Changed from `TurkuNLP/bert-base-finnish-cased-v1` to `xlm-roberta-large-finetuned-conll03-english`
2. **Added Finnish-specific fallback**: New `_load_finnish_fallback_model()` method
3. **Enhanced logging**: Added specific logging for Finnish articles to debug issues
4. **Better error handling**: Catches errors during NER pipeline execution

## Run Again

### Option 1: Test with 100 articles (recommended)
```bash
# On VM
cd ~/NAMO_nov25
source venv/bin/activate

python3 scripts/34_ner_country_specific.py \
  --input data/processed/test_ner_100.parquet \
  --output data/nlp_enriched/test_ner_100_results_v2.parquet \
  --device cuda \
  --score-threshold 0.5
```

### Option 2: Run on full dataset
```bash
# On VM
cd ~/NAMO_nov25
source venv/bin/activate

python3 scripts/34_ner_country_specific.py \
  --input data/processed/sample_1000.parquet \
  --output data/nlp_enriched/sample_1000_ner_v2.parquet \
  --device cuda \
  --score-threshold 0.5
```

## Monitor Progress

```bash
# In another terminal
ssh -p 2111 frede@212.27.13.34
tail -f ~/NAMO_nov25/logs/ner_*.log | grep -E "(Finnish|finland|🇫🇮|ERROR)"
```

## Expected Results

- Finnish articles should now extract entities
- Logs will show "🇫🇮 Finnish article: extracted X entities"
- If still 0 entities, check logs for warnings/errors

## Alternative Models (if needed)

If the current model still doesn't work well for Finnish, we can try:
- `dbmdz/bert-large-cased-finetuned-conll03-english` (English-focused but multilingual)
- `saattrupdan/nbailab-base-ner-scandi` (Scandinavian, might work for Finnish)

