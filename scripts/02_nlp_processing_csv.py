#!/usr/bin/env python3
"""
NLP Processing for CSV files (UCloud version)
Simplified version that reads from CSV and writes back to CSV
"""

import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime
import polars as pl

# Import the NLP processor
sys.path.insert(0, '/work/NAMO_nov25')
from nlp_processor import NLPProcessor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('nlp_processing_csv.log')
    ]
)
logger = logging.getLogger(__name__)


def process_csv(
    input_csv: str,
    output_csv: str,
    model_name: str = "mistralai/Mistral-7B-Instruct-v0.3",
    batch_size: int = 50,
    max_articles: int = None,
    checkpoint_interval: int = 1000
):
    """Process articles from CSV and save enriched results."""
    
    logger.info(f"📂 Loading data from {input_csv}")
    # Support both CSV and Parquet
    if input_csv.endswith('.parquet'):
        df = pl.read_parquet(input_csv)
    else:
        df = pl.read_csv(input_csv, infer_schema_length=10000, ignore_errors=True)
    
    if max_articles:
        df = df.head(max_articles)
        logger.info(f"Processing first {max_articles} articles")
    
    total = len(df)
    logger.info(f"Loaded {total:,} articles")
    
    # Initialize NLP processor
    logger.info("Initializing NLP Processor...")
    processor = NLPProcessor(model_name=model_name)
    logger.info("✓ NLP Processor initialized")
    
    # Process in batches
    results = []
    checkpoint_counter = 0
    
    for i in range(0, total, batch_size):
        batch = df[i:i+batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total + batch_size - 1) // batch_size
        
        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} articles)...")
        
        try:
            # Convert to dict format for processing
            articles = batch.to_dicts()
            
            # Process each article
            for idx, article in enumerate(articles):
                try:
                    # Get text content
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
                    
                    results.append(article)
                    
                    if (len(results) % 100) == 0:
                        logger.info(f"✓ Processed {len(results)}/{total} articles")
                    
                except Exception as e:
                    logger.error(f"Error processing article {i+idx}: {e}")
                    continue
            
            # Checkpoint save
            checkpoint_counter += len(batch)
            if checkpoint_counter >= checkpoint_interval:
                logger.info(f"💾 Checkpoint: Saving {len(results)} articles...")
                if output_csv.endswith('.parquet'):
                    pl.DataFrame(results).write_parquet(output_csv)
                else:
                    pl.DataFrame(results).write_csv(output_csv)
                checkpoint_counter = 0
                logger.info(f"✓ Checkpoint saved to {output_csv}")
        
        except Exception as e:
            logger.error(f"Error processing batch {batch_num}: {e}")
            continue
    
    # Final save
    logger.info(f"💾 Saving final results to {output_csv}")
    result_df = pl.DataFrame(results)
    if output_csv.endswith('.parquet'):
        result_df.write_parquet(output_csv)
    else:
        result_df.write_csv(output_csv)
    
    logger.info(f"✅ Processing complete!")
    logger.info(f"Total articles processed: {len(results):,}")
    logger.info(f"Output saved to: {output_csv}")
    
    return result_df


def main():
    parser = argparse.ArgumentParser(description='NLP Processing for CSV files')
    parser.add_argument('--input', '-i', required=True, help='Input CSV file')
    parser.add_argument('--output', '-o', required=True, help='Output CSV file')
    parser.add_argument('--model', '-m', default='mistralai/Mistral-7B-Instruct-v0.3',
                       help='Model name (default: Mistral-7B-Instruct-v0.3)')
    parser.add_argument('--batch-size', '-b', type=int, default=50,
                       help='Batch size (default: 50)')
    parser.add_argument('--max-articles', '-n', type=int, default=None,
                       help='Maximum articles to process (default: all)')
    parser.add_argument('--checkpoint', '-c', type=int, default=1000,
                       help='Save checkpoint every N articles (default: 1000)')
    
    args = parser.parse_args()
    
    logger.info("="*80)
    logger.info("NLP Processing (CSV Mode) - UCloud")
    logger.info("="*80)
    logger.info(f"Input file: {args.input}")
    logger.info(f"Output file: {args.output}")
    logger.info(f"Model: {args.model}")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Max articles: {args.max_articles or 'ALL'}")
    logger.info(f"Checkpoint interval: {args.checkpoint}")
    logger.info("="*80)
    
    try:
        process_csv(
            input_csv=args.input,
            output_csv=args.output,
            model_name=args.model,
            batch_size=args.batch_size,
            max_articles=args.max_articles,
            checkpoint_interval=args.checkpoint
        )
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == '__main__':
    main()

