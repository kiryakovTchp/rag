"""Embedding tasks for Celery."""

import logging
from typing import List

from celery import current_task
from sqlalchemy.orm import Session

from db.models import Document, Chunk, Job
from db.session import SessionLocal
from services.embed.provider import EmbeddingProvider
from services.index.pgvector import PGVectorIndex

logger = logging.getLogger(__name__)


def embed_document(document_id: int) -> dict:
    """Embed document chunks.
    
    Args:
        document_id: Document ID to embed
        
    Returns:
        Dict with status and metadata
    """
    db = SessionLocal()
    try:
        # Get document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # Get or create embed job
        job = db.query(Job).filter(
            Job.document_id == document_id,
            Job.type == "embed"
        ).first()
        
        if not job:
            job = Job(
                type="embed",
                status="running",
                progress=0,
                document_id=document_id
            )
            db.add(job)
            db.commit()
            db.refresh(job)
        else:
            job.status = "running"
            job.progress = 0
            db.commit()
        
        logger.info(f"Starting embed job {job.id} for document {document_id}")
        
        # Get chunks without embeddings
        chunks = db.query(Chunk).filter(
            Chunk.document_id == document_id
        ).all()
        
        if not chunks:
            logger.warning(f"No chunks found for document {document_id}")
            job.status = "done"
            job.progress = 100
            db.commit()
            return {"status": "success", "message": "No chunks to embed"}
        
        # Initialize services
        embedder = EmbeddingProvider()
        index = PGVectorIndex()
        
        # Process chunks in batches
        batch_size = 64
        total_chunks = len(chunks)
        processed = 0
        
        for i in range(0, total_chunks, batch_size):
            batch_chunks = chunks[i:i + batch_size]
            
            # Update progress
            progress = int((processed / total_chunks) * 100)
            job.progress = progress
            db.commit()
            
            # Get chunk texts
            chunk_texts = [chunk.text for chunk in batch_chunks]
            chunk_ids = [chunk.id for chunk in batch_chunks]
            
            # Generate embeddings
            logger.info(f"Generating embeddings for batch {i//batch_size + 1}")
            embeddings = embedder.embed_texts(chunk_texts)
            
            if len(embeddings) != len(batch_chunks):
                raise ValueError(f"Embedding count mismatch: {len(embeddings)} != {len(batch_chunks)}")
            
            # Upsert embeddings
            provider = embedder.get_provider()
            index.upsert_embeddings(chunk_ids, embeddings, provider)
            
            processed += len(batch_chunks)
            logger.info(f"Processed {processed}/{total_chunks} chunks")
        
        # Update job as done
        job.status = "done"
        job.progress = 100
        db.commit()
        
        logger.info(f"Completed embed job {job.id} for document {document_id}")
        
        return {
            "status": "success",
            "document_id": document_id,
            "chunks_processed": total_chunks,
            "provider": provider
        }
        
    except Exception as e:
        logger.error(f"Error in embed_document {document_id}: {str(e)}")
        
        # Update job as failed
        if 'job' in locals():
            job.status = "error"
            job.error = str(e)
            db.commit()
        
        raise
    finally:
        db.close()
