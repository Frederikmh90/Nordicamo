"""
NAMO NLP Processing Pipeline
=============================
This script performs NLP enrichment on preprocessed articles:
1. Sentiment analysis (using Qwen2.5 quantized LLM)
2. Category classification (using Qwen2.5 quantized LLM)
3. Named Entity Recognition (using spaCy multilingual models)

Designed for Nordic languages (Danish, Swedish, Norwegian, Finnish).
Processes in batches to handle ~1M articles efficiently.
"""

import polars as pl
import json
import os
import time
from pathlib import Path
from typing import List, Dict, Optional
from tqdm import tqdm
import logging
from datetime import datetime
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import spacy
from spacy.language import Language
import re

# Setup logging - enable DEBUG with NLP_DEBUG=true environment variable
log_level = (
    logging.DEBUG if os.getenv("NLP_DEBUG", "false").lower() == "true" else logging.INFO
)
logging.basicConfig(level=log_level, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"
OUTPUT_DIR = BASE_DIR / "data" / "nlp_enriched"
OUTPUT_DIR.mkdir(exist_ok=True)

# Debug logging configuration (NDJSON). Primary is local workspace; secondary is home/NAMO_nov25 for remote runs.
LOG_PATHS = [
    Path("/Users/Codebase/projects/alterpublics/NAMO_nov25/.cursor/debug.log"),  # local workspace
    Path.home() / "NAMO_nov25" / ".cursor" / "debug.log",  # remote home project
    Path("/tmp/namo_debug.log"),  # fallback to always-writable temp
]


def _debug_log(hypothesisId: str, location: str, message: str, data: Dict):
    """Append a small NDJSON log line for GPU/LLM diagnostics."""
    payload = {
        "sessionId": "debug-session",
        "runId": "gpu-check",
        "hypothesisId": hypothesisId,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    for path in LOG_PATHS:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a") as f:
                f.write(json.dumps(payload) + "\n")
        except Exception:
            continue

# News categories (10 categories + "Other" for alternative/hyper-partisan media)
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
    "Other",  # For articles that don't fit clearly into other categories
]


class NLPProcessor:
    """Handles NLP processing using LLM and spaCy models."""

    def __init__(
        self,
        model_name: str = "mistralai/Mistral-7B-Instruct-v0.2",  # Changed default - better JSON following
        use_quantization: bool = False,  # Default False for better JSON output quality
        batch_size: int = 8,
        max_length: int = 512,
    ):
        self.model_name = model_name
        self.use_quantization = use_quantization
        self.batch_size = batch_size
        self.max_length = max_length
        # #region agent log
        _debug_log(
            hypothesisId="H1",
            location="NLPProcessor.__init__:pre-device",
            message="Checking CUDA availability",
            data={
                "torch_cuda_available": torch.cuda.is_available(),
                "torch_cuda_device_count": torch.cuda.device_count(),
                "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
                "torch_version": torch.__version__,
                "torch_cuda_version": torch.version.cuda,
            },
        )
        # #endregion

        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # #region agent log
        name = None
        try:
            if torch.cuda.is_available():
                name = torch.cuda.get_device_name(0)
        except Exception as e:
            name = f"device_name_error:{e}"
        _debug_log(
            hypothesisId="H1",
            location="NLPProcessor.__init__:post-device",
            message="Device selected",
            data={
                "device": self.device,
                "device_name": name,
                "torch_cuda_available": torch.cuda.is_available(),
            },
        )
        # #endregion

        # #region agent log
        if torch.cuda.device_count() > 0:
            try:
                torch.cuda.init()
                _debug_log(
                    hypothesisId="H1",
                    location="NLPProcessor.__init__:cuda-init",
                    message="torch.cuda.init success",
                    data={
                        "is_available": torch.cuda.is_available(),
                        "device_count": torch.cuda.device_count(),
                    },
                )
            except Exception as e:
                _debug_log(
                    hypothesisId="H1",
                    location="NLPProcessor.__init__:cuda-init",
                    message="torch.cuda.init error",
                    data={"error": repr(e)},
                )
        else:
            _debug_log(
                hypothesisId="H1",
                location="NLPProcessor.__init__:cuda-init",
                message="No CUDA devices found",
                data={"device_count": torch.cuda.device_count()},
            )
        # #endregion

        logger.info(f"Initializing NLP Processor on device: {self.device}")
        logger.info(f"Model: {model_name}, Quantization: {use_quantization}")

        # Load models
        self.tokenizer = None
        self.model = None
        self.nlp_models = {}

        self._load_llm()
        self._load_spacy_models()

    def _load_llm(self):
        """Load Qwen2.5 model for sentiment and categorization."""
        logger.info(f"Loading LLM: {self.model_name}")
        logger.info(f"Device: {self.device}")
        logger.info(f"Quantization: {self.use_quantization}")

        # Check GPU availability and memory before loading
        if self.device == "cuda":
            try:
                import subprocess

                result = subprocess.run(
                    [
                        "nvidia-smi",
                        "--query-gpu=memory.total,memory.free,name",
                        "--format=csv,noheader",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    gpu_info = result.stdout.strip().split("\n")[0]
                    logger.info(f"GPU Info: {gpu_info}")
            except Exception as e:
                logger.debug(f"Could not check GPU info: {e}")

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name, trust_remote_code=True
            )

            if self.use_quantization and self.device == "cuda":
                # 4-bit quantization for memory efficiency (fits ~8GB GPU)
                # Using NF4 quantization type for best quality/size tradeoff
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,  # Additional quantization for memory savings
                    bnb_4bit_quant_type="nf4",  # NormalFloat4 - optimized for LLMs
                )

                logger.info("Loading model with 4-bit quantization (NF4)")
                logger.warning(
                    "⚠️  Quantization enabled - may affect JSON output quality"
                )
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    quantization_config=quantization_config,
                    device_map="auto",  # Automatically distribute across GPUs if available
                    trust_remote_code=True,
                    torch_dtype=torch.float16,  # Use float16 for compute
                )
            else:
                logger.info(
                    "Loading model WITHOUT quantization (full precision for better JSON output)"
                )
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float16
                    if self.device == "cuda"
                    else torch.float32,
                    device_map="auto" if self.device == "cuda" else None,
                    trust_remote_code=True,
                )

            logger.info("LLM loaded successfully")

            # Log GPU memory usage after loading
            if self.device == "cuda":
                try:
                    import subprocess

                    result = subprocess.run(
                        [
                            "nvidia-smi",
                            "--query-gpu=memory.used,memory.total",
                            "--format=csv,noheader",
                        ],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if result.returncode == 0:
                        mem_info = result.stdout.strip().split("\n")[0]
                        logger.info(f"GPU Memory after loading: {mem_info}")
                except Exception as e:
                    logger.debug(f"Could not check GPU memory: {e}")

        except Exception as e:
            logger.error(f"Failed to load LLM: {e}")
            logger.warning("NLP processing will be limited without LLM")

    def _load_spacy_models(self):
        """Load spaCy models for NER (multilingual)."""
        logger.info("Loading spaCy models for NER")

        # Try to load multilingual model
        try:
            self.nlp_models["multi"] = spacy.load("xx_ent_wiki_sm")
            logger.info("Loaded spaCy multilingual model")
        except OSError:
            logger.warning(
                "Multilingual spaCy model not found. Install with: python -m spacy download xx_ent_wiki_sm"
            )
            logger.info("NER will be disabled")

    def truncate_text(self, text: str, max_tokens: int = 400) -> str:
        """Truncate text to fit within token limit."""
        if not text:
            return ""

        # Simple word-based truncation (approximate)
        words = text.split()
        if len(words) > max_tokens:
            return " ".join(words[:max_tokens]) + "..."
        return text

    def analyze_sentiment_and_category(self, text: str, language: str = "en") -> Dict:
        """Use LLM to analyze sentiment and categorize article."""
        if not self.model or not text:
            return {
                "sentiment": "neutral",
                "sentiment_score": 0.0,
                "categories": [],
            }

        # CRITICAL: Log what we're actually analyzing
        text_preview = text[:200] if text else "EMPTY"
        logger.info(f"📄 Analyzing article (length: {len(text)} chars)")
        logger.debug(f"   Preview: {text_preview}...")

        # Truncate text (but keep enough for meaningful analysis)
        # Increased from 400 to 600 tokens to preserve more context
        text_truncated = self.truncate_text(text, max_tokens=600)

        # Log truncated length
        logger.debug(f"📄 Truncated to: {len(text_truncated)} chars")

        categories_str = "\n".join([f"- {cat}" for cat in NEWS_CATEGORIES])
        model_lower = self.model_name.lower()

        try:

            def build_instruction(strict: bool = False) -> str:
                strict_section = ""
                if strict:
                    strict_section = (
                        "\n\nCRITICAL REMINDER: Your previous response was invalid. "
                        "You MUST respond with valid JSON only. Do NOT quote or summarize the article. "
                        "The JSON must start with { and end with } without any text before or after."
                    )

                return f"""You are a news article analyzer. Analyze the article below and respond with ONLY a valid JSON object.

IMPORTANT: Do NOT continue the article text. Your response must be JSON only.
{strict_section}

Required JSON format:
{{
  "sentiment": "positive" OR "negative" OR "neutral",
  "categories": ["category1", "category2"]
}}

Category mapping:
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

---
END OF ARTICLE. DO NOT CONTINUE THE ARTICLE TEXT.

Your task: Analyze the article above and respond with ONLY a JSON object in this exact format:
{{
  "sentiment": "positive" OR "negative" OR "neutral",
  "categories": ["category1", "category2"]
}}

Remember: Your response must be JSON only. Do not write any text before or after the JSON. Do not continue the article."""

            def format_prompt(instruction_text: str) -> str:
                if "mistral" in model_lower:
                    # Mistral format: <s>[INST] instruction [/INST]
                    # CRITICAL: Don't start JSON in prompt - let model generate it
                    return f"<s>[INST] {instruction_text} [/INST]"
                if "qwen" in model_lower:
                    return (
                        "<|im_start|>system\nYou are a JSON-only analyzer. "
                        "Always respond with valid JSON.\n<|im_end|>\n"
                        f"<|im_start|>user\n{instruction_text}\n<|im_end|>\n<|im_start|>assistant\n"
                    )
                return instruction_text

            def prepare_text_input(prompt_text: str) -> str:
                # CRITICAL FIX: Use tokenizer's chat template for ALL models
                # This ensures proper formatting that the model expects
                if "mistral" in model_lower:
                    # Extract the instruction text (remove any manual formatting)
                    instruction = (
                        prompt_text.replace("<s>[INST] ", "")
                        .replace(" [/INST]", "")
                        .strip()
                    )

                    # Use Mistral's official chat template with clear system message
                    messages = [
                        {
                            "role": "system",
                            "content": "You are a JSON-only analyzer. You MUST respond with ONLY valid JSON. Never continue article text. Never write explanations before or after JSON.",
                        },
                        {
                            "role": "user",
                            "content": instruction,
                        },
                    ]
                    formatted = self.tokenizer.apply_chat_template(
                        messages, tokenize=False, add_generation_prompt=True
                    )
                    logger.debug(
                        f"🔧 Mistral chat template applied. Length: {len(formatted)}"
                    )
                    logger.debug(f"   Template preview (last 300): {formatted[-300:]}")
                    return formatted
                if "qwen" in model_lower:
                    return prompt_text

                # Generic chat template for other models
                messages = [
                    {
                        "role": "system",
                        "content": "You are a JSON-only analyzer. Always respond with valid JSON.",
                    },
                    {"role": "user", "content": prompt_text},
                ]
                return self.tokenizer.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True
                )

            def extract_json_from_response(raw_response: str) -> Optional[Dict]:
                response_clean = raw_response.strip()
                response_clean = response_clean.replace("<|im_end|>", "").replace(
                    "<|im_start|>", ""
                )

                if response_clean.startswith("```json"):
                    response_clean = response_clean[7:]
                if response_clean.startswith("```"):
                    response_clean = response_clean[3:]
                if response_clean.endswith("```"):
                    response_clean = response_clean[:-3]
                response_clean = response_clean.strip()

                # Stop at balanced braces if extra text exists
                brace_count = 0
                json_end = -1
                for idx, char in enumerate(response_clean):
                    if char == "{":
                        brace_count += 1
                    elif char == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = idx + 1
                            break
                if json_end > 0:
                    response_clean = response_clean[:json_end]

                # If still no leading {, try to find first occurrence
                if not response_clean.startswith("{"):
                    json_start = response_clean.find("{")
                    if json_start > 0:
                        response_clean = response_clean[json_start:]
                    else:
                        return None

                # Strategy 1: Balanced braces regex
                json_match = re.search(
                    r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", response_clean, re.DOTALL
                )
                if json_match:
                    try:
                        return json.loads(json_match.group(0))
                    except Exception:
                        pass

                # Strategy 2: Parse entire response
                try:
                    return json.loads(response_clean)
                except Exception:
                    pass

                # Strategy 3: First { ... last }
                start = response_clean.find("{")
                end = response_clean.rfind("}")
                if start != -1 and end != -1 and end > start:
                    try:
                        return json.loads(response_clean[start : end + 1])
                    except Exception:
                        pass

                return None

            result = None
            response = ""
            max_attempts = 2

            for attempt in range(max_attempts):
                try:
                    instruction_text = build_instruction(strict=attempt > 0)
                    prompt = format_prompt(instruction_text)
                    text_input = prepare_text_input(prompt)

                    # Log prompt for debugging (first attempt only, to avoid spam)
                    if attempt == 0:
                        logger.info(f"🔧 Prompt format: {model_lower} model")
                        logger.debug(f"   Full prompt length: {len(text_input)} chars")
                        logger.debug(
                            f"   Prompt ending (last 400 chars):\n{text_input[-400:]}"
                        )

                    inputs = self.tokenizer(
                        text_input,
                        return_tensors="pt",
                        truncation=True,
                        max_length=self.max_length,
                    ).to(self.device)

                    with torch.no_grad():
                        outputs = self.model.generate(
                            **inputs,
                            max_new_tokens=100,  # Reduced from 200 - removed reasoning field
                            do_sample=False,
                            pad_token_id=self.tokenizer.eos_token_id,
                            eos_token_id=self.tokenizer.eos_token_id,
                            repetition_penalty=1.1,
                        )

                    generated_tokens = outputs[0][inputs["input_ids"].shape[1] :]
                    response = self.tokenizer.decode(
                        generated_tokens, skip_special_tokens=True
                    )

                    # Log raw response for debugging
                    logger.debug(
                        f"🤖 Raw LLM response (attempt {attempt + 1}, length: {len(response)}): {response[:400]}..."
                    )

                    result = extract_json_from_response(response)
                    if result:
                        logger.info(
                            f"✅ Successfully parsed JSON on attempt {attempt + 1}"
                        )
                        break

                    logger.warning(
                        "⚠️  Attempt %s failed to produce JSON. Response preview: %s",
                        attempt + 1,
                        response[:300],
                    )
                except Exception as gen_error:
                    logger.error(f"Failed to generate LLM response: {gen_error}")
                    break

            if not result:
                logger.error("❌ No valid JSON after %s attempts", max_attempts)
                logger.debug(f"Last response: {response[:500]}")
                logger.debug(f"Prompt preview: {prompt[:500]}")

                # Stop at first complete JSON object (balanced braces)
                # This prevents article continuation from being included
                brace_count = 0
                json_end = -1
                for i, char in enumerate(response):
                    if char == "{":
                        brace_count += 1
                    elif char == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i + 1
                            break

                if json_end > 0:
                    response = response[:json_end]

                # Try multiple JSON extraction strategies
                result = None

                # Strategy 1: Try to find JSON object with balanced braces
                json_match = re.search(
                    r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", response, re.DOTALL
                )
                if json_match:
                    try:
                        result = json.loads(json_match.group(0))
                    except:
                        pass

                # Strategy 2: Try to parse the entire response as JSON
                if result is None:
                    try:
                        result = json.loads(response)
                    except:
                        pass

                # Strategy 3: Try to find JSON between first { and last }
                if result is None:
                    start_idx = response.find("{")
                    end_idx = response.rfind("}")
                    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                        try:
                            result = json.loads(response[start_idx : end_idx + 1])
                        except:
                            pass

            if result:
                # Normalize sentiment
                sentiment = result.get("sentiment", "neutral").lower()
                if sentiment not in ["positive", "negative", "neutral"]:
                    sentiment = "neutral"

                # Validate and normalize categories
                categories = result.get("categories", [])
                if not isinstance(categories, list):
                    categories = []

                # Filter to only valid categories
                valid_categories = [cat for cat in categories if cat in NEWS_CATEGORIES]

                # If no valid categories, assign "Other" with detailed logging
                if not valid_categories:
                    valid_categories = ["Other"]
                    logger.warning(
                        f"⚠️  ASSIGNED 'Other' CATEGORY - No valid categories found in parsed result"
                    )
                    logger.warning(f"   Article preview: {text_truncated[:150]}...")
                    logger.warning(f"   Raw categories from LLM: {categories}")
                    logger.warning(
                        f"   ⚠️  This should be rare - consider reviewing the prompt or article content"
                    )

                # Assign sentiment score
                sentiment_scores = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}

                return {
                    "sentiment": sentiment,
                    "sentiment_score": sentiment_scores.get(sentiment, 0.0),
                    "categories": valid_categories[:3],  # Max 3
                }
            else:
                # Last resort: try to extract sentiment and categories from text
                logger.warning(
                    f"Could not parse JSON from LLM response. Attempting text extraction..."
                )
                logger.debug(f"Response preview: {response[:200]}")

                # Try to extract sentiment from text
                sentiment = "neutral"
                sentiment_lower = response.lower()
                if "sentiment" in sentiment_lower:
                    if (
                        '"sentiment": "positive"' in response
                        or "'sentiment': 'positive'" in response
                    ):
                        sentiment = "positive"
                    elif (
                        '"sentiment": "negative"' in response
                        or "'sentiment': 'negative'" in response
                    ):
                        sentiment = "negative"
                    elif (
                        '"sentiment": "neutral"' in response
                        or "'sentiment': 'neutral'" in response
                    ):
                        sentiment = "neutral"

                # Try to extract categories from text
                categories = []
                for cat in NEWS_CATEGORIES:
                    if cat.lower() in response.lower():
                        categories.append(cat)
                        if len(categories) >= 3:
                            break

                # If no categories found, assign "Other" with detailed logging
                if not categories:
                    categories = ["Other"]
                    logger.warning(
                        f"⚠️  ASSIGNED 'Other' CATEGORY - No categories found in response text"
                    )
                    logger.warning(f"   Raw LLM response: {response[:300]}...")
                    logger.warning(f"   Article preview: {text_truncated[:150]}...")
                    logger.warning(
                        f"   ⚠️  JSON parsing failed AND text extraction found no categories"
                    )
                    logger.warning(
                        f"   ⚠️  This indicates a problem - either LLM didn't follow instructions or article is truly unclassifiable"
                    )

                return {
                    "sentiment": sentiment,
                    "sentiment_score": {
                        "positive": 1.0,
                        "neutral": 0.0,
                        "negative": -1.0,
                    }.get(sentiment, 0.0),
                    "categories": categories[:3],
                }

        except Exception as e:
            logger.error(f"Error in sentiment/category analysis: {e}")
            return {
                "sentiment": "neutral",
                "sentiment_score": 0.0,
                "categories": [],
            }

    def extract_entities(self, text: str) -> Dict:
        """Extract named entities using spaCy."""
        if "multi" not in self.nlp_models or not text:
            return {"persons": [], "locations": [], "organizations": []}

        try:
            # Truncate for performance
            text_truncated = self.truncate_text(text, max_tokens=500)

            doc = self.nlp_models["multi"](text_truncated)

            persons = []
            locations = []
            organizations = []

            for ent in doc.ents:
                entity_data = {"name": ent.text}

                if ent.label_ == "PER" or ent.label_ == "PERSON":
                    persons.append(entity_data)
                elif ent.label_ == "LOC" or ent.label_ == "GPE":
                    locations.append(entity_data)
                elif ent.label_ == "ORG":
                    organizations.append(entity_data)

            # Deduplicate
            persons = [dict(t) for t in {tuple(d.items()) for d in persons}]
            locations = [dict(t) for t in {tuple(d.items()) for d in locations}]
            organizations = [dict(t) for t in {tuple(d.items()) for d in organizations}]

            return {
                "persons": persons[:10],  # Limit to top 10
                "locations": locations[:10],
                "organizations": organizations[:10],
            }

        except Exception as e:
            logger.error(f"Error in entity extraction: {e}")
            return {"persons": [], "locations": [], "organizations": []}

    def process_article(self, article_content: str, country: str = None) -> Dict:
        """Process a single article with all NLP tasks."""
        # Determine language from country
        lang_map = {"denmark": "da", "sweden": "sv", "norway": "no", "finland": "fi"}
        language = lang_map.get(country.lower() if country else "", "en")

        # Sentiment and categorization
        sentiment_result = self.analyze_sentiment_and_category(
            article_content, language
        )

        # Named entity recognition
        entities = self.extract_entities(article_content)

        return {
            "sentiment": sentiment_result["sentiment"],
            "sentiment_score": sentiment_result["sentiment_score"],
            "categories": sentiment_result["categories"],
            "entities": entities,
            "nlp_processed_at": datetime.now().isoformat(),
        }

    def process_batch(self, df: pl.DataFrame) -> pl.DataFrame:
        """Process a batch of articles."""
        logger.info(f"Processing batch of {len(df)} articles...")

        results = []
        for row in tqdm(df.iter_rows(named=True), total=len(df)):
            # CRITICAL: Use content column, but fallback to title+description if content is empty
            content = row.get("content", "")
            title = row.get("title", "")
            description = row.get("description", "")

            # If content is empty or too short, combine title + description
            if not content or len(content.strip()) < 50:
                logger.warning(
                    f"⚠️  Article has empty/short content (len={len(content) if content else 0})"
                )
                logger.warning(f"   Title: {title[:100]}")
                # Combine title and description as fallback
                content = f"{title}\n\n{description}".strip()
                if len(content) < 50:
                    logger.warning(
                        f"   ⚠️  Combined title+description still too short, skipping article"
                    )
                    # Skip this article - can't analyze without content
                    results.append(
                        {
                            "sentiment": "neutral",
                            "sentiment_score": 0.0,
                            "categories": ["Other"],
                            "entities": {
                                "persons": [],
                                "locations": [],
                                "organizations": [],
                            },
                            "nlp_processed_at": datetime.now().isoformat(),
                        }
                    )
                    continue

            country = row.get("country", "")

            result = self.process_article(content, country)
            results.append(result)

        # Add results as new columns
        df = df.with_columns(
            [
                pl.Series("sentiment", [r["sentiment"] for r in results]),
                pl.Series("sentiment_score", [r["sentiment_score"] for r in results]),
                pl.Series("categories", [json.dumps(r["categories"]) for r in results]),
                pl.Series(
                    "entities_json", [json.dumps(r["entities"]) for r in results]
                ),
                pl.Series("nlp_processed_at", [r["nlp_processed_at"] for r in results]),
            ]
        )

        return df


def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(description="NAMO NLP Processing Pipeline")
    parser.add_argument(
        "--input", type=str, required=True, help="Input parquet file from preprocessing"
    )
    parser.add_argument("--output", type=str, help="Output parquet file")
    parser.add_argument(
        "--batch-size", type=int, default=8, help="Batch size for processing"
    )
    parser.add_argument(
        "--no-quantization",
        action="store_true",
        help="Disable model quantization (default: quantization disabled for better JSON output)",
    )
    parser.add_argument(
        "--use-quantization",
        action="store_true",
        help="Enable 4-bit quantization (saves GPU memory but may affect JSON output quality)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="mistralai/Mistral-7B-Instruct-v0.2",
        help="LLM model to use. Options: mistralai/Mistral-7B-Instruct-v0.2 (default), Qwen/Qwen2.5-7B-Instruct, meta-llama/Llama-3-8B-Instruct",
    )

    args = parser.parse_args()

    # Load preprocessed data
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return

    logger.info(f"Loading data from {input_path}")
    df = pl.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} articles")

    # Initialize NLP processor
    # Default: no quantization (better JSON output quality)
    # Use --use-quantization to enable if GPU memory is limited
    processor = NLPProcessor(
        model_name=args.model,
        use_quantization=args.use_quantization,  # Only enable if explicitly requested with --use-quantization
        batch_size=args.batch_size,
    )

    # Process
    df_enriched = processor.process_batch(df)

    # Save
    output_path = (
        Path(args.output)
        if args.output
        else OUTPUT_DIR / f"nlp_enriched_{input_path.stem}.parquet"
    )
    df_enriched.write_parquet(output_path)
    logger.info(f"NLP enriched data saved: {output_path}")

    # Show sample
    print("\n" + "=" * 80)
    print("Sample of NLP enriched data:")
    print("=" * 80)
    print(
        df_enriched.select(["title", "sentiment", "categories", "entities_json"]).head(
            3
        )
    )


if __name__ == "__main__":
    main()
