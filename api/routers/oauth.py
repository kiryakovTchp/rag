"""OAuth routes for external connectors (Google, Notion, Confluence)."""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from api.config import get_settings
from api.dependencies.auth import get_current_user
from api.dependencies.db import get_db_lazy
from api.utils.crypto import encrypt_token

router = APIRouter()

# Dependencies
get_db = get_db_lazy
get_current_user_dep = get_current_user


@router.get("/auth/{provider}/start")
async def oauth_start(
    provider: str, request: Request, current_user: Any = Depends(get_current_user_dep)
):
    state = secrets.token_urlsafe(16)
    # Store state in session
    try:
        request.session["oauth_state"] = state  # type: ignore[attr-defined]
    except Exception:
        pass

    if provider == "google":
        settings = get_settings()
        client_id = settings.google_client_id
        redirect_uri = (
            settings.google_redirect_uri or "http://localhost:8000/auth/google/callback"
        )
        scope = "https://www.googleapis.com/auth/drive.readonly https://www.googleapis.com/auth/documents.readonly openid email profile"
        url = (
            "https://accounts.google.com/o/oauth2/v2/auth?response_type=code"
            f"&client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}&state={state}&access_type=offline&prompt=consent"
        )
        return {"url": url}
    elif provider in ("notion", "confluence"):
        # Stubs: return placeholder URL for now
        return {"url": f"/auth/{provider}/callback?code=dummy&state={state}"}
    else:
        raise HTTPException(status_code=404, detail="Unsupported provider")


@router.get("/auth/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),  # noqa: B008
    current_user: Any = Depends(get_current_user_dep),  # noqa: B008
):
    # CSRF: validate state
    try:
        saved_state = request.session.get("oauth_state")  # type: ignore[attr-defined]
    except Exception:
        saved_state = None
    if not state or not saved_state or state != saved_state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    # Exchange code for tokens
    if provider == "google":
        token_endpoint = "https://oauth2.googleapis.com/token"
        settings = get_settings()
        client_id = settings.google_client_id
        client_secret = settings.google_client_secret
        redirect_uri = (
            settings.google_redirect_uri or "http://localhost:8000/auth/google/callback"
        )
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                token_endpoint,
                data={
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail="Token exchange failed")
            data = resp.json()
            access_token = data.get("access_token")
            refresh_token = data.get("refresh_token")
            expires_in = data.get("expires_in")

        # Store tokens encrypted
        from db.models import OAuthAccount, OAuthToken

        account = OAuthAccount(
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            provider="google",
            account_id=str(current_user.email),
            scopes=["drive.readonly", "documents.readonly"],
        )
        db.add(account)
        db.flush()

        token_row = OAuthToken(
            account_id=account.id,
            tenant_id=current_user.tenant_id,
            access_token_encrypted=encrypt_token(access_token),  # type: ignore[arg-type]
            refresh_token_encrypted=encrypt_token(refresh_token)
            if refresh_token
            else None,
            expires_at=(datetime.now(timezone.utc) + timedelta(seconds=int(expires_in)))
            if expires_in
            else None,
        )
        db.add(token_row)
        db.commit()

        # Trigger initial background sync
        try:
            from workers.tasks.connectors import sync_google  # type: ignore

            sync_google.delay(account.id)
        except Exception:
            pass

        return {"status": "connected", "provider": provider}

    elif provider in ("notion", "confluence"):
        # Accept stub, mark as connected
        return {"status": "connected", "provider": provider}

    else:
        raise HTTPException(status_code=404, detail="Unsupported provider")
