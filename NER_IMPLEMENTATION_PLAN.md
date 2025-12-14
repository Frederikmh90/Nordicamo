# NER Implementation Plan - Country-Specific Models

## Overview

Update Named Entity Recognition to use country-specific transformer models instead of spaCy's multilingual model. This will significantly improve accuracy for Nordic languages.

## Current State

- **Current approach**: Uses spaCy's `xx_ent_wiki_sm` (multilingual, generic)
- **Issues**: Poor performance on Nordic languages, especially Finnish
- **Reference**: Danish NER worked well with `saattrupdan/nbailab-base-ner-scandi`

## Recommended Models by Country

### Danish 🇩🇰
- **Primary**: `Maltehb/danish-bert-botxo-ner-dane` (Danish-specific, proven)
- **Alternative**: `saattrupdan/nbailab-base-ner-scandi` (Scandinavian, works for DK/SE/NO)

### Swedish 🇸🇪
- **Primary**: `saattrupdan/nbailab-base-ner-scandi` (Scandinavian, covers Swedish)
- **Alternative**: `KB/bert-base-swedish-cased-ner` (if available)

### Norwegian 🇳🇴
- **Primary**: `saattrupdan/nbailab-base-ner-scandi` (Scandinavian, covers Norwegian)
- **Alternative**: `ltgoslo/norbert2-ner` (if available)

### Finnish 🇫🇮
- **Primary**: `turkunlp/bert-base-finnish-ner` or `TurkuNLP/bert-base-finnish-cased-v1`
- **Alternative**: `xlm-roberta-base` (multilingual, better than spaCy for Finnish)

## Implementation Strategy

### Phase 1: Model Research & Selection ✅
- [x] Research available Nordic NER models
- [x] Identify best models per country
- [ ] Test models on sample data

### Phase 2: Script Development
- [ ] Create `34_ner_country_specific.py` script
- [ ] Implement country-based model loading
- [ ] Add batch processing for efficiency
- [ ] Handle model fallbacks (if primary model fails)

### Phase 3: Database Integration
- [ ] Update entity extraction format
- [ ] Add sentiment to entities (if needed)
- [ ] Create database loading script
- [ ] Update existing articles

### Phase 4: Testing & Deployment
- [ ] Test on sample data per country
- [ ] Run on full dataset (server)
- [ ] Verify database updates
- [ ] Update frontend visualizations

## Technical Details

### Model Loading Strategy
```python
MODELS_BY_COUNTRY = {
    "denmark": "Maltehb/danish-bert-botxo-ner-dane",
    "sweden": "saattrupdan/nbailab-base-ner-scandi",
    "norway": "saattrupdan/nbailab-base-ner-scandi",
    "finland": "turkunlp/bert-base-finnish-ner",  # or alternative
}
```

### Entity Format
```json
{
  "persons": [
    {"name": "Entity Name", "sentiment": "positive|negative|neutral"}
  ],
  "locations": [...],
  "organizations": [...]
}
```

### Performance Considerations
- Load models once per country (not per article)
- Batch processing for efficiency
- GPU acceleration on server
- Truncate long texts (max 512 tokens)

## Next Steps

1. Research and verify model availability
2. Create implementation script
3. Test on sample data
4. Deploy to server
5. Run on full dataset

