# NLP Processing Performance Analysis

## Why is it slow? (~24 seconds per article)

### Current Architecture Issues

1. **Sequential Processing (One at a Time)**
   - The script processes articles **one by one** in a loop (line 779 in `02_nlp_processing.py`)
   - Each article requires:
     - Tokenization (~0.1s)
     - LLM generation (~20-25s) - **BOTTLENECK**
     - JSON parsing (~0.1s)
     - Entity extraction (~0.5s)
   - **Total: ~24s per article**

2. **LLM Generation is the Bottleneck**
   - Mistral 7B generates ~200 tokens per article
   - With `max_new_tokens=200`, each generation takes ~20-25 seconds
   - This is **sequential** - can't parallelize easily without multiple GPUs

3. **No True Batching**
   - The `batch_size` parameter in the script doesn't actually batch LLM calls
   - It just processes multiple articles in a loop
   - Each article still makes a separate LLM API call

### Why Not Faster?

**GPU Utilization:**
- GPU is mostly idle between articles
- Model stays loaded in memory (good!)
- But generation happens one request at a time

**Possible Optimizations:**

1. **True Batching** (if model supports it)
   - Process 4-8 articles simultaneously
   - Requires modifying the generation code
   - Could reduce time to ~6-8s per article (4x speedup)

2. **Smaller Model**
   - Use Mistral 7B quantized (4-bit) - faster generation
   - Or use a smaller model like Mistral 3B
   - Trade-off: slightly lower quality

3. **vLLM with Continuous Batching**
   - vLLM can batch multiple requests automatically
   - But we hit memory limits with 24B model
   - Mistral 7B with vLLM could work better

4. **API-based Solution**
   - Use OpenAI/Anthropic API (faster, but costs money)
   - Or use a dedicated inference server

### Current Performance Breakdown (After Optimization - No Reasoning)

```
Per Article (optimized, ~12-15s each):
├── Load model: 8s (one-time)
├── Tokenization: 0.1s
├── LLM Generation: 10-12s (reduced from 20-25s by removing reasoning)
├── JSON Parsing: 0.1s
└── Entity Extraction: 0.5s
```

**For 1000 articles:**
- Estimated time: ~3.3-4.2 hours (12-15s × 1000)
- With 2s delay between chunks: +20 minutes
- **Total: ~3.5-4.5 hours** (40-50% faster!)

### Previous Performance (Before Optimization)

```
Per Article (with reasoning, ~24s each):
├── Load model: 8s (one-time)
├── Tokenization: 0.1s
├── LLM Generation: 20-25s (BOTTLENECK - included reasoning field)
├── JSON Parsing: 0.1s
└── Entity Extraction: 0.5s
```

**For 1000 articles:**
- Estimated time: ~6.7 hours (24s × 1000)
- With 2s delay between chunks: +20 minutes
- **Total: ~7 hours**

### Recommendations

1. **For now:** Use batch processing script to process in chunks
   - Process 100 articles at a time
   - Save progress after each chunk
   - Can resume if interrupted

2. **Short-term:** Already optimized! ✅
   - Removed "reasoning" field (saves ~50-150 tokens)
   - Reduced `max_new_tokens` from 200 to 100
   - **Current speed: ~12-15s/article**
   - **Total for 1000: ~3.5-4.5 hours**

3. **Further optimization:** Use quantization
   - Use `--use-quantization` flag
   - Should reduce generation time to ~8-10s/article
   - **Total for 1000: ~2.5-3 hours**

3. **Long-term:** Switch to vLLM with proper batching
   - Or use API-based solution for production

