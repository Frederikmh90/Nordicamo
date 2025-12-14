#!/usr/bin/env python3
"""
High-performance NLP processing using vLLM with Mistral-Small-3.1-24B
Batch processing with checkpointing and resume capability
"""

import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime
import polars as pl

sys.path.insert(0, '/work/NAMO_nov25/scripts')
from vllm_nlp_processor import VLLMNLPProcessor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('nlp_vllm_processing.log')
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
    
    logger.info(f"💾 Saved {len(results)} articles")


def process_with_vllm(
    input_file: str,
    output_file: str,
    model_name: str = "mistralai/Mistral-Small-3.1-24B-Instruct-2503",
    vllm_batch_size: int = 16,  # Process this many articles at once
    checkpoint_interval: int = 1000,
    max_articles: int = None,
    tensor_parallel_size: int = 1,
    resume: bool = True
):
    """
    Process articles using vLLM for high-throughput inference.
    """
    
    logger.info("="*80)
    logger.info("vLLM NLP Processing - Mistral-Small-3.1-24B")
    logger.info("="*80)
    logger.info(f"Input: {input_file}")
    logger.info(f"Output: {output_file}")
    logger.info(f"Model: {model_name}")
    logger.info(f"vLLM batch size: {vllm_batch_size} articles in parallel")
    logger.info(f"Checkpoint: Every {checkpoint_interval} articles")
    logger.info(f"Tensor parallel: {tensor_parallel_size}")
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
    
    # Initialize vLLM processor
    logger.info(f"🚀 Initializing vLLM processor...")
    processor = VLLMNLPProcessor(
        model_name=model_name,
        tensor_parallel_size=tensor_parallel_size
    )
    logger.info("✓ vLLM ready")
    
    # Process in batches
    results_buffer = []
    total_processed = 0
    
    articles_list = df.to_dicts()
    
    for i in range(0, total_to_process, vllm_batch_size):
        batch_articles = articles_list[i:i+vllm_batch_size]
        batch_num = i // vllm_batch_size + 1
        total_batches = (total_to_process + vllm_batch_size - 1) // vllm_batch_size
        
        logger.info(f"")
        logger.info(f"Batch {batch_num}/{total_batches}: Processing {len(batch_articles)} articles...")
        
        try:
            # Process batch with vLLM
            enriched = processor.process_articles_batch(batch_articles)
            
            results_buffer.extend(enriched)
            total_processed += len(enriched)
            
            if total_processed % 100 == 0:
                logger.info(f"✓ {total_processed}/{total_to_process} ({100*total_processed/total_to_process:.1f}%)")
            
            # Checkpoint
            if len(results_buffer) >= checkpoint_interval:
                logger.info(f"")
                logger.info(f"{'*'*80}")
                logger.info(f"💾 CHECKPOINT: Saving {len(results_buffer)} articles...")
                save_checkpoint(results_buffer, output_file, mode='append')
                results_buffer = []
                logger.info(f"✓ Checkpoint saved. Total: {total_processed:,}")
                logger.info(f"{'*'*80}")
        
        except Exception as e:
            logger.error(f"Batch {batch_num} error: {e}")
            # Save what we have
            if results_buffer:
                save_checkpoint(results_buffer, output_file, mode='append')
                results_buffer = []
            continue
    
    # Final save
    if results_buffer:
        logger.info(f"")
        logger.info(f"{'*'*80}")
        logger.info(f"💾 Final save: {len(results_buffer)} articles")
        save_checkpoint(results_buffer, output_file, mode='append')
        logger.info(f"{'*'*80}")
    
    logger.info("")
    logger.info("="*80)
    logger.info(f"✅ Complete! Processed {total_processed:,} articles")
    logger.info(f"Output: {output_file}")
    logger.info("="*80)


def main():
    parser = argparse.ArgumentParser(description='vLLM NLP Processing')
    parser.add_argument('--input', '-i', required=True)
    parser.add_argument('--output', '-o', required=True)
    parser.add_argument('--model', '-m', 
                       default='mistralai/Mistral-Small-3.1-24B-Instruct-2503')
    parser.add_argument('--vllm-batch-size', '-v', type=int, default=16,
                       help='Articles to process in parallel (default: 16)')
    parser.add_argument('--checkpoint', '-c', type=int, default=1000)
    parser.add_argument('--max-articles', '-n', type=int, default=None)
    parser.add_argument('--tensor-parallel', '-t', type=int, default=1,
                       help='Tensor parallelism for multi-GPU (default: 1)')
    parser.add_argument('--no-resume', action='store_true')
    
    args = parser.parse_args()
    
    try:
        process_with_vllm(
            input_file=args.input,
            output_file=args.output,
            model_name=args.model,
            vllm_batch_size=args.vllm_batch_size,
            checkpoint_interval=args.checkpoint,
            max_articles=args.max_articles,
            tensor_parallel_size=args.tensor_parallel,
            resume=not args.no_resume
        )
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == '__main__':
    main()

