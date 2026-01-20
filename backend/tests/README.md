# Testing Infrastructure

This directory contains the test suite for the Bedrock backend.

## Structure

- `unit/` - Unit tests for individual components (services, utilities)
- `integration/` - Integration tests for API routes and database operations
- `fixtures/` - Shared test fixtures (if needed)
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

## Test Database

Tests use a separate test database (`bedrock_test`) that is automatically:
- Created before tests run
- Cleaned between test functions
- Dropped after all tests complete

## Fixtures

Key fixtures available:
- `test_db` - Test database connection (session scope)
- `db_session` - Database session for each test (function scope)
- `client` - FastAPI TestClient (synchronous)
- `async_client` - AsyncClient for async tests
- `user_repository` - UserRepository instance
- `test_user` - Pre-created test user
- `authenticated_client` - AsyncClient with valid JWT token

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
@pytest.mark.integration
class TestAuthRoutes:
    async def test_login_success(self, async_client: AsyncClient, test_user):
        response = await async_client.post(
            '/api/auth/login',
            json={'email': 'test@example.com', 'password': 'testpassword123'}
        )
        assert response.status_code == 200
```
