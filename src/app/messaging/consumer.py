import json
import asyncio
import hashlib
from aio_pika import IncomingMessage

from app.db.session import async_session_factory
from app.services.notification_service import send_mock_email, log_notification
from sqlalchemy import text


async def _is_processed(session, event_id: str) -> bool:
    result = await session.execute(text("SELECT 1 FROM processed_events WHERE event_id = :eid"), {"eid": event_id})
    return result.scalars().first() is not None


async def _mark_processed(session, event_id: str) -> None:
    await session.execute(text("INSERT INTO processed_events (event_id) VALUES (:eid)"), {"eid": event_id})


async def handle_user_created(message: IncomingMessage):
    try:
        body = message.body.decode()
        event_id = hashlib.sha256(body.encode()).hexdigest()
        async with async_session_factory() as session:
            if await _is_processed(session, event_id):
                await message.ack()
                return
            data = json.loads(body)
            email = data.get("email", "")
            full_name = data.get("full_name", "")
            user_id = data.get("user_id", "")
            content = f"Welcome {full_name}. Your account is ready."
            await send_mock_email(email, "Welcome", content)
            await log_notification(
                session,
                "user.created",
                body,
                email,
                content,
            )
            await _mark_processed(session, event_id)
            await session.commit()
        await message.ack()
    except Exception:
        await asyncio.sleep(2)
        await message.nack(requeue=True)


async def handle_order_created(message: IncomingMessage):
    try:
        body = message.body.decode()
        event_id = hashlib.sha256(body.encode()).hexdigest()
        async with async_session_factory() as session:
            if await _is_processed(session, event_id):
                await message.ack()
                return
            data = json.loads(body)
            order_id = data.get("order_id")
            user_id = data.get("user_id")
            total_cents = data.get("total_cents")
            content = f"Order {order_id} placed. Total: {total_cents} cents."
            await send_mock_email(f"user-{user_id}@placeholder.local", "Order Confirmation", content)
            await log_notification(
                session,
                "order.created",
                body,
                f"user-{user_id}@placeholder.local",
                content,
            )
            await _mark_processed(session, event_id)
            await session.commit()
        await message.ack()
    except Exception:
        await asyncio.sleep(2)
        await message.nack(requeue=True)
