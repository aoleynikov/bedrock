# Testing Infrastructure

This directory contains the test suite for the Bedrock backend.

## Structure

- `unit/` - Unit tests for individual components (services, utilities)
- `integration/` - Integration tests for API routes and database operations
- `conftest.py` - Pytest configuration and shared fixtures

## Running Tests

### Run all tests
```bash
pytest
```

### Run only unit tests
```bash
pytest tests/unit -m unit
```

### Run only integration tests
```bash
pytest tests/integration -m integration
```

### Run with coverage
```bash
pytest --cov=src --cov-report=html
```

### Run unit tests with coverage reports
```bash
./scripts/run_unit_tests.sh
```

### Run integration tests with coverage reports
```bash
./scripts/run_integration_tests.sh
```

The HTML reports include a coverage summary and a link to the full coverage HTML output.

### Run specific test file
```bash
pytest tests/integration/test_auth_routes.py
```

## Data isolation

Each **Docker** integration test run uses a new Compose project with fresh volumes (see `scripts/run_integration_tests_docker.sh` and [docs/data-persistence.md](../../docs/data-persistence.md)). Unit test runs do not use persistent volumes.

## User roles and the default admin

Do **not** rely on the `ensure_default_admin` background task in integration tests. For any test that needs to act as a user with a given role, create that user as part of the **arrange** stage (or use a fixture that does).

## Test Database

Tests use a separate test database (`bedrock_test`) that is automatically:
- Created before tests run
- Cleaned between test functions
- Dropped after all tests complete

## Fixtures

Key fixtures available:
- `test_db` - Test database connection (session scope, async)
- `db_session` - Database session for each test (function scope, async)
- `client` - Async HTTP client (httpx.AsyncClient) for the app; use for unauthenticated requests
- `user_repository` - UserRepository instance
- `test_user` - Regular user created via API (arrange). Use for tests that need a user-role actor; do not rely on ensure_default_admin.
- `authenticated_client` - Same client as `client` with Authorization header set (regular test user). Depends on `test_user`.
- `admin_client` - Separate AsyncClient authenticated as an admin (admin created in fixture via repository, then login).
- `other_user_client` - Separate AsyncClient authenticated as a second user (created via API). Use when a test needs two users (e.g. forbidden access).
- `user_payload` - Generated email, name, password for request bodies (one per test).
- `five_user_payloads` - Five distinct payloads for tests that need several users (e.g. pagination).

Integration tests use **async HTTP** (httpx.AsyncClient with ASGITransport) so the app and test database share the same event loop. Technical user operations are hidden behind client construction: tests receive ready-to-use clients (`client`, `authenticated_client`, `admin_client`, `other_user_client`) and optional payloads. Implementation lives in [integration/user_helpers.py](integration/user_helpers.py) and [integration/conftest.py](integration/conftest.py); test files do not import user_helpers except when they need `clear_auth` (e.g. to test unauthenticated access using the same client). All user data is generated via [Faker](https://faker.readthedocs.io/); no default credentials are used.

**Client identity:** `client` and `authenticated_client` are the same object; `authenticated_client` just adds the Bearer token to that client. If a test needs both an authenticated and an unauthenticated request, call `clear_auth(client)` before the unauthenticated request (import from `tests.integration.user_helpers`).

## Writing Tests

### Unit Test Example
```python
@pytest.mark.unit
class TestPasswordService:
    def test_hash_password(self):
        password = 'testpassword123'
        hashed = hash_password(password)
        assert hashed != password
```

### Integration Test Example
```python
import pytest
from httpx import AsyncClient

@pytest.mark.integration
class TestAuthRoutes:
    async def test_login_success(self, client: AsyncClient, test_user: dict):
        response = await client.post(
            '/api/auth/login',
            json={
                'email': test_user['email'],
                'password': test_user['password'],
                'strategy': 'credentials',
            },
        )
        assert response.status_code == 200
```
