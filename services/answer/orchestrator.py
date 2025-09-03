"""Answer generation orchestrator."""

import time
from collections.abc import Iterator
from typing import Optional

from sqlalchemy.orm import Session

from db.models import Chunk
from services.answer.logging import log_answer_usage
from services.cache.answers import AnswerCache
from services.embed.provider import EmbeddingProvider
from services.index.pgvector import PGVectorIndex
from services.llm import get_llm_provider
from services.prompt.answer import build_messages
from services.retrieve.rerank import WorkersAIReranker


class AnswerOrchestrator:
    """Orchestrates the answer generation pipeline."""

    def __init__(self, db: Session):
        """Initialize orchestrator."""
        self.db = db
        self.embedder = EmbeddingProvider()
        self.index = PGVectorIndex()
        self.llm = get_llm_provider()
        self.reranker = WorkersAIReranker()
        self.cache = AnswerCache()

    def generate_answer(
        self,
        query: str,
        top_k: int = 10,
        rerank: bool = False,
        max_ctx_tokens: int = 2000,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        timeout_s: int = 30,
        tenant_id: Optional[str] = None,
    ) -> dict:
        """Generate a single answer.

        Args:
            query: User query
            top_k: Number of chunks to retrieve
            rerank: Whether to apply reranking
            max_ctx_tokens: Maximum context tokens
            model: LLM model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            timeout_s: Timeout in seconds
            tenant_id: Tenant ID for logging

        Returns:
            Dict with answer, citations, and usage

        Raises:
            Exception: If no relevant context found or generation fails
        """
        start_time = time.time()

        # Check cache first
        model = model or "gemini-2.5-flash"
        cached_result = self.cache.get(
            tenant_id, query, top_k, rerank, max_ctx_tokens, model
        )
        if cached_result:
            return cached_result

        # Retrieve relevant chunks
        query_embedding = self.embedder.embed_single(query)
        search_results = self.index.search(query_embedding, top_k=top_k)

        if not search_results:
            raise Exception("No relevant context found")

        # Get chunks from database
        chunk_ids = [chunk_id for chunk_id, _ in search_results]
        chunks = self.db.query(Chunk).filter(Chunk.id.in_(chunk_ids)).all()

        # Create chunk_id -> chunk mapping
        chunk_map = {chunk.id: chunk for chunk in chunks}

        # Apply reranking if requested
        if rerank and len(chunks) > 1:
            # Get ordered chunk IDs from search results
            ordered_chunk_ids = [chunk_id for chunk_id, _ in search_results]

            # Prepare pairs for reranking
            pairs = [
                (query, chunk_map[chunk_id].text) for chunk_id in ordered_chunk_ids
            ]
            reranked_indices = self.reranker.rerank(pairs, top_k=len(pairs))

            # Reorder chunks based on reranking using chunk IDs
            reranked_chunks = [
                chunk_map[ordered_chunk_ids[i]]
                for i in reranked_indices
                if i < len(ordered_chunk_ids)
            ]
        else:
            reranked_chunks = chunks

        # Build messages for LLM
        messages, remaining_tokens = build_messages(
            query, reranked_chunks, max_ctx_tokens
        )

        # Generate answer
        answer, usage = self.llm.generate(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout_s=timeout_s,
        )

        # Build citations
        citations = []
        for chunk_id, score in search_results:
            if chunk_id in chunk_map:
                chunk = chunk_map[chunk_id]
                citations.append(
                    {
                        "doc_id": chunk.document_id,
                        "chunk_id": chunk.id,
                        "page": chunk.page,
                        "score": score,
                    }
                )

        # Cache result
        self.cache.set(
            tenant_id,
            query,
            top_k,
            rerank,
            max_ctx_tokens,
            model,
            answer,
            citations,
            usage,
        )

        # Log usage
        if tenant_id:
            log_answer_usage(
                self.db,
                tenant_id=tenant_id,
                query=query,
                provider=usage["provider"],
                model=usage["model"],
                in_tokens=usage["in_tokens"],
                out_tokens=usage["out_tokens"],
                latency_ms=usage["latency_ms"],
                cost_usd=usage.get("cost_usd"),
            )

        return {"answer": answer, "citations": citations, "usage": usage}

    def stream_answer(
        self,
        query: str,
        top_k: int = 10,
        rerank: bool = False,
        max_ctx_tokens: int = 2000,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        timeout_s: int = 30,
        tenant_id: Optional[str] = None,
    ) -> Iterator[dict]:
        """Generate streaming answer.

        Args:
            query: User query
            top_k: Number of chunks to retrieve
            rerank: Whether to apply reranking
            max_ctx_tokens: Maximum context tokens
            model: LLM model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            timeout_s: Timeout in seconds
            tenant_id: Tenant ID for logging

        Yields:
            Dict with chunk text or final data

        Raises:
            Exception: If no relevant context found or generation fails
        """
        start_time = time.time()

        # Retrieve relevant chunks (same as generate_answer)
        query_embedding = self.embedder.embed_single(query)
        search_results = self.index.search(query_embedding, top_k=top_k)

        if not search_results:
            raise Exception("No relevant context found")

        # Get chunks from database
        chunk_ids = [chunk_id for chunk_id, _ in search_results]
        chunks = self.db.query(Chunk).filter(Chunk.id.in_(chunk_ids)).all()

        # Create chunk_id -> chunk mapping
        chunk_map = {chunk.id: chunk for chunk in chunks}

        # Apply reranking if requested
        if rerank and len(chunks) > 1:
            # Get ordered chunk IDs from search results
            ordered_chunk_ids = [chunk_id for chunk_id, _ in search_results]

            # Prepare pairs for reranking
            pairs = [
                (query, chunk_map[chunk_id].text) for chunk_id in ordered_chunk_ids
            ]
            reranked_indices = self.reranker.rerank(pairs, top_k=len(pairs))

            # Reorder chunks based on reranking using chunk IDs
            reranked_chunks = [
                chunk_map[ordered_chunk_ids[i]]
                for i in reranked_indices
                if i < len(ordered_chunk_ids)
            ]
        else:
            reranked_chunks = chunks

        # Build messages for LLM
        messages, remaining_tokens = build_messages(
            query, reranked_chunks, max_ctx_tokens
        )

        # Build citations
        citations = []
        for chunk_id, score in search_results:
            if chunk_id in chunk_map:
                chunk = chunk_map[chunk_id]
                citations.append(
                    {
                        "doc_id": chunk.document_id,
                        "chunk_id": chunk.id,
                        "page": chunk.page,
                        "score": score,
                    }
                )

        # Stream answer
        model = model or "gemini-2.5-flash"
        stream = self.llm.stream(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout_s=timeout_s,
        )

        # Yield text chunks
        for chunk_text in stream:
            yield {"type": "chunk", "text": chunk_text}

        # Calculate final usage
        latency_ms = int((time.time() - start_time) * 1000)
        usage = {
            "in_tokens": None,  # Will be updated if available
            "out_tokens": None,
            "latency_ms": latency_ms,
            "provider": "gemini",
            "model": model,
            "cost_usd": None,
        }

        # Log usage
        if tenant_id:
            log_answer_usage(
                self.db,
                tenant_id=tenant_id,
                query=query,
                provider=usage["provider"],
                model=usage["model"],
                in_tokens=usage["in_tokens"],
                out_tokens=usage["out_tokens"],
                latency_ms=usage["latency_ms"],
                cost_usd=usage.get("cost_usd"),
            )

        # Yield final data
        yield {"type": "done", "citations": citations, "usage": usage}
