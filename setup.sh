#!/bin/bash
# NAMO Setup Script
# This script sets up the environment for the Nordic Alternative Media Observatory

echo "======================================"
echo "NAMO Environment Setup"
echo "======================================"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install it first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "✓ uv found"

# Create virtual environment with uv
echo ""
echo "Creating virtual environment..."
uv venv

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
uv pip install -r requirements.txt

# Install spaCy model
echo ""
echo "Installing spaCy multilingual model..."
python3 -m spacy download xx_ent_wiki_sm

# Create necessary directories
echo ""
echo "Creating directory structure..."
mkdir -p data/processed
mkdir -p data/nlp_enriched
mkdir -p models
mkdir -p logs

echo ""
echo "======================================"
echo "✓ Setup complete!"
echo "======================================"
echo ""
echo "To activate the environment in the future:"
echo "  source .venv/bin/activate"
echo ""
echo "To run the test pipeline:"
echo "  python scripts/run_test_pipeline.py"
echo ""

