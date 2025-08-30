"""Types for retriever services."""

from typing import List, TypedDict, Optional


class ChunkWithScore(TypedDict):
    """Chunk with relevance score and metadata."""
    chunk_id: int
    doc_id: int
    page: Optional[int]
    score: float
    snippet: str
    breadcrumbs: List[str]
