import pytest
from httpx import AsyncClient
from httpx_ws import aconnect_ws, WebSocketDisconnect
from httpx_ws.transport import ASGIWebSocketTransport

from src.main import app
from tests.integration.user_helpers import login_async


def _assert_rejected_4401(exc):
    assert exc.args[0] == 4401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_websocket_reject_no_token(db_session):
    """Create WS client inside test so anyio task group is entered/exited in same task (avoid cancel-scope error)."""
    async with AsyncClient(
        transport=ASGIWebSocketTransport(app=app),
        base_url='http://test',
    ) as ws_client:
        with pytest.raises(WebSocketDisconnect) as exc_info:
            async with aconnect_ws('http://test/api/ws', ws_client) as ws:
                await ws.receive()
        _assert_rejected_4401(exc_info.value)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_websocket_reject_invalid_token(db_session):
    async with AsyncClient(
        transport=ASGIWebSocketTransport(app=app),
        base_url='http://test',
    ) as ws_client:
        with pytest.raises(WebSocketDisconnect) as exc_info:
            async with aconnect_ws('http://test/api/ws?token=invalid', ws_client) as ws:
                await ws.receive()
        _assert_rejected_4401(exc_info.value)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_websocket_accept_valid_token_then_disconnect(client, db_session, test_user):
    token = await login_async(client, test_user['email'], test_user['password'])
    async with AsyncClient(
        transport=ASGIWebSocketTransport(app=app),
        base_url='http://test',
    ) as ws_client:
        async with aconnect_ws(f'http://test/api/ws?token={token}', ws_client) as ws:
            assert ws is not None
