-- Migration 008: full-text search (Chinese) for memory_items
--
-- Adds two columns and a GIN index for token-level full-text search:
--   content_zh  : the tokenized form of `content` (jieba-segmented, space-separated)
--                 filled by Python on every write — this is the "right" path.
--   content_tsv : tsvector GENERATED-style column, populated by a BEFORE INSERT/
--                 UPDATE trigger. The trigger reads content_zh if present, else
--                 applies a regex-based char-split fallback for raw-SQL writes
--                 that bypass the Python layer.
--
-- Why jieba-in-Python instead of zhparser-in-PG:
--   zhparser isn't packaged with the Windows PG 17 build on this machine and
--   compiling a C extension against the running PG version is fragile. jieba
--   is the de-facto Chinese tokenizer; we do segmentation in Python and let
--   PG only do the indexing (`to_tsvector('simple', tokenized_text)` works
--   fine because the words are already space-separated).
--
-- Index choice:
--   GIN on tsvector is the standard pick for full-text lookups; supports the
--   @@ match operator and ts_rank scoring.
--
-- Trigger ordering with migration 004's trg_memory_items_touch_updated_at:
--   004's trigger only fires on UPDATE and bumps updated_at when untouched.
--   008's trigger fires BEFORE INSERT OR UPDATE OF content, content_zh and
--   only mutates content_tsv. No conflict.

BEGIN;

ALTER TABLE memory_items
    ADD COLUMN IF NOT EXISTS content_zh  TEXT;
ALTER TABLE memory_items
    ADD COLUMN IF NOT EXISTS content_tsv TSVECTOR;

CREATE INDEX IF NOT EXISTS idx_memory_tsv
    ON memory_items USING GIN (content_tsv);

-- BEFORE INSERT / UPDATE OF content, content_zh: keep content_tsv in sync.
-- Prefer content_zh (jieba-segmented) when present; otherwise char-split as
-- a last-resort fallback for raw SQL writes that skip the Python layer.
CREATE OR REPLACE FUNCTION memory_items_refresh_tsv()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.content_zh IS NOT NULL AND btrim(NEW.content_zh) <> '' THEN
        NEW.content_tsv := to_tsvector('simple', NEW.content_zh);
    ELSE
        -- Fallback: insert a space between every Chinese char + lowercase ascii.
        -- Quality is far worse than jieba (every CJK char is its own token)
        -- but the column never stays NULL, so the GIN index stays usable.
        NEW.content_tsv := to_tsvector(
            'simple',
            regexp_replace(
                regexp_replace(coalesce(NEW.content, ''), '([一-鿿])', '\1 ', 'g'),
                '([A-Za-z])', '\1', 'g'
            )
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_memory_items_refresh_tsv ON memory_items;
CREATE TRIGGER trg_memory_items_refresh_tsv
    BEFORE INSERT OR UPDATE OF content, content_zh ON memory_items
    FOR EACH ROW
    EXECUTE FUNCTION memory_items_refresh_tsv();

-- Backfill existing rows: refresh content_tsv from whatever content we have.
-- (content_zh will be filled by the Python backfill script after migration.)
UPDATE memory_items SET content_tsv = NULL WHERE TRUE;
UPDATE memory_items SET content_tsv = to_tsvector(
    'simple',
    regexp_replace(content, '([一-鿿])', '\1 ', 'g')
);

COMMIT;
