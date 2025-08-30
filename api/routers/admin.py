"""Admin API router."""

from fastapi import APIRouter, HTTPException, Header
from typing import Optional

from workers.tasks.index import index_document_embeddings

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/reindex/{document_id}")
async def reindex_document(
    document_id: int,
    authorization: Optional[str] = Header(None)
) -> dict:
    """Reindex document embeddings.
    
    Args:
        document_id: Document ID to reindex
        authorization: Authorization header (placeholder)
        
    Returns:
        Task result
    """
    # Simple auth check (placeholder)
    if not authorization or authorization != "Bearer admin-token":
        raise HTTPException(
            status_code=401,
            detail="Unauthorized. Use 'Bearer admin-token' header."
        )
    
    # Trigger reindex task
    task = index_document_embeddings.delay(document_id)
    
    return {
        "status": "queued",
        "document_id": document_id,
        "task_id": task.id
    }
