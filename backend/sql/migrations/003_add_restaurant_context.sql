-- Add restaurant_context column to advice_sessions
ALTER TABLE advice_sessions ADD COLUMN restaurant_context JSON DEFAULT NULL;