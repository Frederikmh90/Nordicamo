#!/usr/bin/env python3
"""
Test Topic Modeling Script Locally
===================================
Quick test of topic modeling with small sample before running on GPU server.
"""

import polars as pl
from pathlib import Path
import sys

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

# Import the module directly
import importlib.util
spec = importlib.util.spec_from_file_location("topic_modeling", str(Path(__file__).parent / "15_topic_modeling_turftopic.py"))
topic_modeling = importlib.util.module_from_spec(spec)
spec.loader.exec_module(topic_modeling)

BASE_DIR = Path(__file__).parent.parent


def test_topic_modeling():
    """Test topic modeling with small sample."""
    print("="*60)
    print("Testing Topic Modeling Script")
    print("="*60)
    
    # Load test data
    input_file = BASE_DIR / "data/nlp_enriched/nlp_enriched_NAMO_preprocessed_test_final.parquet"
    
    if not input_file.exists():
        print(f"❌ Input file not found: {input_file}")
        return False
    
    print(f"✅ Input file found: {input_file}")
    df = pl.read_parquet(input_file)
    print(f"✅ Loaded {len(df):,} articles")
    
    # Test with very small sample
    test_country = "denmark"
    df_test = df.filter(pl.col("country") == test_country).head(50)
    
    if len(df_test) < 10:
        print(f"⚠️  Not enough articles for {test_country}, trying all countries...")
        df_test = df.head(50)
    
    print(f"\nTesting with {len(df_test)} articles...")
    
    # Extract texts
    texts = df_test.select(pl.col("content").cast(pl.Utf8)).to_series().to_list()
    texts = [str(t) if t and len(str(t)) > 50 else "" for t in texts]
    texts = [t for t in texts if t]
    
    print(f"✅ {len(texts)} valid texts")
    
    if len(texts) < 5:
        print("❌ Not enough valid texts for testing")
        return False
    
    # Test model initialization (will download model if needed)
    print("\n" + "="*60)
    print("Testing Model Initialization")
    print("="*60)
    
    try:
        print("Initializing MultilingualTopicModeler...")
        print("(This will download mmBERT if not already cached)")
        
        modeler = 15_topic_modeling_turftopic.MultilingualTopicModeler(
            n_topics=5,  # Small number for testing
            language="da",  # Danish
        )
        
        print("✅ Model initialized successfully")
        
        # Test encoding (small batch)
        print("\nTesting text encoding...")
        test_texts = texts[:5]
        embeddings = modeler.embedding_model.encode(test_texts, batch_size=2)
        print(f"✅ Encoded {len(test_texts)} texts")
        print(f"   Embedding shape: {embeddings.shape}")
        
        # Test full fit_transform (this will take longer)
        print("\n" + "="*60)
        print("Testing Full Topic Modeling (this may take a few minutes)")
        print("="*60)
        print("Fitting topic model...")
        
        topics, probabilities = modeler.fit_transform(texts)
        
        print(f"✅ Topic modeling completed!")
        print(f"   Found {len(set(topics))} topics")
        print(f"   Topics: {set(topics)}")
        
        # Get topic info
        topic_info = modeler.get_topic_info()
        print(f"\n✅ Topic info:")
        print(topic_info.head(10).to_string())
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_topic_modeling()
    
    if success:
        print("\n" + "="*60)
        print("✅ All Tests Passed!")
        print("="*60)
        print("\nReady to run on GPU server:")
        print("  python scripts/17_run_topic_modeling_remote.py \\")
        print("    --input data/nlp_enriched/nlp_enriched_NAMO_preprocessed_test_final.parquet \\")
        print("    --output data/topic_modeled/topics.parquet")
    else:
        print("\n" + "="*60)
        print("❌ Tests Failed")
        print("="*60)
        sys.exit(1)

