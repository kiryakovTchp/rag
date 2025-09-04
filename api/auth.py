"""Compatibility shim for legacy imports.

This module re-exports helpers from api.dependencies.auth to keep
older import paths working (e.g., tests patching api.auth.get_current_user_ws).
"""

from typing import Any, Optional

from fastapi import WebSocket

from api.dependencies.auth import get_current_user_ws as _get_current_user_ws


async def get_current_user_ws(websocket: WebSocket) -> Optional[Any]:
    return await _get_current_user_ws(websocket)
