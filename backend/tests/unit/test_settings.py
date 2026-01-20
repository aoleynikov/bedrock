import pytest
from pydantic import ValidationError

from src.config import Settings


def test_settings_require_admin_and_jwt(monkeypatch):
    monkeypatch.delenv('JWT_SECRET_KEY', raising=False)
    monkeypatch.delenv('ADMIN_DEFAULT_EMAIL', raising=False)
    monkeypatch.delenv('ADMIN_DEFAULT_NAME', raising=False)
    monkeypatch.delenv('ADMIN_DEFAULT_PASSWORD', raising=False)

    with pytest.raises(ValidationError):
        Settings()
