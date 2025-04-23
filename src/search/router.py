# src/search/router.py

import json
import uuid
from typing import Optional, AsyncGenerator, Dict, Any 
from fastapi import APIRouter, Depends, Header, HTTPException 
from fastapi.responses import StreamingResponse
from database.client import get_async_session_factory
from search.services.astralis import Astralis
from search.dependencies import get_astralis
from search.models import QueryRequest
import asyncio
import json


router = APIRouter(prefix="/search", tags=["search"])

@router.get("/")
async def hello():
    return { "message": "Hello from search api v1.0.1 with Sessions!" }

@router.post("/")
async def search(
    request: QueryRequest,
    agent: Astralis = Depends(get_astralis),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """
    Handles search requests, maintaining conversation context via session ID.
    If X-Session-ID header is not provided, a new session is created.
    """
    session_id = x_session_id or str(uuid.uuid4())
    new_session_created = not x_session_id
    print(f"Search request received. Session ID: {session_id} (New: {new_session_created})")
    print(f"Query: {request.query}")

    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate server-sent events with proper formatting and session context."""
        try:
            async for output in agent.run(request.query, session_id=session_id):
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
    if new_session_created:
        response_headers["X-Session-ID"] = session_id
        print(f"Returning new session ID in header: {session_id}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers=response_headers
    )

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

# @router.get("/vector")
# async def test_profile_fetch(agent: Astralis = Depends(get_astralis)):
#     test_user_id = "00a7a0cc-1b25-4d4e-96a6-7d0db3b77d02"
#     try:
#         user = await agent._get_user_profile(test_user_id)
#         if user:
#             return user.for_llm()
#         else:
#             raise HTTPException(status_code=404, detail=f"Test user {test_user_id} not found.")
#     except HTTPException as he:
#         raise he
#     except Exception as e:
#         print(f"Error in /vector test endpoint: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
