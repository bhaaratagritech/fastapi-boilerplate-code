from __future__ import annotations

from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.config import get_settings
from ..core.correlation import get_correlation_id
from ..core.exceptions import AppException
from ..core.logging_config import get_logger
from ..services.auth.jwt import decode_token, extract_token

logger = get_logger(__name__)
settings = get_settings()


class JWTAuthenticationMiddleware(BaseHTTPMiddleware):
    """Authenticate requests using JWT tokens found in the Authorization header."""

    def __init__(self, app, exempt_paths: list[str] | None = None):
        super().__init__(app)
        self.exempt_paths = set(exempt_paths or [])

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        # Skip authentication for exempt paths, OPTIONS requests, documentation endpoints, and common static files
        if (
            request.url.path in self.exempt_paths
            or request.method == "OPTIONS"
            or request.url.path in [
                "/favicon.ico",
                "/robots.txt",
                "/docs",  # Swagger UI documentation
                "/redoc",  # ReDoc documentation
                "/openapi.json",  # OpenAPI schema
            ]
        ):
            return await call_next(request)

        try:
            token = extract_token(request.headers.get("Authorization"))
            payload = decode_token(token)
            request.state.user = payload
        except AppException as exc:
            logger.warning("JWT authentication failed", extra={"path": request.url.path, "reason": exc.message})
            # Return proper JSON response instead of raising exception
            # Correlation ID should always be set by CorrelationIdMiddleware (runs before this middleware)
            correlation_id = getattr(request.state, "correlation_id", None)
            if not correlation_id:
                # Fallback: get from context (should always be set, but safety check)
                correlation_id = get_correlation_id()
                if not correlation_id:
                    # This should never happen if middleware order is correct
                    from ..core.correlation import new_correlation_id
                    correlation_id = new_correlation_id()
                    logger.error(
                        "Correlation ID not found - CorrelationIdMiddleware may not be running first!",
                        extra={"path": request.url.path, "correlation_id": correlation_id}
                    )
            content = {"error": exc.message, "correlation_id": correlation_id}
            if exc.payload:
                content.update(exc.payload)
            return JSONResponse(status_code=exc.status_code, content=content)

        return await call_next(request)


