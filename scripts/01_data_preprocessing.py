"""
NAMO Data Preprocessing Pipeline
=================================
This script performs initial data preprocessing for the Nordic Alternative Media Observatory:
1. Loads article and actor datasets
2. Merges partisan values from actor data
3. Performs NLP processing (sentiment, categorization, NER, link extraction)
4. Saves enriched dataset ready for PostgreSQL import

For ~1M articles, this will run in batches with progress tracking.
"""

import polars as pl
import pandas as pd
import numpy as np
from pathlib import Path
import json
import re
from datetime import datetime
from typing import List, Dict, Optional
from tqdm import tqdm
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('preprocessing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "data" / "processed"
OUTPUT_DIR.mkdir(exist_ok=True)

ARTICLE_PATH = DATA_DIR / "NAMO_2025_09.csv"
ACTOR_PATH = DATA_DIR / "NAMO_actor_251118.xlsx"

# News categories (10 categories + "Other" for alternative/hyper-partisan media)
NEWS_CATEGORIES = [
    "Politics & Governance",
    "Immigration & National Identity",
    "Health & Medicine",
    "Media & Censorship",
    "International Relations & Conflict",
    "Economy & Labor",
    "Crime & Justice",
    "Social Issues & Culture",
    "Environment, Climate & Energy",
    "Technology, Science & Digital Society",
    "Other"  # For articles that don't fit clearly into other categories
]


class DataPreprocessor:
    """Handles data loading, merging, and initial preprocessing."""
    
    def __init__(self, test_mode: bool = True, test_size: int = 1000):
        self.test_mode = test_mode
        self.test_size = test_size
        logger.info(f"Initializing preprocessor (test_mode={test_mode}, test_size={test_size})")
        
    def load_actor_data(self) -> pl.DataFrame:
        """Load actor dataset from Excel."""
        logger.info(f"Loading actor data from {ACTOR_PATH}")
        # Use pandas to read Excel, then convert to polars
        df_actors = pd.read_excel(ACTOR_PATH)
        df_actors = pl.from_pandas(df_actors)
        
        logger.info(f"Actor data loaded: {df_actors.shape[0]} rows, {df_actors.shape[1]} columns")
        logger.info(f"Actor columns: {df_actors.columns}")
        
        # Keep only necessary columns for merge
        actor_cols = ['Actor_domain', 'Actor', 'Country', 'Partisan', 'Partisan_fullcategories']
        available_cols = [col for col in actor_cols if col in df_actors.columns]
        df_actors = df_actors.select(available_cols)
        
        return df_actors
    
    def extract_domain_from_url(self, url: str) -> Optional[str]:
        """Extract domain from URL if domain column is NULL."""
        if not url or pd.isna(url):
            return None
        try:
            from urllib.parse import urlparse
            parsed = urlparse(str(url))
            domain = parsed.netloc
            if domain:
                return self.normalize_domain(domain)
        except:
            pass
        return None
    
    def load_article_data(self) -> pl.DataFrame:
        """Load article dataset (full or test sample)."""
        logger.info(f"Loading article data from {ARTICLE_PATH}")
        
        if self.test_mode:
            logger.info(f"TEST MODE: Loading first {self.test_size} rows")
            df_articles = pl.read_csv(
                ARTICLE_PATH,
                n_rows=self.test_size,
                infer_schema_length=10000
            )
        else:
            logger.info("FULL MODE: Loading all articles (this may take a while...)")
            df_articles = pl.read_csv(
                ARTICLE_PATH,
                infer_schema_length=10000
            )
        
        logger.info(f"Article data loaded: {df_articles.shape[0]} rows, {df_articles.shape[1]} columns")
        logger.info(f"Article columns: {df_articles.columns}")
        
        # Fix NULL domains by extracting from URL
        null_domain_count = df_articles.filter(pl.col('domain').is_null()).shape[0]
        if null_domain_count > 0:
            logger.info(f"Found {null_domain_count:,} articles with NULL domain. Attempting to extract from URL...")
            df_articles = df_articles.with_columns([
                pl.when(pl.col('domain').is_null())
                .then(pl.col('url').map_elements(
                    lambda x: self.extract_domain_from_url(x),
                    return_dtype=pl.Utf8
                ))
                .otherwise(pl.col('domain'))
                .alias('domain')
            ])
            fixed_count = df_articles.filter(pl.col('domain').is_not_null()).shape[0] - (df_articles.shape[0] - null_domain_count)
            logger.info(f"Fixed {fixed_count:,} NULL domains by extracting from URL")
        
        # Remove nordfront.dk articles (as requested)
        before_filter = len(df_articles)
        df_articles = df_articles.filter(
            ~pl.col('domain').str.to_lowercase().str.contains('nordfront.dk', literal=True)
        )
        after_filter = len(df_articles)
        removed_count = before_filter - after_filter
        if removed_count > 0:
            logger.info(f"Removed {removed_count:,} articles from nordfront.dk domain")
        
        return df_articles
    
    def normalize_domain(self, domain: str) -> str:
        """Normalize domain by removing www. prefix and converting to lowercase."""
        if not domain or pd.isna(domain):
            return None
        domain_str = str(domain).lower().strip()
        # Remove www. prefix if present
        if domain_str.startswith('www.'):
            domain_str = domain_str[4:]
        
        # Handle known domain variations/mappings
        domain_mappings = {
            'vastaansanomat.com': 'verkkosanomat.com',  # Vastaan Sanomat = Verkkosanomat
        }
        if domain_str in domain_mappings:
            domain_str = domain_mappings[domain_str]
        
        return domain_str
    
    def merge_partisan_data(self, df_articles: pl.DataFrame, df_actors: pl.DataFrame) -> pl.DataFrame:
        """Merge partisan values from actor dataset to article dataset."""
        logger.info("Merging partisan data from actor dataset...")
        
        # Normalize domains for matching
        df_articles_norm = df_articles.with_columns([
            pl.col('domain').map_elements(
                lambda x: self.normalize_domain(x),
                return_dtype=pl.Utf8
            ).alias('domain_normalized')
        ])
        
        df_actors_norm = df_actors.with_columns([
            pl.col('Actor_domain').map_elements(
                lambda x: self.normalize_domain(x),
                return_dtype=pl.Utf8
            ).alias('domain_normalized')
        ])
        
        # Show unique domains before merge for verification
        n_unique_article_domains = df_articles_norm.select('domain_normalized').filter(
            pl.col('domain_normalized').is_not_null()
        ).n_unique()
        n_unique_actor_domains = df_actors_norm.select('domain_normalized').filter(
            pl.col('domain_normalized').is_not_null()
        ).n_unique()
        logger.info(f"Unique normalized domains in articles: {n_unique_article_domains}")
        logger.info(f"Unique normalized domains in actors: {n_unique_actor_domains}")
        
        # Perform left join on normalized domains
        df_merged = df_articles_norm.join(
            df_actors_norm,
            left_on='domain_normalized',
            right_on='domain_normalized',
            how='left'
        )
        
        # Drop the normalization column (keep original domain)
        df_merged = df_merged.drop('domain_normalized')
        
        # Check merge success
        n_matched = df_merged.filter(pl.col('Partisan').is_not_null()).shape[0]
        n_unmatched = df_merged.filter(pl.col('Partisan').is_null()).shape[0]
        match_rate = (n_matched / df_merged.shape[0]) * 100
        logger.info(f"Merge complete: {n_matched}/{df_merged.shape[0]} articles matched ({match_rate:.1f}%)")
        logger.info(f"Unmatched articles: {n_unmatched:,} ({100-match_rate:.1f}%)")
        
        # Show unmatched domains for debugging
        if n_unmatched > 0:
            unmatched_domains = df_merged.filter(pl.col('Partisan').is_null()).select('domain').unique().head(10)
            logger.info(f"Sample unmatched domains:")
            for domain in unmatched_domains.to_series().to_list():
                count = df_merged.filter(pl.col('domain') == domain).shape[0]
                logger.info(f"  - {domain}: {count} articles")
        
        if match_rate < 80:
            logger.warning(f"Match rate is {match_rate:.1f}%. Some articles may be missing partisan classification.")
            logger.warning("Consider adding missing domains to actor dataset or handling null domains.")
        
        return df_merged
    
    def extract_external_links(self, content: str) -> List[str]:
        """Extract external URLs from article content."""
        if not content or pd.isna(content):
            return []
        
        # Regex pattern for URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, str(content))
        
        # Clean and deduplicate
        urls = list(set([url.rstrip('.,;:)') for url in urls]))
        return urls
    
    def add_basic_features(self, df: pl.DataFrame) -> pl.DataFrame:
        """Add basic features that don't require NLP models."""
        logger.info("Adding basic features (external links, word count, etc.)...")
        
        # Extract external links
        df = df.with_columns([
            pl.col('content').map_elements(
                lambda x: json.dumps(self.extract_external_links(x)),
                return_dtype=pl.Utf8
            ).alias('external_links')
        ])
        
        # Add word count if not present
        if 'word_count' not in df.columns:
            df = df.with_columns([
                pl.col('content').str.split(' ').list.len().alias('word_count')
            ])
        
        # Add processing timestamp
        df = df.with_columns([
            pl.lit(datetime.now().isoformat()).alias('preprocessed_at')
        ])
        
        return df
    
    def save_checkpoint(self, df: pl.DataFrame, stage: str):
        """Save intermediate checkpoint."""
        output_path = OUTPUT_DIR / f"checkpoint_{stage}.parquet"
        df.write_parquet(output_path)
        logger.info(f"Checkpoint saved: {output_path}")
    
    def run_basic_preprocessing(self) -> pl.DataFrame:
        """Run all basic preprocessing steps (no NLP yet)."""
        logger.info("=" * 80)
        logger.info("Starting basic preprocessing pipeline")
        logger.info("=" * 80)
        
        # Step 1: Load data
        df_articles = self.load_article_data()
        df_actors = self.load_actor_data()
        
        # Step 2: Merge partisan data
        df_merged = self.merge_partisan_data(df_articles, df_actors)
        self.save_checkpoint(df_merged, "01_merged")
        
        # Step 3: Add basic features
        df_enriched = self.add_basic_features(df_merged)
        self.save_checkpoint(df_enriched, "02_basic_features")
        
        logger.info("=" * 80)
        logger.info("Basic preprocessing complete!")
        logger.info(f"Final shape: {df_enriched.shape}")
        logger.info(f"Columns: {df_enriched.columns}")
        logger.info("=" * 80)
        
        return df_enriched


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='NAMO Data Preprocessing Pipeline')
    parser.add_argument('--test', action='store_true', help='Run in test mode with small sample')
    parser.add_argument('--test-size', type=int, default=1000, help='Test sample size')
    parser.add_argument('--full', action='store_true', help='Run on full dataset')
    
    args = parser.parse_args()
    
    # Determine mode
    test_mode = args.test or not args.full
    
    # Initialize and run
    preprocessor = DataPreprocessor(test_mode=test_mode, test_size=args.test_size)
    df_result = preprocessor.run_basic_preprocessing()
    
    # Save final result
    output_filename = "NAMO_preprocessed_test.parquet" if test_mode else "NAMO_preprocessed_full.parquet"
    output_path = OUTPUT_DIR / output_filename
    df_result.write_parquet(output_path)
    logger.info(f"Final output saved: {output_path}")
    
    # Show sample
    print("\n" + "=" * 80)
    print("Sample of preprocessed data:")
    print("=" * 80)
    print(df_result.head(3))
    
    return df_result


if __name__ == "__main__":
    main()

