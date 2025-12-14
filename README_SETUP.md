# NAMO Data Pipeline Setup

## Overview

This is the Nordic Alternative Media Observatory (NAMO) data processing and analysis pipeline. The project processes ~1M articles from alternative news media across Nordic countries.

## Project Structure

```
NAMO_nov25/
├── data/
│   ├── NAMO_2025_09.csv           # Raw article dataset (~1M articles)
│   ├── NAMO_actor_251118.xlsx     # Actor/domain metadata
│   ├── processed/                  # Preprocessed data (after merging)
│   └── nlp_enriched/              # NLP-enriched data
├── scripts/
│   ├── 01_data_preprocessing.py   # Initial data merging & preprocessing
│   ├── 02_nlp_processing.py       # NLP enrichment (sentiment, categories, NER)
│   └── run_test_pipeline.py       # Test runner
├── notebooks/                      # Jupyter notebooks for exploration
├── models/                         # Saved ML models
├── backend/                        # FastAPI backend (TBD)
├── frontend/                       # Streamlit dashboard (TBD)
└── requirements.txt               # Python dependencies
```

## Installation

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- GPU with CUDA (optional, for faster NLP processing)

### Setup Steps

1. **Clone and navigate to the project:**
   ```bash
   cd /Users/Codebase/projects/alterpublics/NAMO_nov25
   ```

2. **Run the setup script:**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Activate the virtual environment:**
   ```bash
   source .venv/bin/activate
   ```

## Pipeline Stages

### Stage 1: Data Preprocessing

Merges actor metadata with article data and adds basic features.

**Test run (100 articles):**
```bash
python scripts/01_data_preprocessing.py --test --test-size 100
```

**Full run (~1M articles):**
```bash
python scripts/01_data_preprocessing.py --full
```

**Output:** `data/processed/NAMO_preprocessed_[test|full].parquet`

### Stage 2: NLP Processing

Adds sentiment analysis, categorization, and named entity recognition.

**Features added:**
- **Sentiment:** positive, negative, or neutral (using Qwen2.5-7B quantized)
- **Categories:** Up to 3 categories from 10 predefined news categories
- **Named Entities:** Persons, locations, organizations (using spaCy)
- **External Links:** Extracted from article content (regex)

**Test run:**
```bash
python scripts/02_nlp_processing.py \
  --input data/processed/NAMO_preprocessed_test.parquet \
  --batch-size 4
```

**Full run:**
```bash
python scripts/02_nlp_processing.py \
  --input data/processed/NAMO_preprocessed_full.parquet \
  --batch-size 8
```

**Output:** `data/nlp_enriched/nlp_enriched_*.parquet`

### Stage 3: Database Setup (TBD)

Load enriched data into PostgreSQL database.

### Stage 4: Backend Development (TBD)

FastAPI backend for serving data and analytics.

### Stage 5: Frontend Dashboard (TBD)

Streamlit dashboard for visualization.

## News Categories

The pipeline classifies articles into these categories:

1. **Politics & Governance** - elections, political parties, government actions
2. **Immigration & National Identity** - borders, migration, cultural identity
3. **Economy & Labor** - economic policy, workers' rights, corporate critique
4. **Health & Medicine** - pandemic, vaccines, healthcare policy
5. **Media & Censorship** - mainstream media criticism, free speech
6. **International Relations & Conflict** - war, geopolitics, foreign policy
7. **Environment & Energy** - climate policy, energy independence
8. **Crime & Justice** - law enforcement, judicial system
9. **Social Issues & Culture** - gender, education, religion
10. **Technology & Surveillance** - big tech, privacy, digital rights

## Testing

Run the complete test pipeline (100 articles):

```bash
python scripts/run_test_pipeline.py
```

This will:
1. Run preprocessing on a small sample
2. Check NLP dependencies
3. Run NLP processing
4. Generate test outputs

## GPU Considerations

The NLP processing script uses **4-bit quantization** by default to fit Qwen2.5-7B on most GPUs (8GB+ VRAM).

**To disable quantization** (if you have >24GB VRAM):
```bash
python scripts/02_nlp_processing.py --input <file> --no-quantization
```

**To use a smaller model:**
```bash
python scripts/02_nlp_processing.py --input <file> --model Qwen/Qwen2.5-3B-Instruct
```

## Remote Server Deployment

For deployment to your server (ssh frede@212.27.13.34 -p 2111):

1. Transfer code and data to server
2. Run setup.sh on server
3. Run full pipeline on GPU
4. Set up PostgreSQL database
5. Deploy FastAPI + Streamlit

## Troubleshooting

**Out of memory errors:**
- Reduce `--batch-size` (try 2 or 1)
- Use smaller model: `--model Qwen/Qwen2.5-3B-Instruct`
- Process in smaller chunks

**spaCy model not found:**
```bash
python -m spacy download xx_ent_wiki_sm
```

**CUDA not available:**
The pipeline will automatically fall back to CPU (much slower).

## Next Steps

1. ✅ Test preprocessing on 100 articles
2. ✅ Verify NLP processing works
3. ⏳ Design PostgreSQL schema
4. ⏳ Create database loading script
5. ⏳ Design FastAPI backend
6. ⏳ Create Streamlit dashboard
7. ⏳ Deploy to remote server

## Contact

Questions? Check the logs in `preprocessing.log` or review the code documentation.

