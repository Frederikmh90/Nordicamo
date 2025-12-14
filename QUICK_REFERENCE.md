# Quick Reference - NLP Processing

## 🎯 Current Status

✅ **48-hour run is ACTIVE**  
✅ Processing 15,000 articles  
✅ Started: Dec 12, 2025 at 23:54:33  
✅ Expected completion: ~42 hours

---

## 📊 One-Line Status Check

```bash
ssh namo-server "cd /home/frede/NAMO_nov25 && ./scripts/monitor_nlp.sh"
```

---

## 🔍 Essential Commands

### Monitor Progress
```bash
# Detailed status
ssh namo-server "cd /home/frede/NAMO_nov25 && ./scripts/monitor_nlp.sh"

# Quick count
ssh namo-server "cd /home/frede/NAMO_nov25 && python3 -c 'import os; from dotenv import load_dotenv; import psycopg2; load_dotenv(); conn = psycopg2.connect(host=os.getenv(\"DB_HOST\"), port=os.getenv(\"DB_PORT\"), user=os.getenv(\"DB_USER\"), password=os.getenv(\"DB_PASSWORD\"), dbname=os.getenv(\"DB_NAME\")); cur = conn.cursor(); cur.execute(\"SELECT COUNT(*) FROM articles WHERE nlp_processed_at IS NOT NULL\"); print(f\"Processed: {cur.fetchone()[0]:,}\"); conn.close()'"

# Live logs
ssh namo-server "tail -f /home/frede/NAMO_nov25/logs/nlp_processing_20251212_235427.log"

# GPU status
ssh namo-server "nvidia-smi"
```

### Control tmux Session
```bash
# List sessions
ssh namo-server "tmux list-sessions"

# Attach to view progress
ssh namo-server "tmux attach -t nlp_processing"
# (Detach: Ctrl+B, then D)

# Kill session
ssh namo-server "tmux kill-session -t nlp_processing"
```

### Restart if Needed
```bash
ssh namo-server "cd /home/frede/NAMO_nov25 && ./scripts/start_nlp_tmux.sh"
```

---

## 📁 Important Files

- `48_HOUR_RUN_GUIDE.md` - Complete guide
- `RUN_STATUS.md` - Current run status
- `scripts/start_nlp_tmux.sh` - Start script
- `scripts/monitor_nlp.sh` - Monitoring script
- `scripts/02_nlp_processing_from_db.py` - Main processing script
- `logs/nlp_processing_20251212_235427.log` - Current log file

---

## ⚡ Quick Checks

### Is it running?
```bash
ssh namo-server "tmux has-session -t nlp_processing && echo '✅ Running' || echo '❌ Not running'"
```

### How many processed?
```bash
ssh namo-server "cd /home/frede/NAMO_nov25 && python3 -c 'import os; from dotenv import load_dotenv; import psycopg2; load_dotenv(); conn = psycopg2.connect(host=os.getenv(\"DB_HOST\"), port=os.getenv(\"DB_PORT\"), user=os.getenv(\"DB_USER\"), password=os.getenv(\"DB_PASSWORD\"), dbname=os.getenv(\"DB_NAME\")); cur = conn.cursor(); cur.execute(\"SELECT COUNT(*) FROM articles WHERE nlp_processed_at IS NOT NULL\"); print(f\"{cur.fetchone()[0]:,} / 15,000\"); conn.close()'"
```

### GPU memory?
```bash
ssh namo-server "nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader"
```

---

## 🎓 Understanding the Output

**Log format:**
- `Chunk X/300` - Progress through chunks
- `✅ Successfully parsed JSON` - Article processed successfully
- `Saved X articles to database` - Progress saved

**Processing rate:**
- Initial: ~15 seconds per article (model loading)
- Steady state: ~10-12 seconds per article

**Progress tracking:**
- Every 50 articles = 1 chunk
- 300 chunks = 15,000 articles
- Auto-saves every chunk (never lose progress)

---

## 🔄 Auto-Resume Feature

If processing stops for any reason:
1. Restart with the same command
2. Script queries database for unprocessed articles
3. Automatically skips already-processed ones
4. Continues from where it left off

**You can never lose progress!**

---

## 📞 Need Help?

1. Check `48_HOUR_RUN_GUIDE.md` for detailed troubleshooting
2. Check logs: `/home/frede/NAMO_nov25/logs/`
3. Monitor script: `./scripts/monitor_nlp.sh`

---

**The run is active - you can safely disconnect!** 🚀


