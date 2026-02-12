from unittest.mock import MagicMock, patch

import pytest

from src.services.task_service import TaskService


@pytest.fixture
def task_service():
    return TaskService()


@pytest.mark.unit
@pytest.mark.asyncio
class TestTaskService:
    async def test_get_task_status_invalid_id(self, task_service: TaskService):
        """Test getting task status with invalid ID."""
        with pytest.raises(ValueError, match='errors.task.id_required'):
            await task_service.get_task_status('')

    async def test_get_task_status_not_found_in_test_env(self, task_service: TaskService):
        """Test get_task_status in test env when task is not in in-memory backend."""
        with patch('src.services.task_service.settings') as mock_settings:
            mock_settings.env = 'test'
            with patch('src.services.task_service.get_in_memory_queue_backend') as mock_get:
                mock_get.return_value.get_task.return_value = None
                with pytest.raises(ValueError, match='errors.task.not_found'):
                    await task_service.get_task_status('unknown-task-id')

    async def test_get_task_status_success_in_test_env(self, task_service: TaskService):
        """Test get_task_status in test env when task exists in in-memory backend."""
        with patch('src.services.task_service.settings') as mock_settings:
            mock_settings.env = 'test'
            with patch('src.services.task_service.get_in_memory_queue_backend') as mock_get:
                mock_get.return_value.get_task.return_value = MagicMock()
                result = await task_service.get_task_status('known-task-id')
                assert result['task_id'] == 'known-task-id'
                assert result['status'] == 'PENDING'

    async def test_cancel_task_empty_id(self, task_service: TaskService):
        """Test cancel_task with empty task_id raises error."""
        with pytest.raises(ValueError, match='errors.task.id_required'):
            await task_service.cancel_task('')
