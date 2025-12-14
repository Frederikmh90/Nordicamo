#!/usr/bin/env python3
"""
Install NLP Dependencies on Remote Server
==========================================
Quick script to install missing NLP dependencies.
"""

import subprocess
import sys

def install_package(package):
    """Install a package using pip."""
    print(f"Installing {package}...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", package],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print(f"✅ {package} installed")
        return True
    else:
        print(f"❌ {package} failed: {result.stderr[:200]}")
        return False

def main():
    """Install required NLP dependencies."""
    print("="*60)
    print("Installing NLP Dependencies")
    print("="*60)
    
    # Core NLP packages
    packages = [
        "spacy>=3.7.0",
        "transformers>=4.35.0",
        "torch>=2.0.0",
        "accelerate>=0.24.0",
        "polars>=0.20.0",
        "tqdm>=4.66.0",
    ]
    
    failed = []
    for package in packages:
        if not install_package(package):
            failed.append(package)
    
    print("\n" + "="*60)
    if failed:
        print(f"⚠️  Some packages failed: {failed}")
        print("   Try installing manually:")
        for pkg in failed:
            print(f"   pip install {pkg}")
    else:
        print("✅ All packages installed successfully")
    
    # Download spaCy model
    print("\n" + "="*60)
    print("Downloading spaCy multilingual model...")
    print("="*60)
    result = subprocess.run(
        [sys.executable, "-m", "spacy", "download", "xx_ent_wiki_sm"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("✅ spaCy model downloaded")
    else:
        print(f"⚠️  spaCy model download failed: {result.stderr[:200]}")
        print("   Try manually: python -m spacy download xx_ent_wiki_sm")
    
    print("\n" + "="*60)
    print("Done!")
    print("="*60)

if __name__ == "__main__":
    main()

