# Remote PostgreSQL Setup Instructions

## Current Status

✅ **PostgreSQL is installed** (version 18.0)  
⚠️ **PostgreSQL service needs to be started**  
✅ **Database 'namo_db' exists**  
⏳ **Schema creation pending** (needs PostgreSQL running)

---

## Step 1: Start PostgreSQL Service

**SSH into the server and run:**

```bash
ssh -p 2111 frede@212.27.13.34

# Start PostgreSQL (you'll need sudo password)
sudo systemctl start postgresql

# Verify it's running
pg_isready

# Enable auto-start on boot
sudo systemctl enable postgresql
```

**Alternative (if you don't have sudo):**
- Ask your system administrator to start PostgreSQL
- Or use Docker if you have Docker access

---

## Step 2: Create Database User (if needed)

```bash
# On remote server
sudo -u postgres psql

# In PostgreSQL prompt:
CREATE USER namo_user WITH PASSWORD 'namo_password';
ALTER USER namo_user CREATEDB;
\q
```

---

## Step 3: Create Schema

**After PostgreSQL is running, from your local machine:**

```bash
cd /Users/Codebase/projects/alterpublics/NAMO_nov25
source venv/bin/activate

# Create schema on remote server
python scripts/03_create_database_schema.py \
  --create-db \
  --host 212.27.13.34 \
  --user namo_user \
  --password namo_password \
  --database namo_db
```

---

## Step 4: Load Data

```bash
# Sync final data file to remote
scp -P 2111 data/nlp_enriched/nlp_enriched_NAMO_preprocessed_test_final.parquet \
  frede@212.27.13.34:~/NAMO_nov25/data/nlp_enriched/

scp -P 2111 data/NAMO_actor_251118.xlsx \
  frede@212.27.13.34:~/NAMO_nov25/data/

# Load data (run on remote server or use SSH)
ssh -p 2111 frede@212.27.13.34 << 'EOF'
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
EOF
```

---

## Quick Setup Script

**Run this after starting PostgreSQL:**

```bash
# From local machine
cd /Users/Codebase/projects/alterpublics/NAMO_nov25
source venv/bin/activate

# Complete setup
python scripts/11_setup_remote_complete.py --skip-install-check
```

---

## Troubleshooting

### "Connection refused"
- PostgreSQL is not running
- Start with: `sudo systemctl start postgresql`

### "Permission denied"
- User may not exist
- Create user: `sudo -u postgres createuser namo_user`

### "Database does not exist"
- Database already exists (that's fine, we'll use it)
- Or create manually: `sudo -u postgres createdb namo_db`

### "Authentication failed"
- Check password in `.env` file
- Or use command line arguments: `--user` and `--password`

---

## Connection Details

**Remote Server:**
- Host: `212.27.13.34`
- Port: `2111` (SSH), `5432` (PostgreSQL)
- User: `frede`

**Database:**
- Name: `namo_db`
- User: `namo_user`
- Password: `namo_password`
- Host: `localhost` (on remote server) or `212.27.13.34` (from local)

---

## Next Steps After Setup

1. ✅ Start PostgreSQL service
2. ✅ Create schema
3. ✅ Load data
4. ✅ Test backend API
5. ✅ Test Streamlit dashboard

