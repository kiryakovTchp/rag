"""Authentication middleware for storing user information in request.state."""

import hashlib
import logging

from fastapi import Request

from api.dependencies.db import get_db_lazy
from api.utils.jwt import decode_token
from db.session import set_current_tenant


async def auth_middleware(request: Request, call_next):
    """Middleware to store user information in request.state.

    This middleware runs before other middleware and stores user information
    in request.state for use by metrics, rate limiting, and other components.
    """
    # Initialize user state
    request.state.user = None
    request.state.tenant_id = None

    try:
        logger = logging.getLogger(__name__)
        logger.info("auth_mw start %s %s", request.method, request.url.path)
        # Skip auth for certain paths
        if request.url.path in [
            "/login",
            "/register",
            "/health",
            "/healthz",
            "/docs",
            "/openapi.json",
        ]:
            logger.info("auth_mw skip %s", request.url.path)
            response = await call_next(request)
            return response

        # Try to get user from authorization header
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]

            # Try JWT token first
            try:
                payload = decode_token(token)
                if payload:
                    user_dict = {
                        "tenant_id": payload.get("tenant_id"),
                        "user_id": payload.get("sub"),
                        "role": payload.get("role", "user"),
                        "email": payload.get("email", ""),
                    }
                    request.state.user = user_dict
                    request.state.tenant_id = user_dict.get("tenant_id")
                    set_current_tenant(user_dict.get("tenant_id"))
            except Exception:
                # JWT failed, try API key
                try:
                    db_gen = get_db_lazy()
                    try:
                        db = next(db_gen)
                        # Try to validate API key
                        from db.models import APIKey

                        key_hash = hashlib.sha256(token.encode()).hexdigest()
                        db_key = (
                            db.query(APIKey)
                            .filter(
                                APIKey.key_hash == key_hash, APIKey.revoked_at.is_(None)
                            )
                            .first()
                        )

                        if db_key:
                            user_dict = {
                                "tenant_id": db_key.tenant_id,
                                "user_id": f"api_key_{db_key.id}",
                                "role": db_key.role,
                                "email": "",
                            }
                            request.state.user = user_dict
                            request.state.tenant_id = user_dict.get("tenant_id")
                            set_current_tenant(user_dict.get("tenant_id"))
                    finally:
                        try:
                            next(db_gen)
                        except StopIteration:
                            pass
                except Exception:
                    # API key validation failed
                    pass

        logger.info("auth_mw next %s", request.url.path)
        response = await call_next(request)
        return response

    except Exception:
        # If anything goes wrong, continue without user info
        logger.exception("auth_mw error; proceeding without auth")
        response = await call_next(request)
        return response
