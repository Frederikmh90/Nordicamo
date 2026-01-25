#!/usr/bin/env python3
"""
Full pipeline: Sync script → Run classification on VM → Download → Load to DB → Frontend ready
"""

import paramiko
import getpass
import subprocess
from pathlib import Path
import time
import sys

# Configuration
REMOTE_HOST = "<SERVER_HOST>"
REMOTE_PORT = 2111
REMOTE_USER = "frede"
REMOTE_DIR = "~/NAMO_nov25"
BASE_DIR = Path(__file__).parent.parent

def connect_ssh():
    """Connect to remote server."""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(REMOTE_HOST, port=REMOTE_PORT, username=REMOTE_USER, timeout=30)
        return ssh
    except paramiko.AuthenticationException:
        password = getpass.getpass(f"Password for {REMOTE_USER}@{REMOTE_HOST}: ")
        ssh.connect(REMOTE_HOST, port=REMOTE_PORT, username=REMOTE_USER, password=password, timeout=30)
        return ssh
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        sys.exit(1)

def sync_script(ssh):
    """Sync updated script to VM."""
    print("=" * 60)
    print("Step 1: Syncing updated script to VM")
    print("=" * 60)
    
    # Expand remote directory
    stdin, stdout, stderr = ssh.exec_command(f"echo {REMOTE_DIR}")
    remote_dir_expanded = stdout.read().decode().strip()
    
    # Create remote scripts directory
    ssh.exec_command(f"mkdir -p {remote_dir_expanded}/scripts")
    stdout.channel.recv_exit_status()
    
    # Transfer script
    local_script = BASE_DIR / "scripts" / "26_category_classification_only.py"
    remote_script = f"{remote_dir_expanded}/scripts/26_category_classification_only.py"
    
    print(f"📤 Uploading {local_script.name}...")
    sftp = ssh.open_sftp()
    sftp.put(str(local_script), remote_script)
    sftp.close()
    print(f"✅ Script synced to VM")
    
    return remote_dir_expanded

def run_classification(ssh, remote_dir_expanded):
    """Run classification on VM."""
    print("=" * 60)
    print("Step 2: Running classification on VM")
    print("=" * 60)
    
    input_file = "data/processed/sample_1000.parquet"
    output_file = "data/nlp_enriched/sample_1000_categories.parquet"
    
    # Check if input file exists
    stdin, stdout, stderr = ssh.exec_command(
        f"test -f {remote_dir_expanded}/{input_file} && echo 'exists' || echo 'missing'"
    )
    if stdout.read().decode().strip() == "missing":
        print(f"⚠️  Input file not found on VM: {input_file}")
        print("   Creating sample first...")
        
        # Create sample on VM
        cmd = f"""
cd {remote_dir_expanded} && \
python3 -c "
import polars as pl
df = pl.read_parquet('data/processed/NAMO_preprocessed_test.parquet')
df.head(1000).write_parquet('data/processed/sample_1000.parquet')
print(f'Created sample: {{len(df.head(1000))}} articles')
"
"""
        stdin, stdout, stderr = ssh.exec_command(cmd)
        stdout.channel.recv_exit_status()
        print("✅ Sample created on VM")
    
    # Run classification
    cmd = f"""
cd {remote_dir_expanded} && \
source venv/bin/activate && \
python3 scripts/26_category_classification_only.py \
  --input {input_file} \
  --output {output_file} \
  --model mistralai/Mistral-7B-Instruct-v0.3 \
  --no-quantization 2>&1
"""
    
    print("🚀 Starting classification on VM...")
    print("   (This may take several minutes)")
    
    stdin, stdout, stderr = ssh.exec_command(cmd)
    
    # Stream output
    print("\n--- VM Output ---")
    while True:
        line = stdout.readline()
        if not line:
            break
        print(line.rstrip())
    
    exit_status = stdout.channel.recv_exit_status()
    
    if exit_status != 0:
        print(f"\n❌ Classification failed (exit code: {exit_status})")
        error = stderr.read().decode()
        if error:
            print(f"Error: {error}")
        return False
    
    print("\n✅ Classification complete on VM")
    return True

def download_results(ssh, remote_dir_expanded):
    """Download results from VM."""
    print("=" * 60)
    print("Step 3: Downloading results from VM")
    print("=" * 60)
    
    remote_file = f"{remote_dir_expanded}/data/nlp_enriched/sample_1000_categories.parquet"
    local_file = BASE_DIR / "data" / "nlp_enriched" / "sample_1000_categories.parquet"
    local_file.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"📥 Downloading {remote_file}...")
    
    sftp = ssh.open_sftp()
    sftp.get(remote_file, str(local_file))
    sftp.close()
    
    print(f"✅ Downloaded to: {local_file}")
    return local_file

def load_to_database(result_file):
    """Load results to local database."""
    print("=" * 60)
    print("Step 4: Loading categories to database")
    print("=" * 60)
    
    cmd = [
        "python3",
        str(BASE_DIR / "scripts" / "28_load_categories_to_db.py"),
        "--input", str(result_file),
    ]
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=BASE_DIR)
    
    if result.returncode != 0:
        print("❌ Database loading failed")
        return False
    
    print("✅ Categories loaded to database")
    return True

def main():
    """Main execution."""
    print("\n" + "=" * 60)
    print("NAMO Category Classification - Full Pipeline")
    print("=" * 60 + "\n")
    
    # Connect to VM
    ssh = connect_ssh()
    
    try:
        # Step 1: Sync script
        remote_dir_expanded = sync_script(ssh)
        
        # Step 2: Run classification
        if not run_classification(ssh, remote_dir_expanded):
            print("\n❌ Pipeline stopped: Classification failed")
            return
        
        # Step 3: Download results
        result_file = download_results(ssh, remote_dir_expanded)
        
        # Step 4: Load to database
        if not load_to_database(result_file):
            print("\n❌ Pipeline stopped: Database loading failed")
            return
        
        # Summary
        print("\n" + "=" * 60)
        print("✅ Pipeline Complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Backend should already be running (if not: cd backend && uvicorn app.main:app --reload)")
        print("2. Refresh your Streamlit dashboard to see updated categories")
        print("3. Check the 'News Categories' section in the dashboard")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

