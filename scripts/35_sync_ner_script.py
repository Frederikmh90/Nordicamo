#!/usr/bin/env python3
"""Sync NER script to remote server."""

import paramiko
from pathlib import Path

HOST = "212.27.13.34"
PORT = 2111
USERNAME = "frede"
REMOTE_DIR = "~/NAMO_nov25"

BASE_DIR = Path(__file__).parent.parent
SCRIPT_PATH = BASE_DIR / "scripts" / "34_ner_country_specific.py"

def sync_script():
    """Sync the NER script to remote server."""
    print("=" * 60)
    print("Syncing NER Script to Remote Server")
    print("=" * 60)
    
    if not SCRIPT_PATH.exists():
        print(f"❌ Script not found: {SCRIPT_PATH}")
        return False
    
    print(f"📁 Local script: {SCRIPT_PATH}")
    print(f"🌐 Remote server: {USERNAME}@{HOST}:{PORT}")
    print(f"📂 Remote directory: {REMOTE_DIR}")
    print()
    
    # Connect via SSH
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        print("🔐 Connecting to server...")
        ssh.connect(HOST, port=PORT, username=USERNAME, timeout=30)
        print("✅ Connected!")
        
        # Expand remote directory
        stdin, stdout, stderr = ssh.exec_command(f"echo {REMOTE_DIR}")
        remote_dir_expanded = stdout.read().decode().strip()
        print(f"📂 Remote directory (expanded): {remote_dir_expanded}")
        
        # Create remote scripts directory if needed
        stdin, stdout, stderr = ssh.exec_command(
            f"mkdir -p {remote_dir_expanded}/scripts"
        )
        stdout.channel.recv_exit_status()
        print("✅ Remote scripts directory ready")
        
        # Transfer file
        print(f"📤 Uploading {SCRIPT_PATH.name}...")
        sftp = ssh.open_sftp()
        
        remote_path = f"{remote_dir_expanded}/scripts/{SCRIPT_PATH.name}"
        sftp.put(str(SCRIPT_PATH), remote_path)
        sftp.close()
        
        print(f"✅ Uploaded to: {remote_path}")
        
        # Verify file exists
        stdin, stdout, stderr = ssh.exec_command(f"ls -lh {remote_path}")
        result = stdout.read().decode()
        if result:
            print(f"✅ Verification: {result.strip()}")
        
        ssh.close()
        print()
        print("=" * 60)
        print("✅ Sync complete!")
        print("=" * 60)
        print()
        print("You can now run on VM:")
        print(f"  cd ~/NAMO_nov25")
        print(f"  source venv/bin/activate")
        print(f"  python3 scripts/34_ner_country_specific.py \\")
        print(f"    --input data/processed/sample_1000.parquet \\")
        print(f"    --output data/nlp_enriched/sample_1000_ner.parquet \\")
        print(f"    --device cuda \\")
        print(f"    --score-threshold 0.5")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    sync_script()




