from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg://postgres:root@localhost:5432/eatfit_ai"
    JWT_SECRET_KEY: str = "please-change-this-secret-key-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080
    LLM_API_KEY: Optional[str] = ""
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-4o-mini"
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # Embedding / vector search
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    EMBEDDING_MODEL: str = "qwen3-embedding:0.6b"
    EMBEDDING_DIM: int = 1024
    # 混合排序权重：importance_score 部分最大 10，向量余弦相似度 0~1
    MEMORY_VECTOR_WEIGHT: float = 0.6
    MEMORY_IMPORTANCE_WEIGHT: float = 0.4

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()