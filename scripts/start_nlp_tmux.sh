#!/bin/bash
# Start NLP processing in tmux for long-running execution
# Designed for 48-hour runs with monitoring and auto-resume

set -e

# Configuration
TMUX_SESSION="nlp_processing"
WORK_DIR="/home/frede/NAMO_nov25"
LOG_DIR="$WORK_DIR/logs"
SCRIPT="scripts/02_nlp_processing_from_db.py"
MODEL="mistralai/Mistral-7B-Instruct-v0.3"

# Processing parameters for 48-hour run
# At ~10 seconds per article, we can process ~17,280 articles in 48 hours
# Let's aim for 15,000 to be conservative (allows for slower articles)
TOTAL_ARTICLES=15000
CHUNK_SIZE=50  # Process and save every 50 articles

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Timestamp for this run
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/nlp_processing_${TIMESTAMP}.log"
MONITOR_LOG="$LOG_DIR/nlp_monitor_${TIMESTAMP}.log"

echo "=========================================="
echo "Starting NLP Processing in tmux"
echo "=========================================="
echo "Session name: $TMUX_SESSION"
echo "Total articles: $TOTAL_ARTICLES"
echo "Chunk size: $CHUNK_SIZE"
echo "Model: $MODEL"
echo "Log file: $LOG_FILE"
echo "Monitor log: $MONITOR_LOG"
echo ""

# Check if tmux session already exists
if tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
    echo "⚠️  tmux session '$TMUX_SESSION' already exists"
    echo ""
    echo "Options:"
    echo "  1. Attach to existing session: tmux attach -t $TMUX_SESSION"
    echo "  2. Kill and restart: tmux kill-session -t $TMUX_SESSION && $0"
    echo "  3. View logs: tail -f $LOG_DIR/nlp_processing_*.log"
    echo ""
    exit 1
fi

# Kill any existing NLP processing (clean slate)
echo "Checking for existing NLP processes..."
if pgrep -f "02_nlp_processing" > /dev/null; then
    echo "⚠️  Found existing NLP processing - killing..."
    pkill -f "02_nlp_processing" || true
    sleep 2
    echo "✅ Old NLP processes killed"
fi

echo "Current GPU usage:"
nvidia-smi --query-gpu=memory.used,memory.free,memory.total --format=csv,noheader | \
    awk -F', ' '{print "  Used: " $1 " | Free: " $2 " | Total: " $3}'
echo ""

# Create the tmux session and start processing
echo ""
echo "Creating tmux session and starting NLP processing..."
echo ""

# Create tmux session and start processing
tmux new-session -d -s "$TMUX_SESSION"

# Send commands to the tmux session
tmux send-keys -t "$TMUX_SESSION" "cd $WORK_DIR" C-m
tmux send-keys -t "$TMUX_SESSION" "echo 'NLP Processing Started: $(date)' | tee -a $LOG_FILE" C-m
tmux send-keys -t "$TMUX_SESSION" "python3 $SCRIPT --total-articles $TOTAL_ARTICLES --chunk-size $CHUNK_SIZE --model $MODEL 2>&1 | tee -a $LOG_FILE" C-m

# Give it a moment to start
sleep 2

# Check if session was created successfully
if tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
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
    echo "  View logs (last 50 lines):"
    echo "    tail -50 $LOG_FILE"
    echo ""
    echo "  Check session status:"
    echo "    tmux list-sessions"
    echo ""
    echo "  Monitor GPU usage:"
    echo "    watch -n 1 nvidia-smi"
    echo ""
    echo "  Kill session:"
    echo "    tmux kill-session -t $TMUX_SESSION"
    echo ""
    echo "=========================================="
    echo "Expected completion: ~42 hours (15,000 articles @ 10s each)"
    echo "=========================================="
    echo ""
else
    echo "❌ Failed to create tmux session"
    exit 1
fi

