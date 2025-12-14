#!/usr/bin/env python3
"""
Merge Phase 1 (10% complete) with Phase 2 (ongoing) for interim dataset
"""

import polars as pl
from pathlib import Path
from datetime import datetime

print("="*80)
print("MERGING INTERIM DATASET FOR NORDIC MEDIA OBSERVATORY")
print("="*80)

# Load files
print("\n📂 Loading files...")
df1 = pl.read_parquet("data/interim/NAMO_10pct_enriched.parquet")
df2 = pl.read_parquet("data/interim/NAMO_950k_enriched.parquet")

print(f"  Phase 1 (10% complete): {len(df1):,} articles")
print(f"  Phase 2 (ongoing):      {len(df2):,} articles")

# Check for duplicates
print("\n🔍 Checking for duplicates...")
urls1 = set(df1['url'].to_list())
urls2 = set(df2['url'].to_list())
overlap = urls1.intersection(urls2)
print(f"  Overlapping URLs: {len(overlap):,}")

# Remove duplicates from df2 (keep df1 as authoritative for Phase 1)
if overlap:
    print(f"  Removing {len(overlap):,} duplicates from Phase 2...")
    df2 = df2.filter(~pl.col('url').is_in(list(overlap)))
    print(f"  Phase 2 after dedup: {len(df2):,} articles")

# Merge
print("\n🔗 Merging datasets...")
merged = pl.concat([df1, df2])
print(f"  Total articles: {len(merged):,}")

# Check which articles have NLP processing
print("\n✅ NLP Processing Status:")
nlp_processed = merged.filter(pl.col('nlp_processed_at').is_not_null())
print(f"  Articles with NLP: {len(nlp_processed):,} / {len(merged):,} ({100*len(nlp_processed)/len(merged):.1f}%)")

# Summary statistics
print("\n📊 Summary Statistics:")

# Sentiment distribution
print("\n  Sentiment Distribution:")
sent_dist = nlp_processed.group_by('sentiment').len().sort('len', descending=True)
for row in sent_dist.rows():
    print(f"    {row[0]}: {row[1]:,} ({100*row[1]/len(nlp_processed):.1f}%)")

# Category distribution
print("\n  Top 15 Categories:")
from collections import Counter
all_cats = []
for cats in nlp_processed['categories']:
    if cats:
        all_cats.extend(cats)
cat_counts = Counter(all_cats).most_common(15)
for cat, count in cat_counts:
    print(f"    {cat}: {count:,}")

# Temporal distribution
print("\n  Date Range:")
dates = merged.filter(pl.col('published_date').is_not_null())['published_date']
if len(dates) > 0:
    print(f"    Earliest: {dates.min()}")
    print(f"    Latest:   {dates.max()}")

# Domain distribution
print("\n  Top 15 Domains:")
domain_dist = merged.group_by('domain').len().sort('len', descending=True).head(15)
for row in domain_dist.rows():
    print(f"    {row[0]}: {row[1]:,}")

# Save merged dataset
output_file = "data/NAMO_interim_enriched.parquet"
print(f"\n💾 Saving merged dataset...")
merged.write_parquet(output_file)
print(f"  Output: {output_file}")
print(f"  Size: {Path(output_file).stat().st_size / 1024 / 1024:.1f} MB")

# Also save a sample CSV for quick inspection
sample_file = "data/NAMO_interim_sample.csv"
print(f"\n📄 Saving sample CSV (first 1000 rows)...")
merged.head(1000).write_csv(sample_file)
print(f"  Output: {sample_file}")

print("\n" + "="*80)
print("✅ MERGE COMPLETE!")
print("="*80)
print(f"\nInterim dataset ready for Nordic Media Observatory presentation!")
print(f"Total: {len(merged):,} articles ({len(nlp_processed):,} with NLP)")
print(f"File: {output_file}")
print("="*80)

