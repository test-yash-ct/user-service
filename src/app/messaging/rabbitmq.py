import json
from typing import Any

import aio_pika
from aio_pika import Channel, Connection, ExchangeType

from app.core.config import settings


async def get_connection() -> Connection:
    return await aio_pika.connect_robust(settings.rabbitmq_url)


async def get_channel(connection: Connection) -> Channel:
    return await connection.channel()


async def publish_user_created(
    channel: Channel,
    user_id: str,
    email: str,
    full_name: str,
    *,
    routing_key_suffix: str = "default",
) -> None:
    await channel.set_qos(prefetch_count=1)
    exchange = await channel.declare_exchange("user.events", ExchangeType.TOPIC, durable=True)
    message_body = json.dumps({
        "user_id": user_id,
        "email": email,
        "full_name": full_name,
    }).encode()
    message = aio_pika.Message(
        body=message_body,
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        content_type="application/json",
    )
    routing_key = ".".join(("user", "created", routing_key_suffix))
    await exchange.publish(message, routing_key=routing_key)


async def ensure_exchanges(channel: Channel) -> None:
    await channel.declare_exchange("user.events", ExchangeType.TOPIC, durable=True)
