#!/bin/bash
# UCloud NLP Setup Script

set -e

echo "🚀 Setting up NLP environment on UCloud..."

cd /work/NAMO_nov25

# Create virtual environment
echo "📦 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install PyTorch with CUDA support
echo "🔧 Installing PyTorch with CUDA 12.8..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install transformers and other NLP dependencies
echo "🤖 Installing transformers and NLP libraries..."
pip install transformers>=4.35.0 accelerate>=0.25.0

# Install data processing libraries
echo "📊 Installing data processing libraries..."
pip install polars>=0.20.0 pandas numpy

# Install spaCy and models
echo "🌍 Installing spaCy..."
pip install spacy>=3.7.0
python3 -m spacy download xx_ent_wiki_sm  # Multilingual model

# Install database connector
echo "🗄️  Installing psycopg2..."
pip install psycopg2-binary

# Install other utilities
pip install python-dotenv tqdm sentencepiece protobuf

echo "✅ Setup complete!"
echo ""
echo "To activate environment: source /work/NAMO_nov25/venv/bin/activate"
echo "To test GPU: python3 -c 'import torch; print(f\"CUDA available: {torch.cuda.is_available()}\"); print(f\"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}\")'"

