"""Answer API schemas."""

from typing import List, Optional
from pydantic import BaseModel, Field


class Citation(BaseModel):
    """Citation information."""
    
    doc_id: int
    chunk_id: int
    page: Optional[int] = None
    score: float


class Usage(BaseModel):
    """Usage information."""
    
    in_tokens: Optional[int] = None
    out_tokens: Optional[int] = None
    latency_ms: int
    provider: str
    model: str
    cost_usd: Optional[float] = None


class AnswerRequest(BaseModel):
    """Answer generation request."""
    
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(default=10, ge=1, le=50)
    rerank: bool = Field(default=False)
    max_ctx: int = Field(default=2000, ge=100, le=4096)
    model: Optional[str] = Field(default=None, max_length=100)
    temperature: float = Field(default=0.2, ge=0.0, le=1.0)
    max_tokens: int = Field(default=1024, ge=1, le=4096)
    timeout_s: int = Field(default=30, ge=1, le=120)


class AnswerResponse(BaseModel):
    """Answer generation response."""
    
    answer: str
    citations: List[Citation]
    usage: Usage


class StreamChunk(BaseModel):
    """Streaming chunk response."""
    
    type: str = "chunk"
    text: str


class StreamDone(BaseModel):
    """Streaming final response."""
    
    type: str = "done"
    citations: List[Citation]
    usage: Usage
