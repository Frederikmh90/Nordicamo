# Quick Remote PostgreSQL Setup

## Current Status
- ✅ PostgreSQL 18.0 is installed
- ⚠️ PostgreSQL service needs to be started (requires sudo)
- ✅ Database 'namo_db' exists
- ⏳ Schema creation pending

---

## Manual Steps (You Need to Do This)

### Step 1: Start PostgreSQL

**SSH into server and start PostgreSQL:**

```bash
ssh -p 2111 frede@212.27.13.34

# Start PostgreSQL (you'll be prompted for sudo password)
sudo systemctl start postgresql

# Verify it's running
pg_isready

# Should output: /var/run/postgresql:5432 - accepting connections
```

### Step 2: Create Database User (if not exists)

```bash
# On remote server
sudo -u postgres psql

# In PostgreSQL prompt, run:
CREATE USER namo_user WITH PASSWORD 'namo_password';
ALTER USER namo_user CREATEDB;
GRANT ALL PRIVILEGES ON DATABASE namo_db TO namo_user;
\q
```

---

## Automated Steps (After PostgreSQL is Running)

### Option A: Run Complete Setup Script

**From your local machine:**

```bash
cd /Users/Codebase/projects/alterpublics/NAMO_nov25
source venv/bin/activate

# This will create schema and load data
python scripts/11_setup_remote_complete.py --skip-install-check
```

### Option B: Manual Steps

**1. Create Schema (from local machine):**

```bash
python scripts/03_create_database_schema.py \
  --create-db \
  --host 212.27.13.34 \
  --user namo_user \
  --password namo_password \
  --database namo_db
```

**2. Sync Data Files:**

```bash
# Sync final enriched data
scp -P 2111 data/nlp_enriched/nlp_enriched_NAMO_preprocessed_test_final.parquet \
  frede@212.27.13.34:~/NAMO_nov25/data/nlp_enriched/

# Sync actor data
scp -P 2111 data/NAMO_actor_251118.xlsx \
  frede@212.27.13.34:~/NAMO_nov25/data/
```

**3. Load Data (on remote server):**

```bash
ssh -p 2111 frede@212.27.13.34

cd ~/NAMO_nov25
python3 scripts/04_load_data_to_db.py \
  --articles data/nlp_enriched/nlp_enriched_NAMO_preprocessed_test_final.parquet \
  --actors data/NAMO_actor_251118.xlsx \
  --host localhost \
  --user namo_user \
  --password namo_password \
  --database namo_db \
  --batch-size 100 \
  --stats
```

---

## Verify Setup

**Check database:**

```bash
ssh -p 2111 frede@212.27.13.34

psql -U namo_user -d namo_db -h localhost -c "SELECT COUNT(*) FROM articles;"
psql -U namo_user -d namo_db -h localhost -c "SELECT COUNT(*) FROM actors;"
```

---

## Summary

**What's Ready:**
- ✅ PostgreSQL installed
- ✅ Database exists
- ✅ Scripts ready
- ✅ Data files ready

**What You Need to Do:**
1. Start PostgreSQL: `sudo systemctl start postgresql`
2. Create user (if needed): `sudo -u postgres createuser namo_user`
3. Run setup script: `python scripts/11_setup_remote_complete.py --skip-install-check`

**Then we can:**
- Test backend API
- Test Streamlit dashboard
- Verify everything works!

