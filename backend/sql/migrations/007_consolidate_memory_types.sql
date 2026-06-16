-- Migration 007: consolidate memory_type from 12 → 9
--
-- Background:
--   The original 12-type enum had three problems surfaced by code review:
--     1. 'other'      : never queried by any intent → write-only data hole
--     2. 'body_response': listed in HIGH_IMPORTANCE_TYPES (forces confirm card)
--                         but absent from every intent_memory_map → user
--                         confirms a memory and the agent never recalls it
--     3. 'habit'      : boundary with 'scenario' is undefined (LLM picks
--                         arbitrarily which way a habit goes)
--   'location' is also off the recall path today; we keep it (it carries
--   non-overlapping info — concrete address vs abstract scenario) but add
--   it to the recall map so it actually surfaces in recommendations.
--
-- Consolidation:
--   body_response → allergy_intolerance  (food → negative body reaction)
--   habit         → scenario             (habit = scenario + frequency)
--   other         → allergy_intolerance  (fallback bucket — closest in meaning
--                                          among the surviving types; better
--                                          than silently losing rows)
--   location, sleep, restriction, goal, budget, diet_preference, food_dislike:
--                                          unchanged
--
-- Re-runnable: every UPDATE is gated by an existence check so this migration
-- is idempotent. The CHECK constraint rebuild uses DROP IF EXISTS / ADD.
--
-- Targets PostgreSQL (live DB). Idempotent.

BEGIN;

-- ------------------------------------------------------------
-- 1. Migrate existing rows to the new enum values.
--    Each UPDATE has a WHERE memory_type = '<old>' guard so it's a
--    no-op once the migration has run once.
-- ------------------------------------------------------------
UPDATE memory_items SET memory_type = 'allergy_intolerance'
    WHERE memory_type = 'body_response';
UPDATE memory_items SET memory_type = 'scenario'
    WHERE memory_type = 'habit';
UPDATE memory_items SET memory_type = 'allergy_intolerance'
    WHERE memory_type = 'other';

-- ------------------------------------------------------------
-- 2. Tighten the CHECK constraint to the new 9-type enum.
-- ------------------------------------------------------------
ALTER TABLE memory_items
    DROP CONSTRAINT IF EXISTS memory_items_memory_type_chk;
ALTER TABLE memory_items
    ADD CONSTRAINT memory_items_memory_type_chk
    CHECK (memory_type IN (
        'diet_preference', 'food_dislike', 'allergy_intolerance', 'goal',
        'budget', 'location', 'scenario', 'sleep', 'restriction'
    ));

COMMIT;
