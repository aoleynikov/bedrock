import pytest
from src.auth.dependencies import require_roles
from src.exceptions import ForbiddenException
from src.models.domain import User


@pytest.mark.unit
@pytest.mark.asyncio
async def test_require_roles_allows_when_role_present():
    user = User(
        id='user1',
        email='user@example.com',
        name='Test User',
        hashed_password='hashed',
        role='admin'
    )
    dependency = require_roles('admin')
    result = await dependency(current_user=user)
    assert result == user


@pytest.mark.unit
@pytest.mark.asyncio
async def test_require_roles_forbids_when_role_missing():
    user = User(
        id='user1',
        email='user@example.com',
        name='Test User',
        hashed_password='hashed',
        role='user'
    )
    dependency = require_roles('admin')
    with pytest.raises(ForbiddenException):
        await dependency(current_user=user)
