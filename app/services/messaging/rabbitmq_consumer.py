from __future__ import annotations

import json
from typing import Awaitable, Callable

import aio_pika

from .connection import get_connection


async def consume_messages(
    queue_name: str,
    handler: Callable[[dict], Awaitable[None]],
    prefetch_count: int = 10,
) -> None:
    connection = get_connection()
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=prefetch_count)
    queue = await channel.declare_queue(queue_name, durable=True)

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                payload = json.loads(message.body)
                await handler(payload)


