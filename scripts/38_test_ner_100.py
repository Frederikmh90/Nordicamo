#!/usr/bin/env python3
"""
Test NER processing on 100 articles.
Creates a sample and runs NER with detailed logging.
"""

import polars as pl
from pathlib import Path
import subprocess
import sys

BASE_DIR = Path(__file__).parent.parent

def create_sample(input_file: str, output_file: str, n: int = 100):
    """Create a sample of n articles."""
    print(f"Creating sample of {n} articles...")
    
    input_path = BASE_DIR / input_file if not Path(input_file).is_absolute() else Path(input_file)
    output_path = BASE_DIR / output_file
    
    if not input_path.exists():
        print(f"❌ Input file not found: {input_path}")
        return False
    
    df = pl.read_parquet(input_path)
    print(f"✅ Loaded {len(df)} articles")
    
    # Sample n articles
    df_sample = df.head(n)
    print(f"✅ Sampled {len(df_sample)} articles")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_sample.write_parquet(output_path)
    print(f"✅ Saved sample to {output_path}")
    
    return True

def main():
    """Main execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test NER on 100 articles")
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/NAMO_preprocessed_test.parquet",
        help="Input parquet file",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=100,
        help="Number of articles to sample",
    )
    parser.add_argument(
        "--skip-sample",
        action="store_true",
        help="Skip creating sample (use existing)",
    )
    
    args = parser.parse_args()
    
    sample_file = f"data/processed/test_ner_{args.sample_size}.parquet"
    output_file = f"data/nlp_enriched/test_ner_{args.sample_size}_results.parquet"
    
    print("=" * 60)
    print("NER Test - 100 Articles")
    print("=" * 60)
    
    # Step 1: Create sample
    if not args.skip_sample:
        if not create_sample(args.input, sample_file, args.sample_size):
            return
    else:
        print(f"⏭️  Skipping sample creation, using existing: {sample_file}")
    
    # Step 2: Run NER
    print("\n" + "=" * 60)
    print("Running NER processing...")
    print("=" * 60)
    
    script_path = BASE_DIR / "scripts" / "34_ner_country_specific.py"
    
    cmd = [
        sys.executable,
        str(script_path),
        "--input", sample_file,
        "--output", output_file,
        "--device", "cuda",
        "--score-threshold", "0.5",
    ]
    
    print(f"Command: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(BASE_DIR),
            check=False,
            capture_output=False,  # Show output in real-time
        )
        
        if result.returncode == 0:
            print("\n" + "=" * 60)
            print("✅ NER processing complete!")
            print("=" * 60)
            print(f"\nResults saved to: {output_file}")
            print(f"Check logs in: logs/ directory")
        else:
            print(f"\n❌ NER processing failed (exit code: {result.returncode})")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error running NER: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())




