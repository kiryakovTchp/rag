"""Query schemas."""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, model_validator


class QueryRequest(BaseModel):
    """Query request."""

    model_config = ConfigDict(extra="allow")

    query: str
    # Поддержка старого фронта, который отправляет поле "question"
    question: Optional[str] = None
    top_k: int = 10
    rerank: bool = False
    max_ctx: Optional[int] = None

    @model_validator(mode="before")
    @classmethod
    def support_question_field(cls, data):  # type: ignore[no-untyped-def]
        if isinstance(data, dict) and "query" not in data and "question" in data:
            # Перекладываем значение question в query
            data = {**data, "query": data.get("question")}
        return data

    @model_validator(mode="after")
    def validate_ranges(self):  # type: ignore[no-untyped-def]
        if not self.query or not self.query.strip():
            raise ValueError("query must not be empty")
        if not (1 <= int(self.top_k) <= 200):
            raise ValueError("top_k must be between 1 and 200")
        if self.max_ctx is not None and int(self.max_ctx) > 4000:
            raise ValueError("max_ctx must be <= 4000")
        return self


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
