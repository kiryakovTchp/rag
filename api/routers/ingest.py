import uuid

from fastapi import APIRouter, File, UploadFile

router = APIRouter()

_DEFAULT_FILE = File(...)


@router.post("/ingest")
async def ingest_document(file: UploadFile = _DEFAULT_FILE) -> dict[str, str]:
    # TODO: Implement actual ingestion logic
    job_id = str(uuid.uuid4())
    return {"job_id": job_id, "status": "queued"}
