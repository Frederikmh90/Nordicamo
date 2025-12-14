# Analyze Finnish Entities

## Quick Analysis

Run this script to see top entities extracted from Finnish articles:

```bash
# On VM (if data is there)
cd ~/NAMO_nov25
source venv/bin/activate

python3 scripts/39_analyze_finnish_entities.py \
  --input data/nlp_enriched/test_ner_100_results_finbert.parquet \
  --top 10
```

## Or Download and Analyze Locally

```bash
# 1. Download results from VM
scp -P 2111 frede@212.27.13.34:~/NAMO_nov25/data/nlp_enriched/test_ner_100_results_finbert.parquet \
  data/nlp_enriched/

# 2. Analyze locally
python3 scripts/39_analyze_finnish_entities.py \
  --input data/nlp_enriched/test_ner_100_results_finbert.parquet \
  --top 10
```

## What It Shows

- **Top 10 Persons**: Most mentioned people in Finnish articles
- **Top 10 Locations**: Most mentioned places
- **Top 10 Organizations**: Most mentioned organizations
- **Summary Statistics**: Total counts, unique entities, coverage

## Example Output

```
🇫🇮 Finnish articles: 8
📊 Articles with entities: 6 / 8

TOP 10 PERSONS
1. Example Person Name                    (5 mentions)
...

TOP 10 LOCATIONS
1. Helsinki                               (3 mentions)
...

TOP 10 ORGANIZATIONS
1. Example Organization                   (2 mentions)
...
```




