"""
Reprocess Articles Without Categories
=====================================
Reprocesses articles that don't have categories, assigning "Other" if needed.
"""

import polars as pl
import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "nlp_enriched"


def reprocess_missing_categories(input_path: Path, output_path: Path = None):
    """Reprocess articles without categories, assigning 'Other'."""
    logger.info(f"Loading data from {input_path}")
    df = pl.read_parquet(input_path)
    
    total = len(df)
    
    # Find articles without categories
    no_categories_mask = (
        (pl.col("categories").is_null()) | 
        (pl.col("categories") == "[]") |
        (pl.col("categories") == "")
    )
    
    no_categories_count = df.filter(no_categories_mask).shape[0]
    logger.info(f"Articles without categories: {no_categories_count} ({no_categories_count/total*100:.1f}%)")
    
    # Assign "Other" category to articles without categories
    df_fixed = df.with_columns([
        pl.when(no_categories_mask)
        .then(pl.lit('["Other"]'))
        .otherwise(pl.col("categories"))
        .alias("categories")
    ])
    
    # Verify fix
    still_missing = df_fixed.filter(
        (pl.col("categories").is_null()) | 
        (pl.col("categories") == "[]") |
        (pl.col("categories") == "")
    ).shape[0]
    
    logger.info(f"\nAfter fixing:")
    logger.info(f"  Articles with categories: {total - still_missing} ({100 - still_missing/total*100:.1f}%)")
    logger.info(f"  Articles still without categories: {still_missing}")
    
    # Count "Other" assignments
    other_count = df_fixed.filter(pl.col("categories") == '["Other"]').shape[0]
    logger.info(f"  Articles assigned 'Other': {other_count}")
    
    # Save fixed data
    if output_path is None:
        output_path = input_path.parent / f"{input_path.stem}_with_other.parquet"
    
    df_fixed.write_parquet(output_path)
    logger.info(f"\nFixed data saved to: {output_path}")
    
    return df_fixed, output_path


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Reprocess articles without categories')
    parser.add_argument('--input', type=str, required=True, help='Input parquet file')
    parser.add_argument('--output', type=str, help='Output parquet file (default: adds _with_other suffix)')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else None
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
    else:
        reprocess_missing_categories(input_path, output_path)

