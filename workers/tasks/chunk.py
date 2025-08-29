from db.models import Chunk, Document, Element, Job
from db.session import SessionLocal

# TODO: Import chunking pipeline when it's implemented
# from services.chunking.pipeline import ChunkingPipeline
from workers.app import celery_app


@celery_app.task(bind=True)
def chunk_document(self, document_id: int) -> dict:
    """Chunk document elements into searchable chunks."""
    db = SessionLocal()

    try:
        # Get document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise Exception(f"Document {document_id} not found")

        # Get chunk job
        job = db.query(Job).filter(Job.document_id == document_id, Job.type == "chunk").first()
        if job:
            job.status = "running"
            job.progress = 70
            db.commit()

        # Get all elements for this document
        elements = db.query(Element).filter(Element.document_id == document_id).all()

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

        # Build chunks using pipeline (placeholder implementation)
        # TODO: Implement actual chunking
        chunks_data = []
        for element in element_data:
            chunks_data.append(
                {
                    "level": "section",
                    "header_path": [],
                    "text": element["text"],
                    "token_count": len(element["text"].split()),  # Simple word count
                    "page": element.get("page"),
                    "element_id": element.get("id"),
                }
            )

        # Update progress
        if job:
            job.progress = 85
            db.commit()

        # Save chunks to database
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

        # Update document status
        document.status = "done"

        # Update job as done
        if job:
            job.status = "done"
            job.progress = 100
            db.commit()

        return {
            "status": "success",
            "document_id": document_id,
            "chunks_count": len(chunks_data),
        }

    except Exception as e:
        # Update job status to error
        if job:
            job.status = "error"
            job.error = str(e)
            db.commit()
        raise
    finally:
        db.close()
