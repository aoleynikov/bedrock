import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestTasksRoutes:
    async def test_create_task_success(self, authenticated_client: AsyncClient):
        """Test successful task creation."""
        response = await authenticated_client.post(
            '/api/tasks/example',
            params={'message': 'Test task message'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'task_id' in data
        assert 'status' in data
        assert 'message' in data
        assert data['task_id'] is not None
    
    async def test_create_task_unauthorized(self, async_client: AsyncClient):
        """Test task creation without authentication."""
        response = await async_client.post(
            '/api/tasks/example',
            params={'message': 'Test task message'}
        )
        
        assert response.status_code == 401
        data = response.json()
        # Status can be 'error' (translated) or 'common.error' (translation key)
        assert data['status'] in ('error', 'common.error')
    
    async def test_get_task_status_success(self, authenticated_client: AsyncClient):
        """Test getting task status."""
        # First create a task
        create_response = await authenticated_client.post(
            '/api/tasks/example',
            params={'message': 'Test task message'}
        )
        task_id = create_response.json()['task_id']
        
        # Then get its status
        response = await authenticated_client.get(f'/api/tasks/{task_id}')
        
        assert response.status_code == 200
        data = response.json()
        assert 'task_id' in data
        assert 'status' in data
        assert data['task_id'] == task_id
    
    async def test_get_task_status_not_found(self, authenticated_client: AsyncClient):
        """Test getting status for non-existent task.
        
        Note: With RPC backend, we can't reliably detect non-existent tasks
        as they may appear as PENDING. This test verifies the endpoint doesn't crash.
        """
        response = await authenticated_client.get('/api/tasks/nonexistent-task-id')
        
        # With RPC backend, non-existent tasks may return PENDING status
        # Accept either 200 (with PENDING status) or 400 (if validation catches it)
        assert response.status_code in (200, 400)
        if response.status_code == 200:
            data = response.json()
            assert 'task_id' in data
            assert 'status' in data
    
    async def test_get_task_status_unauthorized(self, async_client: AsyncClient):
        """Test getting task status without authentication."""
        response = await async_client.get('/api/tasks/some-task-id')
        
        assert response.status_code == 401
        data = response.json()
        # Status can be 'error' (translated) or 'common.error' (translation key)
        assert data['status'] in ('error', 'common.error')
