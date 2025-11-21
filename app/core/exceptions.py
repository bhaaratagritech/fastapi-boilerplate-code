from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .correlation import get_correlation_id
from .logging_config import get_logger
from ..utils.pii import scrub_pii

logger = get_logger(__name__)


class AppException(Exception):
    """Custom application exception that carries an HTTP status code and message."""

    def __init__(self, message: str, *, status_code: int = 400, payload: Dict[str, Any] | None = None):
        self.message = message
        self.status_code = status_code
        self.payload = payload or {}
        super().__init__(message)


def _error_response(
    message: str, status_code: int, payload: Dict[str, Any] | None = None, request: Request | None = None
) -> JSONResponse:
    # Correlation ID should always be set by CorrelationIdMiddleware (runs first)
    # Get from request.state first, then context as fallback
    correlation_id = None
    if request:
        correlation_id = getattr(request.state, "correlation_id", None)
    if not correlation_id:
        correlation_id = get_correlation_id()
        if not correlation_id:
            # This should never happen if middleware order is correct
            from .correlation import new_correlation_id
            correlation_id = new_correlation_id()
            logger.error(
                "Correlation ID not found in error response - CorrelationIdMiddleware may not be running first!",
                extra={"path": request.url.path if request else "unknown"}
            )
    
    content = {"error": message, "correlation_id": correlation_id}
    if payload:
        content["details"] = payload
    return JSONResponse(status_code=status_code, content=content)


def register_exception_handlers(app: FastAPI, pii_fields: list[str]) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail_payload = exc.detail if isinstance(exc.detail, dict) else {"detail": exc.detail}
        detail_payload["path"] = request.url.path
        scrubbed_detail = scrub_pii(detail_payload, pii_fields)
        logger.warning("Handled HTTP exception", extra={"status_code": exc.status_code, "detail": scrubbed_detail})
        message = (
            detail_payload.get("message")
            or detail_payload.get("detail")
            or detail_payload.get("error")
            or "HTTP error"
        )
        return _error_response(message, exc.status_code, payload=scrubbed_detail, request=request)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = exc.errors()
        scrubbed_body = scrub_pii(exc.body, pii_fields)
        logger.warning("Validation error", extra={"errors": errors, "body": scrubbed_body})
        return _error_response("Payload validation failed", 422, payload={"errors": errors}, request=request)

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        scrubbed_payload = scrub_pii(exc.payload, pii_fields)
        logger.error(
            "Application exception raised",
            extra={"status_code": exc.status_code, "payload": scrubbed_payload, "path": request.url.path},
        )
        return _error_response(exc.message, exc.status_code, payload=scrubbed_payload, request=request)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception occurred", extra={"path": request.url.path})
        return _error_response("Internal server error", 500, request=request)


