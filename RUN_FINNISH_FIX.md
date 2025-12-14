# Run Finnish NER Fix on VM

## Step 1: Sync Script (Already Done)
The updated script has been synced to the VM.

## Step 2: Run on VM

SSH to VM and run:

```bash
ssh -p 2111 frede@212.27.13.34
cd ~/NAMO_nov25
source venv/bin/activate

# Test with 100 articles (recommended first)
python3 scripts/34_ner_country_specific.py \
  --input data/processed/test_ner_100.parquet \
  --output data/nlp_enriched/test_ner_100_results_v2.parquet \
  --device cuda \
  --score-threshold 0.5
```

## Step 3: Monitor Progress

In another terminal (or use `screen`/`tmux`):

```bash
ssh -p 2111 frede@212.27.13.34
tail -f ~/NAMO_nov25/logs/ner_*.log
```

Or filter for Finnish-specific logs:

```bash
tail -f ~/NAMO_nov25/logs/ner_*.log | grep -E "(Finnish|finland|🇫🇮|ERROR|WARNING)"
```

## What Changed

- **Finnish model**: Changed from `TurkuNLP/bert-base-finnish-cased-v1` (not an NER model) to `xlm-roberta-large-finetuned-conll03-english` (multilingual NER model)
- **Added Finnish-specific logging**: You'll see "🇫🇮 Finnish article: extracted X entities" messages
- **Better error handling**: Catches and logs errors during NER pipeline execution

## Expected Results

- Finnish articles should now extract entities (not 0 anymore)
- Logs will show detailed information about Finnish processing
- Check the summary at the end for Finnish entity counts

## If Still Issues

Check the log file for:
- Model loading errors
- Entity extraction errors
- Text length issues

```bash
# Find latest log
ls -lt ~/NAMO_nov25/logs/ner_*.log | head -1

# View it
cat ~/NAMO_nov25/logs/ner_*.log | grep -A 5 -B 5 "finland\|Finnish\|🇫🇮"
```




