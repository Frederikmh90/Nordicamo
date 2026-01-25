#!/bin/bash
# Script to run NLP processing on remote GPU server
# Usage: ./scripts/05_run_nlp_remote.sh [input_file] [batch_size]

set -e

# Configuration
REMOTE_HOST="<SERVER_HOST>"
REMOTE_PORT="2111"
REMOTE_USER="frede"
REMOTE_DIR="~/NAMO_nov25"
LOCAL_PROJECT_DIR="/Users/Codebase/projects/alterpublics/NAMO_nov25"

# Default values
INPUT_FILE="${1:-data/processed/NAMO_preprocessed_test.parquet}"
BATCH_SIZE="${2:-4}"

echo "=========================================="
echo "NAMO Remote NLP Processing Setup"
echo "=========================================="
echo ""
echo "Remote server: ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PORT}"
echo "Input file: ${INPUT_FILE}"
echo "Batch size: ${BATCH_SIZE}"
echo ""
echo "This script will:"
echo "1. Sync project files to remote server"
echo "2. Set up Python environment on remote"
echo "3. Run NLP processing with Qwen2.5"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."

# Check if input file exists locally
if [ ! -f "${LOCAL_PROJECT_DIR}/${INPUT_FILE}" ]; then
    echo "Error: Input file not found: ${LOCAL_PROJECT_DIR}/${INPUT_FILE}"
    exit 1
fi

echo ""
echo "Step 1: Syncing files to remote server..."
echo "----------------------------------------"

# Create remote directory structure
ssh -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST} << 'ENDSSH'
mkdir -p ~/NAMO_nov25/{scripts,data/processed,data/nlp_enriched,models,logs}
ENDSSH

# Sync necessary files
echo "Syncing scripts..."
rsync -avz -e "ssh -p ${REMOTE_PORT}" \
    ${LOCAL_PROJECT_DIR}/scripts/ \
    ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/scripts/

echo "Syncing input data..."
rsync -avz -e "ssh -p ${REMOTE_PORT}" \
    ${LOCAL_PROJECT_DIR}/${INPUT_FILE} \
    ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/${INPUT_FILE}

echo "Syncing requirements..."
rsync -avz -e "ssh -p ${REMOTE_PORT}" \
    ${LOCAL_PROJECT_DIR}/requirements.txt \
    ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/

echo ""
echo "Step 2: Setting up Python environment on remote..."
echo "----------------------------------------"

# Setup remote environment and run processing
ssh -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST} << ENDSSH
cd ${REMOTE_DIR}

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found. Please install Python 3."
    exit 1
fi

# Check if uv is available, otherwise use pip
if command -v uv &> /dev/null; then
    echo "Using uv for package management..."
    uv pip install -r requirements.txt
else
    echo "Using pip for package management..."
    python3 -m pip install --user -r requirements.txt
fi

# Download spaCy model if needed
python3 -m spacy download xx_ent_wiki_sm || echo "spaCy model download skipped (may already exist)"

echo ""
echo "Step 3: Running NLP processing..."
echo "----------------------------------------"
echo "This may take a while. Processing will run in the background."
echo "Check logs in: ${REMOTE_DIR}/logs/nlp_processing.log"
echo ""

# Run NLP processing (in background with nohup)
nohup python3 scripts/02_nlp_processing.py \
    --input ${INPUT_FILE} \
    --batch-size ${BATCH_SIZE} \
    > logs/nlp_processing.log 2>&1 &

echo "NLP processing started in background!"
echo "Process ID: \$!"
echo ""
echo "To check progress:"
echo "  tail -f ${REMOTE_DIR}/logs/nlp_processing.log"
echo ""
echo "To check if process is running:"
echo "  ps aux | grep nlp_processing"
ENDSSH

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "To monitor progress, run:"
echo "  ssh -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST} 'tail -f ${REMOTE_DIR}/logs/nlp_processing.log'"
echo ""
echo "To download results when complete:"
echo "  rsync -avz -e \"ssh -p ${REMOTE_PORT}\" \\"
echo "    ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/data/nlp_enriched/ \\"
echo "    ${LOCAL_PROJECT_DIR}/data/nlp_enriched/"

