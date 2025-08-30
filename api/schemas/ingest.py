from typing import Optional

from pydantic import BaseModel


class IngestRequest(BaseModel):
    """Request model for document ingestion."""

    tenant_id: Optional[str] = None
    safe_mode: bool = False


class IngestResponse(BaseModel):
    """Response model for document ingestion."""

    job_id: int
    status: str
    message: str = "Document uploaded successfully"


class JobStatusResponse(BaseModel):
    """Response model for job status."""

    job_id: int
    type: str
    status: str
    progress: int
    error: Optional[str] = None
    document_id: int
    created_at: str
    updated_at: str


class JobInfo(BaseModel):
    """Job information model."""

    id: int
    type: str
    status: str
    progress: int
    error: Optional[str] = None
    document_id: int
    created_at: str
    updated_at: str


class DocumentStatusResponse(BaseModel):
    """Response model for document status with all jobs."""

    document_id: int
    status: str
    jobs: list[JobInfo]
