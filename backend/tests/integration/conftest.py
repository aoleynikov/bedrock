import os
import pytest
import asyncio
import httpx
from typing import AsyncGenerator
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from httpx import ASGITransport, AsyncClient
from httpx_ws.transport import ASGIWebSocketTransport

from src.main import app
from src.database.connection import DatabaseConnection
from src.tasks.queue_backend import InMemoryQueueBackend, get_queue_backend
from src.config import settings
from src.repositories.user_repository import UserRepository
from src.services.user_service import UserService
from src.services.task_service import TaskService
from src.services.health_service import HealthService

from tests.integration.user_helpers import (
    fake_credentials,
    create_user_via_api_async,
    create_admin_via_repository_async,
    login_async,
    attach_auth,
    clear_auth,
)


@pytest.fixture(scope='session')
def api_base_url():
    return os.getenv('API_BASE_URL', 'http://localhost:8000')


@pytest.fixture
def in_memory_queue() -> InMemoryQueueBackend:
    backend = get_queue_backend()
    if not isinstance(backend, InMemoryQueueBackend):
        pytest.skip('In-memory queue backend not enabled')
    backend.clear()
    return backend


@pytest.fixture
def api_client(api_base_url):
    with httpx.Client(base_url=api_base_url) as client:
        yield client


@pytest.fixture(scope='session')
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
async def test_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    test_db_name = f"{settings.mongodb_db_name}_test"
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[test_db_name]
    await db.client.drop_database(test_db_name)
    yield db
    await db.client.drop_database(test_db_name)
    client.close()


@pytest.fixture(scope='function')
async def db_session(test_db: AsyncIOMotorDatabase) -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    original_db = DatabaseConnection._db
    original_client = DatabaseConnection._client
    DatabaseConnection._db = test_db
    DatabaseConnection._client = test_db.client
    collections = await test_db.list_collection_names()
    for collection_name in collections:
        await test_db[collection_name].delete_many({})
    yield test_db
    collections = await test_db.list_collection_names()
    for collection_name in collections:
        await test_db[collection_name].delete_many({})
    DatabaseConnection._db = original_db
    DatabaseConnection._client = original_client


@pytest.fixture
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for the app. Same event loop as db_session so DB works."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
    ) as c:
        yield c


@pytest.fixture
async def ws_client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """Async client with WebSocket support. Same event loop as db_session; no separate thread."""
    async with AsyncClient(
        transport=ASGIWebSocketTransport(app=app),
        base_url='http://test',
    ) as c:
        yield c


@pytest.fixture(scope='function')
async def user_repository(db_session: AsyncIOMotorDatabase) -> UserRepository:
    return UserRepository(db_session)


@pytest.fixture
def user_service(user_repository: UserRepository) -> UserService:
    return UserService(user_repository)


@pytest.fixture
def task_service() -> TaskService:
    return TaskService()


@pytest.fixture
def health_service() -> HealthService:
    return HealthService()


@pytest.fixture
def user_payload() -> dict:
    return fake_credentials()


@pytest.fixture
def five_user_payloads() -> list[dict]:
    return [fake_credentials() for _ in range(5)]


@pytest.fixture
async def test_user(client: AsyncClient) -> dict:
    """Create a regular user via API and return user data including password (arrange)."""
    creds = fake_credentials()
    data = await create_user_via_api_async(
        client, creds['email'], creds['name'], creds['password']
    )
    return {**data, 'password': creds['password']}


@pytest.fixture
async def authenticated_client(client: AsyncClient, test_user: dict):
    """Async HTTP client authenticated as the regular test user."""
    token = await login_async(client, test_user['email'], test_user['password'])
    attach_auth(client, token)
    yield client
    clear_auth(client)


@pytest.fixture
async def admin_user(user_repository: UserRepository):
    """Create an admin via repository; return id, email, name, password (arrange)."""
    creds = fake_credentials()
    admin = await create_admin_via_repository_async(
        user_repository, creds['email'], creds['name'], creds['password']
    )
    return {
        'id': admin.id,
        'email': admin.email,
        'name': admin.name,
        'password': creds['password'],
    }


@pytest.fixture
async def admin_client(admin_user: dict) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client authenticated as the admin user."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
    ) as c:
        token = await login_async(
            c, admin_user['email'], admin_user['password']
        )
        attach_auth(c, token)
        yield c
        clear_auth(c)


@pytest.fixture
async def other_user_client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client authenticated as a second user (created via API)."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
    ) as c:
        creds = fake_credentials()
        await create_user_via_api_async(
            c, creds['email'], creds['name'], creds['password']
        )
        token = await login_async(c, creds['email'], creds['password'])
        attach_auth(c, token)
        yield c
        clear_auth(c)
