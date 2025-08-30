"""Query API schemas."""

from typing import List, Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Query request schema."""
    query: str = Field(..., min_length=1, max_length=1000, description="Search query")
    top_k: int = Field(default=50, ge=1, le=200, description="Number of results to return")
    rerank: bool = Field(default=False, description="Enable reranking")
    max_ctx: int = Field(default=1800, ge=100, le=4000, description="Maximum context tokens")


class QueryMatch(BaseModel):
    """Query match schema."""
    doc_id: int = Field(..., description="Document ID")
    chunk_id: int = Field(..., description="Chunk ID")
    page: Optional[int] = Field(None, description="Page number")
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    snippet: str = Field(..., description="Text snippet")
    breadcrumbs: List[str] = Field(default_factory=list, description="Header breadcrumbs")


class QueryUsage(BaseModel):
    """Query usage metrics."""
    in_tokens: int = Field(..., ge=0, description="Input tokens")
    out_tokens: int = Field(default=0, description="Output tokens")


class QueryResponse(BaseModel):
    """Query response schema."""
    matches: List[QueryMatch] = Field(..., description="Search matches")
    usage: QueryUsage = Field(..., description="Usage metrics")
