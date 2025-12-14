#!/usr/bin/env python3
"""
Interactive script to run NLP processing on remote GPU server.
Handles SSH connection with password authentication.
"""

import paramiko
import getpass
import os
import sys
from pathlib import Path
import time
from typing import Optional

# Configuration
REMOTE_HOST = "212.27.13.34"
REMOTE_PORT = 2111
REMOTE_USER = "frede"
REMOTE_DIR = "~/NAMO_nov25"
LOCAL_PROJECT_DIR = Path(__file__).parent.parent


def connect_ssh(password: Optional[str] = None) -> paramiko.SSHClient:
    """Connect to remote server via SSH."""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        if password:
            ssh.connect(
                REMOTE_HOST,
                port=REMOTE_PORT,
                username=REMOTE_USER,
                password=password,
                timeout=30
            )
        else:
            # Try without password first (SSH key)
            ssh.connect(
                REMOTE_HOST,
                port=REMOTE_PORT,
                username=REMOTE_USER,
                timeout=30
            )
        return ssh
    except paramiko.AuthenticationException:
        if not password:
            # Prompt for password
            password = getpass.getpass(f"Password for {REMOTE_USER}@${REMOTE_HOST}: ")
            return connect_ssh(password)
        else:
            raise Exception("Authentication failed. Please check your password.")
    except Exception as e:
        raise Exception(f"Failed to connect: {e}")


def setup_remote_environment(ssh: paramiko.SSHClient):
    """Set up Python environment on remote server."""
    print("\n" + "="*60)
    print("Setting up remote environment...")
    print("="*60)
    
    # Expand ~ to home directory
    stdin, stdout, stderr = ssh.exec_command("echo $HOME")
    home_dir = stdout.read().decode().strip()
    remote_dir_expanded = REMOTE_DIR.replace("~", home_dir)
    
    commands = [
        f"mkdir -p {remote_dir_expanded}/scripts",
        f"mkdir -p {remote_dir_expanded}/data/processed",
        f"mkdir -p {remote_dir_expanded}/data/nlp_enriched",
        f"mkdir -p {remote_dir_expanded}/models",
        f"mkdir -p {remote_dir_expanded}/logs",
        f"cd {remote_dir_expanded}",
        "python3 --version",
    ]
    
    stdin, stdout, stderr = ssh.exec_command(" && ".join(commands))
    stdout.channel.recv_exit_status()  # Wait for completion
    output = stdout.read().decode()
    errors = stderr.read().decode()
    
    if errors:
        print(f"Warnings: {errors}")
    print(output)
    return remote_dir_expanded


def sync_files(ssh: paramiko.SSHClient, input_file: str, remote_dir_expanded: str):
    """Sync necessary files to remote server using SCP."""
    print("\n" + "="*60)
    print("Syncing files to remote server...")
    print("="*60)
    
    # Create SFTP client
    sftp = ssh.open_sftp()
    
    try:
        # Sync scripts directory
        print("Syncing scripts...")
        local_scripts = LOCAL_PROJECT_DIR / "scripts"
        remote_scripts = f"{remote_dir_expanded}/scripts"
        
        # Create remote directory and wait for it
        stdin, stdout, stderr = ssh.exec_command(f"mkdir -p {remote_scripts}")
        stdout.channel.recv_exit_status()  # Wait for command to complete
        
        # Upload each script file
        for script_file in local_scripts.glob("*.py"):
            if script_file.name.startswith("02_"):  # NLP processing script
                remote_path = f"{remote_scripts}/{script_file.name}"
                print(f"  Uploading {script_file.name}...")
                try:
                    sftp.put(str(script_file), remote_path)
                    print(f"    ✓ Uploaded successfully")
                except Exception as e:
                    print(f"    ✗ Error uploading: {e}")
                    raise
        
        # Sync input file
        print(f"Syncing input file: {input_file}...")
        local_input = LOCAL_PROJECT_DIR / input_file
        if not local_input.exists():
            raise FileNotFoundError(f"Input file not found: {local_input}")
        
        remote_input = f"{remote_dir_expanded}/{input_file}"
        # Create remote directory structure
        remote_input_dir = "/".join(remote_input.split("/")[:-1])
        stdin, stdout, stderr = ssh.exec_command(f"mkdir -p {remote_input_dir}")
        stdout.channel.recv_exit_status()  # Wait for command to complete
        print(f"  Uploading {local_input.name} to {remote_input}...")
        try:
            sftp.put(str(local_input), remote_input)
            print(f"    ✓ Uploaded successfully")
        except Exception as e:
            print(f"    ✗ Error uploading: {e}")
            raise
        
        # Sync requirements.txt
        print("Syncing requirements.txt...")
        local_req = LOCAL_PROJECT_DIR / "requirements.txt"
        if local_req.exists():
            sftp.put(str(local_req), f"{remote_dir_expanded}/requirements.txt")
            print(f"    ✓ Uploaded successfully")
        
        print("File sync complete!")
        
    finally:
        sftp.close()


def install_dependencies(ssh: paramiko.SSHClient, remote_dir_expanded: str):
    """Install Python dependencies on remote server."""
    print("\n" + "="*60)
    print("Installing dependencies...")
    print("="*60)
    
    commands = [
        f"cd {remote_dir_expanded}",
        "python3 -m pip install --user -r requirements.txt || echo 'Some packages may already be installed'",
        "python3 -m spacy download xx_ent_wiki_sm || echo 'spaCy model may already exist'",
    ]
    
    stdin, stdout, stderr = ssh.exec_command(" && ".join(commands))
    
    # Show output in real-time
    print("Installing packages (this may take a few minutes)...")
    for line in iter(stdout.readline, ""):
        if line:
            print(f"  {line.strip()}")


def run_nlp_processing(ssh: paramiko.SSHClient, input_file: str, batch_size: int = 4, remote_dir_expanded: str = None):
    """Run NLP processing on remote server."""
    print("\n" + "="*60)
    print("Starting NLP processing...")
    print("="*60)
    
    if remote_dir_expanded is None:
        # Expand ~ to home directory
        stdin, stdout, stderr = ssh.exec_command("echo $HOME")
        home_dir = stdout.read().decode().strip()
        remote_dir_expanded = REMOTE_DIR.replace("~", home_dir)
    
    remote_input = f"{remote_dir_expanded}/{input_file}"
    output_file = f"nlp_enriched_{Path(input_file).stem}.parquet"
    remote_output = f"{remote_dir_expanded}/data/nlp_enriched/{output_file}"
    
    # Create command (default: no quantization for better JSON output)
    command = f"""
cd {remote_dir_expanded} && \
python3 scripts/02_nlp_processing.py \
    --input {remote_input} \
    --output {remote_output} \
    --batch-size {batch_size} \
    --no-quantization \
    2>&1 | tee logs/nlp_processing.log
"""
    
    print(f"Command: python3 scripts/02_nlp_processing.py --input {remote_input} --batch-size {batch_size}")
    print("\nProcessing started. This will take a while...")
    print("Output will be saved to logs/nlp_processing.log")
    print("\nTo monitor progress in another terminal:")
    print(f"  ssh -p {REMOTE_PORT} {REMOTE_USER}@{REMOTE_HOST} 'tail -f {remote_dir_expanded}/logs/nlp_processing.log'")
    print("\n⚠️  Watch for 'Other' category warnings - they will show:")
    print("   - LLM reasoning for why 'Other' was assigned")
    print("   - Article preview")
    print("   - Raw categories from LLM")
    print("\n" + "-"*60)
    
    # Execute command
    stdin, stdout, stderr = ssh.exec_command(command)
    
    # Show output in real-time
    try:
        for line in iter(stdout.readline, ""):
            if line:
                print(line.strip())
                sys.stdout.flush()
    except KeyboardInterrupt:
        print("\n\nProcessing interrupted by user.")
        print("The process may continue running on the remote server.")
        print("Check logs to see current status.")
    
    # Check for errors
    error_output = stderr.read().decode()
    if error_output:
        print("\nErrors:")
        print(error_output)


def main():
    """Main execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run NLP processing on remote GPU server")
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/NAMO_preprocessed_test.parquet",
        help="Input parquet file (relative to project root)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=4,
        help="Batch size for processing"
    )
    parser.add_argument(
        "--setup-only",
        action="store_true",
        help="Only set up environment, don't run processing"
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("NAMO Remote NLP Processing")
    print("="*60)
    print(f"Remote server: {REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PORT}")
    print(f"Input file: {args.input}")
    print(f"Batch size: {args.batch_size}")
    print("="*60)
    
    # Get password if needed
    password = None
    try:
        ssh = connect_ssh()
        print("Connected via SSH key!")
    except:
        password = getpass.getpass(f"Password for {REMOTE_USER}@${REMOTE_HOST}: ")
        ssh = connect_ssh(password)
        print("Connected!")
    
    try:
        # Setup
        remote_dir_expanded = setup_remote_environment(ssh)
        sync_files(ssh, args.input, remote_dir_expanded)
        install_dependencies(ssh, remote_dir_expanded)
        
        if not args.setup_only:
            # Run processing
            run_nlp_processing(ssh, args.input, args.batch_size, remote_dir_expanded)
        else:
            print("\nSetup complete! Run without --setup-only to start processing.")
    
    finally:
        ssh.close()
        print("\nConnection closed.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)

