"""
Data Verification Script
=========================
Quick script to verify data files exist and can be read.
Shows basic statistics about the datasets.
"""

import polars as pl
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

print("=" * 80)
print("NAMO Data Verification")
print("=" * 80)

# Check article dataset
article_path = DATA_DIR / "NAMO_2025_09.csv"
print(f"\n1. Article Dataset: {article_path}")
print(f"   Exists: {article_path.exists()}")
print(f"   Size: {article_path.stat().st_size / (1024**3):.2f} GB")

if article_path.exists():
    # Read first few rows to check structure
    print("\n   Reading first 100 rows to check structure...")
    df_sample = pl.read_csv(article_path, n_rows=100)
    print(f"   Columns: {df_sample.columns}")
    print(f"   Sample shape: {df_sample.shape}")
    print(f"\n   First row preview:")
    for col in df_sample.columns:
        value = df_sample[col][0]
        value_str = str(value)[:100] if value else "None"
        print(f"     {col}: {value_str}")
    
    # Try to count total rows (may be slow)
    print("\n   Estimating total rows...")
    try:
        # Quick row count
        df_full = pl.scan_csv(article_path)
        total_rows = df_full.select(pl.len()).collect()[0, 0]
        print(f"   Total articles: {total_rows:,}")
    except Exception as e:
        print(f"   Could not count rows: {e}")

# Check actor dataset
actor_path = DATA_DIR / "NAMO_actor_251118.xlsx"
print(f"\n2. Actor Dataset: {actor_path}")
print(f"   Exists: {actor_path.exists()}")

if actor_path.exists():
    print(f"   Size: {actor_path.stat().st_size / (1024**2):.2f} MB")
    print("\n   Reading Excel file...")
    df_actors = pd.read_excel(actor_path)
    df_actors_pl = pl.from_pandas(df_actors)
    print(f"   Shape: {df_actors_pl.shape}")
    print(f"   Columns: {df_actors_pl.columns}")
    
    # Check key columns
    if 'Actor_domain' in df_actors_pl.columns:
        print(f"\n   Unique Actor_domain values: {df_actors_pl['Actor_domain'].n_unique()}")
    if 'Partisan' in df_actors_pl.columns:
        print(f"   Partisan values:")
        partisan_counts = df_actors_pl['Partisan'].value_counts().sort('count', descending=True)
        print(partisan_counts)
    if 'Country' in df_actors_pl.columns:
        print(f"\n   Country distribution:")
        country_counts = df_actors_pl['Country'].value_counts().sort('count', descending=True)
        print(country_counts)

print("\n" + "=" * 80)
print("Verification Complete!")
print("=" * 80)
print("\nNext step: Run test preprocessing")
print("  python scripts/01_data_preprocessing.py --test --test-size 100")

