import asyncio
import os
import platform
import sys
import time
import xml.etree.ElementTree as ElementTree
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from tests import test_env
from src.config import settings
from src.database.connection import DatabaseConnection
from src.main import app
from src.models.domain import User
from src.repositories.user_repository import UserRepository
from src.services.health_service import HealthService
from src.services.password import hash_password
from src.services.task_service import TaskService
from src.services.user_service import UserService


@pytest.fixture(scope='session')
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


_report_summary = {}
_report_suite_name = None
_session_start_time = None


def _read_coverage_summary() -> dict | None:
    coverage_xml_path = os.getenv('COVERAGE_XML_PATH')
    if not coverage_xml_path:
        return None
    coverage_path = Path(coverage_xml_path)
    if not coverage_path.exists():
        return None
    root = ElementTree.parse(coverage_path).getroot()
    line_rate = root.attrib.get('line-rate')
    lines_covered = root.attrib.get('lines-covered')
    lines_valid = root.attrib.get('lines-valid')
    if line_rate is None:
        return None
    coverage_percent = round(float(line_rate) * 100, 2)
    summary = {
        'coverage_percent': coverage_percent,
        'lines_covered': lines_covered,
        'lines_valid': lines_valid,
        'coverage_html': os.getenv('COVERAGE_HTML_PATH'),
    }
    return summary


def _resolve_report_suite_name(html_path: str | None) -> str:
    if not html_path:
        return 'Pytest Report'
    name = Path(html_path).name.lower()
    if 'unit' in name:
        return 'Unit Test Report'
    if 'integration' in name:
        return 'Integration Test Report'
    return 'Pytest Report'


def pytest_configure(config):
    global _report_suite_name
    html_path = getattr(config.option, 'htmlpath', None)
    if html_path:
        Path(html_path).parent.mkdir(parents=True, exist_ok=True)
    _report_suite_name = _resolve_report_suite_name(html_path)


def pytest_sessionstart(session):
    global _session_start_time
    _session_start_time = time.time()


def pytest_sessionfinish(session, exitstatus):
    global _report_summary
    terminal_reporter = session.config.pluginmanager.get_plugin('terminalreporter')
    stats = getattr(terminal_reporter, 'stats', {}) if terminal_reporter else {}
    _report_summary = {
        'total': session.testscollected,
        'passed': len(stats.get('passed', [])),
        'failed': len(stats.get('failed', [])),
        'skipped': len(stats.get('skipped', [])),
        'error': len(stats.get('error', [])),
        'xfailed': len(stats.get('xfailed', [])),
        'xpassed': len(stats.get('xpassed', [])),
        'duration_seconds': time.time() - _session_start_time if _session_start_time else None,
        'exit_status': exitstatus,
        'python_version': sys.version.split()[0],
        'platform': platform.platform(),
    }


def pytest_html_report_title(report):
    report.title = _report_suite_name or 'Pytest Report'


def pytest_html_results_summary(prefix, summary, postfix):
    if not _report_summary:
        return
    coverage_summary = _read_coverage_summary()
    duration = (
        round(_report_summary['duration_seconds'], 2)
        if _report_summary['duration_seconds'] is not None
        else 'n/a'
    )
    summary.append('Run summary')
    summary.append(f"Suite: {_report_suite_name or 'Pytest Report'}")
    summary.append(f"Total: {_report_summary['total']}")
    summary.append(f"Passed: {_report_summary['passed']}")
    summary.append(f"Failed: {_report_summary['failed']}")
    summary.append(f"Skipped: {_report_summary['skipped']}")
    summary.append(f"Errors: {_report_summary['error']}")
    summary.append(f"XFailed: {_report_summary['xfailed']}")
    summary.append(f"XPassed: {_report_summary['xpassed']}")
    summary.append(f"Duration (s): {duration}")
    summary.append(f"Python: {_report_summary['python_version']}")
    summary.append(f"Platform: {_report_summary['platform']}")
    if coverage_summary:
        summary.append('Coverage summary')
        summary.append(f"Total: {coverage_summary['coverage_percent']}%")
        if coverage_summary['lines_covered'] and coverage_summary['lines_valid']:
            summary.append(
                f"Lines: {coverage_summary['lines_covered']}/{coverage_summary['lines_valid']}"
            )
        if coverage_summary['coverage_html']:
            summary.append(f"HTML: {coverage_summary['coverage_html']}")


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
    
    # Replace with test database
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
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for FastAPI."""
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
async def test_user(user_repository: UserRepository) -> User:
    """Create a test user."""
    user = User(
        email='test@example.com',
        name='Test User',
        hashed_password=hash_password('testpassword123'),
        created_at=datetime.utcnow()
    )
    created_user = await user_repository.create(user)
    return created_user


@pytest.fixture
async def authenticated_client(
    async_client: AsyncClient,
    test_user: User,
    user_repository: UserRepository
) -> AsyncGenerator[AsyncClient, None]:
    """Provide an authenticated async client."""
    from src.auth.jwt import create_access_token
    
    access_token = create_access_token(
        data={'sub': test_user.id, 'email': test_user.email, 'role': test_user.role}
    )
    
    async_client.headers.update({'Authorization': f'Bearer {access_token}'})
    yield async_client
    async_client.headers.pop('Authorization', None)
