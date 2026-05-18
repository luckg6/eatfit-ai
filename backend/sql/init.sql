CREATE DATABASE IF NOT EXISTS eatfit_ai
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE eatfit_ai;

CREATE TABLE IF NOT EXISTS users (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(64) NOT NULL UNIQUE,
  email VARCHAR(128) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  auto_memory_enabled BOOLEAN NOT NULL DEFAULT TRUE,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS user_food_profiles (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  nickname VARCHAR(64),
  gender VARCHAR(32),
  age INT,
  height_cm DECIMAL(5,2),
  weight_kg DECIMAL(5,2),
  body_fat_percent DECIMAL(5,2),
  target_weight_kg DECIMAL(5,2),
  primary_goal VARCHAR(64),
  activity_level VARCHAR(64),
  training_frequency INT,
  training_type VARCHAR(128),
  food_preferences TEXT,
  food_dislikes TEXT,
  allergies TEXT,
  budget_per_meal DECIMAL(8,2),
  common_eating_scenarios TEXT,
  sleep_sensitive BOOLEAN NOT NULL DEFAULT FALSE,
  sleep_notes TEXT,
  notes TEXT,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_user_food_profiles_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  UNIQUE KEY uk_user_food_profiles_user_id (user_id),
  KEY idx_user_food_profiles_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS memory_items (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  memory_type VARCHAR(64) NOT NULL,
  content TEXT NOT NULL,
  importance_score INT NOT NULL DEFAULT 5,
  source VARCHAR(64) NOT NULL DEFAULT 'manual',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_memory_items_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  KEY idx_memory_items_user_id (user_id),
  KEY idx_memory_items_memory_type (memory_type),
  KEY idx_memory_items_importance_score (importance_score),
  KEY idx_memory_items_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS meal_logs (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  meal_type VARCHAR(64) NOT NULL,
  meal_time DATETIME NOT NULL,
  food_text TEXT NOT NULL,
  scenario VARCHAR(64),
  estimated_calories DECIMAL(8,2),
  estimated_protein DECIMAL(8,2),
  estimated_carbs DECIMAL(8,2),
  estimated_fat DECIMAL(8,2),
  health_score INT,
  sleep_impact VARCHAR(64) DEFAULT 'UNKNOWN',
  ai_comment TEXT,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_meal_logs_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  KEY idx_meal_logs_user_id (user_id),
  KEY idx_meal_logs_meal_time (meal_time),
  KEY idx_meal_logs_meal_type (meal_type),
  KEY idx_meal_logs_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS advice_sessions (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  title VARCHAR(255),
  user_question TEXT,
  context_text TEXT,
  ai_response_json JSON,
  scenario VARCHAR(64) DEFAULT 'OTHER',
  is_training_day TINYINT(1) DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_advice_sessions_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  KEY idx_advice_sessions_user_id (user_id),
  KEY idx_advice_sessions_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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

CREATE TABLE IF NOT EXISTS diet_advice_records (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  session_id BIGINT NOT NULL,
  situation_summary TEXT,
  recommendation_strategy TEXT,
  recommended_options_json JSON,
  not_recommended_json JSON,
  estimated_summary_json JSON,
  next_meal_advice TEXT,
  sleep_friendly_tips TEXT,
  risk_level VARCHAR(64) DEFAULT 'LOW',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_diet_advice_records_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_diet_advice_records_session
    FOREIGN KEY (session_id) REFERENCES advice_sessions(id) ON DELETE CASCADE,
  KEY idx_diet_advice_records_user_id (user_id),
  KEY idx_diet_advice_records_session_id (session_id),
  KEY idx_diet_advice_records_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS weight_records (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  weight_kg DECIMAL(5,2) NOT NULL,
  record_date DATE NOT NULL,
  note TEXT,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_weight_records_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  KEY idx_weight_records_user_id (user_id),
  KEY idx_weight_records_record_date (record_date),
  UNIQUE KEY uk_weight_records_user_date (user_id, record_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS body_fat_records (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  body_fat_percent DECIMAL(5,2) NOT NULL,
  record_date DATE NOT NULL,
  note TEXT,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_body_fat_records_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  KEY idx_body_fat_records_user_id (user_id),
  KEY idx_body_fat_records_record_date (record_date),
  UNIQUE KEY uk_body_fat_records_user_date (user_id, record_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS training_records (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  training_type VARCHAR(128),
  duration_minutes INT,
  intensity VARCHAR(64),
  record_date DATE NOT NULL,
  note TEXT,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_training_records_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  KEY idx_training_records_user_id (user_id),
  KEY idx_training_records_record_date (record_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;