import os
import tempfile

from db.models import Document, Element, Job
from db.session import SessionLocal

# TODO: Import parsers when they're implemented
# from services.parsing.pdf import PDFParser
# from services.parsing.office import OfficeParser
# from services.parsing.tables import TableParser
from storage.r2 import ObjectStore
from workers.app import celery_app


@celery_app.task(bind=True)
def parse_document(self, document_id: int) -> dict:
    """Parse document into elements."""
    db = SessionLocal()
    storage = ObjectStore()

    try:
        # Get document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise Exception(f"Document {document_id} not found")

        # Update job status
        job = db.query(Job).filter(Job.document_id == document_id, Job.type == "parse").first()
        if job:
            job.status = "running"
            job.progress = 10
            db.commit()

        # Download file from S3
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            storage.get_file(document.storage_uri.split("/")[-1], temp_file.name)
            temp_file_path = temp_file.name

        try:
            # Parse based on file type (placeholder implementation)
            elements = []

            # TODO: Implement actual parsing
            # For now, create a simple text element
            with open(temp_file_path, encoding="utf-8", errors="ignore") as f:
                content = f.read()

            elements.append(
                {
                    "type": "text",
                    "text": content[:1000] + "..." if len(content) > 1000 else content,
                    "page": 1,
                    "bbox": None,
                }
            )

            # Update progress
            if job:
                job.progress = 50
                db.commit()

            # Save elements to database
            for element_data in elements:
                element = Element(
                    document_id=document_id,
                    type=element_data["type"],
                    page=element_data.get("page"),
                    bbox=element_data.get("bbox"),
                    table_id=element_data.get("table_id"),
                    text=element_data["text"],
                )
                db.add(element)

            # Update progress
            if job:
                job.progress = 70
                db.commit()

            # Create chunk job
            chunk_job = Job(type="chunk", status="queued", progress=0, document_id=document_id)
            db.add(chunk_job)
            db.commit()

            # Update parse job as done
            if job:
                job.status = "done"
                job.progress = 100
                db.commit()

            # Trigger chunking task
            from workers.tasks.chunk import chunk_document

            chunk_document.delay(document_id)

            return {
                "status": "success",
                "document_id": document_id,
                "elements_count": len(elements),
            }

        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)

    except Exception as e:
        # Update job status to error
        if job:
            job.status = "error"
            job.error = str(e)
            db.commit()
        raise
    finally:
        db.close()
