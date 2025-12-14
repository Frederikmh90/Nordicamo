# Topic Modeling Fix - Command & Dependencies

## 🔍 Issues Fixed

### 1. **Command Construction Error**
- ❌ **Problem**: Command was malformed with `&&` separating arguments incorrectly
- ✅ **Fix**: Properly quote paths and combine arguments in single command string

### 2. **Missing `accelerate` Package**
- ❌ **Problem**: `device_map="auto"` requires `accelerate` package
- ✅ **Fix**: Added `accelerate` to dependency list and added graceful fallback

### 3. **Deprecated `torch_dtype` Parameter**
- ❌ **Problem**: `torch_dtype` is deprecated, should use `dtype`
- ✅ **Fix**: Updated to use `dtype` parameter

---

## ✅ Changes Made

### 1. **Fixed Command Construction** (`scripts/17_run_topic_modeling_remote.py`)
```python
# Before (broken):
cmd_parts = [
    "python3 scripts/15_topic_modeling_turftopic.py",
    f"--input {input_file}",
    f"--output {output_file}",
]
cmd = " && ".join(cmd_parts)  # ❌ Wrong - && separates commands, not args

# After (fixed):
remote_input_full = f"{remote_dir_expanded}/{input_file}"
remote_output_full = f"{remote_dir_expanded}/{output_file}"
cmd_parts = [
    f"cd {remote_dir_expanded}",
    "source venv/bin/activate",
    f"python3 scripts/15_topic_modeling_turftopic.py --input '{remote_input_full}' --output '{remote_output_full}'"
]
cmd = " && ".join(cmd_parts)  # ✅ Correct
```

### 2. **Added `accelerate` Dependency** (`scripts/17_run_topic_modeling_remote.py`)
- Added `accelerate` to ML packages list
- Installs before transformers/bertopic

### 3. **Fixed Model Loading** (`scripts/15_topic_modeling_turftopic.py`)
- Check for `accelerate` before using `device_map="auto"`
- Fallback to manual device placement if not available
- Updated `torch_dtype` → `dtype` parameter

---

## 🚀 Run Again

The script will now:
1. ✅ Install `accelerate` automatically
2. ✅ Use correct command structure
3. ✅ Handle device placement gracefully

```bash
python scripts/17_run_topic_modeling_remote.py \
  --input data/nlp_enriched/nlp_enriched_NAMO_preprocessed_test_final.parquet \
  --output data/topic_modeled/topics.parquet
```

---

## 📋 What Will Happen

1. **Installs `accelerate`** (if not already installed)
2. **Loads mmBERT** with proper device placement
3. **Runs topic modeling** with correct command arguments
4. **Saves results** to specified output path

---

**All fixes applied!** Run the command above to start topic modeling. 🚀

