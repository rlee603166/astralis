# src/search/models.py

from uuid import UUID
from typing import List
from pydantic import BaseModel, PositiveFloat

class QueryRequest(BaseModel):
    query: str
    session_id: UUID

class Metadata(BaseModel):
    text: str
    user_id: str

class PineconeUser(BaseModel):
    id: str
    metadata: Metadata
    score: PositiveFloat
    values: List

class QueryResponse(BaseModel):
    matches: List[PineconeUser]

class SessionCreateRequest(BaseModel):
    user_id: str
