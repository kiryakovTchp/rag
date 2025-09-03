"""Query schemas."""

from pydantic import BaseModel


class QueryRequest(BaseModel):
    """Query request."""

    query: str
    top_k: int = 10
    rerank: bool = False


class QueryResponse(BaseModel):
    """Query response."""

    results: list[dict] = []
    total: int = 0
    query: str
