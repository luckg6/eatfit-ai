-- Migration: Add chat_messages table
-- Run this to add the chat_messages table to an existing database

CREATE TABLE IF NOT EXISTS chat_messages (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  session_id BIGINT NOT NULL,
  user_id BIGINT NOT NULL,
  role VARCHAR(32) NOT NULL,
  content TEXT NOT NULL,
  action_type VARCHAR(64),
  action_status VARCHAR(64),
  action_data JSON,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_chat_messages_session
    FOREIGN KEY (session_id) REFERENCES advice_sessions(id) ON DELETE CASCADE,
  CONSTRAINT fk_chat_messages_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  KEY idx_chat_messages_session_id (session_id),
  KEY idx_chat_messages_user_id (user_id),
  KEY idx_chat_messages_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Also add chat_messages relationship to advice_sessions (handled via FK, no extra column needed)