#!/usr/bin/env python3
"""
Remote Topic Modeling Execution
================================
Connects to remote GPU server, syncs files, and runs topic modeling.
Similar to 05_run_nlp_remote_interactive.py but for topic modeling.
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


def setup_remote_environment(ssh):
    """Set up remote directory structure."""
    stdin, stdout, stderr = ssh.exec_command("echo $HOME")
    home_dir = stdout.read().decode().strip()
    remote_dir_expanded = REMOTE_DIR.replace("~", home_dir)
    
    commands = [
        f"mkdir -p {remote_dir_expanded}/scripts",
        f"mkdir -p {remote_dir_expanded}/data/nlp_enriched",
        f"mkdir -p {remote_dir_expanded}/data/topic_modeled",
        f"mkdir -p {remote_dir_expanded}/models",
    ]
    
    for cmd in commands:
        stdin, stdout, stderr = ssh.exec_command(cmd)
        stdout.channel.recv_exit_status()
    
    return remote_dir_expanded


def sync_files(ssh, input_file: str, remote_dir_expanded: str):
    """Sync necessary files to remote server."""
    sftp = ssh.open_sftp()
    
    try:
        # Sync topic modeling script
        local_script = LOCAL_PROJECT_DIR / "scripts" / "15_topic_modeling_turftopic.py"
        remote_script = f"{remote_dir_expanded}/scripts/15_topic_modeling_turftopic.py"
        
        print(f"Uploading {local_script.name}...")
        sftp.put(str(local_script), remote_script)
        print("✅ Script uploaded")
        
        # Sync input data file
        local_input = LOCAL_PROJECT_DIR / input_file
        if local_input.exists():
            remote_input = f"{remote_dir_expanded}/{input_file}"
            remote_input_dir = os.path.dirname(remote_input)
            ssh.exec_command(f"mkdir -p {remote_input_dir}")
            
            print(f"Uploading {input_file}...")
            sftp.put(str(local_input), remote_input)
            print("✅ Data file uploaded")
        else:
            print(f"⚠️  Input file not found locally: {input_file}")
            print("   Assuming it already exists on remote server")
        
        # Sync requirements.txt
        local_req = LOCAL_PROJECT_DIR / "requirements.txt"
        if local_req.exists():
            sftp.put(str(local_req), f"{remote_dir_expanded}/requirements.txt")
            print("✅ Requirements file uploaded")
        
    finally:
        sftp.close()


def install_dependencies(ssh, remote_dir_expanded: str):
    """Install Python dependencies on remote server."""
    print("\n" + "="*60)
    print("Installing Dependencies")
    print("="*60)
    
    # Check if venv exists
    stdin, stdout, stderr = ssh.exec_command(f"test -d {remote_dir_expanded}/venv && echo 'exists' || echo 'not_exists'")
    venv_exists = stdout.read().decode().strip()
    
    if venv_exists == "not_exists":
        print("Creating virtual environment...")
        cmd = f"cd {remote_dir_expanded} && python3 -m venv venv"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        stdout.channel.recv_exit_status()
        print("✅ Virtual environment created")
    
    # Install dependencies in order (some depend on others)
    print("Installing Python packages...")
    
    # Core packages first
    core_packages = [
        "numpy",
        "pandas",
        "scikit-learn",
        "nltk",
        "tqdm",
    ]
    
    # PyTorch (needs to be installed before transformers/bertopic)
    torch_packages = [
        "torch",
    ]
    
    # ML packages (depend on torch)
    ml_packages = [
        "accelerate",  # Required for device_map="auto"
        "transformers",
        "sentence-transformers",
    ]
    
    # Topic modeling (depends on everything above)
    topic_packages = [
        "bertopic",
    ]
    
    # Data processing
    data_packages = [
        "polars",
    ]
    
    all_packages = [
        ("Core", core_packages),
        ("PyTorch", torch_packages),
        ("ML Libraries", ml_packages),
        ("Topic Modeling", topic_packages),
        ("Data Processing", data_packages),
    ]
    
    failed_packages = []
    
    for category, packages in all_packages:
        print(f"\n  Installing {category}...")
        for package in packages:
            # Don't use --user in virtualenv
            cmd = f"cd {remote_dir_expanded} && source venv/bin/activate && python3 -m pip install {package} --upgrade 2>&1"
            stdin, stdout, stderr = ssh.exec_command(cmd)
            
            # Read output
            output = stdout.read().decode()
            error = stderr.read().decode()
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status == 0:
                print(f"    ✅ {package}")
            else:
                print(f"    ❌ {package} failed")
                print(f"       Error: {error[:200] if error else output[:200]}")
                failed_packages.append(package)
    
    if failed_packages:
        print(f"\n⚠️  Some packages failed to install: {failed_packages}")
        print("   Attempting alternative installation methods...")
        
        # Try installing with --no-cache-dir
        for package in failed_packages:
            print(f"   Retrying {package}...")
            cmd = f"cd {remote_dir_expanded} && source venv/bin/activate && python3 -m pip install {package} --no-cache-dir --upgrade 2>&1"
            stdin, stdout, stderr = ssh.exec_command(cmd)
            exit_status = stdout.channel.recv_exit_status()
            if exit_status == 0:
                print(f"     ✅ {package} installed successfully")
                failed_packages.remove(package)
            else:
                error = stderr.read().decode()
                print(f"     ❌ {package} still failed: {error[:200]}")
    
    if failed_packages:
        print(f"\n❌ Critical packages failed: {failed_packages}")
        print("   Topic modeling may not work. Check error messages above.")
        return False
    
    print("\n✅ All dependencies installed successfully")
    return True


def run_topic_modeling(ssh, remote_dir_expanded: str, input_file: str, output_file: str, sample_size: int = None, unified: bool = False):
    """Run topic modeling on remote server."""
    print("\n" + "="*60)
    print("Running Topic Modeling")
    print("="*60)
    
    # Build command - need to quote paths properly
    remote_input_full = f"{remote_dir_expanded}/{input_file}"
    remote_output_full = f"{remote_dir_expanded}/{output_file}"
    
    cmd_parts = [
        f"cd {remote_dir_expanded}",
        "source venv/bin/activate",
        f"python3 scripts/15_topic_modeling_turftopic.py --input '{remote_input_full}' --output '{remote_output_full}'"
    ]
    
    if sample_size:
        cmd_parts[-1] += f" --sample-size {sample_size}"
    
    if unified:
        cmd_parts[-1] += " --unified"
    
    cmd = " && ".join(cmd_parts)
    
    print(f"Command: {cmd}")
    print("\nStarting topic modeling (this may take a while)...")
    print("="*60)
    
    # Execute command with real-time output
    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
    
    # Stream output in real-time
    import select
    import sys
    
    while True:
        if stdout.channel.recv_ready():
            data = stdout.channel.recv(1024).decode('utf-8', errors='ignore')
            if data:
                print(data, end='')
                sys.stdout.flush()
        
        if stdout.channel.exit_status_ready():
            break
        
        time.sleep(0.1)
    
    # Get exit status
    exit_status = stdout.channel.recv_exit_status()
    
    if exit_status == 0:
        print("\n" + "="*60)
        print("✅ Topic Modeling Completed Successfully!")
        print("="*60)
    else:
        error = stderr.read().decode()
        print("\n" + "="*60)
        print("❌ Topic Modeling Failed")
        print("="*60)
        print(f"Error: {error}")
    
    return exit_status == 0


def download_results(ssh, remote_dir_expanded: str, output_file: str, local_output: str):
    """Download topic modeling results."""
    print("\n" + "="*60)
    print("Downloading Results")
    print("="*60)
    
    remote_output = f"{remote_dir_expanded}/{output_file}"
    local_output_path = LOCAL_PROJECT_DIR / local_output
    local_output_path.parent.mkdir(parents=True, exist_ok=True)
    
    sftp = ssh.open_sftp()
    try:
        print(f"Downloading {output_file}...")
        sftp.get(remote_output, str(local_output_path))
        print(f"✅ Downloaded to {local_output_path}")
        
        # Also download topic info files
        stdin, stdout, stderr = ssh.exec_command(f"ls {remote_dir_expanded}/data/topic_modeled/topic_info_*.csv 2>/dev/null")
        topic_info_files = stdout.read().decode().strip().split('\n')
        
        for remote_file in topic_info_files:
            if remote_file:
                filename = os.path.basename(remote_file)
                local_file = LOCAL_PROJECT_DIR / "data" / "topic_modeled" / filename
                local_file.parent.mkdir(parents=True, exist_ok=True)
                sftp.get(remote_file, str(local_file))
                print(f"✅ Downloaded {filename}")
        
    except Exception as e:
        print(f"⚠️  Error downloading: {e}")
    finally:
        sftp.close()


def main():
    """Main execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run topic modeling on remote GPU server")
    parser.add_argument(
        "--input",
        type=str,
        default="data/nlp_enriched/nlp_enriched_NAMO_preprocessed_test_final.parquet",
        help="Input parquet file (relative to project root)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/topic_modeled/topics.parquet",
        help="Output parquet file (relative to project root)",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=None,
        help="Sample size per country (for testing)",
    )
    parser.add_argument(
        "--skip-install",
        action="store_true",
        help="Skip dependency installation",
    )
    parser.add_argument(
        "--unified",
        action="store_true",
        help="Run one unified topic model on entire corpus instead of per-country",
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("NAMO Remote Topic Modeling")
    print("="*60)
    print(f"Remote server: {REMOTE_USER}@{REMOTE_HOST}:{REMOTE_PORT}")
    print(f"Input file: {args.input}")
    print(f"Output file: {args.output}")
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
        # Setup environment
        remote_dir_expanded = setup_remote_environment(ssh)
        print(f"✅ Remote directory: {remote_dir_expanded}")
        
        # Sync files
        sync_files(ssh, args.input, remote_dir_expanded)
        
        # Install dependencies
        if not args.skip_install:
            deps_ok = install_dependencies(ssh, remote_dir_expanded)
            if not deps_ok:
                print("\n⚠️  Dependency installation had issues.")
                print("   You can try:")
                print("   1. Run with --skip-install if dependencies are already installed")
                print("   2. Manually install on remote server")
                print("   3. Check error messages above for specific issues")
                response = input("\nContinue anyway? (y/n): ")
                if response.lower() != 'y':
                    print("Aborting.")
                    return
        
        # Run topic modeling
        success = run_topic_modeling(
            ssh,
            remote_dir_expanded,
            args.input,
            args.output,
            sample_size=args.sample_size,
            unified=args.unified
        )
        
        if success:
            # Download results
            download_results(ssh, remote_dir_expanded, args.output, args.output)
            
            print("\n" + "="*60)
            print("Next Steps")
            print("="*60)
            print(f"1. Load topics into database:")
            print(f"   python scripts/16_add_topics_to_database.py \\")
            print(f"     --topics {args.output} \\")
            print(f"     --host localhost --user namo_user --password <DB_PASSWORD> --database namo_db")
            print(f"\n2. View topics in dashboard (after loading)")
        else:
            print("\n⚠️  Topic modeling failed. Check logs above.")
    
    finally:
        ssh.close()
        print("\nConnection closed.")


if __name__ == "__main__":
    main()

