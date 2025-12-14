-- Migration: add NLP fields and URL uniqueness for articles
-- Note: review and run manually once approved. Requires PostgreSQL.
-- Safe-guards included to avoid errors if columns/constraints already exist.

-- 1) Ensure pgcrypto is available (for url_hash generation)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 2) Add columns if missing
ALTER TABLE articles
    ADD COLUMN IF NOT EXISTS sentiment TEXT,
    ADD COLUMN IF NOT EXISTS sentiment_score DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS categories JSONB,
    ADD COLUMN IF NOT EXISTS entities_json JSONB,
    ADD COLUMN IF NOT EXISTS topic_id INTEGER,
    ADD COLUMN IF NOT EXISTS topic_probability DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS url_hash TEXT;

-- 3) Populate url_hash for existing rows (only where null)
UPDATE articles
SET url_hash = encode(digest(url, 'sha256'), 'hex')
WHERE url_hash IS NULL AND url IS NOT NULL;

-- 4) Enforce url NOT NULL and uniqueness
ALTER TABLE articles
    ALTER COLUMN url SET NOT NULL;

-- If a unique constraint on url does not exist, create it
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'articles_url_key'
          AND conrelid = 'articles'::regclass
    ) THEN
        ALTER TABLE articles ADD CONSTRAINT articles_url_key UNIQUE (url);
    END IF;
END$$;

-- 5) Add an index on url_hash for faster lookups (idempotent)
CREATE INDEX IF NOT EXISTS idx_articles_url_hash ON articles (url_hash);

-- 6) Set reasonable defaults (optional; keeps NULLs unless populated)
ALTER TABLE articles
    ALTER COLUMN categories SET DEFAULT '[]'::jsonb,
    ALTER COLUMN entities_json SET DEFAULT '{}'::jsonb;

-- Verification queries (optional to run manually after migration):
-- \d articles
-- SELECT COUNT(*) FROM articles;
-- SELECT COUNT(DISTINCT url) FROM articles;


