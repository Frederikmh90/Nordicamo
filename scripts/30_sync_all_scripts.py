#!/usr/bin/env python3
"""Sync all new scripts to remote server."""

import paramiko
from pathlib import Path

HOST = "<SERVER_HOST>"
PORT = 2111
USERNAME = "frede"
REMOTE_DIR = "~/NAMO_nov25"

BASE_DIR = Path(__file__).parent.parent
SCRIPTS_TO_SYNC = [
    "scripts/26_category_classification_only.py",
    "scripts/28_load_categories_to_db.py",
    "scripts/29_run_category_classification_1000.py",
]

def sync_scripts():
    """Sync scripts to remote server."""
    print("=" * 60)
    print("Syncing Scripts to Remote Server")
    print("=" * 60)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print("🔐 Connecting to server...")
        ssh.connect(HOST, port=PORT, username=USERNAME)
        print("✅ Connected!")
        
        # Expand remote directory
        stdin, stdout, stderr = ssh.exec_command(f"echo {REMOTE_DIR}")
        remote_dir_expanded = stdout.read().decode().strip()
        
        # Create remote scripts directory
        ssh.exec_command(f"mkdir -p {remote_dir_expanded}/scripts")
        stdout.channel.recv_exit_status()
        
        # Transfer files
        sftp = ssh.open_sftp()
        for script_path in SCRIPTS_TO_SYNC:
            local_path = BASE_DIR / script_path
            if local_path.exists():
                remote_path = f"{remote_dir_expanded}/{script_path}"
                print(f"📤 Uploading {local_path.name}...")
                sftp.put(str(local_path), remote_path)
                print(f"   ✅ Uploaded")
            else:
                print(f"   ⚠️  Not found: {local_path}")
        sftp.close()
        
        ssh.close()
        print("\n✅ All scripts synced!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    sync_scripts()

