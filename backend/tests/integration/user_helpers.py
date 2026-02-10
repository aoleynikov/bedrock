"""
User operations for integration tests.
Centralizes create-via-API, create-admin-via-repository, and login so tests stay clean
and do not rely on ensure_default_admin. All credentials are generated (no defaults).
Use async helpers with AsyncClient so the app and DB share the same event loop.
"""
import asyncio
from datetime import datetime
from typing import Any

from faker import Faker
from httpx import AsyncClient, Client

from src.models.domain import User
from src.repositories.user_repository import UserRepository
from src.services.password import hash_password

_faker = Faker()


def fake_credentials() -> dict[str, str]:
    """Generate email, name, and password for a user. No hardcoded defaults."""
    return {
        'email': _faker.email(),
        'name': _faker.name(),
        'password': _faker.password(length=12),
    }


async def create_user_via_api_async(
    client: AsyncClient,
    email: str,
    name: str,
    password: str,
) -> dict[str, Any]:
    """Create a regular user via POST /api/users (async). Returns user payload (arrange)."""
    response = await client.post(
        '/api/users',
        json={'email': email, 'name': name, 'password': password},
    )
    assert response.status_code == 201
    return response.json()


async def login_async(client: AsyncClient, email: str, password: str) -> str:
    """Log in via API (async); returns access_token."""
    response = await client.post(
        '/api/auth/login',
        json={'email': email, 'password': password, 'strategy': 'credentials'},
    )
    assert response.status_code == 200
    return response.json()['access_token']


def attach_auth(client: Client | AsyncClient, access_token: str) -> None:
    """Set Authorization header on client."""
    client.headers.update({'Authorization': f'Bearer {access_token}'})


def clear_auth(client: Client | AsyncClient) -> None:
    """Remove Authorization header from client."""
    client.headers.pop('Authorization', None)


async def create_admin_via_repository_async(
    user_repository: UserRepository,
    email: str,
    name: str,
    password: str,
) -> User:
    """Create an admin user via repository (async). Use from async fixtures."""
    admin = User(
        email=email,
        name=name,
        hashed_password=hash_password(password),
        role='admin',
        created_at=datetime.utcnow(),
    )
    return await user_repository.create(admin)


def create_admin_via_repository(
    user_repository: UserRepository,
    email: str,
    name: str,
    password: str,
) -> User:
    """Create an admin user via repository (sync wrapper). Returns User (arrange)."""
    return asyncio.run(
        create_admin_via_repository_async(
            user_repository, email, name, password
        )
    )
