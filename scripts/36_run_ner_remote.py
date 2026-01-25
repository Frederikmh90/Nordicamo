#!/usr/bin/env python3
"""
Run NER processing on remote VM.
Similar to 31_run_full_pipeline.py but for NER.
"""

import paramiko
import getpass
import subprocess
from pathlib import Path
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
        ssh.connect(
            REMOTE_HOST,
            port=REMOTE_PORT,
            username=REMOTE_USER,
            password=password,
            timeout=30,
        )
        return ssh
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        sys.exit(1)


def sync_script(ssh):
    """Sync updated script to VM."""
    print("=" * 60)
    print("Step 1: Syncing NER script to VM")
    print("=" * 60)

    # Expand remote directory
    stdin, stdout, stderr = ssh.exec_command(f"echo {REMOTE_DIR}")
    remote_dir_expanded = stdout.read().decode().strip()

    # Create remote scripts directory
    ssh.exec_command(f"mkdir -p {remote_dir_expanded}/scripts")
    stdout.channel.recv_exit_status()

    # Transfer script
    local_script = BASE_DIR / "scripts" / "34_ner_country_specific.py"
    remote_script = f"{remote_dir_expanded}/scripts/34_ner_country_specific.py"

    print(f"📤 Uploading {local_script.name}...")
    sftp = ssh.open_sftp()
    sftp.put(str(local_script), remote_script)
    sftp.close()
    print(f"✅ Script synced to VM")

    return remote_dir_expanded


def run_ner(ssh, remote_dir_expanded, input_file, output_file, score_threshold=0.5):
    """Run NER processing on VM."""
    print("=" * 60)
    print("Step 2: Running NER processing on VM")
    print("=" * 60)

    # Check if input file exists
    stdin, stdout, stderr = ssh.exec_command(
        f"test -f {remote_dir_expanded}/{input_file} && echo 'exists' || echo 'missing'"
    )
    if stdout.read().decode().strip() == "missing":
        print(f"⚠️  Input file not found on VM: {input_file}")
        print("   Please ensure the input file exists on the VM")
        return False

    # Run NER processing
    cmd = f"""
cd {remote_dir_expanded} && \
source venv/bin/activate && \
python3 scripts/34_ner_country_specific.py \
  --input {input_file} \
  --output {output_file} \
  --device cuda \
  --score-threshold {score_threshold} 2>&1
"""

    print("🚀 Starting NER processing on VM...")
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
        print(f"\n❌ NER processing failed (exit code: {exit_status})")
        error = stderr.read().decode()
        if error:
            print(f"Error: {error}")
        return False

    print("\n✅ NER processing complete on VM")
    return True


def download_results(ssh, remote_dir_expanded, output_file):
    """Download results from VM."""
    print("=" * 60)
    print("Step 3: Downloading results from VM")
    print("=" * 60)

    remote_file = f"{remote_dir_expanded}/{output_file}"
    local_file = BASE_DIR / output_file
    local_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"📥 Downloading {remote_file}...")

    sftp = ssh.open_sftp()
    sftp.get(remote_file, str(local_file))
    sftp.close()

    print(f"✅ Downloaded to: {local_file}")
    return local_file


def main():
    """Main execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Run NER processing on remote VM")
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/sample_1000.parquet",
        help="Input parquet file (relative to VM directory)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/nlp_enriched/sample_1000_ner.parquet",
        help="Output parquet file (relative to VM directory)",
    )
    parser.add_argument(
        "--score-threshold",
        type=float,
        default=0.5,
        help="Minimum confidence score for entities",
    )
    parser.add_argument(
        "--skip-sync",
        action="store_true",
        help="Skip script syncing (if already synced)",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip downloading results",
    )

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("NAMO NER Processing - Remote Execution")
    print("=" * 60 + "\n")

    # Connect to VM
    ssh = connect_ssh()

    try:
        # Step 1: Sync script
        if not args.skip_sync:
            remote_dir_expanded = sync_script(ssh)
        else:
            stdin, stdout, stderr = ssh.exec_command(f"echo {REMOTE_DIR}")
            remote_dir_expanded = stdout.read().decode().strip()

        # Step 2: Run NER
        if not run_ner(
            ssh, remote_dir_expanded, args.input, args.output, args.score_threshold
        ):
            print("\n❌ Pipeline stopped: NER processing failed")
            return

        # Step 3: Download results
        if not args.skip_download:
            result_file = download_results(ssh, remote_dir_expanded, args.output)

            print("\n" + "=" * 60)
            print("✅ NER Processing Complete!")
            print("=" * 60)
            print(f"\nResults downloaded to: {result_file}")
            print("\nNext steps:")
            print("1. Load entities to database:")
            print(f"   python3 scripts/37_load_ner_to_db.py --input {result_file}")
            print("2. Refresh dashboard to see updated entities")
        else:
            print("\n✅ NER processing complete on VM")
            print(f"   Results available at: {remote_dir_expanded}/{args.output}")

    finally:
        ssh.close()


if __name__ == "__main__":
    main()
