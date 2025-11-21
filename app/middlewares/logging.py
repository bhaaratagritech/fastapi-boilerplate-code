from __future__ import annotations

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..core import correlation
from ..core.logging_config import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log inbound requests and outbound responses with correlation IDs."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        # Correlation ID should always be set by CorrelationIdMiddleware (runs before this middleware)
        correlation_id = getattr(request.state, "correlation_id", None) or correlation.get_correlation_id()
        start_time = time.perf_counter()

        logger.info(
            "Incoming request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None,
                "correlation_id": correlation_id,
            },
        )

        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            "Outgoing response",
            extra={
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "correlation_id": correlation_id,
            },
        )

        return response


