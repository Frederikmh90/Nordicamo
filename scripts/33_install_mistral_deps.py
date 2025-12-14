#!/usr/bin/env python3
"""Install dependencies for Mistral v0.3 on remote VM."""

import paramiko
import getpass

REMOTE_HOST = "212.27.13.34"
REMOTE_PORT = 2111
REMOTE_USER = "frede"

def install_dependencies():
    """Install protobuf and sentencepiece on VM."""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(REMOTE_HOST, port=REMOTE_PORT, username=REMOTE_USER, timeout=30)
        print("✅ Connected to VM")
        
        # Install dependencies
        cmd = """
cd ~/NAMO_nov25 && \
source venv/bin/activate && \
pip install protobuf sentencepiece --quiet && \
echo "✅ Dependencies installed"
"""
        
        print("Installing protobuf and sentencepiece...")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        
        # Stream output
        for line in stdout:
            print(line.rstrip())
        
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status == 0:
            print("\n✅ Dependencies installed successfully!")
        else:
            error = stderr.read().decode()
            print(f"\n❌ Installation failed: {error}")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    install_dependencies()

