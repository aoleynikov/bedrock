import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestTasksRoutes:
    async def test_create_task_success(self, authenticated_client: AsyncClient):
        """Test successful task creation."""
        response = await authenticated_client.post(
            '/api/tasks/example',
            params={'message': 'Test task message'},
        )
        assert response.status_code == 200
        data = response.json()
        assert 'task_id' in data
        assert 'status' in data
        assert 'message' in data
        assert data['task_id'] is not None

    async def test_create_task_unauthorized(self, client: AsyncClient):
        """Test task creation without authentication."""
        response = await client.post(
            '/api/tasks/example',
            params={'message': 'Test task message'},
        )
        assert response.status_code == 401
        data = response.json()
        assert data['status'] in ('error', 'common.error')

    async def test_get_task_status_success(self, authenticated_client: AsyncClient):
        """Test getting task status."""
        create_response = await authenticated_client.post(
            '/api/tasks/example',
            params={'message': 'Test task message'},
        )
        task_id = create_response.json()['task_id']
        response = await authenticated_client.get(f'/api/tasks/{task_id}')
        assert response.status_code == 200
        data = response.json()
        assert 'task_id' in data
        assert 'status' in data
        assert data['task_id'] == task_id

    async def test_get_task_status_not_found(self, authenticated_client: AsyncClient):
        """Test getting status for non-existent task."""
        response = await authenticated_client.get('/api/tasks/nonexistent-task-id')
        assert response.status_code in (200, 400)
        if response.status_code == 200:
            data = response.json()
            assert 'task_id' in data
            assert 'status' in data

    async def test_get_task_status_unauthorized(self, client: AsyncClient):
        """Test getting task status without authentication."""
        response = await client.get('/api/tasks/some-task-id')
        assert response.status_code == 401
        data = response.json()
        assert data['status'] in ('error', 'common.error')

    async def test_trigger_cleanup_admin_success(self, admin_client: AsyncClient):
        """Test admin can trigger cleanup task."""
        response = await admin_client.post(
            '/api/tasks/cleanup',
            params={'max_age_hours': 6},
        )
        assert response.status_code == 200
        data = response.json()
        assert 'task_id' in data
        assert data['status'] == 'pending'
        assert data['max_age_hours'] == 6
        assert 'message' in data

    async def test_trigger_cleanup_forbidden(self, authenticated_client: AsyncClient):
        """Test non-admin cannot trigger cleanup task."""
        response = await authenticated_client.post(
            '/api/tasks/cleanup',
            params={'max_age_hours': 6},
        )
        assert response.status_code == 403
        data = response.json()
        assert data['status'] in ('error', 'common.error')

    async def test_trigger_cleanup_unauthorized(self, client: AsyncClient):
        """Test unauthenticated request cannot trigger cleanup task."""
        response = await client.post(
            '/api/tasks/cleanup',
            params={'max_age_hours': 6},
        )
        assert response.status_code == 401

    async def test_trigger_cleanup_invalid_max_age(self, admin_client: AsyncClient):
        """Test cleanup with invalid max_age_hours returns validation error."""
        response = await admin_client.post(
            '/api/tasks/cleanup',
            params={'max_age_hours': 0},
        )
        assert response.status_code == 400
        data = response.json()
        assert 'detail' in data
