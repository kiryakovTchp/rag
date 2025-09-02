"""Hybrid retriever with dense search and optional reranking."""

from typing import List, Optional
import os

import numpy as np

# Lazy imports to prevent startup failures
# from db.models import Chunk
# from db.session import SessionLocal
from services.index.pgvector import PGVectorIndex
from services.retrieve.rerank import WorkersAIReranker
from services.retrieve.types import ChunkWithScore


class HybridRetriever:
    """Hybrid retriever combining dense search with optional reranking."""
    
    def __init__(self, embed_provider: str = None):
        """Initialize hybrid retriever."""
        self.embed_provider = embed_provider or os.getenv("EMBED_PROVIDER", "workers_ai")
        self._embedder = None
        self.index = PGVectorIndex()
        self.reranker = WorkersAIReranker()
    
    def _get_embedder(self):
        """Lazy load embedding provider only when needed."""
        if self._embedder is None:
            try:
                from services.embed.provider import EmbeddingProvider
                self._embedder = EmbeddingProvider(self.embed_provider)
            except ImportError as e:
                raise ImportError(
                    "Embedding service unavailable. "
                    "Check EMBED_PROVIDER configuration."
                ) from e
        return self._embedder
    
    def retrieve(self, query: str, top_k: int = 100, rerank_k: int = 20, 
                 use_rerank: bool = False) -> List[ChunkWithScore]:
        """Retrieve relevant chunks with optional reranking.
        
        Args:
            query: Search query
            top_k: Number of initial results to retrieve
            rerank_k: Number of results to rerank
            use_rerank: Whether to use reranking
            
        Returns:
            List of chunks with scores
        """
        # Embed query
        embedder = self._get_embedder()
        query_vector = embedder.embed_single(query)
        
        # Dense search
        search_results = self.index.search(query_vector, top_k)
        
        if not search_results:
            return []
        
        # Get chunks from database
        chunk_ids = [chunk_id for chunk_id, _ in search_results]
        chunks = self._get_chunks(chunk_ids)
        
        # Create initial results
        results = []
        for (chunk_id, score), chunk in zip(search_results, chunks):
            if chunk:
                results.append(self._create_chunk_with_score(chunk, score))
        
        # Apply reranking if enabled
        if use_rerank and len(results) > 1:
            results = self._apply_reranking(query, results, rerank_k)
        
        return results
    
    def _get_chunks(self, chunk_ids: List[int]) -> List[Optional]:
        """Get chunks from database.
        
        Args:
            chunk_ids: List of chunk IDs
            
        Returns:
            List of chunks (None if not found)
        """
        try:
            from db.models import Chunk
            from db.session import SessionLocal
            
            db = SessionLocal()
            try:
                chunks = db.query(Chunk).filter(Chunk.id.in_(chunk_ids)).all()
                # Create mapping for efficient lookup
                chunk_map = {chunk.id: chunk for chunk in chunks}
                return [chunk_map.get(chunk_id) for chunk_id in chunk_ids]
            finally:
                db.close()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to get chunks from database: {e}")
            return []
    
    def _create_chunk_with_score(self, chunk, score: float) -> ChunkWithScore:
        """Create ChunkWithScore from chunk and score.
        
        Args:
            chunk: Database chunk
            score: Relevance score
            
        Returns:
            ChunkWithScore object
        """
        # Extract breadcrumbs from header_path
        breadcrumbs = []
        if chunk.header_path:
            breadcrumbs = [str(item) for item in chunk.header_path]
        
        # Create snippet
        snippet = self._create_snippet(chunk.text)
        
        return ChunkWithScore(
            chunk_id=chunk.id,
            doc_id=chunk.document_id,
            page=chunk.page,
            score=score,
            snippet=snippet,
            breadcrumbs=breadcrumbs
        )
    
    def _create_snippet(self, text: str, max_length: int = 300) -> str:
        """Create snippet by truncating at sentence boundary.
        
        Args:
            text: Full text
            max_length: Maximum snippet length
            
        Returns:
            Truncated snippet
        """
        if len(text) <= max_length:
            return text
        
        # Find sentence boundaries
        truncated = text[:max_length]
        
        # Try to find last sentence boundary
        sentence_end = max(
            truncated.rfind('. '),
            truncated.rfind('! '),
            truncated.rfind('? '),
            truncated.rfind('\n')
        )
        
        if sentence_end > max_length * 0.7:  # Only if we found a good boundary
            return truncated[:sentence_end + 1].strip()
        
        return truncated.strip()
    
    def _apply_reranking(self, query: str, results: List[ChunkWithScore], 
                        rerank_k: int) -> List[ChunkWithScore]:
        """Apply reranking to top results.
        
        Args:
            query: Search query
            results: Initial search results
            rerank_k: Number of results to rerank
            
        Returns:
            Reranked results
        """
        # Take top rerank_k results
        top_results = results[:rerank_k]
        
        # Prepare pairs for reranking
        pairs = [(query, result["snippet"]) for result in top_results]
        
        # Get reranked indices
        indices = self.reranker.rerank(pairs, rerank_k)
        
        # Reorder results based on reranked indices
        reranked_results = [top_results[i] for i in indices if i < len(top_results)]
        
        # Add remaining results (not reranked)
        remaining_results = results[rerank_k:]
        
        return reranked_results + remaining_results
