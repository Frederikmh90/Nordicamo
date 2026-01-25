#!/usr/bin/env python3
"""
Check GPU Usage on Remote Server
=================================
Quick script to check GPU memory and usage before/after loading models.
"""

import paramiko
import getpass
import sys

# Configuration
REMOTE_HOST = "<SERVER_HOST>"
REMOTE_PORT = 2111
REMOTE_USER = "frede"


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


def check_gpu(ssh):
    """Check GPU status."""
    print("="*60)
    print("GPU Status Check")
    print("="*60)
    
    # Check if nvidia-smi is available
    stdin, stdout, stderr = ssh.exec_command("which nvidia-smi")
    if stdout.read().decode().strip():
        print("✅ nvidia-smi available")
    else:
        print("❌ nvidia-smi not found - GPU may not be available")
        return
    
    # Get GPU info
    print("\nGPU Information:")
    print("-"*60)
    stdin, stdout, stderr = ssh.exec_command("nvidia-smi --query-gpu=index,name,memory.total,memory.free,memory.used,utilization.gpu,temperature.gpu --format=csv")
    output = stdout.read().decode()
    print(output)
    
    # Get detailed memory info
    print("\nDetailed Memory Info:")
    print("-"*60)
    stdin, stdout, stderr = ssh.exec_command("nvidia-smi --query-gpu=memory.total,memory.free,memory.used --format=csv,noheader,nounits")
    mem_output = stdout.read().decode().strip()
    if mem_output:
        lines = mem_output.split('\n')
        for i, line in enumerate(lines):
            total, free, used = map(int, line.split(', '))
            used_pct = (used / total) * 100
            print(f"GPU {i}: {used}MB / {total}MB used ({used_pct:.1f}%), {free}MB free")
    
    # Check if processes are using GPU
    print("\nGPU Processes:")
    print("-"*60)
    stdin, stdout, stderr = ssh.exec_command("nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv")
    processes = stdout.read().decode().strip()
    if processes and "No running processes" not in processes:
        print(processes)
    else:
        print("No processes currently using GPU")


def main():
    """Main execution."""
    print("="*60)
    print("NAMO GPU Usage Checker")
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
        check_gpu(ssh)
        
        print("\n" + "="*60)
        print("Recommendations")
        print("="*60)
        print("For Qwen2.5-7B-Instruct:")
        print("  - Without quantization: ~14GB GPU memory needed")
        print("  - With 4-bit quantization: ~5-6GB GPU memory needed")
        print("\nIf you have enough GPU memory, disable quantization for better JSON output:")
        print("  python scripts/02_nlp_processing.py --no-quantization ...")
        print("\nIf GPU memory is limited, use quantization (may affect JSON quality):")
        print("  python scripts/02_nlp_processing.py --use-quantization ...")
    
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

