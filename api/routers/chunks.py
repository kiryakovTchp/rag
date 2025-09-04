"""Chunk retrieval endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.dependencies.db import get_db_lazy

router = APIRouter(tags=["chunks"])


@router.get("/chunks/{chunk_id}")
async def get_chunk(chunk_id: int, db: Session = Depends(get_db_lazy)) -> dict:
    """Return chunk text and metadata by id."""
    try:
        from db.models import Chunk
    except ImportError as e:
        raise HTTPException(status_code=503, detail="Database unavailable") from e

    chunk = db.query(Chunk).filter(Chunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found")

    return {
        "id": int(chunk.id),
        "doc_id": int(chunk.document_id),
        "page": int(chunk.page) if chunk.page is not None else None,
        "text": chunk.text,
        "breadcrumbs": [str(b) for b in (chunk.header_path or [])],
    }
