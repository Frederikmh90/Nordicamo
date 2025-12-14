#!/bin/bash
# Fix Docker permissions and start PostgreSQL container
# Run this on the remote server after SSH connection

set -e

echo "=========================================="
echo "Fixing Docker Permissions"
echo "=========================================="

# Check if user is in docker group
if groups | grep -q docker; then
    echo "✅ User is already in docker group"
else
    echo "⚠️  User is NOT in docker group"
    echo "Adding user to docker group (requires sudo)..."
    sudo usermod -aG docker $USER
    echo "✅ User added to docker group"
    echo "⚠️  You may need to log out and back in for changes to take effect"
    echo "   Or run: newgrp docker"
fi

echo ""
echo "=========================================="
echo "Starting PostgreSQL Container"
echo "=========================================="

# Try to start with docker group (if available)
if groups | grep -q docker; then
    docker start namo-pg 2>/dev/null || docker-compose up -d namo-pg 2>/dev/null || echo "Container may need to be created first"
else
    # Fallback to sudo
    echo "Using sudo to start container..."
    sudo docker start namo-pg 2>/dev/null || sudo docker-compose up -d namo-pg 2>/dev/null || echo "Container may need to be created first"
fi

# Check if container is running
echo ""
echo "Checking container status..."
if groups | grep -q docker; then
    docker ps | grep namo-pg || echo "Container not running"
else
    sudo docker ps | grep namo-pg || echo "Container not running"
fi

echo ""
echo "=========================================="
echo "Done!"
echo "=========================================="


