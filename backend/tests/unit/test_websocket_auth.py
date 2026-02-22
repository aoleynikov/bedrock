from unittest.mock import AsyncMock, MagicMock

import pytest

from src.auth.service import auth_service


@pytest.mark.unit
class TestWebSocketAuth:
    def test_verify_access_token_returns_none_for_invalid_token(self):
        assert auth_service.verify_access_token('invalid') is None

    def test_verify_access_token_returns_none_for_empty_string(self):
        assert auth_service.verify_access_token('') is None
