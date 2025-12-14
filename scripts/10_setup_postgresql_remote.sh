#!/bin/bash
# Remote PostgreSQL Setup Script for NAMO
# Sets up PostgreSQL on remote server via SSH

set -e

REMOTE_HOST="212.27.13.34"
REMOTE_PORT="2111"
REMOTE_USER="frede"
REMOTE_DIR="~/NAMO_nov25"

echo "=========================================="
echo "NAMO Remote PostgreSQL Setup"
echo "=========================================="
echo ""
echo "Remote server: ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PORT}"
echo ""

# Check SSH connection
echo "Testing SSH connection..."
ssh -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST} "echo 'SSH connection successful!'" || {
    echo "Error: Cannot connect to remote server"
    exit 1
}

echo ""
echo "Setting up PostgreSQL on remote server..."
echo ""

# Run setup commands on remote server
ssh -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST} << 'ENDSSH'
set -e

echo "=========================================="
echo "Step 1: Check PostgreSQL Installation"
echo "=========================================="

# Check if PostgreSQL is installed
if command -v psql &> /dev/null; then
    PG_VERSION=$(psql --version | awk '{print $3}')
    echo "✅ PostgreSQL is installed: version $PG_VERSION"
else
    echo "PostgreSQL is not installed."
    echo ""
    echo "Installing PostgreSQL..."
    
    # Detect OS
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
    else
        echo "Cannot detect OS. Please install PostgreSQL manually."
        exit 1
    fi
    
    if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
        sudo apt update
        sudo apt install -y postgresql postgresql-contrib
        sudo systemctl start postgresql
        sudo systemctl enable postgresql
    elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ]; then
        sudo yum install -y postgresql-server postgresql-contrib
        sudo postgresql-setup initdb
        sudo systemctl start postgresql
        sudo systemctl enable postgresql
    else
        echo "Unsupported OS: $OS"
        echo "Please install PostgreSQL manually."
        exit 1
    fi
    
    echo "✅ PostgreSQL installed successfully"
fi

echo ""
echo "=========================================="
echo "Step 2: Check PostgreSQL Service"
echo "=========================================="

# Check if PostgreSQL is running
if sudo systemctl is-active --quiet postgresql || pg_isready -q 2>/dev/null; then
    echo "✅ PostgreSQL service is running"
else
    echo "Starting PostgreSQL service..."
    sudo systemctl start postgresql || service postgresql start
    sleep 2
    
    if sudo systemctl is-active --quiet postgresql || pg_isready -q 2>/dev/null; then
        echo "✅ PostgreSQL service started"
    else
        echo "⚠️  Warning: Could not verify PostgreSQL is running"
    fi
fi

echo ""
echo "=========================================="
echo "Step 3: Create Database User"
echo "=========================================="

DB_USER="namo_user"
DB_NAME="namo_db"

# Check if user exists
if sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1; then
    echo "✅ Database user '$DB_USER' already exists"
else
    echo "Creating database user '$DB_USER'..."
    sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD 'namo_password';" || {
        echo "Note: User creation may have failed, trying without password..."
        sudo -u postgres createuser $DB_USER || true
    }
    echo "✅ Database user created"
fi

echo ""
echo "=========================================="
echo "Step 4: Create Database"
echo "=========================================="

# Check if database exists
if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    echo "Database '$DB_NAME' already exists."
    read -p "Do you want to drop and recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Dropping existing database..."
        sudo -u postgres dropdb $DB_NAME || true
    else
        echo "Using existing database."
        exit 0
    fi
fi

# Create database
echo "Creating database '$DB_NAME'..."
sudo -u postgres createdb -O $DB_USER $DB_NAME || {
    echo "Trying without owner specification..."
    sudo -u postgres createdb $DB_NAME
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" || true
}

echo "✅ Database '$DB_NAME' created"

echo ""
echo "=========================================="
echo "PostgreSQL Setup Complete!"
echo "=========================================="
echo ""
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo ""
echo "Connection string:"
echo "  postgresql://$DB_USER:namo_password@localhost:5432/$DB_NAME"
echo ""
echo "Next steps:"
echo "  1. Sync schema creation script to remote"
echo "  2. Run: python scripts/03_create_database_schema.py --create-db"
echo "  3. Load data with scripts/04_load_data_to_db.py"

ENDSSH

echo ""
echo "=========================================="
echo "Remote Setup Complete!"
echo "=========================================="
echo ""
echo "Next: Sync files and create schema..."

