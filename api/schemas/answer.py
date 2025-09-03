"""Answer generation schemas."""

from typing import Optional

from pydantic import BaseModel


class AnswerRequest(BaseModel):
    """Request for answer generation."""

    query: str
    top_k: int = 10
    rerank: bool = False
    max_ctx: int = 4000
    model: str = "gemini-pro"
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout_s: int = 60


class Citation(BaseModel):
    """Citation information."""

    doc_id: int
    chunk_id: int
    page: Optional[int] = None
    score: float
    snippet: str
    breadcrumbs: list[str] = []


class UsageInfo(BaseModel):
    """Usage information for answer generation."""

    provider: Optional[str] = None
    model: Optional[str] = None
    in_tokens: Optional[int] = None
    out_tokens: Optional[int] = None
    latency_ms: Optional[int] = None
    cost_usd: Optional[float] = None


class AnswerResponse(BaseModel):
    """Response from answer generation."""

    answer: str
    citations: list[Citation] = []
    usage: Optional[UsageInfo] = None
