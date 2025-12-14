#!/bin/bash
# Local PostgreSQL Setup for NAMO (macOS)
# Sets up PostgreSQL locally for development

set -e

echo "=========================================="
echo "NAMO Local PostgreSQL Setup"
echo "=========================================="
echo ""

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew is not installed."
    echo "Please install Homebrew first:"
    echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

echo "✅ Homebrew found"
echo ""

# Check if PostgreSQL is installed
if brew list postgresql@14 &> /dev/null || brew list postgresql &> /dev/null; then
    echo "✅ PostgreSQL is already installed"
    PG_VERSION=$(psql --version 2>/dev/null | awk '{print $3}' || echo "unknown")
    echo "   Version: $PG_VERSION"
else
    echo "Installing PostgreSQL..."
    brew install postgresql@14
    echo "✅ PostgreSQL installed"
fi

echo ""

# Add PostgreSQL to PATH (for this session)
export PATH="/opt/homebrew/opt/postgresql@14/bin:$PATH"
export PATH="/usr/local/opt/postgresql@14/bin:$PATH"

# Check if PostgreSQL is running
if pg_isready &> /dev/null; then
    echo "✅ PostgreSQL is running"
else
    echo "Starting PostgreSQL service..."
    brew services start postgresql@14 || brew services start postgresql
    sleep 3
    
    if pg_isready &> /dev/null; then
        echo "✅ PostgreSQL started"
    else
        echo "⚠️  PostgreSQL may take a moment to start"
        echo "   Check status: brew services list"
    fi
fi

echo ""
echo "=========================================="
echo "Creating Database"
echo "=========================================="

DB_NAME="namo_db"
DB_USER=$(whoami)

# Check if database exists
if psql -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    echo "Database '$DB_NAME' already exists."
    read -p "Do you want to drop and recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Dropping existing database..."
        dropdb "$DB_NAME" 2>/dev/null || true
    else
        echo "Using existing database."
        echo "✅ Setup complete!"
        exit 0
    fi
fi

# Create database
echo "Creating database '$DB_NAME'..."
createdb "$DB_NAME" || {
    echo "❌ Failed to create database"
    echo "   Try manually: createdb $DB_NAME"
    exit 1
}

echo "✅ Database '$DB_NAME' created"
echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo ""
echo "Next steps:"
echo "  1. Create schema: python scripts/03_create_database_schema.py --create-db"
echo "  2. Load data: python scripts/04_load_data_to_db.py --articles ... --actors ..."
echo ""

