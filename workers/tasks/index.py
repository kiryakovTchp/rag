"""Index embeddings task."""

import logging
import time

from celery import current_task

from db.models import Chunk, Document, Embedding
from db.session import SessionLocal
from services.embed.provider import EmbeddingProvider
from services.index.pgvector import PGVectorIndex
from workers.app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def index_document_embeddings(self, document_id: int) -> dict:
    """Index embeddings for document chunks.

    Args:
        document_id: Document ID to index

    Returns:
        Task result with metrics
    """
    start_time = time.time()

    # Update task status
    current_task.update_state(
        state="RUNNING", meta={"status": "started", "document_id": document_id}
    )

    try:
        # Get document
        db = SessionLocal()
        document = db.query(Document).filter(Document.id == document_id).first()

        if not document:
            raise ValueError(f"Document {document_id} not found")

        logger.info(f"Starting index task for document {document_id}")

        # Get chunks without embeddings
        chunks = (
            db.query(Chunk)
            .filter(
                Chunk.document_id == document_id,
                ~Chunk.id.in_(
                    db.query(Embedding.chunk_id).filter(Embedding.chunk_id == Chunk.id)
                ),
            )
            .all()
        )

        if not chunks:
            logger.info(f"No chunks to index for document {document_id}")
            return {
                "status": "success",
                "document_id": document_id,
                "chunks_indexed": 0,
                "time_taken": time.time() - start_time,
            }

        logger.info(f"Found {len(chunks)} chunks to index")

        # Initialize services
        embedder = EmbeddingProvider()
        index = PGVectorIndex()

        # Get chunk texts
        chunk_texts = [chunk.text for chunk in chunks]

        # Generate embeddings in batches
        all_embeddings = []
        batch_size = embedder.batch_size
        total_chunks = len(chunk_texts)
        processed = 0

        for i in range(0, total_chunks, batch_size):
            batch_texts = chunk_texts[i : i + batch_size]
            batch_embeddings = embedder.embed_texts(batch_texts)
            all_embeddings.extend(batch_embeddings)

            processed += len(batch_texts)

            # Update progress
            progress = int((processed / total_chunks) * 100)
            current_task.update_state(
                state="RUNNING",
                meta={
                    "status": "processing",
                    "document_id": document_id,
                    "progress": progress,
                },
            )

            logger.info(
                f"Processed {processed}/{total_chunks} chunks (progress: {progress}%)"
            )

        # Convert to numpy array
        import numpy as np

        all_embeddings = np.array(all_embeddings, dtype=np.float32)

        # Upsert embeddings
        provider = embedder.get_provider()
        chunk_ids = [chunk.id for chunk in chunks]
        index.upsert_embeddings(chunk_ids, all_embeddings, provider)

        time_taken = time.time() - start_time

        logger.info(f"Indexed {len(chunks)} chunks in {time_taken:.2f}s")

        return {
            "status": "success",
            "document_id": document_id,
            "chunks_indexed": len(chunks),
            "time_taken": time_taken,
            "provider": provider,
        }

    except Exception as e:
        logger.error(f"Index task failed for document {document_id}: {e}")
        current_task.update_state(
            state="FAILURE",
            meta={"status": "error", "document_id": document_id, "error": str(e)},
        )
        raise

    finally:
        db.close()
