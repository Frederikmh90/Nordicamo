#!/bin/bash
# PostgreSQL Setup Script for NAMO
# This script helps set up PostgreSQL for local development

set -e

echo "=========================================="
echo "NAMO PostgreSQL Setup"
echo "=========================================="
echo ""

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "PostgreSQL is not installed."
    echo ""
    echo "To install on macOS:"
    echo "  brew install postgresql@14"
    echo "  brew services start postgresql@14"
    echo ""
    echo "To install on Ubuntu/Debian:"
    echo "  sudo apt update"
    echo "  sudo apt install postgresql postgresql-contrib"
    echo ""
    exit 1
fi

# Check PostgreSQL version
PG_VERSION=$(psql --version | awk '{print $3}')
echo "PostgreSQL version: $PG_VERSION"
echo ""

# Check if PostgreSQL is running
if ! pg_isready -q; then
    echo "⚠️  PostgreSQL server is not running."
    echo ""
    echo "To start PostgreSQL:"
    echo "  macOS: brew services start postgresql@14"
    echo "  Linux: sudo systemctl start postgresql"
    echo ""
    exit 1
fi

echo "✅ PostgreSQL is running"
echo ""

# Create database
DB_NAME="namo_db"
DB_USER="${USER}"

echo "Creating database: $DB_NAME"
echo "User: $DB_USER"
echo ""

# Check if database exists
if psql -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    echo "Database '$DB_NAME' already exists."
    read -p "Do you want to drop and recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Dropping existing database..."
        dropdb "$DB_NAME" || true
    else
        echo "Using existing database."
        exit 0
    fi
fi

# Create database
createdb "$DB_NAME" || {
    echo "Error: Failed to create database. You may need to run:"
    echo "  createdb $DB_NAME"
    exit 1
}

echo "✅ Database '$DB_NAME' created successfully"
echo ""

# Create schema
echo "Creating database schema..."
python3 scripts/03_create_database_schema.py --create-db || {
    echo "Error: Failed to create schema"
    exit 1
}

echo ""
echo "=========================================="
echo "PostgreSQL Setup Complete!"
echo "=========================================="
echo ""
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo ""
echo "To connect:"
echo "  psql $DB_NAME"
echo ""
echo "Next step: Load data with:"
echo "  python scripts/04_load_data_to_db.py \\"
echo "    --articles data/nlp_enriched/nlp_enriched_NAMO_preprocessed_test_final.parquet \\"
echo "    --actors data/NAMO_actor_251118.xlsx \\"
echo "    --stats"

