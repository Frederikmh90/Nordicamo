#!/usr/bin/env python3
"""
Two-phase automated NLP processing with vLLM
Phase 1: 10% stratified sample → saved separately
Phase 2: Remaining 90% → continues automatically
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
        logging.FileHandler('nlp_vllm_full_run.log')
    ]
)
logger = logging.getLogger(__name__)


def save_checkpoint(results: list, output_file: str, mode: str = 'append'):
    """Save checkpoint to file."""
    if not results:
        return
    
    df = pl.DataFrame(results)
    
    if mode == 'append' and Path(output_file).exists():
        existing = pl.read_parquet(output_file)
        combined = pl.concat([existing, df])
        combined.write_parquet(output_file)
    else:
        df.write_parquet(output_file)
    
    logger.info(f"💾 Saved {len(results)} articles to {output_file}")


def process_phase(
    processor: VLLMNLPProcessor,
    input_file: str,
    output_file: str,
    phase_name: str,
    vllm_batch_size: int = 16,
    checkpoint_interval: int = 1000,
    processed_urls: set = None
):
    """Process a single phase."""
    
    logger.info("")
    logger.info("="*80)
    logger.info(f"{phase_name} - Starting")
    logger.info("="*80)
    logger.info(f"Input: {input_file}")
    logger.info(f"Output: {output_file}")
    
    # Load data
    logger.info(f"📂 Loading data...")
    df = pl.read_parquet(input_file)
    total_in_file = len(df)
    logger.info(f"Loaded {total_in_file:,} articles")
    
    # Skip already processed
    if processed_urls:
        df = df.filter(~pl.col('url').is_in(list(processed_urls)))
        logger.info(f"Skipping {total_in_file - len(df):,} already processed")
        logger.info(f"Remaining: {len(df):,} articles")
    
    total_to_process = len(df)
    if total_to_process == 0:
        logger.info("✅ Nothing to process!")
        return set()
    
    # Process in batches
    results_buffer = []
    total_processed = 0
    processed_urls_new = set()
    
    articles_list = df.to_dicts()
    
    for i in range(0, total_to_process, vllm_batch_size):
        batch_articles = articles_list[i:i+vllm_batch_size]
        batch_num = i // vllm_batch_size + 1
        total_batches = (total_to_process + vllm_batch_size - 1) // vllm_batch_size
        
        if batch_num % 10 == 1 or batch_num == total_batches:
            logger.info(f"")
            logger.info(f"Batch {batch_num}/{total_batches}: Processing {len(batch_articles)} articles...")
        
        try:
            # Process batch with vLLM
            enriched = processor.process_articles_batch(batch_articles)
            
            results_buffer.extend(enriched)
            total_processed += len(enriched)
            
            # Track URLs
            for article in enriched:
                processed_urls_new.add(article['url'])
            
            if total_processed % 1000 == 0:
                logger.info(f"✓ {total_processed:,}/{total_to_process:,} ({100*total_processed/total_to_process:.1f}%)")
            
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
    logger.info(f"✅ {phase_name} Complete! Processed {total_processed:,} articles")
    logger.info(f"Output: {output_file}")
    logger.info("="*80)
    
    return processed_urls_new


def main():
    parser = argparse.ArgumentParser(description='Two-phase vLLM NLP Processing')
    parser.add_argument('--full-dataset', required=True, help='Full dataset parquet file')
    parser.add_argument('--sample-10pct', required=True, help='10% stratified sample file')
    parser.add_argument('--output-10pct', required=True, help='Output for 10% sample')
    parser.add_argument('--output-full', required=True, help='Output for full dataset')
    parser.add_argument('--model', '-m', 
                       default='mistralai/Mistral-Small-3.1-24B-Instruct-2503')
    parser.add_argument('--vllm-batch-size', '-v', type=int, default=16)
    parser.add_argument('--checkpoint', '-c', type=int, default=1000)
    parser.add_argument('--tensor-parallel', '-t', type=int, default=1)
    
    args = parser.parse_args()
    
    start_time = datetime.now()
    
    logger.info("")
    logger.info("="*80)
    logger.info("TWO-PHASE AUTOMATED NLP PROCESSING")
    logger.info("="*80)
    logger.info(f"Model: {args.model}")
    logger.info(f"vLLM batch size: {args.vllm_batch_size}")
    logger.info(f"Checkpoint interval: {args.checkpoint}")
    logger.info(f"Start time: {start_time}")
    logger.info("="*80)
    
    try:
        # Initialize vLLM processor (once for both phases)
        logger.info(f"")
        logger.info(f"🚀 Initializing vLLM processor...")
        processor = VLLMNLPProcessor(
            model_name=args.model,
            tensor_parallel_size=args.tensor_parallel
        )
        logger.info("✓ vLLM ready")
        
        # PHASE 1: 10% Sample
        logger.info("")
        logger.info("🎯 Starting Phase 1: 10% Stratified Sample")
        processed_phase1 = process_phase(
            processor=processor,
            input_file=args.sample_10pct,
            output_file=args.output_10pct,
            phase_name="PHASE 1 (10% Sample)",
            vllm_batch_size=args.vllm_batch_size,
            checkpoint_interval=args.checkpoint
        )
        
        phase1_time = datetime.now()
        logger.info(f"")
        logger.info(f"✅ Phase 1 completed at {phase1_time}")
        logger.info(f"⏱️  Phase 1 duration: {phase1_time - start_time}")
        
        # PHASE 2: Remaining 90%
        logger.info("")
        logger.info("🎯 Starting Phase 2: Remaining 90%")
        logger.info("(This will take longer - the full dataset)")
        
        process_phase(
            processor=processor,
            input_file=args.full_dataset,
            output_file=args.output_full,
            phase_name="PHASE 2 (Remaining 90%)",
            vllm_batch_size=args.vllm_batch_size,
            checkpoint_interval=args.checkpoint,
            processed_urls=processed_phase1  # Skip already processed from Phase 1
        )
        
        end_time = datetime.now()
        
        logger.info("")
        logger.info("="*80)
        logger.info("🎉 ALL PROCESSING COMPLETE!")
        logger.info("="*80)
        logger.info(f"Phase 1 (10%): {args.output_10pct}")
        logger.info(f"Full dataset: {args.output_full}")
        logger.info(f"")
        logger.info(f"Start time:  {start_time}")
        logger.info(f"Phase 1 end: {phase1_time}")
        logger.info(f"End time:    {end_time}")
        logger.info(f"")
        logger.info(f"Phase 1 duration: {phase1_time - start_time}")
        logger.info(f"Phase 2 duration: {end_time - phase1_time}")
        logger.info(f"Total duration:   {end_time - start_time}")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == '__main__':
    main()

