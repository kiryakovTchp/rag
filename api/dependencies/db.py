"""Database dependencies with lazy imports."""

from collections.abc import Generator

from fastapi import HTTPException
from sqlalchemy.orm import Session


def get_db_lazy() -> Generator[Session, None, None]:
    """Lazy database dependency that handles import errors gracefully."""
    try:
        from db.session import get_db

        yield from get_db()
    except ImportError:
        raise HTTPException(
            status_code=503, detail="Database service temporarily unavailable"
        )
