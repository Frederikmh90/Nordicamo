#!/usr/bin/env python3
"""
Run category classification on 1000 articles, load to database, and update dashboard.
"""

import polars as pl
from pathlib import Path
import subprocess
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run category classification on 1000 articles")
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/NAMO_preprocessed_test.parquet",
        help="Input parquet file",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="mistralai/Mistral-7B-Instruct-v0.3",
        help="Model to use",
    )
    parser.add_argument(
        "--skip-classification",
        action="store_true",
        help="Skip classification (use existing results)",
    )
    parser.add_argument(
        "--skip-db",
        action="store_true",
        help="Skip database loading",
    )
    
    args = parser.parse_args()
    
    # Step 1: Create sample of 1000 articles
    logger.info("=" * 60)
    logger.info("Step 1: Creating sample of 1000 articles")
    logger.info("=" * 60)
    
    input_path = BASE_DIR / args.input
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return
    
    df = pl.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} articles from {input_path}")
    
    # Take first 1000 articles
    df_sample = df.head(1000)
    sample_path = BASE_DIR / "data" / "processed" / "sample_1000.parquet"
    sample_path.parent.mkdir(parents=True, exist_ok=True)
    df_sample.write_parquet(sample_path)
    logger.info(f"✅ Created sample: {sample_path} ({len(df_sample)} articles)")
    
    # Step 2: Run category classification
    # NOTE: This step requires GPU and PyTorch - should run on VM
    # This script is meant to be run on the VM where GPU/dependencies are available
    if not args.skip_classification:
        logger.info("=" * 60)
        logger.info("Step 2: Running category classification")
        logger.info("=" * 60)
        logger.info("⚠️  NOTE: This requires GPU and PyTorch - should run on VM!")
        logger.info("   If running locally, use --skip-classification and run classification on VM separately")
        
        output_path = BASE_DIR / "data" / "nlp_enriched" / "sample_1000_categories.parquet"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            "python3",
            str(BASE_DIR / "scripts" / "26_category_classification_only.py"),
            "--input", str(sample_path),
            "--output", str(output_path),
            "--model", args.model,
            "--no-quantization",
        ]
        
        logger.info(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=BASE_DIR)
        
        if result.returncode != 0:
            logger.error("❌ Classification failed")
            logger.error("   This likely means PyTorch is not installed locally.")
            logger.error("   Run classification on VM instead, then use --skip-classification here.")
            return
        
        logger.info(f"✅ Classification complete: {output_path}")
    else:
        output_path = BASE_DIR / "data" / "nlp_enriched" / "sample_1000_categories.parquet"
        logger.info(f"⏭️  Skipping classification, using: {output_path}")
    
    # Step 3: Load to database
    if not args.skip_db:
        logger.info("=" * 60)
        logger.info("Step 3: Loading categories to database")
        logger.info("=" * 60)
        
        cmd = [
            "python3",
            str(BASE_DIR / "scripts" / "28_load_categories_to_db.py"),
            "--input", str(output_path),
        ]
        
        logger.info(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=BASE_DIR)
        
        if result.returncode != 0:
            logger.error("❌ Database loading failed")
            return
        
        logger.info("✅ Categories loaded to database")
    
    # Step 4: Summary
    logger.info("=" * 60)
    logger.info("Step 4: Summary")
    logger.info("=" * 60)
    
    if output_path.exists():
        df_result = pl.read_parquet(output_path)
        category_counts = df_result["category"].value_counts().sort("count", descending=True)
        
        logger.info("\n📊 Category Distribution:")
        for row in category_counts.iter_rows(named=True):
            logger.info(f"  {row['category']}: {row['count']} ({row['count']/len(df_result)*100:.1f}%)")
    
    logger.info("\n✅ All steps complete!")
    logger.info("\nNext steps:")
    logger.info("1. Start backend: cd backend && uvicorn app.main:app --reload")
    logger.info("2. Start frontend: streamlit run frontend/app.py")
    logger.info("3. Check dashboard for category visualizations")


if __name__ == "__main__":
    main()

