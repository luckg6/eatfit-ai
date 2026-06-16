-- Migration 006: drop user_question column from advice_sessions
--
-- Background: advice_sessions had two text fields that captured the same
-- first user message at different truncations:
--
--     title        = request.message[:50]   (VARCHAR(255))
--     user_question = request.message[:200]  (TEXT)
--
-- For every row in the live DB where both columns were populated, the values
-- were byte-identical (title == user_question on 30/30 rows). The frontend
-- reads only `title` (Chat.tsx:608, `{s.title || '新对话'}`) and no API
-- response ever returned `user_question` (the AdviceSessionResponse schema
-- was defined but never wired up as a `response_model`).
--
-- This migration drops the redundant column. The `title` field stays as the
-- canonical session label. Idempotent thanks to IF EXISTS, safe to re-run.
--
-- Targets PostgreSQL (live DB). Idempotent.

BEGIN;

ALTER TABLE advice_sessions
    DROP COLUMN IF EXISTS user_question;

COMMIT;
