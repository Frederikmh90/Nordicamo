#!/bin/bash
# Install NLP processing dependencies on remote server
# Run this on the remote server after SSH connection

set -e

echo "=========================================="
echo "Installing NLP Processing Dependencies"
echo "=========================================="

# Check if uv is available, otherwise use pip3
if command -v uv &> /dev/null; then
    echo "Using uv for installation..."
    INSTALL_CMD="uv pip install"
else
    echo "Using pip3 for installation..."
    INSTALL_CMD="pip3 install"
fi

# Core packages needed for NLP processing
echo ""
echo "Installing core packages..."
$INSTALL_CMD torch>=2.0.0 --index-url https://download.pytorch.org/whl/cu121
$INSTALL_CMD transformers>=4.35.0
$INSTALL_CMD accelerate>=0.24.0
$INSTALL_CMD polars>=0.20.0
$INSTALL_CMD psycopg2-binary>=2.9.9
$INSTALL_CMD python-dotenv>=1.0.0
$INSTALL_CMD tqdm>=4.66.0
$INSTALL_CMD spacy>=3.7.0

# Download spaCy model
echo ""
echo "Downloading spaCy multilingual model..."
python3 -m spacy download xx_ent_wiki_sm

echo ""
echo "=========================================="
echo "✅ Installation complete!"
echo "=========================================="
echo ""
echo "Verify installation:"
echo "  python3 -c 'import torch; print(f\"PyTorch: {torch.__version__}\"); print(f\"CUDA available: {torch.cuda.is_available()}\")'"
echo "  python3 -c 'import transformers; print(f\"Transformers: {transformers.__version__}\")'"
echo "  python3 -c 'import polars; print(f\"Polars: {polars.__version__}\")'"


