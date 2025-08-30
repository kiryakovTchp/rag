"""Dense retriever using embeddings."""

import re
from typing import List

from db.models import Chunk
from db.session import SessionLocal
from services.embed.provider import EmbeddingProvider
from services.index.pgvector import PGVectorIndex
from services.retrieve.types import ChunkWithScore


class DenseRetriever:
    """Dense retriever using embeddings and pgvector."""
    
    def __init__(self):
        """Initialize dense retriever."""
        self.embedder = EmbeddingProvider()
        self.index = PGVectorIndex()
    
    def search(self, query: str, top_k: int) -> List[ChunkWithScore]:
        """Search for relevant chunks.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of chunks with scores and metadata
        """
        # Embed query
        query_vector = self.embedder.embed_single(query)
        
        # Search in vector index
        results = self.index.search(query_vector, top_k)
        
        # Enrich with metadata
        enriched_results = []
        db = SessionLocal()
        
        try:
            for chunk_id, score in results:
                chunk = db.query(Chunk).filter(Chunk.id == chunk_id).first()
                if chunk:
                    enriched_results.append(self._enrich_chunk(chunk, score))
        finally:
            db.close()
        
        return enriched_results
    
    def _enrich_chunk(self, chunk: Chunk, score: float) -> ChunkWithScore:
        """Enrich chunk with metadata.
        
        Args:
            chunk: Database chunk
            score: Relevance score
            
        Returns:
            Enriched chunk with metadata
        """
        # Extract breadcrumbs from header_path
        breadcrumbs = []
        if chunk.header_path:
            breadcrumbs = [str(item) for item in chunk.header_path]
        
        # Create snippet (truncate at sentence boundary)
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
