# PostgreSQL Setup Guide for NAMO

## Quick Setup

### macOS (using Homebrew)

```bash
# Install PostgreSQL
brew install postgresql@14

# Start PostgreSQL service
brew services start postgresql@14

# Add to PATH (add to ~/.zshrc or ~/.bash_profile)
export PATH="/opt/homebrew/opt/postgresql@14/bin:$PATH"

# Create database
createdb namo_db

# Create schema
python scripts/03_create_database_schema.py --create-db
```

### Linux (Ubuntu/Debian)

```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database (as postgres user)
sudo -u postgres createdb namo_db
sudo -u postgres createuser $USER

# Create schema
python scripts/03_create_database_schema.py --create-db
```

### Using Docker (Alternative)

```bash
# Run PostgreSQL in Docker
docker run --name namo-postgres \
  -e POSTGRES_PASSWORD=namo_password \
  -e POSTGRES_USER=namo_user \
  -e POSTGRES_DB=namo_db \
  -p 5432:5432 \
  -d postgres:14

# Create schema
python scripts/03_create_database_schema.py --create-db
```

## After Setup

1. **Create schema:**
   ```bash
   python scripts/03_create_database_schema.py --create-db
   ```

2. **Load data:**
   ```bash
   python scripts/04_load_data_to_db.py \
     --articles data/nlp_enriched/nlp_enriched_NAMO_preprocessed_test_final.parquet \
     --actors data/NAMO_actor_251118.xlsx \
     --batch-size 100 \
     --stats
   ```

3. **Verify:**
   ```bash
   psql namo_db -c "SELECT COUNT(*) FROM articles;"
   psql namo_db -c "SELECT COUNT(*) FROM actors;"
   ```

## Environment Variables

Create a `.env` file in the project root:

```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=namo_user
DB_PASSWORD=namo_password
DB_NAME=namo_db
```

Or use your system user (default):
```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=your_username
DB_PASSWORD=
DB_NAME=namo_db
```

## Troubleshooting

**"Connection refused":**
- PostgreSQL is not running
- Start with: `brew services start postgresql@14` (macOS) or `sudo systemctl start postgresql` (Linux)

**"Permission denied":**
- Create user: `createuser -s $USER` (as postgres user)

**"Database does not exist":**
- Create database: `createdb namo_db`

