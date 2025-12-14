# Run Full NER Pipeline

## Quick Start

Run the complete pipeline (NER processing → Download → Database):

```bash
python3 scripts/40_run_full_ner_pipeline.py
```

## Options

### Use different input file
```bash
python3 scripts/40_run_full_ner_pipeline.py \
  --input data/processed/NAMO_preprocessed_test.parquet \
  --output data/nlp_enriched/full_test_ner.parquet
```

### Skip steps (if already done)
```bash
# Skip NER processing (use existing results)
python3 scripts/40_run_full_ner_pipeline.py --skip-ner

# Skip download (results already local)
python3 scripts/40_run_full_ner_pipeline.py --skip-download

# Skip database loading
python3 scripts/40_run_full_ner_pipeline.py --skip-db
```

## Manual Steps (Alternative)

### Step 1: Run NER on VM
```bash
ssh -p 2111 frede@212.27.13.34
cd ~/NAMO_nov25
source venv/bin/activate

python3 scripts/34_ner_country_specific.py \
  --input data/processed/sample_1000.parquet \
  --output data/nlp_enriched/sample_1000_ner_final.parquet \
  --device cuda \
  --score-threshold 0.5
```

### Step 2: Download Results
```bash
scp -P 2111 frede@212.27.13.34:~/NAMO_nov25/data/nlp_enriched/sample_1000_ner_final.parquet \
  data/nlp_enriched/
```

### Step 3: Load to Database
```bash
python3 scripts/37_load_ner_to_db.py \
  --input data/nlp_enriched/sample_1000_ner_final.parquet
```

### Step 4: Verify Frontend
```bash
# Start backend (if not running)
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Start frontend (in another terminal)
streamlit run frontend/app.py
```

## Expected Results

- **NER Processing**: Extracts entities for all countries (Denmark, Sweden, Norway, Finland)
- **Database**: Updates `entities_json` column in `articles` table
- **Frontend**: Shows entity statistics and top entities in dashboard

## Check Results

### Database
```sql
-- Check articles with entities
SELECT 
  country,
  COUNT(*) FILTER (WHERE entities_json IS NOT NULL) as with_entities,
  COUNT(*) as total
FROM articles
GROUP BY country;
```

### Backend API
```bash
# Top persons
curl http://localhost:8000/api/stats/entities/top?entity_type=persons&limit=10

# Entity statistics
curl http://localhost:8000/api/stats/entities/statistics
```




