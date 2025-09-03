from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from api.auth import get_current_user_dict
from api.dependencies.db import get_db_lazy
from api.schemas.ingest import DocumentStatusResponse, IngestResponse, JobStatusResponse
from services.ingest.service import IngestService

router = APIRouter()

_DEFAULT_FILE = File(...)


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    file: UploadFile = _DEFAULT_FILE,
    tenant_id: Optional[str] = Form(None),
    safe_mode: bool = Form(False),
    db: Session = Depends(get_db_lazy),
    user: dict = Depends(get_current_user_dict),
) -> IngestResponse:
    """Upload and ingest a document."""
    # Get user info
    user_tenant_id = user["tenant_id"]
    user_id = user["user_id"]

    # Use user's tenant_id if not provided
    if not tenant_id:
        tenant_id = user_tenant_id

    # Check quota (rate limiting is handled by middleware)
    # await check_quota(tenant_id, estimated_tokens)
    # Validate file type
    allowed_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/markdown",
        "text/html",
        "text/plain",
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
    job_id = await service.ingest_document(file, tenant_id, safe_mode)

    return IngestResponse(
        job_id=job_id, status="queued", message="Document uploaded successfully"
    )


@router.get("/ingest/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: int, db: Session = Depends(get_db_lazy)
) -> JobStatusResponse:
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


@router.get("/ingest/document/{document_id}", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: int, db: Session = Depends(get_db_lazy)
) -> DocumentStatusResponse:
    """Get document status with all jobs."""
    service = IngestService(db)
    document_status = service.get_document_status(document_id)

    if not document_status:
        raise HTTPException(status_code=404, detail="Document not found")

    return document_status
