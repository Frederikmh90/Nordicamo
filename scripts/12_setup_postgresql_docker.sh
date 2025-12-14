#!/bin/bash
# PostgreSQL Docker Setup for NAMO (No sudo required)
# Sets up PostgreSQL in Docker container on remote server

set -e

REMOTE_HOST="212.27.13.34"
REMOTE_PORT="2111"
REMOTE_USER="frede"
CONTAINER_NAME="namo-postgres"
DB_NAME="namo_db"
DB_USER="namo_user"
DB_PASSWORD="namo_password"
PG_PORT="5432"

echo "=========================================="
echo "NAMO PostgreSQL Docker Setup"
echo "=========================================="
echo ""
echo "Remote server: ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PORT}"
echo "Container: ${CONTAINER_NAME}"
echo "Database: ${DB_NAME}"
echo ""

# Check if container already exists
echo "Checking for existing container..."
ssh -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST} << ENDSSH
set -e

# Check if container exists
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}\$"; then
    echo "Container '${CONTAINER_NAME}' already exists."
    read -p "Do you want to remove and recreate it? (y/N): " -n 1 -r
    echo
    if [[ \$REPLY =~ ^[Yy]\$ ]]; then
        echo "Stopping and removing existing container..."
        docker stop ${CONTAINER_NAME} 2>/dev/null || true
        docker rm ${CONTAINER_NAME} 2>/dev/null || true
    else
        echo "Using existing container."
        docker start ${CONTAINER_NAME} 2>/dev/null || true
        echo "✅ Container started"
        exit 0
    fi
fi

echo ""
echo "=========================================="
echo "Creating PostgreSQL Container"
echo "=========================================="

# Create and start PostgreSQL container
docker run -d \
  --name ${CONTAINER_NAME} \
  -e POSTGRES_USER=${DB_USER} \
  -e POSTGRES_PASSWORD=${DB_PASSWORD} \
  -e POSTGRES_DB=${DB_NAME} \
  -p ${PG_PORT}:5432 \
  -v namo-postgres-data:/var/lib/postgresql/data \
  postgres:14-alpine

echo "✅ Container created and started"

# Wait for PostgreSQL to be ready
echo ""
echo "Waiting for PostgreSQL to be ready..."
for i in {1..30}; do
    if docker exec ${CONTAINER_NAME} pg_isready -U ${DB_USER} > /dev/null 2>&1; then
        echo "✅ PostgreSQL is ready!"
        break
    fi
    if [ \$i -eq 30 ]; then
        echo "⚠️  PostgreSQL took too long to start. Check logs with: docker logs ${CONTAINER_NAME}"
        exit 1
    fi
    sleep 1
done

echo ""
echo "=========================================="
echo "PostgreSQL Docker Setup Complete!"
echo "=========================================="
echo ""
echo "Container: ${CONTAINER_NAME}"
echo "Database: ${DB_NAME}"
echo "User: ${DB_USER}"
echo "Port: ${PG_PORT}"
echo ""
echo "Connection string:"
echo "  postgresql://${DB_USER}:${DB_PASSWORD}@localhost:${PG_PORT}/${DB_NAME}"
echo ""
echo "Useful commands:"
echo "  docker start ${CONTAINER_NAME}     # Start container"
echo "  docker stop ${CONTAINER_NAME}      # Stop container"
echo "  docker logs ${CONTAINER_NAME}      # View logs"
echo "  docker exec -it ${CONTAINER_NAME} psql -U ${DB_USER} -d ${DB_NAME}  # Connect to database"

ENDSSH

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Create schema: python scripts/03_create_database_schema.py --create-db --host ${REMOTE_HOST}"
echo "  2. Load data: python scripts/04_load_data_to_db.py --host ${REMOTE_HOST} ..."

