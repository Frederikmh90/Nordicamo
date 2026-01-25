#!/usr/bin/env python3
"""
PostgreSQL Docker Setup for NAMO (No sudo required)
Sets up PostgreSQL in Docker container on remote server
"""

import paramiko
import getpass
import time
import sys

# Configuration
REMOTE_HOST = "<SERVER_HOST>"
REMOTE_PORT = 2111
REMOTE_USER = "frede"
CONTAINER_NAME = "namo-postgres"
DB_NAME = "namo_db"
DB_USER = "namo_user"
DB_PASSWORD = "<DB_PASSWORD>"
PG_PORT = "5432"


def connect_ssh(password=None):
    """Connect to remote server."""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        if password:
            ssh.connect(REMOTE_HOST, port=REMOTE_PORT, username=REMOTE_USER, password=password, timeout=30)
        else:
            ssh.connect(REMOTE_HOST, port=REMOTE_PORT, username=REMOTE_USER, timeout=30)
        return ssh
    except paramiko.AuthenticationException:
        if not password:
            password = getpass.getpass(f"Password for {REMOTE_USER}@{REMOTE_HOST}: ")
            return connect_ssh(password)
        else:
            raise Exception("Authentication failed.")
    except Exception as e:
        raise Exception(f"Failed to connect: {e}")


def check_docker(ssh):
    """Check if Docker is available."""
    print("\n" + "="*60)
    print("Checking Docker")
    print("="*60)
    
    stdin, stdout, stderr = ssh.exec_command("docker --version")
    version = stdout.read().decode().strip()
    if version:
        print(f"✅ Docker found: {version}")
        return True
    else:
        print("❌ Docker not found")
        return False


def check_container(ssh):
    """Check if container exists."""
    cmd = f"docker ps -a --format '{{{{.Names}}}}' | grep -q '^{CONTAINER_NAME}$' && echo 'exists' || echo 'not_exists'"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    result = stdout.read().decode().strip()
    return "exists" in result


def create_container(ssh):
    """Create and start PostgreSQL container."""
    print("\n" + "="*60)
    print("Creating PostgreSQL Container")
    print("="*60)
    
    # Check if container exists
    if check_container(ssh):
        print(f"Container '{CONTAINER_NAME}' already exists.")
        response = input("Do you want to remove and recreate it? (y/N): ").strip().lower()
        if response == 'y':
            print("Stopping and removing existing container...")
            ssh.exec_command(f"docker stop {CONTAINER_NAME} 2>/dev/null || true")
            time.sleep(1)
            ssh.exec_command(f"docker rm {CONTAINER_NAME} 2>/dev/null || true")
            time.sleep(1)
        else:
            print("Starting existing container...")
            stdin, stdout, stderr = ssh.exec_command(f"docker start {CONTAINER_NAME}")
            stdout.channel.recv_exit_status()
            print("✅ Container started")
            return True
    
    # Create container
    print("Creating PostgreSQL container...")
    cmd = f"""docker run -d \\
  --name {CONTAINER_NAME} \\
  -e POSTGRES_USER={DB_USER} \\
  -e POSTGRES_PASSWORD={DB_PASSWORD} \\
  -e POSTGRES_DB={DB_NAME} \\
  -p {PG_PORT}:5432 \\
  -v namo-postgres-data:/var/lib/postgresql/data \\
  postgres:14-alpine"""
    
    stdin, stdout, stderr = ssh.exec_command(cmd)
    exit_status = stdout.channel.recv_exit_status()
    
    if exit_status != 0:
        error = stderr.read().decode()
        print(f"❌ Error creating container: {error}")
        return False
    
    container_id = stdout.read().decode().strip()
    print(f"✅ Container created: {container_id[:12]}...")
    
    # Wait for PostgreSQL to be ready
    print("\nWaiting for PostgreSQL to be ready...")
    for i in range(30):
        cmd = f"docker exec {CONTAINER_NAME} pg_isready -U {DB_USER} > /dev/null 2>&1 && echo 'ready' || echo 'not_ready'"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        result = stdout.read().decode().strip()
        
        if "ready" in result:
            print("✅ PostgreSQL is ready!")
            return True
        
        if i == 29:
            print("⚠️  PostgreSQL took too long to start")
            print("Check logs with: docker logs {CONTAINER_NAME}")
            return False
        
        time.sleep(1)
        if i % 5 == 0:
            print(f"  Waiting... ({i+1}/30)")
    
    return True


def verify_connection(ssh):
    """Verify PostgreSQL connection."""
    print("\n" + "="*60)
    print("Verifying Connection")
    print("="*60)
    
    cmd = f"docker exec {CONTAINER_NAME} psql -U {DB_USER} -d {DB_NAME} -c 'SELECT version();' 2>&1"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    output = stdout.read().decode()
    errors = stderr.read().decode()
    
    if "PostgreSQL" in output:
        print("✅ Connection successful!")
        print(f"   {output.split(chr(10))[2] if len(output.split(chr(10))) > 2 else output[:100]}")
        return True
    else:
        print(f"⚠️  Connection test: {errors or output}")
        return False


def main():
    """Main execution."""
    print("="*60)
    print("NAMO PostgreSQL Docker Setup")
    print("="*60)
    print(f"Remote server: {REMOTE_USER}@{REMOTE_HOST}:{REMOTE_PORT}")
    print(f"Container: {CONTAINER_NAME}")
    print(f"Database: {DB_NAME}")
    print("")
    
    # Connect
    try:
        ssh = connect_ssh()
        print("✅ Connected to remote server")
    except:
        password = getpass.getpass(f"Password for {REMOTE_USER}@{REMOTE_HOST}: ")
        ssh = connect_ssh(password)
        print("✅ Connected")
    
    try:
        # Check Docker
        if not check_docker(ssh):
            print("\n❌ Docker is required but not found. Please install Docker or ask your administrator.")
            return
        
        # Create container
        if create_container(ssh):
            # Verify connection
            if verify_connection(ssh):
                print("\n" + "="*60)
                print("Setup Complete!")
                print("="*60)
                print(f"\nContainer: {CONTAINER_NAME}")
                print(f"Database: {DB_NAME}")
                print(f"User: {DB_USER}")
                print(f"Port: {PG_PORT}")
                print(f"\nConnection string:")
                print(f"  postgresql://{DB_USER}:{DB_PASSWORD}@{REMOTE_HOST}:{PG_PORT}/{DB_NAME}")
                print(f"\nNext steps:")
                print(f"  1. Create schema:")
                print(f"     python scripts/03_create_database_schema.py \\")
                print(f"       --create-db \\")
                print(f"       --host {REMOTE_HOST} \\")
                print(f"       --user {DB_USER} \\")
                print(f"       --password {DB_PASSWORD} \\")
                print(f"       --database {DB_NAME}")
                print(f"\n  2. Load data:")
                print(f"     python scripts/04_load_data_to_db.py \\")
                print(f"       --articles data/nlp_enriched/nlp_enriched_NAMO_preprocessed_test_final.parquet \\")
                print(f"       --actors data/NAMO_actor_251118.xlsx \\")
                print(f"       --host {REMOTE_HOST} \\")
                print(f"       --user {DB_USER} \\")
                print(f"       --password {DB_PASSWORD} \\")
                print(f"       --database {DB_NAME}")
            else:
                print("\n⚠️  Container created but connection verification failed")
        else:
            print("\n❌ Failed to create container")
    
    finally:
        ssh.close()
        print("\nConnection closed.")


if __name__ == "__main__":
    main()

