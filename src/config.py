# src/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path
import os

class Config(BaseSettings):
    SUPABASE_URL: str | None = None # Made optional if only Postgres is used
    SUPABASE_ANON_KEY: str | None = None # Made optional
    DATABASE_URL: str
    APP_VERSION: str = "1.0.1"

    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-2024-08-06"

    PINECONE_API_KEY: str
    PINECONE_INDEX_NAME: str
    PINECONE_CLOUD: str
    PINECONE_REGION: str

    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    REDIS_URL: str

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"
    }

env_path = Path(__file__).parent / ".env"
settings = Config(_env_file=env_path.resolve())


# Validation
if not settings.DATABASE_URL:
    raise ValueError("Missing DATABASE_URL environment variable")
if not settings.OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY environment variable")
if not settings.PINECONE_API_KEY:
    raise ValueError("Missing PINECONE_API_KEY environment variable")
if not settings.REDIS_URL:
    raise ValueError("Missing REDIS_URL environment variable")


@lru_cache
def get_settings() -> Config:
    env_path = Path(__file__).parent / ".env"
    return Config(_env_file=env_path.resolve())