from __future__ import annotations

from fastapi import APIRouter, Depends

from ..dependencies.rate_limit import rate_limiter
from ..services.search import opensearch_client

router = APIRouter(dependencies=[Depends(rate_limiter)])


@router.post("/{index}/{doc_id}")
async def upsert_document(index: str, doc_id: str, payload: dict) -> dict:
    response = await opensearch_client.create_document(index=index, doc_id=doc_id, document=payload)
    return response


@router.get("/{index}/{doc_id}")
async def fetch_document(index: str, doc_id: str) -> dict:
    response = await opensearch_client.read_document(index=index, doc_id=doc_id)
    return response


