#!/bin/bash
# Start Phase 1 with vLLM + Mistral-Small-3.1-24B

SESSION_NAME="nlp_vllm_phase1"
INPUT_FILE="data/NAMO_10pct_stratified.parquet"
OUTPUT_FILE="data/NAMO_10pct_vllm_enriched.parquet"
MODEL_NAME="mistralai/Mistral-Small-3.1-24B-Instruct-2503"
VLLM_BATCH_SIZE=16  # Process 16 articles in parallel
CHECKPOINT_INTERVAL=1000
LOG_FILE="logs/vllm_phase1_$(date +%Y%m%d_%H%M%S).log"

echo "=========================================="
echo "Starting NLP Phase 1 with vLLM"
echo "=========================================="
echo "Session name: $SESSION_NAME"
echo "Model: Mistral-Small-3.1-24B (vLLM)"
echo "Input: 81,272 articles (10% stratified sample)"
echo "vLLM batch size: $VLLM_BATCH_SIZE articles in parallel"
echo "Checkpoint: Every $CHECKPOINT_INTERVAL articles"
echo "Log file: /work/NAMO_nov25/$LOG_FILE"
echo ""

# Check GPU status
echo "Checking GPU..."
nvidia-smi --query-gpu=name,memory.used,memory.free --format=csv,noheader,nounits | awk 'NR==1{print "  GPU: " $0}'

# Create logs directory
mkdir -p logs

# Create tmux session and start processing
echo "Creating tmux session..."
tmux new-session -d -s $SESSION_NAME "cd /work/NAMO_nov25 && source venv/bin/activate && VLLM_WORKER_MULTIPROC_METHOD=spawn python3 scripts/03_nlp_vllm_batch.py --input $INPUT_FILE --output $OUTPUT_FILE --model '$MODEL_NAME' --vllm-batch-size $VLLM_BATCH_SIZE --checkpoint $CHECKPOINT_INTERVAL > $LOG_FILE 2>&1"

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
echo "Useful commands:"
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
echo "  Check progress:"
echo "    python3 -c 'import polars as pl; df = pl.read_parquet(\"$OUTPUT_FILE\"); print(f\"{len(df):,} / 81,272 ({100*len(df)/81272:.1f}%)\")'"
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
echo "Expected completion: ~6-8 hours (10-15x faster!)"
echo "=========================================="

