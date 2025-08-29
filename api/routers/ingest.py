from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from api.deps import get_db
from api.schemas.ingest import IngestResponse, JobStatusResponse
from services.ingest.service import IngestService

router = APIRouter()

_DEFAULT_FILE = File(...)
_GET_DB = Depends(get_db)


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    file: UploadFile = _DEFAULT_FILE,
    tenant_id: Optional[str] = Form(None),
    safe_mode: bool = Form(False),
    db: Session = _GET_DB,
) -> IngestResponse:
    """Upload and ingest a document."""
    # Validate file type
    allowed_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/markdown",
        "text/html",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/csv",
    ]

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Supported types: {allowed_types}",
        )

    # Process document
    service = IngestService(db)
    job_id = service.ingest_document(file, tenant_id, safe_mode)

    return IngestResponse(job_id=job_id, status="queued", message="Document uploaded successfully")


@router.get("/ingest/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: int, db: Session = _GET_DB) -> JobStatusResponse:
    """Get job status by ID."""
    service = IngestService(db)
    job = service.get_job_status(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(
        job_id=job.id,
        type=job.type,
        status=job.status,
        progress=job.progress,
        error=job.error,
        document_id=job.document_id,
        created_at=job.created_at.isoformat() if job.created_at else "",
        updated_at=job.updated_at.isoformat() if job.updated_at else "",
    )
