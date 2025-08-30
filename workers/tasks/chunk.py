import logging

from db.models import Chunk, Document, Element, Job
from db.session import SessionLocal
from services.chunking.pipeline import ChunkingPipeline
from workers.app import celery_app
from workers.tasks.index import index_document_embeddings

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, queue="chunk")
def chunk_document(self, document_id: int) -> dict:
    """Chunk document elements into searchable chunks."""
    logger.info(f"Starting chunk task for document {document_id}")
    db = SessionLocal()

    try:
        # Get document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise Exception(f"Document {document_id} not found")

        logger.info(f"Chunking document: {document.name}")

        # Get chunk job
        job = db.query(Job).filter(Job.document_id == document_id, Job.type == "chunk").first()
        if job:
            job.status = "running"
            job.progress = 70
            db.commit()
            logger.info(f"Updated job {job.id} status to running, progress: 70%")

        # Get all elements for this document
        elements = db.query(Element).filter(Element.document_id == document_id).all()
        logger.info(f"Found {len(elements)} elements to chunk")

        # Convert to dict format for pipeline
        element_data = []
        for element in elements:
            element_data.append(
                {
                    "id": element.id,
                    "type": element.type,
                    "page": element.page,
                    "bbox": element.bbox,
                    "table_id": element.table_id,
                    "text": element.text,
                }
            )

        # Build chunks using pipeline
        logger.info("Building chunks using pipeline...")
        pipeline = ChunkingPipeline()
        chunks_data = pipeline.build_chunks(element_data)
        logger.info(f"Created {len(chunks_data)} chunks")

        # Update progress
        if job:
            job.progress = 85
            db.commit()
            logger.info(f"Updated job {job.id} progress: 85%")

        # Save chunks to database
        logger.info("Saving chunks to database...")
        for chunk_data in chunks_data:
            chunk = Chunk(
                document_id=document_id,
                element_id=chunk_data.get("element_id"),
                level=chunk_data["level"],
                header_path=chunk_data.get("header_path"),
                text=chunk_data["text"],
                token_count=chunk_data["token_count"],
                page=chunk_data.get("page"),
                table_meta=chunk_data.get("table_meta"),
            )
            db.add(chunk)

        db.commit()
        logger.info(f"Saved {len(chunks_data)} chunks to database")

        # Update document status
        document.status = "done"
        db.commit()
        logger.info(f"Updated document {document_id} status to done")

        # Update job as done
        if job:
            job.status = "done"
            job.progress = 100
            db.commit()
            logger.info(f"Updated job {job.id} status to done, progress: 100%")

        # Create embed job and trigger embedding task
        logger.info(f"Creating embed job for document {document_id}")
        embed_job = Job(
            type="embed",
            status="queued",
            progress=0,
            document_id=document_id
        )
        db.add(embed_job)
        db.commit()
        logger.info(f"Created embed job {embed_job.id}")

        # Trigger embedding task
        logger.info(f"Triggering embed task for document {document_id}")
        from workers.tasks.embed import embed_document
        embed_document.apply_async(args=[document_id], queue="embed")

        return {
            "status": "success",
            "document_id": document_id,
            "chunks_count": len(chunks_data),
        }

    except Exception as e:
        logger.error(f"Error in chunk task for document {document_id}: {e}")
        # Update job status to error
        if job:
            job.status = "error"
            job.error = str(e)
            db.commit()
            logger.error(f"Updated job {job.id} status to error: {e}")
        raise
    finally:
        db.close()
