"""Query schemas."""

from typing import List, Optional

from pydantic import BaseModel


class QueryRequest(BaseModel):
    """Query request."""

    query: str
    top_k: int = 10
    rerank: bool = False
    max_ctx: Optional[int] = None


class QueryMatch(BaseModel):
    """Query match result."""

    doc_id: int
    chunk_id: int
    page: Optional[int] = None
    score: float
    snippet: str
    breadcrumbs: Optional[List[str]] = None


class QueryUsage(BaseModel):
    """Query usage statistics."""

    in_tokens: int
    out_tokens: int


class QueryResponse(BaseModel):
    """Query response."""

    matches: List[QueryMatch] = []
    usage: QueryUsage
    query: str
