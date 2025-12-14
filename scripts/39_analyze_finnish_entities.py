#!/usr/bin/env python3
"""
Analyze Finnish entities from NER results.
Shows top entities by type (persons, locations, organizations).
"""

import polars as pl
import json
from pathlib import Path
from collections import Counter
import sys

BASE_DIR = Path(__file__).parent.parent

def analyze_finnish_entities(parquet_file: str, top_n: int = 10):
    """Analyze Finnish entities and show top N."""
    parquet_path = BASE_DIR / parquet_file if not Path(parquet_file).is_absolute() else Path(parquet_file)
    
    if not parquet_path.exists():
        print(f"❌ File not found: {parquet_path}")
        return
    
    print("=" * 60)
    print("Finnish Entity Analysis")
    print("=" * 60)
    print(f"Loading: {parquet_path}")
    
    df = pl.read_parquet(parquet_path)
    print(f"✅ Loaded {len(df)} articles")
    
    # Filter Finnish articles
    if 'country' in df.columns:
        df_finnish = df.filter(pl.col("country").str.to_lowercase() == "finland")
    else:
        print("⚠️  No 'country' column found. Analyzing all articles.")
        df_finnish = df
    
    print(f"🇫🇮 Finnish articles: {len(df_finnish)}")
    
    if len(df_finnish) == 0:
        print("❌ No Finnish articles found!")
        return
    
    # Extract entities
    persons = []
    locations = []
    organizations = []
    
    articles_with_entities = 0
    
    for row in df_finnish.iter_rows(named=True):
        entities_json = row.get("entities_json", "{}")
        
        if not entities_json:
            continue
        
        try:
            if isinstance(entities_json, str):
                entities = json.loads(entities_json)
            else:
                entities = entities_json
            
            # Count entities
            persons_list = entities.get("persons", [])
            locations_list = entities.get("locations", [])
            orgs_list = entities.get("organizations", [])
            
            if persons_list or locations_list or orgs_list:
                articles_with_entities += 1
            
            # Collect entity names
            for p in persons_list:
                if isinstance(p, dict):
                    persons.append(p.get("name", ""))
                else:
                    persons.append(str(p))
            
            for l in locations_list:
                if isinstance(l, dict):
                    locations.append(l.get("name", ""))
                else:
                    locations.append(str(l))
            
            for o in orgs_list:
                if isinstance(o, dict):
                    organizations.append(o.get("name", ""))
                else:
                    organizations.append(str(o))
                    
        except Exception as e:
            print(f"⚠️  Error parsing entities: {e}")
            continue
    
    print(f"\n📊 Articles with entities: {articles_with_entities} / {len(df_finnish)}")
    print(f"Total entities found: {len(persons) + len(locations) + len(organizations)}")
    
    # Count and show top entities
    print("\n" + "=" * 60)
    print(f"TOP {top_n} PERSONS")
    print("=" * 60)
    person_counts = Counter(persons)
    for i, (name, count) in enumerate(person_counts.most_common(top_n), 1):
        print(f"{i:2d}. {name:40s} ({count} mentions)")
    
    print("\n" + "=" * 60)
    print(f"TOP {top_n} LOCATIONS")
    print("=" * 60)
    location_counts = Counter(locations)
    for i, (name, count) in enumerate(location_counts.most_common(top_n), 1):
        print(f"{i:2d}. {name:40s} ({count} mentions)")
    
    print("\n" + "=" * 60)
    print(f"TOP {top_n} ORGANIZATIONS")
    print("=" * 60)
    org_counts = Counter(organizations)
    for i, (name, count) in enumerate(org_counts.most_common(top_n), 1):
        print(f"{i:2d}. {name:40s} ({count} mentions)")
    
    # Summary statistics
    print("\n" + "=" * 60)
    print("SUMMARY STATISTICS")
    print("=" * 60)
    print(f"Total persons:      {len(persons):4d} (unique: {len(person_counts):3d})")
    print(f"Total locations:    {len(locations):4d} (unique: {len(location_counts):3d})")
    print(f"Total organizations: {len(organizations):4d} (unique: {len(org_counts):3d})")
    print(f"Articles with entities: {articles_with_entities}/{len(df_finnish)} ({100*articles_with_entities/len(df_finnish):.1f}%)")


def main():
    """Main execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze Finnish entities from NER results")
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to parquet file with NER results",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of top entities to show (default: 10)",
    )
    
    args = parser.parse_args()
    analyze_finnish_entities(args.input, args.top)


if __name__ == "__main__":
    main()




