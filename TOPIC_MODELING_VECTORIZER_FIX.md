# Topic Modeling Vectorizer Fix

## 🔍 Problem

**Error**: `ValueError: max_df corresponds to < documents than min_df`

This occurs when:
- A topic has very few documents (e.g., Finland with 109 documents total, some topics may have < 5 documents)
- The vectorizer's `max_df=0.95` and `min_df=2` become incompatible
- Example: If a topic has 1 document, `max_df * 1 = 0.95` → 0 documents, but `min_df=2` requires 2

---

## ✅ Fixes Applied

### 1. **More Lenient Default Parameters**
```python
# Before:
min_df=2, max_df=0.95

# After:
min_df=1, max_df=0.99
```

### 2. **Error Handling with Fallback**
- Catches `ValueError` for vectorizer incompatibility
- Automatically recreates BERTopic with very lenient parameters:
  - `min_df=1`
  - `max_df=1.0` (allow all words)
  - `ngram_range=(1, 1)` (only unigrams)

### 3. **Small Document Set Check**
- If < 5 documents, assigns all to topic -1 (noise)
- Prevents errors with very small datasets

---

## 🚀 Run Again

The script will now handle small document sets gracefully:

```bash
python scripts/17_run_topic_modeling_remote.py \
  --input data/nlp_enriched/nlp_enriched_NAMO_preprocessed_test_final.parquet \
  --output data/topic_modeled/topics.parquet
```

---

## 📋 What Happens Now

1. ✅ **Default**: Uses `min_df=1, max_df=0.99` (more lenient)
2. ✅ **If error occurs**: Automatically falls back to `min_df=1, max_df=1.0`
3. ✅ **If < 5 documents**: Assigns to topic -1 (noise) instead of failing

---

**All fixes applied!** The script should now handle Finland's 109 documents without errors. 🚀

