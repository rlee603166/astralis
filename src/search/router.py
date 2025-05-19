# src/search/router.py

import json
import uuid
import asyncio

from sqlalchemy import select, and_, or_, func, text, inspect 
from sqlalchemy.orm import selectinload, aliased
from sqlalchemy import text
from database.models import User
from search.agents.astralis import Astralis
from fastapi.responses import StreamingResponse
from search.services.rag_service import RAGService
from typing import Optional, AsyncGenerator, Dict, Any 
from search.models import QueryRequest, SessionCreateRequest
from fastapi import APIRouter, Depends, Header, HTTPException 
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from search.dependencies import get_astralis, get_rag_service, get_db_factory


router = APIRouter(prefix="/search", tags=["search"])

@router.get("/")
async def hello():
    return { "message": "Hello from search api v1.0.1 with Sessions!" }


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    driver: async_sessionmaker[AsyncSession] = Depends(get_db_factory)
):
    async with driver() as session:
        result = await session.execute(
            text("""
                SELECT * FROM chat_messages
                WHERE session_id = :session_id
                ORDER BY created_at;
            """),
            { "session_id": session_id }
        )
    messages = result.mappings().all()

    return messages


@router.post("/sessions")
async def create_session(
    request: SessionCreateRequest,
    driver: async_sessionmaker[AsyncSession] = Depends(get_db_factory)
):
    user_id = request.user_id
    session_id = str(uuid.uuid4())
    async with driver() as session:
        await session.execute(
            text("""
                INSERT INTO chat_sessions (session_id, user_id)
                VALUES (:session_id, :user_id)
            """),
            { "session_id": session_id, "user_id": user_id }
        )
        await session.commit()

    return {"session_id": session_id}


@router.post("/query")
async def search(
    request: QueryRequest,
    agent: Astralis = Depends(get_astralis)
):
    query = request.query
    session_id = request.session_id
    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate server-sent events with proper formatting and session context."""
        try:
            async for output in agent.run(query, session_id=session_id):
                try:
                    output_json = json.dumps(output)
                    yield f"data: {output_json}\n\n"
                except TypeError as e:
                     print(f"[ERROR] Failed to serialize output chunk to JSON: {e} - Chunk: {output}")
                     error_event = {"type": "error", "message": f"Failed to serialize output: {e}"}
                     yield f"data: {json.dumps(error_event)}\n\n"

        except Exception as e:
            # Catch any unexpected errors during agent execution or streaming
            print(f"[ERROR] Error during search stream for session {session_id}: {e}")

            error_event = {"type": "error", "message": f"An internal error occurred: {e}"}
            try:
                 yield f"data: {json.dumps(error_event)}\n\n"
            except TypeError:
                 yield f"data: {json.dumps({'type': 'error', 'message': 'An internal error occurred.'})}\n\n"
        finally:
            print(f"Finished streaming response for session {session_id}")


    response_headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Content-Type-Options": "nosniff",
    }

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers=response_headers
    )


"""
Test Endpoints
"""
@router.get("/vector")
async def test(agent: Astralis = Depends(get_astralis)):
    user_ids = [
        "00a7a0cc-1b25-4d4e-96a6-7d0db3b77d02",
        "e9acfe1a-8017-4c6d-9062-5ec597f262ae",
        "291810ae-4a38-4c03-afda-01fa6f24a692",
        "23e73c57-fd2f-4f44-8240-2e22d0a8f4cc",
        "ed2ed319-e6a8-4946-a88d-44d0a48e8e2c",
        "4d7e59d5-1e6d-4637-8cbf-3b9e597bf21a",
        "2e8a7cb9-4d4d-4d0b-939c-368ff9f0a92b",
        "b357c1c7-57b8-4f70-a413-6a6d88c1ceb4",
        "74e2f5ef-67a9-4d0a-a5a5-218188a76280",
        "37be97e9-7d7a-41ce-8981-c742af37aa38",
    ]

    async def get_user(user_id):
        user = await agent._get_user_profile(user_id)
        return user.to_dict()

    tasks = [get_user(id) for id in user_ids]

    return await asyncio.gather(*tasks)

async def _get_user_profile(
    user_id: str,
    psql_db_factory: async_sessionmaker[AsyncSession]
) -> User | None:
    print(f"Fetching profile for user_id: {user_id}")
    query = (
        select(User)
        .options(
            selectinload(User.projects),
            selectinload(User.educations),
            selectinload(User.experiences),
            selectinload(User.skills)
        )
        .where(User.user_id == user_id)
    )

    async with psql_db_factory() as session:
        try:
            result = await session.execute(query)
            user = result.scalars().first()
            if not user:
                print(f"[INFO] User profile not found for id: {user_id}")
                return None
            return user
        except Exception as e:
            print(f"[ERROR] Database error fetching profile {user_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Database error fetching profile {user_id}")

@router.get("/graph")
async def graph(
    rag_service: RAGService = Depends(get_rag_service),
    psql_db_factory: async_sessionmaker[AsyncSession] = Depends(get_db_factory)
):
    query = """
    MATCH (p:Person)-[:HAS_EXPERIENCE]->(e1:Experience)
    WHERE toLower(e1.company_name) CONTAINS "google"
      AND toLower(e1.job_title) CONTAINS "software engineer"

    MATCH (e1)-[:NEXT_EXPERIENCE]->(e2:Experience)
    LIMIT 5
    RETURN p, 
           e1.company_name AS from_company, 
           e1.job_title AS from_title, 
           e2.company_name AS to_company, 
           e2.job_title AS to_title,
           e2.start_date AS transition_date
    ORDER BY transition_date
    """

    user_ids = []
    records = await rag_service.query_graph(query)
    for record in records:
        print(record)
        user_ids.append(record.data()["p"]["user_id"])

    unique_user_ids = list(set(user_ids))
    print(f"Found {len(unique_user_ids)} unique user IDs from vector search.")

    if not unique_user_ids:
        return []

    tasks = [_get_user_profile(uid, psql_db_factory) for uid in unique_user_ids]
    fetched_users_results = await asyncio.gather(*tasks, return_exceptions=True)

    fetched_users = []
    for i, result in enumerate(fetched_users_results):
        if isinstance(result, User):
            fetched_users.append(result)
        elif isinstance(result, Exception):
            print(f"[ERROR] Failed to fetch profile for user_id {unique_user_ids[i]}: {result}")

    return fetched_users

