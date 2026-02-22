from unittest.mock import AsyncMock

import pytest

from src.websocket.connection_manager import ConnectionManager


@pytest.mark.unit
@pytest.mark.asyncio
class TestConnectionManager:
    async def test_register_adds_connection_for_user(self):
        manager = ConnectionManager()
        ws = AsyncMock()
        manager.register(ws, 'user1')
        assert 'user1' in manager._connections
        assert ws in manager._connections['user1']

    async def test_unregister_removes_connection(self):
        manager = ConnectionManager()
        ws = AsyncMock()
        manager.register(ws, 'user1')
        manager.unregister(ws)
        assert 'user1' not in manager._connections

    async def test_send_to_user_sends_only_to_that_user(self):
        manager = ConnectionManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        manager.register(ws1, 'user1')
        manager.register(ws2, 'user2')
        await manager.send_to_user('user1', {'msg': 'hello'})
        ws1.send_json.assert_awaited_once_with({'msg': 'hello'})
        ws2.send_json.assert_not_awaited()

    async def test_broadcast_sends_to_all_connections(self):
        manager = ConnectionManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        manager.register(ws1, 'user1')
        manager.register(ws2, 'user2')
        await manager.broadcast({'msg': 'broadcast'})
        ws1.send_json.assert_awaited_once_with({'msg': 'broadcast'})
        ws2.send_json.assert_awaited_once_with({'msg': 'broadcast'})

    async def test_multiple_connections_per_user_all_receive_send_to_user(self):
        manager = ConnectionManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        manager.register(ws1, 'user1')
        manager.register(ws2, 'user1')
        await manager.send_to_user('user1', {'x': 1})
        ws1.send_json.assert_awaited_once_with({'x': 1})
        ws2.send_json.assert_awaited_once_with({'x': 1})

    async def test_send_to_user_unregisters_dead_connections(self):
        manager = ConnectionManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws1.send_json = AsyncMock(side_effect=Exception('closed'))
        manager.register(ws1, 'user1')
        manager.register(ws2, 'user1')
        await manager.send_to_user('user1', {'x': 1})
        assert ws1 not in manager._connections.get('user1', set())
        assert ws2 in manager._connections['user1']
