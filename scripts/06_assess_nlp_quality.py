"""
NLP Quality Assessment Script
=============================
Assesses the quality of NLP enrichment results by analyzing:
- Sentiment distribution and consistency
- Category assignment quality
- Named Entity Recognition accuracy
- JSON parsing success rate
- Sample manual review
"""

import polars as pl
import json
from pathlib import Path
from collections import Counter
import logging
from typing import Dict, List
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "nlp_enriched"


def assess_nlp_quality(parquet_path: Path) -> Dict:
    """Assess quality of NLP enrichment."""
    logger.info(f"Loading enriched data from {parquet_path}")
    df = pl.read_parquet(parquet_path)
    
    total_articles = len(df)
    logger.info(f"Total articles: {total_articles:,}")
    
    results = {
        "total_articles": total_articles,
        "sentiment_analysis": {},
        "category_analysis": {},
        "ner_analysis": {},
        "parsing_quality": {},
        "sample_reviews": []
    }
    
    # 1. Sentiment Analysis Quality
    logger.info("\n" + "="*80)
    logger.info("SENTIMENT ANALYSIS QUALITY")
    logger.info("="*80)
    
    sentiment_dist = df.group_by("sentiment").len().sort("len", descending=True)
    logger.info("\nSentiment Distribution:")
    for row in sentiment_dist.iter_rows(named=True):
        pct = (row['len'] / total_articles) * 100
        logger.info(f"  {row['sentiment']:10s}: {row['len']:5d} ({pct:5.1f}%)")
        results["sentiment_analysis"][row['sentiment']] = {
            "count": row['len'],
            "percentage": pct
        }
    
    # Check for null sentiments
    null_sentiment = df.filter(pl.col("sentiment").is_null()).shape[0]
    if null_sentiment > 0:
        logger.warning(f"  ⚠️  {null_sentiment} articles with NULL sentiment")
    
    # Check sentiment score consistency
    sentiment_score_check = df.filter(
        (pl.col("sentiment") == "positive") & (pl.col("sentiment_score") != 1.0)
    ).shape[0]
    if sentiment_score_check > 0:
        logger.warning(f"  ⚠️  {sentiment_score_check} positive articles with incorrect sentiment_score")
    
    results["sentiment_analysis"]["null_count"] = null_sentiment
    results["sentiment_analysis"]["coverage"] = ((total_articles - null_sentiment) / total_articles) * 100
    
    # 2. Category Analysis Quality
    logger.info("\n" + "="*80)
    logger.info("CATEGORY ANALYSIS QUALITY")
    logger.info("="*80)
    
    # Count articles with categories
    articles_with_categories = df.filter(
        (pl.col("categories").is_not_null()) & 
        (pl.col("categories") != "[]") &
        (pl.col("categories") != "")
    ).shape[0]
    
    logger.info(f"\nArticles with categories: {articles_with_categories:,} ({articles_with_categories/total_articles*100:.1f}%)")
    results["category_analysis"]["articles_with_categories"] = articles_with_categories
    results["category_analysis"]["coverage"] = (articles_with_categories / total_articles) * 100
    
    # Parse categories and count frequency
    all_categories = []
    valid_category_count = 0
    
    for row in df.iter_rows(named=True):
        categories_str = row.get('categories', '[]')
        if categories_str and categories_str != '[]':
            try:
                categories = json.loads(categories_str) if isinstance(categories_str, str) else categories_str
                if isinstance(categories, list) and len(categories) > 0:
                    all_categories.extend(categories)
                    valid_category_count += 1
            except:
                pass
    
    category_freq = Counter(all_categories)
    logger.info(f"\nCategory Frequency (Top 10):")
    for cat, count in category_freq.most_common(10):
        pct = (count / valid_category_count) * 100 if valid_category_count > 0 else 0
        logger.info(f"  {cat:40s}: {count:4d} ({pct:5.1f}%)")
        results["category_analysis"]["top_categories"] = [
            {"category": cat, "count": count, "percentage": pct}
            for cat, count in category_freq.most_common(10)
        ]
    
    # Average categories per article
    avg_categories = len(all_categories) / valid_category_count if valid_category_count > 0 else 0
    logger.info(f"\nAverage categories per article: {avg_categories:.2f}")
    results["category_analysis"]["avg_categories_per_article"] = avg_categories
    
    # 3. Named Entity Recognition Quality
    logger.info("\n" + "="*80)
    logger.info("NAMED ENTITY RECOGNITION QUALITY")
    logger.info("="*80)
    
    articles_with_entities = 0
    total_persons = 0
    total_locations = 0
    total_organizations = 0
    
    for row in df.iter_rows(named=True):
        entities_str = row.get('entities_json', '{}')
        if entities_str and entities_str != '{}':
            try:
                entities = json.loads(entities_str) if isinstance(entities_str, str) else entities_str
                if isinstance(entities, dict):
                    persons = entities.get('persons', [])
                    locations = entities.get('locations', [])
                    organizations = entities.get('organizations', [])
                    
                    if persons or locations or organizations:
                        articles_with_entities += 1
                        total_persons += len(persons)
                        total_locations += len(locations)
                        total_organizations += len(organizations)
            except:
                pass
    
    logger.info(f"\nArticles with entities: {articles_with_entities:,} ({articles_with_entities/total_articles*100:.1f}%)")
    logger.info(f"Total persons extracted: {total_persons:,}")
    logger.info(f"Total locations extracted: {total_locations:,}")
    logger.info(f"Total organizations extracted: {total_organizations:,}")
    
    results["ner_analysis"] = {
        "articles_with_entities": articles_with_entities,
        "coverage": (articles_with_entities / total_articles) * 100,
        "total_persons": total_persons,
        "total_locations": total_locations,
        "total_organizations": total_organizations,
        "avg_entities_per_article": (total_persons + total_locations + total_organizations) / articles_with_entities if articles_with_entities > 0 else 0
    }
    
    # 4. Parsing Quality (estimate based on empty categories vs non-empty)
    logger.info("\n" + "="*80)
    logger.info("JSON PARSING QUALITY")
    logger.info("="*80)
    
    # Articles with empty categories likely had parsing issues
    empty_categories = df.filter(
        (pl.col("categories").is_null()) | 
        (pl.col("categories") == "[]") |
        (pl.col("categories") == "")
    ).shape[0]
    
    # Estimate: articles with categories likely parsed successfully
    successful_parses = articles_with_categories
    parse_errors = empty_categories
    parse_success_rate = (successful_parses / total_articles) * 100
    
    logger.info(f"\nArticles with successful category parsing: {successful_parses:,} ({parse_success_rate:.1f}%)")
    logger.info(f"Articles without categories (likely parse issues): {parse_errors:,} ({100-parse_success_rate:.1f}%)")
    logger.info("\nNote: Sentiment extraction works even with parse errors due to fallback extraction")
    
    results["parsing_quality"] = {
        "successful_parses": successful_parses,
        "parse_errors": parse_errors,
        "success_rate": parse_success_rate,
        "note": "Sentiment extraction works even with parse errors due to fallback extraction"
    }
    
    # 5. Sample Reviews
    logger.info("\n" + "="*80)
    logger.info("SAMPLE ARTICLE REVIEWS")
    logger.info("="*80)
    
    # Sample articles with different characteristics
    samples = []
    
    # Sample 1: Article with categories
    with_categories = df.filter(
        (pl.col("categories").is_not_null()) & 
        (pl.col("categories") != "[]")
    )
    if len(with_categories) > 0:
        sample = with_categories.sample(1).iter_rows(named=True).__next__()
        samples.append({
            "type": "With Categories",
            "title": sample.get('title', '')[:80],
            "sentiment": sample.get('sentiment'),
            "categories": json.loads(sample.get('categories', '[]')) if isinstance(sample.get('categories'), str) else sample.get('categories', []),
            "reasoning": sample.get('reasoning', '')[:100]
        })
    
    # Sample 2: Negative sentiment article
    negative = df.filter(pl.col("sentiment") == "negative")
    if len(negative) > 0:
        sample = negative.sample(1).iter_rows(named=True).__next__()
        samples.append({
            "type": "Negative Sentiment",
            "title": sample.get('title', '')[:80],
            "sentiment": sample.get('sentiment'),
            "categories": json.loads(sample.get('categories', '[]')) if isinstance(sample.get('categories'), str) else sample.get('categories', []),
            "reasoning": sample.get('reasoning', '')[:100]
        })
    
    # Sample 3: Article with entities
    with_entities = df.filter(
        (pl.col("entities_json").is_not_null()) & 
        (pl.col("entities_json") != "{}")
    )
    if len(with_entities) > 0:
        sample = with_entities.sample(1).iter_rows(named=True).__next__()
        entities = json.loads(sample.get('entities_json', '{}')) if isinstance(sample.get('entities_json'), str) else sample.get('entities_json', {})
        samples.append({
            "type": "With Entities",
            "title": sample.get('title', '')[:80],
            "sentiment": sample.get('sentiment'),
            "entities": {
                "persons": len(entities.get('persons', [])),
                "locations": len(entities.get('locations', [])),
                "organizations": len(entities.get('organizations', []))
            }
        })
    
    # Sample 4: Article without categories (likely parse error)
    no_categories = df.filter(
        (pl.col("categories").is_null()) | 
        (pl.col("categories") == "[]") |
        (pl.col("categories") == "")
    )
    if len(no_categories) > 0:
        sample = no_categories.sample(1).iter_rows(named=True).__next__()
        samples.append({
            "type": "No Categories (Possible Parse Issue)",
            "title": sample.get('title', '')[:80],
            "sentiment": sample.get('sentiment'),
            "categories": "[]",
            "note": "Sentiment still extracted via fallback"
        })
    
    for i, sample in enumerate(samples, 1):
        logger.info(f"\nSample {i}: {sample['type']}")
        logger.info(f"  Title: {sample['title']}")
        logger.info(f"  Sentiment: {sample['sentiment']}")
        if 'categories' in sample:
            logger.info(f"  Categories: {sample['categories']}")
        if 'entities' in sample:
            logger.info(f"  Entities: {sample['entities']}")
        if 'reasoning' in sample:
            logger.info(f"  Reasoning: {sample['reasoning']}")
        if 'note' in sample:
            logger.info(f"  Note: {sample['note']}")
    
    results["sample_reviews"] = samples
    
    # Overall Quality Score
    logger.info("\n" + "="*80)
    logger.info("OVERALL QUALITY ASSESSMENT")
    logger.info("="*80)
    
    quality_score = (
        results["sentiment_analysis"]["coverage"] * 0.3 +
        results["category_analysis"]["coverage"] * 0.3 +
        results["ner_analysis"]["coverage"] * 0.2 +
        results["parsing_quality"]["success_rate"] * 0.2
    )
    
    logger.info(f"\nOverall Quality Score: {quality_score:.1f}/100")
    logger.info("\nBreakdown:")
    logger.info(f"  Sentiment Coverage: {results['sentiment_analysis']['coverage']:.1f}% (weight: 30%)")
    logger.info(f"  Category Coverage: {results['category_analysis']['coverage']:.1f}% (weight: 30%)")
    logger.info(f"  NER Coverage: {results['ner_analysis']['coverage']:.1f}% (weight: 20%)")
    logger.info(f"  JSON Parsing Success: {results['parsing_quality']['success_rate']:.1f}% (weight: 20%)")
    
    results["overall_quality_score"] = quality_score
    
    return results


def main():
    """Main execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Assess NLP enrichment quality')
    parser.add_argument('--input', type=str, required=True, help='Path to enriched parquet file')
    parser.add_argument('--output', type=str, help='Path to save quality report JSON')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return
    
    results = assess_nlp_quality(input_path)
    
    # Save results if output path provided
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"\nQuality report saved to: {output_path}")
    
    return results


if __name__ == "__main__":
    main()

