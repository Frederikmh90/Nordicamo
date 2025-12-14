# Finnish NER Model Update

## Better Model Found! 🎉

**New Model**: `Kansallisarkisto/finbert-ner`
- **Source**: Finnish National Archives (Kansallisarkisto)
- **Type**: Finnish-specific NER model
- **Why Better**: Specifically trained for Finnish named entity recognition, not a generic multilingual model

## Updated Code

The script has been updated to use `Kansallisarkisto/finbert-ner` as the primary Finnish model, with `xlm-roberta-large-finetuned-conll03-english` as fallback.

## Test the New Model

```bash
# On VM
cd ~/NAMO_nov25
source venv/bin/activate

python3 scripts/34_ner_country_specific.py \
  --input data/processed/test_ner_100.parquet \
  --output data/nlp_enriched/test_ner_100_results_finbert.parquet \
  --device cuda \
  --score-threshold 0.5
```

## Expected Improvements

- **Better accuracy**: Finnish-specific model should extract entities more accurately
- **Better coverage**: Should find more entities in Finnish text
- **Faster**: No need to download large multilingual model if Finnish model works

## Monitor Results

```bash
# Check Finnish entity extraction
tail -f ~/NAMO_nov25/logs/ner_*.log | grep -E "(Finnish|finland|🇫🇮|finbert)"
```

Look for:
- "🇫🇮 Finnish article: extracted X entities" - should show more entities now
- Model loading messages showing "Kansallisarkisto/finbert-ner"
- Summary at end showing Finnish entity counts

## Comparison

| Model | Type | Expected Performance |
|-------|------|---------------------|
| `Kansallisarkisto/finbert-ner` | Finnish-specific | ✅ Best for Finnish |
| `xlm-roberta-large-finetuned-conll03-english` | Multilingual | ⚠️ Works but not optimized |
| `TurkuNLP/bert-base-finnish-cased-v1` | Finnish BERT (not NER) | ❌ Doesn't work for NER |




