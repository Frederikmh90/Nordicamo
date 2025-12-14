#!/usr/bin/env python3
"""
vLLM-based NLP Processor using Mistral-Small-3.1-24B
Optimized for high-throughput category classification and sentiment analysis
"""

import json
import logging
from typing import List, Dict, Optional
from datetime import datetime
import spacy
from vllm import LLM
from vllm.sampling_params import SamplingParams

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# News categories (same as before)
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


class VLLMNLPProcessor:
    """High-performance NLP processor using vLLM."""
    
    def __init__(
        self,
        model_name: str = "mistralai/Mistral-Small-3.1-24B-Instruct-2503",
        tensor_parallel_size: int = 1,
        max_model_len: int = 8192,
    ):
        self.model_name = model_name
        
        logger.info(f"Loading {model_name} with vLLM...")
        logger.info(f"Tensor parallel size: {tensor_parallel_size}")
        
        # Initialize vLLM with V0 engine (more stable for H100)
        self.llm = LLM(
            model=model_name,
            tokenizer_mode="mistral",
            tensor_parallel_size=tensor_parallel_size,
            max_model_len=max_model_len,
            trust_remote_code=True,
            dtype="bfloat16",
            disable_log_stats=True,
            enforce_eager=False,
            gpu_memory_utilization=0.90,
        )
        
        # Sampling parameters optimized for JSON output
        self.sampling_params = SamplingParams(
            temperature=0.15,  # Low temp for consistent JSON
            max_tokens=150,    # Reduced for speed
            top_p=0.95,
        )
        
        logger.info("✓ vLLM model loaded")
        
        # Initialize spaCy for NER (same as before)
        logger.info("Loading spaCy for NER...")
        try:
            self.nlp_multi = spacy.load("xx_ent_wiki_sm")
            logger.info("✓ spaCy multilingual model loaded")
        except:
            logger.warning("spaCy model not found, NER will be disabled")
            self.nlp_multi = None
    
    def build_category_prompt(self, text: str) -> str:
        """Build prompt for category classification and sentiment analysis."""
        
        # Truncate text to first 500 words
        words = text.split()[:500]
        text_truncated = ' '.join(words)
        
        categories_str = ", ".join(f'"{cat}"' for cat in NEWS_CATEGORIES)
        
        prompt = f"""You are analyzing a Nordic alternative news article for categorization and sentiment.

Article text (first 500 words):
{text_truncated}

Available categories:
{categories_str}

Your task: Analyze the article and respond with ONLY a JSON object in this exact format:
{{
  "sentiment": "positive" OR "negative" OR "neutral",
  "categories": ["category1", "category2"]
}}

Rules:
1. Choose 1-3 categories that best describe the article's main topics
2. Categories MUST be from the available list exactly as written
3. sentiment must be: positive, negative, or neutral
4. Respond with ONLY the JSON object, no other text

JSON:"""
        
        return prompt
    
    def parse_json_response(self, response: str) -> Optional[Dict]:
        """Parse JSON from LLM response."""
        # Clean response
        response = response.strip()
        
        # Remove markdown code blocks if present
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        
        # Extract JSON object
        start = response.find('{')
        end = response.rfind('}')
        if start != -1 and end != -1:
            json_str = response[start:end+1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse error: {e}")
                return None
        return None
    
    def validate_categories(self, categories: List[str]) -> List[str]:
        """Validate and filter categories."""
        valid = []
        for cat in categories:
            if cat in NEWS_CATEGORIES:
                valid.append(cat)
            else:
                # Try fuzzy matching
                cat_lower = cat.lower()
                for valid_cat in NEWS_CATEGORIES:
                    if valid_cat.lower() in cat_lower or cat_lower in valid_cat.lower():
                        valid.append(valid_cat)
                        break
        
        # If no valid categories, assign "Other"
        if not valid:
            valid = ["Other"]
        
        return valid[:3]  # Max 3 categories
    
    def analyze_batch(self, texts: List[str]) -> List[Dict]:
        """Analyze a batch of articles for sentiment and categories."""
        
        # Build prompts for all texts
        prompts = [self.build_category_prompt(text) for text in texts]
        
        # Format as chat messages for Mistral
        messages_batch = []
        for prompt in prompts:
            messages = [
                {
                    "role": "system",
                    "content": "You are a JSON-only analyzer for news categorization. Always respond with valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            messages_batch.append(messages)
        
        # Run inference on batch
        logger.debug(f"Running vLLM inference on batch of {len(texts)} articles...")
        outputs = self.llm.chat(messages_batch, sampling_params=self.sampling_params)
        
        # Parse results
        results = []
        for i, output in enumerate(outputs):
            response_text = output.outputs[0].text
            
            # Parse JSON
            parsed = self.parse_json_response(response_text)
            
            if parsed and 'sentiment' in parsed and 'categories' in parsed:
                sentiment = parsed['sentiment']
                categories = self.validate_categories(parsed['categories'])
                
                # Map sentiment to score
                sentiment_scores = {
                    'positive': 1.0,
                    'neutral': 0.0,
                    'negative': -1.0
                }
                
                results.append({
                    'sentiment': sentiment,
                    'sentiment_score': sentiment_scores.get(sentiment, 0.0),
                    'categories': categories
                })
                logger.debug(f"Article {i}: {sentiment}, {categories}")
            else:
                # Fallback
                logger.warning(f"Article {i}: Failed to parse, using fallback")
                results.append({
                    'sentiment': 'neutral',
                    'sentiment_score': 0.0,
                    'categories': ['Other']
                })
        
        return results
    
    def extract_entities(self, text: str) -> Dict:
        """Extract named entities using spaCy (same as before)."""
        if not self.nlp_multi or not text:
            return {"persons": [], "locations": [], "organizations": []}
        
        try:
            # Truncate for performance
            words = text.split()[:500]
            text_truncated = ' '.join(words)
            
            doc = self.nlp_multi(text_truncated)
            
            persons = []
            locations = []
            organizations = []
            
            for ent in doc.ents:
                entity_data = {"name": ent.text}
                
                if ent.label_ in ["PER", "PERSON"]:
                    persons.append(entity_data)
                elif ent.label_ in ["LOC", "GPE"]:
                    locations.append(entity_data)
                elif ent.label_ == "ORG":
                    organizations.append(entity_data)
            
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
            logger.error(f"Error in entity extraction: {e}")
            return {"persons": [], "locations": [], "organizations": []}
    
    def process_articles_batch(self, articles: List[Dict]) -> List[Dict]:
        """Process a batch of articles with all NLP tasks."""
        
        # Extract texts
        texts = []
        for article in articles:
            text = article.get('content', '') or article.get('description', '') or ''
            texts.append(text)
        
        # Analyze sentiment and categories in batch
        nlp_results = self.analyze_batch(texts)
        
        # Extract entities and combine results
        enriched_articles = []
        for i, article in enumerate(articles):
            entities = self.extract_entities(texts[i])
            
            result = {
                **article,  # Keep original article data
                'sentiment': nlp_results[i]['sentiment'],
                'sentiment_score': nlp_results[i]['sentiment_score'],
                'categories': nlp_results[i]['categories'],
                'entities': entities,
                'nlp_processed_at': datetime.now().isoformat()
            }
            enriched_articles.append(result)
        
        return enriched_articles


if __name__ == "__main__":
    # Quick test
    processor = VLLMNLPProcessor()
    
    test_texts = [
        "The government announced new immigration policies today affecting asylum seekers.",
        "Scientists discovered a new treatment for cancer in clinical trials.",
        "The economy showed strong growth with unemployment falling to record lows."
    ]
    
    test_articles = [{'content': text, 'url': f'test_{i}'} for i, text in enumerate(test_texts)]
    
    results = processor.process_articles_batch(test_articles)
    
    for r in results:
        print(f"\nText: {r['content'][:80]}...")
        print(f"Sentiment: {r['sentiment']}")
        print(f"Categories: {r['categories']}")
        print(f"Entities: {r['entities']}")

