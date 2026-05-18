-- Migration: Enhance memory_items and meal_logs tables
-- Run this to add new fields for enhanced memory and nutrition tracking

-- 1. Enhance memory_items table
ALTER TABLE memory_items
  ADD COLUMN status VARCHAR(32) NOT NULL DEFAULT 'active' AFTER source,
  ADD COLUMN confidence_score DECIMAL(4,2) DEFAULT 0.80 AFTER importance_score,
  ADD COLUMN source_message_id BIGINT NULL AFTER confidence_score,
  ADD COLUMN last_used_at DATETIME NULL AFTER updated_at,
  ADD COLUMN metadata_json JSON NULL AFTER last_used_at;

-- Create index for status filter
CREATE INDEX idx_memory_items_status ON memory_items(status);

-- 2. Enhance meal_logs table
ALTER TABLE meal_logs
  ADD COLUMN calorie_confidence DECIMAL(4,2) DEFAULT 0.70 AFTER estimated_fat,
  ADD COLUMN nutrition_source VARCHAR(64) DEFAULT 'llm_estimate' AFTER calorie_confidence,
  ADD COLUMN source_message_id BIGINT NULL AFTER nutrition_source;

-- Create index for source_message_id
CREATE INDEX idx_meal_logs_source_message ON meal_logs(source_message_id);

-- 3. Add updated_at to chat_messages if not exists
-- Note: This is handled by ON UPDATE in existing schema but we ensure it exists
ALTER TABLE chat_messages
  ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER created_at;

-- Add index for action_status filtering
CREATE INDEX idx_chat_messages_action_status ON chat_messages(action_status);