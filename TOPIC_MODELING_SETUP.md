# Topic Modeling with TurfTopic - Setup Guide

## Overview

This implementation provides multilingual topic modeling for Nordic languages (Danish, Swedish, Norwegian, Finnish) using either:
1. **TurfTopic** (if available) - The new approach mentioned in the JOSS paper
2. **BERTopic with BGE-M3** (fallback) - Multilingual embeddings supporting 100+ languages

## Installation

### Option 1: Try TurfTopic (if available)

```bash
# Check if TurfTopic is available on PyPI or GitHub
pip install turftopic

# Or install from GitHub if available:
# pip install git+https://github.com/[turftopic-repo]
```

### Option 2: Use BERTopic with Multilingual Embeddings (Recommended)

```bash
# Already in requirements.txt
pip install bertopic sentence-transformers scikit-learn nltk
```

The script will automatically use BGE-M3 (`BAAI/bge-m3`) which supports:
- ✅ Danish (da)
- ✅ Swedish (sv)  
- ✅ Norwegian (no)
- ✅ Finnish (fi)
- ✅ 100+ other languages

## Usage

### Basic Usage

```bash
cd /Users/Codebase/projects/alterpublics/NAMO_nov25
source venv/bin/activate

# Process all countries
python scripts/15_topic_modeling_turftopic.py \
  --input data/nlp_enriched/nlp_enriched_NAMO_preprocessed_test_final.parquet \
  --output data/topic_modeled/topics.parquet

# Process specific countries with sampling (for testing)
python scripts/15_topic_modeling_turftopic.py \
  --input data/nlp_enriched/nlp_enriched_NAMO_preprocessed_test_final.parquet \
  --countries denmark sweden \
  --sample-size 1000 \
  --output data/topic_modeled/topics_test.parquet
```

### Process on Remote GPU Server

```bash
# Sync script to remote
scp -P 2111 scripts/15_topic_modeling_turftopic.py \
  frede@212.27.13.34:~/NAMO_nov25/scripts/

# Run on remote (with GPU)
ssh -p 2111 frede@212.27.13.34
cd ~/NAMO_nov25
source venv/bin/activate
python scripts/15_topic_modeling_turftopic.py \
  --input data/nlp_enriched/nlp_enriched_NAMO_preprocessed_test_final.parquet \
  --output data/topic_modeled/topics.parquet
```

## Features

### Multilingual Support
- ✅ Danish (da)
- ✅ Swedish (sv)
- ✅ Norwegian (no)
- ✅ Finnish (fi)
- Uses BGE-M3 embeddings which handle all Nordic languages

### Automatic Topic Detection
- Automatically determines optimal number of topics
- Can be overridden with `--n-topics` parameter

### Per-Country Models
- Trains separate topic models for each country
- Better topic quality for language-specific content
- Models saved to `models/topic_model_{country}/`

### Output Files
1. **Topics Parquet**: Articles with topic assignments
   - `topic_id`: Assigned topic number
   - `topic_probability`: Confidence score

2. **Topic Info CSV**: Topic descriptions per country
   - Top words for each topic
   - Topic sizes
   - Saved to `data/topic_modeled/topic_info_{country}.csv`

3. **Saved Models**: Reusable topic models
   - Saved to `models/topic_model_{country}/`
   - Can be loaded later for inference

## Integration with Database

After running topic modeling, you can load topics into PostgreSQL:

```python
# Add topic_id and topic_probability columns to articles table
# Then load the topic_modeled parquet file
```

## Integration with Dashboard

Topics can be visualized:
- Topic distribution charts
- Topic evolution over time
- Top topics by country/partisan
- Topic-word clouds

## Next Steps

1. ✅ Run topic modeling on test data
2. ✅ Evaluate topic quality
3. ✅ Integrate topics into database schema
4. ✅ Create API endpoints for topic analysis
5. ✅ Add topic visualizations to dashboard

## Troubleshooting

**Out of Memory:**
- Use `--sample-size` to process fewer articles
- Process countries separately
- Use smaller embedding model

**Poor Topic Quality:**
- Increase minimum articles per country
- Adjust vectorizer parameters
- Try different embedding models

**Language Detection Issues:**
- Ensure content column has valid text
- Check for encoding issues
- Verify language codes are correct

