#!/usr/bin/env python3
"""
NAMO Category Classification Only
==================================
Simplified NLP processing: Only classifies articles into ONE primary category.
No sentiment analysis, no NER, just category classification.

Uses local LLM (Hugging Face Transformers) for free processing.
Now with function calling support for Mistral v0.3!
"""

import polars as pl
import json
import os
from pathlib import Path
from typing import Dict, Optional, List
from tqdm import tqdm
import logging
from datetime import datetime
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import re

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "data" / "nlp_enriched"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# News categories (10 categories + "Other")
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

# Category mapping: Common variations -> Exact category names
CATEGORY_MAPPING = {
    # Economy & Labor variations
    "labor & economy": "Economy & Labor",
    "labor and economy": "Economy & Labor",
    "economy and labor": "Economy & Labor",
    "business & economy": "Economy & Labor",
    "business and economy": "Economy & Labor",
    "economy": "Economy & Labor",
    "labor": "Economy & Labor",
    "labor & union": "Economy & Labor",
    "labor and union": "Economy & Labor",
    "financial": "Economy & Labor",
    "business": "Economy & Labor",
    
    # Social Issues & Culture variations
    "social issues and culture": "Social Issues & Culture",
    "social issues & culture": "Social Issues & Culture",
    "culture": "Social Issues & Culture",
    "arts & culture": "Social Issues & Culture",
    "arts and culture": "Social Issues & Culture",
    "social issues": "Social Issues & Culture",
    
    # Environment, Climate & Energy variations
    "environment, climate and energy": "Environment, Climate & Energy",
    "environment climate energy": "Environment, Climate & Energy",
    "climate & environment": "Environment, Climate & Energy",
    "climate and environment": "Environment, Climate & Energy",
    "energy, climate & environment": "Environment, Climate & Energy",
    "energy climate environment": "Environment, Climate & Energy",
    "environment": "Environment, Climate & Energy",
    "climate": "Environment, Climate & Energy",
    "energy": "Environment, Climate & Energy",
    
    # Technology, Science & Digital Society variations
    "technology science digital society": "Technology, Science & Digital Society",
    "technology, science and digital society": "Technology, Science & Digital Society",
    "technology & science": "Technology, Science & Digital Society",
    "technology and science": "Technology, Science & Digital Society",
    "technology": "Technology, Science & Digital Society",
    "science": "Technology, Science & Digital Society",
    "digital": "Technology, Science & Digital Society",
    
    # Politics & Governance variations
    "politics and governance": "Politics & Governance",
    "politics": "Politics & Governance",
    "governance": "Politics & Governance",
    "political": "Politics & Governance",
    
    # Health & Medicine variations
    "health and medicine": "Health & Medicine",
    "health": "Health & Medicine",
    "medicine": "Health & Medicine",
    "medical": "Health & Medicine",
    
    # Immigration & National Identity variations
    "immigration and national identity": "Immigration & National Identity",
    "immigration": "Immigration & National Identity",
    "national identity": "Immigration & National Identity",
    
    # Media & Censorship variations
    "media and censorship": "Media & Censorship",
    "media": "Media & Censorship",
    "censorship": "Media & Censorship",
    
    # International Relations & Conflict variations
    "international relations and conflict": "International Relations & Conflict",
    "international relations": "International Relations & Conflict",
    "conflict": "International Relations & Conflict",
    "war": "International Relations & Conflict",
    "geopolitics": "International Relations & Conflict",
    
    # Crime & Justice variations
    "crime and justice": "Crime & Justice",
    "crime": "Crime & Justice",
    "justice": "Crime & Justice",
    "legal": "Crime & Justice",
    
    # Other invalid categories that should map to existing ones
    "education & learning": "Social Issues & Culture",
    "education": "Social Issues & Culture",
    "religion & spirituality": "Social Issues & Culture",
    "religion": "Social Issues & Culture",
    "philosophy & ideologies": "Social Issues & Culture",
    "philosophy": "Social Issues & Culture",
}


class CategoryClassifier:
    """Simple category classifier using local LLM with function calling support."""

    def __init__(
        self,
        model_name: str = "mistralai/Mistral-7B-Instruct-v0.3",  # Default: Mistral v0.3 (latest, improved vocabulary & function calling)
        device: str = "cuda",
        use_quantization: bool = False,
        hf_token: Optional[str] = None,
        use_function_calling: bool = True,  # Use function calling for structured output
    ):
        self.model_name = model_name
        self.device = device if torch.cuda.is_available() else "cpu"
        self.use_quantization = use_quantization
        self.max_length = 2048
        self.hf_token = hf_token or os.getenv("HF_TOKEN")
        self.use_function_calling = use_function_calling and "mistral" in model_name.lower() and "v0.3" in model_name.lower()

        logger.info(f"Loading model: {model_name}")
        logger.info(f"Device: {self.device}")
        logger.info(f"Quantization: {use_quantization}")
        logger.info(f"Function calling: {self.use_function_calling}")
        if self.hf_token:
            logger.info("Using Hugging Face token for authentication")

        # Prepare tokenizer kwargs
        tokenizer_kwargs = {"trust_remote_code": True}
        if self.hf_token:
            tokenizer_kwargs["token"] = self.hf_token

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name, **tokenizer_kwargs
        )

        # Set pad token if not set
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Prepare model kwargs
        model_kwargs = {"trust_remote_code": True}
        if self.hf_token:
            model_kwargs["token"] = self.hf_token

        # Load model
        if self.use_quantization and self.device == "cuda":
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
            )
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                quantization_config=quantization_config,
                device_map="auto",
                dtype=torch.float16,
                **model_kwargs,
            )
        else:
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None,
                **model_kwargs,
            )

        logger.info("Model loaded successfully")

    def truncate_text(self, text: str, max_words: int = 500) -> str:
        """Truncate text to max_words."""
        words = text.split()
        if len(words) > max_words:
            return " ".join(words[:max_words]) + "..."
        return text

    def _get_function_calling_tools(self) -> List[Dict]:
        """Define function calling tools for structured output."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "classify_article",
                    "description": "Classify a news article into exactly one category from the predefined list.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "enum": NEWS_CATEGORIES,
                                "description": "The exact category name from the predefined list. Must match exactly - no variations.",
                            },
                            "reasoning": {
                                "type": "string",
                                "description": "Brief explanation (1-2 sentences) for why this category was chosen.",
                            },
                        },
                        "required": ["category", "reasoning"],
                    },
                },
            }
        ]

    def _get_prompt_for_language(self, language: str, use_multilingual: bool = False) -> str:
        """Get prompt in the appropriate language."""
        # For Mistral, English prompts work better, but we can use multilingual if needed
        # Note: Finnish may need special handling due to language family differences
        if not use_multilingual:
            lang = "english"
        else:
            # Map country to language
            lang_map = {
                "denmark": "danish",
                "sweden": "swedish", 
                "norway": "norwegian",
                "finland": "finnish",
            }
            lang = lang_map.get(language.lower(), "english")
        
        categories_list = "\n".join([f"{i+1}. {cat}" for i, cat in enumerate(NEWS_CATEGORIES)])
        
        prompts = {
            "danish": f"""Du er en nyhedsartikelklassificerer. Din opgave er at klassificere artiklen i PRÆCIS ÉN kategori.

GYLDIGE KATEGORIER (DU SKAL BRUGE ÉN AF DISSE PRÆCISE NAVNE - INGEN VARIATIONER):
{categories_list}

KRITISKE INSTRUKTIONER:
1. Læs artiklen nedenfor
2. Vælg DEN ENKELTE mest relevante kategori fra listen ovenfor
3. Du SKAL bruge det PRÆCISE kategorinavn som skrevet ovenfor - opfind IKKE nye navne eller brug variationer
4. Hvis indhold handler om arbejde/økonomi, brug "Economy & Labor" (IKKE "Labor & Economy" eller "Business & Economy")
5. Hvis indhold handler om kultur/sociale spørgsmål, brug "Social Issues & Culture" (IKKE "Culture" eller "Arts & Culture")
6. Hvis indhold handler om miljø/klima, brug "Environment, Climate & Energy" (IKKE "Climate & Environment")
7. TVING indholdet ind i en af de 10 kategorier ovenfor - opret IKKE nye kategorier
8. Svar med KUN et JSON-objekt - intet andet!

PÅKRÆVET JSON-FORMAT (kopier dette præcist):
{{"category": "PRÆCIST KATEGORINAVN FRA LISTEN", "reasoning": "kort forklaring"}}

KRITISKE REGLER:
- Dit svar SKAL starte med {{ og slutte med }}
- Skriv IKKE bare kategorinavnet
- Skriv IKKE tekst før eller efter JSON
- Vælg KUN ÉN kategori (den mest relevante)
- Brug det PRÆCISE kategorinavn fra listen - INGEN variationer, INGEN forkortelser, INGEN nye navne
- Brug "Other" KUN hvis artiklen virkelig ikke passer til nogen anden kategori

Eksempel på korrekt svar:
{{"category": "Politics & Governance", "reasoning": "Artikel omhandler regeringspolitik"}}""",
            
            "swedish": f"""Du är en nyhetsartikelklassificerare. Din uppgift är att klassificera artikeln i EXAKT EN kategori.

GYLDIGA KATEGORIER (DU MÅSTE ANVÄNDA ETT AV DESSA EXAKTA NAMN - INGA VARIATIONER):
{categories_list}

KRITISKA INSTRUKTIONER:
1. Läs artikeln nedan
2. Välj DEN ENSTA mest relevanta kategorin från listan ovan
3. Du MÅSTE använda det EXAKTA kategorinamnet som skrivet ovan - uppfinn INTE nya namn eller använd variationer
4. Om innehållet handlar om arbete/ekonomi, använd "Economy & Labor" (INTE "Labor & Economy" eller "Business & Economy")
5. Om innehållet handlar om kultur/sociala frågor, använd "Social Issues & Culture" (INTE "Culture" eller "Arts & Culture")
6. Om innehållet handlar om miljö/klimat, använd "Environment, Climate & Energy" (INTE "Climate & Environment")
7. TVINGA innehållet in i en av de 10 kategorierna ovan - skapa INTE nya kategorier
8. Svara med ENDAST ett JSON-objekt - inget annat!

KRÄVD JSON-FORMAT (kopiera detta exakt):
{{"category": "EXAKT KATEGORINAMN FRÅN LISTAN", "reasoning": "kort förklaring"}}

KRITISKA REGLER:
- Ditt svar MÅSTE börja med {{ och sluta med }}
- Skriv INTE bara kategorinamnet
- Skriv INTE text före eller efter JSON
- Välj ENDAST EN kategori (den mest relevanta)
- Använd det EXAKTA kategorinamnet från listan - INGA variationer, INGA förkortningar, INGA nya namn
- Använd "Other" ENDAST om artikeln verkligen inte passar i någon annan kategori

Exempel på korrekt svar:
{{"category": "Politics & Governance", "reasoning": "Artikel diskuterar regeringspolitik"}}""",
            
            "norwegian": f"""Du er en nyhetsartikkelklassifiserer. Din oppgave er å klassifisere artikkelen i NØYAKTIG ÉN kategori.

GYLDIGE KATEGORIER (DU MÅ BRUKE ÉN AV DISSE PRESISE NAVNENE - INGEN VARIASJONER):
{categories_list}

KRITISKE INSTRUKSJONER:
1. Les artikkelen nedenfor
2. Velg DEN ENESTE mest relevante kategorien fra listen ovenfor
3. Du MÅ bruke det PRESISE kategorinavnet som skrevet ovenfor - oppfinn IKKE nye navn eller bruk variasjoner
4. Hvis innhold handler om arbeid/økonomi, bruk "Economy & Labor" (IKKE "Labor & Economy" eller "Business & Economy")
5. Hvis innhold handler om kultur/sosiale spørsmål, bruk "Social Issues & Culture" (IKKE "Culture" eller "Arts & Culture")
6. Hvis innhold handler om miljø/klima, bruk "Environment, Climate & Energy" (IKKE "Climate & Environment")
7. TVING innholdet inn i en av de 10 kategoriene ovenfor - opprett IKKE nye kategorier
8. Svar med KUN et JSON-objekt - ingenting annet!

PÅKREVD JSON-FORMAT (kopier dette nøyaktig):
{{"category": "PRESIST KATEGORINAVN FRA LISTEN", "reasoning": "kort forklaring"}}

KRITISKE REGLER:
- Ditt svar MÅ starte med {{ og slutte med }}
- Skriv IKKE bare kategorinavnet
- Skriv IKKE tekst før eller etter JSON
- Velg KUN ÉN kategori (den mest relevante)
- Bruk det PRESISE kategorinavnet fra listen - INGEN variasjoner, INGEN forkortelser, INGEN nye navn
- Bruk "Other" KUN hvis artikkelen virkelig ikke passer i noen annen kategori

Eksempel på korrekt svar:
{{"category": "Politics & Governance", "reasoning": "Artikkel diskuterer regjeringspolitikk"}}""",
            
            "finnish": f"""Olet uutisartikkel-luokittelija. Tehtäväsi on luokitella artikkeli TARKALLEEN YHTEEN kategoriaan.

KELPOISET KATEGORIAT (SINUN TÄYTYY KÄYTTÄÄ YHTÄ NÄISTÄ TARKISTA NIMISTÄ - EI MUUNNELMIA):
{categories_list}

KRITISET OHJEET:
1. Lue artikkeli alla
2. Valitse YKSI tärkein kategoria yllä olevasta listasta
3. Sinun TÄYTYY käyttää TARKASTA kategorian nimeä kuten yllä kirjoitettu - ÄLÄ keksi uusia nimiä tai käytä muunnelmia
4. Jos sisältö koskee työtä/taloutta, käytä "Economy & Labor" (EI "Labor & Economy" tai "Business & Economy")
5. Jos sisältö koskee kulttuuria/sosiaalisia kysymyksiä, käytä "Social Issues & Culture" (EI "Culture" tai "Arts & Culture")
6. Jos sisältö koskee ympäristöä/ilmastoa, käytä "Environment, Climate & Energy" (EI "Climate & Environment")
7. PAKOTA sisältö yhteen 10 kategoriasta yllä - ÄLÄ luo uusia kategorioita
8. Vastaa VAIN JSON-objektilla - ei muuta!

HUOMIO SUOMELLE: Jos artikkeli on suomeksi, analysoi sisältö huolellisesti. Suomalaiset artikkelit voivat käsitellä samoja aiheita kuin muut pohjoismaiset artikkelit, mutta käyttävät eri kieltä. Valitse kategoria sisällön perusteella, ei kielen perusteella.

VAADITTU JSON-MUOTO (kopioi tämä tarkalleen):
{{"category": "TARKKA KATEGORIAN NIMI LISTASTA", "reasoning": "lyhyt selitys"}}

KRITISET SÄÄNNÖT:
- Vastauksesi TÄYTYY alkaa {{ ja päättyä }}
- ÄLÄ kirjoita vain kategorian nimeä
- ÄLÄ kirjoita tekstiä ennen tai jälkeen JSON
- Valitse VAIN YKSI kategoria (tärkein)
- Käytä TARKASTA kategorian nimeä listasta - EI muunnelmia, EI lyhenteitä, EI uusia nimiä
- Käytä "Other" VAIN jos artikkeli todella ei sovi mihinkään muuhun kategoriaan

Esimerkki oikeasta vastauksesta:
{{"category": "Politics & Governance", "reasoning": "Artikkelissa käsitellään hallituksen politiikkaa"}}""",
            
            "english": f"""You are a news article classifier. Your task is to classify the article into EXACTLY ONE category.

VALID CATEGORIES (YOU MUST USE ONE OF THESE EXACT NAMES - NO VARIATIONS):
{categories_list}

CRITICAL INSTRUCTIONS:
1. Read the article below
2. Choose the SINGLE most relevant category from the list above
3. You MUST use the EXACT category name as written above - do NOT invent new names or use variations
4. If content is about labor/economy, use "Economy & Labor" (NOT "Labor & Economy" or "Business & Economy")
5. If content is about culture/social issues, use "Social Issues & Culture" (NOT "Culture" or "Arts & Culture")
6. If content is about environment/climate, use "Environment, Climate & Energy" (NOT "Climate & Environment")
7. FORCE the content into one of the 10 categories above - do NOT create new categories
8. Respond with ONLY a JSON object - nothing else!

REQUIRED JSON FORMAT (copy this exactly):
{{"category": "EXACT CATEGORY NAME FROM LIST", "reasoning": "brief explanation"}}

CRITICAL RULES:
- Your response MUST start with {{ and end with }}
- Do NOT write just the category name
- Do NOT write any text before or after the JSON
- Choose ONLY ONE category (the most relevant)
- Use the EXACT category name from the list - NO variations, NO abbreviations, NO new names
- Use "Other" ONLY if the article truly doesn't fit any of the 10 categories above

Example of correct response:
{{"category": "Politics & Governance", "reasoning": "Article discusses government policy"}}""",
        }
        
        return prompts.get(lang, prompts["english"])

    def classify_category(self, text: str, country: str = "") -> Dict:
        """
        Classify article into ONE primary category.
        Returns: {"category": "Category Name", "reasoning": "brief explanation"}
        """
        # Truncate text
        text_truncated = self.truncate_text(text, max_words=500)

        # Get prompt - use English for Mistral (works better), multilingual for others
        # Special note: Finnish may need English prompts due to language family differences
        use_multilingual = "viking" in self.model_name.lower() or "eurollm" in self.model_name.lower()
        
        # For Finnish articles, consider using English prompt (Mistral may handle English better)
        if country.lower() == "finland" and "mistral" in self.model_name.lower():
            prompt_template = self._get_prompt_for_language("english", use_multilingual=False)
            logger.debug("Using English prompt for Finnish article (better Mistral compatibility)")
        else:
            prompt_template = self._get_prompt_for_language(country, use_multilingual=use_multilingual)
        
        # Add article to prompt
        prompt = f"""{prompt_template}

Article:
{text_truncated}

Now classify this article. Respond with ONLY the JSON object:"""

        # Format prompt based on model - try to use model's chat template with function calling
        model_lower = self.model_name.lower()
        
        # Check if tokenizer has a chat template
        if hasattr(self.tokenizer, "apply_chat_template") and self.tokenizer.chat_template is not None:
            # Use model's official chat template
            try:
                messages = [
                    {
                        "role": "system",
                        "content": "You are a JSON-only classifier. Always respond with valid JSON. Never continue article text.",
                    },
                    {"role": "user", "content": prompt},
                ]
                
                # Add function calling tools if supported
                if self.use_function_calling:
                    tools = self._get_function_calling_tools()
                    # Try to add tools to messages (format depends on model)
                    # For Mistral v0.3, tools might be added as a separate parameter
                    # Check if apply_chat_template supports tools parameter
                    try:
                        text_input = self.tokenizer.apply_chat_template(
                            messages, 
                            tools=tools,
                            tool_choice={"type": "function", "function": {"name": "classify_article"}},
                            tokenize=False, 
                            add_generation_prompt=True
                        )
                        logger.debug("Using function calling with Mistral v0.3")
                    except TypeError:
                        # Fallback: tools parameter not supported, use regular template
                        text_input = self.tokenizer.apply_chat_template(
                            messages, tokenize=False, add_generation_prompt=True
                        )
                        logger.debug("Function calling not supported in chat template, using regular template")
                else:
                    text_input = self.tokenizer.apply_chat_template(
                        messages, tokenize=False, add_generation_prompt=True
                    )
                    logger.debug(f"Using model's chat template for {self.model_name}")
            except Exception as e:
                logger.warning(f"Failed to use chat template: {e}, falling back to direct prompt")
                text_input = prompt
        elif "mistral" in model_lower:
            # Use Mistral's chat template
            messages = [
                {
                    "role": "system",
                    "content": "You are a JSON-only classifier. Always respond with valid JSON. Never continue article text.",
                },
                {"role": "user", "content": prompt},
            ]
            text_input = self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
        elif "qwen" in model_lower or "viking" in model_lower or "eurollm" in model_lower:
            # ChatML format for Qwen/Viking/EuroLLM models
            text_input = (
                "<|im_start|>system\nYou are a JSON-only classifier. "
                "Always respond with valid JSON. Never continue article text.\n<|im_end|>\n"
                f"<|im_start|>user\n{prompt}\n<|im_end|>\n<|im_start|>assistant\n"
            )
        else:
            text_input = prompt

        # Tokenize
        inputs = self.tokenizer(
            text_input,
            return_tensors="pt",
            truncation=True,
            max_length=self.max_length,
        ).to(self.device)

        # Generate
        with torch.no_grad():
            # Ensure we have proper pad_token_id
            pad_token_id = self.tokenizer.pad_token_id
            if pad_token_id is None:
                pad_token_id = self.tokenizer.eos_token_id
            
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=200,  # Increased slightly
                do_sample=False,  # Greedy decoding for deterministic output
                pad_token_id=pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                repetition_penalty=1.1,
                # Note: temperature is not valid when do_sample=False
            )

        # Decode response
        generated_tokens = outputs[0][inputs["input_ids"].shape[1] :]
        response = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
        
        # Debug: Log response if empty or very short
        if not response or len(response.strip()) < 10:
            logger.debug(f"⚠️  Empty or very short response (length: {len(response)}). "
                        f"Generated tokens: {len(generated_tokens)}, "
                        f"Model: {self.model_name}")
            # Try decoding without skipping special tokens to see what we got
            response_raw = self.tokenizer.decode(generated_tokens, skip_special_tokens=False)
            logger.debug(f"Raw response (with special tokens): {response_raw[:200]}")

        # Extract JSON (handle function calling format if present)
        result = self._extract_json(response)
        
        # If function calling was used, extract from function call format
        if not result and self.use_function_calling:
            result = self._extract_from_function_call(response)
        
        if result:
            # Normalize and validate category
            category = result.get("category", "")
            category_normalized = self._normalize_category(category)
            
            if category_normalized != category:
                logger.debug(f"🔄 Normalized category '{category}' -> '{category_normalized}'")
            
            if category_normalized not in NEWS_CATEGORIES:
                logger.warning(f"⚠️  Invalid category '{category}' (normalized: '{category_normalized}'), assigning 'Other'")
                category_normalized = "Other"
            
            category = category_normalized
            
            return {
                "category": category,
                "reasoning": result.get("reasoning", ""),
                "nlp_processed_at": datetime.now().isoformat(),
            }
        else:
            # Fallback: Try to extract category name from text response
            category = self._extract_category_from_text(response)
            if category:
                logger.debug(f"✅ Extracted category from text: {category}")
                return {
                    "category": category,
                    "reasoning": f"Extracted from text response: {response[:100]}",
                    "nlp_processed_at": datetime.now().isoformat(),
                }
            else:
                logger.warning(f"⚠️  Failed to parse JSON or extract category. Response: {response[:200]}")
                return {
                    "category": "Other",
                    "reasoning": "Failed to parse LLM response",
                    "nlp_processed_at": datetime.now().isoformat(),
                }

    def _extract_from_function_call(self, response: str) -> Optional[Dict]:
        """Extract JSON from function call format."""
        # Function calling might return format like:
        # <function_calls>
        # <invoke name="classify_article">
        # <parameter name="category">Politics & Governance</parameter>
        # <parameter name="reasoning">...</parameter>
        # </invoke>
        # </function_calls>
        
        # Try to extract function call parameters
        pattern = r'<parameter name="category">(.*?)</parameter>'
        category_match = re.search(pattern, response, re.DOTALL)
        
        pattern_reasoning = r'<parameter name="reasoning">(.*?)</parameter>'
        reasoning_match = re.search(pattern_reasoning, response, re.DOTALL)
        
        if category_match:
            category = category_match.group(1).strip()
            reasoning = reasoning_match.group(1).strip() if reasoning_match else ""
            return {"category": category, "reasoning": reasoning}
        
        return None

    def _extract_json(self, response: str) -> Optional[Dict]:
        """Extract JSON from LLM response."""
        # Clean response
        response_clean = response.strip()
        
        # Remove markdown code fences if present
        response_clean = re.sub(r"```json\s*", "", response_clean)
        response_clean = re.sub(r"```\s*", "", response_clean)
        
        # Strategy 1: Find JSON object with balanced braces
        json_match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", response_clean, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except Exception:
                pass
        
        # Strategy 2: First { to last }
        start = response_clean.find("{")
        end = response_clean.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(response_clean[start : end + 1])
            except Exception:
                pass
        
        return None

    def _normalize_category(self, category: str) -> str:
        """Normalize category name using mapping dictionary."""
        if not category:
            return "Other"
        
        category_clean = category.strip()
        
        # Exact match first
        if category_clean in NEWS_CATEGORIES:
            return category_clean
        
        # Check mapping dictionary (case-insensitive)
        category_lower = category_clean.lower()
        if category_lower in CATEGORY_MAPPING:
            mapped = CATEGORY_MAPPING[category_lower]
            logger.debug(f"✅ Mapped '{category_clean}' -> '{mapped}'")
            return mapped
        
        # Try fuzzy matching: check if any valid category is contained in the response
        for valid_category in NEWS_CATEGORIES:
            # Check if response contains the category (case-insensitive)
            if valid_category.lower() in category_lower or category_lower in valid_category.lower():
                logger.debug(f"✅ Fuzzy matched '{category_clean}' -> '{valid_category}'")
                return valid_category
        
        # Try word-by-word matching for multi-word categories
        category_words = set(category_lower.split())
        for valid_category in NEWS_CATEGORIES:
            valid_words = set(valid_category.lower().replace(",", "").replace("&", "").split())
            # If most words match, use this category
            if len(category_words & valid_words) >= min(2, len(valid_words) - 1):
                logger.debug(f"✅ Word-matched '{category_clean}' -> '{valid_category}'")
                return valid_category
        
        return "Other"
    
    def _extract_category_from_text(self, response: str) -> Optional[str]:
        """Extract category name from text response (fallback when JSON parsing fails)."""
        response_clean = response.strip()
        
        # Remove common prefixes
        response_clean = re.sub(r"^(category|Category|CATEGORY):\s*", "", response_clean, flags=re.IGNORECASE)
        response_clean = re.sub(r"^(EXAMPLE|example|Example):\s*", "", response_clean)
        response_clean = re.sub(r"^(RESPONSE|response|Response):\s*", "", response_clean)
        
        # Check if response is exactly a valid category
        if response_clean in NEWS_CATEGORIES:
            return response_clean
        
        # Try normalization (includes fuzzy matching)
        normalized = self._normalize_category(response_clean)
        if normalized != "Other":
            return normalized
        
        # Check if response starts with a valid category
        for category in NEWS_CATEGORIES:
            if response_clean.startswith(category):
                return category
        
        # Check if any category appears in the response (as substring)
        for category in NEWS_CATEGORIES:
            if category.lower() in response_clean.lower():
                return category
        
        return None

    def _save_checkpoint(
        self,
        df: pl.DataFrame,
        results: List[Dict],
        output_path: Path,
    ) -> None:
        """Save incremental results to a single checkpoint file."""
        if not results:
            return
        output_path.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_df = df.head(len(results)).with_columns([
            pl.Series("category", [r["category"] for r in results]),
            pl.Series("category_reasoning", [r["reasoning"] for r in results]),
            pl.Series("category_processed_at", [r["nlp_processed_at"] for r in results]),
        ])
        checkpoint_df.write_parquet(output_path)
        logger.info(f"💾 Checkpoint saved: {len(results)} rows -> {output_path}")

    def process_batch(
        self,
        df: pl.DataFrame,
        second_pass: bool = True,
        checkpoint_size: int = 0,
        checkpoint_output: Optional[Path] = None,
    ) -> pl.DataFrame:
        """Process a batch of articles with optional second pass for 'Other' categories."""
        logger.info(f"Processing {len(df)} articles for category classification")
        
        results = []
        for row in tqdm(df.iter_rows(named=True), total=len(df), desc="First pass"):
            content = row.get("content", "")
            country = row.get("country", "")
            
            # Fallback to title + description if content is empty
            if not content or len(content.strip()) < 50:
                title = row.get("title", "")
                description = row.get("description", "")
                content = f"{title}\n\n{description}".strip()
                
                if len(content) < 50:
                    logger.warning("⚠️  Article has no usable content, assigning 'Other'")
                    results.append({
                        "category": "Other",
                        "reasoning": "No content available",
                        "nlp_processed_at": datetime.now().isoformat(),
                    })
                    continue
            
            result = self.classify_category(content, country=country)
            results.append(result)
            if checkpoint_size and checkpoint_output and len(results) % checkpoint_size == 0:
                self._save_checkpoint(df, results, checkpoint_output)

        # Add results as new columns
        df = df.with_columns([
            pl.Series("category", [r["category"] for r in results]),
            pl.Series("category_reasoning", [r["reasoning"] for r in results]),
            pl.Series("category_processed_at", [r["nlp_processed_at"] for r in results]),
        ])
        if checkpoint_size and checkpoint_output:
            self._save_checkpoint(df, results, checkpoint_output)
        
        # Second pass: Re-process articles with "Other" category
        if second_pass:
            # Get rows with "Other" category
            other_df = df.filter(pl.col("category") == "Other")
            
            if len(other_df) > 0:
                logger.info(f"🔄 Second pass: Re-processing {len(other_df)} articles with 'Other' category")
                
                updated_categories = []
                updated_reasonings = []
                updated_count = 0
                
                for row in tqdm(other_df.iter_rows(named=True), total=len(other_df), desc="Second pass"):
                    content = row.get("content", "")
                    country = row.get("country", "")
                    
                    # Fallback to title + description if content is empty
                    if not content or len(content.strip()) < 50:
                        title = row.get("title", "")
                        description = row.get("description", "")
                        content = f"{title}\n\n{description}".strip()
                    
                    if len(content) >= 50:
                        # Try again
                        result = self.classify_category(content, country=country)
                        
                        # Only update if we got a different category
                        if result["category"] != "Other":
                            updated_categories.append((row.get("url"), result["category"]))
                            updated_reasonings.append((row.get("url"), result["reasoning"]))
                            updated_count += 1
                        else:
                            updated_categories.append((row.get("url"), "Other"))
                            updated_reasonings.append((row.get("url"), row.get("category_reasoning", "")))
                    else:
                        # Keep as Other
                        updated_categories.append((row.get("url"), "Other"))
                        updated_reasonings.append((row.get("url"), row.get("category_reasoning", "")))
                
                # Update dataframe with new categories
                if updated_categories:
                    # Create mapping dictionaries
                    category_map = dict(updated_categories)
                    reasoning_map = dict(updated_reasonings)
                    
                    # Update using url as key - rebuild columns
                    new_categories = [
                        category_map.get(url, cat) 
                        for url, cat in zip(df["url"], df["category"])
                    ]
                    new_reasonings = [
                        reasoning_map.get(url, reason) 
                        for url, reason in zip(df["url"], df["category_reasoning"])
                    ]
                    
                    df = df.with_columns([
                        pl.Series("category", new_categories),
                        pl.Series("category_reasoning", new_reasonings),
                    ])
                    
                    logger.info(f"✅ Second pass updated {updated_count} articles from 'Other' to specific categories")
        
        return df


def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="NAMO Category Classification Only"
    )
    parser.add_argument(
        "--input", type=str, required=True, help="Input parquet file path"
    )
    parser.add_argument(
        "--output", type=str, help="Output parquet file path (optional)"
    )
    parser.add_argument(
        "--checkpoint-size",
        type=int,
        default=0,
        help="Save incremental results every N rows (0 disables)",
    )
    parser.add_argument(
        "--checkpoint-output",
        type=str,
        help="Checkpoint parquet path (defaults to --output)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="mistralai/Mistral-7B-Instruct-v0.3",
        help="Model name from Hugging Face. Default: Mistral-7B-Instruct-v0.3 (latest, improved vocabulary & function calling).",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda",
        choices=["cuda", "cpu"],
        help="Device to use",
    )
    parser.add_argument(
        "--use-quantization",
        action="store_true",
        help="Use 4-bit quantization (saves GPU memory)",
    )
    parser.add_argument(
        "--no-quantization",
        action="store_true",
        help="Disable quantization (default, better quality)",
    )
    parser.add_argument(
        "--hf-token",
        type=str,
        help="Hugging Face token for accessing private/gated models (or set HF_TOKEN env var)",
    )
    parser.add_argument(
        "--no-function-calling",
        action="store_true",
        help="Disable function calling (use regular JSON prompts)",
    )

    args = parser.parse_args()

    # Determine quantization
    use_quantization = args.use_quantization and not args.no_quantization
    use_function_calling = not args.no_function_calling

    # Load data
    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = BASE_DIR / args.input

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return

    logger.info(f"Loading data from {input_path}")
    df = pl.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} articles")

    # Initialize classifier
    classifier = CategoryClassifier(
        model_name=args.model,
        device=args.device,
        use_quantization=use_quantization,
        hf_token=args.hf_token,
        use_function_calling=use_function_calling,
    )

    # Process
    checkpoint_output = None
    if args.checkpoint_size > 0:
        if args.checkpoint_output:
            checkpoint_output = Path(args.checkpoint_output)
        elif args.output:
            checkpoint_output = Path(args.output)

        if checkpoint_output and not checkpoint_output.is_absolute():
            checkpoint_output = OUTPUT_DIR / checkpoint_output
        if checkpoint_output:
            logger.info(f"Checkpointing enabled: every {args.checkpoint_size} rows -> {checkpoint_output}")

    df_enriched = classifier.process_batch(
        df,
        checkpoint_size=args.checkpoint_size,
        checkpoint_output=checkpoint_output,
    )

    # Save
    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = OUTPUT_DIR / args.output
    else:
        output_path = OUTPUT_DIR / f"category_classified_{input_path.stem}.parquet"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_enriched.write_parquet(output_path)
    logger.info(f"✅ Saved {len(df_enriched)} articles to {output_path}")
    
    # Print summary
    category_counts = df_enriched["category"].value_counts().sort("count", descending=True)
    logger.info("\n📊 Category Distribution:")
    for row in category_counts.iter_rows(named=True):
        logger.info(f"  {row['category']}: {row['count']} ({row['count']/len(df_enriched)*100:.1f}%)")


if __name__ == "__main__":
    main()
