# Unified Topic Modeling Option

## ✅ Added Unified Model Option

You can now run **one topic model on the entire corpus** instead of per-country models.

---

## 🎯 Why Unified vs Per-Country?

### Per-Country Models (Original)
- ✅ **Pros**: Language-specific topics, better for small datasets per country
- ❌ **Cons**: More models to manage, topics may not be comparable across countries

### Unified Model (New Option)
- ✅ **Pros**: 
  - Single model for entire corpus
  - Topics comparable across countries
  - Better for cross-country analysis
  - Simpler to manage
- ❌ **Cons**: 
  - May mix languages (but mmBERT handles this well)
  - Less language-specific nuance

---

## 🚀 Usage

### Unified Model (All Articles Together)

```bash
python scripts/17_run_topic_modeling_remote.py \
  --input data/nlp_enriched/nlp_enriched_NAMO_preprocessed_test_final.parquet \
  --output data/topic_modeled/topics_unified.parquet \
  --unified
```

### Per-Country Models (Original)

```bash
python scripts/17_run_topic_modeling_remote.py \
  --input data/nlp_enriched/nlp_enriched_NAMO_preprocessed_test_final.parquet \
  --output data/topic_modeled/topics.parquet
```

---

## 📊 What Happens

### Unified Model
- ✅ Processes all articles together (all countries)
- ✅ Uses multilingual mode (handles Danish, Swedish, Norwegian, Finnish)
- ✅ Finds topics across entire corpus
- ✅ Saves one model: `models/topic_model_unified/`
- ✅ Saves one topic info file: `data/topic_modeled/topic_info_unified.csv`

### Per-Country Models
- ✅ Processes each country separately
- ✅ Uses language-specific mode
- ✅ Finds topics per country
- ✅ Saves multiple models: `models/topic_model_{country}/`
- ✅ Saves multiple topic info files: `data/topic_modeled/topic_info_{country}.csv`

---

## 💡 Recommendation

**For your test corpus (996 articles):**
- ✅ **Use unified model** - simpler, topics comparable across countries
- ✅ mmBERT handles multilingual content well
- ✅ Easier to analyze and visualize

**For full dataset (1M articles):**
- Consider per-country if you want language-specific topics
- Or unified with sampling per country for comparison

---

**Unified option is ready!** Use `--unified` flag to run one model on entire corpus. 🚀

