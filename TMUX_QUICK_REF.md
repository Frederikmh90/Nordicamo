# Phase 1 Running in tmux - Quick Reference

## ✅ Started in tmux session: `nlp_phase1`

### Configuration
- **Articles**: 81,272 (10% stratified from 57 outlets)
- **Batch size**: 1000
- **Checkpoint**: Every 1000 articles
- **Log**: `/work/NAMO_nov25/logs/nlp_phase1_20251213_233924.log`
- **Time**: ~1-2 days

---

## 🎮 tmux Commands

### Attach to session (watch live)
```bash
ssh -p 2693 ucloud@ssh.cloud.sdu.dk
tmux attach -t nlp_phase1
```

### Detach from session (without stopping it)
Press: `Ctrl+B`, then `D`

### Check if running
```bash
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "tmux list-sessions"
```

### Kill session (stop processing)
```bash
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "tmux kill-session -t nlp_phase1"
```

---

## 📊 Monitoring (Without Attaching)

### Check progress
```bash
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "cd /work/NAMO_nov25 && source venv/bin/activate && python3 -c 'import polars as pl; df = pl.read_parquet(\"data/NAMO_10pct_enriched.parquet\"); print(f\"{len(df):,} / 81,272 ({100*len(df)/81272:.1f}%)\")' 2>/dev/null || echo 'No checkpoint yet'"
```

### View logs (last 20 lines)
```bash
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "tail -20 /work/NAMO_nov25/logs/nlp_phase1_*.log"
```

### Watch logs (live)
```bash
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "tail -f /work/NAMO_nov25/logs/nlp_phase1_*.log"
```

### Check GPU
```bash
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "nvidia-smi"
```

### Check process
```bash
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "ps aux | grep 02_nlp_batch_resume | grep -v grep"
```

---

## 🔄 Resume After Stop

If the process stops (or you kill the session), just rerun:

```bash
ssh -p 2693 ucloud@ssh.cloud.sdu.dk
cd /work/NAMO_nov25
./scripts/start_phase1_tmux.sh
```

The script will automatically resume from the last checkpoint!

---

## 📥 Download Results

When complete (or for partial results):

```bash
scp -P 2693 ucloud@ssh.cloud.sdu.dk:/work/NAMO_nov25/data/NAMO_10pct_enriched.parquet \
    ./data/nlp_enriched/NAMO_10pct_enriched_$(date +%Y%m%d).parquet
```

---

## ⏱️ Expected Timeline

- **First checkpoint**: ~15 minutes (1000 articles)
- **10,000 articles**: ~3 hours
- **Complete (81,272)**: ~1-2 days

---

## 🆘 If Something Goes Wrong

### Session died
```bash
# Check logs for errors
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "tail -50 /work/NAMO_nov25/logs/nlp_phase1_*.log"

# Restart
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "cd /work/NAMO_nov25 && ./scripts/start_phase1_tmux.sh"
```

### Can't attach (session not found)
```bash
# List sessions
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "tmux list-sessions"

# If none exist, restart
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "cd /work/NAMO_nov25 && ./scripts/start_phase1_tmux.sh"
```

