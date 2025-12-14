#!/usr/bin/env python3
"""
Analyze "Other" Category Assignments and Top Topics
====================================================
Analyzes NLP enriched data to:
1. Understand why articles were assigned "Other" category
2. Show top 10 topics from topic modeling
Provides insights for improving category classification.
"""

import polars as pl
from pathlib import Path
import sys
import json
from collections import Counter

BASE_DIR = Path(__file__).parent.parent


def analyze_other_category(input_file: str):
    """Analyze articles assigned to 'Other' category."""
    print("="*60)
    print("Analyzing 'Other' Category Assignments")
    print("="*60)
    
    input_path = BASE_DIR / input_file
    
    if not input_path.exists():
        print(f"❌ Input file not found: {input_path}")
        return
    
    print(f"✅ Loading data from: {input_path}")
    df = pl.read_parquet(input_path)
    print(f"✅ Loaded {len(df):,} articles")
    
    # Check if categories column exists
    if "categories" not in df.columns:
        print("❌ 'categories' column not found in data")
        print(f"   Available columns: {df.columns}")
        return
    
    # Parse categories (they're stored as JSON strings)
    def parse_categories(cat_str):
        """Parse categories from JSON string."""
        if cat_str is None:
            return []
        if isinstance(cat_str, list):
            return cat_str
        if isinstance(cat_str, str):
            try:
                return json.loads(cat_str)
            except:
                return []
        return []
    
    # Add parsed categories column
    df = df.with_columns([
        pl.col("categories").map_elements(parse_categories, return_dtype=pl.Object).alias("categories_parsed")
    ])
    
    # Count total articles
    total = len(df)
    
    # Count articles with "Other" category
    df_other = df.filter(
        pl.col("categories_parsed").map_elements(
            lambda x: isinstance(x, list) and "Other" in x,
            return_dtype=pl.Boolean
        )
    )
    
    other_count = len(df_other)
    other_percentage = (other_count / total * 100) if total > 0 else 0
    
    print(f"\n{'='*60}")
    print("Summary Statistics")
    print(f"{'='*60}")
    print(f"Total articles: {total:,}")
    print(f"Articles with 'Other': {other_count:,} ({other_percentage:.2f}%)")
    print(f"Articles without 'Other': {total - other_count:,} ({100 - other_percentage:.2f}%)")
    
    if other_count == 0:
        print("\n✅ No articles assigned to 'Other' category!")
        return
    
    # Analyze "Other" articles
    print(f"\n{'='*60}")
    print("Analysis of 'Other' Category Articles")
    print(f"{'='*60}")
    
    # Sample some "Other" articles for inspection
    sample_size = min(20, other_count)
    df_sample = df_other.sample(n=sample_size, seed=42)
    
    print(f"\n📋 Sample of {sample_size} articles assigned to 'Other':")
    print("-"*60)
    
    for i, row in enumerate(df_sample.iter_rows(named=True), 1):
        title = row.get("title", "No title")[:80]
        content_preview = row.get("content", "")[:150]
        categories = row.get("categories_parsed", [])
        if not categories:
            # Fallback to original if parsed is empty
            cat_str = row.get("categories", "")
            categories = parse_categories(cat_str)
        reasoning = row.get("reasoning", "No reasoning")
        
        print(f"\n{i}. Title: {title}")
        print(f"   Categories: {categories}")
        print(f"   Content preview: {content_preview}...")
        if reasoning:
            print(f"   LLM Reasoning: {reasoning[:200]}")
        print("-"*60)
    
    # Analyze by country
    if "country" in df_other.columns:
        print(f"\n{'='*60}")
        print("'Other' Category by Country")
        print(f"{'='*60}")
        country_counts = df_other.group_by("country").agg([
            pl.count().alias("other_count")
        ]).sort("other_count", descending=True)
        print(country_counts)
    
    # Analyze by domain
    if "domain" in df_other.columns:
        print(f"\n{'='*60}")
        print("Top Domains with 'Other' Category")
        print(f"{'='*60}")
        domain_counts = df_other.group_by("domain").agg([
            pl.count().alias("other_count")
        ]).sort("other_count", descending=True).head(10)
        print(domain_counts)
    
    # Check if articles have content
    print(f"\n{'='*60}")
    print("Content Analysis")
    print(f"{'='*60}")
    
    if "content" in df_other.columns:
        empty_content = df_other.filter(
            (pl.col("content").is_null()) | 
            (pl.col("content").str.len_chars() < 50)
        )
        print(f"Articles with empty/short content: {len(empty_content):,}")
        
        avg_length = df_other.select(
            pl.col("content").str.len_chars().mean().alias("avg_length")
        ).item()
        print(f"Average content length: {avg_length:.0f} characters")
    
    # Recommendations
    print(f"\n{'='*60}")
    print("Recommendations")
    print(f"{'='*60}")
    
    if other_percentage > 5:
        print("⚠️  WARNING: More than 5% of articles assigned to 'Other'")
        print("   This suggests the prompt may need refinement.")
        print("   Consider:")
        print("   1. Reviewing sample articles above")
        print("   2. Expanding category definitions")
        print("   3. Adding more examples to the prompt")
        print("   4. Checking if articles truly don't fit any category")
    elif other_percentage > 1:
        print("⚠️  More than 1% assigned to 'Other' - review recommended")
    else:
        print("✅ 'Other' category usage is within acceptable range (<1%)")
    
    # Analyze topic distribution (if topic_id exists)
    if "topic_id" in df.columns:
        print(f"\n{'='*60}")
        print("Top 10 Topics Distribution")
        print(f"{'='*60}")
        
        # Filter out noise topic (-1)
        df_with_topics = df.filter(pl.col("topic_id") >= 0)
        
        if len(df_with_topics) > 0:
            topic_counts = df_with_topics.group_by("topic_id").agg([
                pl.count().alias("article_count")
            ]).sort("article_count", descending=True)
            
            total_with_topics = len(df_with_topics)
            
            print(f"Articles with topics: {total_with_topics:,} ({total_with_topics/total*100:.1f}%)")
            print(f"Articles without topics (noise): {total - total_with_topics:,} ({(total - total_with_topics)/total*100:.1f}%)")
            print(f"\nTop 10 Topics:")
            print("-"*60)
            print(f"{'Topic ID':<12} {'Articles':<12} {'Percentage':<12}")
            print("-"*60)
            
            top_10 = topic_counts.head(10)
            for row in top_10.iter_rows(named=True):
                topic_id = row["topic_id"]
                count = row["article_count"]
                pct = (count / total_with_topics * 100) if total_with_topics > 0 else 0
                print(f"{topic_id:<12} {count:<12,} {pct:<12.2f}%")
            
            # Show topic probabilities if available
            if "topic_probability" in df.columns:
                avg_probs = df_with_topics.group_by("topic_id").agg([
                    pl.col("topic_probability").mean().alias("avg_probability")
                ]).sort("avg_probability", descending=True).head(10)
                
                print(f"\nTop 10 Topics by Average Probability:")
                print("-"*60)
                print(f"{'Topic ID':<12} {'Avg Probability':<18}")
                print("-"*60)
                for row in avg_probs.iter_rows(named=True):
                    topic_id = row["topic_id"]
                    prob = row["avg_probability"]
                    print(f"{topic_id:<12} {prob:<18.4f}")
        else:
            print("⚠️  No articles with topics found (all are noise topic -1)")
    else:
        print(f"\n{'='*60}")
        print("Topic Analysis")
        print(f"{'='*60}")
        print("⚠️  'topic_id' column not found - topic modeling may not have been run yet")
    
    # Save sample to file for manual review
    output_file = BASE_DIR / "data" / "nlp_enriched" / "other_category_sample.parquet"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df_sample.write_parquet(output_file)
    print(f"\n💾 Sample saved to: {output_file}")
    print(f"   Review this file to understand why articles were assigned 'Other'")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Analyze 'Other' category assignments in NLP enriched data"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/nlp_enriched/nlp_enriched_NAMO_preprocessed_test_final.parquet",
        help="Input parquet file with NLP enriched data"
    )
    
    args = parser.parse_args()
    
    try:
        analyze_other_category(args.input)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

