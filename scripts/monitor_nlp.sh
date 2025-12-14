#!/bin/bash
# Monitor NLP processing progress
# Run this to check status during the 48-hour processing

set -e

WORK_DIR="/home/frede/NAMO_nov25"
LOG_DIR="$WORK_DIR/logs"

echo "=========================================="
echo "NLP Processing Monitor"
echo "=========================================="
echo ""

# Check if tmux session exists
if tmux has-session -t nlp_processing 2>/dev/null; then
    echo "✅ tmux session 'nlp_processing' is running"
else
    echo "❌ tmux session 'nlp_processing' is NOT running"
fi

echo ""

# GPU status
echo "GPU Status:"
echo "----------"
nvidia-smi --query-gpu=utilization.gpu,utilization.memory,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits | \
    awk -F', ' '{printf "  GPU Util: %s%% | Mem Util: %s%% | Mem Used: %sMB / %sMB | Temp: %s°C\n", $1, $2, $3, $4, $5}'

echo ""

# Database status
echo "Database Progress:"
echo "-----------------"
cd "$WORK_DIR"
python3 << 'EOF'
import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        dbname=os.getenv('DB_NAME')
    )
    cur = conn.cursor()
    
    # Total counts
    cur.execute("SELECT COUNT(*) FROM articles")
    total = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM articles WHERE nlp_processed_at IS NOT NULL")
    processed = cur.fetchone()[0]
    
    unprocessed = total - processed
    percent = (processed / total * 100) if total > 0 else 0
    
    print(f"  Total articles: {total:,}")
    print(f"  Processed: {processed:,} ({percent:.2f}%)")
    print(f"  Unprocessed: {unprocessed:,}")
    
    # Recent processing rate (last hour)
    cur.execute("""
        SELECT COUNT(*) FROM articles 
        WHERE nlp_processed_at > NOW() - INTERVAL '1 hour'
    """)
    last_hour = cur.fetchone()[0]
    
    if last_hour > 0:
        print(f"\n  Processing rate (last hour): {last_hour} articles")
        rate_per_sec = last_hour / 3600
        print(f"  Average: {3600/last_hour:.1f} seconds per article")
        
        # Estimate remaining time
        if rate_per_sec > 0:
            remaining_seconds = unprocessed / rate_per_sec
            remaining_hours = remaining_seconds / 3600
            print(f"  Estimated time remaining: {remaining_hours:.1f} hours")
    
    # Recent processing activity
    cur.execute("""
        SELECT 
            MAX(nlp_processed_at) as last_processed,
            MIN(nlp_processed_at) as first_processed
        FROM articles 
        WHERE nlp_processed_at IS NOT NULL
    """)
    result = cur.fetchone()
    if result[0]:
        print(f"\n  First processed: {result[1]}")
        print(f"  Last processed: {result[0]}")
        
        # Time since last update
        now = datetime.now(result[0].tzinfo) if result[0].tzinfo else datetime.now()
        time_since = now - result[0]
        if time_since.total_seconds() < 3600:
            print(f"  Time since last: {int(time_since.total_seconds())} seconds ago")
        else:
            print(f"  Time since last: {time_since.total_seconds()/3600:.1f} hours ago")
    
    conn.close()
except Exception as e:
    print(f"  ❌ Error connecting to database: {e}")
EOF

echo ""

# Latest log file
echo "Latest Log Entries:"
echo "------------------"
LATEST_LOG=$(ls -t "$LOG_DIR"/nlp_processing_*.log 2>/dev/null | head -1)
if [ -f "$LATEST_LOG" ]; then
    echo "  Log file: $LATEST_LOG"
    echo ""
    tail -20 "$LATEST_LOG" | sed 's/^/  /'
else
    echo "  No log files found"
fi

echo ""
echo "=========================================="
echo ""
echo "To view live logs: tail -f $LOG_DIR/nlp_processing_*.log"
echo "To attach to session: tmux attach -t nlp_processing"
echo ""


