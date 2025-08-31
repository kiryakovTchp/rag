import os
import tempfile
import uuid
from typing import Optional

from fastapi import UploadFile
from sqlalchemy.orm import Session

from db.models import Document, Job
from storage.r2 import ObjectStore
from workers.tasks.parse import parse_document


class IngestService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.storage = ObjectStore()

    def ingest_document(
        self, file: UploadFile, tenant_id: Optional[str] = None, safe_mode: bool = False
    ) -> int:
        """
        Ingest a document: save to S3, create Document and Job records.

        Returns:
            int: The job ID for tracking progress
        """
        # Save file to temporary location
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = file.file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            # Generate unique key for S3
            file_extension = os.path.splitext(file.filename or "unknown")[1]
            s3_key = f"documents/{uuid.uuid4()}{file_extension}"

            # Upload to S3
            storage_uri = self.storage.put_file(temp_file_path, s3_key)

            # Create Document record
            document = Document(
                name=file.filename or "unknown",
                mime=file.content_type or "application/octet-stream",
                storage_uri=storage_uri,
                status="uploaded",
            )
            self.db.add(document)
            self.db.flush()  # Get the ID

            # Create parse job
            job = Job(type="parse", status="queued", progress=0, document_id=document.id)
            self.db.add(job)
            self.db.commit()

            # Trigger parse task
            parse_document.apply_async(args=[document.id, tenant_id], queue="parse")

            return job.id

        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)

    def get_job_status(self, job_id: int) -> Optional[Job]:
        """Get job status by ID."""
        result: Optional[Job] = self.db.query(Job).filter(Job.id == job_id).first()
        return result

    def get_document_status(self, document_id: int):
        """Get document status with all jobs."""
        from api.schemas.ingest import DocumentStatusResponse, JobInfo
        
        # Get document
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return None
        
        # Get all jobs for this document
        jobs = self.db.query(Job).filter(Job.document_id == document_id).all()
        
        # Convert jobs to JobInfo
        job_infos = []
        for job in jobs:
            job_infos.append(JobInfo(
                id=job.id,
                type=job.type,
                status=job.status,
                progress=job.progress,
                error=job.error,
                document_id=job.document_id,
                created_at=job.created_at.isoformat() if job.created_at else "",
                updated_at=job.updated_at.isoformat() if job.updated_at else "",
            ))
        
        return DocumentStatusResponse(
            document_id=document_id,
            status=document.status,
            jobs=job_infos
        )
