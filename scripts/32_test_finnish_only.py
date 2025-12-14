#!/usr/bin/env python3
"""
Test category classification on Finnish articles only.
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
    """Test Finnish articles only."""
    logger.info("=" * 60)
    logger.info("Testing Category Classification on Finnish Articles Only")
    logger.info("=" * 60)
    
    # Load data
    input_path = BASE_DIR / "data" / "processed" / "NAMO_preprocessed_test.parquet"
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return
    
    logger.info(f"Loading data from {input_path}")
    df = pl.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} total articles")
    
    # Filter for Finnish articles only
    df_finnish = df.filter(pl.col("country") == "finland")
    logger.info(f"Found {len(df_finnish)} Finnish articles")
    
    if len(df_finnish) == 0:
        logger.error("No Finnish articles found!")
        return
    
    # Take first 50 Finnish articles for quick test
    df_sample = df_finnish.head(50)
    sample_path = BASE_DIR / "data" / "processed" / "sample_finnish_50.parquet"
    sample_path.parent.mkdir(parents=True, exist_ok=True)
    df_sample.write_parquet(sample_path)
    logger.info(f"✅ Created Finnish sample: {sample_path} ({len(df_sample)} articles)")
    
    # Run classification
    output_path = BASE_DIR / "data" / "nlp_enriched" / "sample_finnish_50_categories.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        "python3",
        str(BASE_DIR / "scripts" / "26_category_classification_only.py"),
        "--input", str(sample_path),
        "--output", str(output_path),
        "--model", "mistralai/Mistral-7B-Instruct-v0.3",
        "--no-quantization",
    ]
    
    logger.info("=" * 60)
    logger.info("Running classification on Finnish articles...")
    logger.info("=" * 60)
    logger.info(f"Command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, cwd=BASE_DIR)
    
    if result.returncode != 0:
        logger.error("❌ Classification failed")
        return
    
    # Analyze results
    if output_path.exists():
        df_result = pl.read_parquet(output_path)
        category_counts = df_result["category"].value_counts().sort("count", descending=True)
        
        logger.info("\n" + "=" * 60)
        logger.info("📊 Finnish Articles - Category Distribution:")
        logger.info("=" * 60)
        for row in category_counts.iter_rows(named=True):
            logger.info(f"  {row['category']}: {row['count']} ({row['count']/len(df_result)*100:.1f}%)")
        
        # Check for "Other" category
        other_count = df_result.filter(pl.col("category") == "Other").height
        logger.info(f"\n⚠️  Articles classified as 'Other': {other_count} ({other_count/len(df_result)*100:.1f}%)")
        
        # Show some examples of "Other" if any
        if other_count > 0:
            logger.info("\nExamples of 'Other' classifications:")
            other_df = df_result.filter(pl.col("category") == "Other")
            for i, row in enumerate(other_df.head(5).iter_rows(named=True)):
                logger.info(f"\n  {i+1}. URL: {row.get('url', 'N/A')[:80]}...")
                logger.info(f"     Reasoning: {row.get('category_reasoning', 'N/A')[:100]}...")
    
    logger.info("\n✅ Finnish test complete!")

if __name__ == "__main__":
    main()

