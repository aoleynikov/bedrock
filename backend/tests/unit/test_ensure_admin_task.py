import pytest

from src.models.domain import User
from src.tasks import ensure_admin


@pytest.mark.unit
@pytest.mark.asyncio
async def test_run_ensure_default_admin(monkeypatch):
    class FakeUserRepository:
        def __init__(self, db):
            self.db = db

    class FakeUserService:
        def __init__(self, repository):
            self.repository = repository

        async def ensure_default_admin(self):
            return User(
                id='admin-id',
                email='admin@example.com',
                name='Admin',
                hashed_password='hashed',
                role='admin'
            )

    async def fake_connect():
        return None

    monkeypatch.setattr(ensure_admin.DatabaseConnection, 'get_db', lambda: None)
    monkeypatch.setattr(ensure_admin.DatabaseConnection, 'connect', fake_connect)
    monkeypatch.setattr(ensure_admin, 'UserRepository', FakeUserRepository)
    monkeypatch.setattr(ensure_admin, 'UserService', FakeUserService)

    result = await ensure_admin._run_ensure_default_admin('corr-id', 'task-id')

    assert result['status'] == 'completed'
    assert result['admin_user_id'] == 'admin-id'
    assert result['admin_email'] == 'admin@example.com'
