"""Admin API router."""

from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException

from api.config import Settings, get_settings
from workers.tasks.index import index_document_embeddings

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/reindex/{document_id}")
async def reindex_document(
    document_id: int,
    authorization: Optional[str] = Header(None),
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> dict:
    """Reindex document embeddings.

    Args:
        document_id: Document ID to reindex
        authorization: Authorization header with ADMIN_API_TOKEN

    Returns:
        Task result
    """
    # Check admin token from environment
    expected_token = settings.admin_api_token
    if not expected_token or authorization != f"Bearer {expected_token}":
        raise HTTPException(
            status_code=401,
            detail="Unauthorized. Provide valid ADMIN_API_TOKEN in the Authorization header.",
        )

    # Trigger reindex task
    task = index_document_embeddings.delay(document_id)

    return {"status": "queued", "document_id": document_id, "task_id": task.id}
