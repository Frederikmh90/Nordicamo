# NLP Quality Assessment Report

**Date:** November 18, 2025  
**Dataset:** 996 articles (test set)  
**Model:** Qwen2.5-7B-Instruct (4-bit quantized)

---

## Overall Quality Score: **69.0/100**

### Quality Breakdown

| Component | Coverage | Weight | Score Contribution |
|-----------|----------|--------|-------------------|
| **Sentiment Analysis** | 100.0% | 30% | 30.0 |
| **Category Classification** | 39.5% | 30% | 11.9 |
| **Named Entity Recognition** | 96.2% | 20% | 19.2 |
| **JSON Parsing Success** | 39.5% | 20% | 7.9 |
| **TOTAL** | | | **69.0** |

---

## 1. Sentiment Analysis ✅ **Excellent**

**Coverage:** 100% (996/996 articles)

**Distribution:**
- **Neutral:** 788 articles (79.1%)
- **Negative:** 182 articles (18.3%)
- **Positive:** 26 articles (2.6%)

**Assessment:**
- ✅ All articles have sentiment analysis
- ✅ Distribution seems reasonable for alternative media (mostly neutral, some negative)
- ✅ Sentiment scores are consistent with sentiment labels
- ✅ Fallback extraction ensures 100% coverage even when JSON parsing fails

**Quality:** ⭐⭐⭐⭐⭐ Excellent

---

## 2. Category Classification ⚠️ **Needs Improvement**

**Coverage:** 39.5% (393/996 articles)

**Top Categories:**
1. Social Issues & Culture: 151 articles (38.4% of categorized)
2. Crime & Justice: 122 articles (31.0%)
3. Politics & Governance: 113 articles (28.8%)
4. Economy & Labor: 68 articles (17.3%)
5. Immigration & National Identity: 56 articles (14.2%)

**Average categories per article:** 1.73 (for articles with categories)

**Issues:**
- ⚠️ Only 39.5% of articles have categories assigned
- ⚠️ 60.5% of articles lack categories (likely due to JSON parsing failures)
- ✅ Categories that are assigned seem reasonable and relevant
- ✅ All 10 categories are represented

**Quality:** ⭐⭐⭐ Needs Improvement

**Recommendation:** Improve JSON parsing or use structured output mode if available.

---

## 3. Named Entity Recognition ✅ **Excellent**

**Coverage:** 96.2% (958/996 articles)

**Entities Extracted:**
- **Persons:** 5,620 total (~5.9 per article)
- **Locations:** 3,629 total (~3.8 per article)
- **Organizations:** 1,639 total (~1.7 per article)
- **Average:** 11.4 entities per article (for articles with entities)

**Assessment:**
- ✅ Very high coverage (96.2%)
- ✅ Good extraction rate (11+ entities per article)
- ✅ spaCy multilingual model working well for Nordic languages
- ✅ Balanced extraction across entity types

**Quality:** ⭐⭐⭐⭐⭐ Excellent

---

## 4. JSON Parsing Quality ⚠️ **Needs Improvement**

**Success Rate:** 39.5% (393/996 articles)

**Issues:**
- ⚠️ 60.5% of articles had JSON parsing failures
- ✅ Fallback extraction ensures sentiment is still captured
- ⚠️ Categories are lost when JSON parsing fails

**Root Cause:**
- LLM sometimes returns text instead of pure JSON
- Response may include explanations or markdown formatting
- Multilingual content (Nordic languages) may confuse JSON structure

**Improvements Made:**
- ✅ Enhanced prompt with stricter JSON requirements
- ✅ Multiple JSON extraction strategies
- ✅ Fallback text extraction for sentiment
- ✅ Markdown code block removal

**Quality:** ⭐⭐ Needs Significant Improvement

**Future Improvements:**
1. Use structured output mode if Qwen2.5 supports it
2. Fine-tune prompts further for JSON-only responses
3. Consider using a smaller, more controllable model for categorization
4. Post-process LLM responses with more aggressive cleaning

---

## Sample Article Reviews

### Sample 1: With Categories ✅
- **Title:** "Tekniske problemer: Vi er tilbake på luften"
- **Sentiment:** neutral
- **Categories:** Technology, Science & Digital Society
- **Assessment:** ✅ Correct categorization

### Sample 2: Negative Sentiment ✅
- **Title:** "Lørdagsvold i og rundt Oslo"
- **Sentiment:** negative
- **Categories:** Crime & Justice
- **Assessment:** ✅ Appropriate sentiment and category

### Sample 3: With Entities ✅
- **Title:** "Antisemitisk attack mot judisk affärskvinna..."
- **Sentiment:** neutral
- **Entities:** 10 persons, 10 locations, 1 organization
- **Assessment:** ✅ Good entity extraction

### Sample 4: Parse Error (Fallback) ⚠️
- **Title:** "Lööf vill cementera fortsatt socialdemokratiskt..."
- **Sentiment:** neutral (extracted via fallback)
- **Categories:** [] (lost due to parse error)
- **Assessment:** ⚠️ Sentiment captured, but categories lost

---

## Recommendations

### Immediate Actions:
1. ✅ **Use current results** - Sentiment and NER are excellent, categories are partial
2. ✅ **Load into database** - Data quality is sufficient for testing
3. ⚠️ **Monitor category coverage** - Consider reprocessing articles without categories

### Short-term Improvements:
1. **Improve JSON parsing** - Try different prompt strategies
2. **Test structured output** - If Qwen2.5 supports JSON mode
3. **Batch reprocessing** - Reprocess articles without categories with improved prompts

### Long-term Considerations:
1. **Fine-tune model** - Fine-tune Qwen2.5 specifically for JSON output
2. **Hybrid approach** - Use smaller model for categorization, LLM for sentiment
3. **Post-processing** - More aggressive JSON cleaning and validation

---

## Conclusion

**Overall Assessment:** 🟡 **Good, with room for improvement**

**Strengths:**
- ✅ Excellent sentiment analysis (100% coverage)
- ✅ Excellent NER (96% coverage, good extraction rate)
- ✅ Robust fallback mechanisms ensure data capture

**Weaknesses:**
- ⚠️ Category coverage is low (39.5%)
- ⚠️ JSON parsing success rate needs improvement

**Verdict:** The NLP enrichment is **production-ready for sentiment and NER**, but **category classification needs improvement** before full deployment. The current quality (69/100) is acceptable for initial testing and dashboard development.

---

**Report Generated:** `reports/nlp_quality_report.json`

