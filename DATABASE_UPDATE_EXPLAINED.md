# How Database Update Works - Simple Explanation

## The Flow

```
1. Query Database         2. Process Articles        3. Update Database
   ──────────────            ───────────────            ──────────────
   SELECT articles          Run LLM on each         UPDATE articles
   WHERE nlp_processed      article to get:         SET sentiment = ...
   IS NULL                  - sentiment             SET categories = ...
                          - categories             SET entities_json = ...
                          - entities               SET nlp_processed_at = NOW()
```

## Step-by-Step

### Step 1: Find Unprocessed Articles

The script runs this SQL query:

```sql
SELECT id, url, title, content, country
FROM articles
WHERE (nlp_processed_at IS NULL OR sentiment IS NULL)
  AND content IS NOT NULL
  AND LENGTH(content) > 50
ORDER BY id
LIMIT 50
OFFSET 0
```

**What this does:**
- Finds articles that haven't been processed yet
- Checks: `nlp_processed_at IS NULL` (never processed) OR `sentiment IS NULL` (incomplete)
- Only gets articles with actual content (>50 characters)
- Gets 50 articles at a time (chunk size)

### Step 2: Process Each Article

For each article, the script:
1. Sends article content to Mistral LLM
2. Gets back JSON with:
   ```json
   {
     "sentiment": "negative",
     "categories": ["Crime & Justice", "Politics & Governance"],
     "reasoning": "Article discusses a court case..."
   }
   ```
3. Extracts entities using spaCy (persons, locations, organizations)

### Step 3: Update Database

After processing a chunk (e.g., 50 articles), the script runs this SQL:

```sql
UPDATE articles
SET 
    sentiment = 'negative',
    sentiment_score = -1.0,
    categories = '["Crime & Justice", "Politics & Governance"]'::jsonb,
    entities_json = '{"persons": [...], "locations": [...]}'::jsonb,
    nlp_processed_at = '2025-12-12 00:40:21',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 12345
```

**This happens for each article in the chunk** (all at once in a batch).

## Visual Example

### Before Processing:

| id  | url | title | content | sentiment | categories | nlp_processed_at |
|-----|-----|-------|---------|-----------|------------|------------------|
| 1   | ... | ...   | ...     | NULL      | NULL       | NULL             |
| 2   | ... | ...   | ...     | NULL      | NULL       | NULL             |
| 3   | ... | ...   | ...     | NULL      | NULL       | NULL             |

### After Processing:

| id  | url | title | content | sentiment | categories | nlp_processed_at |
|-----|-----|-------|---------|-----------|------------|------------------|
| 1   | ... | ...   | ...     | negative  | ["Crime..."] | 2025-12-12... |
| 2   | ... | ...   | ...     | neutral   | ["Politics..."] | 2025-12-12... |
| 3   | ... | ...   | ...     | positive  | ["Other"]      | 2025-12-12... |

## Why This Works Well

1. **Automatic Resume**: If you stop and run again, it only processes articles where `nlp_processed_at IS NULL`
2. **No Duplicates**: Already processed articles are skipped
3. **Direct Updates**: No need to export/import - updates happen in place
4. **Progress Tracking**: You can check progress:
   ```sql
   SELECT COUNT(*) FROM articles WHERE nlp_processed_at IS NOT NULL;
   ```

## What Gets Updated

For each article, these columns are updated:

- `sentiment` → "positive", "negative", or "neutral"
- `sentiment_score` → -1.0, 0.0, or 1.0
- `categories` → JSONB array like `["Crime & Justice", "Politics & Governance"]`
- `entities_json` → JSONB object with persons, locations, organizations
- `nlp_processed_at` → Timestamp of when processing completed
- `updated_at` → Automatically set to current time

## Running It

```bash
cd /home/frede/NAMO_nov25
python3 scripts/02_nlp_processing_from_db.py \
  --total-articles 200 \
  --chunk-size 50
```

**What happens:**
1. Connects to PostgreSQL
2. Finds 200 unprocessed articles
3. Processes 50 at a time
4. Updates database after each chunk of 50
5. Done! Articles are now enriched in the database

No separate loading step needed - it's all automatic!


