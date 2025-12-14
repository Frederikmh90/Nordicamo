# Test NLP Category Classification on VM

## ✅ Updates Complete

### 1. **Enhanced Prompt** (`scripts/02_nlp_processing.py`)
- ✅ Stricter rules: "Other" should be EXTREMELY RARE (<1%)
- ✅ Explicit category mapping for all 10 categories
- ✅ Requires detailed explanation if "Other" is used
- ✅ More examples added

### 2. **Detailed Logging**
- ✅ Warning logs when "Other" is assigned
- ✅ Shows LLM reasoning
- ✅ Article preview
- ✅ Raw categories from LLM

### 3. **Analysis Script** (`scripts/19_analyze_other_category.py`)
- ✅ Statistics on "Other" usage
- ✅ Sample articles for review
- ✅ Breakdown by country/domain

---

## 🚀 Run Test on VM

### Step 1: Run NLP Processing

```bash
cd /Users/Codebase/projects/alterpublics/NAMO_nov25
source venv/bin/activate

# Run on remote GPU server
python scripts/05_run_nlp_remote_interactive.py \
  --input data/processed/NAMO_preprocessed_test.parquet \
  --batch-size 4
```

**Watch for warnings** like:
```
⚠️  ASSIGNED 'Other' CATEGORY - No valid categories found
   LLM Reasoning: [explanation]
   Article preview: [first 150 chars]
   Raw categories from LLM: [what LLM returned]
```

### Step 2: Download Results

After processing completes, download the enriched parquet file from the remote server.

### Step 3: Analyze "Other" Category

```bash
python scripts/19_analyze_other_category.py \
  --input data/nlp_enriched/nlp_enriched_NAMO_preprocessed_test_final.parquet
```

This will show:
- Percentage of "Other" assignments (target: <1%)
- Sample articles with "Other"
- Breakdown by country/domain
- Recommendations

---

## Expected Results

### Target Metrics
- ✅ **"Other" category**: <1% of articles
- ✅ **Clear explanations**: Each "Other" assignment has reasoning
- ✅ **Actionable insights**: Easy to identify why "Other" was used

### What Changed
- **Before**: ~5-10% "Other", minimal guidance
- **After**: <1% target, explicit category mapping, detailed logging

---

## Key Prompt Improvements

1. **CRITICAL RULES** section with explicit category mapping
2. **"look harder"** instruction to find categories
3. **Requires explanation** if "Other" is used
4. **More examples** for different article types

---

**Ready to test!** Run the commands above to process articles with the updated prompt.

