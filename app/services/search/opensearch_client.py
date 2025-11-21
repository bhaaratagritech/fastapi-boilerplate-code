from __future__ import annotations

import asyncio
import math
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse, urlunparse

from opensearchpy import OpenSearch
from opensearchpy.exceptions import ConnectionError as OpenSearchConnectionError

from ...core.config import Settings
from ...core.logging_config import get_logger

logger = get_logger(__name__)

client: Optional[OpenSearch] = None


def _normalize_host(host: str) -> Tuple[str, bool]:
    """Ensure host includes scheme and return (host, use_ssl)."""
    host = host.strip()
    if not host.startswith(("http://", "https://")):
        host = f"http://{host}"

    parsed = urlparse(host)
    scheme = parsed.scheme or "http"
    netloc = parsed.netloc or parsed.path
    normalized = urlunparse((scheme, netloc, "", "", "", ""))
    use_ssl = scheme == "https"
    return normalized, use_ssl


async def _connect_to_opensearch(host: str, settings: Settings, *, max_attempts: int = 5) -> OpenSearch:
    """Create and validate an OpenSearch client for the provided host with retries."""
    normalized_host, use_ssl = _normalize_host(host)
    attempt = 0
    delay_base = 0.5  # seconds

    while True:
        attempt += 1
        try:
            os_client = OpenSearch(
                hosts=[normalized_host],
                http_auth=(settings.opensearch_username, settings.opensearch_password),
                use_ssl=use_ssl,
                verify_certs=False,
            )
            # Cluster health call ensures the connection is valid
            await asyncio.to_thread(os_client.cluster.health)
            return os_client
        except Exception as exc:
            if attempt >= max_attempts:
                raise
            # Service might still be starting; wait and retry
            sleep_for = delay_base * math.pow(2, attempt - 1)
            logger.warning(
                "OpenSearch connection attempt failed, retrying",
                extra={"host": normalized_host, "attempt": attempt, "delay": sleep_for, "error": str(exc)},
            )
            await asyncio.sleep(sleep_for)


async def init_client(settings: Settings) -> None:
    """Initialize OpenSearch client. Gracefully handles connection errors. Note: opensearch-py 3.x uses sync client."""
    global client
    if client:
        return

    primary_host = settings.opensearch_host
    normalized_host, use_ssl = _normalize_host(primary_host)

    try:
        client = await _connect_to_opensearch(normalized_host, settings)
        logger.info("Connected to OpenSearch", extra={"host": normalized_host})
        return
    except OpenSearchConnectionError as exc:
        if use_ssl:
            fallback_host = normalized_host.replace("https://", "http://", 1)
            logger.warning(
                "OpenSearch HTTPS connection failed, retrying over HTTP",
                extra={"host": normalized_host, "error": str(exc)},
            )
            try:
                client = await _connect_to_opensearch(fallback_host, settings)
                logger.info("Connected to OpenSearch over HTTP", extra={"host": fallback_host})
                return
            except Exception as fallback_exc:  # pragma: no cover - rare fallback failure
                logger.error(
                    "Failed to connect to OpenSearch over HTTP",
                    extra={"host": fallback_host, "error": str(fallback_exc), "error_type": type(fallback_exc).__name__},
                )
    except Exception as exc:
        logger.error(
            "Failed to connect to OpenSearch - application will continue without search functionality",
            extra={"host": normalized_host, "error": str(exc), "error_type": type(exc).__name__},
        )

    client = None


async def close_client() -> None:
    """Close OpenSearch client connection."""
    global client
    if client:
        # OpenSearch client doesn't have async close, but connection is closed on GC
        client = None


def get_client() -> OpenSearch:
    """Get the OpenSearch client instance."""
    if not client:
        raise RuntimeError("OpenSearch client not initialised - OpenSearch connection unavailable")
    return client


async def create_document(index: str, doc_id: str, document: Dict[str, Any]) -> Dict[str, Any]:
    """Create or update a document in OpenSearch."""
    opensearch = get_client()
    # Run sync operation in thread pool to avoid blocking
    return await asyncio.to_thread(
        opensearch.index, index=index, id=doc_id, body=document
    )


async def read_document(index: str, doc_id: str) -> Dict[str, Any]:
    """Read a document from OpenSearch."""
    opensearch = get_client()
    # Run sync operation in thread pool to avoid blocking
    return await asyncio.to_thread(opensearch.get, index=index, id=doc_id)


async def check_status(settings: Settings) -> bool:
    """Check whether OpenSearch is reachable."""
    normalized_host, use_ssl = _normalize_host(settings.opensearch_host)
    try:
        await _connect_to_opensearch(normalized_host, settings)
        logger.info("Dependency check: OpenSearch is running", extra={"host": normalized_host})
        return True
    except OpenSearchConnectionError as exc:
        if use_ssl:
            fallback_host = normalized_host.replace("https://", "http://", 1)
            logger.warning(
                "Dependency check: OpenSearch HTTPS endpoint unreachable, retrying over HTTP",
                extra={"host": normalized_host, "error": str(exc)},
            )
            try:
                await _connect_to_opensearch(fallback_host, settings)
                logger.info("Dependency check: OpenSearch is running (HTTP fallback)", extra={"host": fallback_host})
                return True
            except Exception as fallback_exc:
                logger.error(
                    "Dependency check: OpenSearch is NOT running (HTTP fallback failed)",
                    extra={"host": fallback_host, "error": str(fallback_exc), "error_type": type(fallback_exc).__name__},
                )
                return False
        logger.error(
            "Dependency check: OpenSearch is NOT running",
            extra={"host": normalized_host, "error": str(exc), "error_type": type(exc).__name__},
        )
        return False
    except Exception as exc:
        logger.error(
            "Dependency check: OpenSearch is NOT running",
            extra={"host": normalized_host, "error": str(exc), "error_type": type(exc).__name__},
        )
        return False


