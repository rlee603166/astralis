# src/database/client.py

# from supabase import create_client, Client
# from config import settings
#
#
# supabase_client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
#
# def get_subase_client():
#     return supabase_client

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from config import settings
from typing import Optional

async_engine = None
async_session_factory: Optional[async_sessionmaker[AsyncSession]] = None

def get_async_engine():
    global async_engine
    if async_engine is None:
        async_engine = create_async_engine(
            settings.DATABASE_URL
        )
    return async_engine

def get_async_session_factory():
    global async_session_factory
    if async_session_factory is None:
        async_session_factory = async_sessionmaker(
            bind=get_async_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    
    return async_session_factory