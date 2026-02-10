import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestAPIRoutes:
    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get('/api/health')
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        assert 'checks' in data
        assert 'database' in data['checks']

    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint."""
        response = await client.get('/')
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
