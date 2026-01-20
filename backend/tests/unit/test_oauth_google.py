from unittest.mock import Mock

import httpx
import pytest

from src.auth.oauth.google import GoogleOAuthStrategy


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeClient:
    def __init__(self, response):
        self.response = response
        self.calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def post(self, url, data):
        self.calls.append(('post', url, data))
        return self.response

    async def get(self, url, headers):
        self.calls.append(('get', url, headers))
        return self.response


@pytest.mark.unit
@pytest.mark.asyncio
class TestGoogleOAuthStrategy:
    async def test_exchange_code_for_tokens_returns_payload(self, monkeypatch):
        response_payload = {'access_token': 'token-value'}
        fake_client = FakeClient(FakeResponse(response_payload))
        monkeypatch.setattr(httpx, 'AsyncClient', lambda: fake_client)

        strategy = GoogleOAuthStrategy()
        result = await strategy.exchange_code_for_tokens('auth-code')

        assert result == response_payload
        assert fake_client.calls
        method, url, data = fake_client.calls[0]
        assert method == 'post'
        assert url == strategy.TOKEN_URL
        assert data['code'] == 'auth-code'

    async def test_get_user_info_returns_payload(self, monkeypatch):
        response_payload = {'id': 'google-123', 'email': 'user@example.com', 'name': 'User'}
        fake_client = FakeClient(FakeResponse(response_payload))
        monkeypatch.setattr(httpx, 'AsyncClient', lambda: fake_client)

        strategy = GoogleOAuthStrategy()
        result = await strategy.get_user_info('access-token')

        assert result == response_payload
        method, url, headers = fake_client.calls[0]
        assert method == 'get'
        assert url == strategy.USER_INFO_URL
        assert headers['Authorization'] == 'Bearer access-token'

    async def test_authenticate_returns_error_without_token(self):
        strategy = GoogleOAuthStrategy()
        result = await strategy.authenticate(Mock())

        assert result.success is False

    async def test_authenticate_success_with_access_token(self, monkeypatch):
        strategy = GoogleOAuthStrategy()

        async def fake_get_user_info(token):
            return {'id': 'google-123', 'email': 'user@example.com', 'name': 'User'}

        monkeypatch.setattr(strategy, 'get_user_info', fake_get_user_info)
        result = await strategy.authenticate(Mock(), access_token='access-token')

        assert result.success is True
        assert result.user_id == 'google-123'
        assert result.user_data['email'] == 'user@example.com'
        assert result.user_data['provider'] == 'google'

    async def test_authenticate_returns_error_on_exception(self, monkeypatch):
        strategy = GoogleOAuthStrategy()

        async def fake_get_user_info(token):
            raise ValueError('boom')

        monkeypatch.setattr(strategy, 'get_user_info', fake_get_user_info)
        result = await strategy.authenticate(Mock(), access_token='access-token')

        assert result.success is False
