-- Migration 005: drop restaurant_context column from advice_sessions
--
-- Background: this column was added by 003_add_restaurant_context.sql to
-- cache nearby-restaurant search results on the chat session. After
-- audit, no handler ever read it — the field was set on the way in and
-- written back on the way out, forming a dead read->pass->write loop.
-- Real restaurant state already lives in chat_messages.action_data
-- (action_type='restaurant_select') and cross-restaurant uid is parsed
-- directly from the user message text by _handle_restaurant_detail_lookup.
--
-- This migration is a no-op for rows where the column is already absent,
-- and safe to run multiple times thanks to the IF EXISTS guard.
--
-- Targets PostgreSQL (live DB). Idempotent.

BEGIN;

ALTER TABLE advice_sessions
    DROP COLUMN IF EXISTS restaurant_context;

COMMIT;
