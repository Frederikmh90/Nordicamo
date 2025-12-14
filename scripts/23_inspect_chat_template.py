#!/usr/bin/env python3
"""
Inspect Qwen2.5 Chat Template Output
====================================
Shows what the actual prompt looks like after applying chat template.
This helps debug why the model is generating text continuations.
"""

# This can run locally without torch - just inspect the template
try:
    from transformers import AutoTokenizer
    import json
except ImportError:
    print("⚠️  transformers not installed locally - this script needs to run on the server")
    print("   Or install: pip install transformers")
    exit(1)

def inspect_template(model_name: str = "Qwen/Qwen2.5-7B-Instruct"):
    """Inspect what the chat template produces."""
    
    print("="*80)
    print(f"Inspecting Chat Template for: {model_name}")
    print("="*80)
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    except Exception as e:
        print(f"❌ Could not load tokenizer: {e}")
        print("   This script needs to run on the server or with transformers installed")
        return
    
    # Test with current prompt format
    categories_str = "\n".join(["- Politics & Governance", "- Crime & Justice", "- Other"])
    
    prompt = f"""You are a news article analyzer. Your task is to analyze the article below and respond with ONLY a valid JSON object.

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

Available categories:
{categories_str}

Article to analyze:
This is a test article about politics and governance in Denmark.

Now respond with ONLY the JSON object (no other text):"""

    # Test different message formats
    test_cases = [
        ("User only", [{"role": "user", "content": prompt}]),
        ("System + User", [
            {"role": "system", "content": "You are a JSON-only analyzer. Respond with ONLY valid JSON."},
            {"role": "user", "content": prompt}
        ]),
        ("Simplified user", [{"role": "user", "content": "Analyze this article and return JSON:\n{\"sentiment\": \"neutral\", \"categories\": [\"Politics\"]}\n\nArticle: Test article"}]),
    ]
    
    for name, messages in test_cases:
        print(f"\n{'='*80}")
        print(f"Test Case: {name}")
        print(f"{'='*80}")
        
        try:
            # Apply chat template
            text_input = tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            
            print(f"\n📝 Full prompt (first 1000 chars):")
            print("-"*80)
            print(text_input[:1000])
            if len(text_input) > 1000:
                print(f"\n... (truncated, total length: {len(text_input)} chars)")
            print("-"*80)
            
            # Check what comes after the article text
            article_marker = "Article to analyze:" if "Article to analyze:" in text_input else "Article:"
            if article_marker in text_input:
                idx = text_input.find(article_marker)
                after_article = text_input[idx:]
                print(f"\n📄 Text after '{article_marker}' (last 500 chars):")
                print("-"*80)
                print(after_article[-500:])
                print("-"*80)
            
            # Check for special tokens
            special_tokens = ["<|im_start|>", "<|im_end|>", "<|endoftext|>", "<|user|>", "<|assistant|>"]
            found_tokens = [t for t in special_tokens if t in text_input]
            if found_tokens:
                print(f"\n🔤 Special tokens found: {found_tokens}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Check tokenizer special tokens
    print(f"\n{'='*80}")
    print("Tokenizer Configuration")
    print(f"{'='*80}")
    print(f"EOS token: {tokenizer.eos_token} (ID: {tokenizer.eos_token_id})")
    print(f"PAD token: {tokenizer.pad_token} (ID: {tokenizer.pad_token_id})")
    print(f"BOS token: {tokenizer.bos_token} (ID: {tokenizer.bos_token_id})")
    print(f"Chat template: {tokenizer.chat_template is not None}")
    
    if hasattr(tokenizer, 'chat_template') and tokenizer.chat_template:
        print(f"\nChat template type: {type(tokenizer.chat_template)}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Inspect Qwen2.5 chat template")
    parser.add_argument(
        "--model",
        type=str,
        default="Qwen/Qwen2.5-7B-Instruct",
        help="Model name"
    )
    
    args = parser.parse_args()
    inspect_template(args.model)

