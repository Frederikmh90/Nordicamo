#!/bin/bash
# Start NLP Phase 1 in tmux

WORK_DIR="/work/NAMO_nov25"
TMUX_SESSION="nlp_phase1"
SCRIPT="scripts/02_nlp_batch_resume.py"
INPUT="data/NAMO_10pct_stratified.parquet"
OUTPUT="data/NAMO_10pct_enriched.parquet"
MODEL="mistralai/Mistral-7B-Instruct-v0.3"
BATCH_SIZE=1000
CHECKPOINT=1000
LOG_FILE="$WORK_DIR/logs/nlp_phase1_$(date +%Y%m%d_%H%M%S).log"

echo "=========================================="
echo "Starting NLP Phase 1 in tmux"
echo "=========================================="
echo "Session name: $TMUX_SESSION"
echo "Input: 81,272 articles (10% stratified sample)"
echo "Batch size: $BATCH_SIZE"
echo "Checkpoint: Every $CHECKPOINT articles"
echo "Model: $MODEL"
echo "Log file: $LOG_FILE"
echo ""

# Check if session already exists
if tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
    echo "⚠️  Session '$TMUX_SESSION' already exists!"
    echo "   Attach with: tmux attach -t $TMUX_SESSION"
    echo "   Or kill it with: tmux kill-session -t $TMUX_SESSION"
    exit 1
fi

# Check GPU
echo "Checking GPU..."
nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader | \
    awk -F', ' '{print "  Used: "$1" | Free: "$2}'
echo ""

# Create tmux session
echo "Creating tmux session..."
tmux new-session -d -s "$TMUX_SESSION"

# Send commands to tmux
tmux send-keys -t "$TMUX_SESSION" "cd $WORK_DIR" C-m
tmux send-keys -t "$TMUX_SESSION" "source venv/bin/activate" C-m
tmux send-keys -t "$TMUX_SESSION" "echo 'Starting NLP Phase 1: $(date)' | tee -a $LOG_FILE" C-m
tmux send-keys -t "$TMUX_SESSION" "python3 $SCRIPT --input $INPUT --output $OUTPUT --model $MODEL --batch-size $BATCH_SIZE --checkpoint $CHECKPOINT 2>&1 | tee -a $LOG_FILE" C-m

echo "✅ tmux session created successfully"
echo ""
echo "=========================================="
echo "Session is running in background"
echo "=========================================="
echo ""
echo "Useful commands:"
echo ""
echo "  Attach to session:"
echo "    tmux attach -t $TMUX_SESSION"
echo ""
echo "  Detach from session:"
echo "    Press: Ctrl+B, then D"
echo ""
echo "  View logs (live):"
echo "    tail -f $LOG_FILE"
echo ""
echo "  Check progress:"
echo "    python3 -c 'import polars as pl; df = pl.read_parquet(\"$OUTPUT\"); print(f\"{len(df):,} / 81,272\")'"
echo ""
echo "  Check session status:"
echo "    tmux list-sessions"
echo ""
echo "  Check GPU:"
echo "    nvidia-smi"
echo ""
echo "  Kill session:"
echo "    tmux kill-session -t $TMUX_SESSION"
echo ""
echo "=========================================="
echo "Expected completion: ~1-2 days"
echo "=========================================="
echo ""

