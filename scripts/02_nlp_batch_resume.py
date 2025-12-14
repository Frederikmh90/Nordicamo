#!/usr/bin/env python3
"""
NLP Processing with Checkpoint Resume
Processes large datasets in batches with automatic checkpoint/resume
"""

import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime
import polars as pl
import json

# Import the NLP processor
sys.path.insert(0, '/work/NAMO_nov25')
from nlp_processor import NLPProcessor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('nlp_processing_batch.log')
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
        
        # Get URLs that have been processed
        if 'nlp_processed_at' in df.columns:
            processed = df.filter(pl.col('nlp_processed_at').is_not_null())
            urls = set(processed['url'].to_list())
            logger.info(f"📋 Found {len(urls):,} already-processed articles in checkpoint")
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
        # Append to existing file
        if output_file.endswith('.parquet'):
            existing = pl.read_parquet(output_file)
            combined = pl.concat([existing, df])
            combined.write_parquet(output_file)
        else:
            # For CSV, just append
            df.write_csv(output_file, append=True)
    else:
        # Create new file
        if output_file.endswith('.parquet'):
            df.write_parquet(output_file)
        else:
            df.write_csv(output_file)
    
    logger.info(f"💾 Checkpoint saved: {len(results)} articles → {output_file}")


def process_with_checkpoints(
    input_file: str,
    output_file: str,
    model_name: str = "mistralai/Mistral-7B-Instruct-v0.3",
    batch_size: int = 1000,
    checkpoint_interval: int = 1000,
    max_articles: int = None,
    resume: bool = True
):
    """Process articles with checkpointing and resume capability."""
    
    logger.info("="*80)
    logger.info("NLP Batch Processing with Checkpoint Resume")
    logger.info("="*80)
    logger.info(f"Input: {input_file}")
    logger.info(f"Output: {output_file}")
    logger.info(f"Model: {model_name}")
    logger.info(f"Batch size: {batch_size}")
    logger.info(f"Checkpoint interval: {checkpoint_interval}")
    logger.info(f"Resume: {resume}")
    logger.info("="*80)
    
    # Load input data
    logger.info(f"📂 Loading data from {input_file}")
    if input_file.endswith('.parquet'):
        df = pl.read_parquet(input_file)
    else:
        df = pl.read_csv(input_file, infer_schema_length=10000, ignore_errors=True)
    
    total_in_file = len(df)
    logger.info(f"Loaded {total_in_file:,} articles from input file")
    
    # Get already-processed URLs if resuming
    processed_urls = get_processed_urls(output_file) if resume else set()
    
    if processed_urls:
        # Filter out already-processed articles
        df = df.filter(~pl.col('url').is_in(list(processed_urls)))
        logger.info(f"Skipping {len(processed_urls):,} already-processed articles")
        logger.info(f"Remaining to process: {len(df):,} articles")
    
    if max_articles:
        df = df.head(max_articles)
        logger.info(f"Limiting to first {max_articles:,} articles")
    
    total_to_process = len(df)
    
    if total_to_process == 0:
        logger.info("✅ No articles to process! All done.")
        return
    
    # Initialize NLP processor
    logger.info("Initializing NLP Processor...")
    processor = NLPProcessor(model_name=model_name)
    logger.info("✓ NLP Processor initialized")
    
    # Process in batches
    results_buffer = []
    total_processed = 0
    checkpoint_counter = 0
    
    for i in range(0, total_to_process, batch_size):
        batch = df[i:i+batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total_to_process + batch_size - 1) // batch_size
        
        logger.info(f"")
        logger.info(f"{'='*80}")
        logger.info(f"Batch {batch_num}/{total_batches} ({len(batch)} articles)")
        logger.info(f"Progress: {total_processed}/{total_to_process} ({100*total_processed/total_to_process:.1f}%)")
        logger.info(f"{'='*80}")
        
        batch_results = []
        
        try:
            articles = batch.to_dicts()
            
            for idx, article in enumerate(articles):
                try:
                    # Get text content (analyzing 'content' column)
                    text = article.get('content', '') or article.get('description', '') or ''
                    
                    if not text or len(text) < 50:
                        logger.debug(f"Skipping article {i+idx} (insufficient content)")
                        continue
                    
                    # Process with NLP
                    nlp_result = processor.process_article(text)
                    
                    # Add NLP results to article
                    article['sentiment'] = nlp_result.get('sentiment')
                    article['sentiment_score'] = nlp_result.get('sentiment_score')
                    article['categories'] = nlp_result.get('categories', [])
                    article['entities'] = nlp_result.get('entities', [])
                    article['nlp_processed_at'] = datetime.now().isoformat()
                    
                    batch_results.append(article)
                    total_processed += 1
                    
                    if (total_processed % 100) == 0:
                        logger.info(f"✓ Processed {total_processed}/{total_to_process} articles ({100*total_processed/total_to_process:.1f}%)")
                
                except Exception as e:
                    logger.error(f"Error processing article {i+idx}: {e}")
                    continue
            
            # Add batch results to buffer
            results_buffer.extend(batch_results)
            checkpoint_counter += len(batch_results)
            
            # Save checkpoint if interval reached
            if checkpoint_counter >= checkpoint_interval:
                logger.info(f"")
                logger.info(f"{'*'*80}")
                logger.info(f"CHECKPOINT: Saving {len(results_buffer)} articles...")
                logger.info(f"{'*'*80}")
                
                save_checkpoint(results_buffer, output_file, mode='append')
                
                # Clear buffer after successful save
                results_buffer = []
                checkpoint_counter = 0
                
                logger.info(f"✓ Checkpoint saved successfully")
                logger.info(f"Total saved so far: {total_processed:,} articles")
        
        except Exception as e:
            logger.error(f"Error processing batch {batch_num}: {e}")
            # Save what we have so far before continuing
            if results_buffer:
                logger.info(f"Saving {len(results_buffer)} articles before continuing...")
                save_checkpoint(results_buffer, output_file, mode='append')
                results_buffer = []
                checkpoint_counter = 0
            continue
    
    # Final save of remaining results
    if results_buffer:
        logger.info(f"")
        logger.info(f"{'*'*80}")
        logger.info(f"FINAL SAVE: {len(results_buffer)} articles")
        logger.info(f"{'*'*80}")
        save_checkpoint(results_buffer, output_file, mode='append')
    
    logger.info("")
    logger.info("="*80)
    logger.info("✅ Processing Complete!")
    logger.info("="*80)
    logger.info(f"Total articles processed: {total_processed:,}")
    logger.info(f"Output saved to: {output_file}")
    logger.info("="*80)


def main():
    parser = argparse.ArgumentParser(description='NLP Batch Processing with Resume')
    parser.add_argument('--input', '-i', required=True, help='Input file (CSV or Parquet)')
    parser.add_argument('--output', '-o', required=True, help='Output file (CSV or Parquet)')
    parser.add_argument('--model', '-m', default='mistralai/Mistral-7B-Instruct-v0.3',
                       help='Model name')
    parser.add_argument('--batch-size', '-b', type=int, default=1000,
                       help='Batch size (default: 1000)')
    parser.add_argument('--checkpoint', '-c', type=int, default=1000,
                       help='Checkpoint interval (default: 1000)')
    parser.add_argument('--max-articles', '-n', type=int, default=None,
                       help='Max articles to process (default: all)')
    parser.add_argument('--no-resume', action='store_true',
                       help='Start fresh (ignore existing checkpoint)')
    
    args = parser.parse_args()
    
    try:
        process_with_checkpoints(
            input_file=args.input,
            output_file=args.output,
            model_name=args.model,
            batch_size=args.batch_size,
            checkpoint_interval=args.checkpoint,
            max_articles=args.max_articles,
            resume=not args.no_resume
        )
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == '__main__':
    main()

