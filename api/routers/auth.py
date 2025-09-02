"""Authentication and API key management endpoints."""

import secrets
import hashlib
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# Lazy imports to prevent startup failures
# from db.session import get_db
# from db.models import APIKey, User
from api.dependencies.auth import get_current_user
from api.schemas.auth import APIKeyCreate, APIKeyResponse, APIKeyList

router = APIRouter()


def get_db_lazy():
    """Lazy database dependency."""
    try:
        from db.session import get_db
        return next(get_db())
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail="Database service temporarily unavailable"
        )


@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    api_key_data: APIKeyCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db_lazy)
):
    """Create a new API key for the current user's tenant."""
    # Lazy import database models
    try:
        from db.models import APIKey, User
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail="Database service temporarily unavailable"
        )
    
    # Generate a secure random API key
    api_key = f"pk_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    # Create API key record
    db_api_key = APIKey(
        key_hash=key_hash,
        tenant_id=current_user.tenant_id,
        role=api_key_data.role or "user"
    )
    
    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)
    
    # Return the API key only once (it won't be stored in DB)
    return APIKeyResponse(
        id=db_api_key.id,
        key=api_key,  # Only returned once
        tenant_id=db_api_key.tenant_id,
        role=db_api_key.role,
        created_at=db_api_key.created_at
    )


@router.get("/api-keys", response_model=List[APIKeyList])
async def list_api_keys(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db_lazy)
):
    """List all API keys for the current user's tenant."""
    # Lazy import database models
    try:
        from db.models import APIKey, User
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail="Database service temporarily unavailable"
        )
    
    api_keys = db.query(APIKey).filter(
        APIKey.tenant_id == current_user.tenant_id,
        APIKey.revoked_at.is_(None)
    ).all()
    
    return [
        APIKeyList(
            id=key.id,
            tenant_id=key.tenant_id,
            role=key.role,
            created_at=key.created_at
        )
        for key in api_keys
    ]


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db_lazy)
):
    """Revoke an API key."""
    # Lazy import database models
    try:
        from db.models import APIKey, User
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail="Database service temporarily unavailable"
        )
    
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.tenant_id == current_user.tenant_id,
        APIKey.revoked_at.is_(None)
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    api_key.revoked_at = datetime.utcnow()
    db.commit()
    
    return {"message": "API key revoked successfully"}


@router.get("/me")
async def get_current_user_info(current_user = Depends(get_current_user)):
    """Get current user information."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "tenant_id": current_user.tenant_id,
        "role": current_user.role
    }
