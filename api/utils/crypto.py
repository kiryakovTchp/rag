"""Simple token encryption utilities using Fernet.

Requires TOKEN_ENCRYPTION_KEY in env (base64-url Fernet key, 32 bytes).
"""

import os
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken


def _get_fernet() -> Fernet:
    key = os.getenv("TOKEN_ENCRYPTION_KEY")
    if not key:
        raise ValueError(
            "TOKEN_ENCRYPTION_KEY env var is required for OAuth token encryption"
        )
    # Fernet ожидает base64-url строку длиной 44 символа (32 байта) в bytes
    return Fernet(key.encode())


def encrypt_token(raw: str) -> str:
    f = _get_fernet()
    return f.encrypt(raw.encode()).decode()


def decrypt_token(encrypted: str) -> Optional[str]:
    try:
        f = _get_fernet()
        return f.decrypt(encrypted.encode()).decode()
    except (InvalidToken, ValueError):
        return None
