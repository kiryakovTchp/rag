"""Embedding tasks for Celery."""

import logging
import os
import asyncio
from typing import List

import numpy as np
from celery import current_task
from sqlalchemy.orm import Session

from db.models import Document, Chunk, Job
from db.session import SessionLocal
from services.embed.provider import EmbeddingProvider
from services.index.pgvector import PGVectorIndex
from workers.app import celery_app
from api.websocket import emit_job_event_sync
from services.job_manager import job_manager

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, queue="embed")
def embed_document(self, document_id: int, tenant_id: str = None) -> dict:
    """Embed document chunks.
    
    Args:
        document_id: Document ID to embed
        
    Returns:
        Dict with status and metadata
    """
    """
    Считает эмбеддинги для всех чанков документа и апсерчит в embeddings.
    Обновляет Job(type='embed') progress 0→100, status -> done|failed.
    """
    session = SessionLocal()
    try:
        # 1) найти/создать embed-job для документа
        document = session.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        job = session.query(Job).filter(
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
            session.add(job)
            session.commit()
            session.refresh(job)
        else:
            job.status = "running"
            job.progress = 0
            session.commit()
        
        logger.info(f"Starting embed job {job.id} for document {document_id}")
        
        # Emit WebSocket event
        if tenant_id:
            asyncio.create_task(job_manager.job_started(job.id, tenant_id, document_id, "embed"))
        
        # 2) выбрать чанки без эмбеддингов или все (идемпотентно)
        chunks = session.query(Chunk).filter(
            Chunk.document_id == document_id
        ).all()
        
        if not chunks:
            logger.warning(f"No chunks found for document {document_id}")
            job.status = "done"
            job.progress = 100
            session.commit()
            return {"document_id": document_id, "status": "done", "message": "No chunks to embed"}
        
        # 3) батчами по 64 получить вектора (float32, shape=(N,1024))
        embedder = EmbeddingProvider()
        index = PGVectorIndex()
        
        batch_size = 64
        total_chunks = len(chunks)
        processed = 0
        
        for i in range(0, total_chunks, batch_size):
            batch_chunks = chunks[i:i + batch_size]
            
            chunk_texts = [chunk.text for chunk in batch_chunks]
            chunk_ids = [chunk.id for chunk in batch_chunks]
            
            logger.info(f"Generating embeddings for batch {i//batch_size + 1}")
            embeddings = embedder.embed_texts(chunk_texts)
            
            # Ensure embeddings is numpy array with correct shape
            if not isinstance(embeddings, np.ndarray):
                embeddings = np.array(embeddings, dtype=np.float32)
            
            if embeddings.shape != (len(batch_chunks), 1024):
                raise ValueError(f"Embedding shape mismatch: {embeddings.shape} != ({len(batch_chunks)}, 1024)")
            
            # 4) PGVectorIndex().upsert_embeddings(chunk_ids, vectors, provider='bge-m3'|ENV)
            provider = embedder.get_provider()
            index.upsert_embeddings(chunk_ids, embeddings, provider)
            
            processed += len(batch_chunks)
            
            # 5) обновлять progress по мере батчей
            progress = int((processed / total_chunks) * 100)
            job.progress = progress
            session.commit()
            
            # Emit WebSocket event
            if tenant_id:
                asyncio.create_task(job_manager.job_progress(job.id, progress, tenant_id, document_id, "embed"))
            
            logger.info(f"Processed {processed}/{total_chunks} chunks (progress: {progress}%)")
        
        # 6) status='done'
        job.status = "done"
        job.progress = 100
        session.commit()
        
        # Emit WebSocket event
        if tenant_id:
            asyncio.create_task(job_manager.job_done(job.id, tenant_id, document_id, "embed"))
        
        logger.info(f"Completed embed job {job.id} for document {document_id}")
        
        return {"document_id": document_id, "status": "done", "chunks_processed": total_chunks, "provider": provider}
        
    except Exception as e:
        logger.error(f"Error in embed_document {document_id}: {str(e)}")
        
        # status='failed', error=str(e)
        if 'job' in locals():
            job.status = "error"
            job.error = str(e)
            session.commit()
            
            # Emit WebSocket event
            if tenant_id:
                asyncio.create_task(job_manager.job_failed(job.id, str(e), tenant_id, document_id, "embed"))
        
        raise
    finally:
        session.close()
