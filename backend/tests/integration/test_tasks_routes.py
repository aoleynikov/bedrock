import pytest
from httpx import AsyncClient

from src.tasks.startup import _run_startup_tasks


@pytest.mark.integration
class TestTasksRoutes:
    async def test_get_task_status_success(
        self, authenticated_client: AsyncClient, in_memory_queue
    ):
        """Test getting task status for an enqueued task."""
        result = await _run_startup_tasks('corr-id', 'coordinator-id')
        task_id = result['task_ids'][0]
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
