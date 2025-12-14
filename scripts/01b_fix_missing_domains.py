"""
Fix Missing Domains in Actor Dataset
=====================================
This script identifies articles with domains not in the actor dataset
and provides options to handle them.
"""

import polars as pl
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
ARTICLE_PATH = DATA_DIR / "NAMO_2025_09.csv"
ACTOR_PATH = DATA_DIR / "NAMO_actor_251118.xlsx"


def normalize_domain(domain):
    """Normalize domain."""
    if not domain or pd.isna(domain):
        return None
    domain_str = str(domain).lower().strip()
    if domain_str.startswith('www.'):
        domain_str = domain_str[4:]
    # Handle known mappings
    domain_mappings = {
        'vastaansanomat.com': 'verkkosanomat.com',
    }
    if domain_str in domain_mappings:
        domain_str = domain_mappings[domain_str]
    return domain_str


def find_missing_domains():
    """Find domains in articles that are not in actor dataset."""
    logger.info("Loading data...")
    
    # Load articles
    df_articles = pl.read_csv(ARTICLE_PATH)
    logger.info(f"Loaded {len(df_articles):,} articles")
    
    # Load actors
    df_actors_pd = pd.read_excel(ACTOR_PATH)
    df_actors = pl.from_pandas(df_actors_pd)
    logger.info(f"Loaded {len(df_actors)} actors")
    
    # Normalize domains
    df_articles_norm = df_articles.with_columns([
        pl.col('domain').map_elements(lambda x: normalize_domain(x), return_dtype=pl.Utf8).alias('domain_normalized')
    ])
    
    df_actors_norm = df_actors.with_columns([
        pl.col('Actor_domain').map_elements(lambda x: normalize_domain(x), return_dtype=pl.Utf8).alias('domain_normalized')
    ])
    
    # Get unique domains
    article_domains = set(df_articles_norm.select('domain_normalized').filter(
        pl.col('domain_normalized').is_not_null()
    ).unique().to_series().to_list())
    
    actor_domains = set(df_actors_norm.select('domain_normalized').filter(
        pl.col('domain_normalized').is_not_null()
    ).unique().to_series().to_list())
    
    # Find missing
    missing_domains = article_domains - actor_domains
    
    logger.info(f"\n{'='*80}")
    logger.info("MISSING DOMAINS ANALYSIS")
    logger.info(f"{'='*80}")
    logger.info(f"Total article domains: {len(article_domains)}")
    logger.info(f"Total actor domains: {len(actor_domains)}")
    logger.info(f"Missing domains: {len(missing_domains)}")
    
    if missing_domains:
        logger.info("\nMissing domains and article counts:")
        for domain in sorted(missing_domains):
            count = df_articles_norm.filter(
                pl.col('domain_normalized') == domain
            ).shape[0]
            # Get country distribution
            countries = df_articles_norm.filter(
                pl.col('domain_normalized') == domain
            ).select('country').unique().to_series().to_list()
            
            logger.info(f"\n  Domain: {domain}")
            logger.info(f"    Articles: {count:,}")
            logger.info(f"    Countries: {', '.join([str(c) for c in countries if c])}")
            
            # Show sample URLs
            sample_urls = df_articles_norm.filter(
                pl.col('domain_normalized') == domain
            ).select('url').head(3).to_series().to_list()
            logger.info(f"    Sample URLs:")
            for url in sample_urls:
                logger.info(f"      - {url[:80]}...")
    
    # Check null domains
    null_count = df_articles.filter(pl.col('domain').is_null()).shape[0]
    logger.info(f"\n{'='*80}")
    logger.info(f"Articles with NULL domain: {null_count:,} ({null_count/len(df_articles)*100:.1f}%)")
    
    return missing_domains, df_articles_norm, df_actors_norm


def suggest_fixes(missing_domains, df_articles_norm):
    """Suggest fixes for missing domains."""
    logger.info(f"\n{'='*80}")
    logger.info("SUGGESTED FIXES")
    logger.info(f"{'='*80}")
    
    # Check if we can infer country/partisan from articles
    for domain in sorted(missing_domains):
        domain_articles = df_articles_norm.filter(
            pl.col('domain_normalized') == domain
        )
        
        countries = domain_articles.select('country').unique().to_series().to_list()
        country = countries[0] if len(countries) == 1 else None
        
        logger.info(f"\nDomain: {domain}")
        logger.info(f"  Suggested action: Add to actor dataset")
        logger.info(f"  Inferred country: {country}")
        logger.info(f"  Article count: {len(domain_articles):,}")
        logger.info(f"  Note: Partisan classification needs manual review")


if __name__ == "__main__":
    missing, df_articles_norm, df_actors_norm = find_missing_domains()
    suggest_fixes(missing, df_articles_norm)
    
    logger.info(f"\n{'='*80}")
    logger.info("RECOMMENDATION")
    logger.info(f"{'='*80}")
    logger.info("1. Add missing domains to actor dataset Excel file")
    logger.info("2. Or: Update preprocessing script to handle missing domains")
    logger.info("   (e.g., assign 'Unknown' partisan or infer from country)")

