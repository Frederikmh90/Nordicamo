# Entity Extraction & GPU Optimization

## 🔍 How Entities are Extracted

### Model: spaCy Multilingual (`xx_ent_wiki_sm`)

**Location in code**: `scripts/02_nlp_processing.py`, lines 702-740

```python
def extract_entities(self, text: str) -> Dict:
    """Extract named entities using spaCy."""
    doc = self.nlp_models["multi"](text_truncated)
    
    for ent in doc.ents:
        if ent.label_ == "PER" or ent.label_ == "PERSON":
            persons.append({"name": ent.text})
        elif ent.label_ == "LOC" or ent.label_ == "GPE":
            locations.append({"name": ent.text})
        elif ent.label_ == "ORG":
            organizations.append({"name": ent.text})
```

### How It Handles Multiple Languages

**spaCy Model**: `xx_ent_wiki_sm`
- **Type**: Multilingual NER model
- **Training**: Wikipedia data from multiple languages
- **Supports**: 
  - ✅ Danish
  - ✅ Swedish
  - ✅ Norwegian
  - ✅ Finnish
  - ✅ English
  - Plus many others

**Entity Types Extracted:**
1. **PERSON (PER)**: People names
2. **LOCATION (LOC/GPE)**: Places, cities, countries
3. **ORGANIZATION (ORG)**: Companies, institutions

**Performance:**
- Text truncated to 500 tokens for speed
- Top 10 entities per type kept
- Deduplication applied
- Runs on CPU (doesn't use GPU)

### Example Output:
```json
{
  "entities": {
    "persons": [{"name": "Angela Merkel"}, {"name": "Donald Trump"}],
    "locations": [{"name": "Berlin"}, {"name": "Washington"}],
    "organizations": [{"name": "EU"}, {"name": "NATO"}]
  }
}
```

---

## 🚀 GPU Optimization

### Current Bottleneck

**Problem**: Processing one article at a time sequentially
- GPU Util: 65% (should be 95%+)
- Memory: 14GB / 81GB (18% - underutilized!)
- Processing: ~1 second per article

**Solution**: Batch multiple articles together

### Current Architecture:
```
Article 1 → GPU → Result
Article 2 → GPU → Result  
Article 3 → GPU → Result
```
**GPU sits idle between articles!**

### Optimized Architecture:
```
[Article 1, 2, 3, 4, 5, 6, 7, 8] → GPU (parallel) → [Results 1-8]
```
**GPU processes multiple articles simultaneously!**

---

## ⚡ Options to Maximize GPU Usage

### Option 1: Increase Batch Processing (EASIEST)

The current script processes articles sequentially. The issue is in the LLM inference - it's not batching.

**Problem**: Transformers `model.generate()` is called once per article
**Solution**: Use batch inference

However, the current architecture doesn't support true batching because:
1. Each article has different length
2. We're using chat templates individually
3. The processor is designed for sequential processing

### Option 2: Switch to vLLM (BEST for throughput)

**vLLM** is specifically designed for high-throughput LLM inference:
- Continuous batching
- Paged attention (more efficient memory)
- Can achieve **10-20x throughput** improvement

**Time**: Would require refactoring the NLP processor

### Option 3: Multi-GPU or Tensor Parallelism

Your H100 has 80GB - way more than needed for Mistral-7B. Could:
- Run multiple model instances
- Process multiple articles in parallel with different model instances
- Use threading/multiprocessing

### Option 4: Optimize Current Code (QUICK WIN)

**Immediate improvements:**

1. **Reduce max_new_tokens**: Currently set high, can reduce to 50-80
2. **Use cache**: Enable KV-cache for faster generation
3. **Adjust temperature**: Lower temperature = faster generation
4. **Batch similar-length articles**: Group articles by length before processing

---

## 📊 Estimated Impact

### Current Performance:
- **Speed**: 1-2 seconds/article
- **GPU Util**: 65%
- **Throughput**: ~30,000-60,000 articles/day

### With Optimizations:
| Optimization | Speed | GPU Util | Throughput/day |
|--------------|-------|----------|----------------|
| Batch inference | 0.3-0.5s | 85-95% | 150,000-250,000 |
| vLLM | 0.1-0.2s | 95%+ | 400,000-800,000 |
| Multi-instance | 0.5-1s | 95%+ | 100,000-200,000 |

### For Your 81K Articles:
| Method | Current | Batch | vLLM |
|--------|---------|-------|------|
| Time | 1-2 days | 8-12 hours | 2-4 hours |

---

## 🎯 Recommendation

### Immediate (No code change):
**The current approach is fine** for your 81K sample. It will complete in 1-2 days, which is acceptable for a test run.

### For Phase 2 (732K remaining articles):
**Switch to vLLM** - will reduce time from 9-12 days to 2-3 days

### Quick Win (5 minutes):
Let me create a slightly optimized version that:
1. Reduces token generation overhead
2. Uses better inference settings
3. Processes in micro-batches

**Would you like me to:**
1. ✅ **Keep current** (simplest, works well enough for Phase 1)
2. 🔧 **Quick optimize** (reduce tokens, better settings - 20-30% faster)
3. 🚀 **Full vLLM refactor** (10x faster but takes time to implement)

For the 81K Phase 1, I recommend **option 1** (keep current). For Phase 2 (732K), switch to **option 3** (vLLM).

What do you think?

