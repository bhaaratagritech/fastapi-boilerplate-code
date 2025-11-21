from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from opensearchpy import OpenSearch

from ...core.config import Settings
from ...core.logging_config import get_logger

logger = get_logger(__name__)

client: Optional[OpenSearch] = None


async def init_client(settings: Settings) -> None:
    """Initialize OpenSearch client. Gracefully handles connection errors. Note: opensearch-py 3.x uses sync client."""
    global client
    if client:
        return

    try:
        # opensearch-py 3.x removed AsyncOpenSearch, use regular OpenSearch client
        # Wrap sync operations with asyncio.to_thread() for async compatibility
        client = OpenSearch(
            hosts=[settings.opensearch_host],
            http_auth=(settings.opensearch_username, settings.opensearch_password),
            use_ssl=settings.opensearch_host.startswith("https"),
            verify_certs=False,
        )
        # Test connection by checking cluster health
        await asyncio.to_thread(client.cluster.health)
        logger.info("Connected to OpenSearch", extra={"host": settings.opensearch_host})
    except Exception as exc:
        logger.error(
            "Failed to connect to OpenSearch - application will continue without search functionality",
            extra={"host": settings.opensearch_host, "error": str(exc), "error_type": type(exc).__name__}
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


