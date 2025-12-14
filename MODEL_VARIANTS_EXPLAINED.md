# Model Variants Explained

## Key Differences

### 1. **mpasila/Viking-SlimInstruct-V1-7B**
- **Base model**: Viking-7B
- **Size**: 7B parameters
- **Training**: Uses same data as EuroLLM-Nordic-Instruct
- **Format**: ChatML format (standard chat template)
- **Type**: Full fine-tuned model
- **GPU Memory**: ~15GB

### 2. **mpasila/EuroLLM-Nordic-Instruct-9B**
- **Base model**: EuroLLM-9B
- **Size**: 9B parameters
- **Training**: Full fine-tuning on Nordic data
- **Format**: ChatML format
- **Type**: Full fine-tuned model
- **GPU Memory**: ~18GB

### 3. **mpasila/EuroLLM-Nordic-Instruct-LoRA-9B**
- **Base model**: EuroLLM-9B
- **Size**: 9B parameters (base) + small LoRA weights
- **Training**: LoRA (Low-Rank Adaptation) fine-tuning
- **Format**: ChatML format
- **Type**: LoRA adapter (requires base model)
- **GPU Memory**: ~18GB (base) + small LoRA weights

## What is LoRA?

**LoRA (Low-Rank Adaptation)** is a parameter-efficient fine-tuning method:

- ✅ **Smaller file size**: Only stores adapter weights (~100MB-1GB), not full model
- ✅ **Faster to download**: Just download adapter, reuse base model
- ✅ **Less storage**: Base model + adapter vs full fine-tuned model
- ✅ **Same performance**: Usually performs similarly to full fine-tuning
- ❌ **More complex**: Requires loading base model + adapter

**Full Fine-tuning**:
- Stores entire model weights (~14-18GB)
- Simpler to use (just load one model)
- Slightly easier to deploy

## What is ChatML?

**ChatML** is a message format used by many models:
- Uses `<|im_start|>` and `<|im_end|>` tokens
- Standard format: `<|im_start|>system\n...<|im_end|>\n<|im_start|>user\n...<|im_end|>\n<|im_start|>assistant\n`
- Our script already handles ChatML format automatically

## Which Should You Use?

### For Your Use Case (Category Classification):

**Option 1: EuroLLM-Nordic-Instruct-9B (Full Fine-tuned)** ⭐ **RECOMMENDED**
```bash
python3 scripts/26_category_classification_only.py \
  --input data/processed/test_100.parquet \
  --output data/nlp_enriched/test_100_categories.parquet \
  --model mpasila/EuroLLM-Nordic-Instruct-9B \
  --no-quantization
```
- ✅ Simplest to use (one model file)
- ✅ Full fine-tuning (best performance)
- ✅ 9B parameters (good quality)
- ✅ Nordic-specific training

**Option 2: Viking-SlimInstruct-V1-7B**
```bash
python3 scripts/26_category_classification_only.py \
  --input data/processed/test_100.parquet \
  --output data/nlp_enriched/test_100_categories.parquet \
  --model mpasila/Viking-SlimInstruct-V1-7B \
  --no-quantization
```
- ✅ Smaller (7B vs 9B) - needs less GPU memory (~15GB)
- ✅ Uses same Nordic training data
- ✅ ChatML format (our script handles this)

**Option 3: EuroLLM-Nordic-Instruct-LoRA-9B** (More Complex)
- Requires loading base model + LoRA adapter
- Our current script doesn't support LoRA loading
- Would need code changes to use this

## Recommendation

**Use `mpasila/EuroLLM-Nordic-Instruct-9B`**:
- Best performance (full fine-tuning)
- Easiest to use (one model)
- Nordic-specific
- No token required

**If GPU memory is limited (<18GB)**, use:
- `mpasila/Viking-SlimInstruct-V1-7B` (7B, ~15GB)

## Summary Table

| Model | Size | Type | GPU Memory | Ease of Use | Performance |
|-------|------|------|------------|-------------|-------------|
| **EuroLLM-Nordic-Instruct-9B** | 9B | Full fine-tuned | ~18GB | ⭐⭐⭐ Easy | ⭐⭐⭐ Best |
| **Viking-SlimInstruct-V1-7B** | 7B | Full fine-tuned | ~15GB | ⭐⭐⭐ Easy | ⭐⭐ Good |
| **EuroLLM-Nordic-Instruct-LoRA-9B** | 9B | LoRA adapter | ~18GB | ⭐ Complex | ⭐⭐ Good |

