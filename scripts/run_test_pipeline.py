"""
Test Pipeline Runner
====================
Runs the complete preprocessing pipeline on a small test set to verify everything works.
"""

import subprocess
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent


def run_command(cmd: list, description: str):
    """Run a command and log results."""
    logger.info("=" * 80)
    logger.info(f"STEP: {description}")
    logger.info(f"Command: {' '.join(cmd)}")
    logger.info("=" * 80)
    
    # Use python3 if first arg is sys.executable
    if cmd and str(cmd[0]).endswith('python'):
        cmd[0] = 'python3'
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False, text=True)
        logger.info(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ {description} failed with error code {e.returncode}")
        return False


def main():
    """Run the test pipeline."""
    logger.info("\n" + "=" * 80)
    logger.info("NAMO TEST PIPELINE")
    logger.info("=" * 80 + "\n")
    
    # Step 1: Basic preprocessing
    logger.info("Step 1: Running basic preprocessing on test data...")
    success = run_command(
        [sys.executable, str(BASE_DIR / "scripts" / "01_data_preprocessing.py"), "--test", "--test-size", "100"],
        "Basic Preprocessing (100 articles)"
    )
    
    if not success:
        logger.error("Pipeline failed at Step 1")
        return
    
    # Step 2: Check if spaCy model is installed
    logger.info("\nStep 2: Checking NLP dependencies...")
    logger.info("Verifying spaCy multilingual model...")
    
    try:
        import spacy
        try:
            nlp = spacy.load("xx_ent_wiki_sm")
            logger.info("✓ spaCy multilingual model is installed")
        except OSError:
            logger.warning("⚠ spaCy multilingual model not found")
            logger.info("Installing spaCy model...")
            run_command(
                [sys.executable, "-m", "spacy", "download", "xx_ent_wiki_sm"],
                "Install spaCy model"
            )
    except ImportError:
        logger.warning("spaCy not installed yet")
    
    # Step 3: NLP processing
    logger.info("\nStep 3: Running NLP processing...")
    input_file = BASE_DIR / "data" / "processed" / "NAMO_preprocessed_test.parquet"
    
    if input_file.exists():
        success = run_command(
            [
                sys.executable,
                str(BASE_DIR / "scripts" / "02_nlp_processing.py"),
                "--input", str(input_file),
                "--batch-size", "4"
            ],
            "NLP Processing"
        )
        
        if not success:
            logger.error("Pipeline failed at Step 3")
            return
    else:
        logger.warning(f"Input file not found: {input_file}")
        logger.warning("Skipping NLP processing")
    
    logger.info("\n" + "=" * 80)
    logger.info("TEST PIPELINE COMPLETED!")
    logger.info("=" * 80)
    logger.info("\nNext steps:")
    logger.info("1. Review the processed data in: data/processed/")
    logger.info("2. Check NLP enriched data in: data/nlp_enriched/")
    logger.info("3. If test looks good, run on full dataset with --full flag")
    logger.info("4. Proceed to database setup and backend development")


if __name__ == "__main__":
    main()

