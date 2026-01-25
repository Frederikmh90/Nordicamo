#!/usr/bin/env python3
"""
Complete Remote PostgreSQL Setup
==================================
Sets up PostgreSQL, creates schema, and loads data on remote server.
"""

import paramiko
import getpass
import os
from pathlib import Path
import time

# Configuration
REMOTE_HOST = "<SERVER_HOST>"
REMOTE_PORT = 2111
REMOTE_USER = "frede"
REMOTE_DIR = "~/NAMO_nov25"
LOCAL_PROJECT_DIR = Path(__file__).parent.parent


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


def check_postgresql(ssh):
    """Check if PostgreSQL is installed and running."""
    print("\n" + "="*60)
    print("Checking PostgreSQL Installation")
    print("="*60)
    
    # Check if PostgreSQL is installed
    stdin, stdout, stderr = ssh.exec_command("command -v psql")
    if stdout.read().decode().strip():
        stdin, stdout, stderr = ssh.exec_command("psql --version")
        version = stdout.read().decode().strip()
        print(f"✅ PostgreSQL found: {version}")
    else:
        print("❌ PostgreSQL not found. Please install PostgreSQL first.")
        print("\nTo install on Ubuntu/Debian:")
        print("  sudo apt update && sudo apt install -y postgresql postgresql-contrib")
        print("  sudo systemctl start postgresql")
        return False
    
    # Check if PostgreSQL is running
    stdin, stdout, stderr = ssh.exec_command("pg_isready 2>&1 || sudo systemctl is-active postgresql 2>&1")
    status = stdout.read().decode().strip()
    if "accepting" in status.lower() or "active" in status.lower():
        print("✅ PostgreSQL is running")
        return True
    else:
        print("⚠️  PostgreSQL may not be running")
        print("Try: sudo systemctl start postgresql")
        return False


def create_database(ssh):
    """Create database and user."""
    print("\n" + "="*60)
    print("Creating Database")
    print("="*60)
    
    db_name = "namo_db"
    db_user = "namo_user"
    
    # Create user
    print(f"Creating user '{db_user}'...")
    cmd = f"sudo -u postgres psql -c \"CREATE USER {db_user} WITH PASSWORD '<DB_PASSWORD>';\" 2>&1 || echo 'User may already exist'"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    output = stdout.read().decode()
    errors = stderr.read().decode()
    print(output)
    
    # Check if database exists
    cmd = f"sudo -u postgres psql -lqt | cut -d \\| -f 1 | grep -qw {db_name} && echo 'exists' || echo 'not_exists'"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    exists = stdout.read().decode().strip()
    
    if "exists" in exists:
        print(f"Database '{db_name}' already exists.")
        print("Using existing database.")
    else:
        # Create database
        print(f"Creating database '{db_name}'...")
        cmd = f"sudo -u postgres createdb -O {db_user} {db_name} 2>&1"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        output = stdout.read().decode()
        errors = stderr.read().decode()
        if errors and "already exists" not in errors:
            print(f"Note: {errors}")
        print(f"✅ Database '{db_name}' created")
    
    return db_name, db_user


def sync_schema_script(ssh, remote_dir_expanded):
    """Sync schema creation script to remote."""
    print("\n" + "="*60)
    print("Syncing Schema Script")
    print("="*60)
    
    sftp = ssh.open_sftp()
    try:
        local_script = LOCAL_PROJECT_DIR / "scripts" / "03_create_database_schema.py"
        remote_script = f"{remote_dir_expanded}/scripts/03_create_database_schema.py"
        
        print(f"Uploading {local_script.name}...")
        sftp.put(str(local_script), remote_script)
        print("✅ Schema script uploaded")
    finally:
        sftp.close()


def create_schema(ssh, remote_dir_expanded, db_name, db_user):
    """Create database schema."""
    print("\n" + "="*60)
    print("Creating Database Schema")
    print("="*60)
    
    # Update script to use correct database credentials
    script_path = f"{remote_dir_expanded}/scripts/03_create_database_schema.py"
    
    # Run schema creation
    cmd = f"cd {remote_dir_expanded} && python3 scripts/03_create_database_schema.py --create-db --host localhost --user {db_user} --password <DB_PASSWORD> --database {db_name} 2>&1"
    
    stdin, stdout, stderr = ssh.exec_command(cmd)
    
    print("Creating schema...")
    for line in iter(stdout.readline, ""):
        if line:
            print(f"  {line.strip()}")
    
    errors = stderr.read().decode()
    if errors and "Error" in errors:
        print(f"\n⚠️  Errors: {errors}")
        return False
    
    print("✅ Schema created successfully")
    return True


def main():
    """Main execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Complete remote PostgreSQL setup')
    parser.add_argument('--skip-install-check', action='store_true', help='Skip PostgreSQL installation check')
    
    args = parser.parse_args()
    
    print("="*60)
    print("NAMO Remote PostgreSQL Complete Setup")
    print("="*60)
    print(f"Remote server: {REMOTE_USER}@{REMOTE_HOST}:{REMOTE_PORT}")
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
        # Get remote directory
        stdin, stdout, stderr = ssh.exec_command("echo $HOME")
        home_dir = stdout.read().decode().strip()
        remote_dir_expanded = REMOTE_DIR.replace("~", home_dir)
        
        # Check PostgreSQL
        if not args.skip_install_check:
            if not check_postgresql(ssh):
                print("\n⚠️  Please install and start PostgreSQL first, then run again with --skip-install-check")
                return
        
        # Create database
        db_name, db_user = create_database(ssh)
        
        # Sync schema script
        sync_schema_script(ssh, remote_dir_expanded)
        
        # Create schema
        if create_schema(ssh, remote_dir_expanded, db_name, db_user):
            print("\n" + "="*60)
            print("Setup Complete!")
            print("="*60)
            print(f"\nDatabase: {db_name}")
            print(f"User: {db_user}")
            print(f"\nNext step: Load data with:")
            print(f"  python scripts/04_load_data_to_db.py \\")
            print(f"    --articles data/nlp_enriched/nlp_enriched_NAMO_preprocessed_test_final.parquet \\")
            print(f"    --actors data/NAMO_actor_251118.xlsx \\")
            print(f"    --host {REMOTE_HOST} \\")
            print(f"    --user {db_user} \\")
            print(f"    --password <DB_PASSWORD> \\")
            print(f"    --database {db_name} \\")
            print(f"    --stats")
        else:
            print("\n⚠️  Schema creation had issues. Please check manually.")
    
    finally:
        ssh.close()
        print("\nConnection closed.")


if __name__ == "__main__":
    main()

