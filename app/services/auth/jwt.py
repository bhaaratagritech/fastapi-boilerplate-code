from __future__ import annotations

from typing import Any, Dict, Optional

from jose import JWTError, jwt

from ...core.config import get_settings
from ...core.exceptions import AppException

settings = get_settings()


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT token."""
    try:
        options = {"verify_aud": bool(settings.jwt_audience)}
        decoded = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
            options=options,
        )
        return decoded
    except JWTError as exc:
        raise AppException("Invalid or expired token", status_code=401) from exc


def extract_token(auth_header: Optional[str]) -> str:
    if not auth_header:
        raise AppException("Missing authorization header", status_code=401)
    scheme, _, token = auth_header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AppException("Invalid authorization header format", status_code=401)
    return token


