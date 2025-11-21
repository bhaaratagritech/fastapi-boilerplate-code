from __future__ import annotations

from contextvars import ContextVar, Token
from typing import Optional
from uuid import uuid4

CorrelationId = Optional[str]

# HTTP header name for correlation ID
CORRELATION_HEADER = "X-Correlation-ID"

_correlation_id_ctx: ContextVar[CorrelationId] = ContextVar("correlation_id", default=None)


def new_correlation_id() -> str:
    """Generate a new correlation identifier."""
    return str(uuid4())


def set_correlation_id(correlation_id: Optional[str] = None) -> Token:
    """Set and return the correlation id stored in the context var."""
    cid = correlation_id or new_correlation_id()
    return _correlation_id_ctx.set(cid)


def get_correlation_id(default: Optional[str] = None) -> Optional[str]:
    """Fetch the correlation id from the context."""
    return _correlation_id_ctx.get(default)


def reset_correlation_id(token: Optional[Token] = None) -> None:
    """Reset the correlation id in the current context."""
    if token:
        _correlation_id_ctx.reset(token)
    else:
        _correlation_id_ctx.set(None)


