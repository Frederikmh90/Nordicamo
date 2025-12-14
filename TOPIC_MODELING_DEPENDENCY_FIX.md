# Topic Modeling Dependency Installation Fix

## ✅ Updates Made

### 1. **Improved Installation Order** (`scripts/17_run_topic_modeling_remote.py`)
- ✅ Installs packages in correct order (core → torch → ML → bertopic)
- ✅ Better error handling with full error messages
- ✅ Retry logic with `--no-cache-dir` flag
- ✅ Returns success/failure status

### 2. **Standalone Installer** (`scripts/20_install_topic_deps_remote.py`)
- ✅ Can be run separately if main script fails
- ✅ More detailed output
- ✅ Better troubleshooting guidance

---

## 🔧 Solutions

### Option 1: Run Standalone Dependency Installer

```bash
cd /Users/Codebase/projects/alterpublics/NAMO_nov25
source venv/bin/activate

# Install dependencies separately
python scripts/20_install_topic_deps_remote.py
```

This will:
- Upgrade pip first
- Install packages in correct order
- Show detailed error messages
- Retry failed packages with `--no-cache-dir`

### Option 2: Manual Installation on Remote Server

SSH to the server and install manually:

```bash
ssh -p 2111 frede@212.27.13.34

cd ~/NAMO_nov25
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install in order
pip install numpy pandas scikit-learn nltk tqdm
pip install torch
pip install transformers sentence-transformers
pip install bertopic
pip install polars
```

### Option 3: Use --skip-install Flag

If dependencies are already installed (or partially installed):

```bash
python scripts/17_run_topic_modeling_remote.py \
  --input data/nlp_enriched/nlp_enriched_NAMO_preprocessed_test_final.parquet \
  --output data/topic_modeled/topics.parquet \
  --skip-install
```

---

## 🔍 Common Issues

### Issue: `bertopic` fails to install
**Solution**: Install dependencies first:
```bash
pip install numpy scikit-learn umap-learn hdbscan
pip install bertopic
```

### Issue: `sentence-transformers` fails
**Solution**: Install transformers first:
```bash
pip install transformers
pip install sentence-transformers
```

### Issue: Out of disk space
**Check**: `df -h` on remote server
**Solution**: Clean pip cache:
```bash
pip cache purge
pip install --no-cache-dir [package]
```

### Issue: Python version mismatch
**Check**: `python3 --version` (should be 3.8+)
**Solution**: Use correct Python version

---

## 📋 Installation Order (Important!)

1. **Core packages**: numpy, pandas, scikit-learn, nltk, tqdm
2. **PyTorch**: torch (large download, may take time)
3. **ML libraries**: transformers, sentence-transformers
4. **Topic modeling**: bertopic (depends on everything above)
5. **Data processing**: polars

---

## ✅ Verify Installation

After installation, verify on remote server:

```bash
ssh -p 2111 frede@212.27.13.34
cd ~/NAMO_nov25
source venv/bin/activate

python3 -c "
import bertopic
import transformers
import sentence_transformers
import torch
print('✅ All packages imported successfully')
print(f'PyTorch version: {torch.__version__}')
print(f'Transformers version: {transformers.__version__}')
"
```

---

## 🚀 After Dependencies Are Installed

Run topic modeling:

```bash
python scripts/17_run_topic_modeling_remote.py \
  --input data/nlp_enriched/nlp_enriched_NAMO_preprocessed_test_final.parquet \
  --output data/topic_modeled/topics.parquet \
  --skip-install
```

---

**Try Option 1 first** - the standalone installer should handle most issues automatically!

