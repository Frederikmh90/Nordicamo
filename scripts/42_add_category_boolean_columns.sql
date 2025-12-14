-- Migration: Add boolean category columns for easier querying
-- Creates columns like newscat_crimejustice, newscat_politicsgovernance, etc.
-- These are computed from the JSONB categories array

-- Category name to column name mapping
-- Format: "Crime & Justice" -> "newscat_crimejustice"
-- Rules: lowercase, remove spaces and special chars, prefix with "newscat_"

DO $$
DECLARE
    cat_name TEXT;
    col_name TEXT;
    categories TEXT[] := ARRAY[
        'Politics & Governance',
        'Immigration & National Identity',
        'Health & Medicine',
        'Media & Censorship',
        'International Relations & Conflict',
        'Economy & Labor',
        'Crime & Justice',
        'Social Issues & Culture',
        'Environment, Climate & Energy',
        'Technology, Science & Digital Society',
        'Other'
    ];
BEGIN
    -- Add boolean columns for each category
    FOREACH cat_name IN ARRAY categories
    LOOP
        -- Convert category name to column name
        col_name := 'newscat_' || LOWER(REGEXP_REPLACE(cat_name, '[^a-zA-Z0-9]', '', 'g'));
        
        -- Add column if it doesn't exist
        EXECUTE format('
            ALTER TABLE articles 
            ADD COLUMN IF NOT EXISTS %I BOOLEAN DEFAULT FALSE
        ', col_name);
        
        -- Create index for faster filtering
        EXECUTE format('
            CREATE INDEX IF NOT EXISTS idx_articles_%I ON articles (%I) WHERE %I = TRUE
        ', col_name, col_name, col_name);
    END LOOP;
END $$;

-- Function to update boolean columns from JSONB categories array
CREATE OR REPLACE FUNCTION update_category_columns()
RETURNS TRIGGER AS $$
DECLARE
    cat_name TEXT;
    col_name TEXT;
    categories TEXT[] := ARRAY[
        'Politics & Governance',
        'Immigration & National Identity',
        'Health & Medicine',
        'Media & Censorship',
        'International Relations & Conflict',
        'Economy & Labor',
        'Crime & Justice',
        'Social Issues & Culture',
        'Environment, Climate & Energy',
        'Technology, Science & Digital Society',
        'Other'
    ];
BEGIN
    -- Reset all category columns to FALSE
    FOREACH cat_name IN ARRAY categories
    LOOP
        col_name := 'newscat_' || LOWER(REGEXP_REPLACE(cat_name, '[^a-zA-Z0-9]', '', 'g'));
        EXECUTE format('NEW.%I := FALSE', col_name);
    END LOOP;
    
    -- Set to TRUE if category is in JSONB array
    IF NEW.categories IS NOT NULL AND jsonb_typeof(NEW.categories) = 'array' THEN
        FOREACH cat_name IN ARRAY categories
        LOOP
            col_name := 'newscat_' || LOWER(REGEXP_REPLACE(cat_name, '[^a-zA-Z0-9]', '', 'g'));
            IF NEW.categories ? cat_name OR NEW.categories @> to_jsonb(cat_name) THEN
                EXECUTE format('NEW.%I := TRUE', col_name);
            END IF;
        END LOOP;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to auto-update boolean columns when categories change
DROP TRIGGER IF EXISTS trigger_update_category_columns ON articles;
CREATE TRIGGER trigger_update_category_columns
    BEFORE INSERT OR UPDATE OF categories ON articles
    FOR EACH ROW
    EXECUTE FUNCTION update_category_columns();

-- Update existing rows
DO $$
DECLARE
    cat_name TEXT;
    col_name TEXT;
    categories TEXT[] := ARRAY[
        'Politics & Governance',
        'Immigration & National Identity',
        'Health & Medicine',
        'Media & Censorship',
        'International Relations & Conflict',
        'Economy & Labor',
        'Crime & Justice',
        'Social Issues & Culture',
        'Environment, Climate & Energy',
        'Technology, Science & Digital Society',
        'Other'
    ];
BEGIN
    FOREACH cat_name IN ARRAY categories
    LOOP
        col_name := 'newscat_' || LOWER(REGEXP_REPLACE(cat_name, '[^a-zA-Z0-9]', '', 'g'));
        EXECUTE format('
            UPDATE articles
            SET %I = (categories ? %L OR categories @> to_jsonb(%L))
            WHERE categories IS NOT NULL
        ', col_name, cat_name, cat_name);
    END LOOP;
END $$;

-- Verification query
SELECT 
    'newscat_crimejustice' as column_name,
    COUNT(*) FILTER (WHERE newscat_crimejustice = TRUE) as true_count,
    COUNT(*) FILTER (WHERE newscat_crimejustice = FALSE) as false_count
FROM articles
LIMIT 1;


