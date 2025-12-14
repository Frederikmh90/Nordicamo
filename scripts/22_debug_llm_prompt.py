#!/usr/bin/env python3
"""
Debug LLM Prompt and Generation
=================================
Tests different prompt formats and generation parameters on a small dataset
to identify why the model is generating text continuations instead of JSON.
"""

import polars as pl
from pathlib import Path
import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent

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


def test_prompt_variations(model, tokenizer, device, article_text: str, max_samples: int = 5):
    """Test different prompt formats to see which works best."""
    
    categories_str = "\n".join([f"- {cat}" for cat in NEWS_CATEGORIES])
    text_truncated = article_text[:500]  # Truncate for testing
    
    # Prompt Variation 1: Current format (user message only)
    prompt_v1 = f"""You are a news article analyzer. Your task is to analyze the article below and respond with ONLY a valid JSON object.

REQUIRED OUTPUT FORMAT (JSON only, no other text):
{{
  "sentiment": "positive|negative|neutral",
  "categories": ["category1", "category2"],
  "reasoning": "brief explanation"
}}

CRITICAL RULES:
1. Your response MUST start with {{ and end with }}
2. Do NOT continue the article text
3. Do NOT add any explanation before or after the JSON
4. ALWAYS assign at least ONE category. "Other" should be EXTREMELY RARE (<1% of articles).

Category mapping guide:
- Financial/economic/stock market → "Economy & Labor"
- Legal/court/regulatory/lawsuit → "Crime & Justice"
- Political/government/elections → "Politics & Governance"
- Immigration/border/refugees → "Immigration & National Identity"
- Health/medical/disease → "Health & Medicine"
- Media/journalism/censorship → "Media & Censorship"
- International/war/geopolitics → "International Relations & Conflict"
- Social/cultural/gender/education → "Social Issues & Culture"
- Environment/climate/energy → "Environment, Climate & Energy"
- Technology/science/digital → "Technology, Science & Digital Society"

Available categories:
{categories_str}

Article to analyze:
{text_truncated}

Now respond with ONLY the JSON object (no other text):"""

    # Prompt Variation 2: More explicit JSON schema
    prompt_v2 = f"""Analyze this news article and return ONLY a JSON object with this exact structure:

{{
  "sentiment": "positive" OR "negative" OR "neutral",
  "categories": ["category_name1", "category_name2"],
  "reasoning": "brief explanation"
}}

Categories available:
{categories_str}

Article:
{text_truncated}

JSON:"""

    # Prompt Variation 3: System + User with explicit JSON instruction
    prompt_v3_system = """You are a JSON-only news analyzer. You MUST respond with ONLY valid JSON. Never add text before or after the JSON object."""
    prompt_v3_user = f"""Analyze this article and return JSON:

{{
  "sentiment": "positive|negative|neutral",
  "categories": ["category1", "category2"],
  "reasoning": "explanation"
}}

Categories: {categories_str}

Article: {text_truncated}"""

    # Prompt Variation 4: Very explicit with example
    prompt_v4 = f"""Task: Analyze news article and return JSON.

Example response:
{{
  "sentiment": "negative",
  "categories": ["Crime & Justice", "International Relations & Conflict"],
  "reasoning": "Article about UN employee termination"
}}

Categories: {categories_str}

Article: {text_truncated}

Response (JSON only):"""

    prompts = [
        ("V1: Current format", [{"role": "user", "content": prompt_v1}]),
        ("V2: Explicit schema", [{"role": "user", "content": prompt_v2}]),
        ("V3: System+User", [
            {"role": "system", "content": prompt_v3_system},
            {"role": "user", "content": prompt_v3_user}
        ]),
        ("V4: With example", [{"role": "user", "content": prompt_v4}]),
    ]
    
    results = []
    
    for name, messages in prompts[:max_samples]:
        print(f"\n{'='*80}")
        print(f"Testing: {name}")
        print(f"{'='*80}")
        
        # Apply chat template
        text_input = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        
        print(f"\n📝 Full prompt sent to model (first 500 chars):")
        print("-"*80)
        print(text_input[:500])
        print("...")
        print("-"*80)
        
        # Tokenize
        inputs = tokenizer(
            text_input,
            return_tensors="pt",
            truncation=True,
            max_length=1024,
        ).to(device)
        
        # Generate with different parameters
        generation_configs = [
            ("Low temp, greedy", {"temperature": 0.0, "do_sample": False}),
            ("Low temp, sampled", {"temperature": 0.1, "do_sample": True, "top_p": 0.95}),
            ("Very low temp", {"temperature": 0.05, "do_sample": True, "top_p": 0.9}),
        ]
        
        for config_name, gen_params in generation_configs:
            print(f"\n🔧 Generation config: {config_name}")
            print("-"*80)
            
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=200,
                    pad_token_id=tokenizer.eos_token_id,
                    eos_token_id=tokenizer.eos_token_id,
                    **gen_params
                )
            
            # Decode
            generated_tokens = outputs[0][inputs["input_ids"].shape[1]:]
            response = tokenizer.decode(generated_tokens, skip_special_tokens=True)
            
            print(f"Raw response: {response[:300]}")
            
            # Check if it starts with {
            starts_with_json = response.strip().startswith("{")
            has_json = "{" in response
            
            print(f"\n✅ Starts with {{: {starts_with_json}")
            print(f"✅ Contains {{: {has_json}")
            
            if has_json:
                # Try to extract JSON
                json_start = response.find("{")
                json_end = response.rfind("}")
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end+1]
                    try:
                        parsed = json.loads(json_str)
                        print(f"✅ Valid JSON: {parsed}")
                        results.append((name, config_name, True, parsed))
                    except Exception as e:
                        print(f"❌ Invalid JSON: {e}")
                        print(f"   JSON string: {json_str[:200]}")
                        results.append((name, config_name, False, None))
                else:
                    print(f"❌ Could not find complete JSON")
                    results.append((name, config_name, False, None))
            else:
                print(f"❌ No JSON found - got text continuation")
                results.append((name, config_name, False, None))
            
            print("-"*80)
    
    return results


def main():
    """Main debug function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Debug LLM prompt and generation")
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/NAMO_preprocessed_test.parquet",
        help="Input parquet file"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="Qwen/Qwen2.5-7B-Instruct",
        help="Model name"
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=3,
        help="Number of articles to test"
    )
    
    args = parser.parse_args()
    
    # Load data
    input_path = BASE_DIR / args.input
    if not input_path.exists():
        print(f"❌ Input file not found: {input_path}")
        return
    
    print(f"✅ Loading data from: {input_path}")
    df = pl.read_parquet(input_path)
    print(f"✅ Loaded {len(df):,} articles")
    
    # Sample articles
    df_sample = df.head(args.samples)
    print(f"\n📋 Testing with {len(df_sample)} articles")
    
    # Load model
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"\n🔧 Loading model: {args.model}")
    print(f"   Device: {device}")
    
    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        device_map="auto" if device == "cuda" else None,
        trust_remote_code=True,
    )
    model.eval()
    
    print("✅ Model loaded")
    
    # Test each article
    all_results = []
    for i, row in enumerate(df_sample.iter_rows(named=True), 1):
        article_text = row.get("content", "")
        title = row.get("title", "No title")[:80]
        
        if not article_text or len(article_text) < 50:
            print(f"\n⚠️  Skipping article {i}: insufficient content")
            continue
        
        print(f"\n{'#'*80}")
        print(f"ARTICLE {i}: {title}")
        print(f"{'#'*80}")
        
        results = test_prompt_variations(model, tokenizer, device, article_text, max_samples=2)
        all_results.extend([(i, title, *r) for r in results])
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    
    successful = [r for r in all_results if r[4]]  # r[4] is the success boolean
    total = len(all_results)
    
    print(f"Total tests: {total}")
    print(f"Successful JSON: {len(successful)} ({len(successful)/total*100:.1f}%)")
    print(f"Failed: {total - len(successful)} ({(total - len(successful))/total*100:.1f}%)")
    
    if successful:
        print(f"\n✅ Best performing prompt/config combinations:")
        for r in successful[:5]:
            print(f"   Article {r[0]}: {r[2]} + {r[3]}")
    else:
        print(f"\n❌ No successful JSON generations - model may need different approach")


if __name__ == "__main__":
    main()

