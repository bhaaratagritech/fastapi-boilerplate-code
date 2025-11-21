from __future__ import annotations

import json
from contextlib import suppress
from typing import Any, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

from ..core import correlation
from ..core.correlation import CORRELATION_HEADER
from ..core.logging_config import get_logger

logger = get_logger(__name__)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Attach or generate correlation ids for every request and propagate them to responses."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        # Get incoming correlation ID from header, or None if not present
        incoming = request.headers.get(CORRELATION_HEADER)
        
        # Set correlation ID (generates new one if incoming is None/empty)
        token = correlation.set_correlation_id(incoming)
        correlation_id = correlation.get_correlation_id()
        
        # correlation_id should never be None after set_correlation_id, but ensure it's set
        if not correlation_id:
            correlation_id = correlation.new_correlation_id()
            token = correlation.set_correlation_id(correlation_id)
        
        request.state.correlation_id = correlation_id
        
        # Log info if correlation ID was generated (not provided in request)
        if not incoming or not incoming.strip():
            logger.info(
                "Correlation ID not present in request, generated new one",
                extra={"correlation_id": correlation_id, "path": request.url.path}
            )
        else:
            logger.debug(
                "Using correlation ID from request header",
                extra={"correlation_id": correlation_id, "path": request.url.path}
            )

        try:
            response = await call_next(request)
        finally:
            with suppress(Exception):
                correlation.reset_correlation_id(token)

        # Always include correlation ID in response header
        response.headers[CORRELATION_HEADER] = correlation_id
        
        # Inject correlation ID into JSON response bodies
        # Skip for documentation endpoints, OpenAPI schema, and non-JSON responses
        skip_paths = ["/docs", "/redoc", "/openapi.json", "/favicon.ico", "/robots.txt"]
        content_type = response.headers.get("content-type", "")
        
        if (
            request.url.path not in skip_paths
            and content_type.startswith("application/json")
        ):
            try:
                # Read response body from iterator
                body_chunks = []
                async for chunk in response.body_iterator:
                    body_chunks.append(chunk)
                
                # Combine chunks and parse JSON
                if body_chunks:
                    body = b"".join(body_chunks)
                    try:
                        response_data: dict[str, Any] | list[Any] = json.loads(body.decode("utf-8"))
                        
                        # Add correlation_id to response
                        if isinstance(response_data, dict):
                            # If it's a dict, add correlation_id (don't overwrite if already present)
                            if "correlation_id" not in response_data:
                                response_data["correlation_id"] = correlation_id
                        elif isinstance(response_data, list):
                            # If it's a list, wrap it in a dict with correlation_id
                            response_data = {"data": response_data, "correlation_id": correlation_id}
                        else:
                            # For other types, wrap in dict
                            response_data = {"data": response_data, "correlation_id": correlation_id}
                        
                        # Create new response with updated body
                        headers = dict(response.headers)
                        headers.pop("content-length", None)
                        return JSONResponse(
                            content=response_data,
                            status_code=response.status_code,
                            headers=headers,
                        )
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        # If body is not valid JSON, reconstruct original response
                        headers = dict(response.headers)
                        headers.pop("content-length", None)
                        return StarletteResponse(
                            content=body,
                            status_code=response.status_code,
                            headers=headers,
                            media_type=content_type,
                        )
            except Exception as exc:
                # If anything fails, log and return original response structure
                logger.debug(
                    "Could not inject correlation ID into response body",
                    extra={"error": str(exc), "path": request.url.path, "response_type": type(response).__name__}
                )
                # Reconstruct response from chunks if we read them
                if "body_chunks" in locals() and body_chunks:
                    headers = dict(response.headers)
                    headers.pop("content-length", None)
                    return StarletteResponse(
                        content=b"".join(body_chunks),
                        status_code=response.status_code,
                        headers=headers,
                        media_type=content_type,
                    )
        
        return response


