import os
import pytest
import asyncio
import httpx
from typing import AsyncGenerator
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from fastapi.testclient import TestClient
from httpx import AsyncClient
from src.main import app
from src.database.connection import DatabaseConnection
from src.config import settings
from src.repositories.user_repository import UserRepository
from src.services.user_service import UserService
from src.services.task_service import TaskService
from src.services.health_service import HealthService
from src.models.domain import User
from src.services.password import hash_password
from datetime import datetime


@pytest.fixture(scope='session')
def api_base_url():
    return os.getenv('API_BASE_URL', 'http://localhost:8000')


@pytest.fixture
def api_client(api_base_url):
    with httpx.Client(base_url=api_base_url) as client:
        yield client


@pytest.fixture(scope='session')
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
async def test_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """Create a test database connection."""
    test_db_name = f"{settings.mongodb_db_name}_test"
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[test_db_name]
    
    # Clean up before tests
    await db.client.drop_database(test_db_name)
    
    yield db
    
    # Clean up after tests
    await db.client.drop_database(test_db_name)
    client.close()


@pytest.fixture(scope='function')
async def db_session(test_db: AsyncIOMotorDatabase) -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """Provide a database session for each test with automatic cleanup."""
    # Store original database connection
    original_db = DatabaseConnection._db
    original_client = DatabaseConnection._client
    
    # Replace with test database - this ensures get_db() works
    DatabaseConnection._db = test_db
    DatabaseConnection._client = test_db.client
    
    # Clean collections before each test
    collections = await test_db.list_collection_names()
    for collection_name in collections:
        await test_db[collection_name].delete_many({})
    
    yield test_db
    
    # Clean collections after each test
    collections = await test_db.list_collection_names()
    for collection_name in collections:
        await test_db[collection_name].delete_many({})
    
    # Restore original database connection
    DatabaseConnection._db = original_db
    DatabaseConnection._client = original_client


@pytest.fixture
def client() -> TestClient:
    """Create a test client for FastAPI."""
    return TestClient(app)


@pytest.fixture
async def async_client(db_session: AsyncIOMotorDatabase) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for FastAPI.
    
    Note: db_session is included as a dependency to ensure database is set up
    before the client is created.
    """
    async with AsyncClient(app=app, base_url='http://test') as ac:
        yield ac


@pytest.fixture
async def user_repository(db_session: AsyncIOMotorDatabase) -> UserRepository:
    """Provide a user repository for testing."""
    return UserRepository(db_session)


@pytest.fixture
async def user_service(user_repository: UserRepository) -> UserService:
    """Provide a user service for testing."""
    return UserService(user_repository)


@pytest.fixture
def task_service() -> TaskService:
    """Provide a task service for testing."""
    return TaskService()


@pytest.fixture
def health_service() -> HealthService:
    """Provide a health service for testing."""
    return HealthService()


@pytest.fixture
async def test_user(async_client: AsyncClient) -> dict:
    """Create a test user via API and return user data."""
    # Arrange: Create user via API (no backend dependencies)
    response = await async_client.post(
        '/api/users',
        json={
            'email': 'test@example.com',
            'name': 'Test User',
            'password': 'testpassword123'
        }
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
async def authenticated_client(
    async_client: AsyncClient,
    test_user: dict
) -> AsyncGenerator[AsyncClient, None]:
    """Provide an authenticated async client for regular user.
    
    Creates authentication via API login (no backend dependencies).
    """
    # Arrange: Login via API to get token
    login_response = await async_client.post(
        '/api/auth/login',
        json={
            'email': test_user['email'],
            'password': 'testpassword123',
            'strategy': 'credentials'
        }
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    access_token = token_data['access_token']
    
    # Act: Set authorization header
    async_client.headers.update({'Authorization': f'Bearer {access_token}'})
    yield async_client
    async_client.headers.pop('Authorization', None)


@pytest.fixture
async def admin_client(
    async_client: AsyncClient,
    user_repository: UserRepository
) -> AsyncGenerator[AsyncClient, None]:
    """Provide an authenticated async client for admin user.
    
    Note: Admin users must be created via repository since there's no public API
    endpoint to create admin users. This is minimal backend access for test setup.
    After creation, authentication is done via API login.
    """
    # Create admin user via repository (minimal backend access - no public API for admin creation)
    admin_user = User(
        email='admin@test.example.com',
        name='Admin Test User',
        hashed_password=hash_password('adminpassword123'),
        role='admin',
        created_at=datetime.utcnow()
    )
    admin_user = await user_repository.create(admin_user)
    
    # Authenticate via API (login)
    login_response = await async_client.post(
        '/api/auth/login',
        json={
            'email': 'admin@test.example.com',
            'password': 'adminpassword123',
            'strategy': 'credentials'
        }
    )
    
    assert login_response.status_code == 200
    token_data = login_response.json()
    access_token = token_data['access_token']
    
    async_client.headers.update({'Authorization': f'Bearer {access_token}'})
    yield async_client
    async_client.headers.pop('Authorization', None)
