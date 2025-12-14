#!/bin/bash
# Automated Two-Phase NLP Processing
# Phase 1: 10% sample → saved separately
# Phase 2: Remaining 90% → continues automatically

SESSION_NAME="nlp_vllm_full"
FULL_DATASET="data/NAMO_950k.parquet"
SAMPLE_10PCT="data/NAMO_10pct_stratified.parquet"
OUTPUT_10PCT="data/NAMO_10pct_enriched.parquet"
OUTPUT_FULL="data/NAMO_950k_enriched.parquet"
MODEL_NAME="mistralai/Mistral-Small-3.1-24B-Instruct-2503"
VLLM_BATCH_SIZE=16
CHECKPOINT_INTERVAL=1000
LOG_FILE="logs/vllm_full_run_$(date +%Y%m%d_%H%M%S).log"

echo "=========================================="
echo "Two-Phase Automated NLP Processing"
echo "=========================================="
echo "Session name: $SESSION_NAME"
echo "Model: Mistral-Small-3.1-24B (vLLM)"
echo ""
echo "Phase 1: 10% sample (81,272 articles)"
echo "  → Output: $OUTPUT_10PCT"
echo "  → Time: ~2-2.5 hours"
echo ""
echo "Phase 2: Remaining 90% (870,000 articles)"
echo "  → Output: $OUTPUT_FULL"
echo "  → Time: ~3-4 days"
echo ""
echo "Total articles: ~950,000"
echo "vLLM batch size: $VLLM_BATCH_SIZE articles in parallel"
echo "Checkpoint: Every $CHECKPOINT_INTERVAL articles"
echo "Log file: /work/NAMO_nov25/$LOG_FILE"
echo ""

# Check GPU status
echo "Checking GPU..."
nvidia-smi --query-gpu=name,memory.used,memory.free --format=csv,noheader,nounits | awk 'NR==1{print "  GPU: " $0}'

# Check if files exist
echo ""
echo "Checking input files..."
if [ ! -f "$FULL_DATASET" ]; then
    echo "❌ ERROR: $FULL_DATASET not found!"
    exit 1
fi
if [ ! -f "$SAMPLE_10PCT" ]; then
    echo "❌ ERROR: $SAMPLE_10PCT not found!"
    exit 1
fi
echo "✓ Input files found"

# Create logs directory
mkdir -p logs

# Create tmux session and start processing
echo ""
echo "Creating tmux session..."
tmux new-session -d -s $SESSION_NAME "cd /work/NAMO_nov25 && source venv/bin/activate && VLLM_WORKER_MULTIPROC_METHOD=spawn python3 scripts/04_nlp_vllm_two_phase.py --full-dataset '$FULL_DATASET' --sample-10pct '$SAMPLE_10PCT' --output-10pct '$OUTPUT_10PCT' --output-full '$OUTPUT_FULL' --model '$MODEL_NAME' --vllm-batch-size $VLLM_BATCH_SIZE --checkpoint $CHECKPOINT_INTERVAL > $LOG_FILE 2>&1"

if [ $? -eq 0 ]; then
    echo "✅ tmux session created successfully"
else
    echo "❌ Failed to create tmux session. Check for existing sessions or errors."
    exit 1
fi

echo ""
echo "=========================================="
echo "Session is running in background"
echo "=========================================="
echo ""
echo "📊 PROGRESS TRACKING:"
echo ""
echo "  Phase 1 (10%):"
echo "    python3 -c 'import polars as pl; df = pl.read_parquet(\"$OUTPUT_10PCT\"); print(f\"{len(df):,} / 81,272 ({100*len(df)/81272:.1f}%)\")'"
echo ""
echo "  Phase 2 (Full):"
echo "    python3 -c 'import polars as pl; df = pl.read_parquet(\"$OUTPUT_FULL\"); print(f\"{len(df):,} / 950,000 ({100*len(df)/950000:.1f}%)\")'"
echo ""
echo "📋 USEFUL COMMANDS:"
echo ""
echo "  Attach to session:"
echo "    tmux attach -t $SESSION_NAME"
echo ""
echo "  Detach from session:"
echo "    Press: Ctrl+B, then D"
echo ""
echo "  View logs (live):"
echo "    tail -f $LOG_FILE"
echo ""
echo "  Check session status:"
echo "    tmux list-sessions"
echo ""
echo "  Check GPU:"
echo "    nvidia-smi"
echo ""
echo "  Kill session:"
echo "    tmux kill-session -t $SESSION_NAME"
echo ""
echo "=========================================="
echo "⏱️  EXPECTED TIMELINE:"
echo "=========================================="
echo ""
echo "  Phase 1: ~2-2.5 hours"
echo "  Phase 2: ~3-4 days"
echo "  Total:   ~3-4 days"
echo ""
echo "🌙 This will run overnight and continue automatically!"
echo ""
echo "=========================================="

