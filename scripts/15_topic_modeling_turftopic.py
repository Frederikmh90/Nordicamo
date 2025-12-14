"""
NAMO Topic Modeling with TurfTopic (Multilingual)
==================================================
Topic modeling for Nordic languages using TurfTopic or compatible multilingual approach.

Supports: Danish, Swedish, Norwegian, Finnish
"""

import polars as pl
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from tqdm import tqdm
import logging
from datetime import datetime
import json
import pickle

# Setup logging first
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Try to import TurfTopic, fallback to BERTopic with multilingual embeddings
try:
    import turftopic
    TURFTOPIC_AVAILABLE = True
    logger.info("TurfTopic found - using TurfTopic")
except ImportError:
    TURFTOPIC_AVAILABLE = False
    logger.info("TurfTopic not found - using BERTopic with multilingual embeddings")
    from bertopic import BERTopic
    from sentence_transformers import SentenceTransformer
    from sklearn.feature_extraction.text import CountVectorizer
    try:
        import nltk
        from nltk.corpus import stopwords
    except ImportError:
        logger.warning("NLTK not available - stopwords will be limited")
        stopwords = None

import torch

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "nlp_enriched"
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR = BASE_DIR / "data" / "topic_modeled"
OUTPUT_DIR.mkdir(exist_ok=True)

# Nordic language codes
NORDIC_LANGUAGES = {
    "denmark": "da",  # Danish
    "sweden": "sv",   # Swedish
    "norway": "no",   # Norwegian
    "finland": "fi"   # Finnish
}

# Multilingual embedding models (ordered by preference)
# mmBERT: Trained on 3T tokens from 1800+ languages, excellent for Nordic languages
MULTILINGUAL_MODELS = [
    "jhu-clsp/mmBERT-base",  # mmBERT-base: SoTA multilingual encoder, 1800+ languages
    "jhu-clsp/mmBERT-small",  # mmBERT-small: Smaller variant if memory constrained
    "BAAI/bge-m3",  # Fallback: Good multilingual model, supports 100+ languages
    "intfloat/multilingual-e5-base",  # Alternative fallback
]


class MultilingualTopicModeler:
    """Topic modeling for Nordic languages using TurfTopic or BERTopic."""
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        n_topics: Optional[int] = None,  # Auto-detect if None
        language: Optional[str] = None,  # "da", "sv", "no", "fi", or None for multilingual
        use_turftopic: bool = True,
    ):
        self.model_name = model_name
        self.n_topics = n_topics
        self.language = language
        self.use_turftopic = use_turftopic and TURFTOPIC_AVAILABLE
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        self.model = None
        self.embedding_model = None
        self.stopwords = {}
        
        logger.info(f"Initializing MultilingualTopicModeler")
        logger.info(f"Device: {self.device}")
        logger.info(f"Use TurfTopic: {self.use_turftopic}")
        logger.info(f"Preferred model: mmBERT-base (1800+ languages, SoTA performance)")
        
        self._load_stopwords()
        self._load_model()
    
    def _load_stopwords(self):
        """Load stopwords for Nordic languages."""
        if stopwords is None:
            logger.warning("NLTK stopwords not available")
            self.stopwords = {}
            return
        
        try:
            import nltk
            nltk.download("stopwords", quiet=True)
            
            for lang_code in ["danish", "swedish", "norwegian", "finnish"]:
                try:
                    self.stopwords[lang_code] = set(stopwords.words(lang_code))
                except Exception as e:
                    logger.warning(f"Could not load {lang_code} stopwords: {e}")
                    self.stopwords[lang_code] = set()
        except Exception as e:
            logger.warning(f"Could not load stopwords: {e}")
            self.stopwords = {}
    
    def _load_model(self):
        """Load topic modeling model."""
        if self.use_turftopic:
            self._load_turftopic_model()
        else:
            self._load_bertopic_model()
    
    def _load_turftopic_model(self):
        """Load TurfTopic model."""
        try:
            # TurfTopic API - adjust based on actual TurfTopic documentation
            # This is a placeholder - update based on actual TurfTopic API
            if self.model_name:
                self.model = turftopic.TurfTopic(
                    embedding_model=self.model_name,
                    n_topics=self.n_topics,
                    language=self.language,
                )
            else:
                # Use default multilingual model
                self.model = turftopic.TurfTopic(
                    n_topics=self.n_topics,
                    language=self.language,
                )
            logger.info("TurfTopic model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load TurfTopic: {e}")
            logger.info("Falling back to BERTopic")
            self.use_turftopic = False
            self._load_bertopic_model()
    
    def _load_bertopic_model(self):
        """Load BERTopic with multilingual embeddings."""
        # Select embedding model
        if self.model_name:
            embedding_model_name = self.model_name
        else:
            # Try models in order of preference
            embedding_model_name = None
            for model in MULTILINGUAL_MODELS:
                try:
                    embedding_model_name = model
                    logger.info(f"Trying embedding model: {model}")
                    break
                except:
                    continue
            
            if not embedding_model_name:
                raise ValueError("No suitable multilingual embedding model found")
        
        logger.info(f"Loading embedding model: {embedding_model_name}")
        logger.info(f"Device: {self.device}")
        
        # mmBERT models need special handling - they're BERT models, not SentenceTransformer models
        # Check if it's mmBERT
        if "mmbert" in embedding_model_name.lower():
            logger.info("Detected mmBERT model - using AutoModel and AutoTokenizer")
            from transformers import AutoModel, AutoTokenizer
            import torch.nn as nn
            
            # Load mmBERT tokenizer and model
            self.mmbert_tokenizer = AutoTokenizer.from_pretrained(embedding_model_name)
            
            # Check if accelerate is available for device_map
            try:
                import accelerate
                use_device_map = "auto" if self.device == "cuda" else None
            except ImportError:
                logger.warning("accelerate not installed - using manual device placement")
                use_device_map = None
            
            self.mmbert_model = AutoModel.from_pretrained(
                embedding_model_name,
                dtype=torch.float16 if self.device == "cuda" else torch.float32,  # Use dtype instead of torch_dtype
                device_map=use_device_map,
            )
            
            # Manual device placement if device_map not used
            if use_device_map is None and self.device == "cuda":
                self.mmbert_model = self.mmbert_model.to(self.device)
            self.mmbert_model.eval()
            
            # Create a wrapper to make it compatible with SentenceTransformer API
            class mmBERTWrapper:
                def __init__(self, tokenizer, model, device):
                    self.tokenizer = tokenizer
                    self.model = model
                    self.device = device
                
                def encode(self, texts, batch_size=32, show_progress_bar=True, convert_to_numpy=True):
                    """Encode texts using mmBERT."""
                    import torch
                    from tqdm import tqdm
                    
                    embeddings = []
                    for i in tqdm(range(0, len(texts), batch_size), disable=not show_progress_bar):
                        batch_texts = texts[i:i+batch_size]
                        inputs = self.tokenizer(
                            batch_texts,
                            padding=True,
                            truncation=True,
                            max_length=512,
                            return_tensors="pt"
                        ).to(self.device)
                        
                        with torch.no_grad():
                            outputs = self.model(**inputs)
                            # Use [CLS] token embedding (first token)
                            batch_embeddings = outputs.last_hidden_state[:, 0, :]
                            if convert_to_numpy:
                                batch_embeddings = batch_embeddings.cpu().numpy()
                            embeddings.append(batch_embeddings)
                    
                    import numpy as np
                    return np.vstack(embeddings)
            
            self.embedding_model = mmBERTWrapper(
                self.mmbert_tokenizer,
                self.mmbert_model,
                self.device
            )
            logger.info("mmBERT model loaded successfully")
        else:
            # Standard SentenceTransformer model
            # Check if accelerate is available for device_map
            try:
                import accelerate
                use_device_map = "auto" if self.device == "cuda" else None
            except ImportError:
                logger.warning("accelerate not installed - using manual device placement")
                use_device_map = None
            
            self.embedding_model = SentenceTransformer(
                embedding_model_name,
                device=self.device,
                model_kwargs={
                    "dtype": torch.float16 if self.device == "cuda" else torch.float32,  # Use dtype instead of torch_dtype
                    "device_map": use_device_map,
                }
            )
            logger.info(f"SentenceTransformer model loaded: {embedding_model_name}")
        
        # Create vectorizer with multilingual stopwords
        all_stopwords = set()
        for lang_stopwords in self.stopwords.values():
            all_stopwords.update(lang_stopwords)
        
        # Additional common words
        additional_stopwords = {
            "og", "eller", "men", "och", "eller", "men", "ja", "nei", "ja", "ei",
            "the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with"
        }
        all_stopwords.update(additional_stopwords)
        
        # Adjust vectorizer parameters based on document count
        # For small document sets, use more lenient parameters
        # min_df and max_df need to be compatible: max_df * n_docs >= min_df
        vectorizer = CountVectorizer(
            stop_words=list(all_stopwords),
            min_df=1,  # Reduced from 2 to handle small topics
            max_df=0.99,  # Increased from 0.95 to be more lenient
            ngram_range=(1, 2),  # Unigrams and bigrams
        )
        
        # Initialize BERTopic
        self.model = BERTopic(
            embedding_model=self.embedding_model,
            vectorizer_model=vectorizer,
            verbose=True,
            calculate_probabilities=True,
            top_n_words=10,
        )
        
        logger.info("BERTopic model initialized successfully")
    
    def fit_transform(
        self,
        texts: List[str],
        countries: Optional[List[str]] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Fit topic model and transform texts.
        
        Returns:
            topics: Array of topic assignments
            probabilities: Array of topic probabilities
        """
        logger.info(f"Fitting topic model on {len(texts)} documents")
        
        # Check if we have enough documents
        if len(texts) < 5:
            logger.warning(f"⚠️  Only {len(texts)} documents - too few for topic modeling")
            logger.warning("   Assigning all documents to topic -1 (noise)")
            topics = np.array([-1] * len(texts))
            probabilities = np.array([[1.0]] * len(texts))
            return topics, probabilities
        
        # Fit and transform with error handling
        try:
            if self.use_turftopic:
                topics, probabilities = self.model.fit_transform(texts)
            else:
                topics, probabilities = self.model.fit_transform(texts)
        except ValueError as e:
            if "max_df corresponds to < documents than min_df" in str(e):
                logger.warning(f"⚠️  Vectorizer error with {len(texts)} documents: {e}")
                logger.warning("   Using more lenient vectorizer parameters...")
                
                # Recreate vectorizer with very lenient parameters
                all_stopwords = set()
                for lang_stopwords in self.stopwords.values():
                    all_stopwords.update(lang_stopwords)
                additional_stopwords = {
                    "og", "eller", "men", "och", "ja", "nei", "ei",
                    "the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with"
                }
                all_stopwords.update(additional_stopwords)
                
                # Very lenient parameters for small document sets
                lenient_vectorizer = CountVectorizer(
                    stop_words=list(all_stopwords),
                    min_df=1,
                    max_df=1.0,  # Allow all words
                    ngram_range=(1, 1),  # Only unigrams for small sets
                )
                
                # Recreate BERTopic with lenient vectorizer
                from bertopic import BERTopic
                self.model = BERTopic(
                    embedding_model=self.embedding_model,
                    vectorizer_model=lenient_vectorizer,
                    verbose=True,
                    calculate_probabilities=True,
                    top_n_words=10,
                )
                
                # Try again
                topics, probabilities = self.model.fit_transform(texts)
            else:
                raise
        
        logger.info(f"Found {len(set(topics))} topics")
        
        return topics, probabilities
    
    def get_topic_info(self) -> pd.DataFrame:
        """Get topic information."""
        if self.use_turftopic:
            # TurfTopic API - adjust based on actual API
            return self.model.get_topic_info()
        else:
            return self.model.get_topic_info()
    
    def get_topics(self) -> Dict[int, List[Tuple[str, float]]]:
        """Get top words for each topic."""
        if self.use_turftopic:
            return self.model.get_topics()
        else:
            return self.model.get_topics()
    
    def save_model(self, path: Path):
        """Save model to disk."""
        logger.info(f"Saving model to {path}")
        if self.use_turftopic:
            # TurfTopic save method
            self.model.save(str(path))
        else:
            self.model.save(str(path))
        
        # Also save metadata
        metadata = {
            "model_name": self.model_name,
            "n_topics": self.n_topics,
            "language": self.language,
            "use_turftopic": self.use_turftopic,
            "timestamp": datetime.now().isoformat(),
        }
        with open(path.parent / f"{path.name}_metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
    
    @classmethod
    def load_model(cls, path: Path):
        """Load model from disk."""
        logger.info(f"Loading model from {path}")
        
        # Load metadata
        metadata_path = path.parent / f"{path.name}_metadata.json"
        if metadata_path.exists():
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
        else:
            metadata = {}
        
        instance = cls(
            model_name=metadata.get("model_name"),
            n_topics=metadata.get("n_topics"),
            language=metadata.get("language"),
            use_turftopic=metadata.get("use_turftopic", False),
        )
        
        if instance.use_turftopic:
            instance.model = turftopic.TurfTopic.load(str(path))
        else:
            instance.model = BERTopic.load(str(path))
        
        return instance


def process_articles_by_country(
    df: pl.DataFrame,
    country: str,
    min_articles: int = 100,
    sample_size: Optional[int] = None,
) -> Dict:
    """Process articles for a specific country."""
    logger.info(f"Processing articles for {country}")
    
    # Filter by country
    df_country = df.filter(pl.col("country") == country)
    
    if len(df_country) < min_articles:
        logger.warning(f"Only {len(df_country)} articles for {country}, skipping")
        return None
    
    # Sample if needed
    if sample_size and len(df_country) > sample_size:
        logger.info(f"Sampling {sample_size} articles from {len(df_country)}")
        df_country = df_country.sample(sample_size, seed=42)
    
    # Extract texts
    texts = df_country.select(pl.col("content").cast(pl.Utf8)).to_series().to_list()
    texts = [str(t) if t else "" for t in texts]
    
    # Filter out empty texts
    valid_indices = [i for i, t in enumerate(texts) if t and len(t.strip()) > 50]
    texts = [texts[i] for i in valid_indices]
    df_country = df_country[valid_indices]
    
    if len(texts) < min_articles:
        logger.warning(f"Only {len(texts)} valid articles after filtering")
        return None
    
    # Get language code
    lang_code = NORDIC_LANGUAGES.get(country.lower())
    
    # Initialize model
    modeler = MultilingualTopicModeler(
        language=lang_code,
        n_topics=None,  # Auto-detect
    )
    
    # Fit model
    topics, probabilities = modeler.fit_transform(texts)
    
    # Get topic info
    topic_info = modeler.get_topic_info()
    topic_words = modeler.get_topics()
    
    # Add topic assignments to dataframe
    df_result = df_country.with_columns([
        pl.Series("topic_id", topics),
        pl.Series("topic_probability", probabilities.max(axis=1) if len(probabilities.shape) > 1 else probabilities),
    ])
    
    return {
        "country": country,
        "model": modeler,
        "topics": topics,
        "probabilities": probabilities,
        "topic_info": topic_info,
        "topic_words": topic_words,
        "dataframe": df_result,
    }


def main():
    """Main execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Topic modeling for NAMO articles")
    parser.add_argument(
        "--input",
        type=str,
        default="data/nlp_enriched/nlp_enriched_NAMO_preprocessed_test_final.parquet",
        help="Input parquet file",
    )
    parser.add_argument(
        "--countries",
        nargs="+",
        default=["denmark", "sweden", "norway", "finland"],
        help="Countries to process",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=None,
        help="Sample size per country (for testing)",
    )
    parser.add_argument(
        "--min-articles",
        type=int,
        default=100,
        help="Minimum articles required per country",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/topic_modeled/topics.parquet",
        help="Output file",
    )
    parser.add_argument(
        "--unified",
        action="store_true",
        help="Run one unified topic model on entire corpus instead of per-country",
    )
    
    args = parser.parse_args()
    
    # Load data
    input_path = BASE_DIR / args.input
    logger.info(f"Loading data from {input_path}")
    df = pl.read_parquet(input_path)
    logger.info(f"Loaded {len(df):,} articles")
    
    # Initialize results containers
    all_dfs = []
    results = {}
    
    if args.unified:
        # Run one unified model on entire corpus
        logger.info("="*60)
        logger.info("Running UNIFIED topic model on entire corpus")
        logger.info("="*60)
        
        # Sample if needed
        if args.sample_size and len(df) > args.sample_size:
            logger.info(f"Sampling {args.sample_size} articles from {len(df)}")
            df = df.sample(args.sample_size, seed=42)
        
        # Extract texts
        texts = df.select(pl.col("content").cast(pl.Utf8)).to_series().to_list()
        texts = [str(t) if t else "" for t in texts]
        
        # Filter out empty texts
        valid_indices = [i for i, t in enumerate(texts) if t and len(t.strip()) > 50]
        texts = [texts[i] for i in valid_indices]
        df_filtered = df[valid_indices]
        
        if len(texts) < 10:
            logger.error(f"Only {len(texts)} valid articles - need at least 10")
            return
        
        logger.info(f"Processing {len(texts)} articles with unified model")
        
        # Initialize unified multilingual model
        modeler = MultilingualTopicModeler(
            language="multilingual",  # Use multilingual mode
            n_topics=None,  # Auto-detect
        )
        
        # Fit model
        topics, probabilities = modeler.fit_transform(texts)
        
        # Get topic info
        topic_info = modeler.get_topic_info()
        topic_words = modeler.get_topics()
        
        # Add topic assignments to dataframe
        df_result = df_filtered.with_columns([
            pl.Series("topic_id", topics),
            pl.Series("topic_probability", probabilities.max(axis=1) if len(probabilities.shape) > 1 else probabilities),
        ])
        
        # Save model
        model_path = MODELS_DIR / "topic_model_unified"
        modeler.save_model(model_path)
        logger.info(f"Saved unified model to {model_path}")
        
        # Save topic info
        topic_info_path = OUTPUT_DIR / "topic_info_unified.csv"
        topic_info.to_csv(topic_info_path, index=False)
        logger.info(f"Saved topic info to {topic_info_path}")
        
        # Save results
        output_path = BASE_DIR / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_result.write_parquet(output_path)
        logger.info(f"Saved results to {output_path}")
        
        logger.info("="*60)
        logger.info(f"✅ Unified topic modeling complete!")
        logger.info(f"   Found {len(set(topics))} topics across {len(texts)} articles")
        logger.info("="*60)
        
        # Save unified results
        all_dfs = [df_result]
        
    else:
        # Process each country separately (original approach)
        logger.info("Processing articles by country (per-country models)")
        
        for country in args.countries:
            result = process_articles_by_country(
                df,
                country,
                min_articles=args.min_articles,
                sample_size=args.sample_size,
            )
            
            if result:
                results[country] = result
                all_dfs.append(result["dataframe"])
                
                # Save model
                model_path = MODELS_DIR / f"topic_model_{country}"
                result["model"].save_model(model_path)
                
                # Save topic info
                topic_info_path = OUTPUT_DIR / f"topic_info_{country}.csv"
                result["topic_info"].to_csv(topic_info_path, index=False)
                logger.info(f"Saved topic info to {topic_info_path}")
    
    # Combine and save results (if not already saved in unified mode)
    if all_dfs:
        if not args.unified:
            # Per-country mode: combine all country results
            df_combined = pl.concat(all_dfs)
            output_path = BASE_DIR / args.output
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df_combined.write_parquet(output_path)
            logger.info(f"Saved {len(df_combined):,} articles with topics to {output_path}")
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("Topic Modeling Summary")
        logger.info("="*60)
        
        if args.unified:
            # Unified mode summary
            if len(all_dfs) > 0:
                df_result = all_dfs[0]
                n_topics = len(set(df_result["topic_id"].to_list()))
                logger.info(f"Unified Model: {n_topics} topics")
                logger.info(f"  Articles: {len(df_result):,}")
        else:
            # Per-country mode summary
            for country, result in results.items():
                n_topics = len(result["topic_info"])
                logger.info(f"{country.capitalize()}: {n_topics} topics")
                logger.info(f"  Articles: {len(result['dataframe']):,}")
        
        logger.info("="*60)
    else:
        logger.warning("No results to save")


if __name__ == "__main__":
    main()

