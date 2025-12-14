#!/usr/bin/env python3
"""
Full NER Pipeline: Run NER for all countries, load to DB, verify frontend.
"""

import subprocess
import sys
from pathlib import Path
import paramiko
import getpass

BASE_DIR = Path(__file__).parent.parent
REMOTE_HOST = "212.27.13.34"
REMOTE_PORT = 2111
REMOTE_USER = "frede"
REMOTE_DIR = "~/NAMO_nov25"

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

def run_ner_on_vm(ssh, input_file, output_file):
    """Run NER processing on VM."""
    stdin, stdout, stderr = ssh.exec_command(f"echo {REMOTE_DIR}")
    remote_dir_expanded = stdout.read().decode().strip()
    
    cmd = f"""
cd {remote_dir_expanded} && \
source venv/bin/activate && \
python3 scripts/34_ner_country_specific.py \
  --input {input_file} \
  --output {output_file} \
  --device cuda \
  --score-threshold 0.5 2>&1
"""
    
    print("🚀 Running NER processing on VM...")
    print("   (This may take 10-30 minutes depending on dataset size)")
    
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
        print(f"\n❌ NER processing failed (exit code: {exit_status})")
        error = stderr.read().decode()
        if error:
            print(f"Error: {error}")
        return False
    
    print("\n✅ NER processing complete on VM")
    return True

def download_results(ssh, remote_file, local_file):
    """Download results from VM."""
    stdin, stdout, stderr = ssh.exec_command(f"echo {REMOTE_DIR}")
    remote_dir_expanded = stdout.read().decode().strip()
    
    remote_path = f"{remote_dir_expanded}/{remote_file}"
    local_path = BASE_DIR / local_file
    local_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📥 Downloading {remote_path}...")
    
    sftp = ssh.open_sftp()
    sftp.get(remote_path, str(local_path))
    sftp.close()
    
    print(f"✅ Downloaded to: {local_path}")
    return local_path

def load_to_database(local_file):
    """Load NER results to PostgreSQL database."""
    print(f"\n💾 Loading NER results to database...")
    
    cmd = [
        sys.executable,
        str(BASE_DIR / "scripts" / "37_load_ner_to_db.py"),
        "--input",
        str(local_file)
    ]
    
    result = subprocess.run(cmd, cwd=str(BASE_DIR), capture_output=False)
    
    if result.returncode == 0:
        print("✅ Database loading complete")
        return True
    else:
        print(f"❌ Database loading failed (exit code: {result.returncode})")
        return False

def main():
    """Main execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Full NER pipeline")
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/sample_1000.parquet",
        help="Input parquet file (relative to VM directory)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/nlp_enriched/sample_1000_ner_final.parquet",
        help="Output parquet file (relative to VM directory)",
    )
    parser.add_argument(
        "--skip-ner",
        action="store_true",
        help="Skip NER processing (use existing results)",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip downloading results",
    )
    parser.add_argument(
        "--skip-db",
        action="store_true",
        help="Skip database loading",
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("NAMO Full NER Pipeline")
    print("=" * 60)
    print(f"Input: {args.input}")
    print(f"Output: {args.output}")
    print()
    
    ssh = connect_ssh()
    
    try:
        # Step 1: Run NER on VM
        if not args.skip_ner:
            if not run_ner_on_vm(ssh, args.input, args.output):
                print("\n❌ Pipeline stopped: NER processing failed")
                return
        else:
            print("⏭️  Skipping NER processing")
        
        # Step 2: Download results
        if not args.skip_download:
            local_file = download_results(ssh, args.output, args.output)
        else:
            print("⏭️  Skipping download")
            local_file = BASE_DIR / args.output
        
        # Step 3: Load to database
        if not args.skip_db:
            if not load_to_database(local_file):
                print("\n❌ Pipeline stopped: Database loading failed")
                return
        else:
            print("⏭️  Skipping database loading")
        
        print("\n" + "=" * 60)
        print("✅ Full NER Pipeline Complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Verify frontend shows NER data:")
        print("   streamlit run frontend/app.py")
        print("2. Check backend API:")
        print("   curl http://localhost:8000/api/stats/entities/top?entity_type=persons")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()




