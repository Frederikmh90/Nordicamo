#!/usr/bin/env python3
"""
Install Topic Modeling Dependencies on Remote Server
=====================================================
Standalone script to install dependencies for topic modeling.
Can be run separately if installation fails during main script.
"""

import paramiko
import getpass
import sys
from pathlib import Path

# Configuration
REMOTE_HOST = "212.27.13.34"
REMOTE_PORT = 2111
REMOTE_USER = "frede"
REMOTE_DIR = "~/NAMO_nov25"


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


def install_dependencies(ssh, remote_dir_expanded: str):
    """Install dependencies with better error handling."""
    print("="*60)
    print("Installing Topic Modeling Dependencies")
    print("="*60)
    
    # Upgrade pip first
    print("\n1. Upgrading pip...")
    cmd = f"cd {remote_dir_expanded} && source venv/bin/activate && python3 -m pip install --upgrade pip setuptools wheel"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    stdout.channel.recv_exit_status()
    print("   ✅ pip upgraded")
    
    # Install packages in order
    packages = [
        ("numpy", "Core numerical library"),
        ("pandas", "Data manipulation"),
        ("scikit-learn", "Machine learning utilities"),
        ("nltk", "Natural language toolkit"),
        ("tqdm", "Progress bars"),
        ("torch", "PyTorch (this may take a while)"),
        ("transformers", "Hugging Face transformers"),
        ("sentence-transformers", "Sentence embeddings"),
        ("bertopic", "Topic modeling library"),
        ("polars", "Fast data processing"),
    ]
    
    failed = []
    
    for package, description in packages:
        print(f"\n2. Installing {package} ({description})...")
        
        # Try normal install
        cmd = f"cd {remote_dir_expanded} && source venv/bin/activate && python3 -m pip install {package} --upgrade 2>&1"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        
        output = stdout.read().decode()
        error = stderr.read().decode()
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status == 0:
            print(f"   ✅ {package} installed")
        else:
            print(f"   ⚠️  {package} failed, trying --no-cache-dir...")
            
            # Try with --no-cache-dir
            cmd = f"cd {remote_dir_expanded} && source venv/bin/activate && python3 -m pip install {package} --no-cache-dir --upgrade 2>&1"
            stdin, stdout, stderr = ssh.exec_command(cmd)
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status == 0:
                print(f"   ✅ {package} installed (with --no-cache-dir)")
            else:
                error = stderr.read().decode() or stdout.read().decode()
                print(f"   ❌ {package} failed")
                print(f"      Error: {error[:300]}")
                failed.append(package)
    
    print("\n" + "="*60)
    if failed:
        print(f"❌ Failed to install: {failed}")
        print("\nTroubleshooting:")
        print("1. Check if virtual environment is activated")
        print("2. Check disk space: df -h")
        print("3. Check Python version: python3 --version")
        print("4. Try manual installation:")
        print(f"   ssh -p {REMOTE_PORT} {REMOTE_USER}@{REMOTE_HOST}")
        print(f"   cd {remote_dir_expanded}")
        print(f"   source venv/bin/activate")
        print(f"   pip install {' '.join(failed)}")
        return False
    else:
        print("✅ All dependencies installed successfully!")
        return True


def main():
    """Main execution."""
    print("="*60)
    print("NAMO Topic Modeling Dependency Installer")
    print("="*60)
    print(f"Remote server: {REMOTE_USER}@{REMOTE_HOST}:{REMOTE_PORT}")
    print("")
    
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
        
        # Check if venv exists
        stdin, stdout, stderr = ssh.exec_command(f"test -d {remote_dir_expanded}/venv && echo 'exists' || echo 'not_exists'")
        venv_exists = stdout.read().decode().strip()
        
        if venv_exists == "not_exists":
            print(f"\n⚠️  Virtual environment not found at {remote_dir_expanded}/venv")
            print("   Creating virtual environment...")
            cmd = f"cd {remote_dir_expanded} && python3 -m venv venv"
            stdin, stdout, stderr = ssh.exec_command(cmd)
            stdout.channel.recv_exit_status()
            print("   ✅ Virtual environment created")
        
        # Install dependencies
        success = install_dependencies(ssh, remote_dir_expanded)
        
        if success:
            print("\n✅ Ready to run topic modeling!")
            print(f"   Run: python scripts/17_run_topic_modeling_remote.py --skip-install")
        else:
            print("\n⚠️  Some dependencies failed. Check errors above.")
            sys.exit(1)
    
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
        import traceback
        traceback.print_exc()
        sys.exit(1)

