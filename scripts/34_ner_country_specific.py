#!/usr/bin/env python3
"""
NAMO Country-Specific NER Processing
====================================
Uses country-specific transformer models for Named Entity Recognition.

Based on reference implementation that worked well for Danish.
Uses separate models for each Nordic country for better accuracy.
"""

import polars as pl
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from tqdm import tqdm
import logging
from datetime import datetime
import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
import re
import traceback

# Setup logging with file output
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"ner_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Configure logging to both file and console
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"Logging to: {LOG_FILE}")

# Paths
BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "data" / "nlp_enriched"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Country-specific NER models
# Based on reference: saattrupdan/nbailab-base-ner-scandi works well for Scandinavian languages
NER_MODELS_BY_COUNTRY = {
    "denmark": "Maltehb/danish-bert-botxo-ner-dane",  # Danish-specific (proven in reference)
    "sweden": "saattrupdan/nbailab-base-ner-scandi",  # Scandinavian (covers Swedish)
    "norway": "saattrupdan/nbailab-base-ner-scandi",  # Scandinavian (covers Norwegian)
    # Finnish: Use multilingual NER model (xlm-roberta-large-finetuned-conll03-english)
    # This multilingual model works well for Finnish when Finnish-specific models are not available
    "finland": "xlm-roberta-large-finetuned-conll03-english",  # Multilingual NER (works for Finnish)
}

# Fallback model if country-specific model fails
FALLBACK_MODEL = "saattrupdan/nbailab-base-ner-scandi"  # Scandinavian (covers DK/SE/NO)

# Finnish-specific fallback (if primary Finnish model fails)
FINNISH_FALLBACK_MODEL = "xlm-roberta-large-finetuned-conll03-english"  # Multilingual NER model

# Entity label mappings (standardize across models)
ENTITY_LABEL_MAPPING = {
    # Person entities
    "PER": "PER",
    "PERSON": "PER",
    "B-PER": "PER",
    "I-PER": "PER",
    # Location entities
    "LOC": "LOC",
    "LOCATION": "LOC",
    "GPE": "LOC",  # Geopolitical entity
    "B-LOC": "LOC",
    "I-LOC": "LOC",
    # Organization entities
    "ORG": "ORG",
    "ORGANIZATION": "ORG",
    "B-ORG": "ORG",
    "I-ORG": "ORG",
    # Miscellaneous
    "MISC": "MISC",
    "MISCELLANEOUS": "MISC",
    "B-MISC": "MISC",
    "I-MISC": "MISC",
}


class CountrySpecificNER:
    """NER processor using country-specific transformer models."""

    def __init__(
        self,
        device: str = "cuda",
        batch_size: int = 32,
        score_threshold: float = 0.5,
        hf_token: Optional[str] = None,
    ):
        self.device = device if torch.cuda.is_available() else "cpu"
        self.batch_size = batch_size
        self.score_threshold = score_threshold
        self.hf_token = hf_token or os.getenv("HF_TOKEN")
        self.models = {}  # Cache loaded models per country
        self.pipelines = {}  # Cache pipelines per country

        logger.info(f"Initializing Country-Specific NER on device: {self.device}")
        logger.info(f"Score threshold: {score_threshold}")

    def _get_model_for_country(self, country: str) -> str:
        """Get the appropriate model for a country."""
        country_lower = country.lower() if country else ""
        return NER_MODELS_BY_COUNTRY.get(country_lower, FALLBACK_MODEL)

    def _load_model(self, country: str):
        """Load NER model for a specific country (with caching)."""
        if country in self.pipelines:
            logger.debug(f"Using cached model for {country}")
            return self.pipelines[country]

        model_name = self._get_model_for_country(country)
        logger.info(f"🔄 Loading NER model for {country}: {model_name}")
        logger.debug(f"Device: {self.device}, CUDA available: {torch.cuda.is_available()}")

        try:
            # Prepare tokenizer kwargs
            tokenizer_kwargs = {}
            if self.hf_token:
                tokenizer_kwargs["token"] = self.hf_token
                logger.debug("Using Hugging Face token for authentication")

            # Load tokenizer
            logger.debug(f"Step 1/3: Loading tokenizer for {model_name}...")
            tokenizer = AutoTokenizer.from_pretrained(model_name, **tokenizer_kwargs)
            logger.debug(f"✅ Tokenizer loaded: {type(tokenizer).__name__}")

            # Load model
            logger.debug(f"Step 2/3: Loading model for {model_name}...")
            logger.debug(f"GPU memory before: {torch.cuda.memory_allocated() / 1024**3:.2f} GB" if torch.cuda.is_available() else "CPU mode")
            model = AutoModelForTokenClassification.from_pretrained(
                model_name,
                **tokenizer_kwargs
            )
            logger.debug(f"✅ Model loaded: {type(model).__name__}")
            logger.debug(f"GPU memory after: {torch.cuda.memory_allocated() / 1024**3:.2f} GB" if torch.cuda.is_available() else "CPU mode")

            # Create pipeline
            logger.debug(f"Step 3/3: Creating NER pipeline...")
            device_id = 0 if self.device == "cuda" and torch.cuda.is_available() else -1
            logger.debug(f"Pipeline device ID: {device_id}")
            
            nlp_pipeline = pipeline(
                task="ner",
                model=model,
                tokenizer=tokenizer,
                aggregation_strategy="first",  # Same as reference
                device=device_id,
            )

            # Cache pipeline
            self.pipelines[country] = nlp_pipeline
            self.models[country] = model_name

            logger.info(f"✅ Loaded NER model for {country} ({model_name})")
            return nlp_pipeline

        except Exception as e:
            logger.error(f"❌ Failed to load model for {country}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Try Finnish-specific fallback first
            if country.lower() == "finland" and model_name != FINNISH_FALLBACK_MODEL:
                logger.info(f"Trying Finnish fallback model: {FINNISH_FALLBACK_MODEL}")
                try:
                    return self._load_finnish_fallback_model()
                except Exception as e2:
                    logger.error(f"Finnish fallback also failed: {e2}")
            # Try general fallback
            if model_name != FALLBACK_MODEL:
                logger.info(f"Trying general fallback model: {FALLBACK_MODEL}")
                return self._load_fallback_model()
            raise

    def _load_fallback_model(self):
        """Load fallback Scandinavian model."""
        if "fallback" in self.pipelines:
            return self.pipelines["fallback"]

        logger.info(f"Loading fallback model: {FALLBACK_MODEL}")
        try:
            tokenizer_kwargs = {}
            if self.hf_token:
                tokenizer_kwargs["token"] = self.hf_token

            tokenizer = AutoTokenizer.from_pretrained(FALLBACK_MODEL, **tokenizer_kwargs)
            model = AutoModelForTokenClassification.from_pretrained(
                FALLBACK_MODEL, **tokenizer_kwargs
            )

            nlp_pipeline = pipeline(
                task="ner",
                model=model,
                tokenizer=tokenizer,
                aggregation_strategy="first",
                device=0 if self.device == "cuda" else -1,
            )

            self.pipelines["fallback"] = nlp_pipeline
            logger.info("✅ Loaded fallback model")
            return nlp_pipeline

        except Exception as e:
            logger.error(f"❌ Failed to load fallback model: {e}")
            raise

    def _load_finnish_fallback_model(self):
        """Load Finnish-specific fallback model (multilingual)."""
        if "finnish_fallback" in self.pipelines:
            return self.pipelines["finnish_fallback"]

        logger.info(f"Loading Finnish fallback model: {FINNISH_FALLBACK_MODEL}")
        logger.warning("⚠️  Note: Finnish NER models are limited. Using multilingual model.")
        try:
            tokenizer_kwargs = {}
            if self.hf_token:
                tokenizer_kwargs["token"] = self.hf_token

            # Try to load as NER model first
            try:
                tokenizer = AutoTokenizer.from_pretrained(FINNISH_FALLBACK_MODEL, **tokenizer_kwargs)
                model = AutoModelForTokenClassification.from_pretrained(
                    FINNISH_FALLBACK_MODEL, **tokenizer_kwargs
                )
            except Exception:
                # If that fails, try using the model with a generic NER head
                logger.warning("Model not found as NER model, trying alternative approach...")
                # Use a multilingual NER model that supports Finnish
                alternative_model = "xlm-roberta-large-finetuned-conll03-english"
                logger.info(f"Trying alternative: {alternative_model}")
                tokenizer = AutoTokenizer.from_pretrained(alternative_model, **tokenizer_kwargs)
                model = AutoModelForTokenClassification.from_pretrained(
                    alternative_model, **tokenizer_kwargs
                )

            nlp_pipeline = pipeline(
                task="ner",
                model=model,
                tokenizer=tokenizer,
                aggregation_strategy="first",
                device=0 if self.device == "cuda" else -1,
            )

            self.pipelines["finnish_fallback"] = nlp_pipeline
            logger.info("✅ Loaded Finnish fallback model")
            return nlp_pipeline

        except Exception as e:
            logger.error(f"❌ Failed to load Finnish fallback model: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def _normalize_entity_label(self, label: str) -> str:
        """Normalize entity labels across different models."""
        # Remove B-/I- prefixes
        label_clean = re.sub(r"^[BI]-", "", label)
        return ENTITY_LABEL_MAPPING.get(label_clean, label_clean)

    def extract_entities(self, text: str, country: str = "") -> Dict:
        """
        Extract named entities from text using country-specific model.
        
        Returns:
            {
                "persons": [{"name": "...", "sentiment": "neutral"}],
                "locations": [...],
                "organizations": [...]
            }
        """
        if not text or len(text.strip()) < 10:
            logger.debug(f"Skipping empty/short text (length: {len(text) if text else 0})")
            return {"persons": [], "locations": [], "organizations": []}

        try:
            # Truncate text (models typically have 512 token limit)
            text_truncated = self._truncate_text(text, max_tokens=500)
            logger.debug(f"Text length: {len(text)} -> {len(text_truncated)} (truncated)")

            # Load appropriate model for country
            logger.debug(f"Loading model for country: {country}")
            nlp_pipeline = self._load_model(country)

            # Extract entities
            logger.debug(f"Running NER pipeline on text (first 100 chars: {text_truncated[:100]}...)")
            logger.debug(f"Country: {country}, Model: {self.models.get(country, 'unknown')}")
            
            try:
                entities = nlp_pipeline(text_truncated)
                logger.debug(f"Extracted {len(entities)} raw entities")
                
                # Special logging for Finnish to debug issues
                if country.lower() == "finland":
                    logger.info(f"🇫🇮 Finnish article: extracted {len(entities)} entities")
                    if len(entities) == 0:
                        logger.warning(f"⚠️  No entities found for Finnish text (length: {len(text_truncated)})")
                        logger.debug(f"Text sample: {text_truncated[:200]}")
            except Exception as e:
                logger.error(f"Error running NER pipeline for {country}: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                # Return empty entities on error
                return {"persons": [], "locations": [], "organizations": []}

            # Process and categorize entities
            persons = []
            locations = []
            organizations = []

            for entity in entities:
                # Filter by score threshold
                score = entity.get("score", 0)
                if score < self.score_threshold:
                    logger.debug(f"Filtered entity (score {score:.3f} < {self.score_threshold}): {entity.get('word', '')}")
                    continue

                entity_name = entity.get("word", "").strip()
                entity_label = entity.get("entity_group", "")

                if not entity_name:
                    logger.debug(f"Skipping empty entity name")
                    continue

                # Normalize label
                normalized_label = self._normalize_entity_label(entity_label)
                logger.debug(f"Entity: {entity_name} ({entity_label} -> {normalized_label}, score: {score:.3f})")

                # Categorize entity
                entity_data = {
                    "name": entity_name,
                    "sentiment": "neutral",  # Could add sentiment analysis later
                }

                if normalized_label == "PER":
                    persons.append(entity_data)
                elif normalized_label == "LOC":
                    locations.append(entity_data)
                elif normalized_label == "ORG":
                    organizations.append(entity_data)
                else:
                    logger.debug(f"Uncategorized entity label: {normalized_label}")

            # Deduplicate entities (same name)
            persons = self._deduplicate_entities(persons)
            locations = self._deduplicate_entities(locations)
            organizations = self._deduplicate_entities(organizations)

            result = {
                "persons": persons[:20],  # Limit to top 20
                "locations": locations[:20],
                "organizations": organizations[:20],
            }
            logger.debug(f"Final entities: {len(persons)} persons, {len(locations)} locations, {len(organizations)} orgs")
            return result

        except Exception as e:
            logger.error(f"Error extracting entities for {country}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {"persons": [], "locations": [], "organizations": []}

    def _truncate_text(self, text: str, max_tokens: int = 500) -> str:
        """Truncate text to max_tokens words."""
        words = text.split()
        if len(words) > max_tokens:
            return " ".join(words[:max_tokens])
        return text

    def _deduplicate_entities(self, entities: List[Dict]) -> List[Dict]:
        """Remove duplicate entities by name (case-insensitive)."""
        seen = set()
        unique = []
        for entity in entities:
            name_lower = entity["name"].lower()
            if name_lower not in seen:
                seen.add(name_lower)
                unique.append(entity)
        return unique

    def process_batch(self, df: pl.DataFrame) -> pl.DataFrame:
        """Process a batch of articles and extract entities."""
        logger.info(f"Processing {len(df)} articles for NER")
        logger.info(f"Countries in batch: {df['country'].unique().to_list() if 'country' in df.columns else 'N/A'}")

        results = []
        processed_count = 0
        error_count = 0
        
        for idx, row in enumerate(tqdm(df.iter_rows(named=True), total=len(df), desc="Extracting entities")):
            try:
                url = row.get("url", f"row_{idx}")
                content = row.get("content", "")
                country = row.get("country", "")
                
                logger.debug(f"[{idx+1}/{len(df)}] Processing article: {url[:50]}... (country: {country})")

                # Fallback to title + description if content is empty
                if not content or len(content.strip()) < 50:
                    title = row.get("title", "")
                    description = row.get("description", "")
                    content = f"{title}\n\n{description}".strip()
                    logger.debug(f"Using title+description fallback (content length: {len(content)})")

                if len(content) < 10:
                    logger.debug(f"Skipping article {idx+1}: content too short ({len(content)} chars)")
                    results.append({
                        "entities_json": json.dumps({"persons": [], "locations": [], "organizations": []}),
                        "ner_processed_at": datetime.now().isoformat(),
                    })
                    continue

                # Extract entities
                logger.debug(f"Extracting entities from article {idx+1}...")
                entities = self.extract_entities(content, country=country)
                processed_count += 1

                results.append({
                    "entities_json": json.dumps(entities),
                    "ner_processed_at": datetime.now().isoformat(),
                })
                
                # Log progress every 10 articles
                if (idx + 1) % 10 == 0:
                    logger.info(f"Progress: {idx+1}/{len(df)} articles processed ({processed_count} successful, {error_count} errors)")

            except Exception as e:
                error_count += 1
                logger.error(f"Error processing article {idx+1}: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                results.append({
                    "entities_json": json.dumps({"persons": [], "locations": [], "organizations": []}),
                    "ner_processed_at": datetime.now().isoformat(),
                })

        logger.info(f"✅ Batch processing complete: {processed_count} successful, {error_count} errors")

        # Add results as new columns
        df = df.with_columns([
            pl.Series("entities_json", [r["entities_json"] for r in results]),
            pl.Series("ner_processed_at", [r["ner_processed_at"] for r in results]),
        ])

        # Print summary
        total_entities = sum(
            len(json.loads(r["entities_json"]).get("persons", [])) +
            len(json.loads(r["entities_json"]).get("locations", [])) +
            len(json.loads(r["entities_json"]).get("organizations", []))
            for r in results
        )
        logger.info(f"✅ Extracted {total_entities} total entities from {len(df)} articles")

        return df


def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(description="Country-Specific NER Processing")
    parser.add_argument(
        "--input", type=str, required=True, help="Input parquet file path"
    )
    parser.add_argument(
        "--output", type=str, help="Output parquet file path (optional)"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda",
        choices=["cuda", "cpu"],
        help="Device to use",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size for processing",
    )
    parser.add_argument(
        "--score-threshold",
        type=float,
        default=0.5,
        help="Minimum confidence score for entities",
    )
    parser.add_argument(
        "--hf-token",
        type=str,
        help="Hugging Face token (or set HF_TOKEN env var)",
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("NAMO Country-Specific NER Processing")
    logger.info("=" * 60)
    logger.info(f"Input file: {args.input}")
    logger.info(f"Device: {args.device}")
    logger.info(f"Score threshold: {args.score_threshold}")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Log file: {LOG_FILE}")
    logger.info("=" * 60)

    # Load data
    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = BASE_DIR / args.input

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return

    logger.info(f"Loading data from {input_path}")
    try:
        df = pl.read_parquet(input_path)
        logger.info(f"✅ Loaded {len(df)} articles")
        logger.debug(f"Columns: {df.columns}")
        logger.debug(f"Memory usage: {df.estimated_size('mb'):.2f} MB")
    except Exception as e:
        logger.error(f"Failed to load parquet file: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return

    # Initialize NER processor
    ner_processor = CountrySpecificNER(
        device=args.device,
        batch_size=args.batch_size,
        score_threshold=args.score_threshold,
        hf_token=args.hf_token,
    )

    # Process
    df_enriched = ner_processor.process_batch(df)

    # Save
    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = OUTPUT_DIR / args.output
    else:
        output_path = OUTPUT_DIR / f"ner_enriched_{input_path.stem}.parquet"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_enriched.write_parquet(output_path)
    logger.info(f"✅ Saved {len(df_enriched)} articles to {output_path}")

    # Print summary by country
    logger.info("\n📊 Entity Extraction Summary by Country:")
    for country in ["denmark", "sweden", "norway", "finland"]:
        country_df = df_enriched.filter(pl.col("country") == country)
        if len(country_df) > 0:
            total_entities = 0
            for row in country_df.iter_rows(named=True):
                entities = json.loads(row.get("entities_json", "{}"))
                total_entities += (
                    len(entities.get("persons", [])) +
                    len(entities.get("locations", [])) +
                    len(entities.get("organizations", []))
                )
            logger.info(f"  {country.capitalize()}: {total_entities} entities from {len(country_df)} articles")


if __name__ == "__main__":
    main()

