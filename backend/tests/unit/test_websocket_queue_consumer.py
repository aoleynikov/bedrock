from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.websocket.queue_consumer import _handle_message


@pytest.mark.unit
@pytest.mark.asyncio
class TestQueueConsumer:
    async def test_handle_message_send_to_user(self):
        message = MagicMock()
        message.body = b'{"user_id": "u1", "payload": {"x": 1}}'
        message.process = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(), __aexit__=AsyncMock(return_value=None)))
        with patch('src.websocket.queue_consumer.connection_manager') as mgr:
            mgr.send_to_user = AsyncMock()
            await _handle_message(message)
            mgr.send_to_user.assert_awaited_once_with('u1', {'x': 1})

    async def test_handle_message_broadcast(self):
        message = MagicMock()
        message.body = b'{"broadcast": true, "payload": {"msg": "hi"}}'
        message.process = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(), __aexit__=AsyncMock(return_value=None)))
        with patch('src.websocket.queue_consumer.connection_manager') as mgr:
            mgr.broadcast = AsyncMock()
            await _handle_message(message)
            mgr.broadcast.assert_awaited_once_with({'msg': 'hi'})
