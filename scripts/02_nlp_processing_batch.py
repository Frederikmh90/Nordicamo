"""
NAMO NLP Processing Pipeline - Batch Processing Version
========================================================
Processes articles in chunks to avoid overwhelming the server.
Designed to process large datasets incrementally (e.g., 1000 articles in batches of 100).

Usage:
    python scripts/02_nlp_processing_batch.py \
        --input /path/to/data.parquet \
        --output-dir /path/to/output \
        --total-articles 1000 \
        --chunk-size 100 \
        --start-from 0
"""

import polars as pl
import json
import os
import time
from pathlib import Path
from typing import List, Dict, Optional
from tqdm import tqdm
import logging
from datetime import datetime
import argparse
import sys

# Import the NLPProcessor from the main script
# Add parent directory to path to import from scripts
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Import NLPProcessor - we'll use exec to load it
import importlib.util
nlp_script_path = Path(__file__).parent / "02_nlp_processing.py"
spec = importlib.util.spec_from_file_location("nlp_processing", nlp_script_path)
nlp_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nlp_module)
NLPProcessor = nlp_module.NLPProcessor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def process_chunk(
    processor: NLPProcessor,
    chunk_df: pl.DataFrame,
    chunk_num: int,
    total_chunks: int
) -> pl.DataFrame:
    """Process a single chunk of articles."""
    logger.info(f"Processing chunk {chunk_num}/{total_chunks} ({len(chunk_df)} articles)...")
    start_time = time.time()
    
    results = []
    for row in tqdm(chunk_df.iter_rows(named=True), total=len(chunk_df), desc=f"Chunk {chunk_num}"):
        content = row.get("content", "")
        title = row.get("title", "")
        description = row.get("description", "")
        
        if not content or len(content.strip()) < 50:
            content = f"{title}\n\n{description}".strip()
            if len(content) < 50:
                results.append({
                    "sentiment": "neutral",
                    "sentiment_score": 0.0,
                    "categories": ["Other"],
                    "entities": {"persons": [], "locations": [], "organizations": []},
                    "nlp_processed_at": datetime.now().isoformat(),
                })
                continue
        
        country = row.get("country", "")
        result = processor.process_article(content, country)
        results.append(result)
    
    # Add results to dataframe
    chunk_df = chunk_df.with_columns([
        pl.Series("sentiment", [r["sentiment"] for r in results]),
        pl.Series("sentiment_score", [r["sentiment_score"] for r in results]),
        pl.Series("categories", [json.dumps(r["categories"]) for r in results]),
        pl.Series("entities_json", [json.dumps(r["entities"]) for r in results]),
        pl.Series("nlp_processed_at", [r["nlp_processed_at"] for r in results]),
    ])
    
    elapsed = time.time() - start_time
    avg_time = elapsed / len(chunk_df)
    logger.info(f"✓ Chunk {chunk_num} completed in {elapsed:.1f}s ({avg_time:.1f}s/article)")
    
    return chunk_df


def main():
    parser = argparse.ArgumentParser(
        description="NAMO NLP Processing Pipeline - Batch Processing"
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Input parquet file path"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Output directory for processed chunks"
    )
    parser.add_argument(
        "--total-articles",
        type=int,
        default=1000,
        help="Total number of articles to process (default: 1000)"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=100,
        help="Number of articles per chunk (default: 100)"
    )
    parser.add_argument(
        "--start-from",
        type=int,
        default=0,
        help="Start from article index (for resuming) (default: 0)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="mistralai/Mistral-7B-Instruct-v0.3",
        help="LLM model to use"
    )
    parser.add_argument(
        "--use-quantization",
        action="store_true",
        help="Enable 4-bit quantization (saves GPU memory)"
    )
    
    args = parser.parse_args()
    
    # Load data
    logger.info(f"Loading data from {args.input}")
    df = pl.read_parquet(args.input)
    logger.info(f"Loaded {len(df)} total articles")
    
    # Determine range to process
    end_idx = min(args.start_from + args.total_articles, len(df))
    df_to_process = df[args.start_from:end_idx]
    logger.info(f"Processing articles {args.start_from} to {end_idx-1} ({len(df_to_process)} articles)")
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize NLP processor (once, reused for all chunks)
    logger.info("Initializing NLP Processor...")
    processor = NLPProcessor(
        model_name=args.model,
        use_quantization=args.use_quantization,
        batch_size=1,  # Process one at a time to avoid memory issues
    )
    logger.info("✓ NLP Processor initialized")
    
    # Process in chunks
    total_chunks = (len(df_to_process) + args.chunk_size - 1) // args.chunk_size
    all_results = []
    
    logger.info(f"Processing {len(df_to_process)} articles in {total_chunks} chunks of {args.chunk_size}")
    logger.info("=" * 80)
    
    for chunk_num in range(total_chunks):
        start_idx = chunk_num * args.chunk_size
        end_idx_chunk = min(start_idx + args.chunk_size, len(df_to_process))
        chunk_df = df_to_process[start_idx:end_idx_chunk]
        
        # Process chunk
        processed_chunk = process_chunk(processor, chunk_df, chunk_num + 1, total_chunks)
        all_results.append(processed_chunk)
        
        # Save chunk immediately (for safety)
        chunk_output = output_dir / f"chunk_{chunk_num + 1:04d}.parquet"
        processed_chunk.write_parquet(chunk_output)
        logger.info(f"✓ Saved chunk to {chunk_output}")
        
        # Small delay between chunks to avoid overwhelming GPU
        if chunk_num < total_chunks - 1:
            time.sleep(2)
    
    # Combine all chunks
    logger.info("Combining all chunks...")
    final_df = pl.concat(all_results)
    
    # Save final combined file
    final_output = output_dir / f"nlp_enriched_{args.start_from}_{args.start_from + len(df_to_process) - 1}.parquet"
    final_df.write_parquet(final_output)
    logger.info(f"✓ Final combined file saved: {final_output}")
    
    # Summary
    logger.info("=" * 80)
    logger.info("PROCESSING COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total articles processed: {len(final_df)}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Final file: {final_output}")
    
    # Show sample
    print("\n" + "=" * 80)
    print("Sample of processed data:")
    print("=" * 80)
    print(final_df.select(["title", "sentiment", "categories", "entities_json"]).head(3))


if __name__ == "__main__":
    main()

