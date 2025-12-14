
# 48-Hour NLP Processing Run - Complete Guide

## Current Status

**Server:** dmlbeast (212.27.13.34:2111)  
**GPU:** NVIDIA RTX 4090 (24GB) with ~22.5GB available  
**Database:** PostgreSQL with 114,009 unprocessed articles  
**Expected Processing:** ~15,000 articles in 48 hours (~10 seconds per article)

---

## 🚀 Quick Start

### Step 1: SSH into Server
```bash
ssh namo-server
# Or: ssh -p 2111 frede@212.27.13.34
```

### Step 2: Start Processing
```bash
cd /home/frede/NAMO_nov25
./scripts/start_nlp_tmux.sh
```

### Step 3: Detach and Let It Run
- Press `Ctrl+B`, then `D` to detach from tmux
- Processing will continue in background for 48 hours

---

## 📊 Monitoring Progress

### Check Status
```bash
# From your local machine (no SSH needed)
ssh namo-server "cd /home/frede/NAMO_nov25 && ./scripts/monitor_nlp.sh"

# Or on the server
cd /home/frede/NAMO_nov25
./scripts/monitor_nlp.sh
```

### View Live Logs
```bash
ssh namo-server "tail -f /home/frede/NAMO_nov25/logs/nlp_processing_*.log"
```

### Check GPU Usage
```bash
ssh namo-server "watch -n 2 nvidia-smi"
```

### Attach to tmux Session
```bash
ssh namo-server
tmux attach -t nlp_processing
# Detach: Ctrl+B, then D
```

---

## ⚙️ Configuration

### Current Settings
- **Total articles:** 15,000 (conservative for 48-hour window)
- **Chunk size:** 50 (saves progress every 50 articles)
- **Model:** Mistral-7B-Instruct-v0.3
- **Processing rate:** ~10 seconds per article
- **Expected completion:** ~42 hours

### Auto-Resume Feature
The script queries the database for unprocessed articles, so if it stops:
1. It will automatically skip already-processed articles
2. You can restart with the same command
3. Progress is never lost (saved every 50 articles)

---

## 🔧 Troubleshooting

### If Processing Stops

1. **Check if session is still running:**
   ```bash
   ssh namo-server "tmux list-sessions"
   ```

2. **Check for errors in logs:**
   ```bash
   ssh namo-server "tail -50 /home/frede/NAMO_nov25/logs/nlp_processing_*.log"
   ```

3. **Check GPU processes:**
   ```bash
   ssh namo-server "nvidia-smi"
   ```

4. **Restart if needed:**
   ```bash
   ssh namo-server "cd /home/frede/NAMO_nov25 && tmux kill-session -t nlp_processing && ./scripts/start_nlp_tmux.sh"
   ```

### If GPU is Full

This is a shared server. Check for other processes:
```bash
ssh namo-server "nvidia-smi"
```

If needed, kill your own processes:
```bash
ssh namo-server "pkill -f '02_nlp_processing'"
```

**Note:** Don't kill other users' processes (e.g., jakobbaek's Streamlit app).

### If SSH Connection Drops

The processing continues in tmux even if you disconnect. Just reconnect:
```bash
ssh namo-server
tmux attach -t nlp_processing
```

---

## 📈 Expected Progress

### Timeline (15,000 articles @ 10 seconds each)

| Time Elapsed | Articles Processed | Articles Remaining | Progress |
|-------------|-------------------|-------------------|----------|
| 6 hours     | ~2,160            | ~12,840           | 14%      |
| 12 hours    | ~4,320            | ~10,680           | 29%      |
| 24 hours    | ~8,640            | ~6,360            | 58%      |
| 36 hours    | ~12,960           | ~2,040            | 86%      |
| 42 hours    | ~15,000           | 0                 | 100%     |

### Database Progress
```bash
# Check from command line
ssh namo-server "cd /home/frede/NAMO_nov25 && python3 -c '
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
conn = psycopg2.connect(
    host=os.getenv(\"DB_HOST\"),
    port=os.getenv(\"DB_PORT\"),
    user=os.getenv(\"DB_USER\"),
    password=os.getenv(\"DB_PASSWORD\"),
    dbname=os.getenv(\"DB_NAME\")
)
cur = conn.cursor()
cur.execute(\"SELECT COUNT(*) FROM articles WHERE nlp_processed_at IS NOT NULL\")
print(f\"Processed: {cur.fetchone()[0]:,} articles\")
conn.close()
'"
```

---

## 🛑 Stopping the Processing

### Graceful Stop
```bash
ssh namo-server "tmux send-keys -t nlp_processing C-c"
```

### Force Stop
```bash
ssh namo-server "tmux kill-session -t nlp_processing"
```

### Emergency Kill
```bash
ssh namo-server "pkill -9 -f '02_nlp_processing'"
```

---

## 🔄 Continuing After Stop

If processing stops for any reason, simply restart:

```bash
ssh namo-server
cd /home/frede/NAMO_nov25
./scripts/start_nlp_tmux.sh
```

The script will automatically:
- ✅ Skip already-processed articles
- ✅ Continue from where it left off
- ✅ Process remaining articles up to the total limit

---

## 📝 Log Files

All logs are saved in `/home/frede/NAMO_nov25/logs/`:
- `nlp_processing_YYYYMMDD_HHMMSS.log` - Main processing log
- Logs include timestamps, progress, and any errors

### View All Logs
```bash
ssh namo-server "ls -lh /home/frede/NAMO_nov25/logs/"
```

### View Latest Log
```bash
ssh namo-server "tail -50 \$(ls -t /home/frede/NAMO_nov25/logs/nlp_processing_*.log | head -1)"
```

---

## 🎯 After Completion

### Verify Results
```bash
ssh namo-server "cd /home/frede/NAMO_nov25 && python3 -c '
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
conn = psycopg2.connect(
    host=os.getenv(\"DB_HOST\"),
    port=os.getenv(\"DB_PORT\"),
    user=os.getenv(\"DB_USER\"),
    password=os.getenv(\"DB_PASSWORD\"),
    dbname=os.getenv(\"DB_NAME\")
)
cur = conn.cursor()

# Total processed
cur.execute(\"SELECT COUNT(*) FROM articles WHERE nlp_processed_at IS NOT NULL\")
processed = cur.fetchone()[0]

# Sentiment distribution
cur.execute(\"SELECT sentiment, COUNT(*) FROM articles WHERE sentiment IS NOT NULL GROUP BY sentiment ORDER BY sentiment\")
sentiments = cur.fetchall()

# Category distribution (top 5)
cur.execute(\"SELECT jsonb_array_elements_text(categories) as category, COUNT(*) FROM articles WHERE categories IS NOT NULL GROUP BY category ORDER BY COUNT(*) DESC LIMIT 5\")
categories = cur.fetchall()

print(f\"Total Processed: {processed:,} articles\")
print(f\"\nSentiment Distribution:\")
for sent, count in sentiments:
    print(f\"  {sent}: {count:,}\")
    
print(f\"\nTop 5 Categories:\")
for cat, count in categories:
    print(f\"  {cat}: {count:,}\")

conn.close()
'"
```

### Clean Up
```bash
# Kill the tmux session
ssh namo-server "tmux kill-session -t nlp_processing"

# Optionally compress old logs
ssh namo-server "cd /home/frede/NAMO_nov25/logs && gzip nlp_processing_*.log"
```

---

## 📞 Contact & Support

### If Something Goes Wrong
1. Check the logs first
2. Check the monitoring output
3. Verify GPU status
4. Check database connectivity
5. Restart the process

### Server Maintenance
- Server may require reboot (notice: "System restart required")
- After reboot, you'll need to:
  1. Start PostgreSQL container: `docker start namo-pg`
  2. Restart NLP processing: `./scripts/start_nlp_tmux.sh`

---

## 🎊 Success Criteria

After 48 hours, you should have:
- ✅ ~15,000 articles processed with sentiment analysis
- ✅ ~15,000 articles categorized
- ✅ ~15,000 articles with named entity recognition
- ✅ All data saved in PostgreSQL database
- ✅ Progress logged and verifiable
- ✅ Auto-resume capability for remaining articles

---

## ⚡ Quick Reference Commands

```bash
# Start processing
ssh namo-server "cd /home/frede/NAMO_nov25 && ./scripts/start_nlp_tmux.sh"

# Check status
ssh namo-server "cd /home/frede/NAMO_nov25 && ./scripts/monitor_nlp.sh"

# View logs
ssh namo-server "tail -f /home/frede/NAMO_nov25/logs/nlp_processing_*.log"

# Attach to session
ssh namo-server "tmux attach -t nlp_processing"

# Stop processing
ssh namo-server "tmux kill-session -t nlp_processing"

# Check GPU
ssh namo-server "nvidia-smi"

# Database count
ssh namo-server "cd /home/frede/NAMO_nov25 && python3 -c 'import os; from dotenv import load_dotenv; import psycopg2; load_dotenv(); conn = psycopg2.connect(host=os.getenv(\"DB_HOST\"), port=os.getenv(\"DB_PORT\"), user=os.getenv(\"DB_USER\"), password=os.getenv(\"DB_PASSWORD\"), dbname=os.getenv(\"DB_NAME\")); cur = conn.cursor(); cur.execute(\"SELECT COUNT(*) FROM articles WHERE nlp_processed_at IS NOT NULL\"); print(f\"Processed: {cur.fetchone()[0]:,}\"); conn.close()'"
```

---

**Good luck with your 48-hour run! 🚀**


