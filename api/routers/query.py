"""Query API router."""

import os
from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from api.schemas.query import QueryRequest, QueryResponse, QueryMatch, QueryUsage
from services.chunking.token import TokenTextSplitter
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
    
    # Initialize services with lazy loading
    try:
        from services.retrieve.hybrid import HybridRetriever
        retriever = HybridRetriever(
            embed_provider=os.getenv("EMBED_PROVIDER", "workers_ai")
        )
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail="Retrieval service temporarily unavailable"
        )
    
    context_builder = ContextBuilder()
    token_splitter = TokenTextSplitter()
    
    # Count input tokens
    in_tokens = token_splitter.count_tokens(request.query)
    
    # Retrieve relevant chunks
    matches = retriever.retrieve(
        query=request.query,
        top_k=request.top_k,
        rerank_k=min(20, request.top_k),
        use_rerank=request.rerank
    )
    
    if not matches:
        return QueryResponse(
            matches=[],
            usage=QueryUsage(in_tokens=in_tokens, out_tokens=0)
        )
    
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
