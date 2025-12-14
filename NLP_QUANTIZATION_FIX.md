# NLP Processing - Quantization Fix

## 🔍 Problem Identified

The LLM is producing **text continuations instead of JSON** responses. Looking at the logs:
- Raw LLM responses are fragments like: `"tilbake i Ukraine etter å ha vært forhindret av krigen...."`
- These look like continuations of the article text, not JSON
- This suggests the model is not following the JSON format instruction

## 💡 Root Cause

**4-bit quantization** may be causing the model to:
- Produce incomplete outputs
- Not follow JSON format instructions properly
- Generate text continuations instead of structured responses

## ✅ Solution

### 1. **Disable Quantization by Default**

Updated `scripts/02_nlp_processing.py`:
- ✅ **Default**: Quantization **DISABLED** (better JSON output quality)
- ✅ **Option**: Use `--use-quantization` flag if GPU memory is limited
- ✅ **GPU monitoring**: Added GPU memory checks before/after loading

### 2. **Check GPU Usage**

New script to check GPU availability:
```bash
python scripts/21_check_gpu_usage.py
```

This shows:
- GPU memory total/free/used
- Current GPU processes
- Recommendations for quantization

### 3. **Updated Remote Script**

`scripts/05_run_nlp_remote_interactive.py` now defaults to `--no-quantization`

---

## 🚀 Run Without Quantization

### Check GPU First

```bash
python scripts/21_check_gpu_usage.py
```

### Run NLP Processing (No Quantization)

```bash
python scripts/05_run_nlp_remote_interactive.py \
  --input data/processed/NAMO_preprocessed_test.parquet \
  --batch-size 4
```

This will automatically use `--no-quantization` for better JSON output.

### If GPU Memory is Limited

If you get out-of-memory errors, you can enable quantization:
```bash
# Manually edit the command in 05_run_nlp_remote_interactive.py
# Change --no-quantization to --use-quantization
```

Or run directly:
```bash
ssh -p 2111 frede@212.27.13.34
cd ~/NAMO_nov25
source venv/bin/activate
python3 scripts/02_nlp_processing.py \
  --input data/processed/NAMO_preprocessed_test.parquet \
  --output data/nlp_enriched/test.parquet \
  --batch-size 4 \
  --use-quantization  # Only if needed
```

---

## 📊 Expected Improvements

### Before (With Quantization)
- ❌ Many JSON parsing failures
- ❌ Text continuations instead of JSON
- ❌ High "Other" category rate

### After (Without Quantization)
- ✅ Better JSON format compliance
- ✅ More complete responses
- ✅ Lower "Other" category rate
- ✅ Better category classification

---

## 💾 GPU Memory Requirements

**Qwen2.5-7B-Instruct:**
- **Without quantization**: ~14GB GPU memory
- **With 4-bit quantization**: ~5-6GB GPU memory

**Check your GPU:**
```bash
python scripts/21_check_gpu_usage.py
```

---

## ⚠️ Trade-offs

**Without Quantization:**
- ✅ Better JSON output quality
- ✅ More reliable category classification
- ❌ Requires more GPU memory (~14GB)

**With Quantization:**
- ✅ Lower GPU memory usage (~5-6GB)
- ❌ May produce incomplete JSON
- ❌ Higher "Other" category rate

---

**Recommendation**: Use **no quantization** if you have enough GPU memory (14GB+). The improved JSON output quality is worth the extra memory usage.

