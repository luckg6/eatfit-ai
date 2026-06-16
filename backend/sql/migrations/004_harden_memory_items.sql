-- Migration 004: harden memory_items schema
-- Targets: data-integrity gaps surfaced during the pgvector migration review.
--   * CHECK constraints on enum-like varchar columns
--   * CHECK on importance_score / confidence_score ranges
--   * UNIQUE (user_id, memory_type, content) for dedup at the DB layer
--   * BEFORE UPDATE trigger to auto-bump updated_at (covers raw-SQL paths
--     that bypass SQLAlchemy's onupdate=func.now())
--   * New index (user_id, status, last_used_at DESC) for "active memories
--     by recency" queries
--   * Partial index on embedding_status = 'pending' for the backfill worker
--
-- Re-runnable: every ALTER uses IF NOT EXISTS / DROP IF EXISTS guards.
--
-- Targets PostgreSQL (live DB). Idempotent.

BEGIN;

-- ------------------------------------------------------------
-- 1. CHECK constraints (enum-like columns)
-- ------------------------------------------------------------
ALTER TABLE memory_items
    DROP CONSTRAINT IF EXISTS memory_items_status_chk;
ALTER TABLE memory_items
    ADD CONSTRAINT memory_items_status_chk
    CHECK (status IN ('active', 'inactive', 'superseded', 'pending'));

ALTER TABLE memory_items
    DROP CONSTRAINT IF EXISTS memory_items_embedding_status_chk;
ALTER TABLE memory_items
    ADD CONSTRAINT memory_items_embedding_status_chk
    CHECK (embedding_status IN ('pending', 'ready', 'failed'));

ALTER TABLE memory_items
    DROP CONSTRAINT IF EXISTS memory_items_source_chk;
ALTER TABLE memory_items
    ADD CONSTRAINT memory_items_source_chk
    CHECK (source IN ('manual', 'chat', 'auto_extracted', 'rest_api'));

-- memory_type is the enum maintained in app code (MemoryTools.MEMORY_TYPES).
-- Mirror it here so DB rejects typos.
ALTER TABLE memory_items
    DROP CONSTRAINT IF EXISTS memory_items_memory_type_chk;
ALTER TABLE memory_items
    ADD CONSTRAINT memory_items_memory_type_chk
    CHECK (memory_type IN (
        'diet_preference', 'food_dislike', 'allergy_intolerance', 'goal',
        'budget', 'location', 'scenario', 'sleep', 'body_response',
        'restriction', 'habit', 'other'
    ));

-- ------------------------------------------------------------
-- 2. Range checks on numeric columns
-- ------------------------------------------------------------
ALTER TABLE memory_items
    DROP CONSTRAINT IF EXISTS memory_items_importance_score_range_chk;
ALTER TABLE memory_items
    ADD CONSTRAINT memory_items_importance_score_range_chk
    CHECK (importance_score BETWEEN 1 AND 10);

ALTER TABLE memory_items
    DROP CONSTRAINT IF EXISTS memory_items_confidence_score_range_chk;
ALTER TABLE memory_items
    ADD CONSTRAINT memory_items_confidence_score_range_chk
    CHECK (confidence_score IS NULL
           OR confidence_score BETWEEN 0.00 AND 1.00);

-- ------------------------------------------------------------
-- 3. Sanity: updated_at cannot predate created_at
-- ------------------------------------------------------------
ALTER TABLE memory_items
    DROP CONSTRAINT IF EXISTS memory_items_updated_at_after_created_at_chk;
ALTER TABLE memory_items
    ADD CONSTRAINT memory_items_updated_at_after_created_at_chk
    CHECK (updated_at >= created_at);

-- ------------------------------------------------------------
-- 4. UNIQUE constraint for dedup (DB-layer guard against
--    "user said the same thing 3 times -> 3 rows")
-- ------------------------------------------------------------
-- Case-sensitive, exact text match. Normalization is the app's job;
-- the DB only blocks the obvious case.
ALTER TABLE memory_items
    DROP CONSTRAINT IF EXISTS memory_items_user_type_content_uq;
ALTER TABLE memory_items
    ADD CONSTRAINT memory_items_user_type_content_uq
    UNIQUE (user_id, memory_type, content);

-- ------------------------------------------------------------
-- 5. BEFORE UPDATE trigger: bump updated_at if and only if
--    the caller didn't explicitly change it. Covers raw-SQL
--    UPDATE statements (e.g. _hybrid_search's batch touch on
--    last_used_at) that bypass SQLAlchemy's onupdate hook.
-- ------------------------------------------------------------
CREATE OR REPLACE FUNCTION memory_items_touch_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.updated_at IS NOT DISTINCT FROM OLD.updated_at THEN
        NEW.updated_at := NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_memory_items_touch_updated_at ON memory_items;
CREATE TRIGGER trg_memory_items_touch_updated_at
    BEFORE UPDATE ON memory_items
    FOR EACH ROW
    EXECUTE FUNCTION memory_items_touch_updated_at();

-- ------------------------------------------------------------
-- 6. New indexes
-- ------------------------------------------------------------
-- 6a. "Get my active memories, most recently used first"
--     used by advisory endpoints that rank by recency.
CREATE INDEX IF NOT EXISTS idx_memory_user_status_last_used
    ON memory_items (user_id, status, last_used_at DESC NULLS LAST);

-- 6b. Partial index for the embedding backfill worker
--     (only ~rows needing work are indexed).
CREATE INDEX IF NOT EXISTS idx_memory_embedding_pending
    ON memory_items (user_id, id)
    WHERE embedding_status IN ('pending', 'failed');

-- 6c. Source-message traceability index. Helps look up
--     "what memories did this message produce?" cheaply.
CREATE INDEX IF NOT EXISTS idx_memory_source_message
    ON memory_items (source_message_id)
    WHERE source_message_id IS NOT NULL;

COMMIT;
