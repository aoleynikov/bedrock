import json
import asyncio

import aio_pika
from aio_pika import IncomingMessage

from src.config import settings
from src.websocket.connection_manager import connection_manager


async def _handle_message(message: IncomingMessage) -> None:
    async with message.process():
        try:
            body = json.loads(message.body.decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            return
        payload = body.get('payload')
        if payload is None:
            return
        if body.get('broadcast'):
            await connection_manager.broadcast(payload)
        else:
            user_id = body.get('user_id')
            if user_id:
                await connection_manager.send_to_user(user_id, payload)


async def consume_ws_queue() -> None:
    connection = None
    while True:
        try:
            connection = await aio_pika.connect_robust(settings.rabbitmq_url)
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=10)
            queue = await channel.declare_queue(settings.ws_messages_queue, durable=True)
            await queue.consume(_handle_message)
            await asyncio.Future()
        except asyncio.CancelledError:
            break
        except Exception:
            await asyncio.sleep(5)
        finally:
            if connection:
                await connection.close()
                connection = None
