#!/usr/bin/env python3
"""
NAMO NLP Processing with OpenRouter API
========================================
Uses OpenRouter API with function calling for reliable JSON output.
Based on working domain classification example.
"""

import polars as pl
import json
import os
import time
from pathlib import Path
from typing import Dict, Optional, List
from tqdm import tqdm
import logging
from datetime import datetime
import requests
import spacy

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "data" / "nlp_enriched"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# News categories
NEWS_CATEGORIES = [
    "Politics & Governance",
    "Immigration & National Identity",
    "Health & Medicine",
    "Media & Censorship",
    "International Relations & Conflict",
    "Economy & Labor",
    "Crime & Justice",
    "Social Issues & Culture",
    "Environment, Climate & Energy",
    "Technology, Science & Digital Society",
    "Other",
]


class NLPProcessorOpenRouter:
    """NLP processor using OpenRouter API with function calling."""

    def __init__(self, api_key: str, model_name: str = "openai/gpt-4o-mini"):
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # System prompt
        self.system_prompt = f"""You are a news article analyzer. Analyze articles and classify them into categories.

CATEGORIES (choose 1-3 most relevant):
1. Politics & Governance - Political content, government, elections
2. Immigration & National Identity - Immigration, borders, refugees, national identity
3. Health & Medicine - Health, medical, disease content
4. Media & Censorship - Media, journalism, censorship issues
5. International Relations & Conflict - International affairs, war, geopolitics
6. Economy & Labor - Financial, economic, stock market, labor issues
7. Crime & Justice - Legal, court, regulatory, lawsuit content
8. Social Issues & Culture - Social, cultural, gender, education issues
9. Environment, Climate & Energy - Environment, climate, energy content
10. Technology, Science & Digital Society - Technology, science, digital issues
11. Other - Only use if article truly doesn't fit any category (should be <1%)

SENTIMENT: "positive", "negative", or "neutral"

RULES:
- ALWAYS assign at least ONE category
- Use "Other" EXTREMELY RARELY (<1% of articles)
- Choose 1-3 most relevant categories
- Most articles fit multiple categories - choose the MOST relevant"""

        # Tool specification for structured output
        self.tool_spec = [
            {
                "type": "function",
                "function": {
                    "name": "analyze_article",
                    "description": "Analyze a news article and return sentiment and categories.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sentiment": {
                                "type": "string",
                                "enum": ["positive", "negative", "neutral"],
                                "description": "Overall sentiment of the article",
                            },
                            "categories": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": NEWS_CATEGORIES,
                                },
                                "minItems": 1,
                                "maxItems": 3,
                                "description": "1-3 most relevant categories",
                            },
                            "reasoning": {
                                "type": "string",
                                "maxLength": 500,
                                "description": "Brief explanation for sentiment and category choices",
                            },
                        },
                        "required": ["sentiment", "categories", "reasoning"],
                        "additionalProperties": False,
                    },
                },
            }
        ]

    def analyze_article(self, text: str) -> Dict:
        """Analyze a single article using OpenRouter API."""
        # Truncate text
        words = text.split()
        if len(words) > 600:
            text_truncated = " ".join(words[:600]) + "..."
        else:
            text_truncated = text

        user_prompt = f"""Analyze this news article:

{text_truncated}

Provide:
1. Sentiment (positive/negative/neutral)
2. 1-3 most relevant categories
3. Brief reasoning

Remember: Use "Other" only if article truly doesn't fit any category (should be rare)."""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "tools": self.tool_spec,
            "tool_choice": {
                "type": "function",
                "function": {"name": "analyze_article"},
            },
            "temperature": 0.1,
            "max_tokens": 1000,
        }

        try:
            response = requests.post(
                self.base_url, headers=headers, json=payload, timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            message = result["choices"][0]["message"]
            
            if "tool_calls" in message and len(message["tool_calls"]) > 0:
                tool_call = message["tool_calls"][0]
                args = json.loads(tool_call["function"]["arguments"])
                
                # Validate categories
                categories = args.get("categories", [])
                valid_categories = [c for c in categories if c in NEWS_CATEGORIES]
                
                if not valid_categories:
                    valid_categories = ["Other"]
                    logger.warning(f"⚠️  No valid categories found, assigned 'Other'")
                
                sentiment_scores = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}
                
                return {
                    "sentiment": args.get("sentiment", "neutral"),
                    "sentiment_score": sentiment_scores.get(args.get("sentiment", "neutral"), 0.0),
                    "categories": valid_categories[:3],  # Max 3
                    "reasoning": args.get("reasoning", ""),
                    "nlp_processed_at": datetime.now().isoformat(),
                }
            else:
                logger.warning("No tool_calls in response")
                return self._fallback_result()
                
        except Exception as e:
            logger.error(f"API call failed: {e}")
            return self._fallback_result()

    def _fallback_result(self) -> Dict:
        """Fallback result for failed API calls."""
        return {
            "sentiment": "neutral",
            "sentiment_score": 0.0,
            "categories": ["Other"],
            "reasoning": "API call failed",
            "nlp_processed_at": datetime.now().isoformat(),
        }

    def extract_entities(self, text: str) -> Dict:
        """Extract named entities using spaCy (same as original)."""
        try:
            nlp = spacy.load("xx_ent_wiki_sm")
            doc = nlp(text[:5000])  # Truncate for performance
            
            persons = [{"name": ent.text} for ent in doc.ents if ent.label_ in ["PER", "PERSON"]]
            locations = [{"name": ent.text} for ent in doc.ents if ent.label_ in ["LOC", "GPE"]]
            organizations = [{"name": ent.text} for ent in doc.ents if ent.label_ == "ORG"]
            
            # Deduplicate
            persons = [dict(t) for t in {tuple(d.items()) for d in persons}]
            locations = [dict(t) for t in {tuple(d.items()) for d in locations}]
            organizations = [dict(t) for t in {tuple(d.items()) for d in organizations}]
            
            return {
                "persons": persons[:10],
                "locations": locations[:10],
                "organizations": organizations[:10],
            }
        except Exception as e:
            logger.warning(f"NER failed: {e}")
            return {"persons": [], "locations": [], "organizations": []}

    def process_batch(self, df: pl.DataFrame) -> pl.DataFrame:
        """Process a batch of articles."""
        logger.info(f"Processing {len(df)} articles with OpenRouter API")
        
        # Load spaCy model once
        try:
            nlp = spacy.load("xx_ent_wiki_sm")
        except:
            logger.warning("spaCy model not available - NER will be skipped")
            nlp = None
        
        results = []
        for row in tqdm(df.iter_rows(named=True), total=len(df)):
            content = row.get("content", "")
            if not content or len(content.strip()) < 50:
                results.append({
                    **self._fallback_result(),
                    "entities": {"persons": [], "locations": [], "organizations": []},
                })
                continue
            
            # Analyze with OpenRouter
            result = self.analyze_article(content)
            
            # Extract entities with spaCy
            if nlp:
                entities = self.extract_entities(content)
            else:
                entities = {"persons": [], "locations": [], "organizations": []}
            
            results.append({
                **result,
                "entities": entities,
            })
            
            # Rate limiting (OpenRouter has rate limits)
            time.sleep(0.1)  # Adjust based on your API limits
        
        # Add results as new columns
        df = df.with_columns([
            pl.Series("sentiment", [r["sentiment"] for r in results]),
            pl.Series("sentiment_score", [r["sentiment_score"] for r in results]),
            pl.Series("categories", [json.dumps(r["categories"]) for r in results]),
            pl.Series("entities_json", [json.dumps(r["entities"]) for r in results]),
            pl.Series("nlp_processed_at", [r["nlp_processed_at"] for r in results]),
        ])
        
        return df


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="NAMO NLP Processing with OpenRouter")
    parser.add_argument("--input", type=str, required=True, help="Input parquet file")
    parser.add_argument("--output", type=str, help="Output parquet file")
    parser.add_argument(
        "--model",
        type=str,
        default="openai/gpt-4o-mini",
        help="OpenRouter model name (e.g., openai/gpt-4o-mini, anthropic/claude-3-haiku)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="OpenRouter API key (or set OPENROUTER_API_KEY env var)",
    )
    
    args = parser.parse_args()
    
    # Get API key
    api_key = args.api_key or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.error("No API key provided. Set OPENROUTER_API_KEY or use --api-key")
        return
    
    # Load data
    input_path = BASE_DIR / args.input
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return
    
    logger.info(f"Loading data from {input_path}")
    df = pl.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} articles")
    
    # Initialize processor
    processor = NLPProcessorOpenRouter(api_key=api_key, model_name=args.model)
    
    # Process
    df_enriched = processor.process_batch(df)
    
    # Save
    output_path = (
        BASE_DIR / args.output
        if args.output
        else OUTPUT_DIR / f"nlp_enriched_{input_path.stem}.parquet"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_enriched.write_parquet(output_path)
    logger.info(f"Saved to {output_path}")


if __name__ == "__main__":
    main()

