"""Types for retriever services."""

from typing import TypedDict


class ChunkWithScore(TypedDict):
    """Chunk with relevance score."""

    chunk_id: int
    doc_id: int
    page: int
    score: float
    snippet: str
    breadcrumbs: list[str]
