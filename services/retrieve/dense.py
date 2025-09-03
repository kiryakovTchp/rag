"""Dense retriever using embeddings."""

from db.models import Chunk
from services.embed.provider import EmbeddingProvider
from services.index.pgvector import PGVectorIndex
from services.retrieve.types import ChunkWithScore


class DenseRetriever:
    """Dense retriever using vector similarity search."""

    def __init__(self, embed_provider: str = "workers_ai"):
        """Initialize dense retriever."""
        self.embedder = EmbeddingProvider(embed_provider)
        self.index = PGVectorIndex()

    def search(self, query: str, top_k: int) -> list[ChunkWithScore]:
        """Search for relevant chunks.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of chunks with scores
        """
        # Embed query
        query_vector = self.embedder.embed_single(query)

        # Search index
        results = self.index.search(query_vector, top_k)

        if not results:
            return []

        # Get chunks from database
        chunk_ids = [chunk_id for chunk_id, _ in results]
        chunks = self._get_chunks(chunk_ids)

        # Create results
        search_results = []
        for (_, score), chunk in zip(results, chunks):
            if chunk:
                search_results.append(
                    ChunkWithScore(
                        chunk_id=chunk.id,
                        doc_id=chunk.document_id,
                        page=chunk.page,
                        score=score,
                        snippet=chunk.text[:300],
                        breadcrumbs=[],
                    )
                )

        return search_results

    def _get_chunks(self, chunk_ids: list[int]) -> list[Chunk]:
        """Get chunks from database."""
        try:
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
