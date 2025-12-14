# Getting Started with NAMO

**Welcome to the Nordic Alternative Media Observatory (NAMO) project!**

This guide will help you get started with the data processing and analysis pipeline.

---

## 🎯 Quick Start

### 1. Verify Your Data (1 minute)

```bash
cd /Users/Codebase/projects/alterpublics/NAMO_nov25
python3 scripts/00_verify_data.py
```

**Expected output:**
- ✅ 9.5M articles loaded
- ✅ 75 actors loaded
- ✅ Data structure verified

### 2. Test Preprocessing (1 minute)

```bash
python3 scripts/01_data_preprocessing.py --test --test-size 100
```

**Expected output:**
- ✅ 100 articles processed
- ✅ ~64% match rate with actor data
- ✅ Output saved to `data/processed/NAMO_preprocessed_test.parquet`

**Status:** ✅ **COMPLETED** - This works!

### 3. Install Dependencies for NLP (5-10 minutes)

**Option A: Using uv (recommended)**
```bash
chmod +x setup.sh
./setup.sh
```

**Option B: Manual installation**
```bash
pip3 install polars pandas numpy openpyxl
pip3 install transformers torch sentence-transformers spacy
pip3 install accelerate bitsandbytes
pip3 install fastapi uvicorn streamlit plotly
pip3 install psycopg2-binary sqlalchemy
pip3 install tqdm python-dotenv pyyaml

python3 -m spacy download xx_ent_wiki_sm
```

### 4. Test NLP Processing (10-30 minutes depending on GPU)

```bash
python3 scripts/02_nlp_processing.py \
  --input data/processed/NAMO_preprocessed_test.parquet \
  --batch-size 4
```

**Note:** This will download Qwen2.5-7B model (~4GB with quantization) on first run.

**Expected output:**
- ✅ Sentiment, categories, and entities added
- ✅ Output saved to `data/nlp_enriched/nlp_enriched_*.parquet`

---

## 📁 What You Have Now

### ✅ Completed Files

| File | Description | Status |
|------|-------------|--------|
| `scripts/00_verify_data.py` | Data verification script | ✅ Tested, works |
| `scripts/01_data_preprocessing.py` | Merge actor data, extract links | ✅ Tested, works |
| `scripts/02_nlp_processing.py` | Sentiment, categories, NER | ✅ Ready to test |
| `scripts/run_test_pipeline.py` | Run complete pipeline | ✅ Ready to test |
| `requirements.txt` | All dependencies | ✅ Complete |
| `setup.sh` | Automated setup | ✅ Ready |
| `STATUS_REPORT.md` | Detailed status report | ✅ Up to date |
| `BACKEND_DESIGN.md` | Backend architecture design | ✅ Ready for review |
| `README_SETUP.md` | Setup documentation | ✅ Complete |

### 📊 Processed Data

| File | Records | Size | Status |
|------|---------|------|--------|
| `data/NAMO_2025_09.csv` | 9.5M | 2.35 GB | ✅ Original data |
| `data/NAMO_actor_251118.xlsx` | 75 | 0.04 MB | ✅ Original data |
| `data/processed/NAMO_preprocessed_test.parquet` | 100 | ~50 KB | ✅ Test output |
| `data/processed/checkpoint_01_merged.parquet` | 100 | ~40 KB | ✅ Checkpoint |
| `data/processed/checkpoint_02_basic_features.parquet` | 100 | ~50 KB | ✅ Checkpoint |

---

## 🎨 News Categories

Your articles will be classified into these 10 categories:

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

**Question:** Do these categories work for alternative/hyper-partisan Nordic media? Any adjustments needed?

---

## 🗄️ Database Schema Preview

Once NLP processing is complete, your articles will have these fields:

### Original Fields (11)
- url, title, description, content, author, date, extraction_method
- domain, country, content_length, scraped_at

### Added by Preprocessing (7)
- Actor, Country (from actor dataset), Partisan, Partisan_fullcategories
- external_links, word_count, preprocessed_at

### Added by NLP Processing (5)
- sentiment, sentiment_score, categories, entities_json, nlp_processed_at

**Total: 23 fields**

---

## 🚀 Next Steps

### Immediate Actions (Today/This Week)

1. **Test NLP processing** on 100 articles
   ```bash
   python3 scripts/02_nlp_processing.py \
     --input data/processed/NAMO_preprocessed_test.parquet \
     --batch-size 4
   ```

2. **Review the results** - Check if sentiment and categories make sense

3. **Decide on processing strategy:**
   - **Option A:** Process larger sample locally (1K-10K articles) to validate
   - **Option B:** Move to GPU server for full processing

4. **Review BACKEND_DESIGN.md** - Discuss database schema and API endpoints

### Short-term (Next 1-2 Weeks)

1. **Create PostgreSQL database** and load test data
2. **Build basic FastAPI endpoints** (overview statistics, articles by country)
3. **Create simple Streamlit dashboard** with 2-3 key visualizations
4. **Test end-to-end workflow** on localhost

### Medium-term (Next Month)

1. **Process full dataset** on GPU server (9.5M articles)
2. **Deploy to production server** (ssh frede@212.27.13.34 -p 2111)
3. **Complete dashboard** with all visualizations
4. **Set up update pipeline** for bi-annual refreshes

### Long-term (2-3 Months)

1. **Methods paper** writing and submission
2. **Public launch** of observatory
3. **Advanced analytics** (topic modeling, network analysis)

---

## 💡 Key Decisions Needed

### 1. NLP Processing

- **Question:** Should we use Qwen2.5-7B or a smaller model (3B) for faster processing?
- **Current setup:** Qwen2.5-7B with 4-bit quantization
- **Trade-off:** Quality vs speed

### 2. Processing Location

- **Question:** Where to process the full 9.5M articles?
- **Options:**
  - **Local:** Slow but convenient (~8-12 days CPU only)
  - **Remote GPU:** Fast but requires setup (~1-2 days)
- **Recommendation:** Use remote server with GPU

### 3. Database Design

- **Question:** Should we partition the articles table by year or country?
- **Current recommendation:** Partition by year for better time-based queries
- **See:** `BACKEND_DESIGN.md` for full schema

### 4. Dashboard Priority

- **Question:** Which visualizations are most important?
- **Suggestions in priority order:**
  1. Articles count by country/partisan (bar charts)
  2. Articles over time (line chart with filters)
  3. Sentiment distribution by outlet
  4. Top categories by country
  5. Entity analysis (most mentioned people/orgs)
  6. Topic modeling visualization (later)

### 5. Category Refinement

- **Question:** Are the 10 categories appropriate for Nordic alternative media?
- **Current list:** See "News Categories" section above
- **Feedback needed:** Any categories to add/remove/modify?

---

## 📊 Data Quality Notes

From the test run (100 articles):

- **Match rate:** 64% of articles matched with actor data
  - This is expected since articles dataset (9.5M) comes from more domains than actor dataset (75 domains)
  - 36% of articles are from domains not in the actor list
  
- **Recommendation:** Consider expanding the actor dataset or flagging unmatched domains for review

---

## 🔧 Troubleshooting

### "python: command not found"
**Solution:** Use `python3` instead of `python`

### Out of memory during NLP processing
**Solutions:**
- Reduce batch size: `--batch-size 1`
- Use smaller model: `--model Qwen/Qwen2.5-3B-Instruct`
- Process on GPU server instead

### Slow processing
**Expected:** NLP processing is compute-intensive
- CPU only: ~1-2 minutes per article
- GPU (quantized): ~5-10 seconds per article
- For 9.5M articles, GPU server is strongly recommended

### spaCy model not found
```bash
python3 -m spacy download xx_ent_wiki_sm
```

---

## 📚 Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| `GETTING_STARTED.md` | Quick start guide (this file) | You (getting started) |
| `README_SETUP.md` | Detailed setup instructions | Setup & deployment |
| `STATUS_REPORT.md` | Comprehensive status report | Project overview |
| `BACKEND_DESIGN.md` | Database & API architecture | Backend development |

---

## 🎯 Success Criteria

### Phase 1: Preprocessing ✅
- [x] Data verification script working
- [x] Preprocessing script working
- [x] Test run successful (100 articles)
- [x] Actor data merged correctly

### Phase 2: NLP Processing ⏳
- [ ] NLP script tested on 100 articles
- [ ] Sentiment analysis validated
- [ ] Categories reviewed and adjusted if needed
- [ ] Larger sample processed (1K-10K articles)

### Phase 3: Database ⏳
- [ ] PostgreSQL schema created
- [ ] Test data loaded
- [ ] Query performance validated
- [ ] Update pipeline designed

### Phase 4: Backend ⏳
- [ ] FastAPI structure set up
- [ ] Basic endpoints working
- [ ] Caching implemented
- [ ] API documentation generated

### Phase 5: Frontend ⏳
- [ ] Streamlit app created
- [ ] Overview page complete
- [ ] Country-specific pages
- [ ] Search functionality

### Phase 6: Deployment ⏳
- [ ] Deployed to remote server
- [ ] Domain configured
- [ ] SSL enabled
- [ ] Monitoring set up

### Phase 7: Methods Paper ⏳
- [ ] Outline created
- [ ] Data collection section written
- [ ] Methodology documented
- [ ] Descriptive statistics compiled
- [ ] Draft complete

---

## 📞 Where to Get Help

- **Logs:** Check `preprocessing.log` for detailed execution logs
- **Data verification:** Run `python3 scripts/00_verify_data.py`
- **Test pipeline:** Run `python3 scripts/run_test_pipeline.py`

---

## 🎉 What's Working Right Now

✅ **Data verification** - All data files accessible and readable  
✅ **Basic preprocessing** - Merging, link extraction, word count  
✅ **Project structure** - All directories and files organized  
✅ **Documentation** - Comprehensive guides and design docs  
✅ **Dependencies** - Requirements file complete

**You're ready to proceed with NLP processing testing!**

---

## 📝 Recommended Next Command

```bash
# Install dependencies (if not done yet)
pip3 install transformers torch spacy accelerate bitsandbytes tqdm

# Download spaCy model
python3 -m spacy download xx_ent_wiki_sm

# Test NLP processing on 100 articles
python3 scripts/02_nlp_processing.py \
  --input data/processed/NAMO_preprocessed_test.parquet \
  --batch-size 4
```

This will take 10-30 minutes and show you if the NLP pipeline works correctly.

After this completes successfully, we can discuss:
1. Adjusting categories if needed
2. Processing a larger sample
3. Moving to database setup
4. Backend development

---

**Let me know when you're ready to proceed or if you have any questions!**

