"""Query API router."""

import os
from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from api.schemas.query import QueryRequest, QueryResponse, QueryMatch, QueryUsage
from services.chunking.token_splitter import TokenSplitter
from services.retrieve.dense import DenseRetriever
from services.retrieve.rerank import WorkersAIReranker
from services.retrieve.context_builder import ContextBuilder
from services.retrieve.types import ChunkWithScore

router = APIRouter(prefix="/query", tags=["query"])


@router.post("/", response_model=QueryResponse)
async def query(request: QueryRequest) -> QueryResponse:
    """Search for relevant chunks."""
    # Validate rerank availability
    if request.rerank and not os.getenv("RERANK_ENABLED", "false").lower() == "true":
        raise HTTPException(
            status_code=400,
            detail="Reranking is not enabled. Set RERANK_ENABLED=true to enable."
        )
    
    # Initialize services
    retriever = DenseRetriever()
    context_builder = ContextBuilder()
    token_splitter = TokenSplitter()
    
    # Count input tokens
    in_tokens = token_splitter.count_tokens(request.query)
    
    # Search for relevant chunks
    matches = retriever.search(request.query, request.top_k)
    
    if not matches:
        return QueryResponse(
            matches=[],
            usage=QueryUsage(in_tokens=in_tokens, out_tokens=0)
        )
    
    # Apply reranking if enabled
    if request.rerank:
        matches = await _apply_reranking(request.query, matches, request.top_k)
    
    # Build context
    context_matches = context_builder.build(matches, request.max_ctx)
    
    # Count output tokens
    out_tokens = sum(token_splitter.count_tokens(match["snippet"]) for match in context_matches)
    
    # Convert to response format
    response_matches = [_chunk_to_match(match) for match in context_matches]
    
    return QueryResponse(
        matches=response_matches,
        usage=QueryUsage(in_tokens=in_tokens, out_tokens=out_tokens)
    )


async def _apply_reranking(query: str, matches: List[ChunkWithScore], top_k: int) -> List[ChunkWithScore]:
    """Apply reranking to matches."""
    reranker = WorkersAIReranker()
    
    # Prepare pairs for reranking
    pairs = [(query, match["snippet"]) for match in matches]
    
    # Get reranked indices
    indices = reranker.rerank(pairs, top_k)
    
    # Reorder matches based on reranked indices
    reranked_matches = [matches[i] for i in indices if i < len(matches)]
    
    return reranked_matches


def _chunk_to_match(chunk: ChunkWithScore) -> QueryMatch:
    """Convert ChunkWithScore to QueryMatch."""
    return QueryMatch(
        doc_id=chunk["doc_id"],
        chunk_id=chunk["chunk_id"],
        page=chunk["page"],
        score=chunk["score"],
        snippet=chunk["snippet"],
        breadcrumbs=chunk["breadcrumbs"]
    )
