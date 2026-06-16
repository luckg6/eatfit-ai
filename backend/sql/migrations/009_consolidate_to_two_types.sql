-- Migration 009: consolidate memory_type from 9 → 2
--
-- Background:
--   The 9-type enum introduced in migration 007 was still too granular:
--   most of the categories overlapped in practice (preference / dislike /
--   restriction / scenario / location were all "soft context the agent
--   should weight when recommending"), and the LLM extractor struggled to
--   pick one consistently (e.g., "我不吃辣" — dislike? restriction?
--   diet_preference?).
--
--   Review with the user landed on two clear categories:
--     preference          : everything the agent should respect when
--                           recommending (口味 / 不喜欢 / 目标 / 预算 /
--                           地点 / 场景 / 睡眠敏感 / 现实限制 — anything
--                           that's not a medical hard constraint)
--     allergy_intolerance : the only category that's medically dangerous
--                           to drop. Always HIGH_IMPORTANCE.
--
-- Migration order matters:
--   1. DROP the old CHECK so the new values are accepted
--   2. UPDATE every row to one of the two new values
--   3. ADD the new tightened CHECK
--
-- Re-runnable: every UPDATE is guarded, the CHECK rebuild uses
-- DROP IF EXISTS / ADD.

BEGIN;

-- 1. Drop old constraint so UPDATEs aren't blocked.
ALTER TABLE memory_items
    DROP CONSTRAINT IF EXISTS memory_items_memory_type_chk;

-- 2. Migrate data. All non-allergy rows collapse into preference.
UPDATE memory_items SET memory_type = 'allergy_intolerance'
    WHERE memory_type = 'allergy_intolerance';
UPDATE memory_items SET memory_type = 'preference'
    WHERE memory_type <> 'allergy_intolerance';

-- 3. Add the tightened constraint.
ALTER TABLE memory_items
    ADD CONSTRAINT memory_items_memory_type_chk
    CHECK (memory_type IN ('preference', 'allergy_intolerance'));

COMMIT;
