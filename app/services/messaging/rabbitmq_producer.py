from __future__ import annotations

import json
from typing import Any, Dict

import aio_pika

from .connection import get_connection


async def publish_message(exchange_name: str, routing_key: str, payload: Dict[str, Any]) -> None:
    connection = get_connection()
    channel = await connection.channel()
    exchange = await channel.declare_exchange(exchange_name, aio_pika.ExchangeType.TOPIC, durable=True)
    message = aio_pika.Message(body=json.dumps(payload).encode("utf-8"), content_type="application/json")
    await exchange.publish(message, routing_key=routing_key)
    await channel.close()


