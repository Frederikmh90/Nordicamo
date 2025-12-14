# PostgreSQL Setup Without Sudo - Solutions

## Current Situation

- ❌ Cannot start PostgreSQL service (requires sudo)
- ❌ Cannot use Docker (user not in docker group)
- ❌ Cannot access existing PostgreSQL instance
- ✅ Docker is installed on server
- ✅ Scripts are ready

---

## ✅ Recommended Solution: Request Docker Access

**This is a one-time request to your system administrator:**

```bash
sudo usermod -aG docker frede
```

**After this, you can:**
1. Log out and log back in (or run `newgrp docker`)
2. Run: `python scripts/13_setup_postgresql_docker_python.py`
3. PostgreSQL will be running in Docker (no sudo needed)

**Why this is best:**
- ✅ Full control over your database
- ✅ No sudo needed after initial setup
- ✅ Easy to restart/recreate
- ✅ Isolated environment

---

## Alternative: Use Cloud PostgreSQL (No Admin Needed)

### Option A: Supabase (Free Tier - 500MB)

1. **Sign up:** https://supabase.com
2. **Create project** → Get connection string
3. **Update scripts to use cloud database:**

```bash
python scripts/03_create_database_schema.py \
  --create-db \
  --host db.xxxxx.supabase.co \
  --user postgres \
  --password YOUR_PASSWORD \
  --database postgres
```

**Pros:** Free, no setup, accessible from anywhere  
**Cons:** Limited storage (500MB), requires internet

---

### Option B: Neon (Free Tier - 3GB)

1. **Sign up:** https://neon.tech
2. **Create project** → Get connection string
3. **Use same scripts with cloud host**

**Pros:** More storage (3GB), good performance  
**Cons:** Requires internet

---

## Alternative: Run PostgreSQL Locally (Your Mac)

**Set up PostgreSQL on your local machine:**

```bash
# Install PostgreSQL
brew install postgresql@14

# Start PostgreSQL
brew services start postgresql@14

# Create database
createdb namo_db

# Create schema
cd /Users/Codebase/projects/alterpublics/NAMO_nov25
source venv/bin/activate
python scripts/03_create_database_schema.py --create-db

# Load data
python scripts/04_load_data_to_db.py \
  --articles data/nlp_enriched/nlp_enriched_NAMO_preprocessed_test_final.parquet \
  --actors data/NAMO_actor_251118.xlsx \
  --stats
```

**Then:**
- Work locally for development
- Deploy to remote server later (when you have access)
- Or use SSH tunnel to connect remotely

**Pros:** Full control, works immediately  
**Cons:** Data stays on your Mac (not on server)

---

## Quick Decision Guide

**Choose based on your needs:**

| Option | Setup Time | Cost | Best For |
|--------|-----------|------|----------|
| **Docker Access** | 5 min (admin) | Free | Production use |
| **Supabase** | 2 min | Free | Quick testing |
| **Neon** | 2 min | Free | Development |
| **Local Mac** | 5 min | Free | Local development |

---

## My Recommendation

**For immediate progress:** Use **Supabase** or **Neon** (cloud PostgreSQL)
- Sign up (2 minutes)
- Get connection string
- Run our scripts with cloud host
- No admin needed, works immediately

**For long-term:** Request **Docker access**
- One-time admin request
- Full control on your server
- Better for production

---

## Next Steps

**Tell me which option you prefer:**

1. **"Request Docker access"** → I'll prepare instructions for your admin
2. **"Use Supabase"** → I'll help you set it up
3. **"Use Neon"** → I'll help you set it up  
4. **"Run locally"** → I'll help you set it up on your Mac

Once you choose, I'll guide you through the setup! 🚀

