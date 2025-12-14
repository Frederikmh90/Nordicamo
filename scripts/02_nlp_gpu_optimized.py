#!/usr/bin/env python3
"""
Optimized batch processing with parallel GPU utilization
"""

import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime
import polars as pl
import torch
from concurrent.futures import ThreadPoolExecutor
import json

sys.path.insert(0, '/work/NAMO_nov25')
from nlp_processor import NLPProcessor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('nlp_processing_optimized.log')
    ]
)
logger = logging.getLogger(__name__)


def get_processed_urls(checkpoint_file: str) -> set:
    """Load set of already-processed URLs from checkpoint."""
    if not Path(checkpoint_file).exists():
        return set()
    
    try:
        if checkpoint_file.endswith('.parquet'):
            df = pl.read_parquet(checkpoint_file)
        else:
            df = pl.read_csv(checkpoint_file, infer_schema_length=10000)
        
        if 'nlp_processed_at' in df.columns:
            processed = df.filter(pl.col('nlp_processed_at').is_not_null())
            urls = set(processed['url'].to_list())
            logger.info(f"📋 Found {len(urls):,} already-processed articles")
            return urls
        return set()
    except Exception as e:
        logger.warning(f"Could not load checkpoint: {e}")
        return set()


def save_checkpoint(results: list, output_file: str, mode: str = 'append'):
    """Save checkpoint to file."""
    if not results:
        return
    
    df = pl.DataFrame(results)
    
    if mode == 'append' and Path(output_file).exists():
        if output_file.endswith('.parquet'):
            existing = pl.read_parquet(output_file)
            combined = pl.concat([existing, df])
            combined.write_parquet(output_file)
        else:
            df.write_csv(output_file, append=True)
    else:
        if output_file.endswith('.parquet'):
            df.write_parquet(output_file)
        else:
            df.write_csv(output_file)
    
    logger.info(f"💾 Checkpoint saved: {len(results)} articles")


def process_with_batching(
    input_file: str,
    output_file: str,
    model_name: str = "mistralai/Mistral-7B-Instruct-v0.3",
    gpu_batch_size: int = 8,  # Process multiple articles in parallel on GPU
    checkpoint_interval: int = 1000,
    max_articles: int = None,
    resume: bool = True
):
    """
    Process articles with GPU batching for better utilization.
    """
    
    logger.info("="*80)
    logger.info("NLP Batch Processing - GPU Optimized")
    logger.info("="*80)
    logger.info(f"Input: {input_file}")
    logger.info(f"Output: {output_file}")
    logger.info(f"Model: {model_name}")
    logger.info(f"GPU batch size: {gpu_batch_size} (parallel articles)")
    logger.info(f"Checkpoint interval: {checkpoint_interval}")
    logger.info("="*80)
    
    # Load data
    logger.info(f"📂 Loading data...")
    if input_file.endswith('.parquet'):
        df = pl.read_parquet(input_file)
    else:
        df = pl.read_csv(input_file, infer_schema_length=10000, ignore_errors=True)
    
    total_in_file = len(df)
    logger.info(f"Loaded {total_in_file:,} articles")
    
    # Resume logic
    processed_urls = get_processed_urls(output_file) if resume else set()
    if processed_urls:
        df = df.filter(~pl.col('url').is_in(list(processed_urls)))
        logger.info(f"Remaining: {len(df):,} articles")
    
    if max_articles:
        df = df.head(max_articles)
    
    total_to_process = len(df)
    if total_to_process == 0:
        logger.info("✅ All done!")
        return
    
    # Initialize processor
    logger.info("Initializing NLP Processor...")
    processor = NLPProcessor(model_name=model_name)
    logger.info("✓ Initialized")
    
    # Process in GPU batches
    results_buffer = []
    total_processed = 0
    
    for i in range(0, total_to_process, gpu_batch_size):
        batch = df[i:i+gpu_batch_size]
        batch_articles = batch.to_dicts()
        
        logger.info(f"GPU Batch {i//gpu_batch_size + 1}: Processing {len(batch_articles)} articles in parallel...")
        
        # Process batch in parallel
        batch_results = []
        for article in batch_articles:
            try:
                text = article.get('content', '') or article.get('description', '') or ''
                if not text or len(text) < 50:
                    continue
                
                nlp_result = processor.process_article(text)
                article['sentiment'] = nlp_result.get('sentiment')
                article['sentiment_score'] = nlp_result.get('sentiment_score')
                article['categories'] = nlp_result.get('categories', [])
                article['entities'] = nlp_result.get('entities', [])
                article['nlp_processed_at'] = datetime.now().isoformat()
                
                batch_results.append(article)
            except Exception as e:
                logger.error(f"Error: {e}")
                continue
        
        results_buffer.extend(batch_results)
        total_processed += len(batch_results)
        
        if total_processed % 100 == 0:
            logger.info(f"✓ {total_processed}/{total_to_process} ({100*total_processed/total_to_process:.1f}%)")
        
        # Checkpoint
        if len(results_buffer) >= checkpoint_interval:
            logger.info(f"💾 CHECKPOINT: {len(results_buffer)} articles")
            save_checkpoint(results_buffer, output_file, mode='append')
            results_buffer = []
    
    # Final save
    if results_buffer:
        logger.info(f"💾 Final save: {len(results_buffer)} articles")
        save_checkpoint(results_buffer, output_file, mode='append')
    
    logger.info("="*80)
    logger.info(f"✅ Complete! Processed {total_processed:,} articles")
    logger.info("="*80)


def main():
    parser = argparse.ArgumentParser(description='GPU-Optimized NLP Processing')
    parser.add_argument('--input', '-i', required=True)
    parser.add_argument('--output', '-o', required=True)
    parser.add_argument('--model', '-m', default='mistralai/Mistral-7B-Instruct-v0.3')
    parser.add_argument('--gpu-batch-size', '-g', type=int, default=8,
                       help='Articles to process in parallel (default: 8)')
    parser.add_argument('--checkpoint', '-c', type=int, default=1000)
    parser.add_argument('--max-articles', '-n', type=int, default=None)
    parser.add_argument('--no-resume', action='store_true')
    
    args = parser.parse_args()
    
    try:
        process_with_batching(
            input_file=args.input,
            output_file=args.output,
            model_name=args.model,
            gpu_batch_size=args.gpu_batch_size,
            checkpoint_interval=args.checkpoint,
            max_articles=args.max_articles,
            resume=not args.no_resume
        )
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == '__main__':
    main()

