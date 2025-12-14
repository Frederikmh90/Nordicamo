# Topic Modeling with mmBERT

## mmBERT: Modern Multilingual Encoder

**mmBERT** is an excellent choice for multilingual topic modeling:
- ✅ **Trained on 3T tokens** from **1800+ languages**
- ✅ **State-of-the-art (SoTA)** performance on benchmarks
- ✅ **Exceptional low-resource performance**
- ✅ **Perfect for Nordic languages**: Danish, Swedish, Norwegian, Finnish
- ✅ **Available models**: `mmBERT-base` and `mmBERT-small`

**Hugging Face**: https://huggingface.co/collections/jhu-clsp/mmbert-a-modern-multilingual-encoder-68b725831d7c6e3acc435ed4

---

## Implementation

### Updated Script

The topic modeling script (`scripts/15_topic_modeling_turftopic.py`) now:
1. **Prioritizes mmBERT** as the primary embedding model
2. **Falls back** to BGE-M3 or other models if mmBERT unavailable
3. **Handles mmBERT** models correctly (BERT architecture, not SentenceTransformer)
4. **Optimized for GPU** usage on remote server

### Model Priority Order

1. **`jhu-clsp/mmBERT-base`** ⭐ (Primary - Best performance)
2. **`jhu-clsp/mmBERT-small`** (If memory constrained)
3. **`BAAI/bge-m3`** (Fallback)
4. **`intfloat/multilingual-e5-base`** (Alternative fallback)

---

## Running on Remote GPU Server

### Quick Start

```bash
cd /Users/Codebase/projects/alterpublics/NAMO_nov25
source venv/bin/activate

# Run topic modeling on remote GPU server
python scripts/17_run_topic_modeling_remote.py \
  --input data/nlp_enriched/nlp_enriched_NAMO_preprocessed_test_final.parquet \
  --output data/topic_modeled/topics.parquet

# Or with sampling for testing
python scripts/17_run_topic_modeling_remote.py \
  --input data/nlp_enriched/nlp_enriched_NAMO_preprocessed_test_final.parquet \
  --output data/topic_modeled/topics_test.parquet \
  --sample-size 1000
```

### What the Script Does

1. ✅ **Connects** to remote GPU server (`212.27.13.34:2111`)
2. ✅ **Syncs** topic modeling script and data files
3. ✅ **Installs** dependencies (bertopic, transformers, mmBERT, etc.)
4. ✅ **Runs** topic modeling with mmBERT on GPU
5. ✅ **Downloads** results automatically

### Manual Remote Execution

If you prefer to run manually:

```bash
# SSH to remote server
ssh -p 2111 frede@212.27.13.34

# Navigate to project
cd ~/NAMO_nov25
source venv/bin/activate

# Install mmBERT dependencies
pip install transformers torch sentence-transformers bertopic

# Run topic modeling
python scripts/15_topic_modeling_turftopic.py \
  --input data/nlp_enriched/nlp_enriched_NAMO_preprocessed_test_final.parquet \
  --output data/topic_modeled/topics.parquet
```

---

## mmBERT Model Details

### mmBERT-base
- **Model**: `jhu-clsp/mmBERT-base`
- **Languages**: 1800+ languages including all Nordic languages
- **Training**: 3T tokens
- **Performance**: SoTA on multilingual benchmarks
- **Use case**: Best quality, requires more GPU memory

### mmBERT-small
- **Model**: `jhu-clsp/mmBERT-small`
- **Languages**: Same 1800+ languages
- **Use case**: Lower memory footprint, still excellent quality

---

## GPU Requirements

**Recommended GPU**: 
- NVIDIA GPU with 8GB+ VRAM (for mmBERT-base)
- NVIDIA GPU with 4GB+ VRAM (for mmBERT-small)

**The script automatically**:
- Detects GPU availability
- Uses GPU if available (`cuda`)
- Falls back to CPU if needed
- Uses mixed precision (float16) for efficiency

---

## Expected Performance

With mmBERT:
- ✅ **Better topic quality** for Nordic languages
- ✅ **More coherent topics** due to superior embeddings
- ✅ **Handles code-switching** (mixing languages)
- ✅ **Low-resource language support** (Finnish benefits especially)

---

## Next Steps

1. ✅ **Run topic modeling** on remote GPU server
2. ✅ **Download results** (automatic with script)
3. ✅ **Load into database** using `scripts/16_add_topics_to_database.py`
4. 🎯 **Visualize topics** in dashboard

---

## Troubleshooting

**mmBERT not loading:**
- Check GPU memory: `nvidia-smi`
- Try mmBERT-small if base doesn't fit
- Ensure transformers library is up to date

**Out of memory:**
- Use `--sample-size` to process fewer articles
- Process countries separately
- Use mmBERT-small instead of base

**Slow performance:**
- Ensure GPU is being used (check logs)
- Increase batch size if memory allows
- Process countries in parallel if possible

---

**mmBERT is now configured as the primary embedding model!** 🚀

Run `python scripts/17_run_topic_modeling_remote.py` to start topic modeling on your GPU server.

