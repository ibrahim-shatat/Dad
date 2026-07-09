"""Token encryption at rest, and the signed OAuth 'state' parameter used to carry the
initiating user's identity through the redirect-based connect flow (see api/v1/endpoints/email.py
for why the callback endpoint can't just use get_current_user).
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from jose import JWTError, jwt

from app.core.config import settings

_fernet = Fernet(settings.token_encryption_key.encode())

_OAUTH_STATE_PURPOSE = "oauth_state"


def encrypt_token(raw_token: str) -> str:
    return _fernet.encrypt(raw_token.encode()).decode()


def decrypt_token(encrypted_token: str) -> str:
    try:
        return _fernet.decrypt(encrypted_token.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Could not decrypt stored OAuth token") from exc


def create_oauth_state_token(user_id: uuid.UUID, provider: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "provider": provider,
        "purpose": _OAUTH_STATE_PURPOSE,
        "iat": now,
        "exp": now + timedelta(minutes=10),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_oauth_state_token(token: str, expected_provider: str) -> uuid.UUID | None:
    try:
        payload: dict[str, Any] = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
    except JWTError:
        return None

    if payload.get("purpose") != _OAUTH_STATE_PURPOSE or payload.get("provider") != expected_provider:
        return None

    try:
        return uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        return None
