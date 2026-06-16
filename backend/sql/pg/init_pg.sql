-- ============================================================
-- eatfit_ai schema for PostgreSQL 17 + pgvector 0.8.2
-- 对应原 MySQL init.sql；memory_items 多了一个 vector(1024) 列
-- ============================================================

-- users ------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id                  BIGSERIAL PRIMARY KEY,
    username            VARCHAR(64)  NOT NULL UNIQUE,
    email               VARCHAR(128) NOT NULL UNIQUE,
    password_hash       VARCHAR(255) NOT NULL,
    auto_memory_enabled BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- user_food_profiles ----------------------------------------
CREATE TABLE IF NOT EXISTS user_food_profiles (
    id                       BIGSERIAL PRIMARY KEY,
    user_id                  BIGINT       NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    nickname                 VARCHAR(64),
    gender                   VARCHAR(32),
    age                      INTEGER,
    height_cm                DECIMAL(5,2),
    weight_kg                DECIMAL(5,2),
    body_fat_percent         DECIMAL(5,2),
    target_weight_kg         DECIMAL(5,2),
    primary_goal             VARCHAR(64),
    activity_level           VARCHAR(64),
    training_frequency       INTEGER,
    training_type            VARCHAR(128),
    food_preferences         TEXT,
    food_dislikes            TEXT,
    allergies                TEXT,
    budget_per_meal          DECIMAL(8,2),
    common_eating_scenarios  TEXT,
    sleep_sensitive          BOOLEAN      NOT NULL DEFAULT FALSE,
    sleep_notes              TEXT,
    notes                    TEXT,
    created_at               TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at               TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- memory_items (含 embedding) -------------------------------
CREATE TABLE IF NOT EXISTS memory_items (
    id                  BIGSERIAL PRIMARY KEY,
    user_id             BIGINT       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    memory_type         VARCHAR(64)  NOT NULL,
    content             TEXT         NOT NULL,
    importance_score    INTEGER      NOT NULL DEFAULT 5,
    confidence_score    DECIMAL(4,2) DEFAULT 0.80,
    source_message_id   BIGINT,
    source              VARCHAR(64)  NOT NULL DEFAULT 'manual',
    status              VARCHAR(32)  NOT NULL DEFAULT 'active',
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_used_at        TIMESTAMPTZ,
    metadata_json       JSONB,
    -- 向量字段：1024 维，qwen3-embedding:0.6b 输出维度
    embedding           vector(1024),
    embedding_status    VARCHAR(32)  NOT NULL DEFAULT 'pending',
    embedding_updated_at TIMESTAMPTZ,
    -- enum-like guards (mirror MemoryTools.MEMORY_TYPES)
    CONSTRAINT memory_items_status_chk
        CHECK (status IN ('active', 'inactive', 'superseded', 'pending')),
    CONSTRAINT memory_items_embedding_status_chk
        CHECK (embedding_status IN ('pending', 'ready', 'failed')),
    CONSTRAINT memory_items_source_chk
        CHECK (source IN ('manual', 'chat', 'auto_extracted', 'rest_api')),
    CONSTRAINT memory_items_memory_type_chk
        CHECK (memory_type IN ('preference', 'allergy_intolerance')),
    CONSTRAINT memory_items_importance_score_range_chk
        CHECK (importance_score BETWEEN 1 AND 10),
    CONSTRAINT memory_items_confidence_score_range_chk
        CHECK (confidence_score IS NULL OR confidence_score BETWEEN 0.00 AND 1.00),
    CONSTRAINT memory_items_updated_at_after_created_at_chk
        CHECK (updated_at >= created_at),
    CONSTRAINT memory_items_user_type_content_uq
        UNIQUE (user_id, memory_type, content)
);
CREATE INDEX IF NOT EXISTS idx_memory_user_type_status ON memory_items(user_id, memory_type, status);
CREATE INDEX IF NOT EXISTS idx_memory_user_importance  ON memory_items(user_id, importance_score DESC);
CREATE INDEX IF NOT EXISTS idx_memory_user_status_last_used
    ON memory_items(user_id, status, last_used_at DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_memory_embedding_pending
    ON memory_items(user_id, id)
    WHERE embedding_status IN ('pending', 'failed');
CREATE INDEX IF NOT EXISTS idx_memory_source_message
    ON memory_items(source_message_id)
    WHERE source_message_id IS NOT NULL;

-- Auto-bump updated_at on UPDATE (covers raw-SQL paths that bypass
-- SQLAlchemy's onupdate=func.now()). Only fires when the caller did
-- not explicitly assign a new value.
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

-- meal_logs -------------------------------------------------
CREATE TABLE IF NOT EXISTS meal_logs (
    id                  BIGSERIAL PRIMARY KEY,
    user_id             BIGINT       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    meal_type           VARCHAR(64)  NOT NULL,
    meal_time           TIMESTAMPTZ  NOT NULL,
    food_text           TEXT         NOT NULL,
    scenario            VARCHAR(64),
    estimated_calories  DECIMAL(8,2),
    estimated_protein   DECIMAL(8,2),
    estimated_carbs     DECIMAL(8,2),
    estimated_fat       DECIMAL(8,2),
    calorie_confidence  DECIMAL(4,2) DEFAULT 0.70,
    nutrition_source    VARCHAR(64)  DEFAULT 'llm_estimate',
    source_message_id   BIGINT,
    health_score        INTEGER,
    sleep_impact        VARCHAR(64)  DEFAULT 'UNKNOWN',
    ai_comment          TEXT,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_meal_user_time ON meal_logs(user_id, meal_time DESC);
CREATE INDEX IF NOT EXISTS idx_meal_user_scenario ON meal_logs(user_id, scenario);

-- advice_sessions -------------------------------------------
CREATE TABLE IF NOT EXISTS advice_sessions (
    id                  BIGSERIAL PRIMARY KEY,
    user_id             BIGINT       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title               VARCHAR(255),
    context_text        TEXT,
    ai_response_json    JSONB,
    scenario            VARCHAR(64)  DEFAULT 'OTHER',
    is_training_day     BOOLEAN      DEFAULT FALSE,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_advice_sessions_user_created ON advice_sessions(user_id, created_at DESC);

-- chat_messages ---------------------------------------------
CREATE TABLE IF NOT EXISTS chat_messages (
    id              BIGSERIAL PRIMARY KEY,
    session_id      BIGINT       NOT NULL REFERENCES advice_sessions(id) ON DELETE CASCADE,
    user_id         BIGINT       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role            VARCHAR(32)  NOT NULL,
    content         TEXT         NOT NULL,
    action_type     VARCHAR(64),
    action_status   VARCHAR(64),
    action_data     JSONB,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_messages(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_chat_user    ON chat_messages(user_id, created_at DESC);

-- weight_records --------------------------------------------
CREATE TABLE IF NOT EXISTS weight_records (
    id            BIGSERIAL PRIMARY KEY,
    user_id       BIGINT       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    weight_kg     DECIMAL(5,2) NOT NULL,
    record_date   DATE         NOT NULL,
    note          TEXT,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_weight_user_date ON weight_records(user_id, record_date DESC);

-- body_fat_records ------------------------------------------
CREATE TABLE IF NOT EXISTS body_fat_records (
    id                BIGSERIAL PRIMARY KEY,
    user_id           BIGINT       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    body_fat_percent  DECIMAL(5,2) NOT NULL,
    record_date       DATE         NOT NULL,
    note              TEXT,
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_body_fat_user_date ON body_fat_records(user_id, record_date DESC);

-- training_records ------------------------------------------
CREATE TABLE IF NOT EXISTS training_records (
    id                BIGSERIAL PRIMARY KEY,
    user_id           BIGINT       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    training_type     VARCHAR(128),
    duration_minutes  INTEGER,
    intensity         VARCHAR(64),
    record_date       DATE         NOT NULL,
    note              TEXT,
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_training_user_date ON training_records(user_id, record_date DESC);

-- diet_advice_records ---------------------------------------
CREATE TABLE IF NOT EXISTS diet_advice_records (
    id                       BIGSERIAL PRIMARY KEY,
    user_id                  BIGINT       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id               BIGINT       NOT NULL REFERENCES advice_sessions(id) ON DELETE CASCADE,
    situation_summary        TEXT,
    recommendation_strategy  TEXT,
    recommended_options_json JSONB,
    not_recommended_json     JSONB,
    estimated_summary_json   JSONB,
    next_meal_advice         TEXT,
    sleep_friendly_tips      TEXT,
    risk_level               VARCHAR(64)  DEFAULT 'LOW',
    created_at               TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_diet_advice_user ON diet_advice_records(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_diet_advice_session ON diet_advice_records(session_id);
