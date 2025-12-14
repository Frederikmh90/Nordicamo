# Test with xlm-roberta-large-finetuned-conll03-english

## Step 1: Run NER on VM

```bash
ssh -p 2111 frede@212.27.13.34
cd ~/NAMO_nov25
source venv/bin/activate

python3 scripts/34_ner_country_specific.py \
  --input data/processed/test_ner_100.parquet \
  --output data/nlp_enriched/test_ner_100_xlmroberta.parquet \
  --device cuda \
  --score-threshold 0.5
```

## Step 2: Download Results

```bash
# From local machine
scp -P 2111 frede@212.27.13.34:~/NAMO_nov25/data/nlp_enriched/test_ner_100_xlmroberta.parquet \
  data/nlp_enriched/
```

## Step 3: Analyze Finnish Entities

```bash
python3 scripts/39_analyze_finnish_entities.py \
  --input data/nlp_enriched/test_ner_100_xlmroberta.parquet \
  --top 10
```




