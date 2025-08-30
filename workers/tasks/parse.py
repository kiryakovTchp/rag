import logging
import os
import tempfile

from db.models import Document, Element, Job
from db.session import SessionLocal
from services.parsing.office import OfficeParser
from services.parsing.pdf import PDFParser
from services.parsing.tables import TableParser
from storage.r2 import ObjectStore
from workers.app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def parse_document(self, document_id: int) -> dict:
    """Parse document into elements."""
    logger.info(f"Starting parse task for document {document_id}")
    db = SessionLocal()
    storage = ObjectStore()

    try:
        # Get document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise Exception(f"Document {document_id} not found")

        logger.info(f"Processing document: {document.name} ({document.mime})")

        # Update job status
        job = db.query(Job).filter(Job.document_id == document_id, Job.type == "parse").first()
        if job:
            job.status = "running"
            job.progress = 10
            db.commit()
            logger.info(f"Updated job {job.id} status to running, progress: 10%")

        # Download file from S3
        logger.info("Downloading file from S3...")
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # Extract key from storage_uri (remove s3://bucket/ prefix)
            key = document.storage_uri.replace(f"s3://{storage.bucket}/", "")
            storage.get_file(key, temp_file.name)
            temp_file_path = temp_file.name

        try:
            # Parse based on file type
            elements = []
            logger.info(f"Parsing document with mime type: {document.mime}")

            if document.mime == "application/pdf":
                logger.info("Using PDF parser")
                pdf_parser = PDFParser()
                elements = pdf_parser.parse_to_elements(temp_file_path)
            else:
                logger.info("Using Office parser")
                office_parser = OfficeParser()
                elements = office_parser.parse_to_elements(temp_file_path)

            logger.info(f"Parsed {len(elements)} elements")

            # Update progress
            if job:
                job.progress = 50
                db.commit()
                logger.info(f"Updated job {job.id} progress: 50%")

            # Extract tables if any
            logger.info("Extracting tables...")
            table_parser = TableParser()
            table_elements = table_parser.extract_tables(temp_file_path, document.mime)
            elements.extend(table_elements)
            logger.info(f"Extracted {len(table_elements)} table elements")

            # Save elements to database
            logger.info("Saving elements to database...")
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

            db.commit()
            logger.info(f"Saved {len(elements)} elements to database")

            # Update progress
            if job:
                job.progress = 70
                db.commit()
                logger.info(f"Updated job {job.id} progress: 70%")

            # Create chunk job
            chunk_job = Job(type="chunk", status="queued", progress=0, document_id=document_id)
            db.add(chunk_job)
            db.commit()
            logger.info(f"Created chunk job {chunk_job.id}")

            # Update parse job as done
            if job:
                job.status = "done"
                job.progress = 100
                db.commit()
                logger.info(f"Updated job {job.id} status to done, progress: 100%")

            # Trigger chunking task
            from workers.tasks.chunk import chunk_document

            chunk_document.delay(document_id)
            logger.info(f"Triggered chunk task for document {document_id}")

            return {
                "status": "success",
                "document_id": document_id,
                "elements_count": len(elements),
            }

        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
            logger.info("Cleaned up temporary file")

    except Exception as e:
        logger.error(f"Error in parse task for document {document_id}: {e}")
        # Update job status to error
        if job:
            job.status = "error"
            job.error = str(e)
            db.commit()
            logger.error(f"Updated job {job.id} status to error: {e}")
        raise
    finally:
        db.close()
        logger.info(f"Completed parse task for document {document_id}")
