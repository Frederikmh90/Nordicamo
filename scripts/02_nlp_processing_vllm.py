"""
NLP Processing with vLLM and Mistral Small 3.1 24B
Processes articles for sentiment, categories, and entity extraction using vLLM.
"""
import argparse
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

import polars as pl
from tqdm import tqdm
from vllm import LLM, SamplingParams

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# System prompt for the model
SYSTEM_PROMPT = """You are an expert analyst for the Nordic Alternative Media Observatory (NAMO).
Analyze news articles and extract structured information.

Output valid JSON only, no explanations."""


def create_analysis_prompt(title: str, description: str, content: str) -> str:
    """Create analysis prompt for an article."""
    text = f"Title: {title}\n"
    if description:
        text += f"Description: {description}\n"
    if content:
        text += f"Content: {content[:2000]}\n"  # Limit content length
    
    prompt = f"""{text}

Analyze this article and provide:
1. Sentiment: positive, negative, or neutral
2. Categories: List of relevant categories from: Politics, Immigration, Climate, Economy, Health, Education, Crime, International, Technology, Culture, Other
3. Entities: Key persons, organizations, and locations mentioned

Respond with valid JSON in this exact format:
{{
    "sentiment": "neutral",
    "categories": ["Politics", "Immigration"],
    "entities": {{
        "persons": ["Name1", "Name2"],
        "organizations": ["Org1"],
        "locations": ["Location1"]
    }}
}}"""
    return prompt


def parse_llm_output(output: str) -> Dict[str, Any]:
    """Parse LLM JSON output with error handling."""
    try:
        # Try to extract JSON from markdown code blocks if present
        if "```json" in output:
            output = output.split("```json")[1].split("```")[0].strip()
        elif "```" in output:
            output = output.split("```")[1].split("```")[0].strip()
        
        result = json.loads(output)
        
        # Validate structure
        if not isinstance(result.get("sentiment"), str):
            result["sentiment"] = "neutral"
        if not isinstance(result.get("categories"), list):
            result["categories"] = []
        if not isinstance(result.get("entities"), dict):
            result["entities"] = {"persons": [], "organizations": [], "locations": []}
            
        return result
    except Exception as e:
        logger.warning(f"Failed to parse LLM output: {e}. Output was: {output[:200]}")
        return {
            "sentiment": "neutral",
            "categories": [],
            "entities": {"persons": [], "organizations": [], "locations": []}
        }


def process_batch_vllm(
    llm: LLM,
    articles: List[Dict[str, Any]],
    sampling_params: SamplingParams
) -> List[Dict[str, Any]]:
    """Process a batch of articles using vLLM."""
    # Create prompts for all articles
    prompts = []
    for article in articles:
        user_prompt = create_analysis_prompt(
            article.get("title", ""),
            article.get("description", ""),
            article.get("content", "")
        )
        
        # Format as chat message for vLLM
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        prompts.append(messages)
    
    # Generate outputs for all prompts in batch
    outputs = llm.chat(prompts, sampling_params=sampling_params)
    
    # Parse results
    results = []
    for output in outputs:
        text = output.outputs[0].text
        parsed = parse_llm_output(text)
        results.append(parsed)
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Process articles with vLLM and Mistral Small 3.1 24B"
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Input parquet file path"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output parquet file path"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="mistralai/Mistral-Small-3.1-24B-Instruct-2503",
        help="Model name"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=8,
        help="Batch size for processing"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=512,
        help="Maximum tokens for generation"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.15,
        help="Temperature for generation (0.15 recommended by model card)"
    )
    parser.add_argument(
        "--gpu-memory-utilization",
        type=float,
        default=0.9,
        help="GPU memory utilization (0.0-1.0)"
    )
    
    args = parser.parse_args()
    
    # Load data
    logger.info(f"Loading data from {args.input}")
    df = pl.read_parquet(args.input)
    logger.info(f"Loaded {len(df)} articles")
    
    # Initialize vLLM
    logger.info(f"Initializing vLLM with model: {args.model}")
    llm = LLM(
        model=args.model,
        tokenizer_mode="mistral",
        gpu_memory_utilization=args.gpu_memory_utilization,
        max_model_len=4096,  # Context length
    )
    logger.info("✓ vLLM initialized successfully")
    
    # Sampling parameters
    sampling_params = SamplingParams(
        max_tokens=args.max_tokens,
        temperature=args.temperature,
    )
    
    # Process articles in batches
    articles = df.to_dicts()
    all_results = []
    
    logger.info(f"Processing {len(articles)} articles in batches of {args.batch_size}")
    for i in tqdm(range(0, len(articles), args.batch_size), desc="Processing batches"):
        batch = articles[i:i + args.batch_size]
        batch_results = process_batch_vllm(llm, batch, sampling_params)
        all_results.extend(batch_results)
    
    # Add results to dataframe
    df = df.with_columns([
        pl.Series("sentiment", [r["sentiment"] for r in all_results]),
        pl.Series("categories", [r["categories"] for r in all_results]),
        pl.Series("entities_json", [json.dumps(r["entities"]) for r in all_results]),
    ])
    
    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(args.output)
    logger.info(f"✓ NLP enriched data saved: {args.output}")
    
    # Show sample
    print("\n" + "=" * 80)
    print("Sample of NLP enriched data:")
    print("=" * 80)
    print(df.select(["title", "sentiment", "categories", "entities_json"]).head(3))


if __name__ == "__main__":
    main()


