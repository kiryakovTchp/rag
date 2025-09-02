"""Authentication and API key management endpoints."""

import hashlib
import secrets
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies.auth import get_current_user
from api.dependencies.db import get_db_lazy
from api.schemas.auth import (
    APIKeyCreate,
    APIKeyList,
    APIKeyResponse,
    TokenResponse,
    UserInfo,
    UserLogin,
    UserRegister,
)
from api.utils.jwt import create_access_token
from api.utils.password import hash_password, verify_password

router = APIRouter()

# Create dependency variables to avoid calling Depends in argument defaults
get_db = get_db_lazy
get_current_user_dep = get_current_user


@router.post("/register", response_model=UserInfo, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister, db: Session = Depends(get_db)  # noqa: B008
):
    """Register a new user with email and password."""
    # Check if user already exists
    from db.models import User

    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    # Create new user
    hashed_password = hash_password(user_data.password)
    new_user = User(email=user_data.email, password_hash=hashed_password, role="user")

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserInfo(
        id=int(new_user.id),
        email=str(new_user.email),
        tenant_id=str(new_user.tenant_id) if new_user.tenant_id else None,
        role=str(new_user.role),
        created_at=new_user.created_at,  # type: ignore
    )


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):  # noqa: B008
    """Login user with email and password."""
    from db.models import User

    # Find user by email
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    # Verify password
    if not verify_password(user_data.password, str(user.password_hash)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    # Create access token
    access_token = create_access_token(
        user_id=int(user.id),
        email=str(user.email),
        tenant_id=str(user.tenant_id) if user.tenant_id else None,
        role=str(user.role),
    )

    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(
    current_user: Any = Depends(get_current_user_dep),  # noqa: B008
):
    """Get current user information."""
    return UserInfo(
        id=int(current_user.id),
        email=str(current_user.email),
        tenant_id=str(current_user.tenant_id) if current_user.tenant_id else None,
        role=str(current_user.role),
        created_at=current_user.created_at,  # type: ignore
    )


@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    api_key_data: APIKeyCreate,
    current_user: Any = Depends(get_current_user_dep),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    """Create a new API key for the current user's tenant."""
    # Generate a secure random API key
    api_key = f"pk_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    # Create API key record
    from db.models import APIKey

    db_api_key = APIKey(
        key_hash=key_hash,
        tenant_id=current_user.tenant_id,
        role=api_key_data.role or "user",
    )

    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)

    # Return the API key only once (it won't be stored in DB)
    return APIKeyResponse(
        id=int(db_api_key.id),
        key=api_key,  # Only returned once
        tenant_id=str(db_api_key.tenant_id),
        role=str(db_api_key.role),
        created_at=db_api_key.created_at,  # type: ignore
    )


@router.get("/api-keys", response_model=list[APIKeyList])
async def list_api_keys(
    current_user: Any = Depends(get_current_user_dep),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    """List all API keys for the current user's tenant."""
    from db.models import APIKey

    api_keys = (
        db.query(APIKey)
        .filter(APIKey.tenant_id == current_user.tenant_id, APIKey.revoked_at.is_(None))
        .all()
    )

    return [
        APIKeyList(
            id=int(key.id),
            tenant_id=str(key.tenant_id),
            role=str(key.role),
            created_at=key.created_at,  # type: ignore
        )
        for key in api_keys
    ]


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: int,
    current_user: Any = Depends(get_current_user_dep),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    """Revoke an API key."""
    from db.models import APIKey

    api_key = (
        db.query(APIKey)
        .filter(
            APIKey.id == key_id,
            APIKey.tenant_id == current_user.tenant_id,
            APIKey.revoked_at.is_(None),
        )
        .first()
    )

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
        )

    api_key.revoked_at = datetime.now(timezone.utc)  # type: ignore
    db.commit()

    return {"message": "API key revoked successfully"}


# Duplicate endpoint removed - using the one above with UserInfo response model
