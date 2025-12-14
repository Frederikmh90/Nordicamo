# NAMO Project Status Report

**Date:** November 18, 2025  
**Status:** ✅ Phase 1 Complete - Data Preprocessing Pipeline Ready

---

## Executive Summary

Successfully created data preprocessing pipeline for the Nordic Alternative Media Observatory (NAMO). The pipeline handles **9.5 million articles** across 4 Nordic countries (Denmark, Sweden, Norway, Finland) from 75 alternative media outlets.

### Key Achievements

✅ **Data verification completed**
- 9.5M articles loaded and accessible
- 75 actors with partisan classifications
- Successful domain-based merge (64% match rate on test sample)

✅ **Preprocessing pipeline built**
- Script 1: Data loading, merging, and basic feature extraction
- Script 2: NLP processing (sentiment, categorization, NER)
- Batch processing support for large-scale datasets

✅ **Project infrastructure established**
- Directory structure created
- Dependencies documented
- Setup script ready for deployment

---

## Dataset Overview

### Article Dataset (`NAMO_2025_09.csv`)
- **Size:** 2.35 GB
- **Total Articles:** 9,578,179
- **Columns:** 11 (url, title, description, content, author, date, extraction_method, domain, country, content_length, scraped_at)

### Actor Dataset (`NAMO_actor_251118.xlsx`)
- **Size:** 0.04 MB
- **Total Actors:** 75
- **Columns:** 25 (including Actor_domain, Partisan, Country, etc.)

### Partisan Distribution
- **Right:** 40 actors (53%)
- **Left:** 18 actors (24%)
- **Other:** 17 actors (23%)

### Country Distribution
- **Sweden:** 24 actors (32%)
- **Finland:** 21 actors (28%)
- **Denmark:** 16 actors (21%)
- **Norway:** 14 actors (19%)

---

## News Categories (10 Categories)

The NLP pipeline will classify articles into these categories:

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

---

## Completed Scripts

### 1. `scripts/00_verify_data.py`
Quick verification script to check data integrity and show basic statistics.

**Usage:**
```bash
python3 scripts/00_verify_data.py
```

### 2. `scripts/01_data_preprocessing.py`
Main preprocessing script that:
- Loads article and actor datasets
- Merges partisan values based on domain matching
- Extracts external links from article content
- Adds word count and timestamps
- Saves to optimized Parquet format

**Test run (100 articles):**
```bash
python3 scripts/01_data_preprocessing.py --test --test-size 100
```

**Full run (9.5M articles):**
```bash
python3 scripts/01_data_preprocessing.py --full
```

**Results from test run:**
- ✅ 100 articles processed in ~20 seconds
- ✅ 64% match rate with actor data
- ✅ 18 columns in final output (7 new columns added)
- ✅ Saved to `data/processed/NAMO_preprocessed_test.parquet`

### 3. `scripts/02_nlp_processing.py`
NLP enrichment script that adds:
- **Sentiment analysis:** positive/negative/neutral (using Qwen2.5-7B quantized)
- **Category classification:** Up to 3 categories per article
- **Named Entity Recognition:** Persons, locations, organizations (using spaCy)

**Features:**
- 4-bit quantization for GPU memory efficiency
- Batch processing with progress tracking
- Multilingual support (Danish, Swedish, Norwegian, Finnish)
- Configurable model and batch size

**Test run:**
```bash
python3 scripts/02_nlp_processing.py \
  --input data/processed/NAMO_preprocessed_test.parquet \
  --batch-size 4
```

**Status:** ⏳ Ready to test (requires dependencies installation)

### 4. `scripts/run_test_pipeline.py`
Automated test runner that executes the complete pipeline end-to-end.

---

## Project Structure

```
NAMO_nov25/
├── data/
│   ├── NAMO_2025_09.csv              # Raw article data (2.35 GB, 9.5M articles)
│   ├── NAMO_actor_251118.xlsx        # Actor metadata (75 actors)
│   ├── processed/                     # ✅ Preprocessed data
│   │   ├── checkpoint_01_merged.parquet
│   │   ├── checkpoint_02_basic_features.parquet
│   │   └── NAMO_preprocessed_test.parquet
│   └── nlp_enriched/                  # ⏳ NLP-enriched data (pending)
│
├── scripts/
│   ├── 00_verify_data.py              # ✅ Data verification
│   ├── 01_data_preprocessing.py       # ✅ Basic preprocessing
│   ├── 02_nlp_processing.py           # ✅ NLP enrichment (ready)
│   └── run_test_pipeline.py           # ✅ Test pipeline runner
│
├── notebooks/                          # Jupyter notebooks
│   ├── reference_02_bertopic_da.py    # BERTopic reference
│   └── test_wrangling.py
│
├── models/                             # Saved ML models
├── logs/                               # Log files
│
├── requirements.txt                    # ✅ Python dependencies
├── setup.sh                            # ✅ Setup script
├── README_SETUP.md                     # ✅ Setup documentation
└── STATUS_REPORT.md                    # This file
```

---

## Next Steps

### Phase 2: NLP Enrichment (⏳ In Progress)

1. **Install dependencies**
   ```bash
   # If using uv (recommended)
   chmod +x setup.sh && ./setup.sh
   
   # Or manually
   pip3 install -r requirements.txt
   python3 -m spacy download xx_ent_wiki_sm
   ```

2. **Test NLP pipeline on 100 articles**
   ```bash
   python3 scripts/02_nlp_processing.py \
     --input data/processed/NAMO_preprocessed_test.parquet \
     --batch-size 4
   ```

3. **Review results and adjust categories if needed**

4. **Run on larger sample (e.g., 10,000 articles) to benchmark performance**

5. **Decide on processing strategy for full 9.5M articles:**
   - **Option A:** Process on local machine (slow, ~weeks)
   - **Option B:** Use remote GPU server (ssh frede@212.27.13.34 -p 2111)
   - **Option C:** Process in chunks over time

### Phase 3: Database Setup (📋 Planned)

1. **Design PostgreSQL schema**
   - Articles table with NLP columns
   - Actors table
   - Indexes for efficient querying
   - Consider partitioning by country/date for performance

2. **Create database loading script**
   - Batch insertion
   - Duplicate handling
   - Update mechanism for bi-annual refreshes

3. **Set up PostgreSQL on server**

### Phase 4: Backend Development (📋 Planned)

1. **Design FastAPI endpoints**
   - Article retrieval and filtering
   - Aggregated statistics by country/partisan/category
   - Time-series data for charts
   - Topic modeling results

2. **Implement data analytics queries**
   - Article counts by country
   - Partisan distribution over time
   - Category trends
   - Sentiment analysis by outlet

3. **Add caching for performance**

### Phase 5: Frontend Dashboard (📋 Planned)

1. **Create Streamlit dashboard**
   - Overview page with key metrics
   - Country-specific pages
   - Topic exploration
   - Search functionality

2. **Design visualizations**
   - Article counts over time (line charts)
   - Partisan distribution (pie/bar charts)
   - Category heatmaps
   - Geographic distribution
   - Topic modeling visualization

### Phase 6: Deployment (📋 Planned)

1. **Deploy to remote server**
2. **Set up automatic data updates**
3. **Configure domain and SSL**
4. **User access management**

### Phase 7: Methods Paper (📋 Planned)

1. **Expand on existing draft** (references/Chapter 15_Henriksen_fmh.pdf)
2. **Document data collection methodology**
3. **Describe NLP processing pipeline**
4. **Present descriptive statistics**
5. **Discuss alternative media landscape in Nordic countries**

---

## Technical Decisions & Rationale

### ✅ Polars over Pandas
- **Why:** 10-100x faster for large datasets, better memory efficiency
- **Trade-off:** Less familiar syntax, but worth it for 9.5M articles

### ✅ Parquet over CSV
- **Why:** Columnar format, compressed, 5-10x smaller, faster I/O
- **Trade-off:** Requires specific tools to read, but standard in data engineering

### ✅ Qwen2.5 with 4-bit Quantization
- **Why:** Good multilingual performance, fits on 8GB GPU with quantization
- **Trade-off:** Slightly lower quality vs full precision, but acceptable
- **Alternative:** Could use Qwen2.5-3B for faster processing

### ✅ spaCy for NER
- **Why:** Fast, lightweight, multilingual model available
- **Trade-off:** Less accurate than LLM-based NER, but much faster

### ✅ FastAPI over Flask
- **Why:** Async support, automatic API docs, type validation, modern
- **Trade-off:** Slightly steeper learning curve

### ✅ Streamlit over React
- **Why:** Python-based, rapid development, perfect for research dashboards
- **Trade-off:** Less customizable than React, but sufficient for this use case

---

## Performance Considerations

### Processing Time Estimates

**On local machine (M1/M2 Mac, CPU only):**
- Preprocessing (9.5M articles): ~4-6 hours
- NLP processing (9.5M articles): ~200-300 hours (8-12 days)

**On remote GPU server (assuming RTX 3090/4090):**
- Preprocessing (9.5M articles): ~2-3 hours
- NLP processing (9.5M articles): ~20-40 hours (1-2 days)

### Recommendations

1. **For testing:** Use local machine with small samples (100-10,000 articles)
2. **For full processing:** Use remote GPU server
3. **For production:** Process incrementally, cache results, update bi-annually

---

## Questions for Discussion

### NLP Processing

1. **LLM Model:** Qwen2.5-7B vs Qwen2.5-3B? (speed vs quality trade-off)
2. **Category list:** Are the 10 categories appropriate? Any adjustments needed?
3. **Processing location:** Local vs remote server for full dataset?
4. **Batch size:** How large is the GPU on the remote server?

### Database Design

1. **Partitioning strategy:** By country? By date? Both?
2. **Historical data:** Keep all versions or only latest?
3. **Access patterns:** What queries will be most common?

### Dashboard Design

1. **Target audience:** Researchers? Public? Journalists?
2. **Key metrics:** What are the most important statistics to display?
3. **Interactivity level:** Simple filters or advanced exploration tools?

### Methods Paper

1. **Target journal/venue:** Specific publication in mind?
2. **Focus areas:** Data collection methodology vs analysis vs findings?
3. **Timeline:** When do you need the paper ready?

---

## Contact & Support

- **Project directory:** `/Users/Codebase/projects/alterpublics/NAMO_nov25`
- **Remote server:** `ssh frede@212.27.13.34 -p 2111`
- **Logs:** Check `preprocessing.log` for detailed execution logs

---

## Appendix: Sample Output

### Preprocessed Article (columns)
```
url, title, description, content, author, date, extraction_method, domain, 
country, content_length, scraped_at, Actor, Country, Partisan, 
Partisan_fullcategories, external_links, word_count, preprocessed_at
```

### After NLP Enrichment (additional columns)
```
sentiment, sentiment_score, categories (JSON), entities_json, 
nlp_processed_at
```

### Example Entity JSON
```json
{
  "persons": [{"name": "Donald Trump"}],
  "locations": [{"name": "Oslo"}],
  "organizations": [{"name": "NATO"}]
}
```

---

**Last Updated:** November 18, 2025  
**Version:** 1.0

