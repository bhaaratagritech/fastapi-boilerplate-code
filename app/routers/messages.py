from __future__ import annotations

import json
from typing import Any, Dict

import asyncio

from fastapi import APIRouter, Depends, HTTPException

from ..core.logging_config import get_logger
from ..dependencies.rate_limit import rate_limiter
from ..services.messaging import rabbitmq_consumer, rabbitmq_producer
from ..services.messaging.connection import get_connection

router = APIRouter(dependencies=[Depends(rate_limiter)])
logger = get_logger(__name__)


@router.post("/publish")
async def publish_message(exchange: str, routing_key: str, payload: Dict[str, Any]) -> dict:
    await rabbitmq_producer.publish_message(exchange, routing_key, payload)
    return {"status": "accepted", "exchange": exchange, "routing_key": routing_key}


@router.post("/consume-once")
async def consume_once(queue: str) -> dict:
    connection = get_connection()
    channel = await connection.channel()
    queue_obj = await channel.declare_queue(queue, durable=True)
    message = await queue_obj.get(fail=False)
    if not message:
        await channel.close()
        raise HTTPException(status_code=404, detail="No messages available")
    async with message.process():
        body = message.body.decode("utf-8")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = body
    await channel.close()
    return {"payload": payload}


@router.post("/consume")
async def start_consumer(queue: str) -> dict:
    async def handler(message: dict) -> None:
        logger.info("Consumed message", extra={"queue": queue, "payload": message})

    asyncio.create_task(rabbitmq_consumer.consume_messages(queue, handler))
    return {"status": "consumer-started", "queue": queue}


