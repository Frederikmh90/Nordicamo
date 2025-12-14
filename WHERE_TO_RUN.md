# Where to Run Each Script

## Classification (GPU Required) → **VM/Server**

**Script**: `scripts/26_category_classification_only.py`

**Why VM:**
- ✅ Has GPU for faster processing
- ✅ Has PyTorch, transformers installed
- ✅ Can handle large models (Mistral-7B)

**Run on VM:**
```bash
# SSH to server
ssh -p 2111 frede@212.27.13.34

cd ~/NAMO_nov25
source venv/bin/activate

python3 scripts/26_category_classification_only.py \
  --input data/processed/sample_1000.parquet \
  --output data/nlp_enriched/sample_1000_categories.parquet \
  --model mistralai/Mistral-7B-Instruct-v0.2 \
  --no-quantization
```

## Database Loading → **Local Computer**

**Script**: `scripts/28_load_categories_to_db.py`

**Why Local:**
- ✅ PostgreSQL is running locally
- ✅ Only needs psycopg2 (lightweight)
- ✅ No GPU needed

**Run Locally:**
```bash
# On your local machine
cd /Users/Codebase/projects/alterpublics/NAMO_nov25

# Make sure PostgreSQL is running
brew services list | grep postgresql

# Run database loading
python3 scripts/28_load_categories_to_db.py \
  --input data/nlp_enriched/sample_1000_categories.parquet
```

**Note**: You'll need to download the parquet file from the VM first, or set up the database on the VM.

## Recommended Workflow

### Option 1: Run Everything on VM (if PostgreSQL is on VM)

```bash
# On VM
cd ~/NAMO_nov25
source venv/bin/activate

# Step 1: Classification (on VM)
python3 scripts/26_category_classification_only.py \
  --input data/processed/sample_1000.parquet \
  --output data/nlp_enriched/sample_1000_categories.parquet \
  --model mistralai/Mistral-7B-Instruct-v0.2 \
  --no-quantization

# Step 2: Database loading (on VM, if PostgreSQL is there)
python3 scripts/28_load_categories_to_db.py \
  --input data/nlp_enriched/sample_1000_categories.parquet
```

### Option 2: Classification on VM, Database on Local

```bash
# Step 1: Classification on VM
ssh -p 2111 frede@212.27.13.34
cd ~/NAMO_nov25
source venv/bin/activate
python3 scripts/26_category_classification_only.py \
  --input data/processed/sample_1000.parquet \
  --output data/nlp_enriched/sample_1000_categories.parquet \
  --model mistralai/Mistral-7B-Instruct-v0.2 \
  --no-quantization

# Step 2: Download result file
# In another terminal (local):
scp -P 2111 frede@212.27.13.34:~/NAMO_nov25/data/nlp_enriched/sample_1000_categories.parquet \
  data/nlp_enriched/

# Step 3: Load to database locally
python3 scripts/28_load_categories_to_db.py \
  --input data/nlp_enriched/sample_1000_categories.parquet
```

## Quick Answer

**Classification**: VM (has GPU + dependencies)
**Database Loading**: Local (PostgreSQL is local)

