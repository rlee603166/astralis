# src/search/dependencies.py

import redis.asyncio as redis
import uuid
from fastapi import Depends, HTTPException
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from config import Config, get_settings
from search.services import embedding_engine
from search.agents.astralis import Astralis
from search.services.rag_service import RAGService
from database.client import get_async_session_factory
from sentence_transformers import SentenceTransformer
from search.services.prompt_manager import PromptManager
from search.services.pinecone_manager import PineconeManager
from search.services.neo_manager import NeoManager
from typing import AsyncGenerator


def get_pinecone_manager():
    return PineconeManager()

def get_neo_manager():
    return NeoManager()

def get_rag_service(
    neo_manager:        NeoManager = Depends(get_neo_manager),
    pinecone_manager:   PineconeManager = Depends(get_pinecone_manager),
    embedding_engine:   SentenceTransformer = Depends(embedding_engine.get_embedding_engine)
) -> RAGService:
    return RAGService(
        neo_manager,
        pinecone_manager,
        embedding_engine
    )

async def get_db_factory() -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    session_factory = get_async_session_factory()
    yield session_factory

_openai_client = None

def get_llm(settings: Config = Depends(get_settings)) -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        if not settings.OPENAI_API_KEY:
             raise ValueError("OPENAI_API_KEY not configured")
        _openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client

def get_prompt_manager() -> PromptManager:
    return PromptManager(template_file="search/prompts.yaml")


_redis_pool = None

async def get_redis_client(settings: Config = Depends(get_settings)) -> AsyncGenerator[redis.Redis, None]:
    """Provides a Redis client connection from a pool."""
    global _redis_pool
    if _redis_pool is None:
        try:
            print(f"Initializing Redis connection pool for URL: {settings.REDIS_URL}")
            _redis_pool = redis.from_url(settings.REDIS_URL, decode_responses=True)
            await _redis_pool.ping()
            print("Redis connection successful.")
        except redis.exceptions.RedisError as e:
            print(f"Failed to connect to Redis: {e}")
            raise HTTPException(status_code=503, detail=f"Could not connect to Redis: {e}")

    if _redis_pool:
        yield _redis_pool
    else:
        raise HTTPException(status_code=503, detail="Redis client not available.")

def get_astralis(
    settings: Config = Depends(get_settings),
    client: AsyncOpenAI = Depends(get_llm),
    psql_db_factory: async_sessionmaker[AsyncSession] = Depends(get_db_factory),
    rag_service: RAGService = Depends(get_rag_service),
    prompt_manager: PromptManager = Depends(get_prompt_manager),
    redis_client: redis.Redis = Depends(get_redis_client)
) -> Astralis:
    return Astralis(
        model=settings.OPENAI_MODEL,
        client=client,
        psql_db=psql_db_factory,
        rag_service=rag_service,
        prompt_manager=prompt_manager,
        redis_client=redis_client
    )
